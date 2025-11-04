"""
Chat service for handling LLM interactions and business logic.

This module provides the core chat functionality including LLM communication,
response generation, and context formatting for the chat assistant.
"""

import time
import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger
from app.services.ai_services.chat_services.context_retriever import ContextRetriever
from app.schemas.chat_assistant_schemas.chat_assistant_schema import (
    ChatContext,
    UserContextLocation,
    UserLocation
)


logger = get_logger(__name__)


class ChatService:
    """
    Core chat service handling LLM interactions and business logic.

    This service is responsible for:
    - LLM communication and response generation
    - Context formatting and system prompt creation
    - Response validation and confidence calculation
    - Entity extraction and question analysis
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
        )
        self.context_retriever = ContextRetriever(db)
        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": getattr(settings, "chat_max_tokens", 2000),
            "timeout": settings.llm_request_timeout,
        }

    async def generate_response(
        self,
        question: str,
        context_data: Dict[str, Any],
        context_type: ChatContext,
        user_location: UserContextLocation,
        question_complexity: str = "medium",
        restricted: bool = False,
        previous_response: Optional[str] = None,
        original_user_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using LLM based on context and restrictions.

        Args:
            question: User's question
            context_data: Retrieved context information
            context_type: Type of context being used
            user_location: User's current location in the application
            question_complexity: Complexity level of the question
            restricted: Whether response should be restricted
            previous_response: Previous response for continuation
            original_user_question: Original question for continuation context

        Returns:
            Dict containing response text, confidence, and timing
        """
        start_time = time.time()

        try:
            if restricted:
                response_text = self._generate_restricted_response(question)
                confidence = 0.9
                logger.info(f"Generated restricted response for quiz attempt")
            else:
                response_text, confidence = await self._generate_llm_response(
                    question=question,
                    context_data=context_data,
                    context_type=context_type,
                    user_location=user_location,
                    question_complexity=question_complexity,
                    previous_response=previous_response,
                    original_user_question=original_user_question
                )

            llm_response_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"Generated response for user in {llm_response_time}ms "
                f"(confidence: {confidence:.2f}, restricted: {restricted})"
            )

            return {
                "response": response_text,
                "confidence": confidence,
                "llm_response_time_ms": llm_response_time,
                "restricted": restricted
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble generating a response right now. Please try again.",
                "confidence": 0.0,
                "llm_response_time_ms": int((time.time() - start_time) * 1000),
                "restricted": restricted,
                "error": str(e)
            }

    async def _generate_llm_response(
        self,
        question: str,
        context_data: Dict[str, Any],
        context_type: ChatContext,
        user_location: UserContextLocation,
        question_complexity: str,
        previous_response: Optional[str] = None,
        original_user_question: Optional[str] = None
    ) -> tuple[str, float]:
        """
        Generate response using LLM with context and conversation handling.

        Returns:
            Tuple of (response_text, confidence_score)
        """
        system_prompt = self.create_location_aware_system_prompt(
            context_type, user_location, question_complexity
        )
        context_text = self.format_location_aware_context(
            context_data, context_type, user_location
        )

        # Handle continuation requests
        is_continue = question.strip().lower() == "continue"

        if is_continue and previous_response:
            messages = self._build_continuation_messages(
                system_prompt=system_prompt,
                context_text=context_text,
                previous_response=previous_response,
                original_user_question=original_user_question
            )
        else:
            messages = self._build_standard_messages(
                system_prompt=system_prompt,
                context_text=context_text,
                question=question
            )

        # Call LLM with proper configuration and timeout
        logger.debug("Making LLM call for chat response generation")
        logger.debug(f"Using model: {self.generation_config['model']}")
        logger.debug(f"Messages count: {len(messages)}")
        logger.debug(f"Total prompt length: {sum(len(str(msg)) for msg in messages)} characters")

        response = await asyncio.wait_for(
            self.llm_client.chat.completions.create(
                model=self.generation_config["model"],
                messages=messages,
                max_completion_tokens=self.generation_config["max_tokens"],
            ),
            timeout=self.generation_config["timeout"]
        )

        response_text = response.choices[0].message.content
        confidence = self._calculate_confidence(context_data, context_type, response_text)

        return response_text, confidence

    def _build_continuation_messages(
        self,
        system_prompt: str,
        context_text: str,
        previous_response: str,
        original_user_question: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build messages for continuation requests."""
        last_item_number = self._extract_last_numbered_item(previous_response)

        if last_item_number:
            continuation_instruction = (
                f"The last item you completed was number {last_item_number}. "
                f"Continue the list starting with item {last_item_number + 1}. "
                "Do not repeat any previous items."
            )
        else:
            continuation_instruction = (
                "Continue your previous answer, starting from where you left off. "
                "Do not repeat any information already provided above."
            )

        if original_user_question:
            messages = [
                {"role": "system", "content": "You are a helpful educational assistant with deep knowledge of learning paths, modules, and student progress."},
                {"role": "user", "content": f"{system_prompt}\n\nCONTEXT INFORMATION:\n{context_text}"},
                {"role": "user", "content": original_user_question},
                {"role": "assistant", "content": previous_response},
                {"role": "user", "content": continuation_instruction}
            ]
        else:
            messages = [
                {"role": "system", "content": "You are a helpful educational assistant with deep knowledge of learning paths, modules, and student progress."},
                {"role": "user", "content": f"{system_prompt}\n\nCONTEXT INFORMATION:\n{context_text}"},
                {"role": "assistant", "content": previous_response},
                {"role": "user", "content": continuation_instruction}
            ]

        return messages

    def _build_standard_messages(
        self,
        system_prompt: str,
        context_text: str,
        question: str
    ) -> List[Dict[str, str]]:
        """Build messages for standard requests."""
        prompt = f"""
{system_prompt}

CONTEXT INFORMATION:
{context_text}

USER QUESTION: {question}

Please provide a helpful, accurate response based on the context provided. Be specific and reference the relevant information from the context.
"""

        return [
            {
                "role": "system",
                "content": "You are a helpful educational assistant with deep knowledge of learning paths, modules, and student progress."
            },
            {"role": "user", "content": prompt}
        ]

    def _extract_last_numbered_item(self, text: str) -> Optional[int]:
        """Extract the last numbered item from text (e.g., '3. ...' returns 3)."""
        import re
        matches = re.findall(r'^(\d+)\.', text, re.MULTILINE)
        if matches:
            return int(matches[-1])
        return None

    def _generate_restricted_response(self, question: str) -> str:
        """
        Generate response for restricted contexts (quiz sessions).

        Args:
            question: User's question

        Returns:
            Appropriate restricted response
        """
        if self._is_casual_question(question):
            casual_responses = [
                "I'm doing well, thank you for asking! Focus on your quiz for now – you've got this! 💪",
                "Hi there! I see you're working on a quiz. Take your time and trust what you've learned!",
                "Hello! Great to hear from you. Concentrate on your quiz for now – I'll be here when you're done! 📚",
                "I'm here and doing well! You're doing great by staying focused on your quiz. Keep it up!",
                "Good to hear from you! I believe in you – finish your quiz and then we can chat about your learning! ✨"
            ]
            return casual_responses[hash(question) % len(casual_responses)]
        else:
            restriction_responses = [
                "I can see you're currently taking a quiz! I can't help with educational questions right now as that wouldn't be fair to your learning assessment. Please finish your quiz first, then I'll be happy to help with any questions you have! 📝",
                "Hey there! You're in the middle of a quiz, so I need to step back from answering educational questions. This helps ensure your quiz results truly reflect your knowledge. Come back when you're done and I'll be glad to help! 🎯",
                "I notice you're taking a quiz right now! I want to make sure you get a fair assessment of your learning, so I can't provide educational assistance during quizzes. Feel free to ask me casual questions like 'How are you?' or come back after you finish! 🚀",
                "You're currently in a quiz session! While I'd love to help with learning questions, I need to stay quiet during assessments to keep things fair. Finish up your quiz and then we can dive into any questions you have! Good luck! 🌟"
            ]
            return restriction_responses[hash(question) % len(restriction_responses)]

    def _is_casual_question(self, question: str) -> bool:
        """Check if a question is casual/social rather than educational."""
        question_lower = question.strip().lower()

        casual_patterns = [
            r'^(hi|hello|hey)(\s|!|\?|\.)*$',
            r'^(how are you|how\'re you)(\s|!|\?|\.)*$',
            r'^(thanks?|thank you)(\s|!|\?|\.)*$',
            r'^(bye|goodbye|see you)(\s|!|\?|\.)*$',
        ]

        import re
        for pattern in casual_patterns:
            if re.match(pattern, question_lower):
                return True

        return False

    def create_location_aware_system_prompt(
        self,
        context_type: ChatContext,
        user_location: UserContextLocation,
        question_complexity: str = "medium"
    ) -> str:
        """
        Create system prompt with location awareness.

        Args:
            context_type: Type of context being used
            user_location: User's current location
            question_complexity: Complexity level of the question

        Returns:
            Formatted system prompt
        """
        base_prompt = f"""You are a helpful learning assistant. The user is currently in their learning platform at location: {user_location.location.value.replace('_', ' ').title()}.

CORE PRINCIPLES:
- Always use ACTUAL names and titles from the provided context data
- Never use placeholder text like "Learning Path 1" or "Module X" - use the real names
- Be specific and reference actual content
- When referring to learning paths or modules by number, use their actual names from the context
- Be helpful, encouraging, and educational

RESPONSE STYLE:"""

        # Add complexity-based guidance
        if question_complexity == "simple":
            base_prompt += "\nProvide a concise, direct answer."
        elif question_complexity == "complex":
            base_prompt += "\nProvide a detailed, comprehensive explanation with examples and context."
        else:  # medium
            base_prompt += "\nProvide a balanced response with enough detail to be helpful but not overwhelming."

        # Add location-specific guidance
        if user_location.location == UserLocation.DASHBOARD:
            if user_location.team_id:
                base_prompt += """

TEAM DASHBOARD CONTEXT: You're helping someone navigate their team's dashboard. Focus on:
- You have access to the LAST 5 CREATED TEAM learning paths only (use their actual names from the context)
- Progress across these 5 team learning paths
- Comparing and contrasting these team learning paths
- When they mention a specific learning path, refer to it by its actual name from the context
- When they ask about "team learning paths" or "our learning paths", provide information about these 5 available team paths
- Use the actual learning path names and module names from the context data
- If they ask about a specific path number (1, 2, 3, etc.), refer to the path at that position by its actual name
- Remember this is a TEAM dashboard - these are shared learning paths for the team

IMPORTANT LIMITATIONS:
- You only have access to the last 5 created TEAM learning paths for this team
- If the user asks about team learning paths not in your context, politely explain that you can only see the 5 most recent team learning paths
- If they ask about older team learning paths, suggest they check the full team dashboard or learning path history
- Always be transparent about this limitation when relevant"""
            else:
                base_prompt += """

PERSONAL DASHBOARD CONTEXT: You're helping someone navigate their personal dashboard. Focus on:
- You have access to the LAST 5 CREATED PERSONAL learning paths only (use their actual names from the context)
- Progress across these 5 personal learning paths
- Comparing and contrasting these personal learning paths
- When they mention a specific learning path, refer to it by its actual name from the context
- When they ask about "my learning paths", provide information about these 5 available personal paths
- Use the actual learning path names and module names from the context data
- If they ask about a specific path number (1, 2, 3, etc.), refer to the path at that position by its actual name
- Remember this is a PERSONAL dashboard - these are the user's own learning paths

IMPORTANT LIMITATIONS:
- You only have access to the last 5 created PERSONAL learning paths
- If the user asks about personal learning paths not in your context, politely explain that you can only see their 5 most recent personal learning paths
- If they ask about older personal learning paths, suggest they check their full dashboard or learning path history
- Always be transparent about this limitation when relevant"""

        elif user_location.location == UserLocation.LEARNING_PATH:
            base_prompt += """

LEARNING PATH CONTEXT: You're helping someone navigate a specific learning path. Focus on:
- Modules within THIS specific learning path (use their actual names from the context)
- Progress through the current path
- What's next in their current learning sequence
- When they mention "Module 2" or "second module", refer to the actual module name at position 2 in the context
- Use the actual learning path name and module names from the context data
- If they ask about a specific module number, find that module in the context list and use its real name and learning objectives"""

        elif context_type == ChatContext.MODULE:
            base_prompt += """

MODULE-SPECIFIC GUIDANCE:
- Use the actual module titles and descriptions provided in the context
- Reference specific learning objectives when available - list them out specifically
- If asked about module content, provide detailed information based on the context
- Replace any placeholder text with actual information from the module learning objectives
- When learning objectives are available, list them specifically as bullet points
- Never refer to modules by ID numbers - always use their actual names from the context"""

        if user_location.location == UserLocation.REVIEW_ANSWERS:
            base_prompt += """

REVIEW ANSWERS CONTEXT: The user is reviewing their quiz answers.

You have access to:
- The learning path (title, description)
- The module (title, description, learning objectives)
- The quiz (title, total questions, passing score)
- The user's latest quiz attempt (answers, which were correct/incorrect, feedback)

INSTRUCTIONS:
- Use ALL available context to generate tailored feedback and follow-up questions
- When the user asks for more questions, generate new questions based on the module's learning objectives and the quiz content
- If the user got some answers wrong, focus on those topics for follow-up questions
- If you see the user's answers and which were incorrect, provide constructive feedback and suggest areas for improvement
- Always reference the actual names and content from the context
- If any context is missing, politely inform the user and ask for clarification if needed"""

        return base_prompt

    def format_location_aware_context(
        self,
        context_data: Dict[str, Any],
        context_type: ChatContext,
        user_location: UserContextLocation
    ) -> str:
        """
        Format context with location awareness.

        Args:
            context_data: Raw context data
            context_type: Type of context
            user_location: User's current location

        Returns:
            Formatted context string
        """
        if "error" in context_data:
            error_msg = context_data["error"]
            logger.error(f"Context error: {error_msg}")
            return f"Error retrieving context: {error_msg}"

        try:
            context_text = f"USER LOCATION: {user_location.location.value.replace('_', ' ').title()}\n"

            # Handle dashboard context with multiple learning paths
            if user_location.location == UserLocation.DASHBOARD and context_data.get("context_type") == "dashboard":
                learning_paths = context_data.get("learning_paths", [])
                total_paths = context_data.get("total_paths", 0)
                team_context = context_data.get("team_context", False)
                team_id = context_data.get("team_id")

                if team_context:
                    context_text += f"TEAM DASHBOARD OVERVIEW: This is the dashboard for team {team_id}\n"
                    context_text += f"You have {total_paths} TEAM learning paths available\n"
                    context_text += "NOTE: I can only see the LAST 5 CREATED team learning paths. If the team has more, I won't be able to see older ones.\n\n"

                    if learning_paths:
                        context_text += "TEAM LEARNING PATHS (Last 5 created):\n"
                        for i, path in enumerate(learning_paths, 1):
                            # Handle both old LearningPathResponse objects and new dict format
                            if hasattr(path, 'title'):  # Old LearningPathResponse object
                                title = path.title
                                path_id = path.id
                                description = path.description or 'No description'
                                estimated_days = path.estimated_days or 'Not specified'
                                total_modules = path.total_modules or 0
                            else:  # New dict format
                                title = path.get('title', 'Untitled')
                                path_id = path.get('id')
                                description = path.get('description', 'No description')
                                estimated_days = path.get('estimated_days', 'Not specified')
                                total_modules = path.get('total_modules', 0)

                            context_text += f"{i}. **{title}** (ID: {path_id})\n"
                            context_text += f"   Description: {description}\n"
                            context_text += f"   Estimated Days: {estimated_days}\n"
                            context_text += f"   Total Modules: {total_modules}\n\n"
                    else:
                        context_text += "No team learning paths found.\n"
                else:
                    context_text += "PERSONAL DASHBOARD OVERVIEW: This is your personal dashboard\n"
                    context_text += f"You have {total_paths} PERSONAL learning paths available\n"
                    context_text += "NOTE: I can only see your LAST 5 CREATED personal learning paths. If you have more, I won't be able to see older ones.\n\n"

                    if learning_paths:
                        context_text += "YOUR PERSONAL LEARNING PATHS (Last 5 created):\n"
                        for i, path in enumerate(learning_paths, 1):
                            # Handle both old LearningPathResponse objects and new dict format
                            if hasattr(path, 'title'):  # Old LearningPathResponse object
                                title = path.title
                                path_id = path.id
                                description = path.description or 'No description'
                                estimated_days = path.estimated_days or 'Not specified'
                                total_modules = path.total_modules or 0
                            else:  # New dict format
                                title = path.get('title', 'Untitled')
                                path_id = path.get('id')
                                description = path.get('description', 'No description')
                                estimated_days = path.get('estimated_days', 'Not specified')
                                total_modules = path.get('total_modules', 0)

                            context_text += f"{i}. **{title}** (ID: {path_id})\n"
                            context_text += f"   Description: {description}\n"
                            context_text += f"   Estimated Days: {estimated_days}\n"
                            context_text += f"   Total Modules: {total_modules}\n\n"
                    else:
                        context_text += "No personal learning paths found.\n"

                return context_text

            # Handle single learning path context
            if "learning_path" in context_data and context_data["learning_path"]:
                path = context_data["learning_path"]
                # Handle both old LearningPathResponse objects and new dict format
                if hasattr(path, 'title'):  # Old LearningPathResponse object
                    title = path.title
                    path_id = path.id
                    description = path.description or 'No description'
                    estimated_days = path.estimated_days or 'Not specified'
                    total_modules = path.total_modules or 0
                else:  # New dict format
                    title = path.get('title', 'Untitled')
                    path_id = path.get('id')
                    description = path.get('description', 'No description')
                    estimated_days = path.get('estimated_days', 'Not specified')
                    total_modules = path.get('total_modules', 0)

                context_text += f"CURRENT LEARNING PATH: **{title}** (ID: {path_id})\n"
                context_text += f"Description: {description}\n"
                context_text += f"Estimated Days: {estimated_days}\n"
                context_text += f"Total Modules: {total_modules}\n\n"

            # Add modules information
            if "modules" in context_data and context_data["modules"]:
                modules = context_data["modules"]
                context_text += f"MODULES ({len(modules)} total):\n"
                for i, module in enumerate(modules, 1):
                    # Handle both old module objects and new dict format
                    if hasattr(module, 'title'):  # Old module object
                        title = module.title
                        description = module.description
                        learning_objectives = getattr(module, 'learning_objectives', []) or []
                        duration = getattr(module, 'duration', 'N/A')
                        difficulty = getattr(module, 'difficulty', 'intermediate')
                        has_quiz = getattr(module, 'has_quiz', False)
                    else:  # New dict format
                        title = module.get('title', 'Untitled Module')
                        description = module.get('description')
                        learning_objectives = module.get('learning_objectives', []) or []
                        duration = module.get('duration', 'N/A')
                        difficulty = module.get('difficulty', 'intermediate')
                        has_quiz = module.get('has_quiz', False)

                    context_text += f"{i}. **{title}**\n"
                    if description:
                        context_text += f"   Description: {description}\n"
                    if learning_objectives:
                        objectives_text = ", ".join(learning_objectives[:3])
                        context_text += f"   Objectives: {objectives_text}\n"
                    context_text += f"   Duration: {duration} min\n"
                    context_text += f"   Difficulty: {difficulty}\n"
                    context_text += f"   Has Quiz: {'Yes' if has_quiz else 'No'}\n\n"

            # Add module-specific context
            if "module" in context_data and context_data["module"]:
                module = context_data["module"]
                # Handle both old module objects and new dict format
                if hasattr(module, 'title'):  # Old module object
                    title = module.title
                    module_id = module.id
                    description = module.description or 'No description'
                    duration = getattr(module, 'duration', 'N/A')
                    difficulty = getattr(module, 'difficulty', 'intermediate')
                    learning_style = getattr(module, 'learning_style', 'mixed')
                    learning_objectives = getattr(module, 'learning_objectives', [])
                else:  # New dict format
                    title = module.get('title', 'Untitled Module')
                    module_id = module.get('id')
                    description = module.get('description', 'No description')
                    duration = module.get('duration', 'N/A')
                    difficulty = module.get('difficulty', 'intermediate')
                    learning_style = module.get('learning_style', 'mixed')
                    learning_objectives = module.get('learning_objectives', [])

                context_text += f"CURRENT MODULE: **{title}** (ID: {module_id})\n"
                context_text += f"Description: {description}\n"
                context_text += f"Duration: {duration} minutes\n"
                context_text += f"Difficulty: {difficulty}\n"
                context_text += f"Learning Style: {learning_style}\n"

                if learning_objectives:
                    context_text += "Learning Objectives:\n"
                    for obj in learning_objectives:
                        context_text += f"  • {obj}\n"
                context_text += "\n"

            return context_text

        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return f"Error formatting context: {str(e)}"

    def extract_entity_references(self, question: str) -> Dict[str, Any]:
        """
        Extract entity references from question.

        Args:
            question: User's question

        Returns:
            Dict containing extracted entities
        """
        import re

        entities = {
            "module_number": None,
            "module_name": None,
            "quiz_number": None,
            "specific_topic": None
        }

        question_lower = question.lower()

        # Text to number mapping for written numbers
        text_numbers = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        # Look for written module numbers
        for text_num, num_val in text_numbers.items():
            patterns = [
                rf'the\s+{text_num}\s+module',
                rf'{text_num}\s+module',
                rf'module\s+{text_num}',
            ]
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    entities["module_number"] = num_val
                    break
            if entities["module_number"]:
                break

        # Look for numeric module patterns if no written number found
        if not entities["module_number"]:
            module_patterns = [
                r'module\s+(\d+)',
                r'(\d+)(?:st|nd|rd|th)\s+module',
                r'the\s+(\d+)(?:st|nd|rd|th)\s+module',
                r'module\s+number\s+(\d+)',
            ]
            for pattern in module_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    entities["module_number"] = int(match.group(1))
                    break

        # Look for quiz numbers with similar patterns
        for text_num, num_val in text_numbers.items():
            quiz_text_patterns = [
                rf'the\s+{text_num}\s+quiz',
                rf'{text_num}\s+quiz',
            ]
            for pattern in quiz_text_patterns:
                if re.search(pattern, question_lower):
                    entities["quiz_number"] = num_val
                    break
            if entities["quiz_number"]:
                break

        if not entities["quiz_number"]:
            quiz_patterns = [
                r'quiz\s+(\d+)',
                r'(\d+)(?:st|nd|rd|th)\s+quiz',
                r'the\s+(\d+)(?:st|nd|rd|th)\s+quiz',
            ]
            for pattern in quiz_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    entities["quiz_number"] = int(match.group(1))
                    break

        # Look for quoted names
        name_match = re.search(r'"([^"]*)"', question)
        if name_match:
            entities["module_name"] = name_match.group(1)

        return entities

    def analyze_question_complexity(self, question: str) -> str:
        """
        Analyze question complexity.

        Args:
            question: User's question

        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        question_lower = question.lower()

        simple_indicators = ["what is", "how many", "when", "where", "who"]
        if any(indicator in question_lower for indicator in simple_indicators):
            return "simple"

        complex_indicators = ["analyze", "compare", "explain why", "how does", "what are the differences"]
        if any(indicator in question_lower for indicator in complex_indicators):
            return "complex"

        return "medium"

    def _calculate_confidence(self, context_data: Dict[str, Any], context_type: ChatContext, response: str) -> float:
        """
        Calculate response confidence based on context and response quality.

        Args:
            context_data: Available context data
            context_type: Type of context used
            response: Generated response text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5

        # Increase confidence if good context is available
        if context_data and not context_data.get("error"):
            confidence += 0.3

        # Increase confidence if response contains relevant keywords
        if any(keyword in response.lower() for keyword in ["module", "quiz", "learning path", "progress"]):
            confidence += 0.1

        # Decrease confidence if there were context errors
        if context_data.get("error"):
            confidence -= 0.2

        return min(max(confidence, 0.0), 1.0)

    def validate_response(
        self,
        response: str,
        context_data: Dict[str, Any],
        user_location: UserContextLocation
    ) -> Dict[str, Any]:
        """
        Validate response and add metadata.

        Args:
            response: Generated response text
            context_data: Context data used
            user_location: User's current location

        Returns:
            Dict containing sources and location info
        """
        # Add sources based on location context
        sources = []
        if user_location.learning_path_id and "learning_path" in context_data:
            sources.append(f"Learning Path: {context_data['learning_path'].get('title', 'Current Path')}")
        if user_location.module_id and "module" in context_data:
            sources.append(f"Module: {context_data['module'].get('title', 'Current Module')}")
        if user_location.quiz_id and "quiz" in context_data:
            sources.append(f"Quiz: {context_data['quiz'].get('title', 'Current Quiz')}")

        # Add location context info
        location_info = {
            "current_location": user_location.location.value,
            "learning_path_id": user_location.learning_path_id,
            "module_id": user_location.module_id,
            "quiz_id": user_location.quiz_id,
            "team_id": user_location.team_id
        }

        return {
            "sources": sources,
            "location_info": location_info,
            "validation_complete": True
        }

    async def stream_response(self, response_text: str) -> AsyncGenerator[str, None]:
        """
        Stream response text word by word.

        Args:
            response_text: Complete response text to stream

        Yields:
            JSON strings containing streamed content
        """
        words = response_text.split()
        for word in words:
            yield json.dumps({"type": "content", "content": word + " "})
            await asyncio.sleep(0.03)


# Helper function to create user location from request parameters
def create_user_location(
    location: str,
    learning_path_id: Optional[int] = None,
    module_id: Optional[int] = None,
    quiz_id: Optional[int] = None,
    quiz_attempt_id: Optional[int] = None,
    team_id: Optional[str] = None
) -> UserContextLocation:
    """
    Create UserContextLocation from request parameters.

    Args:
        location: Location string
        learning_path_id: Optional learning path ID
        module_id: Optional module ID
        quiz_id: Optional quiz ID
        quiz_attempt_id: Optional quiz attempt ID
        team_id: Optional team ID

    Returns:
        UserContextLocation instance
    """
    try:
        location_enum = UserLocation(location)
    except ValueError:
        location_enum = UserLocation.DASHBOARD

    return UserContextLocation(
        location=location_enum,
        learning_path_id=learning_path_id,
        module_id=module_id,
        quiz_id=quiz_id,
        quiz_attempt_id=quiz_attempt_id,
        team_id=team_id
    )
