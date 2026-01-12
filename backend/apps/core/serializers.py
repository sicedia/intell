"""
Serializers for core app (health checks).
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Health check exitoso',
            value={
                'status': 'ok',
                'service': 'intelli-backend'
            }
        ),
    ]
)
class HealthCheckResponseSerializer(serializers.Serializer):
    """Response serializer for basic health check."""
    status = serializers.CharField(help_text='Estado del servicio: ok')
    service = serializers.CharField(help_text='Nombre del servicio')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Redis saludable',
            value={
                'status': 'ok',
                'service': 'redis'
            }
        ),
        OpenApiExample(
            'Error de Redis',
            value={
                'status': 'error',
                'service': 'redis',
                'message': 'Connection failed'
            }
        ),
    ]
)
class RedisHealthCheckResponseSerializer(serializers.Serializer):
    """Response serializer for Redis health check."""
    status = serializers.CharField(help_text='Estado: ok, error')
    service = serializers.CharField(help_text='Nombre del servicio: redis')
    message = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='Mensaje de error si status es error'
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Celery saludable',
            value={
                'status': 'ok',
                'service': 'celery',
                'workers': 2
            }
        ),
        OpenApiExample(
            'Advertencia de Celery',
            value={
                'status': 'warning',
                'service': 'celery',
                'message': 'No active workers found'
            }
        ),
        OpenApiExample(
            'Error de Celery',
            value={
                'status': 'error',
                'service': 'celery',
                'message': 'Connection failed'
            }
        ),
    ]
)
class CeleryHealthCheckResponseSerializer(serializers.Serializer):
    """Response serializer for Celery health check."""
    status = serializers.CharField(help_text='Estado: ok, warning, error')
    service = serializers.CharField(help_text='Nombre del servicio: celery')
    workers = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='Número de workers activos (solo si status es ok)'
    )
    message = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='Mensaje de advertencia o error'
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Database healthy',
            value={
                'status': 'healthy',
                'message': 'Database connection successful',
                'database': 'default',
                'response_time_ms': 2.45
            }
        ),
        OpenApiExample(
            'Database degraded',
            value={
                'status': 'degraded',
                'message': 'Database responding slowly (4500ms)',
                'database': 'default',
                'response_time_ms': 4500.0
            }
        ),
        OpenApiExample(
            'Database unhealthy',
            value={
                'status': 'unhealthy',
                'message': 'Database connection failed: connection refused',
                'database': 'default',
                'response_time_ms': 5000.0,
                'details': {
                    'error_type': 'OperationalError',
                    'error': 'connection refused'
                }
            }
        ),
    ]
)
class DatabaseHealthCheckResponseSerializer(serializers.Serializer):
    """Response serializer for database health check."""
    status = serializers.CharField(
        help_text='Estado: healthy, unhealthy, degraded, unknown'
    )
    message = serializers.CharField(help_text='Mensaje descriptivo del estado')
    database = serializers.CharField(help_text='Alias de la base de datos')
    response_time_ms = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text='Tiempo de respuesta en milisegundos'
    )
    details = serializers.DictField(
        required=False,
        allow_null=True,
        help_text='Información adicional de diagnóstico'
    )
