"use client"

import React from 'react';
import { usePathname } from 'next/navigation';
import { Menu, Search, ChevronRight, Home } from 'lucide-react';
import { Button } from "@/shared/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/shared/components/ui/sheet";
import { Separator } from "@/shared/components/ui/separator";
import { Sidebar } from './Sidebar';
import { UserMenu } from "@/features/auth";
import { NotificationDropdown } from "@/features/notifications";
import { useAuthStore } from "@/features/auth/stores/useAuthStore";
import { cn } from "@/shared/lib/utils";

// Map path segments to readable labels
const pathLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  generate: 'Generate',
  images: 'Image Library',
  themes: 'Themes & Styling',
  settings: 'Settings',
  reports: 'Reports',
  diag: 'Diagnostics',
};

function Breadcrumbs() {
  const pathname = usePathname();
  
  // Extract path segments, skipping locale
  const segments = pathname?.split('/').filter(Boolean) || [];
  const locale = segments[0];
  const pathSegments = segments.slice(1);

  if (pathSegments.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-1 text-sm text-muted-foreground" aria-label="Breadcrumb">
      <Home className="h-4 w-4" />
      <ChevronRight className="h-4 w-4" />
      {pathSegments.map((segment, index) => {
        const isLast = index === pathSegments.length - 1;
        const label = pathLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
        
        return (
          <React.Fragment key={segment}>
            {isLast ? (
              <span className="font-medium text-foreground">{label}</span>
            ) : (
              <>
                <span>{label}</span>
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

export function Topbar() {
    const [open, setOpen] = React.useState(false);
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isAuthLoading = useAuthStore((state) => state.isLoading);

    return (
        <header className="h-16 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-[40] flex items-center px-4 md:px-6">
            {/* Mobile Menu */}
            <div className="md:hidden mr-4">
                <Sheet open={open} onOpenChange={setOpen}>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Menu className="h-5 w-5" />
                            <span className="sr-only">Toggle menu</span>
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-[240px]">
                        <span className="sr-only" role="heading" aria-level={1}>
                            Navigation Menu
                        </span>
                        <Sidebar onClose={() => setOpen(false)} />
                    </SheetContent>
                </Sheet>
            </div>

            {/* Desktop Layout */}
            <div className="flex-1 flex items-center justify-between gap-4">
                {/* Breadcrumbs - Desktop */}
                <div className="hidden md:flex items-center">
                    <Breadcrumbs />
                </div>

                {/* Search Bar */}
                <div className="hidden md:flex items-center text-muted-foreground bg-muted/40 rounded-md px-3 py-1.5 w-64 text-sm border focus-within:ring-1 focus-within:ring-ring transition-all">
                    <Search className="h-4 w-4 mr-2 shrink-0" />
                    <input
                        type="text"
                        placeholder="Search resources..."
                        className="bg-transparent border-none outline-none w-full placeholder:text-muted-foreground/70"
                    />
                </div>

                {/* Right Side Actions */}
                <div className="flex items-center gap-2 ml-auto">
                    {/* Only render notifications if user is authenticated and not loading */}
                    {isAuthenticated && !isAuthLoading && <NotificationDropdown />}

                    <Separator orientation="vertical" className="h-6 mx-1" />

                    {/* User Menu */}
                    <UserMenu showName />
                </div>
            </div>
        </header>
    );
}
