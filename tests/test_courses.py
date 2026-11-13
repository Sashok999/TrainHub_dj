"""Тесты для модуля работы с учебными курсами."""

from models import Course
from models.courses import (
    add_course,
    check_course_duration,
    filter_courses_by_duration,
    find_course,
    sort_courses,
)


def test_course_creation():
    """Проверка создания объекта Course и его атрибутов."""
    course = Course(
        course_id=1,
        name="Python: базовый уровень",
        description="Курс для начинающих разработчиков",
        duration_days=10,
        course_type="онлайн",
        is_mandatory=True,
    )
    assert course.id == 1
    assert course.name == "Python: базовый уровень"
    assert course.duration_days == 10
    assert course.course_type == "онлайн"
    assert course.is_mandatory is True


def test_course_is_suitable_for():
    """Проверка метода проверки соответствия длительности курса."""
    course = Course(
        course_id=1,
        name="Вводный инструктаж",
        description="Краткий курс",
        duration_days=3,
    )
    assert course.is_suitable_for(5) is True
    assert course.is_suitable_for(3) is True
    assert course.is_suitable_for(2) is False


def test_validate_duration():
    """Проверка статического метода валидации длительности."""
    assert Course.validate_duration(1) is True
    assert Course.validate_duration(30) is True
    assert Course.validate_duration(0) is False
    assert Course.validate_duration(-5) is False


def test_course_str():
    """Проверка строкового представления объекта Course."""
    course = Course(
        course_id=2,
        name="Охрана труда",
        description="Инструктаж",
        duration_days=5,
        course_type="онлайн",
        is_mandatory=False,
    )
    res = str(course)
    assert "Охрана труда" in res
    assert "5 дн." in res


def test_add_course():
    """Проверка добавления курса в коллекцию."""
    courses = []
    created = add_course(
        courses,
        name="Git для команды",
        description="Основы контроля версий",
        duration_days=4,
    )
    assert len(courses) == 1
    assert created.id == 1
    assert created.name == "Git для команды"


def test_find_course():
    """Проверка поиска курсов по подстроке."""
    courses = [
        Course(1, "Архитектура ПО", "Принципы SOLID", 14),
        Course(2, "Базы данных", "SQL и проектирование", 21),
    ]
    found = find_course(courses, "базы")
    assert len(found) == 1
    assert found[0].id == 2


def test_check_course_duration():
    """Проверка соответствия длительности курса лимиту."""
    courses = [Course(1, "Спринт по Python", "Интенсив", 7)]
    assert check_course_duration(courses, 1, 10) is True
    assert check_course_duration(courses, 1, 5) is False
    assert check_course_duration(courses, 999, 10) is False


def test_filter_courses_by_duration():
    """Проверка фильтрации курсов по длительности."""
    courses = [
        Course(1, "Короткий курс", "", 2),
        Course(2, "Средний курс", "", 7),
        Course(3, "Длинный курс", "", 30),
    ]
    filtered = filter_courses_by_duration(courses, 7)
    assert len(filtered) == 2
    assert [c.id for c in filtered] == [1, 2]


def test_sort_courses():
    """Проверка сортировки курсов по длительности."""
    courses = [
        Course(1, "Курс Б", "", 20),
        Course(2, "Курс А", "", 5),
        Course(3, "Курс В", "", 12),
    ]
    sorted_list = sort_courses(courses)
    assert [c.duration_days for c in sorted_list] == [5, 12, 20]
