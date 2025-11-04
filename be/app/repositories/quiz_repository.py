"""
Quiz Repository
==============

Database operations for quiz-related entities including quizzes, questions,
attempts, and answers.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc, select

from app.core.logger import get_logger
from app.models.quiz import Quiz, Question, QuizAttempt, Answer
from app.schemas.core_schemas.quiz_schema import (
    QuizCreate, QuestionCreate, QuizAttemptCreate, AnswerCreate
)

logger = get_logger(__name__)


async def create_quiz(db: AsyncSession, quiz_data: QuizCreate) -> Quiz:
    """Create a new quiz"""
    try:
        quiz = Quiz(**quiz_data.model_dump())
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        logger.info(f"Created quiz {quiz.id} for module {quiz.module_id}")
        return quiz
    except Exception as e:
        logger.error(f"Error creating quiz: {str(e)}")
        await db.rollback()
        raise


async def create_question(db: AsyncSession, question_data: QuestionCreate) -> Question:
    """Create a new question"""
    try:
        question = Question(**question_data.model_dump())
        db.add(question)
        await db.commit()
        await db.refresh(question)
        logger.debug(f"Created question {question.id} for quiz {question.quiz_id}")
        return question
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating question: {str(e)}")
        raise


async def create_questions_batch(db: AsyncSession, questions_data: List[QuestionCreate]) -> List[Question]:
    """Create multiple questions in a batch"""
    try:
        questions = [Question(**q.model_dump()) for q in questions_data]
        db.add_all(questions)
        await db.commit()
        for question in questions:
            await db.refresh(question)
        logger.info(f"Created {len(questions)} questions in batch")
        return questions
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating questions batch: {str(e)}")
        raise


async def get_quiz_by_id(db: AsyncSession, quiz_id: int) -> Optional[Quiz]:
    """Get quiz by ID with all related data"""
    try:
        result = await db.execute(select(Quiz).options(
            joinedload(Quiz.questions),
            joinedload(Quiz.module)
        ).filter(Quiz.id == quiz_id))
        quiz = result.unique().scalar_one_or_none()
        return quiz
    except Exception as e:
        logger.error(f"Error getting quiz {quiz_id}: {str(e)}")
        raise


async def get_quiz_by_module_id(db: AsyncSession, module_id: int) -> Optional[Quiz]:
    """Get quiz by module ID"""
    try:
        result = await db.execute(select(Quiz).filter(
            and_(Quiz.module_id == module_id, Quiz.is_active == True)
        ))
        quiz = result.scalar_one_or_none()
        return quiz
    except Exception as e:
        logger.error(f"Error getting quiz for module {module_id}: {str(e)}")
        raise


async def get_quiz_for_taking(db: AsyncSession, quiz_id: int) -> Optional[Quiz]:
    """Get quiz with questions for taking (without correct answers)"""
    try:
        result = await db.execute(select(Quiz).options(
            joinedload(Quiz.questions)
        ).filter(
            and_(Quiz.id == quiz_id, Quiz.is_active == True)
        ))
        quiz = result.unique().scalar_one_or_none()
        return quiz
    except Exception as e:
        logger.error(f"Error getting quiz {quiz_id} for taking: {str(e)}")
        raise


async def create_quiz_attempt(db: AsyncSession, attempt_data: QuizAttemptCreate) -> QuizAttempt:
    """Create a new quiz attempt"""
    try:
        attempt = QuizAttempt(**attempt_data.model_dump())
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        logger.info(f"Created quiz attempt {attempt.id} for user {attempt.user_id}")
        return attempt
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating quiz attempt: {str(e)}")
        raise


async def get_quiz_attempt_by_id(db: AsyncSession, attempt_id: int) -> Optional[QuizAttempt]:
    """Get quiz attempt by ID with related data"""
    try:
        result = await db.execute(select(QuizAttempt).options(
            joinedload(QuizAttempt.quiz).joinedload(Quiz.questions),
            joinedload(QuizAttempt.answers).joinedload(Answer.question),
            joinedload(QuizAttempt.user)
        ).filter(QuizAttempt.id == attempt_id))
        attempt = result.unique().scalar_one_or_none()
        return attempt
    except Exception as e:
        logger.error(f"Error getting quiz attempt {attempt_id}: {str(e)}")
        raise


async def get_user_quiz_attempts_by_module(db: AsyncSession, module_id: int, user_id: str) -> List[QuizAttempt]:
    """Get all quiz attempts for a user and module"""
    try:
        result = await db.execute(select(QuizAttempt).join(Quiz).filter(
            and_(
                Quiz.module_id == module_id,
                QuizAttempt.user_id == user_id
            )
        ).order_by(desc(QuizAttempt.started_at)))
        attempts = result.scalars().all()
        return attempts
    except Exception as e:
        logger.error(f"Error getting quiz attempts for module {module_id}, user {user_id}: {str(e)}")
        raise


async def get_user_quiz_attempts_by_quiz(db: AsyncSession, quiz_id: int, user_id: str) -> List[QuizAttempt]:
    """Get all quiz attempts for a user and specific quiz"""
    try:
        result = await db.execute(select(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id
            )
        ).order_by(desc(QuizAttempt.started_at)))
        attempts = result.scalars().all()
        return attempts
    except Exception as e:
        logger.error(f"Error getting quiz attempts for quiz {quiz_id}, user {user_id}: {str(e)}")
        raise


async def create_answer(db: AsyncSession, answer_data: AnswerCreate) -> Answer:
    """Create a new answer"""
    try:
        answer = Answer(**answer_data.model_dump())
        db.add(answer)
        await db.commit()
        await db.refresh(answer)
        return answer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating answer: {str(e)}")
        raise


async def create_answers_batch(db: AsyncSession, answers_data: List[AnswerCreate]) -> List[Answer]:
    """Create multiple answers in a batch"""
    try:
        answers = [Answer(**a.model_dump()) for a in answers_data]
        db.add_all(answers)
        await db.commit()
        for answer in answers:
            await db.refresh(answer)
        await db.flush()  # Ensure all changes are written to the database
        logger.info(f"Created {len(answers)} answers in batch")
        return answers
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating answers batch: {str(e)}")
        raise


async def update_quiz_attempt(db: AsyncSession, attempt_id: int, **kwargs) -> Optional[QuizAttempt]:
    """Update quiz attempt with provided fields"""
    try:
        result = await db.execute(select(QuizAttempt).filter(QuizAttempt.id == attempt_id))
        attempt = result.scalar_one_or_none()
        if attempt:
            for key, value in kwargs.items():
                if hasattr(attempt, key):
                    setattr(attempt, key, value)
            await db.commit()
            await db.refresh(attempt)
            logger.info(f"Updated quiz attempt {attempt_id}")
        return attempt
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating quiz attempt {attempt_id}: {str(e)}")
        raise


async def check_if_user_passed_quiz_before(db: AsyncSession, quiz_id: int, user_id: str) -> bool:
    """Check if user has previously passed this quiz"""
    try:
        result = await db.execute(select(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.passed == True,
                QuizAttempt.skill_points_awarded == True
            )
        ))
        passed_attempt = result.scalar_one_or_none()
        return passed_attempt is not None
    except Exception as e:
        logger.error(f"Error checking if user {user_id} passed quiz {quiz_id}: {str(e)}")
        raise


async def get_question_by_id(db: AsyncSession, question_id: int) -> Optional[Question]:
    """Get question by ID"""
    try:
        result = await db.execute(select(Question).filter(Question.id == question_id))
        question = result.scalar_one_or_none()
        return question
    except Exception as e:
        logger.error(f"Error getting question {question_id}: {str(e)}")
        raise


async def get_quiz_questions(db: AsyncSession, quiz_id: int) -> List[Question]:
    """Get all questions for a quiz ordered by order_index"""
    try:
        result = await db.execute(select(Question).filter(
            Question.quiz_id == quiz_id
        ).order_by(Question.order_index))
        questions = result.scalars().all()
        return questions
    except Exception as e:
        logger.error(f"Error getting questions for quiz {quiz_id}: {str(e)}")
        raise


async def delete_quiz(db: AsyncSession, quiz_id: int) -> bool:
    """Delete a quiz and all related data"""
    try:
        result = await db.execute(select(Quiz).filter(Quiz.id == quiz_id))
        quiz = result.scalar_one_or_none()
        if quiz:
            await db.delete(quiz)
            await db.commit()
            logger.info(f"Deleted quiz {quiz_id}")
            return True
        return False
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
        raise


async def update_quiz(db: AsyncSession, quiz_id: int, **kwargs) -> Optional[Quiz]:
    """Update quiz with provided fields"""
    try:
        result = await db.execute(select(Quiz).filter(Quiz.id == quiz_id))
        quiz = result.scalar_one_or_none()
        if quiz:
            for key, value in kwargs.items():
                if hasattr(quiz, key):
                    setattr(quiz, key, value)
            await db.commit()
            await db.refresh(quiz)
            logger.info(f"Updated quiz {quiz_id}")
        return quiz
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating quiz {quiz_id}: {str(e)}")
        raise
