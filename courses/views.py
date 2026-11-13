"""Каталог, карточка и поиск доступных для назначения курсов."""

from datetime import date

from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from homepage.data import load_project_data, project_query
from homepage.views import not_found
from models.courses import find_course_by_id
from models.enrollments import is_course_available
from models.users import find_user_by_id


def courses(request):
    catalog, _, _, _ = load_project_data()
    mandatory = request.GET.get('mandatory') == '1'
    if mandatory:
        if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
            ids = {row['id'] for row in project_query('mandatory_courses')}
            catalog = [item for item in catalog if item.id in ids]
        else:
            catalog = [item for item in catalog if item.is_mandatory]
    return render(request, 'courses/list.html', {
        'title': 'Курсы', 'courses': catalog, 'mandatory': mandatory,
    })


def course_detail(request, course_id):
    catalog, staff, trainings, _ = load_project_data()
    course = find_course_by_id(catalog, course_id)
    if course is None:
        return not_found(
            request, 'Курс не найден', 'courses:courses', 'К курсам',
        )
    if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
        ids = {row['id'] for row in project_query(
            'course_trainings', (course_id,),
        )}
        trainings = [item for item in trainings if item.id in ids]
    else:
        trainings = [item for item in trainings if item.course.id == course_id]
    today = timezone.localdate()
    availability = [{
        'employee': employee,
        'available': is_course_available(
            trainings, course, employee, today.isoformat(),
        ),
    } for employee in staff]
    return render(request, 'courses/detail.html', {
        'title': course.name, 'course': course, 'today': today,
        'availability': availability, 'trainings': trainings,
    })


def available(request):
    catalog, staff, trainings, _ = load_project_data()
    employee_id = request.GET.get('employee', '')
    selected_date = request.GET.get('date', timezone.localdate().isoformat())
    employee = None
    found = None
    error = ''
    if request.GET:
        try:
            employee = find_user_by_id(staff, int(employee_id))
            if employee is None:
                raise ValueError
            parsed = date.fromisoformat(selected_date)
            if parsed.isoformat() != selected_date:
                raise ValueError
        except (ValueError, TypeError):
            error = 'Выберите существующего сотрудника и корректную дату.'
        else:
            if settings.TRAINHUB_DATA_BACKEND == 'sqlite':
                found = project_query(
                    'available_courses', (employee.id, selected_date),
                )
            else:
                found = [c for c in catalog if is_course_available(
                    trainings, c, employee, selected_date,
                )]
    return render(request, 'courses/available.html', {
        'title': 'Доступные курсы', 'employees': staff,
        'employee_id': employee_id, 'selected_date': selected_date,
        'employee': employee, 'courses': found, 'error': error,
    }, status=400 if error else 200)
