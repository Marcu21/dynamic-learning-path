"""
Chat assistant workflow using LangGraph for state management and flow control.

This module provides the workflow orchestration for the chat assistant,
managing the flow from query analysis through response generation.
"""

import time
import json
from typing import Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END

from app.core.logger import get_logger
from app.services.ai_services.chat_services.chat_service import ChatService
from app.services.ai_services.chat_services.context_retriever import ContextRetriever
from app.schemas.chat_assistant_schemas.chat_assistant_schema import UserContextLocation, ChatContext, UserLocation
from app.services.core_services.statistics_service import get_user_statistics

logger = get_logger(__name__)


class ChatAssistantWorkflow:
    """
    LangGraph-based workflow for the chat assistant.

    This class orchestrates the entire chat flow:
    1. Query analysis and entity extraction
    2. Restriction checking for quiz attempts
    3. Context retrieval based on user location
    4. Response generation using LLM
    5. Response validation and metadata addition
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_service = ChatService(db)
        self.context_retriever = ContextRetriever(db)
        self.graph = self._create_workflow_graph()

    def _create_workflow_graph(self) -> StateGraph:
        """
        Create the LangGraph workflow for the chat assistant.

        Returns:
            Compiled StateGraph for the chat workflow
        """
        workflow = StateGraph(dict)

        # Add workflow nodes
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("check_restrictions", self._check_restrictions_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("validate_response", self._validate_response_node)

        # Define workflow edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "check_restrictions")

        # Conditional edge based on restrictions
        workflow.add_conditional_edges(
            "check_restrictions",
            self._should_restrict_response,
            {
                "restrict": "generate_response",  # Skip context retrieval for restricted responses
                "continue": "retrieve_context"
            }
        )

        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", "validate_response")
        workflow.add_edge("validate_response", END)

        return workflow.compile()

    async def _analyze_query_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the user query and determine context requirements.

        Args:
            state: Current workflow state

        Returns:
            Updated state with analysis results
        """
        question = state["question"]
        user_location = state["user_location"]

        logger.debug(f"Analyzing query: '{question[:50]}...' at location: {user_location.location}")

        # Determine context type based on location and question
        context_type = self._determine_context_type(question, user_location)

        # Extract entity references from question
        entities = self.chat_service.extract_entity_references(question)

        # Analyze question complexity
        question_complexity = self.chat_service.analyze_question_complexity(question)

        state.update({
            "context_type": context_type,
            "entities": entities,
            "question_complexity": question_complexity,
            "analysis_complete": True
        })

        logger.info(
            f"Query analysis complete: context_type={context_type.value}, "
            f"location={user_location.location.value}, entities={entities}"
        )

        return state

    def _determine_context_type(self, question: str, user_location: UserContextLocation) -> ChatContext:
        """
        Determine the appropriate context type based on user location and question.

        Args:
            question: User's question
            user_location: User's current location in the application

        Returns:
            Appropriate ChatContext type
        """
        # If user is taking a quiz, restrict all educational content
        if user_location.location in [UserLocation.QUIZ, UserLocation.QUIZ_ATTEMPT_ACTIVE]:
            return ChatContext.RESTRICTED

        question_lower = question.lower()

        # Context type based on location and question content
        if user_location.location == UserLocation.MODULE or "module" in question_lower:
            return ChatContext.MODULE
        elif user_location.location == UserLocation.QUIZ or "quiz" in question_lower:
            return ChatContext.QUIZ
        elif "progress" in question_lower or "completion" in question_lower:
            return ChatContext.USER_PROGRESS
        elif user_location.learning_path_id or "learning path" in question_lower:
            return ChatContext.LEARNING_PATH
        else:
            return ChatContext.GENERAL

    async def _check_restrictions_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if response should be restricted based on user location and quiz attempts.

        Args:
            state: Current workflow state

        Returns:
            Updated state with restriction information
        """
        context_type = state["context_type"]
        user_location = state["user_location"]
        user_id = state["user_id"]

        logger.debug(f"Checking restrictions for user {user_id} at location {user_location.location}")

        # Check for active quiz attempts
        active_attempt = await self.context_retriever.check_active_quiz_attempt(
            user_id, user_location.quiz_id
        )

        # Determine if response should be restricted
        if user_location.location in [UserLocation.QUIZ, UserLocation.QUIZ_ATTEMPT_ACTIVE]:
            if context_type == ChatContext.RESTRICTED:
                state["restriction_reason"] = "active_quiz_session"
                state["restricted"] = True
                logger.info(f"Response restricted: active quiz session for user {user_id}")
            else:
                # Check if it's a casual question during quiz
                question = state["question"]
                if not self.chat_service._is_casual_question(question):
                    state["restriction_reason"] = "educational_content_during_quiz"
                    state["restricted"] = True
                    logger.info(f"Response restricted: educational content during quiz for user {user_id}")
                else:
                    state["restricted"] = False
        elif active_attempt:
            # User has active quiz attempt but not in quiz location
            state["restriction_reason"] = "active_quiz_attempt_detected"
            state["restricted"] = True
            logger.warning(f"Response restricted: active quiz attempt detected for user {user_id}")
        else:
            state["restricted"] = False

        state["active_quiz_attempt"] = active_attempt

        return state

    def _should_restrict_response(self, state: Dict[str, Any]) -> str:
        """
        Determine workflow path based on restriction status.

        Args:
            state: Current workflow state

        Returns:
            Next workflow step: "restrict" or "continue"
        """
        return "restrict" if state.get("restricted", False) else "continue"

    async def _retrieve_context_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve context scoped to user's location and question type.

        Args:
            state: Current workflow state

        Returns:
            Updated state with context data
        """
        context_type = state["context_type"]
        user_id = state["user_id"]
        user_location = state["user_location"]
        entities = state.get("entities", {})

        logger.debug(f"Retrieving context: type={context_type.value}, user={user_id}")

        context_result = {}

        try:
            if context_type == ChatContext.LEARNING_PATH:
                context_result = await self.context_retriever.get_scoped_learning_path_context(
                    user_id, user_location
                )
            elif context_type == ChatContext.MODULE:
                context_result = await self.context_retriever.get_scoped_module_context(
                    user_id, user_location, entities
                )
            elif context_type == ChatContext.QUIZ:
                context_result = await self.context_retriever.get_scoped_quiz_context(
                    user_id, user_location
                )
            elif context_type == ChatContext.USER_PROGRESS:
                # Get user progress summary
                progress_summary = get_user_statistics(self.db, user_id)
                context_result = {
                    "data": {"overall_progress": progress_summary},
                    "cache_hit": False,
                    "retrieval_time_ms": 0
                }
            else:
                # For general questions, get basic learning path context
                context_result = await self.context_retriever.get_scoped_learning_path_context(
                    user_id, user_location
                )

            logger.info(
                f"Context retrieved successfully: type={context_type.value}, "
                f"cache_hit={context_result.get('cache_hit', False)}, "
                f"time={context_result.get('retrieval_time_ms', 0)}ms"
            )

        except Exception as e:
            logger.error(f"Error retrieving context for user {user_id}: {str(e)}")
            context_result = {
                "data": {},
                "cache_hit": False,
                "retrieval_time_ms": 0,
                "error": str(e)
            }

        state.update({
            "context_data": context_result.get("data", {}),
            "cache_hit": context_result.get("cache_hit", False),
            "context_retrieval_time_ms": context_result.get("retrieval_time_ms", 0),
            "context_error": context_result.get("error")
        })

        return state

    async def _generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response using the chat service.

        Args:
            state: Current workflow state

        Returns:
            Updated state with generated response
        """
        logger.debug(f"Generating response for user {state['user_id']}")

        response_result = await self.chat_service.generate_response(
            question=state["question"],
            context_data=state.get("context_data", {}),
            context_type=state["context_type"],
            user_location=state["user_location"],
            question_complexity=state.get("question_complexity", "medium"),
            restricted=state.get("restricted", False),
            previous_response=state.get("previous_response"),
            original_user_question=state.get("original_user_question")
        )

        state.update({
            "response": response_result["response"],
            "confidence": response_result["confidence"],
            "llm_response_time_ms": response_result["llm_response_time_ms"],
            "generation_error": response_result.get("error")
        })

        logger.info(
            f"Response generated: confidence={response_result['confidence']:.2f}, "
            f"time={response_result['llm_response_time_ms']}ms, "
            f"restricted={response_result['restricted']}"
        )

        return state

    async def _validate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate response and add metadata.

        Args:
            state: Current workflow state

        Returns:
            Updated state with validation results
        """
        logger.debug(f"Validating response for user {state['user_id']}")

        validation_result = self.chat_service.validate_response(
            response=state["response"],
            context_data=state.get("context_data", {}),
            user_location=state["user_location"]
        )

        state.update(validation_result)

        logger.debug("Response validation complete")

        return state

    async def execute_chat(
            self,
            user_id: str,
            question: str,
            user_location: UserContextLocation,
            previous_response: Optional[str] = None,
            original_user_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete chat workflow.

        Args:
            user_id: ID of the user
            question: User's question
            user_location: User's current location in the application
            previous_response: Previous response for continuation
            original_user_question: Original question for continuation context

        Returns:
            Complete chat response with metadata
        """
        start_time = time.time()

        logger.info(
            f"Starting chat workflow: user_id={user_id}, "
            f"location={user_location.location.value}, "
            f"learning_path_id={user_location.learning_path_id}, "
            f"question='{question[:50]}...'"
        )

        initial_state = {
            "user_id": user_id,
            "question": question,
            "user_location": user_location,
            "previous_response": previous_response,
            "original_user_question": original_user_question,
            "context_type": ChatContext.GENERAL,
            "context_data": {},
            "entities": {},
            "response": "",
            "confidence": 0.0,
            "sources": [],
            "restricted": False,
            "cache_hit": False,
            "processing_time_ms": 0
        }

        try:
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state)

            total_time = int((time.time() - start_time) * 1000)

            logger.info(f"Chat workflow completed successfully for user {user_id} in {total_time}ms")

            return {
                "response": final_state["response"],
                "context_type": final_state["context_type"].value,
                "confidence": final_state["confidence"],
                "sources": final_state["sources"],
                "cache_hit": final_state.get("cache_hit", False),
                "processing_time_ms": total_time,
                "context_retrieval_time_ms": final_state.get("context_retrieval_time_ms", 0),
                "llm_response_time_ms": final_state.get("llm_response_time_ms", 0),
                "location_info": final_state.get("location_info", {}),
                "restricted": final_state.get("restricted", False),
                "restriction_reason": final_state.get("restriction_reason"),
                "active_quiz_attempt": final_state.get("active_quiz_attempt")
            }

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            logger.error(f"Chat workflow error for user {user_id}: {str(e)}")

            return {
                "response": "I apologize, but I encountered an error while processing your question. Please try again.",
                "context_type": "error",
                "confidence": 0.0,
                "sources": [],
                "cache_hit": False,
                "processing_time_ms": total_time,
                "error": str(e)
            }

    async def execute_chat_stream(
            self,
            user_id: str,
            question: str,
            user_location: UserContextLocation,
            previous_response: Optional[str] = None,
            original_user_question: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute chat workflow with streaming response.

        Args:
            user_id: ID of the user
            question: User's question
            user_location: User's current location in the application
            previous_response: Previous response for continuation
            original_user_question: Original question for continuation context

        Yields:
            JSON strings containing streaming updates
        """
        try:
            # Send initial status
            yield json.dumps({
                "type": "status",
                "message": f"Analyzing question for {user_location.location.value.replace('_', ' ')}..."
            })

            # Get the full response using the workflow
            result = await self.execute_chat(
                user_id=user_id,
                question=question,
                user_location=user_location,
                previous_response=previous_response,
                original_user_question=original_user_question
            )

            # Send context status
            cache_status = "from cache" if result.get('cache_hit') else "fresh lookup"
            restriction_info = f" (restricted: {result.get('restriction_reason')})" if result.get('restricted') else ""

            yield json.dumps({
                "type": "status",
                "message": f"Context retrieved {cache_status}{restriction_info}, generating response..."
            })

            # Stream the response
            async for chunk in self.chat_service.stream_response(result["response"]):
                yield chunk

            # Send final metadata
            yield json.dumps({
                "type": "metadata",
                "context_type": result["context_type"],
                "confidence": result["confidence"],
                "sources": result["sources"],
                "cache_hit": result.get("cache_hit", False),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "location_info": result.get("location_info", {}),
                "restricted": result.get("restricted", False),
                "active_quiz_attempt": result.get("active_quiz_attempt")
            })

        except Exception as e:
            logger.error(f"Streaming chat workflow error for user {user_id}: {str(e)}")
            yield json.dumps({"type": "error", "message": str(e)})


class ChatAgent:
    """
    Backward compatibility wrapper for the refactored chat system.

    This class maintains the same interface as the original ChatAgent
    while delegating to the new workflow-based implementation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workflow = ChatAssistantWorkflow(db)
        self.context_retriever = self.workflow.context_retriever

    async def chat(
            self,
            user_id: str,
            question: str,
            user_location: UserContextLocation
    ) -> Dict[str, Any]:
        """
        Main chat interface with location awareness.

        Args:
            user_id: ID of the user
            question: User's question
            user_location: User's current location

        Returns:
            Chat response with metadata
        """
        return await self.workflow.execute_chat(user_id, question, user_location)

    async def chat_stream(
            self,
            user_id: str,
            question: str,
            user_location: UserContextLocation
    ) -> AsyncGenerator[str, None]:
        """
        Streaming interface with location awareness.

        Args:
            user_id: ID of the user
            question: User's question
            user_location: User's current location

        Yields:
            JSON strings containing streaming updates
        """
        async for chunk in self.workflow.execute_chat_stream(user_id, question, user_location):
            yield chunk
