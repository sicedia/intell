"use client";

/**
 * Notification dropdown component.
 * 
 * Provides a robust notification system with:
 * - Real-time unread count badge
 * - Dropdown menu with notifications list
 * - Mark as read functionality
 * - Automatic cleanup when opened
 * - Proper TypeScript types and error handling
 */
import React, { useEffect, useState } from "react";
import { Bell, Check, CheckCheck, Loader2, AlertCircle, CheckCircle, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";
import { useNotifications } from "../hooks/useNotifications";
import type { Notification } from "../types";

/**
 * Format notification time relative to now.
 */
function formatNotificationTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return "hace un momento";
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
      return `hace ${diffInMinutes} ${diffInMinutes === 1 ? "minuto" : "minutos"}`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
      return `hace ${diffInHours} ${diffInHours === 1 ? "hora" : "horas"}`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) {
      return `hace ${diffInDays} ${diffInDays === 1 ? "día" : "días"}`;
    }
    
    const diffInWeeks = Math.floor(diffInDays / 7);
    if (diffInWeeks < 4) {
      return `hace ${diffInWeeks} ${diffInWeeks === 1 ? "semana" : "semanas"}`;
    }
    
    const diffInMonths = Math.floor(diffInDays / 30);
    if (diffInMonths < 12) {
      return `hace ${diffInMonths} ${diffInMonths === 1 ? "mes" : "meses"}`;
    }
    
    const diffInYears = Math.floor(diffInDays / 365);
    return `hace ${diffInYears} ${diffInYears === 1 ? "año" : "años"}`;
  } catch {
    return "hace un momento";
  }
}

/**
 * Get icon for notification type.
 */
function getNotificationIcon(type: Notification["type"]) {
  switch (type) {
    case "DESCRIPTION_COMPLETED":
    case "JOB_COMPLETED":
    case "IMAGE_GENERATED":
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case "DESCRIPTION_FAILED":
    case "JOB_FAILED":
      return <XCircle className="h-4 w-4 text-red-500" />;
    case "SYSTEM":
      return <AlertCircle className="h-4 w-4 text-blue-500" />;
    default:
      return <Bell className="h-4 w-4 text-muted-foreground" />;
  }
}

/**
 * Single notification item component.
 */
function NotificationItem({
  notification,
  onMarkAsRead,
  onNavigate,
}: {
  notification: Notification;
  onMarkAsRead: (id: number) => void;
  onNavigate: (url: string | null) => void;
}) {
  const handleClick = () => {
    if (!notification.is_read) {
      onMarkAsRead(notification.id);
    }
    if (notification.related_object_url) {
      onNavigate(notification.related_object_url);
    }
  };

  return (
    <DropdownMenuItem
      key={notification.id}
      className={cn(
        "flex items-start gap-3 p-3 cursor-pointer",
        "hover:bg-accent transition-colors",
        !notification.is_read && "bg-accent/30 border-l-2 border-l-primary"
      )}
      onClick={handleClick}
      onSelect={(e) => {
        e.preventDefault();
        handleClick();
      }}
    >
      <div className="mt-0.5 shrink-0">
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex-1 min-w-0">
            <p
              className={cn(
                "text-sm font-medium line-clamp-2 mb-1",
                !notification.is_read && "font-semibold text-foreground"
              )}
            >
              {notification.title}
            </p>
            <p className="text-xs text-muted-foreground line-clamp-2 mb-1.5">
              {notification.message}
            </p>
          </div>
          {!notification.is_read && (
            <div className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1" />
          )}
        </div>
        <p className="text-xs text-muted-foreground/70">
          {formatNotificationTime(notification.created_at)}
        </p>
      </div>
    </DropdownMenuItem>
  );
}

/**
 * Notification dropdown component.
 *
 * Note: This component assumes the user is authenticated.
 * Conditional rendering should be handled by the parent component.
 */
export function NotificationDropdown() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const {
    notifications,
    unreadCount,
    isLoading,
    isLoadingCount,
    error,
    markAsRead,
    markAllAsRead,
    refetch,
  } = useNotifications();

  // Debug: Log notifications when they change
  useEffect(() => {
    if (notifications.length > 0) {
      console.log(`[Notifications] Loaded ${notifications.length} notifications (${unreadCount} unread)`);
    }
  }, [notifications.length, unreadCount]);

  // Refetch when dropdown is opened to get latest notifications
  useEffect(() => {
    if (isOpen) {
      refetch();
    }
  }, [isOpen, refetch]);

  // Separate unread and read notifications for better organization
  // Sort by created_at descending (newest first)
  const sortedNotifications = [...notifications].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  const unreadNotifications = sortedNotifications.filter((n) => !n.is_read);
  const readNotifications = sortedNotifications.filter((n) => n.is_read);
  const hasNotifications = notifications.length > 0;

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground relative"
          aria-label="Notificaciones"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span
              className={cn(
                "absolute top-0 right-0 h-5 w-5 rounded-full bg-destructive",
                "flex items-center justify-center",
                "text-[10px] font-bold text-destructive-foreground",
                "min-w-[1.25rem] min-h-[1.25rem]",
                "border-2 border-background"
              )}
              aria-label={`${unreadCount} notificaciones no leídas`}
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
          <span className="sr-only">Notificaciones</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-[420px] max-h-[600px] overflow-hidden flex flex-col p-0"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b bg-background sticky top-0 z-10">
          <DropdownMenuLabel className="text-base font-semibold">
            Notificaciones
          </DropdownMenuLabel>
          {unreadNotifications.length > 0 && (
            <button
              type="button"
              className="text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1.5 px-2.5 py-1.5 rounded-md hover:bg-accent"
              onClick={(e) => {
                e.stopPropagation();
                markAllAsRead();
              }}
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Marcar todas como leídas
            </button>
          )}
        </div>
        
        {error ? (
          <div className="flex flex-col items-center justify-center py-8 px-4">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-sm text-destructive text-center">
              Error al cargar notificaciones
            </p>
            <button
              type="button"
              onClick={() => refetch()}
              className="text-xs text-primary hover:underline mt-2"
            >
              Reintentar
            </button>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">
              Cargando notificaciones...
            </span>
          </div>
        ) : !hasNotifications ? (
          <div className="flex flex-col items-center justify-center py-8 px-4">
            <Bell className="h-12 w-12 text-muted-foreground/50 mb-2" />
            <p className="text-sm text-muted-foreground text-center">
              No hay notificaciones
            </p>
            <p className="text-xs text-muted-foreground/70 text-center mt-1">
              Te notificaremos cuando haya actualizaciones
            </p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            {/* Show unread notifications first */}
            {unreadNotifications.length > 0 && (
              <>
                <div className="px-4 py-2.5 bg-primary/5 border-b sticky top-0 z-10">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Nuevas ({unreadNotifications.length})
                  </p>
                </div>
                {unreadNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={markAsRead}
                    onNavigate={(url) => {
                      if (url) {
                        setIsOpen(false);
                        router.push(url);
                      }
                    }}
                  />
                ))}
                {readNotifications.length > 0 && (
                  <div className="h-px bg-border" />
                )}
              </>
            )}

            {/* Show read notifications (history) */}
            {readNotifications.length > 0 && (
              <>
                <div className="px-4 py-2.5 bg-muted/30 border-b sticky top-0 z-10">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Anteriores ({readNotifications.length})
                  </p>
                </div>
                {readNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={markAsRead}
                    onNavigate={(url) => {
                      if (url) {
                        setIsOpen(false);
                        router.push(url);
                      }
                    }}
                  />
                ))}
              </>
            )}

            {/* Footer with total count */}
            {hasNotifications && (
              <div className="px-4 py-2.5 border-t bg-muted/20 text-center">
                <p className="text-xs text-muted-foreground">
                  {notifications.length} {notifications.length === 1 ? 'notificación' : 'notificaciones'} en total
                </p>
              </div>
            )}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}