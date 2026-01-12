import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { generateAIDescription, getDescriptionTask } from "../api/descriptions";
import { AIDescriptionRequest, DescriptionTask, DescriptionTaskStatus } from "../types";
import { toast } from "sonner";
import { HttpError, ConnectionError } from "@/shared/lib/api-client";

/**
 * Hook to generate AI description with polling and error handling
 */
export function useAIDescription() {
  const queryClient = useQueryClient();
  const [pollingTaskId, setPollingTaskId] = useState<number | null>(null);
  const [lastStatus, setLastStatus] = useState<DescriptionTaskStatus | null>(null);

  // Reset function to clear current task and allow new generation
  const reset = useCallback(() => {
    setPollingTaskId(null);
    setLastStatus(null);
    queryClient.removeQueries({ queryKey: ["description-task"] });
  }, [queryClient]);

  // Poll description task status
  const { data: descriptionTask } = useQuery({
    queryKey: ["description-task", pollingTaskId],
    queryFn: () => getDescriptionTask(pollingTaskId!),
    enabled: !!pollingTaskId,
    refetchInterval: (query) => {
      const task = query.state.data as DescriptionTask | undefined;
      if (!task) return 1000; // Poll every 1 second if no data yet
      
      // Stop polling if task is in final state
      if (task.status === "SUCCESS" || task.status === "FAILED" || task.status === "CANCELLED") {
        return false;
      }
      
      return 1000; // Continue polling every 1 second
    },
    staleTime: 0, // Always refetch
  });

  // Track status changes and show toasts
  useEffect(() => {
    if (!descriptionTask) return;

    const currentStatus = descriptionTask.status;
    
    // Only show toast on status change
    if (lastStatus !== currentStatus) {
      if (currentStatus === "RUNNING") {
        toast.info("Generando descripción con IA...", { duration: 2000 });
      } else if (currentStatus === "SUCCESS") {
        const provider = descriptionTask.provider_used || "proveedor automático";
        toast.success(`Descripción generada exitosamente con ${provider}`);
        setPollingTaskId(null); // Stop polling
        // Invalidate image queries to refresh data
        queryClient.invalidateQueries({ queryKey: ["images"] });
        queryClient.invalidateQueries({ queryKey: ["image", descriptionTask.image_task] });
      } else if (currentStatus === "FAILED") {
        const errorMsg = descriptionTask.error_message || "Error al generar la descripción";
        // Check if it's a provider fallback scenario
        if (errorMsg.includes("provider") || errorMsg.includes("fallback")) {
          toast.warning("Proveedor principal no disponible, intentando con alternativa...", { duration: 3000 });
        } else {
          toast.error(errorMsg);
          setPollingTaskId(null); // Stop polling only on final failure
        }
      }
      
      setLastStatus(currentStatus);
    }
  }, [descriptionTask, lastStatus, queryClient]);

  // Mutation to generate description
  const generateMutation = useMutation({
    mutationFn: (data: AIDescriptionRequest) => generateAIDescription(data),
    onSuccess: (response) => {
      // Start polling the description task
      setPollingTaskId(response.description_task_id);
      setLastStatus("PENDING");
      toast.info("Solicitud de descripción creada", { duration: 2000 });
    },
    onError: (error) => {
      let errorMessage = "Error al generar la descripción";
      
      if (error instanceof HttpError) {
        if (error.status === 400) {
          errorMessage = "Error en la solicitud. Verifica los datos proporcionados.";
        } else if (error.status === 404) {
          errorMessage = "Imagen no encontrada";
        } else if (error.status >= 500) {
          errorMessage = "Error del servidor. Por favor, intenta de nuevo.";
        } else {
          errorMessage = error.message;
        }
      } else if (error instanceof ConnectionError) {
        errorMessage = "No se puede conectar al servidor. Verifica tu conexión.";
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    },
  });

  const generateDescription = useCallback(
    (data: AIDescriptionRequest) => {
      generateMutation.mutate(data);
    },
    [generateMutation]
  );

  return {
    generateDescription,
    descriptionTask,
    isGenerating: generateMutation.isPending || (pollingTaskId !== null && descriptionTask?.status !== "SUCCESS" && descriptionTask?.status !== "FAILED"),
    progress: descriptionTask?.progress ?? 0,
    error: generateMutation.error,
    reset,
  };
}
