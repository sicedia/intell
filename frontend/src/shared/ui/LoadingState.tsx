import React from 'react';
import { cn } from "@/shared/lib/utils";
import { Spinner } from "@/shared/components/ui/spinner";
import { Skeleton } from "@/shared/components/ui/skeleton";

export interface LoadingStateProps {
  variant?: 'spinner' | 'skeleton' | 'minimal';
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
  children?: React.ReactNode;
}

export function LoadingState({
  variant = 'spinner',
  size = 'md',
  message = "Loading...",
  className,
  children,
}: LoadingStateProps) {
  if (variant === 'minimal') {
    return <Spinner size={size} className={className} />;
  }

  if (variant === 'skeleton') {
    return (
      <div className={cn("space-y-4 p-6", className)}>
        {children || (
          <>
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-5/6" />
            <Skeleton className="h-8 w-4/6" />
          </>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4",
      className
    )}>
      <Spinner size={size} variant="primary" className="mb-4" />
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
