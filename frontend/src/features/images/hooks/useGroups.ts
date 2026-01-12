import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getGroups, createGroup, updateGroup, deleteGroup } from "../api/groups";
import { ImageGroup } from "../types";
import { toast } from "sonner";

/**
 * Hook to fetch all groups for current user
 */
export function useGroups() {
  return useQuery({
    queryKey: ["groups"],
    queryFn: getGroups,
    staleTime: 2 * 60 * 1000, // 2 minutes
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
 * Hook to create a new group
 */
export function useCreateGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      toast.success("Grupo creado exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al crear el grupo";
      toast.error(errorMessage);
    },
  });
}

/**
 * Hook to update a group
 */
export function useUpdateGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ groupId, data }: { groupId: number; data: { name?: string; description?: string } }) =>
      updateGroup(groupId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
      toast.success("Grupo actualizado exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al actualizar el grupo";
      toast.error(errorMessage);
    },
  });
}

/**
 * Hook to delete a group
 */
export function useDeleteGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
      toast.success("Grupo eliminado exitosamente");
    },
    onError: (error) => {
      const errorMessage =
        error instanceof Error ? error.message : "Error al eliminar el grupo";
      toast.error(errorMessage);
    },
  });
}
