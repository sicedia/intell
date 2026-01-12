import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getImages, getImage, updateImageMetadata, publishImage } from "../api/images";
import { ImageFilters, ImageTask, ImageTaskUpdate, ImageLibraryItem } from "../types";
import { toast } from "sonner";

/**
 * Hook to fetch images list with filters
 */
export function useImages(filters?: ImageFilters, library: boolean = false) {
  return useQuery({
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
