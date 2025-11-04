"""
AI Services - Quiz Generation Service
====================================

This module handles the generation of quizzes for learning modules using AI/LLM.
It creates comprehensive quizzes with multiple question types, detailed explanations,
and appropriate difficulty levels based on module content and learning objectives.

The quiz generation service:
1. Analyzes module content and learning objectives
2. Generates targeted questions based on module difficulty and subject
3. Creates appropriate question types (multiple choice, true/false, short answer)
4. Provides detailed explanations for each question
5. Persists generated quizzes to the database
6. Handles retries and error scenarios with comprehensive logging
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.models.quiz import QuestionType
from app.models.module import Module
from app.models.enums import DifficultyLevel
from app.repositories import quiz_repository
from app.schemas.core_schemas.quiz_schema import QuizCreate, QuestionCreate
from app.schemas.path_generation_schemas.quiz_generation_schema import QuizContentResponse, QuizGenerationMetrics

logger = get_logger(__name__)


class QuizGenerationService:
    """
    Service responsible for generating comprehensive quizzes using AI/LLM.

    This service orchestrates the complete quiz generation process from analyzing
    module content to persisting the generated quiz in the database. It provides
    robust error handling, retry mechanisms, and comprehensive logging.

    Key Responsibilities:
    1. Analyze module content and learning objectives
    2. Generate contextually appropriate quiz questions
    3. Validate generated content structure and quality
    4. Persist quizzes using the core quiz service
    5. Handle AI response parsing and error recovery
    6. Track generation metrics and performance
    """

    def __init__(self, db_session: AsyncSession = None):
        """
        Initialize the quiz generation service.

        Args:
            db_session: Optional database session for persistence operations
        """
        self.db = db_session
        self.logger = get_logger(__name__)

        # Initialize OpenAI client with configuration
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
        )

        # Set up generation configuration
        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": getattr(settings, "blueprint_max_tokens", 3000),
            "timeout": settings.llm_request_timeout,
        }

        # Service configuration
        self.max_retries = getattr(settings, 'quiz_generation_max_retries', 3)
        self.default_question_count = settings.default_quiz_questions

        self.logger.info("Quiz generation service initialized")

    async def generate_quiz_for_module(
            self,
            module_id: int,
            num_questions: Optional[int] = None,
            question_types: Optional[List[QuestionType]] = None
    ) -> QuizCreate:
        """
        Generate a complete quiz for a specific learning module.

        This is the main entry point for quiz generation. It orchestrates the entire
        process from module analysis to quiz persistence, with comprehensive error
        handling and performance tracking.

        Args:
            module_id: Unique identifier of the module to create a quiz for
            num_questions: Number of questions to generate (uses default if None)
            question_types: Types of questions to include (uses defaults if None)

        Returns:
            QuizCreate: Complete quiz schema ready for database persistence

        Raises:
            ValueError: If module not found or invalid parameters
            RuntimeError: If quiz generation fails after all retries
        """
        generation_start_time = datetime.now()
        self.logger.info(
            f"Starting quiz generation for module {module_id} with "
            f"{num_questions or self.default_question_count} questions"
        )

        try:
            # Check if quiz already exists for this module
            existing_quiz = await self._check_existing_quiz(module_id)
            if existing_quiz:
                self.logger.info(f"Quiz already exists for module {module_id}, skipping generation")
                return existing_quiz

            # Validate and prepare generation parameters
            validated_params = await self._prepare_generation_parameters(
                module_id, num_questions, question_types
            )
            module = validated_params['module']
            num_questions = validated_params['num_questions']
            question_types = validated_params['question_types']

            # Generate quiz content using AI with retry logic
            quiz_content = await self._generate_quiz_content_with_retries(
                module, num_questions, question_types
            )

            # Create quiz schema for database persistence
            quiz_data = await self._create_quiz_schema(
                module_id, quiz_content, num_questions
            )

            # Persist quiz to database using core service
            persisted_quiz = await self._persist_quiz_to_database(quiz_data)

            # Calculate and log performance metrics
            total_time = (datetime.now() - generation_start_time).total_seconds()
            await self._log_generation_metrics(
                generation_start_time, total_time, num_questions, True
            )

            self.logger.info(
                f"Successfully generated and persisted quiz for module {module_id} "
                f"in {total_time:.2f} seconds"
            )

            return quiz_data['quiz_schema']

        except Exception as e:
            total_time = (datetime.now() - generation_start_time).total_seconds()
            await self._log_generation_metrics(
                generation_start_time, total_time, num_questions or 0, False, str(e)
            )

            self.logger.error(
                f"Quiz generation failed for module {module_id}: {str(e)}"
            )
            raise


    async def _prepare_generation_parameters(
            self,
            module_id: int,
            num_questions: Optional[int],
            question_types: Optional[List[QuestionType]]
    ) -> Dict[str, Any]:
        """
        Validate and prepare parameters for quiz generation.

        Ensures all required data is available and parameters are within
        acceptable ranges before starting the generation process.

        Args:
            module_id: Module identifier to validate
            num_questions: Requested number of questions
            question_types: Requested question types

        Returns:
            Dict containing validated module and parameters

        Raises:
            ValueError: If module not found or parameters invalid
        """
        self.logger.debug(f"Preparing generation parameters for module {module_id}")

        # Validate module exists and retrieve data
        module = await self.db.execute(select(Module).filter(Module.id == module_id))
        module = module.scalar_one_or_none()
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")

        # Set default question count if not provided
        if num_questions is None:
            num_questions = self.default_question_count

        # Validate question count is within acceptable limits
        if num_questions < 1:
            raise ValueError("Number of questions must be at least 1")
        if num_questions > settings.max_quiz_questions:
            raise ValueError(
                f"Number of questions cannot exceed {settings.max_quiz_questions}"
            )

        # Set default question types if not provided
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]

        # Validate question types are supported
        valid_types = list(QuestionType)
        for q_type in question_types:
            if q_type not in valid_types:
                raise ValueError(f"Unsupported question type: {q_type}")

        self.logger.debug(
            f"Generation parameters prepared: {num_questions} questions, "
            f"types: {[qt.value for qt in question_types]}"
        )

        return {
            'module': module,
            'num_questions': num_questions,
            'question_types': question_types
        }

    async def _generate_quiz_content_with_retries(
            self,
            module: Module,
            num_questions: int,
            question_types: List[QuestionType]
    ) -> Dict[str, Any]:
        """
        Generate quiz content using AI with automatic retry logic.

        Implements robust retry mechanism for AI content generation,
        handling various failure scenarios like API timeouts, invalid
        responses, or parsing errors.

        Args:
            module: Module entity containing content and metadata
            num_questions: Number of questions to generate
            question_types: Types of questions to include

        Returns:
            Dict containing complete quiz content

        Raises:
            RuntimeError: If generation fails after all retry attempts
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    f"Quiz generation attempt {attempt + 1}/{self.max_retries} "
                    f"for module {module.id}"
                )

                ai_start_time = datetime.now()
                quiz_content = await self._generate_quiz_content(
                    module, num_questions, question_types
                )
                ai_duration = (datetime.now() - ai_start_time).total_seconds()

                # Validate generated content structure
                validated_content = await self._validate_quiz_content(
                    quiz_content, num_questions
                )

                self.logger.debug(
                    f"Quiz content generated successfully in {ai_duration:.2f} seconds"
                )

                return validated_content

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Quiz generation attempt {attempt + 1} failed: {str(e)}"
                )

                # Wait before retrying (exponential backoff)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.debug(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        error_msg = f"Quiz generation failed after {self.max_retries} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"

        self.logger.error(error_msg)
        raise RuntimeError(error_msg)

    async def _generate_quiz_content(
            self,
            module: Module,
            num_questions: int,
            question_types: List[QuestionType]
    ) -> Dict[str, Any]:
        """
        Generate complete quiz content using OpenAI API.

        Creates a comprehensive prompt based on module content and generates
        quiz questions with appropriate difficulty and subject matter alignment.

        Args:
            module: Module entity with content and learning objectives
            num_questions: Number of questions to generate
            question_types: Types of questions to include

        Returns:
            Dict containing quiz title, description, and questions

        Raises:
            ValueError: If AI response is invalid or unparseable
            RuntimeError: If API request fails
        """
        self.logger.debug(f"Generating quiz content for module '{module.title}'")

        # Extract module metadata and learning context
        learning_objectives = module.learning_objectives if module.learning_objectives else []
        difficulty = module.difficulty.value if module.difficulty else DifficultyLevel.INTERMEDIATE.value
        platform = getattr(module, 'platform_name', 'General')

        # Build comprehensive module context for AI prompt
        module_context = self._build_module_context(module, difficulty, platform)

        # Create detailed system prompt for quiz generation
        system_prompt = self._create_quiz_generation_prompt(
            module_context, num_questions, question_types, learning_objectives
        )

        # Create user prompt with specific instructions
        user_prompt = self._create_user_prompt(module, difficulty, num_questions, learning_objectives)

        try:
            # Make API request to OpenAI
            self.logger.debug("Sending quiz generation request to AI service")
            response = await self.client.chat.completions.create(
                model=self.generation_config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=self.generation_config['max_tokens'],
                timeout=self.generation_config['timeout']
            )

            # Extract response content first
            response_content = response.choices[0].message.content

            logger.info(f"Raw AI response: {response}")
            logger.info(f"Response choices: {response.choices}")
            logger.info(f"Response content: {response.choices[0].message.content if response.choices else 'No choices'}")

            # More robust validation - allow whitespace and formatting
            if not response_content or response_content.strip() == "":
                self.logger.error("AI returned empty response")
                self.logger.debug(f"Response choices: {len(response.choices) if response.choices else 0}")
                self.logger.debug(f"Response content type: {type(response_content)}")
                raise ValueError("Empty response from AI service")

            # Add debug logging to see what we actually received
            self.logger.debug(f"Raw AI response length: {len(response_content) if response_content else 0}")
            self.logger.debug(f"Raw AI response: {response_content[:500]}...")

            # Extract and parse JSON response
            quiz_data = self._extract_json_from_response(response_content)

            # Post-process and clean quiz data
            cleaned_quiz_data = self._post_process_quiz_data(quiz_data)

            self.logger.debug("Quiz content generation completed successfully")
            return cleaned_quiz_data

        except Exception as e:
            self.logger.error(f"AI quiz generation failed: {str(e)}")
            raise RuntimeError(f"AI service error: {str(e)}")

    def _build_module_context(self, module: Module, difficulty: str, platform: str) -> str:
        """
        Build comprehensive context string about the module for AI prompt.

        Creates a detailed description of the module that helps the AI understand
        what specific content should be tested in the quiz.

        Args:
            module: Module entity with content information
            difficulty: Difficulty level of the module
            platform: Platform where the module content originates

        Returns:
            Formatted string with module context
        """
        context_parts = [
            f"Module Title: {module.title}",
            f"Module Description: {module.description or 'No description provided'}",
            f"Difficulty Level: {difficulty}",
            f"Platform: {platform}",
            f"Duration: {module.duration} minutes"
        ]

        return "\n".join(context_parts)

    def _create_quiz_generation_prompt(
            self,
            module_context: str,
            num_questions: int,
            question_types: List[QuestionType],
            learning_objectives: List[str]
    ) -> str:
        """
        Create comprehensive system prompt for AI quiz generation.

        Builds detailed instructions for the AI to generate high-quality,
        contextually appropriate quiz questions.

        Args:
            module_context: Formatted module information
            num_questions: Number of questions to generate
            question_types: Types of questions to include
            learning_objectives: Learning objectives to focus on

        Returns:
            Complete system prompt for AI
        """
        objectives_text = json.dumps(learning_objectives) if learning_objectives else 'General knowledge and skills'
        question_types_text = [qt.value for qt in question_types]

        return f"""You are an expert educational assessment designer. Create a high-quality quiz that tests specific knowledge and skills from this learning module.

{module_context}

Learning Objectives: {objectives_text}

CRITICAL REQUIREMENTS:
1. Questions must be SPECIFIC to the module content, not generic
2. Test practical knowledge that students would learn from this exact module
3. Avoid vague questions like "What is an important concept in [module title]?"
4. Create questions that test understanding, application, and recall of specific facts/skills
5. Use the module title and description to infer what specific topics are covered

Question Guidelines:
- For technical subjects: Ask about specific techniques, tools, methods, or procedures
- For skill-based learning: Test practical application and step-by-step processes  
- For theoretical content: Test understanding of concepts, definitions, and relationships
- Always include detailed explanations that reinforce learning

Generate {num_questions} questions using these types: {question_types_text}

JSON Structure Required:
{{
    "title": "Specific quiz title related to module content",
    "description": "Brief description of what this quiz tests",
    "passing_score": 0.7,
    "questions": [
        {{
            "question_text": "Specific, detailed question about module content",
            "question_type": "multiple_choice|true_false|short_answer",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Correct answer text",
            "explanation": "Detailed explanation of why this is correct and what it teaches",
            "points": 1,
            "order_index": 0
        }}
    ]
}}

FORMATTING RULES:
- Use ONLY double quotes, never single quotes
- No trailing commas
- All strings must be properly escaped
- Numbers should not be quoted
- Return ONLY the JSON object, no other text

IMPORTANT: Return ONLY a valid JSON object with no additional text, thinking, or formatting.
"""

    def _create_user_prompt(
            self,
            module: Module,
            difficulty: str,
            num_questions: int,
            learning_objectives: List[str]
    ) -> str:
        """
        Create user prompt with specific generation instructions.

        Args:
            module: Module entity
            difficulty: Module difficulty level
            num_questions: Number of questions requested
            learning_objectives: Learning objectives to focus on

        Returns:
            User prompt string
        """
        objectives_text = json.dumps(learning_objectives,
                                     indent=2) if learning_objectives else 'General knowledge and skills'

        return f"""Generate a {difficulty} level quiz with {num_questions} questions for the module "{module.title}".

Focus on these learning objectives:
{objectives_text}

Make questions challenging but fair, with clear explanations. Return only the JSON object."""

    async def _validate_quiz_content(self, quiz_content: Dict[str, Any], expected_questions: int) -> Dict[str, Any]:
        """
        Validate generated quiz content structure and completeness.

        Ensures the AI-generated content meets all requirements and has
        proper structure before attempting database persistence.

        Args:
            quiz_content: Raw quiz content from AI
            expected_questions: Expected number of questions

        Returns:
            Validated and cleaned quiz content

        Raises:
            ValueError: If content validation fails
        """
        try:
            # Validate using Pydantic model
            validated_response = QuizContentResponse(**quiz_content)
            quiz_data = validated_response.model_dump()

            # Additional business validation
            if len(quiz_data['questions']) != expected_questions:
                raise ValueError(
                    f"Expected {expected_questions} questions, got {len(quiz_data['questions'])}"
                )

            # Validate each question has required fields
            for i, question in enumerate(quiz_data['questions']):
                self._validate_question_structure(question, i)

            self.logger.debug("Quiz content validation passed")
            return quiz_data

        except ValidationError as e:
            self.logger.error(f"Quiz content validation failed: {str(e)}")
            raise ValueError(f"Invalid quiz content structure: {str(e)}")

    def _validate_question_structure(self, question: Dict[str, Any], index: int) -> None:
        """
        Validate individual question structure and content.

        Args:
            question: Question data to validate
            index: Question index for error reporting

        Raises:
            ValueError: If question structure is invalid
        """
        required_fields = ['question_text', 'question_type', 'correct_answer', 'points']

        for field in required_fields:
            if field not in question or not question[field]:
                raise ValueError(f"Question {index + 1}: Missing required field '{field}'")

        # Validate question type
        if question['question_type'] not in [qt.value for qt in QuestionType]:
            raise ValueError(f"Question {index + 1}: Invalid question type '{question['question_type']}'")

        # Validate multiple choice questions have options
        if question['question_type'] == 'multiple_choice' and not question.get('options'):
            raise ValueError(f"Question {index + 1}: Multiple choice questions must have options")

        # Validate points are positive
        if question['points'] <= 0:
            raise ValueError(f"Question {index + 1}: Points must be positive")

    async def _create_quiz_schema(
            self,
            module_id: int,
            quiz_content: Dict[str, Any],
            num_questions: int
    ) -> Dict[str, Any]:
        """
        Create QuizCreate schema and questions data from generated content for database persistence.

        Transforms AI-generated content into the proper schema format
        required by the database persistence layer.

        Args:
            module_id: ID of the module this quiz belongs to
            quiz_content: Validated quiz content from AI
            num_questions: Number of questions in the quiz

        Returns:
            Dict containing quiz_schema and questions_data
        """
        self.logger.debug("Creating quiz schema for database persistence")

        # Create question schemas
        questions_data = []
        for i, q_data in enumerate(quiz_content['questions']):
            # Convert options list to dictionary format if it's a list
            options = q_data.get('options')
            if options and isinstance(options, list):
                # Convert list to dictionary with A, B, C, D labels
                options_dict = {}
                for idx, option in enumerate(options):
                    label = chr(65 + idx)  # A, B, C, D...
                    options_dict[label] = option
                options = options_dict

            question_data = {
                'question_text': q_data['question_text'],
                'question_type': QuestionType(q_data['question_type']),
                'options': options,
                'correct_answer': q_data['correct_answer'],
                'explanation': q_data.get('explanation'),
                'points': q_data.get('points', 1),
                'order_index': i
            }
            questions_data.append(question_data)

        # Calculate estimated completion time
        estimated_time = self._calculate_estimated_completion_time(num_questions)

        # Create quiz schema
        quiz_schema = QuizCreate(
            module_id=module_id,
            title=quiz_content['title'],
            description=quiz_content['description'],
            total_questions=num_questions,
            passing_score=quiz_content.get('passing_score', settings.default_quiz_passing_score),
            estimated_completion_time=estimated_time
        )

        self.logger.debug("Quiz schema created successfully")
        return {
            'quiz_schema': quiz_schema,
            'questions_data': questions_data
        }

    async def _persist_quiz_to_database(self, quiz_data: Dict[str, Any]) -> Any:
        """
        Persist generated quiz and questions to database using core quiz service.

        Uses the established core service for database operations,
        ensuring proper business logic and validation are applied.

        Args:
            quiz_data: Dict containing quiz_schema and questions_data

        Returns:
            Persisted quiz entity

        Raises:
            RuntimeError: If database persistence fails
        """
        if not self.db:
            raise RuntimeError("Database session not available for quiz persistence")

        try:
            self.logger.debug("Persisting quiz to database using core service")

            # Extract quiz schema and questions data
            quiz_schema = quiz_data['quiz_schema']
            questions_data = quiz_data['questions_data']

            # Create the quiz first
            persisted_quiz = await quiz_repository.create_quiz(self.db, quiz_schema)

            # Now create the questions with the correct quiz_id
            for question_data in questions_data:
                question_create = QuestionCreate(
                    quiz_id=persisted_quiz.id,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    options=question_data['options'],
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data['explanation'],
                    points=question_data['points'],
                    order_index=question_data['order_index']
                )
                await quiz_repository.create_question(self.db, question_create)

            self.logger.info(f"Quiz successfully persisted with ID: {persisted_quiz.id}")
            return persisted_quiz

        except Exception as e:
            self.logger.error(f"Quiz persistence failed: {str(e)}")
            raise RuntimeError(f"Failed to persist quiz: {str(e)}")

    def _calculate_estimated_completion_time(self, num_questions: int) -> int:
        """
        Calculate estimated completion time in minutes based on question count.

        Uses empirical data about average time spent per question type
        to provide realistic completion time estimates.

        Args:
            num_questions: Number of questions in the quiz

        Returns:
            Estimated completion time in minutes
        """
        # Base time: 1-1.5 minutes per question for reading, thinking, and answering
        base_time_per_question = 1.25
        estimated_minutes = int(num_questions * base_time_per_question)

        # Add buffer time for setup and review
        buffer_minutes = 2

        # Cap at reasonable limits (minimum 5 minutes, maximum 30 minutes)
        total_time = estimated_minutes + buffer_minutes
        return max(5, min(30, total_time))

    def _post_process_quiz_data(self, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and standardize quiz data after AI generation.

        Handles common formatting issues, standardizes data types,
        and applies business rules to the generated content.

        Args:
            quiz_data: Raw quiz data from AI

        Returns:
            Cleaned and processed quiz data
        """
        # Process questions
        if 'questions' in quiz_data:
            for question in quiz_data['questions']:
                # Convert boolean correct_answer to string for true/false questions
                if 'correct_answer' in question:
                    if isinstance(question['correct_answer'], bool):
                        question['correct_answer'] = str(question['correct_answer']).lower()

                # Ensure question_type is lowercase and valid
                if 'question_type' in question:
                    question['question_type'] = question['question_type'].lower()

                # Set default values if missing
                if 'points' not in question:
                    question['points'] = 1

                if 'order_index' not in question:
                    question['order_index'] = 0

                # Clean up options for non-multiple choice questions
                if question.get('question_type') != 'multiple_choice' and 'options' in question:
                    del question['options']

        # Set default passing score if not provided
        if 'passing_score' not in quiz_data:
            quiz_data['passing_score'] = settings.default_quiz_passing_score

        return quiz_data

    def _extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from AI response with multiple fallback strategies.
        Handles various JSON formatting issues that can occur with LLM responses.
        """
        import re
        import json
        from typing import Dict, Any

        self.logger.debug("Extracting JSON from AI response")

        # Helper function for cleaning JSON
        def clean_json_string(json_str: str) -> str:
            """Clean up common JSON formatting issues."""
            # Remove any text before the first {
            json_str = json_str[json_str.find('{'):]

            # Remove any text after the last }
            json_str = json_str[:json_str.rfind('}') + 1]

            # Fix common quote issues
            json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)

            # Fix trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

            # Fix single quotes to double quotes (basic approach)
            json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)  # Keys
            json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # Values

            return json_str

        # Helper function for fixing JSON issues
        def fix_json_issues(content: str) -> str:
            """Fix common JSON formatting issues in LLM responses."""
            # Extract the main JSON block
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in response")

            json_content = content[start_idx:end_idx + 1]

            # Fix common issues
            fixes = [
                # Fix trailing commas
                (r',(\s*[}\]])', r'\1'),
                # Fix unquoted keys
                (r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":'),
                # Fix single quotes around strings
                (r"'([^']*)'", r'"\1"'),
                # Fix escaped quotes issues
                (r'\\"', '"'),
                # Fix newlines in strings
                (r'"\s*\n\s*"', ''),
            ]

            for pattern, replacement in fixes:
                json_content = re.sub(pattern, replacement, json_content, flags=re.MULTILINE)

            return json_content

        # Helper function for fallback quiz
        def create_fallback_quiz() -> Dict[str, Any]:
            """Create a basic fallback quiz when AI generation fails."""
            return {
                "title": "Basic Quiz: Module Content",
                "description": "A basic quiz covering key concepts from this module. This quiz was automatically generated as a fallback.",
                "passing_score": 0.7,  # Fixed from 0.6 to 0.7 (70%)
                "questions": [
                    {
                        "question_text": "What is a key concept covered in this module?",
                        "question_type": "multiple_choice",
                        "options": [
                            "Important concept A from the module",
                            "Important concept B from the module",
                            "Important concept C from the module",
                            "None of the above"
                        ],
                        "correct_answer": "Important concept A from the module",
                        "explanation": "This question tests understanding of key concepts from the module. Please review the module content for specific details.",
                        "points": 1,
                        "order_index": 1
                    },
                    {
                        "question_text": "Based on this module, which statement is most accurate?",
                        "question_type": "multiple_choice",
                        "options": [
                            "The module covers fundamental concepts in the subject area",
                            "The module is only for advanced learners",
                            "The module contains outdated information",
                            "The module is not relevant to the learning path"
                        ],
                        "correct_answer": "The module covers fundamental concepts in the subject area",
                        "explanation": "This module is designed to provide foundational knowledge in its subject area.",
                        "points": 1,
                        "order_index": 2
                    },
                    {
                        "question_text": "What should you do after completing this module?",
                        "question_type": "multiple_choice",
                        "options": [
                            "Practice the concepts learned",
                            "Skip to an unrelated topic",
                            "Forget everything learned",
                            "Avoid applying the knowledge"
                        ],
                        "correct_answer": "Practice the concepts learned",
                        "explanation": "Practicing and applying what you've learned helps reinforce the concepts and improve retention.",
                        "points": 1,
                        "order_index": 3
                    }
                ]
            }

        # Strategy 1: Try direct JSON parsing
        try:
            return json.loads(response_content.strip())
        except json.JSONDecodeError:
            self.logger.debug("Direct JSON parsing failed, trying cleanup strategies")

        # Strategy 2: Extract JSON from code blocks
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
        except json.JSONDecodeError:
            self.logger.debug("Code block JSON extraction failed")

        # Strategy 3: Find JSON between braces with cleanup
        try:
            # Find the main JSON object
            brace_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
            matches = re.findall(brace_pattern, response_content, re.DOTALL)

            for match in matches:
                try:
                    # Clean up common JSON formatting issues
                    cleaned_json = clean_json_string(match)
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    continue

            self.logger.warning("Failed to parse JSON from brace extraction")

        except Exception as e:
            self.logger.error(f"Brace extraction failed: {str(e)}")

        # Strategy 4: Try to fix common JSON issues and parse
        try:
            fixed_json = fix_json_issues(response_content)
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass

        # Strategy 5: Create fallback quiz if all parsing fails
        self.logger.error("All JSON extraction methods failed, creating fallback quiz")
        return create_fallback_quiz()


    async def _log_generation_metrics(
            self,
            start_time: datetime,
            total_time: float,
            questions_count: int,
            success: bool,
            error_message: Optional[str] = None
    ) -> None:
        """
        Log comprehensive metrics about quiz generation performance.

        Tracks generation performance for monitoring and optimization purposes.
        Metrics can be used for alerting, performance analysis, and service improvement.

        Args:
            start_time: When generation started
            total_time: Total time taken in seconds
            questions_count: Number of questions generated
            success: Whether generation succeeded
            error_message: Error message if generation failed
        """
        metrics = QuizGenerationMetrics(
            generation_start_time=start_time,
            ai_request_time_seconds=0.0,  # Would be tracked separately in production
            json_parsing_time_seconds=0.0,  # Would be tracked separately in production
            database_persistence_time_seconds=0.0,  # Would be tracked separately in production
            total_generation_time_seconds=total_time,
            questions_generated=questions_count,
            ai_model_used=settings.llm_model,
            generation_success=success,
            retry_count=0,  # Would be tracked during retries
            error_message=error_message
        )

        if success:
            self.logger.info(
                f"Quiz generation metrics - Success: {total_time:.2f}s total, "
                f"{questions_count} questions, model: {settings.llm_model}"
            )
        else:
            self.logger.error(
                f"Quiz generation metrics - Failed: {total_time:.2f}s total, "
                f"error: {error_message}, model: {settings.llm_model}"
            )

    async def _check_existing_quiz(self, module_id: int) -> Optional[QuizCreate]:
        """
        Check if a quiz already exists for the given module.

        Args:
            module_id: ID of the module to check

        Returns:
            QuizCreate: Existing quiz data if found, None otherwise
        """
        try:
            # Check if quiz exists using repository
            from app.repositories import quiz_repository

            existing_quiz = await quiz_repository.get_quiz_by_module_id(self.db, module_id)

            if existing_quiz:
                self.logger.info(f"Found existing quiz {existing_quiz.id} for module {module_id}")

                # Convert existing quiz to QuizCreate format for consistency
                # Note: QuizCreate doesn't include questions, they are created separately
                return QuizCreate(
                    module_id=existing_quiz.module_id,
                    title=existing_quiz.title,
                    description=existing_quiz.description,
                    total_questions=existing_quiz.total_questions,
                    passing_score=existing_quiz.passing_score,
                    estimated_completion_time=existing_quiz.estimated_completion_time
                )

            return None

        except Exception as e:
            self.logger.warning(f"Error checking for existing quiz for module {module_id}: {str(e)}")
            # If we can't check, assume no quiz exists and continue with generation
            return None
