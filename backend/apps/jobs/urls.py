"""
URL configuration for jobs app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, ImageTaskViewSet, DescriptionTaskViewSet, AIDescribeView

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'image-tasks', ImageTaskViewSet, basename='imagetask')
router.register(r'description-tasks', DescriptionTaskViewSet, basename='descriptiontask')
router.register(r'ai/describe', AIDescribeView, basename='ai-describe')

urlpatterns = [
    path('', include(router.urls)),
]

