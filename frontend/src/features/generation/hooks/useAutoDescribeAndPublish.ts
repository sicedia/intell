import { useEffect, useState, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { generateAIDescription, getDescriptionTask } from "@/features/images/api/descriptions";
import { publishImage, updateImageMetadata } from "@/features/images/api/images";
import { ImageTask, JobStatus } from "../constants/job";
import { AIDescriptionRequest, DescriptionTask } from "@/features/images/types";
import { toast } from "sonner";

/**
 * Generate automatic context for AI description based on algorithm and job info
 */
function generateAutoContext(task: ImageTask, jobSourceType?: string): string {
  const algorithmName = task.algorithm_key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  const sourceInfo = jobSourceType === "lens" 
    ? "datos de patentes obtenidos desde Lens API"
    : jobSourceType === "espacenet_excel"
    ? "datos de patentes obtenidos desde un archivo Excel de Espacenet"
    : "datos de patentes";

  return `Este gráfico muestra visualizaciones de ${sourceInfo} utilizando el algoritmo ${algorithmName}. El gráfico representa análisis de tendencias, evolución o distribución de patentes según el tipo de visualización seleccionada. Los datos han sido procesados y visualizados para facilitar la comprensión de patrones y tendencias en el campo de las patentes.`;
}

/**
 * Hook to automatically describe and publish images when they complete
 */
export function useAutoDescribeAndPublish(
  task: ImageTask,
  enabled: boolean,
  jobSourceType?: string,
  jobId?: number
) {
  const queryClient = useQueryClient();
  const [descriptionTaskId, setDescriptionTaskId] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const hasProcessedRef = useRef(false); // Prevent duplicate processing

  // Poll description task status
  const { data: descriptionTask } = useQuery({
    queryKey: ["description-task", descriptionTaskId],
    queryFn: () => getDescriptionTask(descriptionTaskId!),
    enabled: !!descriptionTaskId,
    refetchInterval: (query) => {
      const task = query.state.data as DescriptionTask | undefined;
      if (!task) return 1000;
      
      if (task.status === "SUCCESS" || task.status === "FAILED" || task.status === "CANCELLED") {
        return false;
      }
      
      return 1000;
    },
    staleTime: 0,
  });

  // Reset processing flag when task changes or auto mode is disabled
  useEffect(() => {
    if (!enabled || task.status !== JobStatus.SUCCESS || task.is_published) {
      hasProcessedRef.current = false;
    }
  }, [enabled, task.status, task.id, task.is_published]);

  // Auto-generate description when image completes and auto mode is enabled
  useEffect(() => {
    if (
      !enabled ||
      task.status !== JobStatus.SUCCESS ||
      isProcessing ||
      descriptionTaskId !== null ||
      task.is_published ||
      hasProcessedRef.current
    ) {
      return;
    }

    const triggerAutoDescription = async () => {
      setIsProcessing(true);
      
      try {
        const autoContext = generateAutoContext(task, jobSourceType);
        
        const request: AIDescriptionRequest = {
          image_task_id: task.id,
          user_context: autoContext,
          provider_preference: undefined, // Use automatic provider selection
        };

        const response = await generateAIDescription(request);
        setDescriptionTaskId(response.description_task_id);
        toast.info("Generando descripción automática con IA...", { duration: 2000 });
      } catch (error) {
        console.error("Failed to auto-generate description:", error);
        toast.error("Error al generar descripción automática");
        setIsProcessing(false);
        hasProcessedRef.current = false; // Reset on error
      }
    };

    triggerAutoDescription();
  }, [enabled, task.status, task.id, task.is_published, jobSourceType, isProcessing, descriptionTaskId]);

  // Auto-save description and publish when description completes successfully
  useEffect(() => {
    if (
      !enabled ||
      !descriptionTask ||
      descriptionTask.status !== "SUCCESS" ||
      task.is_published ||
      !descriptionTask.result_text ||
      hasProcessedRef.current // Prevent duplicate processing
    ) {
      return;
    }

    const saveAndPublishAutomatically = async () => {
      // Mark as processing to prevent duplicate calls
      hasProcessedRef.current = true;
      
      try {
        // Step 1: Save the description to the image's user_description field
        // Use API directly to avoid duplicate toast notifications
        await updateImageMetadata(task.id, {
          user_description: descriptionTask.result_text ?? undefined,
        });
        
        // Step 2: Publish the image automatically
        await publishImage(task.id, true);
        
        toast.success("Descripción generada, guardada y publicada automáticamente", {
          duration: 3000,
        });
        
        // Invalidate queries to refresh UI
        if (jobId) {
          await queryClient.invalidateQueries({ queryKey: ["job", jobId] });
        }
        await queryClient.invalidateQueries({ queryKey: ["images"] });
        await queryClient.invalidateQueries({ queryKey: ["image", task.id] });
        await queryClient.invalidateQueries({ queryKey: ["description-task", descriptionTaskId] });
        
        setIsProcessing(false);
        setDescriptionTaskId(null);
      } catch (error) {
        console.error("Failed to auto-save and publish:", error);
        toast.error("Error al guardar descripción o publicar automáticamente");
        setIsProcessing(false);
        hasProcessedRef.current = false; // Reset on error to allow retry
      }
    };

    saveAndPublishAutomatically();
  }, [enabled, descriptionTask, task.id, task.is_published, jobId, queryClient, descriptionTaskId]);

  return {
    isProcessing,
    descriptionTask,
    descriptionProgress: descriptionTask?.progress ?? 0,
  };
}
