from django.urls import path

from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employees, name='employees'),
    path('<int:employee_id>/', views.employee_detail, name='employee_detail'),
]
