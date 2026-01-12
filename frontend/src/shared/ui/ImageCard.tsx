
import React from 'react';
import { Card } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import { cn } from "@/shared/lib/utils";
import { Edit, Sparkles, Eye } from "lucide-react";

interface ImageCardProps {
    title: string;
    imageUrl?: string | null;
    status: string;
    subtitle?: string; // e.g., Algorithm name
    className?: string;
    onView?: () => void;
    onEdit?: () => void;
    onGenerateDescription?: () => void;
    onDownload?: () => void; // Reserved for future use
}

export function ImageCard({ 
    title, 
    imageUrl, 
    status, 
    subtitle, 
    className, 
    onView,
    onEdit,
    onGenerateDescription 
}: ImageCardProps) {
    const isSuccess = status === "SUCCESS";
    
    return (
        <Card className={cn("overflow-hidden flex flex-col h-full", className)}>
            <div className="relative aspect-square w-full bg-muted/40 cursor-pointer group overflow-hidden" onClick={onView}>
                {imageUrl ? (
                    // Use native img for external URLs to avoid Next.js Image optimization issues
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        src={imageUrl}
                        alt={title}
                        className="absolute inset-0 w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
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
                    <h4 className="font-semibold text-sm line-clamp-1" title={title}>{title || "Sin título"}</h4>
                    {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
                </div>
            </div>
            <div className="p-3 pt-0 flex gap-2">
                {isSuccess && onView && (
                    <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1 text-xs h-8" 
                        onClick={(e) => {
                            e.stopPropagation();
                            onView();
                        }}
                    >
                        <Eye className="h-3 w-3 mr-1" />
                        Ver
                    </Button>
                )}
                {isSuccess && onEdit && (
                    <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1 text-xs h-8" 
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit();
                        }}
                    >
                        <Edit className="h-3 w-3 mr-1" />
                        Editar
                    </Button>
                )}
                {isSuccess && onGenerateDescription && (
                    <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1 text-xs h-8" 
                        onClick={(e) => {
                            e.stopPropagation();
                            onGenerateDescription();
                        }}
                        title="Generar descripción con IA"
                    >
                        <Sparkles className="h-3 w-3" />
                    </Button>
                )}
            </div>
        </Card>
    );
}
