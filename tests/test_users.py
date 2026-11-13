"""Тесты для модуля работы с сотрудниками и пользователями."""

from models import User
from models.users import add_user, find_user, find_user_by_id


def test_user_creation():
    """Проверка создания объекта User и его атрибутов."""
    user = User(
        user_id=1,
        name="Иван Иванов",
        email="ivanov@example.com",
        position="Разработчик",
        role="сотрудник",
    )
    assert user.id == 1
    assert user.name == "Иван Иванов"
    assert user.email == "ivanov@example.com"
    assert user.position == "Разработчик"
    assert user.role == "сотрудник"


def test_user_str():
    """Проверка строкового представления пользователя."""
    user = User(1, "Петр Петров", "petrov@example.com", "Менеджер")
    res = str(user)
    assert "Петр Петров" in res
    assert "Менеджер" in res
    assert "petrov@example.com" in res


def test_user_from_data():
    """Проверка создания объекта User через classmethod from_data."""
    data = {
        "id": 5,
        "name": "Анна Сидорова",
        "email": "anna@example.com",
        "position": "Аналитик",
        "role": "сотрудник",
    }
    user = User.from_data(data)
    assert isinstance(user, User)
    assert user.id == 5
    assert user.name == "Анна Сидорова"
    assert user.email == "anna@example.com"
    assert user.position == "Аналитик"


def test_user_validate_email():
    """Проверка валидации email."""
    assert User.validate_email("user@company.com") is True
    assert User.validate_email("user.name@sub.domain.ru") is True
    assert User.validate_email("invalid_email") is False
    assert User.validate_email("user@domain") is False
    assert User.validate_email("@domain.com") is False


def test_add_user():
    """Проверка добавления пользователя в коллекцию."""
    users = []
    created = add_user(
        users, "Елена Смирнова", "elena@example.com", "Дизайнер"
    )
    assert len(users) == 1
    assert created.id == 1
    assert created.name == "Елена Смирнова"


def test_find_user():
    """Проверка поиска пользователей по имени или email."""
    users = [
        User(1, "Иван Иванов", "ivan@test.ru"),
        User(2, "Сергей Смирнов", "sergey@test.ru"),
    ]
    found = find_user(users, "иван")
    assert len(found) == 1
    assert found[0].id == 1

    found_by_email = find_user(users, "sergey@")
    assert len(found_by_email) == 1
    assert found_by_email[0].id == 2


def test_find_user_by_id():
    """Проверка поиска пользователя по ID."""
    users = [User(10, "Алексей", "alex@test.ru")]
    assert find_user_by_id(users, 10) is not None
    assert find_user_by_id(users, 99) is None
