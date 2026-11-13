"""Целостность SQL, атомарность импорта и результаты предметных запросов."""

import json
import sqlite3

import pytest

from db.database import (
    BASE_DIR, connection, get_connection, initialize_database, queries, select,
)
from db.import_json import AlreadyImportedError, import_data
from homepage.data import load_project_data
from storage import load_courses, load_enrollments, load_results, load_users


def source_copy(tmp_path):
    data_dir = tmp_path / 'source'
    data_dir.mkdir()
    for source in (BASE_DIR / 'data').glob('*.json'):
        (data_dir / source.name).write_bytes(source.read_bytes())
    return data_dir


def test_import_preserves_every_source_field(sql_database):
    catalog = load_courses(BASE_DIR / 'data/courses.json')
    employees = load_users(BASE_DIR / 'data/users.json')
    trainings = load_enrollments(
        BASE_DIR / 'data/enrollments.json', catalog, employees,
    )
    results = load_results(BASE_DIR / 'data/results.json', trainings)
    from django.test import override_settings
    with override_settings(
        TRAINHUB_DATABASE=sql_database, TRAINHUB_DATA_BACKEND='sqlite',
    ):
        actual = load_project_data()
    expected = (catalog, employees, trainings, results)
    for source, imported in zip(expected, actual):
        source_rows = sorted(
            [x.to_dict() for x in source], key=lambda x: x['id'],
        )
        imported_rows = sorted(
            [x.to_dict() for x in imported], key=lambda x: x['id'],
        )
        assert source_rows == imported_rows


def test_repeated_import_preserves_database(sql_database):
    before = sql_database.read_bytes()
    with pytest.raises(AlreadyImportedError):
        import_data(db_path=sql_database)
    assert sql_database.read_bytes() == before


def test_empty_import_is_also_protected(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    for name in ('users', 'courses', 'enrollments', 'results'):
        (source / f'{name}.json').write_text('[]', encoding='utf-8')
    target = tmp_path / 'empty.sqlite'
    assert not any(import_data(source, target).values())
    with pytest.raises(AlreadyImportedError):
        import_data(source, target)


def test_failed_bulk_import_rolls_back_all_rows(tmp_path):
    source = source_copy(tmp_path)
    course_file = source / 'courses.json'
    courses = json.loads(course_file.read_text(encoding='utf-8'))
    courses.append(courses[0])
    course_file.write_text(json.dumps(courses), encoding='utf-8')
    target = tmp_path / 'invalid.sqlite'
    with pytest.raises(sqlite3.IntegrityError):
        import_data(source, target)
    with connection(target) as conn:
        count = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
        assert count == 0
        assert conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0] == 0
        assert conn.execute('PRAGMA user_version').fetchone()[0] == 0
    courses.pop()
    course_file.write_text(json.dumps(courses), encoding='utf-8')
    assert import_data(source, target)['employees'] == 3


@pytest.mark.parametrize('bad_file', ['users.json', 'results.json'])
def test_invalid_json_does_not_create_database(tmp_path, bad_file):
    source = source_copy(tmp_path)
    (source / bad_file).write_text('{broken', encoding='utf-8')
    target = tmp_path / 'bad.sqlite'
    with pytest.raises(ValueError):
        import_data(source, target)
    assert not target.exists()


def test_schema_and_connection_rules(sql_database):
    conn = get_connection(sql_database)
    try:
        assert conn.row_factory is sqlite3.Row
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'",
        ).fetchall()
        assert {r['name'] for r in tables} == {
            'employees', 'courses', 'trainings', 'results',
        }
    finally:
        conn.close()
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute('SELECT 1')


@pytest.mark.parametrize('statement,parameters', [
    ('INSERT INTO trainings VALUES (?, ?, ?, ?, ?, ?)',
     (90, 999, 1, '2026-11-02', 0, 0)),
    ('INSERT INTO trainings VALUES (?, ?, ?, ?, ?, ?)',
     (90, 1, 999, '2026-11-02', 0, 0)),
    ('DELETE FROM employees WHERE id = ?', (1,)),
    ('DELETE FROM courses WHERE id = ?', (1,)),
    ('DELETE FROM trainings WHERE id = ?', (2,)),
    ('INSERT INTO trainings VALUES (?, ?, ?, ?, ?, ?)',
     (90, 1, 1, '2026-10-01', 0, 0)),
    ('INSERT INTO trainings VALUES (?, ?, ?, ?, ?, ?)',
     (90, 1, 1, '2026-02-30', 0, 0)),
    ('INSERT INTO results VALUES (?, ?, ?, ?, ?)',
     (90, 999, 80, '2026-11-02', '')),
    ('INSERT INTO results VALUES (?, ?, ?, ?, ?)',
     (90, 1, 80, '2026-11-02', '')),
    ('INSERT INTO results VALUES (?, ?, ?, ?, ?)',
     (90, 2, 101, '2026-11-02', '')),
    ('INSERT INTO results VALUES (?, ?, ?, ?, ?)',
     (90, 2, 80.5, '2026-11-02', '')),
    ('UPDATE results SET completed_date = ? WHERE id = ?', ('2026-10-01', 1)),
])
def test_database_rejects_invalid_writes(sql_database, statement, parameters):
    with pytest.raises(sqlite3.IntegrityError):
        with connection(sql_database) as conn:
            conn.execute(statement, parameters)


def test_readonly_queries_cannot_write(sql_database):
    with connection(sql_database, readonly=True) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE courses SET name = 'changed'")


def test_all_queries_have_expected_business_results(sql_database):
    with connection(sql_database, readonly=True) as conn:
        assert len(queries()) == 14
        assert len(select(conn, 'employees')) == 3
        assert len(select(conn, 'courses')) == 3
        assert [r['id'] for r in select(conn, 'mandatory_courses')] == [1, 2]
        assert [r['id'] for r in select(conn, 'active_trainings')] == [1]
        assert select(conn, 'trainings')[0]['employee_name'] == 'Иван Иванов'
        assert select(conn, 'results')[0]['score'] == 92
        assert dict(select(conn, 'training_totals')[0]) == {
            'total': 2, 'active': 1, 'completed': 1, 'cancelled': 0,
        }
        summary = select(conn, 'result_summary')[0]
        assert summary['average_score'] == 92
        assert summary['minimum_score'] == summary['maximum_score'] == 92
        courses = select(conn, 'course_statistics')
        assert [r['training_count'] for r in courses] == [1, 1, 0]
        assert [r['completion_rate'] for r in courses] == [0.0, 100.0, None]
        staff = {r['id']: r for r in select(conn, 'employee_statistics')}
        assert staff[2]['average_score'] == 92
        assert staff[3]['average_score'] is None
        assert len(select(conn, 'popular_courses', (1,))) == 2
        assert not select(conn, 'popular_courses', (2,))
        assert [r['id'] for r in select(
            conn, 'available_courses', (1, '2026-10-01'),
        )] == [2, 3]
        assert [r['id'] for r in select(
            conn, 'employee_trainings', (1,),
        )] == [1]
        assert [r['employee_id'] for r in select(
            conn, 'course_trainings', (2,),
        )] == [2]


def test_cancelled_training_is_available_and_result_hidden(sql_database):
    with connection(sql_database) as conn:
        conn.execute(
            'UPDATE trainings SET is_cancelled = 1 WHERE id = ?', (2,),
        )
        assert 2 in {r['id'] for r in select(
            conn, 'available_courses', (2, '2026-10-05'),
        )}
        assert not select(conn, 'results')
        assert select(conn, 'training_totals')[0]['cancelled'] == 1
        assert select(conn, 'training_totals')[0]['completed'] == 0


def test_empty_aggregates_are_defined(tmp_path):
    path = tmp_path / 'empty.sqlite'
    initialize_database(path)
    with connection(path, readonly=True) as conn:
        assert dict(select(conn, 'training_totals')[0]) == {
            'total': 0, 'active': 0, 'completed': 0, 'cancelled': 0,
        }
        assert select(conn, 'result_summary')[0]['average_score'] is None
