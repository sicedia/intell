"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";
import { ImageLibraryFilters } from "@/features/images/ui/ImageLibraryFilters";
import { ImageDetailDialog } from "@/features/images/ui/ImageDetailDialog";
import { AIDescriptionDialog } from "@/features/images/ui/AIDescriptionDialog";
import { useImages } from "@/features/images/hooks/useImages";
import { ImageLibraryItem, ImageFilters, ImageTask } from "@/features/images/types";
import { Image as ImageIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/shared/components/ui/button";
import { LoadingState } from "@/shared/ui/LoadingState";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { useImageLibraryViewMode } from "@/features/images/hooks/useImageLibraryViewMode";

export default function ImagesPage() {
  const queryClient = useQueryClient();
  const { viewMode: libraryViewMode, setViewMode: setLibraryViewMode } = useImageLibraryViewMode();
  const [filters, setFilters] = useState<ImageFilters>(() => {
    // Initialize filters based on localStorage view mode after hydration
    // This will be updated by the useEffect below
    return {};
  });

  // Sync filters.group_by with libraryViewMode whenever it changes
  // This handles both initial load from localStorage and manual changes
  useEffect(() => {
    const expectedGroupBy = libraryViewMode === "grouped" ? "job" : undefined;
    setFilters((prev) => {
      // Only update if the value actually changed to avoid unnecessary re-renders
      if (prev.group_by !== expectedGroupBy) {
        return { ...prev, group_by: expectedGroupBy };
      }
      return prev;
    });
  }, [libraryViewMode]);

  // Handler to update both libraryViewMode and filters immediately
  // Using useCallback to avoid recreating the function on each render
  const handleLibraryViewModeChange = useCallback((mode: "all" | "grouped") => {
    setLibraryViewMode(mode);
    // Immediately update filters to avoid delay
    const expectedGroupBy = mode === "grouped" ? "job" : undefined;
    setFilters((prev) => ({
      ...prev,
      group_by: expectedGroupBy,
    }));
  }, [setLibraryViewMode]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false);
  const [aiImage, setAiImage] = useState<ImageTask | null>(null);

  const { data: images, isLoading, error } = useImages(filters, true);

  // Memoize handlers to avoid recreating them on each render
  const handleViewImage = useCallback((imageId: number) => {
    setSelectedImageId(imageId);
    setIsDetailDialogOpen(true);
  }, []);

  const handleEditImage = useCallback((imageId: number) => {
    setSelectedImageId(imageId);
    setIsDetailDialogOpen(true);
  }, []);

  // Helper function to convert ImageLibraryItem to ImageTask
  const convertLibraryItemToTask = useCallback((image: ImageLibraryItem): ImageTask => {
    return {
      id: image.id,
      job: image.job_id,
      created_by: image.created_by,
      created_by_username: image.created_by_username,
      created_by_email: image.created_by_email,
      algorithm_key: image.algorithm_key,
      algorithm_version: "1.0",
      params: {},
      output_format: "both",
      status: image.status,
      progress: 100,
      artifact_png_url: image.artifact_png_url,
      artifact_svg_url: image.artifact_svg_url,
      chart_data: null,
      error_code: null,
      error_message: null,
      trace_id: null,
      title: image.title,
      user_description: image.user_description,
      ai_context: image.ai_context,
      group: image.group,
      tags: image.tags.map((t) => t.id),
      is_published: image.is_published,
      published_at: image.published_at,
      created_at: image.created_at,
      updated_at: image.updated_at,
    };
  }, []);

  const handleGenerateDescription = useCallback((image: ImageLibraryItem | ImageTask) => {
    // Convert ImageLibraryItem to ImageTask format if needed
    const imageTask: ImageTask = "job_id" in image 
      ? convertLibraryItemToTask(image as ImageLibraryItem)
      : (image as ImageTask);
    
    setAiImage(imageTask);
    setIsAIDialogOpen(true);
  }, [convertLibraryItemToTask]);

  const imagesList = (images as ImageLibraryItem[]) || [];
  const isGrouped = filters.group_by === "job";

  // Group images by job_id when in grouped mode
  const groupedImages = useMemo(() => {
    if (!isGrouped) return null;

    const groups: Record<number, ImageLibraryItem[]> = {};
    imagesList.forEach((image) => {
      const jobId = image.job_id;
      if (!groups[jobId]) {
        groups[jobId] = [];
      }
      groups[jobId].push(image);
    });

    // Sort groups by most recent image in each group
    return Object.entries(groups)
      .map(([jobId, images]) => ({
        jobId: parseInt(jobId),
        images: images.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
        dateTag: images[0]?.tags.find((t) => t.name.startsWith("Generado ")),
      }))
      .sort((a, b) => {
        // Sort by most recent image creation date
        const aDate = new Date(a.images[0]?.created_at || 0).getTime();
        const bDate = new Date(b.images[0]?.created_at || 0).getTime();
        return bDate - aDate;
      });
  }, [imagesList, isGrouped]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Image Library"
        subtitle="Browse and manage all generated visualizations"
        actions={
          <Link href="/generate">
            <Button>
              <ImageIcon className="mr-2 h-4 w-4" />
              Generate New
            </Button>
          </Link>
        }
      />

      {/* Filters */}
      <ImageLibraryFilters
        filters={filters}
        onFiltersChange={setFilters}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        libraryViewMode={libraryViewMode}
        onLibraryViewModeChange={handleLibraryViewModeChange}
      />

      {/* Content */}
      {isLoading ? (
        <LoadingState variant="skeleton" />
      ) : error ? (
        <EmptyState
          title="Error al cargar imágenes"
          description={error instanceof Error ? error.message : "Ocurrió un error desconocido"}
          icon={<ImageIcon className="h-12 w-12 text-muted-foreground" />}
        />
      ) : imagesList.length === 0 ? (
        <EmptyState
          title="No hay imágenes en tu librería"
          description="Genera visualizaciones desde tus datos para verlas aparecer aquí. Puedes organizar, buscar y descargar tus imágenes generadas."
          icon={<ImageIcon className="h-12 w-12 text-muted-foreground" />}
          action={{
            label: "Generar tu primera imagen",
            href: "/generate",
            variant: "default",
          }}
        />
      ) : isGrouped && groupedImages ? (
        // Grouped view
        <div className="space-y-6">
          {groupedImages.map((group) => (
            <Card key={group.jobId}>
              <CardHeader>
                <CardTitle className="text-lg">
                  {group.dateTag?.name || `Lote generado el ${new Date(group.images[0]?.created_at || "").toLocaleDateString()}`}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {group.images.length} {group.images.length === 1 ? "imagen" : "imágenes"} de este lote
                </p>
              </CardHeader>
              <CardContent>
                <GalleryGrid isLoading={false}>
                  {group.images.map((image) => (
                    <ImageCard
                      key={image.id}
                      title={image.title || `Imagen ${image.id}`}
                      imageUrl={image.artifact_png_url}
                      svgUrl={image.artifact_svg_url}
                      status={image.status}
                      subtitle={image.algorithm_key}
                      createdBy={image.created_by}
                      createdByUsername={image.created_by_username}
                      createdByEmail={image.created_by_email}
                      showFormatToggle={true}
                      showDownload={true}
                      onView={() => handleViewImage(image.id)}
                      onEdit={() => handleEditImage(image.id)}
                      onGenerateDescription={() => handleGenerateDescription(image)}
                    />
                  ))}
                </GalleryGrid>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        // All images view
        <GalleryGrid isLoading={false}>
          {imagesList.map((image) => (
            <ImageCard
              key={image.id}
              title={image.title || `Imagen ${image.id}`}
              imageUrl={image.artifact_png_url}
              svgUrl={image.artifact_svg_url}
              status={image.status}
              subtitle={image.algorithm_key}
              createdBy={image.created_by}
              createdByUsername={image.created_by_username}
              createdByEmail={image.created_by_email}
              showFormatToggle={true}
              showDownload={true}
              onView={() => handleViewImage(image.id)}
              onEdit={() => handleEditImage(image.id)}
              onGenerateDescription={() => handleGenerateDescription(image)}
            />
          ))}
        </GalleryGrid>
      )}

      {/* Detail Dialog */}
      <ImageDetailDialog
        imageId={selectedImageId}
        open={isDetailDialogOpen}
        onOpenChange={setIsDetailDialogOpen}
      />

      {/* AI Description Dialog */}
      {aiImage && (
        <AIDescriptionDialog
          image={aiImage}
          open={isAIDialogOpen}
          onOpenChange={(open) => {
            setIsAIDialogOpen(open);
            if (!open) {
              setAiImage(null);
            }
          }}
          onDescriptionSaved={() => {
            // Refresh images list
            queryClient.invalidateQueries({ queryKey: ["images"] });
            if (aiImage) {
              queryClient.invalidateQueries({ queryKey: ["image", aiImage.id] });
            }
          }}
        />
      )}
    </div>
  );
}
