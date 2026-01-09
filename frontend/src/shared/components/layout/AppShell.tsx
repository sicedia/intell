import React from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

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
        </div>
    );
}
