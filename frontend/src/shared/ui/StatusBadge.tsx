
import React from 'react';
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";

export type StatusType =
    | 'PENDING'
    | 'RUNNING'
    | 'SUCCESS'
    | 'PARTIAL_SUCCESS'
    | 'FAILED'
    | 'CANCELLED'
    | 'COMPLETED'; // Aligning with common backends

interface StatusBadgeProps {
    status: string;
    className?: string;
}

const statusStyles: Record<string, string> = {
    PENDING: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    RUNNING: "bg-blue-100 text-blue-700 hover:bg-blue-100/80 border-blue-200",
    SUCCESS: "bg-success/15 text-success hover:bg-success/25 border-success/20",
    COMPLETED: "bg-success/15 text-success hover:bg-success/25 border-success/20",
    PARTIAL_SUCCESS: "bg-warning/15 text-warning-foreground hover:bg-warning/25 border-warning/20",
    FAILED: "bg-destructive/15 text-destructive hover:bg-destructive/25 border-destructive/20",
    CANCELLED: "bg-muted text-muted-foreground hover:bg-muted/80",
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
    const normalizedStatus = status?.toUpperCase() || 'PENDING';
    const style = statusStyles[normalizedStatus] || statusStyles.PENDING;

    return (
        <Badge variant="outline" className={cn("capitalize px-2 py-0.5", style, className)}>
            {normalizedStatus.replace('_', ' ').toLowerCase()}
        </Badge>
    );
}
