"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import health_check, redis_health_check, celery_health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/', include('apps.jobs.urls')),
    # Health checks
    path('api/health/', health_check, name='health'),
    path('api/health/redis/', redis_health_check, name='health-redis'),
    path('api/health/celery/', celery_health_check, name='health-celery'),
    # Redirect favicon.ico to prevent 404 errors
    path('favicon.ico', RedirectView.as_view(url='/static/admin/img/favicon.ico', permanent=True)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
