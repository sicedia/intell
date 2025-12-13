import React from 'react';
import Link from 'next/link';
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/components/ui/button";

type StateVariant = 'loading' | 'empty' | 'error' | 'success' | 'default';

interface StateBlockProps {
    variant?: StateVariant;
    title?: string;
    description?: string;
    icon?: React.ReactNode;
    action?: {
        label: string;
        onClick?: () => void;
        href?: string;
    };
    className?: string;
    children?: React.ReactNode;
}

export function StateBlock({
    variant = 'default',
    title,
    description,
    icon,
    action,
    className,
    children
}: StateBlockProps) {
    return (
        <div className={cn(
            "flex flex-col items-center justify-center py-12 px-4 text-center rounded-lg border border-dashed",
            {
                "bg-muted/30": variant === 'empty',
                "bg-destructive/5 border-destructive/20": variant === 'error',
                "bg-background": variant === 'default',
                "bg-success/5 border-success/20": variant === 'success',
            },
            className
        )}>
            {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
            {title && <h3 className="text-lg font-semibold tracking-tight mb-1">{title}</h3>}
            {description && <p className="text-sm text-muted-foreground max-w-sm mb-4">{description}</p>}

            {children}

            {action && (
                action.href ? (
                    <Link href={action.href} className={cn(buttonVariants({ variant: variant === 'error' ? 'destructive' : 'default' }), "mt-4")}>
                        {action.label}
                    </Link>
                ) : (
                    <Button onClick={action.onClick} variant={variant === 'error' ? 'destructive' : 'default'} className="mt-4">
                        {action.label}
                    </Button>
                )
            )}
        </div>
    );
}
