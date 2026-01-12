/**
 * Notification store using Zustand.
 *
 * Manages:
 * - Notifications list
 * - Unread count
 * - Loading states
 * - Real-time updates
 */
import { create } from "zustand";
import type { Notification } from "../types";

// ============================================================================
// Types
// ============================================================================

interface NotificationState {
  /** List of notifications */
  notifications: Notification[];
  
  /** Unread count */
  unreadCount: number;
  
  /** Whether notifications are being loaded */
  isLoading: boolean;
  
  /** Whether unread count is being loaded */
  isLoadingCount: boolean;
  
  /** Last error */
  error: Error | null;
  
  /** Set notifications */
  setNotifications: (notifications: Notification[]) => void;
  
  /** Add notification to list */
  addNotification: (notification: Notification) => void;
  
  /** Update notification */
  updateNotification: (id: number, updates: Partial<Notification>) => void;
  
  /** Remove notification */
  removeNotification: (id: number) => void;
  
  /** Set unread count */
  setUnreadCount: (count: number) => void;
  
  /** Increment unread count */
  incrementUnreadCount: () => void;
  
  /** Decrement unread count */
  decrementUnreadCount: () => void;
  
  /** Mark notification as read locally */
  markAsRead: (id: number) => void;
  
  /** Mark all as read locally */
  markAllAsRead: () => void;
  
  /** Set loading state */
  setLoading: (loading: boolean) => void;
  
  /** Set count loading state */
  setLoadingCount: (loading: boolean) => void;
  
  /** Set error */
  setError: (error: Error | null) => void;
  
  /** Clear error */
  clearError: () => void;
  
  /** Reset store */
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  isLoadingCount: false,
  error: null,
};

// ============================================================================
// Store
// ============================================================================

export const useNotificationStore = create<NotificationState>((set, get) => ({
  ...initialState,

  setNotifications: (notifications) =>
    set({
      notifications,
      unreadCount: notifications.filter((n) => !n.is_read).length,
    }),

  addNotification: (notification) => {
    const state = get();
    // Avoid duplicates
    if (state.notifications.some((n) => n.id === notification.id)) {
      return;
    }
    
    set({
      notifications: [notification, ...state.notifications],
      unreadCount: notification.is_read
        ? state.unreadCount
        : state.unreadCount + 1,
    });
  },

  updateNotification: (id, updates) => {
    const state = get();
    const notification = state.notifications.find((n) => n.id === id);
    if (!notification) return;

    const updated = { ...notification, ...updates };
    const wasRead = notification.is_read;
    const isNowRead = updated.is_read;

    set({
      notifications: state.notifications.map((n) =>
        n.id === id ? updated : n
      ),
      unreadCount:
        wasRead !== isNowRead
          ? isNowRead
            ? Math.max(0, state.unreadCount - 1)
            : state.unreadCount + 1
          : state.unreadCount,
    });
  },

  removeNotification: (id) => {
    const state = get();
    const notification = state.notifications.find((n) => n.id === id);
    
    set({
      notifications: state.notifications.filter((n) => n.id !== id),
      unreadCount: notification && !notification.is_read
        ? Math.max(0, state.unreadCount - 1)
        : state.unreadCount,
    });
  },

  setUnreadCount: (count) => set({ unreadCount: Math.max(0, count) }),

  incrementUnreadCount: () =>
    set((state) => ({ unreadCount: state.unreadCount + 1 })),

  decrementUnreadCount: () =>
    set((state) => ({ unreadCount: Math.max(0, state.unreadCount - 1) })),

  markAsRead: (id) => {
    const state = get();
    const notification = state.notifications.find((n) => n.id === id);
    if (!notification || notification.is_read) return;

    set({
      notifications: state.notifications.map((n) =>
        n.id === id
          ? { ...n, is_read: true, read_at: new Date().toISOString() }
          : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    });
  },

  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.is_read
          ? n
          : { ...n, is_read: true, read_at: new Date().toISOString() }
      ),
      unreadCount: 0,
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setLoadingCount: (loading) => set({ isLoadingCount: loading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));

// ============================================================================
// Selectors
// ============================================================================

export const selectNotifications = (state: NotificationState) => state.notifications;
export const selectUnreadNotifications = (state: NotificationState) =>
  state.notifications.filter((n) => !n.is_read);
export const selectUnreadCount = (state: NotificationState) => state.unreadCount;
export const selectIsLoading = (state: NotificationState) => state.isLoading;
export const selectIsLoadingCount = (state: NotificationState) => state.isLoadingCount;
export const selectError = (state: NotificationState) => state.error;