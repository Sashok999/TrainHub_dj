"""Список и карточка результатов корпоративного обучения."""

from django.shortcuts import render

from homepage.data import load_project_data
from homepage.views import not_found
from models.results import find_result_by_id


def results(request):
    _, _, _, outcomes = load_project_data()
    return render(request, 'results/list.html', {
        'title': 'Результаты', 'results': outcomes,
    })


def result_detail(request, result_id):
    _, _, _, outcomes = load_project_data()
    result = find_result_by_id(outcomes, result_id)
    if result is None:
        return not_found(
            request, 'Результат не найден', 'results:results', 'К результатам',
        )
    return render(request, 'results/detail.html', {
        'title': f'Результат №{result.id}', 'result': result,
        'training': result.enrollment,
    })
