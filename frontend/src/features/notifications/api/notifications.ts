/**
 * API functions for notifications.
 */
import { apiClient } from "@/shared/lib/api-client";
import type {
  Notification,
  NotificationListResponse,
  UnreadCountResponse,
  MarkReadRequest,
  MarkReadResponse,
} from "../types";

/**
 * Get list of notifications for the current user.
 */
export async function getNotifications(params?: {
  is_read?: boolean;
  type?: string;
}): Promise<Notification[]> {
  const queryParams = new URLSearchParams();
  if (params?.is_read !== undefined) {
    queryParams.append('is_read', params.is_read.toString());
  }
  if (params?.type) {
    queryParams.append('type', params.type);
  }
  
  const queryString = queryParams.toString();
  const baseEndpoint = '/notifications/';
  const endpoint = queryString ? `${baseEndpoint}?${queryString}` : baseEndpoint;
  
  const response = await apiClient.get<Notification[]>(endpoint);
  return Array.isArray(response) ? response : [];
}

/**
 * Get a single notification by ID.
 */
export async function getNotification(notificationId: number): Promise<Notification> {
  const response = await apiClient.get<Notification>(`/notifications/${notificationId}/`);
  return response;
}

/**
 * Get count of unread notifications.
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response = await apiClient.get<UnreadCountResponse>(
    '/notifications/unread-count/'
  );
  return response;
}

/**
 * Mark notifications as read.
 * If notification_ids is provided, marks only those.
 * Otherwise, marks all unread notifications.
 */
export async function markNotificationsAsRead(
  data?: MarkReadRequest
): Promise<MarkReadResponse> {
  const response = await apiClient.post<MarkReadResponse>(
    '/notifications/mark-read/',
    data || {}
  );
  return response;
}