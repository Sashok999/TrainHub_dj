from django.urls import path

from . import views

app_name = 'results'

urlpatterns = [
    path('', views.results, name='results'),
    path('<int:result_id>/', views.result_detail, name='result_detail'),
]
