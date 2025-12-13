
import React from 'react';
import { Card } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import { cn } from "@/shared/lib/utils";

interface ImageCardProps {
    title: string;
    imageUrl?: string | null;
    status: string;
    subtitle?: string; // e.g., Algorithm name
    className?: string;
    onView?: () => void;
    onDownload?: () => void;
}

export function ImageCard({ title, imageUrl, status, subtitle, className, onView, onDownload }: ImageCardProps) {
    return (
        <Card className={cn("overflow-hidden flex flex-col h-full", className)}>
            <div className="relative aspect-square w-full bg-muted/40 cursor-pointer group" onClick={onView}>
                {imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        src={imageUrl}
                        alt={title}
                        className="object-cover w-full h-full transition-transform duration-300 group-hover:scale-105"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                        Pending...
                    </div>
                )}
                <div className="absolute top-2 right-2">
                    <StatusBadge status={status} />
                </div>
            </div>
            <div className="p-3 flex-1 flex flex-col gap-2">
                <div>
                    <h4 className="font-semibold text-sm line-clamp-1" title={title}>{title}</h4>
                    {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
                </div>
            </div>
            <div className="p-3 pt-0 flex gap-2">
                <Button variant="outline" size="sm" className="w-full text-xs h-8" onClick={onView} disabled={!imageUrl}>
                    View
                </Button>
            </div>
        </Card>
    );
}
