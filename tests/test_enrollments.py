"""Тесты для модуля работы с назначениями курсов (Enrollment)."""

import os
from models import Course, Enrollment, User
from models.enrollments import (
    cancel_enrollment,
    create_enrollment,
    is_course_available,
    register_on_courses,
)
from storage import load_enrollments, save_enrollments


def create_sample_entities():
    """Вспомогательная функция для создания тестовых курса и сотрудника."""
    course = Course(
        course_id=1,
        name="Информационная безопасность",
        description="Базовый курс",
        duration_days=7,
    )
    user = User(
        user_id=1,
        name="Иван Иванов",
        email="ivanov@example.com",
    )
    return course, user


def test_enrollment_creation():
    """Проверка создания объекта Enrollment и связей с Course и User."""
    course, user = create_sample_entities()
    enrollment = Enrollment(
        enrollment_id=1,
        course=course,
        enrollment_date="2026-10-01",
        user=user,
    )
    assert enrollment.id == 1
    assert enrollment.course is course
    assert enrollment.user is user
    assert enrollment.course.name == "Информационная безопасность"
    assert enrollment.user.name == "Иван Иванов"
    assert enrollment.is_cancelled is False
    assert enrollment.status == "Активно"


def test_enrollment_cancel():
    """Проверка отмены назначения через метод объекта cancel()."""
    course, user = create_sample_entities()
    enrollment = Enrollment(1, course, "2026-10-01", user)
    enrollment.cancel()
    assert enrollment.is_cancelled is True
    assert enrollment.status == "Отменено"


def test_enrollment_complete():
    """Проверка завершения обучения."""
    course, user = create_sample_entities()
    enrollment = Enrollment(1, course, "2026-10-01", user)
    enrollment.complete()
    assert enrollment.is_completed is True
    assert enrollment.status == "Завершено"


def test_is_course_available():
    """Проверка доступности курса при отсутствии активных назначений."""
    course, user = create_sample_entities()
    enrollments = []
    assert is_course_available(enrollments, course, user, "2026-10-01") is True


def test_duplicate_enrollment_forbidden():
    """Проверка запрета повторного активного назначения на одну дату."""
    course, user = create_sample_entities()
    enrollments = []
    first = create_enrollment(enrollments, course, "2026-10-01", user)
    assert first is not None
    assert len(enrollments) == 1

    # Попытка повторной записи того же пользователя на тот же курс и дату
    second = create_enrollment(enrollments, course, "2026-10-01", user)
    assert second is None
    assert len(enrollments) == 1


def test_cancelled_enrollment_allows_rebooking():
    """Проверка, что отмененное назначение разблокирует дату."""
    course, user = create_sample_entities()
    enrollments = []
    first = create_enrollment(enrollments, course, "2026-10-01", user)
    assert first is not None

    # Отменяем первое назначение
    first.cancel()
    assert first.is_cancelled is True

    # Теперь назначение на эту же дату должно успешно создаваться
    second = create_enrollment(enrollments, course, "2026-10-01", user)
    assert second is not None
    assert len(enrollments) == 2
    assert second.id == 2
    assert second.is_cancelled is False


def test_cancel_enrollment_function():
    """Проверка функции cancel_enrollment по идентификатору."""
    course, user = create_sample_entities()
    enrollments = [Enrollment(10, course, "2026-10-01", user)]
    res = cancel_enrollment(enrollments, 10)
    assert res is True
    assert enrollments[0].is_cancelled is True

    res_missing = cancel_enrollment(enrollments, 999)
    assert res_missing is False


def test_register_on_courses_legacy():
    """Проверка адаптированной функции register_on_courses (из ПР1)."""
    course, user = create_sample_entities()
    enrollments = []
    e = register_on_courses(enrollments, user, course, "2026-10-15")
    assert e is not None
    assert e.course is course
    assert e.user is user


def test_storage_roundtrip(tmp_path):
    """Проверка сохранения и загрузки назначений с восстановлением связей."""
    course, user = create_sample_entities()
    enrollments = [Enrollment(1, course, "2026-10-01", user)]
    temp_file = str(tmp_path / "test_enrollments.json")

    save_enrollments(temp_file, enrollments)
    assert os.path.exists(temp_file)

    loaded = load_enrollments(temp_file, [course], [user])
    assert len(loaded) == 1
    assert loaded[0].id == 1
    assert loaded[0].course is course
    assert loaded[0].user is user
