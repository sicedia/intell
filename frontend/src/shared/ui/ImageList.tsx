"use client";

import React, { memo } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { Button } from "@/shared/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import { UserInfo } from "./UserInfo";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";
import { ImageLibraryItem } from "@/features/images/types";
import { Eye, Edit, Sparkles, Trash2, Download, Image as ImageIcon, FileImage } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

interface ImageListProps {
  images: ImageLibraryItem[];
  isLoading?: boolean;
  onView?: (imageId: number) => void;
  onEdit?: (imageId: number) => void;
  onGenerateDescription?: (image: ImageLibraryItem) => void;
  onDelete?: (image: ImageLibraryItem) => void;
  className?: string;
}

/**
 * List view component for displaying images in a table format
 * Optimized for showing more information in a compact layout
 */
export const ImageList = memo(function ImageList({
  images,
  isLoading = false,
  onView,
  onEdit,
  onGenerateDescription,
  onDelete,
  className,
}: ImageListProps) {
  const handleDownload = async (format: "png" | "svg", url: string | null | undefined, title: string) => {
    if (!url) return;

    try {
      // Fetch the image as a blob to force download instead of opening
      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch image");

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);

      // Create a temporary anchor element to trigger download
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${title || "image"}.${format}`;
      link.style.display = "none";
      document.body.appendChild(link);
      link.click();

      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Error downloading image:", error);
      // Fallback to direct download if fetch fails
      const link = document.createElement("a");
      link.href = url;
      link.download = `${title || "image"}.${format}`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (isLoading) {
    return (
      <div className={cn("rounded-md border", className)}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Imagen</TableHead>
              <TableHead>Título</TableHead>
              <TableHead>Algoritmo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Creado por</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Skeleton className="h-16 w-16 rounded" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-32" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-24" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-6 w-20" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-28" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-24" />
                </TableCell>
                <TableCell className="text-right">
                  <Skeleton className="h-8 w-24 ml-auto" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className={cn("rounded-md border p-8 text-center", className)}>
        <p className="text-muted-foreground">No hay imágenes para mostrar</p>
      </div>
    );
  }

  return (
    <div className={cn("rounded-md border overflow-hidden", className)}>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Imagen</TableHead>
              <TableHead>Título</TableHead>
              <TableHead className="hidden sm:table-cell">Algoritmo</TableHead>
              <TableHead className="hidden md:table-cell">Estado</TableHead>
              <TableHead className="hidden lg:table-cell">Creado por</TableHead>
              <TableHead className="hidden md:table-cell">Fecha</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {images.map((image) => {
              const isSuccess = image.status === "SUCCESS";
              const hasBothFormats = !!(image.artifact_png_url && image.artifact_svg_url);

              return (
                <TableRow
                  key={image.id}
                  className="hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => onView?.(image.id)}
                >
                  {/* Thumbnail */}
                  <TableCell className="w-[100px]">
                    <div className="relative w-16 h-16 rounded overflow-hidden bg-muted/40 flex items-center justify-center">
                      {image.artifact_png_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={image.artifact_png_url}
                          alt={image.title || `Imagen ${image.id}`}
                          className="w-full h-full object-contain"
                          loading="lazy"
                        />
                      ) : (
                        <div className="text-xs text-muted-foreground text-center p-2">
                          Sin imagen
                        </div>
                      )}
                      {isSuccess && (
                        <div className="absolute top-1 right-1">
                          <StatusBadge status={image.status} className="text-[10px] px-1 py-0" />
                        </div>
                      )}
                    </div>
                  </TableCell>

                  {/* Title */}
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <div className="font-medium line-clamp-1">
                        {image.title || `Imagen ${image.id}`}
                      </div>
                      {image.user_description && (
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {image.user_description}
                        </div>
                      )}
                    </div>
                  </TableCell>

                  {/* Algorithm - Hidden on small screens */}
                  <TableCell className="hidden sm:table-cell">
                    <div className="text-sm text-muted-foreground">{image.algorithm_key}</div>
                  </TableCell>

                  {/* Status - Hidden on medium screens */}
                  <TableCell className="hidden md:table-cell">
                    <StatusBadge status={image.status} />
                  </TableCell>

                  {/* Created By - Hidden on large screens */}
                  <TableCell className="hidden lg:table-cell">
                    {(image.created_by_username || image.created_by_email || image.created_by) && (
                      <UserInfo
                        username={image.created_by_username}
                        email={image.created_by_email}
                        userId={image.created_by}
                        variant="compact"
                        showIcon={false}
                      />
                    )}
                  </TableCell>

                  {/* Date - Hidden on medium screens */}
                  <TableCell className="hidden md:table-cell">
                    <div className="text-sm text-muted-foreground">
                      {new Date(image.created_at).toLocaleDateString("es-ES", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </div>
                  </TableCell>

                  {/* Actions */}
                  <TableCell className="text-right">
                    <div
                      className="flex items-center justify-end gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {isSuccess && (
                        <>
                          {onView && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => onView(image.id)}
                              aria-label="Ver imagen"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          )}
                          {onEdit && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => onEdit(image.id)}
                              aria-label="Editar imagen"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                          {hasBothFormats && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  aria-label="Descargar imagen"
                                >
                                  <Download className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                {image.artifact_png_url && (
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleDownload(
                                        "png",
                                        image.artifact_png_url,
                                        image.title || `Imagen ${image.id}`
                                      )
                                    }
                                  >
                                    <FileImage className="h-4 w-4 mr-2" />
                                    Descargar PNG
                                  </DropdownMenuItem>
                                )}
                                {image.artifact_svg_url && (
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleDownload(
                                        "svg",
                                        image.artifact_svg_url,
                                        image.title || `Imagen ${image.id}`
                                      )
                                    }
                                  >
                                    <ImageIcon className="h-4 w-4 mr-2" />
                                    Descargar SVG
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                          {!hasBothFormats && image.artifact_png_url && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() =>
                                handleDownload(
                                  "png",
                                  image.artifact_png_url,
                                  image.title || `Imagen ${image.id}`
                                )
                              }
                              aria-label="Descargar PNG"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          )}
                          {onGenerateDescription && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => onGenerateDescription(image)}
                              aria-label="Generar descripción con IA"
                              title="Generar descripción con IA"
                            >
                              <Sparkles className="h-4 w-4" />
                            </Button>
                          )}
                          {onDelete && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                              onClick={() => onDelete(image)}
                              aria-label="Eliminar imagen"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
});
