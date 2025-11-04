from typing import TypeVar
from datetime import datetime, timezone
import pytz
from sqlalchemy.orm import Session
from app.core.logger import get_logger
from app.models.enums import LearningStyle, DifficultyLevel
from app.models.platform import Platform

logger = get_logger(__name__)
T = TypeVar('T')

# UTC+2 timezone (Central European Time)
TIMEZONE_UTC_PLUS_2 = pytz.timezone('Europe/Bucharest')

# Time zone utility functions
def get_current_utc_plus_2_time() -> datetime:
    """Get current time in UTC+2 timezone"""
    return datetime.now(TIMEZONE_UTC_PLUS_2)

def convert_utc_plus_2_to_utc(local_datetime: datetime) -> datetime:
    """Convert UTC+2 datetime to UTC"""
    if local_datetime.tzinfo is None:
        local_datetime = TIMEZONE_UTC_PLUS_2.localize(local_datetime)
    return local_datetime.astimezone(timezone.utc)


def get_enum_value(val):
    """
    Enhanced enum value extraction with proper JSON serialization.
    Handles all cases: None, lists, enums, strings, and nested structures.
    """
    if val is None:
        return None

    # Handle lists/arrays
    if isinstance(val, list):
        return [get_enum_value(item) for item in val]

    # Handle dictionaries
    if isinstance(val, dict):
        return {key: get_enum_value(value) for key, value in val.items()}

    # Handle enums with .value attribute
    if hasattr(val, 'value'):
        return val.value

    # Handle strings (already serializable)
    if isinstance(val, str):
        return val

    # Handle other types by converting to string
    return str(val)

def convert_difficulty_to_enum(difficulty: str) -> DifficultyLevel:
    """
    Convert difficulty string to DifficultyLevel enum.

    Args:
        difficulty: Difficulty as string

    Returns:
        DifficultyLevel enum value

    Raises:
        ValueError: If the difficulty string is unrecognized
    """
    if not difficulty:
        return DifficultyLevel.INTERMEDIATE  # Default fallback

    try:
        return DifficultyLevel[difficulty.upper()]
    except KeyError:
        raise ValueError(f"Unrecognized difficulty level: {difficulty}")


def get_platform_id(platform_name: str, db_session: Session) -> int:
    """
    Get platform ID by name, creating the platform if it doesn't exist.

    Args:
        platform_name: Name of the platform (e.g., 'YouTube', 'Spotify')
        db_session: Database session for queries

    Returns:
        Platform ID (integer)

    Raises:
        ValueError: If database operations fails
    """
    try:
        # Normalize platform name
        platform_name = platform_name.strip() if platform_name else "Unknown"

        # Try to find existing platform (case-insensitive)
        platform = db_session.query(Platform).filter(
            Platform.name.ilike(platform_name)
        ).first()

        if platform:
            logger.debug(f"Found existing platform: {platform_name} (ID: {platform.id})")
            return platform.id

        # Create new platform if not found
        new_platform = Platform(name=platform_name)
        db_session.add(new_platform)
        db_session.flush()  # Get the ID without committing

        logger.info(f"Created new platform: {platform_name} (ID: {new_platform.id})")
        return new_platform.id

    except Exception as e:
        logger.error(f"Error getting/creating platform ID for '{platform_name}': {str(e)}")

        # Try to get a default platform as fallback
        try:
            default_platform = db_session.query(Platform).filter(
                Platform.name.ilike("Manual Search")
            ).first()

            if default_platform:
                logger.warning(f"Using fallback platform 'Manual Search' (ID: {default_platform.id})")
                return default_platform.id

            # Create Manual Search as ultimate fallback
            fallback_platform = Platform(name="Manual Search")
            db_session.add(fallback_platform)
            db_session.flush()

            logger.warning(f"Created fallback platform 'Manual Search' (ID: {fallback_platform.id})")
            return fallback_platform.id

        except Exception as fallback_error:
            logger.error(f"Failed to create fallback platform: {str(fallback_error)}")
            raise ValueError(f"Unable to resolve platform ID for '{platform_name}': {str(e)}")


def get_learning_style_by_platform_name(platform_name: str) -> LearningStyle:
    """
    Map platform name to the most appropriate learning style.

    Args:
        platform_name: Name of the platform (e.g., 'YouTube', 'Spotify', etc.)

    Returns:
        LearningStyle: Learning style enum that best matches the platform
    """
    # Normalize platform name for consistent matching
    platform_lower = platform_name.lower() if platform_name else ""

    # Platform to learning style mapping using enum values
    platform_learning_style_map = {
        # Visual platforms (video, images, diagrams)
        "youtube": LearningStyle.VISUAL,
        "udemy": LearningStyle.VISUAL,
        "coursera": LearningStyle.VISUAL,
        "edx": LearningStyle.VISUAL,
        "khan academy": LearningStyle.VISUAL,
        "linkedin learning": LearningStyle.VISUAL,
        "pluralsight": LearningStyle.VISUAL,
        "skillshare": LearningStyle.VISUAL,
        "masterclass": LearningStyle.VISUAL,
        "codecademy": LearningStyle.VISUAL,

        # Auditory platforms (audio, podcasts, spoken content)
        "spotify": LearningStyle.AUDITORY,
        "audible": LearningStyle.AUDITORY,
        "podcast": LearningStyle.AUDITORY,
        "soundcloud": LearningStyle.AUDITORY,
        "apple podcasts": LearningStyle.AUDITORY,
        "google podcasts": LearningStyle.AUDITORY,

        # Reading/Writing platforms (text, articles, documentation)
        "medium": LearningStyle.READING_WRITING,
        "google books": LearningStyle.READING_WRITING,
        "semantic scholar": LearningStyle.READING_WRITING,
        "arxiv": LearningStyle.READING_WRITING,
        "wikipedia": LearningStyle.READING_WRITING,
        "documentation": LearningStyle.READING_WRITING,
        "blog": LearningStyle.READING_WRITING,
        "article": LearningStyle.READING_WRITING,
        "book": LearningStyle.READING_WRITING,

        # Kinesthetic platforms (hands-on, interactive, practice)
        "freecodecamp": LearningStyle.KINESTHETIC,
        "hackerrank": LearningStyle.KINESTHETIC,
        "leetcode": LearningStyle.KINESTHETIC,
        "codepen": LearningStyle.KINESTHETIC,
        "github": LearningStyle.KINESTHETIC,
        "interactive": LearningStyle.KINESTHETIC,
        "simulation": LearningStyle.KINESTHETIC,
        "lab": LearningStyle.KINESTHETIC,
        "workshop": LearningStyle.KINESTHETIC,

        # Fallback/generic platforms
        "manual search": LearningStyle.VISUAL,  # Default fallback
        "unknown": LearningStyle.VISUAL,
        "fallback": LearningStyle.VISUAL
    }

    # Try exact match first
    if platform_lower in platform_learning_style_map:
        learning_style = platform_learning_style_map[platform_lower]
        return learning_style

    # Try partial matches for compound platform names
    for platform_key, learning_style in platform_learning_style_map.items():
        if platform_key in platform_lower or platform_lower in platform_key:
            return learning_style

    # Default fallback
    return LearningStyle.VISUAL
