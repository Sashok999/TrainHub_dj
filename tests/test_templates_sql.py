"""Полные HTTP-сценарии ПР6/ПР7: шаблоны, SQLite и статика."""

import hashlib
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.test import override_settings
from django.test.utils import setup_test_environment, teardown_test_environment

from db.database import connection, initialize_database


@pytest.fixture
def template_environment():
    setup_test_environment()
    yield
    teardown_test_environment()


@pytest.mark.parametrize('url,template', [
    ('/', 'homepage/index.html'),
    ('/employees/', 'employees/list.html'),
    ('/employees/1/', 'employees/detail.html'),
    ('/courses/', 'courses/list.html'),
    ('/courses/1/', 'courses/detail.html'),
    ('/trainings/', 'trainings/list.html'),
    ('/trainings/1/', 'trainings/detail.html'),
    ('/results/', 'results/list.html'),
    ('/results/1/', 'results/detail.html'),
    ('/courses/available/', 'courses/available.html'),
    ('/statistics/', 'homepage/statistics.html'),
])
def test_pages_render_templates(
    client, template_environment, url, template,
):
    response = client.get(url)
    assert response.status_code == 200
    names = {t.name for t in response.templates}
    assert {template, 'base.html', 'includes/navigation.html'} <= names
    assert response.context['title']


def test_sql_changes_appear_without_json_reads(
    client, sql_database, monkeypatch,
):
    def fail(*args, **kwargs):
        raise AssertionError('JSON must not be read in SQL mode')
    for name in (
        'load_courses', 'load_users', 'load_enrollments', 'load_results',
    ):
        monkeypatch.setattr(f'homepage.data.{name}', fail)
    with connection(sql_database) as conn:
        conn.execute('UPDATE employees SET name = ? WHERE id = ?', (
            'Сотрудник из SQLite', 1,
        ))
        conn.execute('UPDATE courses SET name = ? WHERE id = ?', (
            '<script>alert("x")</script>', 1,
        ))
    assert 'Сотрудник из SQLite' in client.get('/employees/').content.decode()
    html = client.get('/courses/1/').content.decode()
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


def test_sql_filters_and_statistics(client, template_environment):
    catalog = client.get('/courses/?mandatory=1')
    assert [c.id for c in catalog.context['courses']] == [1, 2]
    active = client.get('/trainings/?status=active')
    assert [t.id for t in active.context['trainings']] == [1]
    stats = client.get('/statistics/')
    assert stats.context['totals']['completed'] == 1
    assert '92,0' in stats.content.decode()


@pytest.mark.parametrize('employee,date,expected', [
    (1, '2026-10-01', [2, 3]),
    (1, '2026-10-02', [1, 2, 3]),
    (2, '2026-10-05', [1, 3]),
    (3, '2026-10-01', [1, 2, 3]),
])
def test_available_course_search(
    client, template_environment, employee, date, expected,
):
    response = client.get('/courses/available/', {
        'employee': employee, 'date': date,
    })
    assert response.status_code == 200
    assert [c['id'] for c in response.context['courses']] == expected


@pytest.mark.parametrize('parameters', [
    {'employee': '1 OR 1=1', 'date': '2026-10-01'},
    {'employee': '999', 'date': '2026-10-01'},
    {'employee': '1', 'date': '2026-02-30'},
    {'employee': '1', 'date': "2026-10-01'; DROP TABLE courses; --"},
    {'employee': '1', 'date': '20261001'},
    {'employee': '', 'date': ''},
])
def test_search_rejects_invalid_parameters(client, parameters):
    assert client.get('/courses/available/', parameters).status_code == 400
    assert client.get('/courses/').status_code == 200


def test_empty_sql_pages_and_statistics(client, tmp_path):
    path = tmp_path / 'empty.sqlite'
    initialize_database(path)
    with override_settings(TRAINHUB_DATABASE=path):
        for url in (
            '/', '/employees/', '/courses/', '/trainings/', '/results/',
            '/statistics/', '/courses/available/',
        ):
            response = client.get(url)
            assert response.status_code == 200
            assert 'None' not in response.content.decode()
        for section in ('employees', 'courses', 'trainings', 'results'):
            assert client.get(f'/{section}/1/').status_code == 404


def test_get_does_not_change_sql_database(client, sql_database):
    before = hashlib.sha256(sql_database.read_bytes()).hexdigest()
    for url in (
        '/', '/employees/1/', '/courses/1/', '/trainings/2/', '/results/1/',
        '/statistics/', '/courses/available/?employee=1&date=2026-10-01',
    ):
        assert client.get(url).status_code == 200
    assert hashlib.sha256(sql_database.read_bytes()).hexdigest() == before


def test_styles_image_and_javascript_are_connected(client):
    html = client.get('/courses/available/').content.decode()
    for name in ('css/style.css', 'img/logo.svg', 'js/main.js'):
        relative = f'homepage/{name}'
        assert Path(finders.find(relative)).is_file()
        assert f'/static/{relative}' in html


def test_legacy_json_pages_work_without_sql_database(client, tmp_path):
    with override_settings(
        TRAINHUB_DATA_BACKEND='json',
        TRAINHUB_DATABASE=tmp_path / 'does-not-exist.sqlite',
    ):
        for url in (
            '/', '/employees/', '/employees/1/', '/courses/', '/courses/1/',
            '/trainings/', '/trainings/2/', '/results/', '/results/1/',
            '/courses/?mandatory=1', '/trainings/?status=active',
            '/courses/available/?employee=1&date=2026-10-01',
        ):
            response = client.get(url)
            assert response.status_code == 200
            assert 'href="/statistics/"' not in response.content.decode()
        assert client.get('/statistics/').status_code == 404
