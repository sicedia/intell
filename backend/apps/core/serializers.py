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
