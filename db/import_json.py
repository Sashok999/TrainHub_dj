"""Однократный атомарный импорт: python -m db.import_json."""

import argparse
from datetime import date
import json
from pathlib import Path
import sqlite3

from db.database import BASE_DIR, DB_PATH, connection, initialize_database
from models.courses import Course
from models.enrollments import Enrollment
from models.results import Result
from models.users import User


class AlreadyImportedError(ValueError):
    """База уже содержит данные или отметку успешного импорта."""


def load_json(path):
    """Не превращать поврежденный или отсутствующий файл в пустой список."""
    with Path(path).open(encoding='utf-8-sig') as stream:
        data = json.load(stream)
    if not isinstance(data, list) or any(
        not isinstance(item, dict) for item in data
    ):
        raise ValueError(f'{path}: ожидается список объектов JSON.')
    return data


def import_data(data_dir=BASE_DIR / 'data', db_path=DB_PATH):
    """Сохранить все четыре коллекции целиком или откатить весь импорт."""
    data_dir = Path(data_dir)
    # Сохраняются правила и значения по умолчанию существующих классов.
    employees = [User.from_data(i) for i in load_json(
        data_dir / 'users.json',
    )]
    courses = [Course.from_data(i) for i in load_json(
        data_dir / 'courses.json',
    )]
    staff = {item.id: item for item in employees}
    catalog = {item.id: item for item in courses}
    trainings = []
    for item in load_json(data_dir / 'enrollments.json'):
        date.fromisoformat(item['enrollment_date'])
        trainings.append(Enrollment(
            item['id'], catalog[item['course_id']], item['enrollment_date'],
            staff[item['user_id']], item.get('is_cancelled', False),
            item.get('is_completed', False),
        ))
    assignments = {item.id: item for item in trainings}
    results = [Result(
        item['id'], assignments[item['enrollment_id']], item['score'],
        item['completed_date'], item.get('comment', ''),
    ) for item in load_json(data_dir / 'results.json')]

    initialize_database(db_path)
    with connection(db_path) as conn:
        # Блокировка до проверки исключает два одновременных импорта.
        conn.execute('BEGIN IMMEDIATE')
        populated = conn.execute('''
            SELECT EXISTS(SELECT 1 FROM employees)
                OR EXISTS(SELECT 1 FROM courses)
                OR EXISTS(SELECT 1 FROM trainings)
                OR EXISTS(SELECT 1 FROM results)
        ''').fetchone()[0]
        if populated or conn.execute('PRAGMA user_version').fetchone()[0]:
            raise AlreadyImportedError(
                'Импорт пропущен: база уже заполнена. Данные не изменены.',
            )
        conn.executemany('''
            INSERT INTO employees (id, name, email, position, role)
            VALUES (?, ?, ?, ?, ?)
        ''', [(e.id, e.name, e.email, e.position, e.role) for e in employees])
        conn.executemany('''
            INSERT INTO courses
                (id, name, description, duration_days,
                 course_type, is_mandatory)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [(
            c.id, c.name, c.description, c.duration_days,
            c.course_type, c.is_mandatory,
        ) for c in courses])
        conn.executemany('''
            INSERT INTO trainings
                (id, employee_id, course_id, enrollment_date,
                 is_cancelled, is_completed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [(
            t.id, t.user.id, t.course.id, t.enrollment_date,
            t.is_cancelled, t.is_completed,
        ) for t in trainings])
        conn.executemany('''
            INSERT INTO results
                (id, training_id, score, completed_date, comment)
            VALUES (?, ?, ?, ?, ?)
        ''', [(
            r.id, r.enrollment.id, r.score, r.completed_date, r.comment,
        ) for r in results])
        # Отметка защищает от повторного импорта даже пустого набора JSON.
        conn.execute('PRAGMA user_version = 1')
    return {
        'employees': len(employees), 'courses': len(courses),
        'trainings': len(trainings), 'results': len(results),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BASE_DIR / 'data')
    parser.add_argument('--database', type=Path, default=DB_PATH)
    args = parser.parse_args()
    try:
        counts = import_data(args.data_dir, args.database)
    except AlreadyImportedError as exc:
        print(exc)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f'Ошибка импорта: {exc}\n')
    else:
        print(f'Импорт завершен: {counts}. База: {args.database}')


if __name__ == '__main__':
    main()
