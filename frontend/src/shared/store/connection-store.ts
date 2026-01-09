import { create } from "zustand";

// ============================================================================
// Types
// ============================================================================

interface ConnectionState {
  /**
   * Estado de conexión:
   * - null: desconocido (inicial o después de clearError)
   * - true: conectado (último request exitoso)
   * - false: desconectado (error de conexión detectado)
   */
  isConnected: boolean | null;
  
  /** Último error de conexión (para debugging/logging) */
  lastError: Error | null;
  
  /** Timestamp del último error (para dedupe) */
  lastErrorTime: number;
  
  /** Marca estado como desconectado con error */
  setConnectionError: (error: Error) => void;
  
  /** Marca estado como conectado (llamar en success) */
  setConnected: () => void;
  
  /** Limpia error y resetea estado a desconocido (cierra banner) */
  clearError: () => void;
}

// ============================================================================
// Constants
// ============================================================================

/** Tiempo mínimo entre actualizaciones de error para evitar spam */
const ERROR_DEDUPE_MS = 3000; // 3 segundos

// ============================================================================
// Store
// ============================================================================

export const useConnectionStore = create<ConnectionState>((set, get) => ({
  isConnected: null,
  lastError: null,
  lastErrorTime: 0,

  setConnectionError: (error: Error) => {
    const now = Date.now();
    const state = get();
    
    // Dedupe: solo actualizar si pasó suficiente tiempo desde el último error
    if (now - state.lastErrorTime > ERROR_DEDUPE_MS) {
      set({
        isConnected: false,
        lastError: error,
        lastErrorTime: now,
      });
    }
  },

  setConnected: () => {
    const state = get();
    // Solo actualizar si no estaba conectado (evitar re-renders innecesarios)
    if (state.isConnected !== true) {
      set({
        isConnected: true,
        lastError: null,
        // No reseteamos lastErrorTime para mantener el dedupe
      });
    }
  },

  clearError: () => {
    // Resetear a estado "desconocido" - esto oculta el banner
    set({
      isConnected: null,
      lastError: null,
    });
  },
}));

// ============================================================================
// Selectors (para uso optimizado en componentes)
// ============================================================================

/** Selector: ¿está desconectado? (para mostrar banner) */
export const selectIsDisconnected = (state: ConnectionState) => 
  state.isConnected === false;

/** Selector: último error */
export const selectLastError = (state: ConnectionState) => 
  state.lastError;
