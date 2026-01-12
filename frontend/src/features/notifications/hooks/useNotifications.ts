/**
 * Hook to manage notifications with React Query and Zustand.
 */
import { useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getNotifications,
  getUnreadCount,
  markNotificationsAsRead,
} from "../api/notifications";
import {
  useNotificationStore,
  selectNotifications,
  selectUnreadCount,
} from "../stores/useNotificationStore";
import { HttpError, ConnectionError } from "@/shared/lib/api-client";

/**
 * Hook to fetch and manage notifications.
 */
export function useNotifications(params?: { is_read?: boolean; type?: string }) {
  const queryClient = useQueryClient();
  // Get only the specific functions we need from the store
  const setNotifications = useNotificationStore((state) => state.setNotifications);
  const setUnreadCount = useNotificationStore((state) => state.setUnreadCount);
  const markAsReadLocal = useNotificationStore((state) => state.markAsRead);
  const markAllAsReadLocal = useNotificationStore((state) => state.markAllAsRead);
  const notifications = useNotificationStore(selectNotifications);
  const unreadCount = useNotificationStore(selectUnreadCount);

  // Fetch notifications
  const {
    data: fetchedNotifications,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["notifications", params],
    queryFn: () => getNotifications(params),
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error instanceof HttpError && error.status < 500) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // Fetch unread count
  const {
    data: unreadCountData,
    isLoading: isLoadingCount,
    refetch: refetchCount,
  } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: getUnreadCount,
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Poll every 30 seconds
    retry: (failureCount, error) => {
      if (error instanceof HttpError && error.status < 500) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // Sync fetched notifications to store (only when data actually changes)
  useEffect(() => {
    if (fetchedNotifications) {
      setNotifications(fetchedNotifications);
    }
  }, [fetchedNotifications, setNotifications]);

  // Sync unread count to store (only when count actually changes)
  useEffect(() => {
    if (unreadCountData !== undefined && unreadCountData.unread_count !== unreadCount) {
      setUnreadCount(unreadCountData.unread_count);
    }
  }, [unreadCountData, unreadCount, setUnreadCount]);

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: (notificationIds?: number[]) =>
      markNotificationsAsRead(notificationIds ? { notification_ids: notificationIds } : undefined),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      refetch();
      refetchCount();
    },
    onError: (error) => {
      console.error("Error marking notifications as read:", error);
    },
  });

  // Mark single notification as read
  const markAsRead = useCallback(
    (notificationId: number) => {
      // Optimistically update
      markAsReadLocal(notificationId);
      markAsReadMutation.mutate([notificationId]);
    },
    [markAsReadLocal, markAsReadMutation]
  );

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    // Optimistically update
    markAllAsReadLocal();
    markAsReadMutation.mutate();
  }, [markAllAsReadLocal, markAsReadMutation]);

  return {
    notifications,
    unreadCount,
    isLoading,
    isLoadingCount,
    error: error instanceof Error ? error : null,
    markAsRead,
    markAllAsRead,
    refetch,
    refetchCount,
  };
}