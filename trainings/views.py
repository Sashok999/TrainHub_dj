"""Страницы обучения используют существующие назначения Enrollment."""

from django.conf import settings
from django.shortcuts import render

from homepage.data import load_project_data, project_query
from homepage.views import not_found
from models.enrollments import find_enrollment_by_id


def trainings(request):
    _, _, assignments, _ = load_project_data()
    active = request.GET.get('status') == 'active'
    if active:
        if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
            ids = {row['id'] for row in project_query('active_trainings')}
            assignments = [item for item in assignments if item.id in ids]
        else:
            assignments = [item for item in assignments
                           if not item.is_cancelled and not item.is_completed]
    return render(request, 'trainings/list.html', {
        'title': 'Обучения', 'trainings': assignments, 'active': active,
    })


def training_detail(request, training_id):
    _, _, assignments, outcomes = load_project_data()
    training = find_enrollment_by_id(assignments, training_id)
    if training is None:
        return not_found(
            request, 'Обучение не найдено',
            'trainings:trainings', 'К обучениям',
        )
    return render(request, 'trainings/detail.html', {
        'title': f'Обучение №{training.id}', 'training': training,
        'results': [r for r in outcomes if r.enrollment.id == training.id],
    })
