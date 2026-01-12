"""
Serializers for notifications app.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Notification


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Notificación de descripción completada',
            value={
                'id': 1,
                'user': 1,
                'type': 'DESCRIPTION_COMPLETED',
                'title': 'Descripción generada exitosamente',
                'message': 'La descripción de la imagen #123 ha sido generada con éxito usando OpenAI GPT-4.',
                'related_object_type': 'DescriptionTask',
                'related_object_id': 456,
                'metadata': {
                    'provider': 'openai',
                    'model': 'gpt-4',
                    'image_task_id': 123
                },
                'is_read': False,
                'read_at': None,
                'created_at': '2024-01-01T10:00:00Z',
                'updated_at': '2024-01-01T10:00:00Z',
                'related_object_url': '/images/123'
            }
        ),
    ]
)
class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    related_object_url = serializers.SerializerMethodField()
    
    def get_related_object_url(self, obj):
        """Get related object URL from model property."""
        try:
            return obj.related_object_url
        except (AttributeError, TypeError):
            return None
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'type',
            'title',
            'message',
            'related_object_type',
            'related_object_id',
            'metadata',
            'is_read',
            'read_at',
            'created_at',
            'updated_at',
            'related_object_url',
        ]
        read_only_fields = [
            'id',
            'user',
            'created_at',
            'updated_at',
            'related_object_url',
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )