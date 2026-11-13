"""Модуль работы с назначениями курсов (записями на обучение).

Содержит класс Enrollment и функции для работы с коллекцией назначений.
"""

from typing import List, Optional

from .courses import Course
from .users import User


class Enrollment:
    """Класс, связывающий пользователя и курс (назначение на обучение)."""

    def __init__(
        self,
        enrollment_id: int,
        course: Course,
        enrollment_date: str,
        user: User,
        is_cancelled: bool = False,
        is_completed: bool = False,
    ) -> None:
        """Создать объект назначения курса."""
        self.id = enrollment_id
        self.course = course
        self.enrollment_date = enrollment_date
        self.user = user
        self.is_cancelled = is_cancelled
        self.is_completed = is_completed

    def cancel(self) -> None:
        """Отменить назначение курса."""
        self.is_cancelled = True

    def complete(self) -> None:
        """Отметить курс как успешно завершенный."""
        if not self.is_cancelled:
            self.is_completed = True

    @property
    def status(self) -> str:
        """Получить текущий статус назначения в виде текста."""
        if self.is_cancelled:
            return "Отменено"
        if self.is_completed:
            return "Завершено"
        return "Активно"

    def to_dict(self) -> dict:
        """Преобразовать объект назначения в словарь для сохранения в JSON."""
        return {
            "id": self.id,
            "course_id": self.course.id,
            "user_id": self.user.id,
            "enrollment_date": self.enrollment_date,
            "is_cancelled": self.is_cancelled,
            "is_completed": self.is_completed,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление назначения."""
        return (
            f"Назначение #{self.id}: {self.user.name} -> '{self.course.name}' "
            f"({self.enrollment_date}) [{self.status}]"
        )


def is_course_available(
    enrollments: List[Enrollment],
    course: Course,
    user: User,
    enrollment_date: str,
) -> bool:
    """Проверить, доступно ли назначение курса сотруднику на дату.

    Активное назначение на тот же курс и дату блокирует повторную запись.
    Отмененное назначение не блокирует запись.
    """
    for e in enrollments:
        if (
            e.course.id == course.id
            and e.user.id == user.id
            and e.enrollment_date == enrollment_date
            and not e.is_cancelled
        ):
            return False
    return True


def get_enrollment_status(is_available: bool) -> str:
    """Вернуть статус доступности назначения (преемственность ПР1/ПР2)."""
    if is_available:
        return "Курс доступен для назначения"
    return "Сотрудник уже записан на этот курс на указанную дату"


def create_enrollment(
    enrollments: List[Enrollment],
    course: Course,
    enrollment_date: str,
    user: User,
) -> Optional[Enrollment]:
    """Создать новое назначение курса сотруднику.

    Если сотрудник уже активно записан на этот курс на данную дату,
    возвращается None.
    """
    if not is_course_available(enrollments, course, user, enrollment_date):
        return None

    new_id = max([e.id for e in enrollments], default=0) + 1
    enrollment = Enrollment(
        enrollment_id=new_id,
        course=course,
        enrollment_date=enrollment_date,
        user=user,
    )
    enrollments.append(enrollment)
    return enrollment


def register_on_courses(
    enrollments: List[Enrollment],
    user: User,
    course: Course,
    enrollment_date: str = "2026-09-28",
) -> Optional[Enrollment]:
    """Зарегистрировать на курс (адаптированная функция из ПР1)."""
    return create_enrollment(enrollments, course, enrollment_date, user)


def cancel_booking(
    enrollments: List[Enrollment],
    enrollment_id: int,
) -> bool:
    """Отменить назначение по идентификатору (алиас cancel_booking)."""
    return cancel_enrollment(enrollments, enrollment_id)


def cancel_enrollment(
    enrollments: List[Enrollment],
    enrollment_id: int,
) -> bool:
    """Отменить назначение по идентификатору.

    Объект не удаляется из коллекции, а переводится в статус отмененного.
    """
    for e in enrollments:
        if e.id == enrollment_id:
            e.cancel()
            return True
    return False


def find_enrollment_by_id(
    enrollments: List[Enrollment],
    enrollment_id: int,
) -> Optional[Enrollment]:
    """Найти назначение по его идентификатору."""
    for e in enrollments:
        if e.id == enrollment_id:
            return e
    return None


def filter_enrollments_by_user(
    enrollments: List[Enrollment],
    user_id: int,
) -> List[Enrollment]:
    """Отобрать назначения для конкретного пользователя."""
    return [e for e in enrollments if e.user.id == user_id]


def show_enrollments(enrollments: List[Enrollment]) -> None:
    """Вывести список назначений в виде таблицы."""
    if not enrollments:
        print("Список назначений пуст.")
        return
    print("-" * 80)
    print(
        f"{'ID':<4} | {'Сотрудник':<20} | {'Курс':<24} | "
        f"{'Дата':<10} | {'Статус':<12}"
    )
    print("-" * 80)
    for e in enrollments:
        print(
            f"{e.id:<4} | {e.user.name[:20]:<20} | "
            f"{e.course.name[:24]:<24} | {e.enrollment_date:<10} | "
            f"{e.status:<12}"
        )
    print("-" * 80)
