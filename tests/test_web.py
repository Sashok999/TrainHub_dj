"""Проверки маршрутов, связей, 404 и безопасного отображения JSON."""

import hashlib
from html.parser import HTMLParser

import pytest
from django.conf import settings
from django.test import override_settings

from storage import load_courses, save_courses


@pytest.mark.parametrize('url,text', [
    ('/', 'Система учета корпоративного обучения'),
    ('/employees/', 'Иван Иванов'),
    ('/employees/1/', 'Инженер-программист'),
    ('/courses/', 'Введение в корпоративную безопасность'),
    ('/courses/1/', 'Доступность назначения на'),
    ('/trainings/', 'Завершено'),
    ('/trainings/1/', 'Иван Иванов'),
    ('/trainings/2/', '/results/1/'),
    ('/results/', '92 / 100'),
    ('/results/1/', '/trainings/2/'),
])
def test_pages_use_existing_data(client, url, text):
    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert text in html
    assert '<!DOCTYPE html>' in html
    assert '<html lang="ru">' in html
    assert 'name="viewport"' in html
    assert 'bootstrap@5.3.3' in html


@pytest.mark.parametrize('section', [
    'employees', 'courses', 'trainings', 'results',
])
def test_missing_object_returns_404(client, section):
    response = client.get(f'/{section}/999/')
    assert response.status_code == 404
    assert 'не найден' in response.content.decode()


@pytest.mark.parametrize('url', [
    '/nonexistent/', '/courses/abc/', '/trainings/-1/', '/results/1/extra/',
])
def test_custom_404_with_debug_disabled(client, url):
    with override_settings(DEBUG=False):
        response = client.get(url)
    assert response.status_code == 404
    assert '404 - страница не найдена' in response.content.decode()
    assert 'На главную' in response.content.decode()


def test_links_between_all_pages(client):
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = set()

        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                if tag == 'a' and name == 'href' and value.startswith('/'):
                    self.urls.add(value)

    pending = ['/']
    visited = set()
    while pending:
        url = pending.pop()
        if url in visited:
            continue
        response = client.get(url)
        assert response.status_code == 200, url
        visited.add(url)
        parser = Links()
        parser.feed(response.content.decode())
        pending.extend(parser.urls - visited)
    assert '/results/1/' in visited
    assert '/employees/3/' in visited
    assert '/trainings/2/' in visited


def test_empty_data_is_displayed(client, tmp_path):
    with override_settings(
        TRAINHUB_DATA_DIR=tmp_path, TRAINHUB_DATA_BACKEND='json',
    ):
        urls = ['/', '/employees/', '/courses/', '/trainings/', '/results/']
        for url in urls:
            assert client.get(url).status_code == 200
        assert client.get('/courses/1/').status_code == 404


def test_html_from_json_is_escaped(client, tmp_path):
    courses = load_courses(settings.TRAINHUB_DATA_DIR / 'courses.json')
    courses[0].name = '<script>alert("x")</script>'
    courses[0].description = '<img src=x onerror=alert(1)>'
    save_courses(str(tmp_path / 'courses.json'), courses)
    with override_settings(
        TRAINHUB_DATA_DIR=tmp_path, TRAINHUB_DATA_BACKEND='json',
    ):
        response = client.get('/courses/1/')
    html = response.content.decode()
    assert '<script>' not in html
    assert '<img src=x' not in html
    assert '&lt;script&gt;' in html
    assert '&lt;img' in html


def test_get_does_not_modify_data(client):
    paths = list(settings.TRAINHUB_DATA_DIR.glob('*.json'))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    for url in ['/', '/trainings/2/', '/results/1/', '/courses/1/']:
        assert client.get(url).status_code == 200
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert before == after


def test_web_data_paths_do_not_depend_on_cwd(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert client.get('/employees/1/').status_code == 200
