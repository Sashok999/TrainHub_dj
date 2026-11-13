"""Главный модуль приложения TrainHub.

Обеспечивает взаимодействие с пользователем через консольное меню,
оркестрацию объектов предметной области (Course, User, Enrollment)
и сохранение результатов в JSON-хранилище.
"""

from typing import List

from models import Course, Enrollment, User
from models.courses import (
    add_course,
    check_course_duration,
    find_course,
    find_course_by_id,
    show_courses,
    sort_courses,
)
from models.enrollments import (
    cancel_enrollment,
    get_enrollment_status,
    is_course_available,
    register_on_courses,
    show_enrollments,
)
from models.users import (
    add_user,
    find_user,
    find_user_by_id,
    show_employees,
    show_users,
)
from storage import (
    load_courses,
    load_enrollments,
    load_users,
    save_courses,
    save_enrollments,
    save_users,
)
from utils import input_date, input_int, input_non_empty_str

DATA_COURSES = "data/courses.json"
DATA_USERS = "data/users.json"
DATA_ENROLLMENTS = "data/enrollments.json"


def create_new_enrollment(
    enrollments: List[Enrollment],
    courses: List[Course],
    users: List[User],
) -> None:
    """Интерактивный сценарий назначения курса сотруднику."""
    print("\n--- Назначение курса сотруднику ---")
    if not courses:
        print("Ошибка: в системе нет доступных курсов.")
        return
    if not users:
        print("Ошибка: в системе нет сотрудников.")
        return

    show_courses(courses)
    course_id = input_int("Введите ID курса: ", min_value=1)
    course = find_course_by_id(courses, course_id)
    if course is None:
        print(f"Курс с ID {course_id} не найден.")
        return

    show_employees(users)
    user_id = input_int("Введите ID сотрудника: ", min_value=1)
    user = find_user_by_id(users, user_id)
    if user is None:
        print(f"Сотрудник с ID {user_id} не найден.")
        return

    date_str = input_date("Введите дату назначения (ГГГГ-ММ-ДД): ")

    enrollment = register_on_courses(enrollments, user, course, date_str)
    if enrollment is None:
        print("Не удалось создать назначение:")
        print(get_enrollment_status(False))
    else:
        print("Назначение успешно создано!")
        print(
            f"Сотрудник {user.name} записан на курс "
            f"'{course.name}' на {date_str}."
        )
        print(f"ID записи: {enrollment.id}")


def handle_check_availability(
    enrollments: List[Enrollment],
    courses: List[Course],
    users: List[User],
) -> None:
    """Проверка возможности записи сотрудника на курс."""
    print("\n--- Проверка доступности назначения ---")
    course_id = input_int("Введите ID курса: ", min_value=1)
    course = find_course_by_id(courses, course_id)
    if course is None:
        print("Курс не найден.")
        return

    user_id = input_int("Введите ID сотрудника: ", min_value=1)
    user = find_user_by_id(users, user_id)
    if user is None:
        print("Сотрудник не найден.")
        return

    date_str = input_date("Введите дату для проверки (ГГГГ-ММ-ДД): ")
    available = is_course_available(enrollments, course, user, date_str)
    print(get_enrollment_status(available))


def handle_check_duration(courses: List[Course]) -> None:
    """Проверка соответствия длительности курса допустимому лимиту."""
    print("\n--- Проверка длительности курса ---")
    course_id = input_int("Введите ID курса: ", min_value=1)
    course = find_course_by_id(courses, course_id)
    if course is None:
        print("Курс не найден.")
        return

    max_days = input_int("Введите допустимый лимит (в днях): ", min_value=1)
    fits = check_course_duration(courses, course_id, max_days)
    if fits:
        print(
            f"Курс '{course.name}' ({course.duration_days} дн.) "
            f"укладывается в лимит {max_days} дн."
        )
    else:
        print(
            f"Курс '{course.name}' ({course.duration_days} дн.) "
            f"превышает лимит {max_days} дн."
        )


def handle_add_course(courses: List[Course]) -> None:
    """Добавить новый курс в каталог."""
    print("\n--- Добавление нового курса ---")
    name = input_non_empty_str("Введите название курса: ")
    description = input("Введите описание курса: ").strip()
    duration = input_int("Введите длительность курса в днях: ", min_value=1)
    course_type = input(
        "Введите формат (онлайн/очно) [онлайн]: "
    ).strip() or "онлайн"
    mandatory_choice = input(
        "Является ли курс обязательным? (д/н) [н]: "
    ).strip().lower()
    is_mandatory = mandatory_choice in ("д", "y", "yes", "да")

    course = add_course(
        courses,
        name=name,
        description=description,
        duration_days=duration,
        course_type=course_type,
        is_mandatory=is_mandatory,
    )
    print(f"Курс успешно добавлен: {course}")


def handle_add_user(users: List[User]) -> None:
    """Добавить нового сотрудника в систему."""
    print("\n--- Добавление сотрудника ---")
    name = input_non_empty_str("Введите ФИО сотрудника: ")
    while True:
        email = input_non_empty_str("Введите рабочий email: ")
        if User.validate_email(email):
            break
        print("Некорректный email. Пример: employee@company.ru")

    position = input(
        "Введите должность [Сотрудник]: "
    ).strip() or "Сотрудник"
    user = add_user(users, name=name, email=email, position=position)
    print(f"Сотрудник успешно добавлен: {user}")


def handle_cancel_enrollment(enrollments: List[Enrollment]) -> None:
    """Отмена назначения курса."""
    print("\n--- Отмена назначения на курс ---")
    if not enrollments:
        print("Список назначений пуст.")
        return
    show_enrollments(enrollments)
    prompt = "Введите ID назначения для отмены: "
    enrollment_id = input_int(prompt, min_value=1)
    success = cancel_enrollment(enrollments, enrollment_id)
    if success:
        print(f"Назначение #{enrollment_id} успешно отменено.")
    else:
        print(f"Назначение с ID {enrollment_id} не найдено.")


# Сохраняем функции ПР1 для демонстрации преемственности этапов
def create_courses() -> str:
    """Функция создания курса из ПР1 (сохранена для преемственности)."""
    print("enter course name:")
    return input()


def main() -> None:
    """Точка запуска приложения TrainHub."""
    courses = load_courses(DATA_COURSES)
    users = load_users(DATA_USERS)
    enrollments = load_enrollments(DATA_ENROLLMENTS, courses, users)

    print("=" * 60)
    print("  TrainHub — Система учета корпоративного обучения (ПР3)")
    print("=" * 60)

    while True:
        print("\n=== Главное меню ===")
        print("1. Показать список курсов")
        print("2. Найти курс по названию")
        print("3. Проверить длительность курса")
        print("4. Отсортировать курсы по длительности")
        print("5. Показать сотрудников")
        print("6. Найти сотрудника")
        print("7. Проверить доступность назначения на курс")
        print("8. Назначить курс сотруднику (Зарегистрировать)")
        print("9. Отменить назначение")
        print("10. Показать все назначения")
        print("11. Добавить новый курс")
        print("12. Добавить сотрудника")
        print("0. Выход и сохранение")

        choice = input_int("Выберите действие: ", min_value=0, max_value=12)

        if choice == 1:
            show_courses(courses)
        elif choice == 2:
            q = input_non_empty_str("Введите поисковый запрос: ")
            results = find_course(courses, q)
            show_courses(results)
        elif choice == 3:
            handle_check_duration(courses)
        elif choice == 4:
            sorted_c = sort_courses(courses)
            show_courses(sorted_c)
        elif choice == 5:
            show_users(users)
        elif choice == 6:
            q = input_non_empty_str("Введите имя или email для поиска: ")
            found = find_user(users, q)
            show_users(found)
        elif choice == 7:
            handle_check_availability(enrollments, courses, users)
        elif choice == 8:
            create_new_enrollment(enrollments, courses, users)
            save_enrollments(DATA_ENROLLMENTS, enrollments)
        elif choice == 9:
            handle_cancel_enrollment(enrollments)
            save_enrollments(DATA_ENROLLMENTS, enrollments)
        elif choice == 10:
            show_enrollments(enrollments)
        elif choice == 11:
            handle_add_course(courses)
            save_courses(DATA_COURSES, courses)
        elif choice == 12:
            handle_add_user(users)
            save_users(DATA_USERS, users)
        elif choice == 0:
            save_courses(DATA_COURSES, courses)
            save_users(DATA_USERS, users)
            save_enrollments(DATA_ENROLLMENTS, enrollments)
            print("Данные сохранены. Завершение работы программы.")
            break


if __name__ == "__main__":
    main()
