"""Просмотр сотрудников с повторным использованием User и функций ПР3."""

from django.conf import settings
from django.shortcuts import render

from homepage.data import load_project_data, project_query
from homepage.views import not_found
from models.enrollments import filter_enrollments_by_user
from models.users import find_user_by_id


def employees(request):
    _, staff, _, _ = load_project_data()
    return render(request, 'employees/list.html', {
        'title': 'Сотрудники', 'employees': staff,
    })


def employee_detail(request, employee_id):
    _, staff, trainings, _ = load_project_data()
    employee = find_user_by_id(staff, employee_id)
    if employee is None:
        return not_found(
            request, 'Сотрудник не найден',
            'employees:employees', 'К сотрудникам',
        )
    if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
        ids = {row['id'] for row in project_query(
            'employee_trainings', (employee_id,),
        )}
        assignments = [item for item in trainings if item.id in ids]
    else:
        assignments = filter_enrollments_by_user(trainings, employee_id)
    return render(request, 'employees/detail.html', {
        'title': employee.name, 'employee': employee,
        'trainings': assignments,
    })
