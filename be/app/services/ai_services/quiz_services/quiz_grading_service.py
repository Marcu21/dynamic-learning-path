# =============================================================================
# QUIZ GRADING SERVICE
# =============================================================================

"""
AI Services - Quiz Grading Service
==================================

This module handles comprehensive grading of quiz attempts using AI-powered
analysis for subjective questions and rule-based grading for objective questions.
It provides detailed feedback, calculates scores, and manages skill point awards.

The quiz grading service:
1. Grades objective questions using exact matching with normalization
2. Uses AI to evaluate subjective answers with partial credit
3. Generates personalized feedback for each question and overall performance
4. Calculates final scores and determines pass/fail status
5. Awards skill points for first-time quiz completions
6. Handles various question types with appropriate grading strategies
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from openai import AsyncOpenAI
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.utils import get_current_utc_plus_2_time, convert_utc_plus_2_to_utc
from app.models.quiz import QuizAttempt, Answer, QuizStatus
from app.schemas.core_schemas.quiz_schema import QuizSubmission
from app.services.ai_services.quiz_services.quiz_generation_service import QuizGenerationService
from app.schemas.path_generation_schemas.quiz_generation_schema import QuizGradingMetrics
from app.repositories import progress_repository

logger = get_logger(__name__)


class QuizGradingService:
    """
    Service responsible for comprehensive quiz grading using rule-based and AI methods.

    This service orchestrates the complete grading process from individual answer
    evaluation to final score calculation and feedback generation. It handles
    different question types appropriately and provides detailed analytics.

    Key Responsibilities:
    1. Grade objective questions with intelligent answer matching
    2. Use AI for subjective question evaluation with partial credit
    3. Generate constructive feedback for each answer
    4. Calculate overall scores and determine pass/fail status
    5. Award skill points for first-time completions
    6. Generate personalized overall feedback
    7. Track grading performance metrics
    """

    def __init__(self, db_session: AsyncSession = None):
        """
        Initialize the quiz grading service.

        Args:
            db_session: Database session for persistence operations
        """
        self.db = db_session
        self.logger = get_logger(__name__)

        # Initialize OpenAI client for subjective question grading
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
        )

        # Initialize LLM client configuration
        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": getattr(settings, "blueprint_max_tokens", 300),
            "timeout": settings.llm_request_timeout,
        }

        # Grading configuration
        self.partial_credit_threshold = getattr(settings, 'partial_credit_threshold', 0.5)

        self.logger.info("Quiz grading service initialized")

    async def grade_quiz_attempt(self, attempt_id: int, db_session: AsyncSession = None) -> Dict[str, Any]:
        """
        Grade a complete quiz attempt and provide comprehensive feedback.

        This is the main entry point for quiz grading. It orchestrates the entire
        grading process including individual question grading, score calculation,
        skill point awards, and feedback generation.

        Args:
            attempt_id: Unique identifier of the quiz attempt to grade
            db_session: Optional database session to use. If not provided, uses self.db

        Returns:
            Dict containing complete grading results, scores, and feedback

        Raises:
            ValueError: If attempt not found or in invalid state
            RuntimeError: If grading process fails
        """
        grading_metrics = QuizGradingMetrics()

        self.logger.info(f"Starting comprehensive grading for quiz attempt {attempt_id}")

        # Use provided session or fall back to instance session
        db = db_session or self.db
        if not db:
            raise ValueError("No database session available for grading")

        try:
            # Validate attempt exists and retrieve with related data
            attempt = await self._load_quiz_attempt_with_data(attempt_id, db)

            # Grade each individual answer
            grading_results = await self._grade_all_answers(attempt, grading_metrics, db)

            # Calculate overall scores and determine pass/fail
            score_data = await self._calculate_overall_scores(attempt, grading_results)

            # Handle skill points award for first-time passes
            skill_points_awarded = await self._handle_skill_points_award(attempt, score_data['passed'], db)

            # Generate comprehensive overall feedback
            overall_feedback = await self._generate_comprehensive_feedback(
                attempt, grading_results, score_data['score']
            )

            # Update attempt with final results
            await self._update_attempt_with_results(
                attempt, score_data, overall_feedback, grading_results, db
            )

            # Prepare final response
            final_results = {
                "attempt_id": attempt_id,
                "score": score_data['score'],
                "passed": score_data['passed'],
                "total_points": score_data['total_points'],
                "earned_points": score_data['earned_points'],
                "feedback": overall_feedback,
                "question_results": grading_results,
                "skill_points_awarded": skill_points_awarded,
                "grading_time_seconds": (datetime.now() - grading_metrics.grading_start_time).total_seconds()
            }

            # Log grading metrics
            await self._log_grading_metrics(grading_metrics, len(grading_results), True)

            self.logger.info(
                f"Quiz attempt {attempt_id} graded successfully - "
                f"Score: {score_data['score']:.1%}, Passed: {score_data['passed']}"
            )

            return final_results

        except Exception as e:
            grading_metrics.grading_success = False
            grading_metrics.error_message = str(e)
            await self._log_grading_metrics(grading_metrics, 0, False)

            self.logger.error(f"Quiz grading failed for attempt {attempt_id}: {str(e)}")
            raise RuntimeError(f"Grading failed: {str(e)}")

    async def submit_quiz_attempt(self, db: AsyncSession, attempt_id: int, submission: QuizSubmission) -> Dict[str, Any]:
        """
        Submit and grade a quiz attempt with comprehensive error handling.

        This method is maintained for backward compatibility but delegates
        the actual grading to the QuizGradingService for separation of concerns.

        Args:
            db: Database session
            attempt_id: ID of the quiz attempt to submit
            submission: Quiz submission data with answers

        Returns:
            Dict containing grading results and performance data

        Raises:
            ValueError: If attempt not found or in invalid state
            SQLAlchemyError: If database operations fail
        """
        self.logger.info(f"Submitting quiz attempt {attempt_id}")

        try:
            # Validate attempt exists and is in correct state
            result = await db.execute(select(QuizAttempt).filter(QuizAttempt.id == attempt_id))
            attempt = result.scalar_one_or_none()
            if not attempt:
                raise ValueError(f"Quiz attempt with ID {attempt_id} not found")

            if attempt.status != QuizStatus.DRAFT:
                raise ValueError("Quiz attempt is not in draft status")

            # Save submitted answers to database
            for answer_data in submission.answers:
                answer = Answer(
                    attempt_id=attempt_id,
                    question_id=answer_data.question_id,
                    answer_text=answer_data.submitted_answer
                )
                db.add(answer)

            # Flush to ensure answers get IDs before updating attempt
            await db.flush()

            # Update attempt status and completion timing
            attempt.status = QuizStatus.COMPLETED
            completion_utc_plus_2_time = get_current_utc_plus_2_time()
            completion_utc_time = convert_utc_plus_2_to_utc(completion_utc_plus_2_time)
            attempt.completed_at = completion_utc_time

            # Calculate time taken in seconds with timezone handling
            if attempt.started_at:
                started_at = attempt.started_at
                completed_at = attempt.completed_at

                # Ensure both timestamps are timezone-aware for accurate calculation
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)

                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)

                time_diff = completed_at - started_at
                attempt.time_taken = int(time_diff.total_seconds())
                self.logger.info(f"Quiz attempt {attempt_id} took {attempt.time_taken} seconds")

            # Commit changes before grading
            await db.commit()

            # Delegate grading to specialized service using the same database session
            grading_results = await self.grade_quiz_attempt(attempt_id, db_session=db)

            self.logger.info(f"Quiz attempt {attempt_id} submitted and graded successfully")
            return grading_results

        except SQLAlchemyError as e:
            self.logger.error(f"Database error submitting quiz attempt: {str(e)}")
            await db.rollback()
            raise ValueError(f"Failed to submit quiz attempt: {str(e)}")

    async def _load_quiz_attempt_with_data(self, attempt_id: int, db: AsyncSession = None) -> QuizAttempt:
        """
        Load quiz attempt with all necessary related data for grading.

        Efficiently loads the attempt along with answers, questions, and quiz
        metadata to minimize database queries during grading.

        Args:
            attempt_id: ID of the attempt to load
            db: Database session to use. If not provided, uses self.db

        Returns:
            QuizAttempt entity with related data loaded

        Raises:
            ValueError: If attempt not found
        """
        from sqlalchemy.orm import selectinload
        
        # Use provided session or fall back to instance session
        session = db or self.db
        
        result = await session.execute(
            select(QuizAttempt)
            .options(
                selectinload(QuizAttempt.answers).selectinload(Answer.question),
                selectinload(QuizAttempt.quiz)
            )
            .filter(QuizAttempt.id == attempt_id)
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise ValueError(f"Quiz attempt with ID {attempt_id} not found")

        # Ensure related data is loaded
        if not attempt.answers:
            self.logger.warning(f"No answers found for attempt {attempt_id}")

        self.logger.debug(f"Loaded attempt {attempt_id} with {len(attempt.answers)} answers")
        return attempt

    async def _grade_all_answers(
            self,
            attempt: QuizAttempt,
            metrics: QuizGradingMetrics,
            db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Grade all answers in the quiz attempt using appropriate methods.

        Uses a hybrid approach: objective questions are graded using rule-based methods,
        while all subjective questions are graded together in a single AI request for efficiency.

        Args:
            attempt: Quiz attempt with answers to grade
            metrics: Metrics tracking object
            db: Database session to use. If not provided, uses self.db

        Returns:
            List of grading results for each answer
        """
        # Use provided session or fall back to instance session
        session = db or self.db
        
        grading_results = []
        subjective_answers = []
        objective_answers = []

        self.logger.debug(f"Grading {len(attempt.answers)} answers")

        # Separate answers by question type
        for answer in attempt.answers:
            question = answer.question
            if question.question_type.value in ["multiple_choice", "true_false"]:
                objective_answers.append(answer)
            else:
                subjective_answers.append(answer)

        # Grade objective questions individually (rule-based)
        for answer in objective_answers:
            try:
                grade_result = await self._grade_objective_answer(answer)
                grading_results.append(grade_result)
                metrics.objective_questions_graded += 1

                # Update answer entity with grading results
                answer.is_correct = grade_result['is_correct']
                answer.points_earned = grade_result['points_earned']
                answer.ai_feedback = grade_result['feedback']

            except Exception as e:
                self.logger.error(f"Failed to grade objective answer for question {answer.question_id}: {str(e)}")
                fallback_result = {
                    "question_id": answer.question_id,
                    "is_correct": False,
                    "points_earned": 0,
                    "feedback": "Unable to grade this answer automatically. Please review with instructor."
                }
                grading_results.append(fallback_result)

        # Grade all subjective questions together in a single AI request
        if subjective_answers:
            try:
                ai_start_time = datetime.now()
                subjective_results = await self._grade_subjective_answers_batch(subjective_answers)
                ai_duration = (datetime.now() - ai_start_time).total_seconds()
                metrics.ai_grading_time_seconds += ai_duration
                metrics.subjective_questions_graded += len(subjective_answers)

                # Update answer entities with AI grading results
                for i, answer in enumerate(subjective_answers):
                    if i < len(subjective_results):
                        result = subjective_results[i]
                        answer.is_correct = result['is_correct']
                        answer.points_earned = result['points_earned']
                        answer.ai_feedback = result['feedback']
                        grading_results.append(result)
                    else:
                        # Fallback if AI didn't return enough results
                        fallback_result = {
                            "question_id": answer.question_id,
                            "is_correct": False,
                            "points_earned": 0,
                            "feedback": "Unable to grade this answer automatically. Please review with instructor."
                        }
                        grading_results.append(fallback_result)

            except Exception as e:
                self.logger.error(f"Failed to grade subjective answers in batch: {str(e)}")
                # Create fallback results for all subjective questions
                for answer in subjective_answers:
                    fallback_result = {
                        "question_id": answer.question_id,
                        "is_correct": False,
                        "points_earned": 0,
                        "feedback": "Unable to grade this answer automatically. Please review with instructor."
                    }
                    grading_results.append(fallback_result)

        # Commit all answer updates to database
        await session.commit()

        self.logger.debug(f"Completed grading all answers")
        return grading_results

    async def _grade_subjective_answers_batch(self, answers: List[Answer]) -> List[Dict[str, Any]]:
        """
        Grade multiple subjective answers in a single AI request for efficiency.

        Leverages AI to evaluate all open-ended responses at once, providing partial credit
        and detailed feedback for subjective questions in batch.

        Args:
            answers: List of Answer entities for subjective questions

        Returns:
            List of AI grading results for each answer
        """
        if not answers:
            return []

        # Create comprehensive batch grading prompt
        system_prompt = self._create_batch_subjective_grading_prompt(answers)
        user_prompt = self._create_batch_user_prompt(answers)

        try:
            # Request AI grading with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.generation_config['model'],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=self.generation_config['max_tokens'] * len(answers),  # Scale tokens with number of questions
                ),
                timeout=self.generation_config['timeout'] * 2  # Give more time for batch processing
            )

            # Parse AI response
            ai_result = json.loads(response.choices[0].message.content)

            # Validate and process batch AI response
            return self._validate_batch_ai_grading_result(ai_result, answers)

        except asyncio.TimeoutError:
            self.logger.warning(f"AI batch grading timeout for {len(answers)} questions")
            return [self._create_fallback_grading_result(answer.question) for answer in answers]
        except Exception as e:
            self.logger.error(f"AI batch grading failed for {len(answers)} questions: {str(e)}")
            return [self._create_fallback_grading_result(answer.question) for answer in answers]

    def _create_batch_subjective_grading_prompt(self, answers: List[Answer]) -> str:
        """
        Create comprehensive prompt for AI-based batch subjective grading.

        Args:
            answers: List of Answer entities to create grading prompt for

        Returns:
            System prompt for AI batch grading
        """
        questions_info = []
        for i, answer in enumerate(answers, 1):
            question = answer.question
            questions_info.append(f"""
Question {i}:
- ID: {question.id}
- Text: {question.question_text}
- Correct Answer: {question.correct_answer}
- Max Points: {question.points}""")

        questions_text = "\n".join(questions_info)

        return f"""You are an expert educator grading multiple quiz answers in batch. 

QUESTIONS TO GRADE:
{questions_text}

Grade all student answers and provide constructive feedback for each.
Return JSON array with one object per question in the same order: 
[
  {{
    "question_id": {answers[0].question.id},
    "is_correct": true/false,
    "points_earned": 0-{answers[0].question.points},
    "feedback": "Detailed feedback for the student"
  }},
  // ... one object for each question
]

GRADING CRITERIA:
- Award full points for completely correct answers
- Award partial points for partially correct answers (minimum 50% understanding)
- Award no points for incorrect answers
- Provide constructive feedback explaining the grade
- Focus on understanding rather than exact wording
- Be consistent in grading standards across all questions
- Ensure the response contains exactly {len(answers)} grading objects in the same order as the questions"""

    def _create_batch_user_prompt(self, answers: List[Answer]) -> str:
        """
        Create user prompt containing all student answers for batch grading.

        Args:
            answers: List of Answer entities

        Returns:
            User prompt with all student answers
        """
        answers_text = []
        for i, answer in enumerate(answers, 1):
            answers_text.append(f"Question {i} Student Answer: {answer.answer_text}")

        return "Grade these student answers:\n\n" + "\n\n".join(answers_text)

    def _validate_batch_ai_grading_result(self, ai_result: List[Dict[str, Any]], answers: List[Answer]) -> List[Dict[str, Any]]:
        """
        Validate and sanitize AI batch grading results.

        Args:
            ai_result: Raw AI grading response (should be a list)
            answers: List of Answer entities for validation context

        Returns:
            List of validated grading results
        """
        try:
            if not isinstance(ai_result, list):
                self.logger.error("AI batch grading result is not a list")
                return [self._create_fallback_grading_result(answer.question) for answer in answers]

            if len(ai_result) != len(answers):
                self.logger.warning(f"AI returned {len(ai_result)} results but expected {len(answers)}")
                # Pad with fallback results if needed
                while len(ai_result) < len(answers):
                    ai_result.append({})

            validated_results = []
            for i, (result, answer) in enumerate(zip(ai_result, answers)):
                try:
                    # Ensure required fields exist
                    is_correct = bool(result.get('is_correct', False))
                    points_earned = float(result.get('points_earned', 0))
                    feedback = str(result.get('feedback', 'No feedback provided'))
                    question_id = result.get('question_id', answer.question.id)

                    # Validate points are within acceptable range
                    max_points = float(answer.question.points)
                    points_earned = max(0, min(points_earned, max_points))

                    validated_results.append({
                        "question_id": question_id,
                        "is_correct": is_correct,
                        "points_earned": points_earned,
                        "feedback": feedback
                    })

                except Exception as e:
                    self.logger.error(f"AI result validation failed for question {i}: {str(e)}")
                    validated_results.append(self._create_fallback_grading_result(answer.question))

            return validated_results

        except Exception as e:
            self.logger.error(f"AI batch result validation failed: {str(e)}")
            return [self._create_fallback_grading_result(answer.question) for answer in answers]

    async def _calculate_overall_scores(
            self,
            attempt: QuizAttempt,
            grading_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate overall quiz scores and determine pass/fail status.

        Args:
            attempt: Quiz attempt entity
            grading_results: List of individual question grading results

        Returns:
            Dict containing score calculations
        """
        total_points = sum(answer.question.points for answer in attempt.answers)
        earned_points = sum(result['points_earned'] for result in grading_results)

        # Calculate score with precision handling
        score = (earned_points / total_points) if total_points > 0 else 0

        # Get the quiz passing score and normalize it
        quiz_passing_score = attempt.quiz.passing_score

        # Safety check: if passing score seems to be a percentage (>1), convert to decimal
        if quiz_passing_score > 1:
            quiz_passing_score = quiz_passing_score / 100
            logger.warning(f"Quiz {attempt.quiz.id} has passing_score > 1 ({attempt.quiz.passing_score}), converted to {quiz_passing_score}")

        # Ensure passing score is reasonable (between 0.5 and 1.0)
        elif quiz_passing_score < 0.5 or quiz_passing_score > 1:
            logger.error(f"Quiz {attempt.quiz.id} has invalid passing_score: {attempt.quiz.passing_score}, defaulting to 0.7")
            quiz_passing_score = 0.7  # Default to 70%

        # Determine pass/fail with small tolerance for floating point precision
        passed = score >= (quiz_passing_score - 0.001)

        # Add debugging to identify the passing score issue
        logger.warning(f"PASSING SCORE DEBUG: earned_points={earned_points}, total_points={total_points}, score={score:.3f}")
        logger.warning(f"PASSING SCORE DEBUG: original_quiz_passing_score={attempt.quiz.passing_score}, normalized_passing_score={quiz_passing_score}, calculated_score={score:.3f}, passed={passed}")

        # Also log the quiz details for debugging
        logger.warning(f"QUIZ DEBUG: Quiz ID={attempt.quiz.id}, Title='{attempt.quiz.title}', Default passing_score should be 0.7 (70%)")

        return {
            'total_points': total_points,
            'earned_points': earned_points,
            'score': score,
            'passed': passed
        }

    async def _handle_skill_points_award(self, attempt: QuizAttempt, passed: bool, db: AsyncSession = None) -> bool:
        """
        Handle skill points award for first-time quiz completions.

        Awards skill points only for the first successful completion of each quiz
        to prevent point farming and ensure fair progression.

        Args:
            attempt: Quiz attempt entity
            passed: Whether the attempt was successful
            db: Database session to use. If not provided, uses self.db

        Returns:
            True if skill points were awarded, False otherwise
        """
        # Use provided session or fall back to instance session
        session = db or self.db
        
        skill_points_awarded = False

        if passed and not attempt.skill_points_awarded:
            # Check if user has already passed this quiz before
            count_result = await session.execute(select(func.count()).select_from(
                select(QuizAttempt).filter(
                    QuizAttempt.user_id == attempt.user_id,
                    QuizAttempt.quiz_id == attempt.quiz_id,
                    QuizAttempt.passed == True,
                    QuizAttempt.id != attempt.id
                ).subquery()
            ))
            previous_passed_attempts = count_result.scalar()

            if previous_passed_attempts == 0:
                # This is the first time the user passed this quiz
                attempt.skill_points_awarded = True
                skill_points_awarded = True
                
                # Calculate skill points based on quiz difficulty (you can adjust this logic)
                skill_points = settings.default_quiz_skill_points  # Use configured quiz skill points
                
                # Actually award the skill points to the user
                try:
                    await progress_repository.award_quiz_skill_points(
                        db=session,
                        user_id=attempt.user_id,
                        quiz_id=attempt.quiz_id,
                        score=skill_points
                    )
                    self.logger.info(
                        f"Successfully awarded {skill_points} skill points to user {attempt.user_id} for quiz {attempt.quiz_id}"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to award skill points to user {attempt.user_id}: {str(e)}")
                    # Don't raise the exception to avoid breaking the quiz grading flow
                
                self.logger.info(
                    f"Awarding skill points for first-time quiz pass: "
                    f"user {attempt.user_id}, quiz {attempt.quiz_id}"
                )
            else:
                self.logger.info(
                    f"User already passed this quiz before, no skill points awarded: "
                    f"user {attempt.user_id}, quiz {attempt.quiz_id}"
                )

        return skill_points_awarded

    async def _generate_comprehensive_feedback(
            self,
            attempt: QuizAttempt,
            grading_results: List[Dict[str, Any]],
            score: float
    ) -> str:
        """
        Generate comprehensive overall feedback for the quiz attempt.

        Creates personalized feedback that combines performance statistics
        with AI-generated insights and encouragement.

        Args:
            attempt: Quiz attempt entity
            grading_results: List of question grading results
            score: Overall quiz score

        Returns:
            Comprehensive feedback string
        """
        # Generate performance summary
        correct_count = sum(1 for result in grading_results if result['is_correct'])
        total_questions = len(grading_results)

        performance_summary = f"You answered {correct_count} out of {total_questions} questions correctly ({score:.1%})."

        if score >= attempt.quiz.passing_score:
            performance_summary += " Congratulations! You passed the quiz."
        else:
            performance_summary += f" You need {attempt.quiz.passing_score:.1%} to pass. Keep studying and try again!"

        # Generate AI-powered personalized feedback
        try:
            ai_feedback = await self._generate_ai_feedback(attempt, performance_summary, score)
            return f"{performance_summary}\n\n{ai_feedback}"
        except Exception as e:
            self.logger.warning(f"AI feedback generation failed: {str(e)}")
            return performance_summary

    async def _generate_ai_feedback(
            self,
            attempt: QuizAttempt,
            performance_summary: str,
            score: float
    ) -> str:
        """
        Generate AI-powered personalized feedback for the quiz attempt.

        Uses AI to create encouraging, constructive feedback that provides
        specific guidance for improvement and acknowledges achievements.

        Args:
            attempt: Quiz attempt entity
            performance_summary: Basic performance statistics
            score: Overall quiz score

        Returns:
            AI-generated personalized feedback
        """
        system_prompt = f"""Generate personalized feedback for a quiz attempt.

Performance: {performance_summary}
Quiz Topic: {attempt.quiz.title}
Pass/Fail: {'Passed' if score >= attempt.quiz.passing_score else 'Failed'}

Provide encouraging, constructive feedback (2-3 sentences) focusing on:
- Acknowledgment of performance
- Areas for improvement
- Encouragement for continued learning

Keep the tone positive and motivational."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": performance_summary}
                ],
                max_completion_tokens=200
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"AI feedback generation failed: {str(e)}")
            return "Keep up the great work! Review the explanations and continue learning."

    async def _update_attempt_with_results(
            self,
            attempt: QuizAttempt,
            score_data: Dict[str, Any],
            overall_feedback: str,
            grading_results: List[Dict[str, Any]],
            db: AsyncSession = None
    ) -> None:
        """
        Update quiz attempt entity with final grading results.

        Persists all grading results, scores, and feedback to the database
        while maintaining data consistency.

        Args:
            attempt: Quiz attempt entity to update
            score_data: Calculated scores and pass/fail status
            overall_feedback: Generated overall feedback
            grading_results: Individual question results
            db: Database session to use. If not provided, uses self.db
        """
        # Use provided session or fall back to instance session
        session = db or self.db
        
        try:
            # Update attempt with final results
            attempt.total_points = score_data['total_points']
            attempt.earned_points = score_data['earned_points']
            attempt.score = score_data['score']
            attempt.passed = score_data['passed']
            attempt.feedback = overall_feedback

            # Commit all changes to database
            await session.commit()

            self.logger.debug(f"Updated attempt {attempt.id} with final grading results")

        except Exception as e:
            self.logger.error(f"Failed to update attempt with results: {str(e)}")
            await session.rollback()
            raise RuntimeError(f"Failed to save grading results: {str(e)}")

    async def _log_grading_metrics(
            self,
            metrics: QuizGradingMetrics,
            questions_graded: int,
            success: bool
    ) -> None:
        """
        Log comprehensive metrics about quiz grading performance.

        Tracks grading performance for monitoring, alerting, and optimization.
        Metrics help identify bottlenecks and ensure service quality.

        Args:
            metrics: Grading metrics object with performance data
            questions_graded: Total number of questions graded
            success: Whether grading completed successfully
        """
        metrics.total_grading_time_seconds = (
                datetime.now() - metrics.grading_start_time
        ).total_seconds()

        if success:
            self.logger.info(
                f"Quiz grading metrics - Success: {metrics.total_grading_time_seconds:.2f}s total, "
                f"{questions_graded} questions ({metrics.objective_questions_graded} objective, "
                f"{metrics.subjective_questions_graded} subjective), "
                f"AI time: {metrics.ai_grading_time_seconds:.2f}s"
            )
        else:
            self.logger.error(
                f"Quiz grading metrics - Failed: {metrics.total_grading_time_seconds:.2f}s total, "
                f"error: {metrics.error_message}"
            )

    async def _grade_objective_answer(self, answer: Answer) -> Dict[str, Any]:
        """
        Grade objective questions using intelligent string matching.

        Implements sophisticated answer comparison that handles common
        variations in student responses while maintaining grading accuracy.

        Args:
            answer: Answer entity for objective question

        Returns:
            Dict containing grading results
        """
        question = answer.question

        # Normalize both answers for intelligent comparison
        user_answer_normalized = self._normalize_answer_text(answer.answer_text)
        correct_answer_normalized = self._normalize_answer_text(question.correct_answer)

        # Determine if answer is correct using multiple matching strategies
        is_correct = self._answers_match(user_answer_normalized, correct_answer_normalized)

        # Calculate points earned
        points_earned = question.points if is_correct else 0

        # Generate appropriate feedback
        if is_correct:
            feedback = "Correct! " + (question.explanation or "Good job!")
        else:
            feedback = (
                    f"Incorrect. The correct answer is: {question.correct_answer}. " +
                    (question.explanation or "Please review this topic.")
            )

        return {
            "question_id": question.id,
            "is_correct": is_correct,
            "points_earned": points_earned,
            "feedback": feedback
        }

    def _normalize_answer_text(self, text: str) -> str:
        """
        Normalize answer text for consistent comparison.

        Removes common variations that don't affect answer correctness
        such as punctuation, case differences, and extra whitespace.

        Args:
            text: Raw answer text to normalize

        Returns:
            Normalized text suitable for comparison
        """
        if not text:
            return ""

        import re

        # Convert to lowercase
        normalized = text.strip().lower()

        # Remove leading option letters and punctuation (e.g., 'c)', 'c.', 'c:')
        normalized = re.sub(r'^[a-d]\W*', '', normalized)

        # Remove all non-alphanumeric except spaces
        normalized = re.sub(r'[^a-z0-9 ]', '', normalized)

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _answers_match(self, user_answer: str, correct_answer: str) -> bool:
        """
        Determine if user answer matches correct answer using multiple strategies.

        Implements various matching approaches to handle common student
        response variations while maintaining grading accuracy.

        Args:
            user_answer: Normalized user answer
            correct_answer: Normalized correct answer

        Returns:
            True if answers match, False otherwise
        """
        if not user_answer or not correct_answer:
            return False

        # Exact match
        if user_answer == correct_answer:
            return True

        # User answer is contained in correct answer
        if user_answer in correct_answer:
            return True

        # Correct answer is contained in user answer (handles expanded responses)
        if correct_answer in user_answer:
            return True

        # Handle common boolean variations
        boolean_variations = {
            'true': ['t', 'yes', 'correct', '1'],
            'false': ['f', 'no', 'incorrect', '0']
        }

        for canonical, variations in boolean_variations.items():
            if correct_answer == canonical and user_answer in variations:
                return True
            if user_answer == canonical and correct_answer in variations:
                return True

        return False

    def _create_fallback_grading_result(self, question) -> Dict[str, Any]:
        """
        Create fallback grading result when AI grading fails.

        Args:
            question: Question entity to create fallback for

        Returns:
            Fallback grading result
        """
        return {
            "question_id": question.id,
            "is_correct": False,
            "points_earned": 0,
            "feedback": "Unable to grade this answer automatically. Please review with instructor."
        }


# =============================================================================
# FACTORY FUNCTIONS AND SERVICE UTILITIES
# =============================================================================

def create_quiz_generation_service(db_session: AsyncSession = None) -> QuizGenerationService:
    """
    Factory function to create a quiz generation service instance.

    Provides a standardized way to instantiate the service with proper
    configuration and dependency injection.

    Args:
        db_session: Optional database session for persistence operations

    Returns:
        Configured QuizGenerationService instance
    """
    return QuizGenerationService(db_session=db_session)


def create_quiz_grading_service(db_session: AsyncSession = None) -> QuizGradingService:
    """
    Factory function to create a quiz grading service instance.

    Provides a standardized way to instantiate the service with proper
    configuration and dependency injection.

    Args:
        db_session: Database session for grading operations

    Returns:
        Configured QuizGradingService instance
    """
    return QuizGradingService(db_session=db_session)


# =============================================================================
# SERVICE CONFIGURATION AND VALIDATION
# =============================================================================

def validate_quiz_service_configuration() -> bool:
    """
    Validate that all required configuration is available for quiz services.

    Checks API keys, database connections, and other dependencies required
    for proper service operation.

    Returns:
        True if configuration is valid, False otherwise
    """
    required_settings = [
        'llm_api_key',
        'llm_url',
        'llm_model',
        'default_quiz_questions',
        'max_quiz_questions',
        'default_quiz_passing_score'
    ]

    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)

    if missing_settings:
        logger.error(f"Missing required settings for quiz services: {missing_settings}")
        return False

    logger.info("Quiz service configuration validation passed")
    return True


# =============================================================================
# ERROR HANDLING AND RECOVERY UTILITIES
# =============================================================================

class QuizServiceError(Exception):
    """Base exception for quiz service errors."""
    pass


class QuizGenerationError(QuizServiceError):
    """Exception raised when quiz generation fails."""
    pass


class QuizGradingError(QuizServiceError):
    """Exception raised when quiz grading fails."""
    pass


def handle_quiz_service_error(error: Exception, operation: str, context: Dict[str, Any]) -> None:
    """
    Centralized error handling for quiz service operations.

    Provides consistent error logging, alerting, and recovery strategies
    across all quiz service operations.

    Args:
        error: Exception that occurred
        operation: Description of the operation that failed
        context: Additional context about the error
    """
    error_details = {
        'operation': operation,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.now().isoformat()
    }

    logger.error(f"Quiz service error in {operation}: {error_details}")

    # In production, this could trigger alerts, metrics collection, etc.
    # For now, we log the structured error information


# =============================================================================
# PERFORMANCE MONITORING AND HEALTH CHECKS
# =============================================================================

async def check_quiz_services_health() -> Dict[str, Any]:
    """
    Perform health checks on quiz services.

    Validates that all service dependencies are available and functioning
    properly for monitoring and alerting purposes.

    Returns:
        Dict containing health status information
    """
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'services': {}
    }

    try:
        # Check configuration
        config_valid = validate_quiz_service_configuration()
        health_status['services']['configuration'] = 'healthy' if config_valid else 'unhealthy'

        # Check AI service connectivity
        try:
            client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_url)
            # Simple test request
            await client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": "test"}],
                max_completion_tokens=1
            )
            health_status['services']['ai_service'] = 'healthy'
        except Exception as e:
            health_status['services']['ai_service'] = f'unhealthy: {str(e)}'
            health_status['overall_status'] = 'degraded'

        # Determine overall status
        unhealthy_services = [
            name for name, status in health_status['services'].items()
            if status != 'healthy'
        ]

        if unhealthy_services:
            health_status['overall_status'] = 'degraded'
            health_status['unhealthy_services'] = unhealthy_services

    except Exception as e:
        health_status['overall_status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status
