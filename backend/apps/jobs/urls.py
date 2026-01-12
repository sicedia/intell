"""
URL configuration for jobs app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet, ImageTaskViewSet, DescriptionTaskViewSet, AIDescribeView,
    TagViewSet, ImageGroupViewSet, serve_test_excel
)

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'image-tasks', ImageTaskViewSet, basename='imagetask')
router.register(r'description-tasks', DescriptionTaskViewSet, basename='descriptiontask')
router.register(r'ai/describe', AIDescribeView, basename='ai-describe')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'image-groups', ImageGroupViewSet, basename='imagegroup')

urlpatterns = [
    path('', include(router.urls)),
    # TEMPORARY: Test endpoint - remove after testing
    path('test-excel/', serve_test_excel, name='test-excel'),
]

