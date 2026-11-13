"""Доступность SQL-функций в навигации совместимого режима ПР6."""

from django.conf import settings


def data_backend(request):
    return {'sql_enabled': settings.TRAINHUB_DATA_BACKEND == 'sqlite'}
