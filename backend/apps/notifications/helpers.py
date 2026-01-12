"""
Helper functions for creating notifications.
"""
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def create_notification(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    related_object_type: Optional[str] = None,
    related_object_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Notification:
    """
    Create a notification for a user.
    
    Args:
        user: User to receive the notification
        notification_type: Type of notification (from Notification.Type choices)
        title: Notification title
        message: Notification message
        related_object_type: Type of related object (e.g., 'DescriptionTask', 'ImageTask')
        related_object_id: ID of related object
        metadata: Additional metadata dictionary
    
    Returns:
        Created Notification instance
    """
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        metadata=metadata or {},
    )
    
    return notification