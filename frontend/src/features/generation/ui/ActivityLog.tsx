"use client";

import { useEffect, useRef, useState } from "react";
import { JobEvent } from "../constants/job";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/lib/utils";
import { collapsiblePattern, terminalLogPattern } from "@/shared/design-system";
import { Terminal, ChevronRight, ChevronDown, AlertCircle } from "lucide-react";

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
                    <span className="text-sm text-muted-foreground">Activity Log</span>
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
                            Warnings
                        </Badge>
                    )}
                </div>
                <span className="text-xs text-muted-foreground">
                    {isCollapsed ? "Click to expand" : "Click to collapse"}
                </span>
            </button>

            {/* Expandable content */}
            {!isCollapsed && (
                <div className="mt-2 rounded-lg overflow-hidden border">
                    {events.length === 0 ? (
                        <div className="flex items-center justify-center p-6 text-muted-foreground bg-muted/20">
                            <Terminal className="h-5 w-5 mr-2 opacity-50" />
                            <span className="text-sm">Waiting for events...</span>
                        </div>
                    ) : (
                        <div
                            ref={scrollRef}
                            onScroll={handleScroll}
                            className={terminalLogPattern.containerClasses}
                            style={{ maxHeight }}
                        >
                            <div className="p-3 space-y-1">
                                {/* Terminal log rows - uses terminalLogPattern from design system */}
                                {[...events]
                                    .sort(
                                        (a, b) =>
                                            new Date(a.created_at).getTime() -
                                            new Date(b.created_at).getTime()
                                    )
                                    .map((event, i) => (
                                        <div
                                            key={i}
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
                                        Scroll to latest
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
