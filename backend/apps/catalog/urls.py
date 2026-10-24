from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TopicViewSet, DirectionViewSet


router = DefaultRouter()
router.register('topics', TopicViewSet, basename='topic')
router.register('directions', DirectionViewSet, basename='direction')

urlpatterns = [
    path('', include(router.urls)),
]