"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { JobEvent } from "../constants/job";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Progress } from "@/shared/components/ui/progress";
import { cn } from "@/shared/lib/utils";
import { collapsiblePattern, terminalLogPattern } from "@/shared/design-system";
import { Terminal, ChevronRight, ChevronDown, AlertCircle, CheckCircle2, Circle, Loader2 } from "lucide-react";

interface ActivityLogProps {
    events: JobEvent[];
    className?: string;
    defaultCollapsed?: boolean;
    maxHeight?: string;
}

export const ActivityLog = ({
    events,
    className,
    defaultCollapsed = true,
    maxHeight = "300px",
}: ActivityLogProps) => {
    const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [autoScroll, setAutoScroll] = useState(true);
    const t = useTranslations('generate.activityLog');

    // Auto-scroll to bottom when new events arrive
    useEffect(() => {
        if (autoScroll && scrollRef.current && events.length > 0) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events, autoScroll]);

    // Detect if user scrolled up to disable auto-scroll
    const handleScroll = () => {
        if (!scrollRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
        setAutoScroll(isAtBottom);
    };

    const hasErrors = events.some((e) => e.level === "ERROR");
    const hasWarnings = events.some((e) => e.level === "WARNING");
    const errorCount = events.filter((e) => e.level === "ERROR").length;

    // Group events by entity_id (image_task_id) to show progress per task
    const groupedEvents = useMemo(() => {
        const groups: Map<number | string | null, JobEvent[]> = new Map();
        const jobEvents: JobEvent[] = [];
        
        events.forEach((event) => {
            // Check if event is for an image task (entity_type is 'image_task')
            const isImageTaskEvent = event.entity_type === 'image_task' || 
                (event.entity_type && event.entity_type.toLowerCase() === 'imagetask');
            
            if (isImageTaskEvent && event.entity_id) {
                const taskId = event.entity_id;
                if (!groups.has(taskId)) {
                    groups.set(taskId, []);
                }
                groups.get(taskId)!.push(event);
            } else {
                jobEvents.push(event);
            }
        });
        
        return { groups, jobEvents };
    }, [events]);

    // Get latest progress for each task
    const getLatestProgress = (taskEvents: JobEvent[]): number => {
        const progressEvents = taskEvents
            .filter((e) => e.progress !== null && e.progress !== undefined)
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        return progressEvents.length > 0 ? Number(progressEvents[0].progress) : 0;
    };

    // Check if task is completed
    const isTaskCompleted = (taskEvents: JobEvent[]): boolean => {
        return taskEvents.some((e) => e.event_type === "DONE" && Number(e.progress) === 100);
    };

    // Check if task is in progress
    const isTaskInProgress = (taskEvents: JobEvent[]): boolean => {
        const latestProgress = getLatestProgress(taskEvents);
        return latestProgress > 0 && latestProgress < 100 && !isTaskCompleted(taskEvents);
    };

    return (
        <div className={cn("border-t pt-4", className)}>
            {/* Compact toggle header - uses collapsiblePattern from design system */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className={cn(
                    collapsiblePattern.toggleClasses,
                    isCollapsed ? collapsiblePattern.collapsedClasses : collapsiblePattern.expandedClasses
                )}
            >
                <div className="flex items-center gap-2">
                    {isCollapsed ? (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                    <Terminal className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">{t('activityLog')}</span>
                    {events.length > 0 && (
                        <Badge variant="secondary" className="text-[10px] h-5 px-1.5">
                            {events.length}
                        </Badge>
                    )}
                    {hasErrors && (
                        <Badge variant="destructive" className="text-[10px] h-5 px-1.5 gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errorCount}
                        </Badge>
                    )}
                    {hasWarnings && !hasErrors && (
                        <Badge variant="outline" className="text-[10px] h-5 px-1.5 text-amber-600">
                            {t('warnings')}
                        </Badge>
                    )}
                </div>
                <span className="text-xs text-muted-foreground">
                    {isCollapsed ? t('clickToExpand') : t('clickToCollapse')}
                </span>
            </button>

            {/* Expandable content */}
            {!isCollapsed && (
                <div className="mt-2 rounded-lg overflow-hidden border">
                    {events.length === 0 ? (
                        <div className="flex items-center justify-center p-6 text-muted-foreground bg-muted/20">
                            <Terminal className="h-5 w-5 mr-2 opacity-50" />
                            <span className="text-sm">{t('waitingForEvents')}</span>
                        </div>
                    ) : (
                        <div
                            ref={scrollRef}
                            onScroll={handleScroll}
                            className={terminalLogPattern.containerClasses}
                            style={{ maxHeight }}
                        >
                            <div className="p-3 space-y-3">
                                {/* Job-level events */}
                                {groupedEvents.jobEvents
                                    .sort(
                                        (a, b) =>
                                            new Date(a.created_at).getTime() -
                                            new Date(b.created_at).getTime()
                                    )
                                    .map((event, i) => (
                                        <div
                                            key={`job-${i}`}
                                            className={cn(
                                                terminalLogPattern.rowClasses,
                                                event.level === "ERROR" && terminalLogPattern.errorRowClasses
                                            )}
                                        >
                                            <span className={terminalLogPattern.timestampClasses}>
                                                {new Date(event.created_at).toLocaleTimeString()}
                                            </span>
                                            <span
                                                className={cn(
                                                    "shrink-0 w-14 text-right",
                                                    terminalLogPattern.levelClasses[event.level as keyof typeof terminalLogPattern.levelClasses] ||
                                                        terminalLogPattern.levelClasses.DEBUG
                                                )}
                                            >
                                                [{event.level}]
                                            </span>
                                            <span className={terminalLogPattern.messageClasses}>
                                                {event.message}
                                            </span>
                                            {Number(event.progress) > 0 && (
                                                <span className="text-green-400 shrink-0 ml-auto">
                                                    {event.progress}%
                                                </span>
                                            )}
                                        </div>
                                    ))}

                                {/* Task-level events grouped by image_task_id */}
                                {Array.from(groupedEvents.groups.entries())
                                    .map(([taskId, taskEvents]) => {
                                        const sortedEvents = taskEvents.sort(
                                            (a, b) =>
                                                new Date(a.created_at).getTime() -
                                                new Date(b.created_at).getTime()
                                        );
                                        const latestProgress = getLatestProgress(sortedEvents);
                                        const completed = isTaskCompleted(sortedEvents);
                                        const inProgress = isTaskInProgress(sortedEvents);
                                        
                                        // Get task name from first START event
                                        const startEvent = sortedEvents.find((e) => e.event_type === "START");
                                        const taskName = startEvent?.message?.split(":")[1]?.trim() || t('task', { id: taskId ?? 0 });

                                        return (
                                            <div
                                                key={`task-${taskId}`}
                                                className="border-l-2 border-slate-700 pl-3 space-y-1.5"
                                            >
                                                {/* Task header with progress */}
                                                <div className="flex items-center gap-2 mb-1">
                                                    {completed ? (
                                                        <CheckCircle2 className="h-3.5 w-3.5 text-green-400 shrink-0" />
                                                    ) : inProgress ? (
                                                        <Loader2 className="h-3.5 w-3.5 text-blue-400 shrink-0 animate-spin" />
                                                    ) : (
                                                        <Circle className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                                                    )}
                                                    <span className="text-xs font-medium text-slate-300">
                                                        {taskName}
                                                    </span>
                                                    {inProgress && (
                                                        <span className="text-xs text-blue-400 ml-auto">
                                                            {latestProgress}%
                                                        </span>
                                                    )}
                                                    {completed && (
                                                        <span className="text-xs text-green-400 ml-auto">
                                                            Complete
                                                        </span>
                                                    )}
                                                </div>
                                                
                                                {/* Progress bar for in-progress tasks */}
                                                {inProgress && (
                                                    <div className="mb-1.5">
                                                        <Progress 
                                                            value={latestProgress} 
                                                            className="h-1 bg-slate-800"
                                                        />
                                                    </div>
                                                )}

                                                {/* Task events */}
                                                <div className="space-y-0.5 ml-5">
                                                    {sortedEvents.map((event, i) => (
                                                        <div
                                                            key={`task-${taskId}-event-${i}`}
                                                            className={cn(
                                                                "text-xs",
                                                                terminalLogPattern.rowClasses,
                                                                event.level === "ERROR" && terminalLogPattern.errorRowClasses,
                                                                "py-0.5"
                                                            )}
                                                        >
                                                            <span className={terminalLogPattern.timestampClasses}>
                                                                {new Date(event.created_at).toLocaleTimeString()}
                                                            </span>
                                                            <span
                                                                className={cn(
                                                                    "shrink-0 w-12 text-right text-[10px]",
                                                                    terminalLogPattern.levelClasses[event.level as keyof typeof terminalLogPattern.levelClasses] ||
                                                                        terminalLogPattern.levelClasses.DEBUG
                                                                )}
                                                            >
                                                                [{event.level}]
                                                            </span>
                                                            <span className={cn(terminalLogPattern.messageClasses, "text-xs")}>
                                                                {event.message}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                            </div>
                            {/* Auto-scroll indicator */}
                            {!autoScroll && events.length > 5 && (
                                <div className="sticky bottom-0 p-2 bg-slate-900/90 border-t border-slate-800">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setAutoScroll(true);
                                            if (scrollRef.current) {
                                                scrollRef.current.scrollTop =
                                                    scrollRef.current.scrollHeight;
                                            }
                                        }}
                                        className="w-full text-xs text-slate-400 hover:text-slate-200"
                                    >
                                        <ChevronDown className="h-3 w-3 mr-1" />
                                        {t('scrollToLatest')}
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
