from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, ThesisViewSet, StageViewSet


router = DefaultRouter()
router.register('applications', ApplicationViewSet, basename='application')
router.register('theses', ThesisViewSet, basename='thesis')
router.register('stages', StageViewSet, basename='stage')

urlpatterns = [
    path('', include(router.urls)),
]