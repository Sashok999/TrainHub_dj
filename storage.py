"""Модуль сохранения и загрузки данных в формате JSON.

Обеспечивает сериализацию объектов Course, User, Enrollment в JSON
и десериализацию структур JSON в связанные объекты предметной области.
"""

import json
import os
from typing import List

from models.courses import Course, find_course_by_id
from models.enrollments import Enrollment
from models.users import User, find_user_by_id


def load_courses(filename: str = "data/courses.json") -> List[Course]:
    """Загрузить курсы из JSON-файла."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Course.from_data(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_courses(filename: str, courses: List[Course]) -> None:
    """Сохранить коллекцию курсов в JSON-файл."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data = [course.to_dict() for course in courses]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_users(filename: str = "data/users.json") -> List[User]:
    """Загрузить пользователей из JSON-файла."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [User.from_data(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_users(filename: str, users: List[User]) -> None:
    """Сохранить коллекцию пользователей в JSON-файл."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data = [user.to_dict() for user in users]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_enrollments(
    filename: str,
    courses: List[Course],
    users: List[User],
) -> List[Enrollment]:
    """Загрузить назначения из JSON-файла и связать их с объектами.

    В JSON хранятся course_id и user_id, которые восстанавливаются
    в ссылки на реальные объекты Course и User.
    """
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            enrollments: List[Enrollment] = []
            for item in data:
                course = find_course_by_id(courses, item.get("course_id"))
                user = find_user_by_id(users, item.get("user_id"))
                if course is not None and user is not None:
                    enrollment = Enrollment(
                        enrollment_id=item["id"],
                        course=course,
                        enrollment_date=item["enrollment_date"],
                        user=user,
                        is_cancelled=item.get("is_cancelled", False),
                        is_completed=item.get("is_completed", False),
                    )
                    enrollments.append(enrollment)
            return enrollments
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_enrollments(filename: str, enrollments: List[Enrollment]) -> None:
    """Сохранить назначения в JSON-файл с сохранением ID связанных объектов."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data = [e.to_dict() for e in enrollments]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_results(filename, enrollments):
    """Загрузить результаты и восстановить связь с обучением ПР3.

    Результаты удаленных, отмененных и незавершенных назначений пропускаются.
    Отсутствующий файл означает, что результатов еще нет.
    """
    from models.results import Result
    from models.enrollments import find_enrollment_by_id

    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as stream:
            data = json.load(stream)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        try:
            enrollment = find_enrollment_by_id(
                enrollments, item['enrollment_id'],
            )
            if enrollment is None:
                continue
            results.append(Result(
                item['id'], enrollment, item['score'],
                item['completed_date'], item.get('comment', ''),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return results


def save_results(filename, results):
    """Сохранить результаты, не изменяя назначения и данные ПР3."""
    from pathlib import Path

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as stream:
        json.dump(
            [result.to_dict() for result in results],
            stream, ensure_ascii=False, indent=2,
        )
