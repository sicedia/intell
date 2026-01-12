import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTags, createTag } from "../api/tags";
import { Tag } from "../types";
import { toast } from "sonner";

/**
 * Hook to fetch all tags
 */
export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: getTags,
    staleTime: 5 * 60 * 1000, // 5 minutes
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
 * Hook to create a new tag
 */
export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTag,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      toast.success("Tag creado exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al crear el tag";
      toast.error(errorMessage);
    },
  });
}
