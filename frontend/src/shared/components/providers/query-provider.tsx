"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { 
  isConnectionError, 
  isCancelledError,
  ApiError,
  HttpError,
} from "@/shared/lib/api-client";
import { useConnectionStore } from "@/shared/store/connection-store";

// ============================================================================
// Retry Logic
// ============================================================================

/**
 * Lógica de retry inteligente para queries
 * - ConnectionError: 2 reintentos rápidos
 * - 500+: 1 reintento
 * - 400/401/403/404: no reintentar
 * - CancelledError: no reintentar
 */
function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  // Cancelaciones: nunca reintentar
  if (isCancelledError(error)) {
    return false;
  }

  // Errores de conexión: hasta 2 reintentos
  if (isConnectionError(error)) {
    return failureCount < 2;
  }

  // Errores HTTP
  if (error instanceof HttpError || error instanceof ApiError) {
    const status = error.status;
    
    // Server errors (500+): 1 reintento
    if (status >= 500) {
      return failureCount < 1;
    }
    
    // Client errors: no reintentar
    // 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
    if (status >= 400 && status < 500) {
      return false;
    }
  }

  // Default: no reintentar errores desconocidos
  return false;
}

/**
 * Lógica de retry más conservadora para mutations
 * - Solo ConnectionError: 1 reintento (puede duplicar operaciones no idempotentes)
 * - Resto: no reintentar
 */
function shouldRetryMutation(failureCount: number, error: unknown): boolean {
  // Cancelaciones: nunca reintentar
  if (isCancelledError(error)) {
    return false;
  }

  // Solo reintentar errores de conexión, y solo 1 vez
  // NOTA: Esto puede duplicar operaciones si el backend ejecutó pero la respuesta se perdió
  // Para operaciones críticas no idempotentes, considera retry: false
  if (isConnectionError(error)) {
    return failureCount < 1;
  }

  // Mutations: no reintentar otros errores
  return false;
}

// ============================================================================
// Error Handling
// ============================================================================

/** ID único para toast de conexión (evita duplicados) */
const CONNECTION_ERROR_TOAST_ID = "connection-error";

/**
 * Maneja errores globalmente
 * - Errores de conexión: actualiza store + toast único
 * - Otros errores: solo logging
 */
function handleGlobalError(error: unknown, context: "query" | "mutation") {
  // Ignorar cancelaciones
  if (isCancelledError(error)) {
    return;
  }

  // Usar getState() dentro del handler (más robusto que snapshot al cargar módulo)
  const { setConnectionError } = useConnectionStore.getState();

  if (isConnectionError(error)) {
    setConnectionError(error instanceof Error ? error : new Error(String(error)));
    
    // Toast único con dedupe (sonner usa el ID para no duplicar)
    toast.error("Sin conexión con el servidor", {
      id: CONNECTION_ERROR_TOAST_ID,
      description: "Verifica tu conexión o que el servidor esté funcionando",
      duration: 5000,
    });
  } else {
    // Logging para otros errores (opcional: enviar a Sentry si existe)
    console.error(`[${context}] Error:`, error);
  }
}

/**
 * Maneja éxitos globalmente
 * - Marca conexión como activa (oculta banner si estaba visible)
 */
function handleGlobalSuccess() {
  // Usar getState() dentro del handler
  const { setConnected } = useConnectionStore.getState();
  setConnected();
}

// ============================================================================
// Query Client Factory
// ============================================================================

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minuto
        refetchOnWindowFocus: false,
        retry: shouldRetryQuery,
        // Retry delay: exponencial con máximo de 10s
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
      },
      mutations: {
        retry: shouldRetryMutation,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
      },
    },
  });
}

// ============================================================================
// Provider Component
// ============================================================================

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Usar useRef para mantener la misma instancia de QueryClient
  const queryClientRef = useRef<QueryClient | null>(null);
  
  if (!queryClientRef.current) {
    queryClientRef.current = createQueryClient();
  }
  
  const queryClient = queryClientRef.current;

  // Setup global handlers con useEffect (correcto para side effects)
  useEffect(() => {
    const cache = queryClient.getQueryCache();
    const mutationCache = queryClient.getMutationCache();

    // Subscribe to query events
    const unsubscribeQueries = cache.subscribe((event) => {
      if (event.type === "updated") {
        const query = event.query;
        if (query.state.status === "error") {
          handleGlobalError(query.state.error, "query");
        } else if (query.state.status === "success") {
          handleGlobalSuccess();
        }
      }
    });

    // Subscribe to mutation events
    const unsubscribeMutations = mutationCache.subscribe((event) => {
      if (event.type === "updated") {
        const mutation = event.mutation;
        if (mutation?.state.status === "error") {
          handleGlobalError(mutation.state.error, "mutation");
        } else if (mutation?.state.status === "success") {
          handleGlobalSuccess();
        }
      }
    });

    // Cleanup subscriptions on unmount
    return () => {
      unsubscribeQueries();
      unsubscribeMutations();
    };
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV !== "production" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
