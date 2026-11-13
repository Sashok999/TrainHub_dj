"""Единая точка загрузки существующих объектов из SQLite или JSON."""

from django.conf import settings

from db.database import connection, select
from models.courses import Course
from models.enrollments import Enrollment
from models.results import Result
from models.users import User
from storage import load_courses, load_enrollments, load_results, load_users


def load_project_data():
    """Получить связанные объекты без зависимости от рабочей папки сервера."""
    if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
        return load_sql_data()
    if settings.TRAINHUB_DATA_BACKEND != 'json':
        raise ValueError('TRAINHUB_DATA_BACKEND должен быть sqlite или json.')
    data_dir = settings.TRAINHUB_DATA_DIR
    courses = load_courses(data_dir / 'courses.json')
    employees = load_users(data_dir / 'users.json')
    trainings = load_enrollments(
        data_dir / 'enrollments.json', courses, employees,
    )
    results = load_results(data_dir / 'results.json', trainings)
    return courses, employees, trainings, results


def load_sql_data():
    """Восстановить те же классы ПР3 из именованных SQL-выборок."""
    with connection(settings.TRAINHUB_DATABASE, readonly=True) as conn:
        conn.execute('BEGIN')
        courses = [Course.from_data(dict(row))
                   for row in select(conn, 'courses')]
        employees = [User.from_data(dict(row))
                     for row in select(conn, 'employees')]
        catalog = {item.id: item for item in courses}
        staff = {item.id: item for item in employees}
        trainings = [Enrollment(
            row['id'], catalog[row['course_id']], row['enrollment_date'],
            staff[row['employee_id']], bool(row['is_cancelled']),
            bool(row['is_completed']),
        ) for row in select(conn, 'trainings')]
        assignments = {item.id: item for item in trainings}
        results = [Result(
            row['id'], assignments[row['training_id']], row['score'],
            row['completed_date'], row['comment'],
        ) for row in select(conn, 'results')]
    return courses, employees, trainings, results


def project_query(name, parameters=()):
    """Получить sqlite3.Row для контекста страниц ПР7."""
    with connection(settings.TRAINHUB_DATABASE, readonly=True) as conn:
        return select(conn, name, parameters)
