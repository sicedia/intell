"use client";

import { WifiOff, X, RefreshCw } from "lucide-react";
import { useConnectionStore, selectIsDisconnected } from "@/shared/store/connection-store";
import { cn } from "@/shared/lib/utils";
import { env } from "@/shared/lib/env";
import { useState } from "react";

/**
 * Banner global que muestra estado de desconexión con el servidor
 * 
 * Se muestra automáticamente cuando:
 * - isConnected === false (error de conexión detectado)
 * 
 * Se oculta cuando:
 * - isConnected === true (request exitoso)
 * - isConnected === null (estado desconocido / usuario cerró banner)
 */
export function ConnectionBanner() {
  const isDisconnected = useConnectionStore(selectIsDisconnected);
  const clearError = useConnectionStore((state) => state.clearError);
  const [isRetrying, setIsRetrying] = useState(false);

  // No mostrar si está conectado o estado desconocido
  if (!isDisconnected) {
    return null;
  }

  const handleRetry = async () => {
    setIsRetrying(true);
    
    // Intentar un health check manual
    try {
      const response = await fetch(
        `${env.NEXT_PUBLIC_API_BASE_URL}/health/`,
        { method: "GET" }
      );
      
      if (response.ok) {
        // Conexión restaurada
        useConnectionStore.getState().setConnected();
      }
    } catch {
      // Sigue sin conexión - el banner permanece
    } finally {
      setIsRetrying(false);
    }
  };

  const handleDismiss = () => {
    // Resetea a estado desconocido (oculta el banner)
    clearError();
  };

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        "fixed top-0 left-0 right-0 z-50",
        "bg-red-600 text-white",
        "px-4 py-3",
        "shadow-lg",
        "animate-in slide-in-from-top duration-300"
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Icono y mensaje */}
        <div className="flex items-center gap-3">
          <WifiOff className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
            <span className="font-medium">Sin conexión con el servidor</span>
            <span className="text-red-100 text-sm hidden sm:inline">
              Verifica tu conexión o que el servidor esté funcionando
            </span>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex items-center gap-2">
          {/* Botón reintentar */}
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium",
              "bg-red-700 hover:bg-red-800 transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-red-600"
            )}
            aria-label="Reintentar conexión"
          >
            <RefreshCw
              className={cn("h-4 w-4", isRetrying && "animate-spin")}
              aria-hidden="true"
            />
            <span className="hidden sm:inline">
              {isRetrying ? "Verificando..." : "Reintentar"}
            </span>
          </button>

          {/* Botón cerrar */}
          <button
            onClick={handleDismiss}
            className={cn(
              "p-1.5 rounded-md",
              "hover:bg-red-700 transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-red-600"
            )}
            aria-label="Cerrar notificación"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
