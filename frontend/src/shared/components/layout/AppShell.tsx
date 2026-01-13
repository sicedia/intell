"use client";

import React from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { useNotificationToasts } from '@/features/notifications';
import { useAuthStore } from '@/features/auth/stores/useAuthStore';

/**
 * Component to handle notification toasts.
 * Only renders when user is authenticated.
 */
function NotificationToastsProvider() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    
    // Always call the hook (hooks must be called unconditionally)
    // The hook itself will handle the authentication check internally
    useNotificationToasts();
    
    return null;
}

export function AppShell({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex min-h-screen w-full bg-muted/20">
            <div className="hidden md:block w-64 fixed inset-y-0 z-[50] transition-all duration-300">
                <Sidebar className="h-full" />
            </div>
            <div className="md:pl-64 flex flex-col min-h-screen w-full">
                <Topbar />
                <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full">
                    {children}
                </main>
            </div>
            {/* Notification toasts provider - handles showing toasts for new notifications */}
            <NotificationToastsProvider />
        </div>
    );
}
