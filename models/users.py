"""Модуль работы с сотрудниками и пользователями системы.

Содержит класс User и функции для работы с коллекцией пользователей.
"""

from typing import List, Optional


class User:
    """Класс, представляющий пользователя (сотрудника) системы."""

    def __init__(
        self,
        user_id: int,
        name: str,
        email: str,
        position: str = "Сотрудник",
        role: str = "сотрудник",
    ) -> None:
        """Создать объект пользователя."""
        self.id = user_id
        self.name = name
        self.email = email
        self.position = position
        self.role = role

    @staticmethod
    def validate_email(email: str) -> bool:
        """Проверить базовую корректность адреса электронной почты."""
        if "@" not in email:
            return False
        parts = email.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return False
        return "." in parts[1] and len(parts[1].split(".")[-1]) >= 2

    @classmethod
    def from_data(cls, data: dict) -> "User":
        """Создать объект User из словаря данных."""
        return cls(
            user_id=data["id"],
            name=data["name"],
            email=data["email"],
            position=data.get("position", "Сотрудник"),
            role=data.get("role", "сотрудник"),
        )

    def to_dict(self) -> dict:
        """Преобразовать объект пользователя в словарь для JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "position": self.position,
            "role": self.role,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return f"{self.name} ({self.position}, {self.email})"


def add_user(
    users: List[User],
    name: str,
    email: str,
    position: str = "Сотрудник",
    role: str = "сотрудник",
) -> User:
    """Создать пользователя и добавить его в коллекцию."""
    new_id = max([u.id for u in users], default=0) + 1
    user = User(
        user_id=new_id,
        name=name,
        email=email,
        position=position,
        role=role,
    )
    users.append(user)
    return user


def find_user(users: List[User], query: str) -> List[User]:
    """Найти пользователей по подстроке в имени или email."""
    lower_query = query.lower()
    return [
        u for u in users
        if lower_query in u.name.lower() or lower_query in u.email.lower()
    ]


def find_user_by_id(
    users: List[User],
    user_id: int,
) -> Optional[User]:
    """Найти пользователя по его идентификатору."""
    for u in users:
        if u.id == user_id:
            return u
    return None


def show_employees(employees: List[User]) -> None:
    """Вывести список сотрудников (преемственность с ПР1)."""
    print(f"{len(employees)} сотрудников в системе:")
    for employee in employees:
        print(f"- {employee}")


def show_users(users: List[User]) -> None:
    """Вывести список пользователей в виде таблицы."""
    if not users:
        print("Список пользователей пуст.")
        return
    print("-" * 75)
    print(f"{'ID':<4} | {'ФИО / Имя':<24} | {'Должность':<20} | {'Email':<22}")
    print("-" * 75)
    for u in users:
        print(
            f"{u.id:<4} | {u.name[:24]:<24} | "
            f"{u.position[:20]:<20} | {u.email:<22}"
        )
    print("-" * 75)
