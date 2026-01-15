import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { generateAIDescription, getDescriptionTask } from "../api/descriptions";
import { getImage } from "../api/images";
import { AIDescriptionRequest, DescriptionTask, DescriptionTaskStatus, DescriptionTaskEvent } from "../types";
import { toast } from "sonner";
import { HttpError, ConnectionError } from "@/shared/lib/api-client";
import { WSClient } from "@/shared/lib/ws";

/**
 * Hook to generate AI description with WebSocket real-time updates and polling fallback
 */
export function useAIDescription() {
  const queryClient = useQueryClient();
  const [pollingTaskId, setPollingTaskId] = useState<number | null>(null);
  const [lastStatus, setLastStatus] = useState<DescriptionTaskStatus | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);
  const [realTimeEvents, setRealTimeEvents] = useState<DescriptionTaskEvent[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [modelAttempts, setModelAttempts] = useState<Array<{ model: string; status: 'attempting' | 'failed' | 'success'; error?: string }>>([]);
  const wsRef = useRef<WSClient | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Reset function to clear current task and allow new generation
  const reset = useCallback(() => {
    setPollingTaskId(null);
    setLastStatus(null);
    setJobId(null);
    setRealTimeEvents([]);
    setCurrentModel(null);
    setModelAttempts([]);
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
    queryClient.removeQueries({ queryKey: ["description-task"] });
  }, [queryClient]);

  // Poll description task status (fallback if WebSocket fails)
  // Keep query enabled even after polling stops to maintain data
  const { data: descriptionTask } = useQuery({
    queryKey: ["description-task", pollingTaskId],
    queryFn: () => getDescriptionTask(pollingTaskId!),
    enabled: !!pollingTaskId, // Only fetch when we have a task ID
    refetchInterval: (query) => {
      const task = query.state.data as DescriptionTask | undefined;
      if (!task) return 2000; // Poll every 2 seconds if no data yet
      
      // Stop polling if task is in final state
      if (task.status === "SUCCESS" || task.status === "FAILED" || task.status === "CANCELLED") {
        // For SUCCESS, do one more refetch to get model_used if not present
        if (task.status === "SUCCESS" && !task.model_used) {
          // Schedule a refetch after backend has time to save
          setTimeout(() => {
            queryClient.refetchQueries({ queryKey: ["description-task", pollingTaskId] });
          }, 1500);
          // Continue polling one more time to get the updated data
          return 2000;
        }
        // For other final states or if we already have model_used, stop polling
        return false;
      }
      
      // Poll less frequently if WebSocket is connected (fallback only)
      return 2000; // Continue polling every 2 seconds as fallback
    },
    staleTime: 0, // Always refetch
    // Keep data in cache even after query is disabled
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!jobId || !pollingTaskId) {
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }
      return;
    }

    // Small delay to prevent double-connect
    connectionTimeoutRef.current = setTimeout(() => {
      const ws = new WSClient(`jobs/${jobId}/`, {
        onOpen: () => {
          // WebSocket connected
        },
        onMessage: (data: unknown) => {
          if (!data || typeof data !== "object" || !("event_type" in data)) {
            return;
          }

          const event = data as any; // Event from WebSocket
          
          // Only process events related to this description task
          // Events have entity_type and entity_id, or description_task_id in payload
          const isDescriptionTaskEvent = 
            event.entity_type === 'description_task' && 
            event.entity_id === pollingTaskId;
          
          const eventDescriptionTaskId = (event.payload as any)?.description_task_id;
          const matchesDescriptionTask = eventDescriptionTaskId === pollingTaskId;
          
          // Also check if job_id matches (all events from the job are sent, but we filter by description_task)
          if (!isDescriptionTaskEvent && !matchesDescriptionTask) {
            // Not for this description task - skip
            return;
          }

          // Add event to real-time events list
          setRealTimeEvents((prev) => {
            // Avoid duplicates based on trace_id and created_at
            const exists = prev.some(
              (e) => e.payload?.trace_id === event.payload?.trace_id &&
                     e.created_at === event.created_at
            );
            if (exists) return prev;
            return [...prev, event];
          });

          // Process specific event types for UI feedback
          if (event.event_type === "MODEL_ATTEMPT" && event.payload?.model) {
            const model = event.payload.model as string;
            setCurrentModel(model);
            setModelAttempts((prev) => {
              // Remove any existing "attempting" status for this model
              const filtered = prev.filter((m) => !(m.model === model && m.status === "attempting"));
              return [...filtered, { model, status: "attempting" as const }];
            });
            toast.info(`Intentando modelo: ${model}`, { duration: 2000 });
          } else if (event.event_type === "MODEL_FAILED" && event.payload?.model) {
            const model = event.payload.model as string;
            const error = event.payload.error as string || "Error desconocido";
            setModelAttempts((prev) => {
              const filtered = prev.filter((m) => m.model !== model || m.status !== "attempting");
              return [...filtered, { model, status: "failed" as const, error }];
            });
            toast.warning(`Modelo ${model} falló: ${error}`, { duration: 3000 });
          } else if (event.event_type === "MODEL_SUCCESS" && event.payload?.model) {
            const model = event.payload.model as string;
            setCurrentModel(model);
            setModelAttempts((prev) => {
              const filtered = prev.filter((m) => m.model !== model);
              return [...filtered, { model, status: "success" as const }];
            });
          } else if (event.event_type === "FALLBACK" && event.payload?.from_model && event.payload?.to_model) {
            const fromModel = event.payload.from_model as string;
            const toModel = event.payload.to_model as string;
            toast.info(`Cambiando de ${fromModel} a ${toModel}`, { duration: 2000 });
          } else if (event.event_type === "PROGRESS" && event.payload?.model) {
            setCurrentModel(event.payload.model as string);
          } else if (event.event_type === "DONE") {
            setCurrentModel(null);
            // Extract model from event payload if available
            const modelFromEvent = event.payload?.model as string | undefined;
            if (modelFromEvent) {
              console.log("DONE event received with model:", modelFromEvent);
            }
            // Invalidate queries to get latest data with model_used
            queryClient.invalidateQueries({ queryKey: ["description-task", pollingTaskId] });
            queryClient.invalidateQueries({ queryKey: ["images"] });
          } else if (event.event_type === "AI_PROVIDER_ERROR" || event.event_type === "ERROR") {
            const errorMsg = event.message || "Error al generar la descripción";
            toast.error(errorMsg);
          }
        },
        onError: (err) => {
          console.error("WebSocket error for description task:", err);
          // Fallback to polling - it's already enabled
        },
        onClose: () => {
          // WebSocket closed - polling will continue as fallback
        },
      });

      wsRef.current = ws;
      ws.connect();
    }, 100);

    return () => {
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }
    };
  }, [jobId, pollingTaskId, queryClient]);

  // Track status changes and show toasts
  useEffect(() => {
    if (!descriptionTask) return;

    const currentStatus = descriptionTask.status;
    
    // Only show toast on status change
    if (lastStatus !== currentStatus) {
      if (currentStatus === "RUNNING") {
        toast.info("Generando descripción con IA...", { duration: 2000 });
      } else if (currentStatus === "SUCCESS") {
        // Invalidate queries to get the latest data including model_used
        queryClient.invalidateQueries({ queryKey: ["description-task", pollingTaskId] });
        queryClient.invalidateQueries({ queryKey: ["images"] });
        queryClient.invalidateQueries({ queryKey: ["image", descriptionTask.image_task] });
        
        // Show toast with available info
        const provider = descriptionTask.provider_used || "proveedor automático";
        const model = descriptionTask.model_used;
        if (model) {
          toast.success(`Descripción generada exitosamente con ${provider} (${model})`);
        } else {
          // Model not yet available, show generic message
          toast.success(`Descripción generada exitosamente con ${provider}`);
          // Schedule another refetch after a delay to get model_used
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["description-task", pollingTaskId] });
          }, 1500);
        }
        
        // Stop polling after ensuring we've had time to refetch
        setTimeout(() => {
          setPollingTaskId(null);
        }, 2500);
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
    mutationFn: async (data: AIDescriptionRequest) => {
      const response = await generateAIDescription(data);
      // If job_id is not in response, get it from image (fallback)
      if (!response.job_id) {
        const image = await getImage(data.image_task_id);
        return { ...response, job_id: image.job };
      }
      return response;
    },
    onSuccess: (response) => {
      // Start polling the description task
      setPollingTaskId(response.description_task_id);
      setJobId(response.job_id);
      setLastStatus("PENDING");
      setRealTimeEvents([]);
      setCurrentModel(null);
      setModelAttempts([]);
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

  // Calculate isGenerating: true only if actively generating (not failed or cancelled)
  const isGenerating = generateMutation.isPending || 
    (pollingTaskId !== null && 
     descriptionTask?.status !== "SUCCESS" && 
     descriptionTask?.status !== "FAILED" && 
     descriptionTask?.status !== "CANCELLED");

  return {
    generateDescription,
    descriptionTask,
    isGenerating,
    progress: descriptionTask?.progress ?? 0,
    error: generateMutation.error,
    reset,
    // Real-time feedback
    realTimeEvents,
    currentModel,
    modelAttempts,
  };
}
