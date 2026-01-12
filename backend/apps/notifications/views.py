"""
API views for notifications app.
"""
import logging
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from .models import Notification
from .serializers import NotificationSerializer, NotificationMarkReadSerializer

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class to ensure users can only access their own notifications.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for owner
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        # Write permissions for owner
        return obj.user == request.user


@extend_schema_view(
    list=extend_schema(
        summary='Listar notificaciones',
        description='Obtiene la lista de notificaciones del usuario autenticado.',
        tags=['Notifications'],
        responses={
            200: NotificationSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        summary='Obtener notificación',
        description='Obtiene los detalles de una notificación específica.',
        tags=['Notifications'],
        responses={
            200: NotificationSerializer,
            404: OpenApiResponse(description='Notificación no encontrada'),
        }
    ),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Notification model.
    
    Provides read-only access to user's notifications with ability to mark as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        Filter notifications to only show those belonging to the current user.
        """
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Optional filtering by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        # Optional filtering by type
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        return queryset.select_related('user').order_by('-created_at')
    
    @extend_schema(
        summary='Marcar notificaciones como leídas',
        description='Marca una o todas las notificaciones como leídas.',
        tags=['Notifications'],
        request=NotificationMarkReadSerializer,
        responses={
            200: inline_serializer(
                name='MarkReadResponse',
                fields={
                    'marked_count': serializers.IntegerField(),
                    'message': serializers.CharField(),
                }
            ),
        }
    )
    @action(detail=False, methods=['post'], url_path='mark-read', url_name='mark-read')
    def mark_read(self, request):
        """
        Mark one or more notifications as read.
        If notification_ids is provided, marks only those.
        Otherwise, marks all unread notifications for the user.
        """
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', None)
        
        queryset = Notification.objects.filter(user=request.user, is_read=False)
        
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        marked_count = queryset.update(is_read=True, read_at=timezone.now())
        
        return Response({
            'marked_count': marked_count,
            'message': f'Se marcaron {marked_count} notificación(es) como leída(s).'
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary='Obtener contador de notificaciones no leídas',
        description='Obtiene el número de notificaciones no leídas del usuario.',
        tags=['Notifications'],
        responses={
            200: inline_serializer(
                name='UnreadCountResponse',
                fields={
                    'unread_count': serializers.IntegerField(),
                }
            ),
        }
    )
    @action(detail=False, methods=['get'], url_path='unread-count', url_name='unread-count')
    def unread_count(self, request):
        """
        Get count of unread notifications for the current user.
        """
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return Response({
            'unread_count': count
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a notification and automatically mark it as read when accessed.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Automatically mark as read when retrieved
        instance.mark_as_read()
        
        return Response(serializer.data)