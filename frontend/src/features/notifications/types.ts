/**
 * Types for notifications feature.
 */

export type NotificationType =
  | 'DESCRIPTION_COMPLETED'
  | 'DESCRIPTION_FAILED'
  | 'JOB_COMPLETED'
  | 'JOB_FAILED'
  | 'IMAGE_GENERATED'
  | 'SYSTEM';

export interface Notification {
  id: number;
  user: number;
  type: NotificationType;
  title: string;
  message: string;
  related_object_type: string | null;
  related_object_id: number | null;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  updated_at: string;
  related_object_url: string | null;
}

export interface NotificationListResponse {
  results: Notification[];
  count?: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface MarkReadRequest {
  notification_ids?: number[];
}

export interface MarkReadResponse {
  marked_count: number;
  message: string;
}