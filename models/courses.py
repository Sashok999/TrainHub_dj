"""Модуль работы с учебными курсами.

Содержит класс Course и функции для работы с коллекцией курсов.
"""

from typing import List, Optional


class Course:
    """Класс, представляющий учебный курс."""

    def __init__(
        self,
        course_id: int,
        name: str,
        description: str,
        duration_days: int,
        course_type: str = "онлайн",
        is_mandatory: bool = False,
    ) -> None:
        """Создать объект учебного курса."""
        self.id = course_id
        self.name = name
        self.description = description
        self.duration_days = duration_days
        self.course_type = course_type
        self.is_mandatory = is_mandatory

    def is_suitable_for(self, max_days: int) -> bool:
        """Проверить, подходит ли курс по длительности."""
        return self.duration_days <= max_days

    @staticmethod
    def validate_duration(duration_days: int) -> bool:
        """Проверить корректность длительности курса."""
        return duration_days > 0

    @classmethod
    def from_data(cls, data: dict) -> "Course":
        """Создать объект Course из словаря данных."""
        return cls(
            course_id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            duration_days=data["duration_days"],
            course_type=data.get("course_type", "онлайн"),
            is_mandatory=data.get("is_mandatory", False),
        )

    def to_dict(self) -> dict:
        """Преобразовать объект курса в словарь для JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "duration_days": self.duration_days,
            "course_type": self.course_type,
            "is_mandatory": self.is_mandatory,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление курса."""
        mandatory_str = " (обязательный)" if self.is_mandatory else ""
        return (
            f"Курс #{self.id}: '{self.name}' ({self.duration_days} дн., "
            f"{self.course_type}){mandatory_str}"
        )


def add_course(
    courses: List[Course],
    name: str,
    description: str,
    duration_days: int,
    course_type: str = "онлайн",
    is_mandatory: bool = False,
) -> Course:
    """Создать курс и добавить его в коллекцию."""
    new_id = max([c.id for c in courses], default=0) + 1
    course = Course(
        course_id=new_id,
        name=name,
        description=description,
        duration_days=duration_days,
        course_type=course_type,
        is_mandatory=is_mandatory,
    )
    courses.append(course)
    return course


def find_course(courses: List[Course], query: str) -> List[Course]:
    """Найти курсы по подстроке в названии или описании."""
    lower_query = query.lower()
    return [
        c for c in courses
        if (
            lower_query in c.name.lower()
            or lower_query in c.description.lower()
        )
    ]


def find_course_by_id(
    courses: List[Course],
    course_id: int,
) -> Optional[Course]:
    """Найти курс по его идентификатору."""
    for c in courses:
        if c.id == course_id:
            return c
    return None


def check_course_duration(
    courses: List[Course],
    course_id: int,
    max_days: int,
) -> bool:
    """Проверить, укладывается ли курс в указанную длительность."""
    course = find_course_by_id(courses, course_id)
    if course is None:
        return False
    return course.is_suitable_for(max_days)


def filter_courses_by_duration(
    courses: List[Course],
    max_days: int,
) -> List[Course]:
    """Отобрать курсы, длительность которых не превышает max_days."""
    return [c for c in courses if c.is_suitable_for(max_days)]


def sort_courses(
    courses: List[Course],
    reverse: bool = False,
) -> List[Course]:
    """Отсортировать курсы по длительности с использованием lambda."""
    return sorted(
        courses,
        key=lambda c: c.duration_days,
        reverse=reverse,
    )


def show_courses(courses: List[Course]) -> None:
    """Вывести список курсов в форматированном виде."""
    if not courses:
        print("Список курсов пуст.")
        return
    print("-" * 75)
    header = (
        f"{'ID':<4} | {'Название':<28} | {'Длит.':<8} | "
        f"{'Тип':<10} | Обяз."
    )
    print(header)
    print("-" * 75)
    for c in courses:
        mand = "Да" if c.is_mandatory else "Нет"
        print(
            f"{c.id:<4} | {c.name[:28]:<28} | "
            f"{c.duration_days:<4} дн | {c.course_type:<10} | {mand}"
        )
    print("-" * 75)
