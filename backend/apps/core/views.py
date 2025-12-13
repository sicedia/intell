"""
Health check views.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from celery import current_app


@api_view(['GET'])
def health_check(request):
    """Basic health check."""
    return Response({
        'status': 'ok',
        'service': 'intelli-backend'
    })


@api_view(['GET'])
def redis_health_check(request):
    """Redis health check."""
    try:
        cache.set('health_check', 'ok', 10)
        value = cache.get('health_check')
        if value == 'ok':
            return Response({
                'status': 'ok',
                'service': 'redis'
            })
        else:
            return Response({
                'status': 'error',
                'service': 'redis',
                'message': 'Cache test failed'
            }, status=500)
    except Exception as e:
        return Response({
            'status': 'error',
            'service': 'redis',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
def celery_health_check(request):
    """Celery health check."""
    try:
        inspect = current_app.control.inspect()
        active_queues = inspect.active_queues()
        if active_queues:
            return Response({
                'status': 'ok',
                'service': 'celery',
                'workers': len(active_queues)
            })
        else:
            return Response({
                'status': 'warning',
                'service': 'celery',
                'message': 'No active workers found'
            })
    except Exception as e:
        return Response({
            'status': 'error',
            'service': 'celery',
            'message': str(e)
        }, status=500)

