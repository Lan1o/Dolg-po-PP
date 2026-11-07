from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, ThesisViewSet, StageViewSet, student_history

router = DefaultRouter()
router.register('applications', ApplicationViewSet, basename='application')
router.register('theses', ThesisViewSet, basename='thesis')
router.register('stages', StageViewSet, basename='stage')

urlpatterns = [
    path('', include(router.urls)),
    path('theses/<int:thesis_id>/history/', student_history, name='student-history'), # НОВЫЙ МАРШРУТ
]