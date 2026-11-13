"""Пакет моделей предметной области TrainHub."""

from .courses import Course
from .enrollments import Enrollment
from .users import User
from .results import Result

__all__ = ["Course", "User", "Enrollment", "Result"]
