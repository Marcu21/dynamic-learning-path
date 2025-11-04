"""
Module Repository

This module provides data access methods for module operations.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

from app.core.logger import get_logger
from app.models import Platform
from app.models.module import Module
from app.models.enums import LearningStyle, DifficultyLevel
from app.schemas.core_schemas.module_schema import ModuleResponse, ModuleCreate

logger = get_logger(__name__)


def create_module(db: Session, module_data: ModuleCreate) -> ModuleResponse:
   """
   Create a new module.

   Args:
       db: Database session
       module_data: Module creation data

   Returns:
       ModuleResponse object with created module details
   """
   logger.info(f"Creating module: {getattr(module_data, 'title')} for learning path {getattr(module_data, 'learning_path_id')}")

   try:
       # Create module instance
       module = Module(
           learning_path_id=getattr(module_data, "learning_path_id"),
           platform_id=getattr(module_data, "platform_id"),
           title=getattr(module_data, "title"),
           description=getattr(module_data, "description"),
           learning_objectives=getattr(module_data, "learning_objectives"),
           duration=getattr(module_data, "duration"),
           order_index=getattr(module_data, "order_index"),
           content_url=getattr(module_data, "content_url"),
           difficulty=getattr(module_data, "difficulty"),
           learning_style=getattr(module_data, "learning_style"),
           is_inserted=getattr(module_data, "is_inserted")
       )

       db.add(module)
       db.flush()  # Get the module ID

       # Get the platform information
       result = db.query(Platform).filter(Platform.id == module.platform_id)
       platform = result.first()
       if not platform:
           raise ValueError(f"Platform with ID {module.platform_id} not found")

       db.commit()

       # Build response object with platform name
       module_response = ModuleResponse(
           id=module.id,
           learning_path_id=module.learning_path_id,
           platform_id=module.platform_id,
           platform_name=platform.name,
           title=module.title,
           description=module.description,
           learning_objectives=module.learning_objectives,
           duration=module.duration,
           order_index=module.order_index,
           content_url=module.content_url,
           difficulty=module.difficulty,
           learning_style=module.learning_style[0] if module.learning_style and len(module.learning_style) > 0 else LearningStyle.VISUAL,
           completed=False,
           created_at=module.created_at if module.created_at else datetime.now(),
           is_inserted=module.is_inserted
       )

       logger.info(f"Created module {module.id}: {module.title}")
       return module_response

   except Exception as e:
       logger.error(f"Error creating module {getattr(module_data, 'title')}: {str(e)}")
       db.rollback()
       raise

async def get_by_id(db: AsyncSession, module_id: int) -> Optional[ModuleResponse]:
    """
    Get module by ID.

    Args:
        db: Database session
        module_id: ID of the module

    Returns:
        ModuleResponse object or None if not found
    """
    logger.debug(f"Getting module by ID: {module_id}")

    try:
        result = await db.execute(select(Module).options(joinedload(Module.platform)).filter(Module.id == module_id))
        module = result.scalar_one_or_none()

        if not module:
            return None

        return ModuleResponse(
            id=module.id,
            learning_path_id=module.learning_path_id,
            platform_id=module.platform_id,
            platform_name=module.platform.name,  
            title=module.title,
            description=module.description,
            learning_objectives=module.learning_objectives,
            duration=module.duration,
            order_index=module.order_index,
            content_url=module.content_url,
            difficulty=module.difficulty if module.difficulty else DifficultyLevel.BEGINNER,
            learning_style=module.learning_style[0] if module.learning_style and len(module.learning_style) > 0 else LearningStyle.VISUAL,
            completed=False,
            created_at=module.created_at if module.created_at else datetime.now(),
            is_inserted=module.is_inserted
        )

    except Exception as e:
        logger.error(f"Error getting module {module_id}: {str(e)}")
        raise


async def get_by_learning_path_id(db: AsyncSession, learning_path_id: int) -> List[ModuleResponse]:
    """
    Get all modules for a learning path, ordered by order_index.

    Args:
        db: Database session
        learning_path_id: ID of the learning path

    Returns:
        List of ModuleResponse objects
    """
    logger.debug(f"Getting modules for learning path: {learning_path_id}")

    try:
        result = await db.execute(select(Module).options(joinedload(Module.platform)).filter(
            Module.learning_path_id == learning_path_id
        ).order_by(Module.order_index))
        modules = result.scalars().all()

        result = []
        for module in modules:
            # Validate that required fields exist
            if module.difficulty is None:
                logger.error(f"Module {module.id} has NULL difficulty - this should not happen")
                raise ValueError(f"Module {module.id} is missing required difficulty field")

            if module.learning_style is None or len(module.learning_style) == 0:
                logger.error(f"Module {module.id} has NULL or empty learning_style - this should not happen")
                raise ValueError(f"Module {module.id} is missing required learning_style field")

            result.append(ModuleResponse(
                id=module.id,
                learning_path_id=module.learning_path_id,
                platform_id=module.platform_id,
                platform_name=module.platform.name,  # Use the relationship
                title=module.title,
                description=module.description,
                learning_objectives=module.learning_objectives,
                duration=module.duration,
                order_index=module.order_index,
                content_url=module.content_url,
                difficulty=module.difficulty,
                learning_style=module.learning_style[0],
                completed=False,
                created_at=module.created_at if module.created_at else datetime.now(),
                is_inserted=module.is_inserted
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting modules for learning path {learning_path_id}: {str(e)}")
        raise


async def get_learning_path_id_by_module(db: AsyncSession, module_id: int) -> Optional[int]:
    """
    Get learning path ID for a module.

    Args:
        db: Database session
        module_id: ID of the module

    Returns:
        Learning path ID or None if module not found
    """
    logger.debug(f"Getting learning path ID for module: {module_id}")

    try:
        result = await db.execute(select(Module).filter(Module.id == module_id))
        module = result.scalar_one_or_none()
        return module.learning_path_id if module else None

    except Exception as e:
        logger.error(f"Error getting learning path ID for module {module_id}: {str(e)}")
        raise


async def delete_with_cascade(db: AsyncSession, module_id: int) -> Dict[str, Any]:
    """
    Delete module and all associated data.

    Args:
        db: Database session
        module_id: ID of the module to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting module {module_id} with cascade")

    try:
        # Get module first
        result = await db.execute(select(Module).filter(Module.id == module_id))
        module = result.scalar_one_or_none()

        if not module:
            raise ValueError("Module not found")

        # Count quizzes to be deleted
        deleted_quizzes_count = 1 if module.quiz else 0

        # Delete the module (cascade will handle quiz and progress records)
        await db.delete(module)
        await db.commit()

        return {
            "deleted_quizzes_count": deleted_quizzes_count
        }

    except Exception as e:
        logger.error(f"Error deleting module {module_id}: {str(e)}")
        await db.rollback()
        raise


async def reorder_modules(db: AsyncSession, learning_path_id: int, modules_to_update: List[Dict[str, Any]], user_id: str) -> None:
    """
    Reorder modules by updating their order_index values.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        modules_to_update: List of dicts with module_id and new_order_index
        user_id: ID of the user performing the reorder (for logging)
    """
    logger.info(f"Reordering {len(modules_to_update)} modules in learning path {learning_path_id} for user {user_id}")

    try:
        # Update each module's order_index
        for module_update in modules_to_update:
            module_id = module_update["module_id"]
            new_order_index = module_update["new_order_index"]

            # Get the module and update its order_index
            result = await db.execute(select(Module).filter(
                and_(
                    Module.id == module_id,
                    Module.learning_path_id == learning_path_id
                )
            ))
            module = result.scalar_one_or_none()

            if module:
                old_order_index = module.order_index
                module.order_index = new_order_index
                logger.debug(f"Updated module {module_id} order: {old_order_index} -> {new_order_index}")
            else:
                logger.warning(f"Module {module_id} not found in learning path {learning_path_id}")

        await db.commit()
        logger.info(f"Successfully reordered {len(modules_to_update)} modules in learning path {learning_path_id}")

    except Exception as e:
        logger.error(f"Error reordering modules in learning path {learning_path_id}: {str(e)}")
        await db.rollback()
        raise

async def get_platform_by_id(db: AsyncSession, platform_id: int) -> Optional[str]:
    """
    Get platform name by ID.

    Args:
        db: Database session
        platform_id: ID of the platform

    Returns:
        Platform name or None if not found
    """
    logger.debug(f"Getting platform name for ID: {platform_id}")

    try:
        result = await db.execute(select(Platform).filter(Platform.id == platform_id))
        platform = result.scalar_one_or_none()
        return platform.name if platform else None

    except Exception as e:
        logger.error(f"Error getting platform name for ID {platform_id}: {str(e)}")
        raise


async def get_platform_id_by_name(db: AsyncSession, platform_name: str) -> Optional[int]:
    """
    Get platform ID by name (case-insensitive).

    Args:
        db: Database session
        platform_name: Name of the platform

    Returns:
        Platform ID or None if not found
    """
    logger.debug(f"Getting platform ID for name: {platform_name}")

    try:
        platform = await db.execute(select(Platform).filter(Platform.name.ilike(platform_name)))
        platform = platform.scalar_one_or_none()

        if platform:
            logger.debug(f"Found platform '{platform.name}' with ID: {platform.id}")
            return platform.id
        else:
            logger.debug(f"No platform found matching '{platform_name}'")
            return None

    except Exception as e:
        logger.error(f"Error getting platform ID for name {platform_name}: {str(e)}")
        raise
