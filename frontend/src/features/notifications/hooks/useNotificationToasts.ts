"use client";

/**
 * Hook to show toast notifications when new notifications arrive.
 * 
 * This hook monitors the notification store and displays toast messages
 * when new unread notifications are detected.
 * 
 * Features:
 * - Tracks previously seen notification IDs to avoid duplicate toasts
 * - Only shows toasts for new unread notifications
 * - Automatically cleans up old seen IDs
 * - Prevents toasts on initial load
 */
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useNotificationStore, selectNotifications } from "../stores/useNotificationStore";
import type { Notification } from "../types";
import { CheckCircle, XCircle, AlertCircle, Bell } from "lucide-react";
import React from "react";

/**
 * Get icon component for notification type.
 * Uses React.createElement to avoid JSX parsing issues in helper functions.
 */
function getNotificationIcon(type: Notification["type"]): React.ReactNode {
  switch (type) {
    case "DESCRIPTION_COMPLETED":
    case "JOB_COMPLETED":
    case "IMAGE_GENERATED":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-500" });
    case "DESCRIPTION_FAILED":
    case "JOB_FAILED":
      return React.createElement(XCircle, { className: "h-4 w-4 text-red-500" });
    case "SYSTEM":
      return React.createElement(AlertCircle, { className: "h-4 w-4 text-blue-500" });
    default:
      return React.createElement(Bell, { className: "h-4 w-4" });
  }
}

/**
 * Get toast variant based on notification type.
 */
function getToastVariant(type: Notification["type"]): "success" | "error" | "info" | "default" {
  switch (type) {
    case "DESCRIPTION_COMPLETED":
    case "JOB_COMPLETED":
    case "IMAGE_GENERATED":
      return "success";
    case "DESCRIPTION_FAILED":
    case "JOB_FAILED":
      return "error";
    case "SYSTEM":
      return "info";
    default:
      return "default";
  }
}

/**
 * Hook to automatically show toast notifications for new unread notifications.
 * 
 * This hook:
 * - Tracks previously seen notification IDs
 * - Detects new unread notifications
 * - Shows toast messages for new notifications
 * - Prevents duplicate toasts for the same notification
 * - Skips toasts on initial load (only shows for truly new notifications)
 */
export function useNotificationToasts() {
  const notifications = useNotificationStore(selectNotifications);
  const seenNotificationIds = useRef<Set<number>>(new Set());
  const isInitialLoad = useRef<boolean>(true);

  useEffect(() => {
    // Skip if no notifications (user not authenticated or no data yet)
    // This prevents the hook from running when there's no data
    if (notifications.length === 0) {
      return;
    }

    // Skip toasts on initial load to avoid showing all existing notifications
    if (isInitialLoad.current) {
      // Mark all current notifications as seen
      notifications.forEach((notification) => {
        seenNotificationIds.current.add(notification.id);
      });
      isInitialLoad.current = false;
      return;
    }

    // Get unread notifications
    const unreadNotifications = notifications.filter((n) => !n.is_read);

    // Find new notifications (not seen before)
    const newNotifications = unreadNotifications.filter(
      (notification) => !seenNotificationIds.current.has(notification.id)
    );

    // Show toast for each new notification
    newNotifications.forEach((notification) => {
      // Mark as seen immediately to prevent duplicate toasts
      seenNotificationIds.current.add(notification.id);

      // Determine toast variant
      const variant = getToastVariant(notification.type);

      // Show toast with appropriate variant
      const toastOptions = {
        duration: 5000, // 5 seconds
        icon: getNotificationIcon(notification.type),
        id: `notification-${notification.id}`, // Prevent duplicates
      };

      switch (variant) {
        case "success":
          toast.success(notification.title, {
            ...toastOptions,
            description: notification.message,
          });
          break;
        case "error":
          toast.error(notification.title, {
            ...toastOptions,
            description: notification.message,
          });
          break;
        case "info":
          toast.info(notification.title, {
            ...toastOptions,
            description: notification.message,
          });
          break;
        default:
          toast(notification.title, {
            ...toastOptions,
            description: notification.message,
          });
      }
    });

    // Clean up old seen IDs (keep only IDs that still exist in notifications)
    // This prevents memory leaks from accumulating seen IDs
    const currentNotificationIds = new Set(notifications.map((n) => n.id));
    seenNotificationIds.current.forEach((id) => {
      if (!currentNotificationIds.has(id)) {
        seenNotificationIds.current.delete(id);
      }
    });
  }, [notifications]);
}
