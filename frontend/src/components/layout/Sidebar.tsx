
"use client"

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from "@/shared/lib/utils";
import {
    LayoutDashboard,
    Sparkles,
    Image as ImageIcon,
    Palette,
    FileText,
    Settings,
} from 'lucide-react';

const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/generate', label: 'Generate', icon: Sparkles },
    { href: '/images', label: 'Images', icon: ImageIcon },
    { href: '/themes', label: 'Themes', icon: Palette },
    { href: '/reports', label: 'Reports', icon: FileText },
    { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar({ className, onClose }: { className?: string, onClose?: () => void }) {
    const pathname = usePathname();
    const localeSegment = pathname?.split("/")[1] ?? "";

    return (
        <div className={cn("flex flex-col h-full bg-card border-r", className)}>
            <div className="p-6 flex items-center gap-2 border-b">
                <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                    <span className="text-primary-foreground font-bold text-lg">I</span>
                </div>
                <span className="text-xl font-bold tracking-tight">Intell.AI</span>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
                <nav className="space-y-1 px-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const targetHref = `/${localeSegment}${item.href}`;
                        const isActive = pathname === targetHref || pathname?.startsWith(`${targetHref}/`);

                        return (
                            <Link
                                key={item.href}
                                href={targetHref}
                                onClick={onClose}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                                    isActive
                                        ? "bg-primary/10 text-primary"
                                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                )}
                            >
                                <Icon className="h-4 w-4" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
            </div>

            <div className="p-4 border-t">
                {/* User profile stub */}
                <div className="flex items-center gap-3 px-2 py-2">
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs">U</div>
                    <div className="text-sm">
                        <p className="font-medium">User Profile</p>
                        <p className="text-xs text-muted-foreground">Admin</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
