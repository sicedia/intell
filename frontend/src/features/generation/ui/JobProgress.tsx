import { JobEvent } from "../constants/job";
import { Badge } from "@/shared/components/ui/badge";

interface JobProgressProps {
    events: JobEvent[];
}

export const JobProgress = ({ events }: JobProgressProps) => {
    if (events.length === 0) {
        return (
            <div className="text-center p-4 text-muted-foreground border rounded-lg bg-muted/20">
                Waiting for events...
            </div>
        );
    }

    // Sort events: newest first
    const sortedEvents = [...events].sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    return (
        <div className="space-y-2">
            <h3 className="text-lg font-medium">Activity Log</h3>
            <div className="h-[300px] border rounded-lg p-4 bg-black/5 dark:bg-white/5 overflow-y-auto">
                <div className="space-y-3">
                    {sortedEvents.map((event, i) => (
                        <div key={i} className="flex flex-col space-y-1 pb-2 border-b border-border/50 last:border-0 last:pb-0">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                    <Badge variant={event.level === 'ERROR' ? 'destructive' : 'secondary'} className="text-[10px] px-1 py-0 h-5">
                                        {event.level}
                                    </Badge>
                                    <span className="text-xs font-mono text-muted-foreground">
                                        {new Date(event.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                                {event.progress > 0 && (
                                    <span className="text-xs font-bold">{event.progress}%</span>
                                )}
                            </div>
                            <p className="text-sm">{event.message}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
