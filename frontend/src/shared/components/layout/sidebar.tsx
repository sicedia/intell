"use client"

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import { cn } from "@/shared/lib/utils";
import {
    LayoutDashboard,
    Sparkles,
    Image as ImageIcon,
    Palette,
    FileText,
    Settings,
    ChevronLeft,
    ChevronRight,
} from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { Button } from "@/shared/components/ui/button";

export function Sidebar({ className, onClose }: { className?: string, onClose?: () => void }) {
    const pathname = usePathname();
    const localeSegment = pathname?.split("/")[1] ?? "";
    const [collapsed, setCollapsed] = useState(false);
    const { theme, resolvedTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const t = useTranslations('common');

    useEffect(() => {
        setMounted(true);
    }, []);

    // Use resolvedTheme to handle 'system' theme
    const isDarkMode = mounted && (resolvedTheme === 'dark' || theme === 'dark');
    const logoSrc = isDarkMode ? '/cedia-logo-blank.png' : '/cedia-logo.png';

    const navItems = [
        { href: '/dashboard', label: t('dashboard'), icon: LayoutDashboard },
        { href: '/generate', label: t('generate'), icon: Sparkles },
        { href: '/images', label: t('images'), icon: ImageIcon },
        { href: '/themes', label: t('themes'), icon: Palette },
        { href: '/reports', label: t('reports'), icon: FileText },
        { href: '/settings', label: t('settings'), icon: Settings },
    ];

    return (
        <div 
            className={cn(
                "flex flex-col h-full bg-card border-r transition-all duration-300 relative",
                collapsed ? "w-16" : "w-64",
                className
            )}
            data-sidebar
        >
            {/* Header */}
            <div className="p-6 flex items-center gap-2 border-b">
                {!collapsed && (
                    <>
                        <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                            <span className="text-primary-foreground font-bold text-lg">I</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight">Intell.AI</span>
                    </>
                )}
                {collapsed && (
                    <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center mx-auto">
                        <span className="text-primary-foreground font-bold text-lg">I</span>
                    </div>
                )}
            </div>

            {/* Collapse Toggle Button */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                                "absolute top-20 -right-3 h-6 w-6 rounded-full border bg-background shadow-md z-10",
                                collapsed ? "rotate-180" : ""
                            )}
                            onClick={() => setCollapsed(!collapsed)}
                        >
                            {collapsed ? (
                                <ChevronRight className="h-4 w-4" />
                            ) : (
                                <ChevronLeft className="h-4 w-4" />
                            )}
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                        <p>{collapsed ? t('expandSidebar') : t('collapseSidebar')}</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* Navigation */}
            <div className="flex-1 overflow-y-auto py-4">
                <nav className="space-y-1 px-2">
                    <TooltipProvider>
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const targetHref = `/${localeSegment}${item.href}`;
                            const isActive = pathname === targetHref || pathname?.startsWith(`${targetHref}/`);

                            const linkContent = (
                                <Link
                                    href={targetHref}
                                    onClick={onClose}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                                        collapsed && "justify-center",
                                        isActive
                                            ? "bg-primary/10 text-primary"
                                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                    )}
                                >
                                    <Icon className="h-4 w-4 shrink-0" />
                                    {!collapsed && <span>{item.label}</span>}
                                </Link>
                            );

                            if (collapsed) {
                                return (
                                    <Tooltip key={item.href}>
                                        <TooltipTrigger asChild>
                                            {linkContent}
                                        </TooltipTrigger>
                                        <TooltipContent side="right">
                                            <p>{item.label}</p>
                                        </TooltipContent>
                                    </Tooltip>
                                );
                            }

                            return (
                                <div key={item.href}>
                                    {linkContent}
                                </div>
                            );
                        })}
                    </TooltipProvider>
                </nav>
            </div>

            {/* CEDIA Logo */}
            <div className="p-4 border-t">
                <div className={cn(
                    "flex items-center justify-center",
                    collapsed ? "px-2" : "px-2"
                )}>
                    {collapsed ? (
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <div className="relative w-10 h-10 cursor-pointer hover:opacity-80 transition-opacity">
                                        <Image
                                            src={logoSrc}
                                            alt="CEDIA"
                                            fill
                                            className="object-contain"
                                            priority
                                        />
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent side="right">
                                    <p className="font-medium">CEDIA</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    ) : (
                        <div className="relative w-full h-12">
                            <Image
                                src={logoSrc}
                                alt="CEDIA"
                                fill
                                className="object-contain"
                                priority
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
