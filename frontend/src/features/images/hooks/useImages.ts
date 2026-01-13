import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getImages, getImage, updateImageMetadata, publishImage, deleteImage } from "../api/images";
import { ImageFilters, ImageTask, ImageTaskUpdate, ImageLibraryItem, PaginatedImageResponse, PaginationMetadata } from "../types";
import { toast } from "sonner";

/**
 * Hook to fetch images list with filters and pagination
 * Returns images array and pagination metadata
 */
export function useImages(filters?: ImageFilters, library: boolean = false) {
  const queryResult = useQuery({
    queryKey: ["images", filters, library],
    queryFn: () => getImages(filters, library),
    staleTime: 30 * 1000, // 30 seconds
    retry: (failureCount, error) => {
      // Don't retry on 404 - endpoint might not exist yet
      if (error instanceof Error && 'status' in error && (error as { status: number }).status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // Extract pagination metadata from response
  const paginationMetadata: PaginationMetadata | null = React.useMemo(() => {
    if (!queryResult.data) return null;

    // Check if response is paginated
    if (Array.isArray(queryResult.data)) {
      // Non-paginated response
      return null;
    }

    const paginatedResponse = queryResult.data as PaginatedImageResponse<ImageLibraryItem | ImageTask>;
    const pageSize = filters?.pageSize || 20;
    const currentPage = filters?.page || 1;
    const totalCount = paginatedResponse.count || 0;
    const totalPages = Math.ceil(totalCount / pageSize);

    return {
      currentPage,
      pageSize,
      totalCount,
      totalPages,
      hasNext: !!paginatedResponse.next,
      hasPrevious: !!paginatedResponse.previous,
    };
  }, [queryResult.data, filters?.page, filters?.pageSize]);

  // Extract images array from response
  const images: (ImageLibraryItem | ImageTask)[] = React.useMemo(() => {
    if (!queryResult.data) return [];

    if (Array.isArray(queryResult.data)) {
      return queryResult.data;
    }

    const paginatedResponse = queryResult.data as PaginatedImageResponse<ImageLibraryItem | ImageTask>;
    return paginatedResponse.results || [];
  }, [queryResult.data]);

  return {
    ...queryResult,
    data: images,
    pagination: paginationMetadata,
  };
}

/**
 * Hook to fetch single image detail
 */
export function useImageDetail(imageId: number | null) {
  return useQuery({
    queryKey: ["image", imageId],
    queryFn: () => getImage(imageId!),
    enabled: !!imageId,
    staleTime: 30 * 1000,
  });
}

/**
 * Hook to update image metadata
 */
export function useImageUpdate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ imageId, data }: { imageId: number; data: ImageTaskUpdate }) =>
      updateImageMetadata(imageId, data),
    onSuccess: (data, variables) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: ["images"] });
      queryClient.invalidateQueries({ queryKey: ["image", variables.imageId] });
      toast.success("Imagen actualizada exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al actualizar la imagen";
      toast.error(errorMessage);
    },
  });
}

/**
 * Hook to publish or unpublish an image
 */
export function usePublishImage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ imageId, publish }: { imageId: number; publish: boolean }) =>
      publishImage(imageId, publish),
    onSuccess: (data) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: ["images"] });
      queryClient.invalidateQueries({ queryKey: ["image", data.id] });
      toast.success(data.message);
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al publicar/despublicar la imagen";
      toast.error(errorMessage);
    },
  });
}

/**
 * Hook to delete an image
 */
export function useDeleteImage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (imageId: number) => deleteImage(imageId),
    onSuccess: (_, imageId) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: ["images"] });
      queryClient.invalidateQueries({ queryKey: ["image", imageId] });
      toast.success("Imagen eliminada exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al eliminar la imagen";
      toast.error(errorMessage);
    },
  });
}
