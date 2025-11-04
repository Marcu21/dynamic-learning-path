"""
Celery Database Base Configuration
=================================

This module provides a separate database base for Celery tasks that need
to import models without triggering async engine creation.
"""

from sqlalchemy.orm import declarative_base

# Separate declarative base for Celery contexts
CeleryBase = declarative_base()
