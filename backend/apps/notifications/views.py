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
    def has_permission(self, request, view):
        """
        Allow access to list and custom actions for authenticated users.
        Object-level permissions are checked in has_object_permission.
        """
        # Check if user is authenticated
        # In development, AllowAny is set globally, but we still want to check authentication
        # for notifications to ensure users only see their own notifications
        if not request.user:
            return False
        # Check if user is authenticated (not AnonymousUser)
        return hasattr(request.user, 'is_authenticated') and request.user.is_authenticated
    
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
    # Use IsOwnerOrReadOnly for object-level permissions, but allow global permission classes for view-level
    permission_classes = []  # Use global permission classes  # IsOwnerOrReadOnly already checks authentication
    # Disable pagination to show all notifications (like Facebook/Instagram)
    pagination_class = None
    
    def get_queryset(self):
        """
        Filter notifications to only show those belonging to the current user.
        """
        # If user is authenticated, filter by user; otherwise return empty queryset
        if self.request.user and self.request.user.is_authenticated:
            queryset = Notification.objects.filter(user=self.request.user)
        else:
            # Return empty queryset for anonymous users
            queryset = Notification.objects.none()

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
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

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
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'unread_count': 0},
                status=status.HTTP_200_OK
            )

        count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'unread_count': count
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a notification and automatically mark it as read when accessed.
        """
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Automatically mark as read when retrieved
        instance.mark_as_read()

        return Response(serializer.data)