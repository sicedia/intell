
import React from 'react';
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/components/ui/badge";

export type EventLevel = 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';

export interface TimelineEvent {
    id: string;
    timestamp: string;
    message: string;
    level: EventLevel;
    progress?: number;
}

interface EventTimelineProps {
    events: TimelineEvent[];
    className?: string;
}

const levelColorMap: Record<EventLevel, string> = {
    INFO: "bg-blue-500",
    WARNING: "bg-yellow-500",
    ERROR: "bg-red-500",
    SUCCESS: "bg-green-500",
};

export function EventTimeline({ events, className }: EventTimelineProps) {
    if (events.length === 0) {
        return <div className="text-sm text-muted-foreground text-center py-4">No events logged yet.</div>;
    }

    return (
        <div className={cn("space-y-4 pl-2", className)}>
            {events.map((event, index) => (
                <div key={event.id || index} className="relative pl-6 pb-2 border-l border-border last:border-l-0 last:pb-0">
                    <div className={cn(
                        "absolute -left-1.5 top-1.5 h-3 w-3 rounded-full border border-background",
                        levelColorMap[event.level] || "bg-gray-500"
                    )} />
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                            {event.progress !== undefined && (
                                <Badge variant="secondary" className="text-[10px] h-4 px-1">{Math.round(event.progress)}%</Badge>
                            )}
                        </div>
                        <p className="text-sm text-foreground">{event.message}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
