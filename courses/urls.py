from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.courses, name='courses'),
    path('available/', views.available, name='available'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
]
