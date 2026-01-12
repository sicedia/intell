"""
Health check views.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from celery import current_app
from drf_spectacular.utils import extend_schema
from .serializers import (
    HealthCheckResponseSerializer,
    RedisHealthCheckResponseSerializer,
    CeleryHealthCheckResponseSerializer,
    DatabaseHealthCheckResponseSerializer,
)
from .db import get_database_status, DatabaseHealthStatus


@extend_schema(
    summary='Health check básico',
    description='Verifica el estado básico del servicio API.',
    tags=['Health'],
    responses={
        200: HealthCheckResponseSerializer,
    },
)
@api_view(['GET'])
def health_check(request):
    """Basic health check."""
    return Response({
        'status': 'ok',
        'service': 'intelli-backend'
    })


@extend_schema(
    summary='Health check de Redis',
    description='Verifica el estado de la conexión con Redis y la funcionalidad del cache.',
    tags=['Health'],
    responses={
        200: RedisHealthCheckResponseSerializer,
        500: RedisHealthCheckResponseSerializer,
    },
)
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


@extend_schema(
    summary='Health check de Celery',
    description='Verifica el estado de Celery y el número de workers activos.',
    tags=['Health'],
    responses={
        200: CeleryHealthCheckResponseSerializer,
        500: CeleryHealthCheckResponseSerializer,
    },
)
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


@extend_schema(
    summary='Health check de Base de Datos',
    description=(
        'Verifica el estado de la conexión con la base de datos. '
        'Incluye tiempo de respuesta y detalles de diagnóstico opcionales.'
    ),
    tags=['Health'],
    responses={
        200: DatabaseHealthCheckResponseSerializer,
        500: DatabaseHealthCheckResponseSerializer,
    },
)
@api_view(['GET'])
def database_health_check(request):
    """
    Database health check with detailed status.
    
    Returns the health status of the database connection including:
    - Connection status (healthy, unhealthy, degraded)
    - Response time in milliseconds
    - Diagnostic details (optional, via ?details=true query param)
    """
    include_details = request.query_params.get('details', 'false').lower() == 'true'
    database = request.query_params.get('database', 'default')
    
    status = get_database_status(
        database=database,
        include_details=include_details,
    )
    
    response_data = status.to_dict()
    
    # Determine HTTP status code based on health status
    if status.status == DatabaseHealthStatus.HEALTHY:
        return Response(response_data, status=200)
    elif status.status == DatabaseHealthStatus.DEGRADED:
        return Response(response_data, status=200)  # Still operational
    else:
        return Response(response_data, status=500)

