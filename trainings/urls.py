from django.urls import path

from . import views

app_name = 'trainings'

urlpatterns = [
    path('', views.trainings, name='trainings'),
    path('<int:training_id>/', views.training_detail, name='training_detail'),
]
