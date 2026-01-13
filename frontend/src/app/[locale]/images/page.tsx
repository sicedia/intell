"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslations } from "next-intl";
import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageList } from "@/shared/ui/ImageList";
import { ImageCard } from "@/shared/ui/ImageCard";
import { Pagination } from "@/shared/ui/Pagination";
import { ImageLibraryFilters } from "@/features/images/ui/ImageLibraryFilters";
import { ImageDetailDialog } from "@/features/images/ui/ImageDetailDialog";
import { AIDescriptionDialog } from "@/features/images/ui/AIDescriptionDialog";
import { useImages, useDeleteImage } from "@/features/images/hooks/useImages";
import { useImageViewMode } from "@/features/images/hooks/useImageViewMode";
import { ImageLibraryItem, ImageFilters, ImageTask } from "@/features/images/types";
import { Image as ImageIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/shared/components/ui/button";
import { LoadingState } from "@/shared/ui/LoadingState";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { useImageLibraryViewMode } from "@/features/images/hooks/useImageLibraryViewMode";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/components/ui/alert-dialog";

const DEFAULT_PAGE_SIZE = 20;

export default function ImagesPage() {
  const queryClient = useQueryClient();
  const { viewMode: libraryViewMode, setViewMode: setLibraryViewMode } = useImageLibraryViewMode();
  const { viewMode, setViewMode } = useImageViewMode(); // Grid/List view mode with persistence
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [currentPage, setCurrentPage] = useState(1);
  
  const [filters, setFilters] = useState<ImageFilters>(() => {
    // Initialize filters based on localStorage view mode after hydration
    // This will be updated by the useEffect below
    return {
      page: 1,
      pageSize: DEFAULT_PAGE_SIZE,
    };
  });

  // Sync filters.group_by with libraryViewMode whenever it changes
  // This handles both initial load from localStorage and manual changes
  useEffect(() => {
    const expectedGroupBy = libraryViewMode === "grouped" ? "job" : undefined;
    setFilters((prev) => {
      // Only update if the value actually changed to avoid unnecessary re-renders
      if (prev.group_by !== expectedGroupBy) {
        return { ...prev, group_by: expectedGroupBy, page: 1 }; // Reset to page 1 when changing view mode
      }
      return prev;
    });
  }, [libraryViewMode]);

  // Sync current page with filters.page
  useEffect(() => {
    if (filters.page && filters.page !== currentPage) {
      setCurrentPage(filters.page);
    }
  }, [filters.page, currentPage]);

  // Handler to update both libraryViewMode and filters immediately
  // Using useCallback to avoid recreating the function on each render
  const handleLibraryViewModeChange = useCallback((mode: "all" | "grouped") => {
    setLibraryViewMode(mode);
    // Immediately update filters to avoid delay
    const expectedGroupBy = mode === "grouped" ? "job" : undefined;
    setFilters((prev) => ({
      ...prev,
      group_by: expectedGroupBy,
      page: 1, // Reset to page 1 when changing library view mode
    }));
  }, [setLibraryViewMode]);

  // Handler for filter changes - reset to page 1 when filters change (not page/pageSize)
  const handleFiltersChange = useCallback((newFilters: ImageFilters) => {
    setFilters((prev) => {
      // Check if any filter (except page/pageSize) changed
      const filterChanged = 
        prev.status !== newFilters.status ||
        prev.search !== newFilters.search ||
        JSON.stringify(prev.tags) !== JSON.stringify(newFilters.tags) ||
        prev.group !== newFilters.group ||
        prev.date_from !== newFilters.date_from ||
        prev.date_to !== newFilters.date_to;
      
      const updatedFilters = {
        ...prev,
        ...newFilters,
        page: filterChanged ? 1 : (newFilters.page || prev.page || 1),
        pageSize: newFilters.pageSize || prev.pageSize || DEFAULT_PAGE_SIZE,
      };
      
      if (filterChanged) {
        setCurrentPage(1);
      } else if (updatedFilters.page !== currentPage) {
        setCurrentPage(updatedFilters.page);
      }
      
      return updatedFilters;
    });
  }, [currentPage]);

  // Handler for page change
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    setFilters((prev) => ({
      ...prev,
      page,
    }));
  }, []);

  // Handler for page size change
  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      pageSize: newPageSize,
    }));
  }, []);

  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false);
  const [aiImage, setAiImage] = useState<ImageTask | null>(null);
  const [imageToDelete, setImageToDelete] = useState<{ id: number; title: string } | null>(null);

  const { data: images, isLoading, error, pagination } = useImages(filters, true);
  const deleteImage = useDeleteImage();
  const t = useTranslations('images');
  const tCommon = useTranslations('common');

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

  const handleDeleteClick = useCallback((image: ImageLibraryItem) => {
    setImageToDelete({
      id: image.id,
      title: image.title || t('imageTitle', { id: image.id }),
    });
  }, [t]);

  const handleConfirmDelete = useCallback(async () => {
    if (!imageToDelete) return;
    
    try {
      await deleteImage.mutateAsync(imageToDelete.id);
      setImageToDelete(null);
      // If the deleted image was open in detail dialog, close it
      if (selectedImageId === imageToDelete.id) {
        setIsDetailDialogOpen(false);
        setSelectedImageId(null);
      }
    } catch (error) {
      // Error is handled by the hook (toast notification)
    }
  }, [imageToDelete, deleteImage, selectedImageId]);

  const imagesList = useMemo(() => (images as ImageLibraryItem[]) || [], [images]);
  const isGrouped = useMemo(() => filters.group_by === "job", [filters.group_by]);

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
        onFiltersChange={handleFiltersChange}
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
          title={t('errorLoadingImages')}
          description={error instanceof Error ? error.message : t('unknownError')}
          icon={<ImageIcon className="h-12 w-12 text-muted-foreground" />}
        />
      ) : imagesList.length === 0 ? (
        <EmptyState
          title={t('noImagesInLibrary')}
          description={t('generateFirstImageDescription')}
          icon={<ImageIcon className="h-12 w-12 text-muted-foreground" />}
          action={{
            label: t('generateFirstImage'),
            href: "/generate",
            variant: "default",
          }}
        />
      ) : isGrouped && groupedImages ? (
        // Grouped view (always grid, no list view for grouped)
        <div className="space-y-6">
          {groupedImages.map((group) => (
            <Card key={group.jobId}>
              <CardHeader>
                <CardTitle className="text-lg">
                  {group.dateTag?.name || t('batchGeneratedOn', { date: new Date(group.images[0]?.created_at || "").toLocaleDateString() })}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {t('imagesFromThisBatch', { count: group.images.length })}
                </p>
              </CardHeader>
              <CardContent>
                <GalleryGrid isLoading={false}>
                  {group.images.map((image) => (
                    <ImageCard
                      key={image.id}
                      title={image.title || t('imageTitle', { id: image.id })}
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
                      onDelete={() => handleDeleteClick(image)}
                    />
                  ))}
                </GalleryGrid>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : viewMode === "list" ? (
        // List view
        <div className="space-y-4">
          <ImageList
            images={imagesList}
            isLoading={isLoading}
            onView={handleViewImage}
            onEdit={handleEditImage}
            onGenerateDescription={handleGenerateDescription}
            onDelete={handleDeleteClick}
          />
          {pagination && (
            <Pagination
              currentPage={pagination.currentPage}
              pageSize={pagination.pageSize}
              totalCount={pagination.totalCount}
              totalPages={pagination.totalPages}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          )}
        </div>
      ) : (
        // Grid view
        <div className="space-y-4">
          <GalleryGrid isLoading={false}>
            {imagesList.map((image) => (
              <ImageCard
                key={image.id}
                title={image.title || t('imageTitle', { id: image.id })}
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
                onDelete={() => handleDeleteClick(image)}
              />
            ))}
          </GalleryGrid>
          {pagination && (
            <Pagination
              currentPage={pagination.currentPage}
              pageSize={pagination.pageSize}
              totalCount={pagination.totalCount}
              totalPages={pagination.totalPages}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          )}
        </div>
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!imageToDelete} onOpenChange={(open) => !open && setImageToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('deleteImageConfirm')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('deleteImageConfirmDescription', { title: imageToDelete?.title || '' })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon('cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {t('delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
