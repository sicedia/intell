
import React from 'react';
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

interface GalleryGridProps {
    isLoading?: boolean;
    children?: React.ReactNode; // Optional when isLoading is true
    className?: string;
    itemCount?: number; // for skeleton count
}

export function GalleryGrid({ isLoading, children, className, itemCount = 6 }: GalleryGridProps) {
    if (isLoading) {
        return (
            <div className={cn("grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4", className)}>
                {Array.from({ length: itemCount }).map((_, i) => (
                    <div key={i} className="flex flex-col space-y-3">
                        <Skeleton className="h-[200px] w-full rounded-xl" />
                        <div className="space-y-2">
                            <Skeleton className="h-4 w-[80%]" />
                            <Skeleton className="h-4 w-[40%]" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    return (
        <div className={cn("grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4", className)}>
            {children}
        </div>
    );
}
