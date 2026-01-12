"use client";

import React from 'react';
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/components/ui/button";
import Link from 'next/link';

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick?: () => void;
    href?: string;
    variant?: 'default' | 'outline' | 'secondary';
  };
  className?: string;
  children?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
  children,
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center rounded-lg border border-dashed bg-muted/30",
      className
    )}>
      {icon && (
        <div className="mb-4 text-muted-foreground flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold tracking-tight mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-sm mb-4">{description}</p>
      )}

      {children}

      {action && (
        action.href ? (
          <Link 
            href={action.href} 
            className={cn(
              buttonVariants({ variant: action.variant || 'default' }), 
              "mt-4"
            )}
          >
            {action.label}
          </Link>
        ) : (
          <Button 
            onClick={action.onClick} 
            variant={action.variant || 'default'} 
            className="mt-4"
          >
            {action.label}
          </Button>
        )
      )}
    </div>
  );
}
