
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('reports/<int:rep_id>/', views.reports),
]
