"use client";

import React, { useState } from 'react';
import { Card } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import { cn } from "@/shared/lib/utils";
import { Edit, Sparkles, Eye, Download, Image as ImageIcon, FileImage } from "lucide-react";
import { UserInfo } from "./UserInfo";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";

interface ImageCardProps {
    title: string;
    imageUrl?: string | null; // PNG URL (default)
    svgUrl?: string | null; // SVG URL (optional)
    status: string;
    subtitle?: string; // e.g., Algorithm name
    className?: string;
    size?: "sm" | "md" | "lg"; // Card size variant
    variant?: "compact" | "detailed"; // Compact for gallery, detailed for generate page
    onView?: () => void;
    onEdit?: () => void;
    onGenerateDescription?: () => void;
    createdByUsername?: string | null;
    createdByEmail?: string | null;
    createdBy?: number | null;
    showFormatToggle?: boolean; // Show SVG/PNG toggle (for images page)
    showDownload?: boolean; // Show download button
}

/**
 * Reusable ImageCard component with download and format switching capabilities
 * Used across /generate, /images, and /dashboard pages
 */
export function ImageCard({ 
    title, 
    imageUrl,
    svgUrl,
    status, 
    subtitle, 
    className,
    size = "md",
    variant = "compact",
    onView,
    onEdit,
    onGenerateDescription,
    createdByUsername,
    createdByEmail,
    createdBy,
    showFormatToggle = false,
    showDownload = true,
}: ImageCardProps) {
    const isSuccess = status === "SUCCESS";
    const [selectedFormat, setSelectedFormat] = useState<"png" | "svg">(
        svgUrl ? "svg" : "png"
    );
    
    // Size variants for compact mode
    const sizeClasses = {
        sm: "aspect-square",
        md: "aspect-square",
        lg: "aspect-square",
    };
    
    // For detailed variant, use fixed height
    const isDetailed = variant === "detailed";

    const handleDownload = (format: "png" | "svg", url: string | null | undefined) => {
        if (!url) return;
        
        // Create a temporary anchor element to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = `${title || 'image'}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const currentImageUrl = selectedFormat === "svg" && svgUrl ? svgUrl : imageUrl;
    const hasBothFormats = !!(imageUrl && svgUrl);
    const canToggleFormat = showFormatToggle && hasBothFormats;

    // Render image area based on variant
    const renderImageArea = () => {
        if (isDetailed) {
            // Detailed variant: larger image with tabs if both formats available
            const hasBoth = !!(imageUrl && svgUrl);
            
            return (
                <div className="relative bg-checkered bg-gray-50 dark:bg-gray-900 border-b">
                    {hasBoth ? (
                        <Tabs value={selectedFormat} onValueChange={(v) => setSelectedFormat(v as "png" | "svg")} className="w-full">
                            <div className="p-4 min-h-[300px] flex items-center justify-center relative">
                                <TabsContent value="png" className="mt-0 w-full flex justify-center">
                                    {imageUrl ? (
                                        <div className="relative w-full max-w-full h-[300px] flex items-center justify-center">
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img 
                                                src={imageUrl} 
                                                alt={`${title} - PNG`} 
                                                className="max-h-[300px] max-w-full object-contain"
                                            />
                                        </div>
                                    ) : (
                                        <span className="text-sm text-muted-foreground">No PNG available</span>
                                    )}
                                </TabsContent>
                                <TabsContent value="svg" className="mt-0 w-full flex justify-center">
                                    {svgUrl ? (
                                        <div className="relative w-full max-w-full h-[300px] flex items-center justify-center">
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img 
                                                src={svgUrl} 
                                                alt={`${title} - SVG`} 
                                                className="max-h-[300px] max-w-full object-contain"
                                            />
                                        </div>
                                    ) : (
                                        <span className="text-sm text-muted-foreground">No SVG available</span>
                                    )}
                                </TabsContent>
                                
                                {/* Status Badge */}
                                <div className="absolute top-2 right-2 z-10">
                                    <StatusBadge status={status} />
                                </div>

                                {/* Download Button - Top Left */}
                                {isSuccess && showDownload && (
                                    <div className="absolute top-2 left-2 z-10">
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button
                                                    variant="secondary"
                                                    size="sm"
                                                    className="h-8 w-8 p-0 bg-background/90 hover:bg-background shadow-md"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <Download className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="start">
                                                {imageUrl && (
                                                    <DropdownMenuItem
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDownload("png", imageUrl);
                                                        }}
                                                    >
                                                        <FileImage className="h-4 w-4 mr-2" />
                                                        Descargar PNG
                                                    </DropdownMenuItem>
                                                )}
                                                {svgUrl && (
                                                    <DropdownMenuItem
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDownload("svg", svgUrl);
                                                        }}
                                                    >
                                                        <ImageIcon className="h-4 w-4 mr-2" />
                                                        Descargar SVG
                                                    </DropdownMenuItem>
                                                )}
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                )}
                            </div>
                            <TabsList className="w-full rounded-none border-b">
                                <TabsTrigger value="png" className="flex-1">PNG</TabsTrigger>
                                <TabsTrigger value="svg" className="flex-1">SVG</TabsTrigger>
                            </TabsList>
                        </Tabs>
                    ) : (
                        <div className="p-4 min-h-[300px] flex items-center justify-center relative">
                            {currentImageUrl ? (
                                <div className="relative w-full max-w-full h-[300px] flex items-center justify-center">
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                    <img 
                                        src={currentImageUrl} 
                                        alt={title} 
                                        className="max-h-[300px] max-w-full object-contain"
                                    />
                                </div>
                            ) : (
                                <span className="text-sm text-muted-foreground">No image available</span>
                            )}
                            
                            {/* Status Badge */}
                            <div className="absolute top-2 right-2 z-10">
                                <StatusBadge status={status} />
                            </div>

                            {/* Download Button - Top Left */}
                            {isSuccess && showDownload && currentImageUrl && (
                                <div className="absolute top-2 left-2 z-10">
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                className="h-8 w-8 p-0 bg-background/90 hover:bg-background shadow-md"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <Download className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="start">
                                            {imageUrl && (
                                                <DropdownMenuItem
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDownload("png", imageUrl);
                                                    }}
                                                >
                                                    <FileImage className="h-4 w-4 mr-2" />
                                                    Descargar PNG
                                                </DropdownMenuItem>
                                            )}
                                            {svgUrl && (
                                                <DropdownMenuItem
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDownload("svg", svgUrl);
                                                    }}
                                                >
                                                    <ImageIcon className="h-4 w-4 mr-2" />
                                                    Descargar SVG
                                                </DropdownMenuItem>
                                            )}
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            );
        } else {
            // Compact variant: smaller card for gallery
            return (
                <div className={cn(
                    "relative w-full bg-muted/40 cursor-pointer group overflow-hidden",
                    sizeClasses[size]
                )}>
                    {currentImageUrl ? (
                        <div className="absolute inset-0 flex items-center justify-center p-2">
                            {/* Use native img for external URLs to avoid Next.js Image optimization issues */}
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src={currentImageUrl}
                                alt={title}
                                className="max-w-full max-h-full w-auto h-auto object-contain transition-transform duration-300 group-hover:scale-105"
                            />
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                            Pending...
                        </div>
                    )}
                    
                    {/* Status Badge */}
                    <div className="absolute top-2 right-2 z-10">
                        <StatusBadge status={status} />
                    </div>

                    {/* Download Button - Top Left */}
                    {isSuccess && showDownload && currentImageUrl && (
                        <div className="absolute top-2 left-2 z-10">
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        className="h-8 w-8 p-0 bg-background/90 hover:bg-background shadow-md"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <Download className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start">
                                    {imageUrl && (
                                        <DropdownMenuItem
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDownload("png", imageUrl);
                                            }}
                                        >
                                            <FileImage className="h-4 w-4 mr-2" />
                                            Descargar PNG
                                        </DropdownMenuItem>
                                    )}
                                    {svgUrl && (
                                        <DropdownMenuItem
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDownload("svg", svgUrl);
                                            }}
                                        >
                                            <ImageIcon className="h-4 w-4 mr-2" />
                                            Descargar SVG
                                        </DropdownMenuItem>
                                    )}
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    )}

                    {/* Format Toggle - Bottom Right (only in images page) */}
                    {canToggleFormat && (
                        <div className="absolute bottom-2 right-2 z-10">
                            <Tabs value={selectedFormat} onValueChange={(v) => setSelectedFormat(v as "png" | "svg")}>
                                <TabsList className="h-8 bg-background/90 shadow-md">
                                    <TabsTrigger 
                                        value="png" 
                                        className="text-xs px-2"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        PNG
                                    </TabsTrigger>
                                    <TabsTrigger 
                                        value="svg" 
                                        className="text-xs px-2"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        SVG
                                    </TabsTrigger>
                                </TabsList>
                            </Tabs>
                        </div>
                    )}
                </div>
            );
        }
    };

    return (
        <Card className={cn("overflow-hidden flex flex-col h-full", className)}>
            {/* Header/Title Section - Only for detailed variant */}
            {isDetailed && (
                <div className="py-4 px-4 bg-muted/30 border-b">
                    <div className="flex justify-between items-start gap-2">
                        <div className="flex-1 min-w-0">
                            <h4 className="text-base font-medium truncate" title={title}>{title || subtitle || "Sin título"}</h4>
                            {subtitle && title && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
                            {(createdByUsername || createdByEmail || createdBy) && (
                                <div className="mt-1.5">
                                    <UserInfo
                                        username={createdByUsername}
                                        email={createdByEmail}
                                        userId={createdBy}
                                        variant="compact"
                                        showIcon={true}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
            
            {renderImageArea()}

            {/* Content Section - Only for compact variant */}
            {!isDetailed && (
                <>
                    <div className="p-3 flex-1 flex flex-col gap-2">
                        <div>
                            <h4 className="font-semibold text-sm line-clamp-1" title={title}>{title || "Sin título"}</h4>
                            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
                        </div>
                        {(createdByUsername || createdByEmail || createdBy) && (
                            <UserInfo
                                username={createdByUsername}
                                email={createdByEmail}
                                userId={createdBy}
                                variant="compact"
                                showIcon={true}
                            />
                        )}
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
                </>
            )}
        </Card>
    );
}
