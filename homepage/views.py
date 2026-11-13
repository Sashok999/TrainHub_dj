"""Главная, SQL-статистика и общая страница ошибки через Django templates."""

from django.conf import settings
from django.shortcuts import render

from .data import load_project_data, project_query


def not_found(request, title, back_route, back_text):
    return render(request, '404.html', {
        'title': title, 'back_route': back_route, 'back_text': back_text,
    }, status=404)


def index(request):
    courses, employees, trainings, results = load_project_data()
    return render(request, 'homepage/index.html', {
        'title': 'Главная', 'courses': courses, 'employees': employees,
        'trainings': trainings, 'results': results,
    })


def statistics(request):
    if settings.TRAINHUB_DATA_BACKEND != 'sqlite':
        return not_found(
            request, 'SQL-статистика недоступна в режиме JSON',
            'homepage:index', 'На главную',
        )
    return render(request, 'homepage/statistics.html', {
        'title': 'Статистика',
        'totals': project_query('training_totals')[0],
        'summary': project_query('result_summary')[0],
        'course_statistics': project_query('course_statistics'),
        'employee_statistics': project_query('employee_statistics'),
        'popular_courses': project_query('popular_courses', (1,)),
    })


def page_not_found(request, exception):
    """Обработчик неизвестных URL при DEBUG=False."""
    return not_found(
        request, '404 - страница не найдена', 'homepage:index', 'На главную',
    )
