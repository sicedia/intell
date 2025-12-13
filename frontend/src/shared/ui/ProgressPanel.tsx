import React from 'react';
import { Progress } from "@/shared/components/ui/progress";
import { cn } from "@/shared/lib/utils";

interface ProgressPanelProps {
    progress: number;
    message?: string;
    step?: string;
    className?: string;
}

export function ProgressPanel({ progress, message, step, className }: ProgressPanelProps) {
    return (
        <div className={cn("p-4 rounded-xl border bg-card shadow-sm space-y-3", className)}>
            <div className="flex justify-between items-end text-sm">
                <span className="font-medium text-foreground">{step || "Processing..."}</span>
                <span className="text-muted-foreground">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            {message && (
                <p className="text-xs text-muted-foreground animate-pulse">
                    {message}
                </p>
            )}
        </div>
    );
}
