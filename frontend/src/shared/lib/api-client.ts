import { env } from "./env";

// ============================================================================
// Error Types - Jerarquía de errores tipados
// ============================================================================

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    // Fix para instanceof en JavaScript transpilado
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Error de conexión: red/DNS/CORS/servidor inaccesible
 * status = 0 indica error de red
 */
export class ConnectionError extends ApiError {
  constructor(message: string, originalError?: unknown) {
    super(message, 0, { originalError });
    this.name = "ConnectionError";
    Object.setPrototypeOf(this, ConnectionError.prototype);
  }
}

/**
 * Error HTTP: respuesta del servidor con status de error
 */
export class HttpError extends ApiError {
  constructor(message: string, status: number, data?: unknown) {
    super(message, status, data);
    this.name = "HttpError";
    Object.setPrototypeOf(this, HttpError.prototype);
  }
}

/**
 * Error de cancelación: request abortado intencionalmente
 * status = -1 para diferenciarlo de errores de conexión
 */
export class CancelledError extends ApiError {
  constructor(message: string = "Request cancelled") {
    super(message, -1);
    this.name = "CancelledError";
    Object.setPrototypeOf(this, CancelledError.prototype);
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Verifica si el error es un error de conexión (red/servidor inaccesible)
 * Excluye explícitamente CancelledError y status -1
 */
export function isConnectionError(error: unknown): boolean {
  if (error instanceof CancelledError) {
    return false;
  }
  if (error instanceof ConnectionError) {
    return true;
  }
  if (error instanceof ApiError) {
    // status 0 = error de red, pero no -1 (cancelado)
    return error.status === 0;
  }
  return false;
}

/**
 * Verifica si el error es una cancelación intencional
 */
export function isCancelledError(error: unknown): boolean {
  return error instanceof CancelledError || 
         (error instanceof ApiError && error.status === -1);
}

/**
 * Obtiene un mensaje de error amigable para el usuario
 */
export function getConnectionErrorMessage(error: unknown): string {
  if (isConnectionError(error)) {
    return "No se puede conectar al servidor. Verifica tu conexión o que el servidor esté funcionando.";
  }
  if (isCancelledError(error)) {
    return "La solicitud fue cancelada";
  }
  if (error instanceof ApiError) {
    // Intentar extraer mensaje del data si existe
    if (error.data && typeof error.data === "object") {
      const data = error.data as Record<string, unknown>;
      if (typeof data.message === "string") return data.message;
      if (typeof data.detail === "string") return data.detail;
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Ha ocurrido un error inesperado";
}

// ============================================================================
// Default Timeout (configurable por tipo de request)
// ============================================================================

const DEFAULT_TIMEOUT = 15000; // 15s para requests normales
const UPLOAD_TIMEOUT = 60000; // 60s para uploads

// ============================================================================
// Fetch JSON - Pipeline simple sin interceptores complejos
// ============================================================================

async function fetchJSON<T>(
  endpoint: string,
  options?: RequestInit & { timeout?: number }
): Promise<T> {
  const url = `${env.NEXT_PUBLIC_API_BASE_URL}${endpoint}`;
  const timeout = options?.timeout ?? DEFAULT_TIMEOUT;
  
  // AbortController para timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    // Manejo de respuestas vacías (204 No Content, etc.)
    if (response.status === 204 || response.headers.get("content-length") === "0") {
      if (!response.ok) {
        throw new HttpError(`HTTP ${response.status}: ${response.statusText}`, response.status);
      }
      return {} as T;
    }

    // Leer body como texto primero (solo se puede leer una vez)
    const text = await response.text();

    if (!response.ok) {
      // Intentar parsear error como JSON
      let errorData: unknown;
      try {
        errorData = text ? JSON.parse(text) : { message: `Error ${response.status}: ${response.statusText}` };
      } catch {
        errorData = { message: text || `Error ${response.status}: ${response.statusText}` };
      }

      throw new HttpError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    // Body vacío pero status OK
    if (!text || text.trim() === "") {
      return {} as T;
    }

    // Parsear JSON con fallback seguro
    try {
      return JSON.parse(text) as T;
    } catch (parseError) {
      console.warn("Failed to parse JSON response:", parseError);
      // Si no es JSON pero response.ok, retornar objeto vacío
      return {} as T;
    }
  } catch (error) {
    clearTimeout(timeoutId);

    // Re-throw errores ya tipados
    if (error instanceof ApiError) {
      throw error;
    }

    // AbortError = cancelación intencional (NO es error de conexión)
    if (error instanceof Error && error.name === "AbortError") {
      throw new CancelledError("Request cancelled or timed out");
    }

    // TypeError/DOMException = red/DNS/CORS/servidor inaccesible
    if (error instanceof TypeError || error instanceof DOMException) {
      throw new ConnectionError(
        "No se puede conectar al servidor",
        error instanceof Error ? error.message : error
      );
    }

    // Error desconocido
    throw error;
  }
}

// ============================================================================
// API Client - Métodos HTTP
// ============================================================================

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit & { timeout?: number }) =>
    fetchJSON<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestInit & { timeout?: number }) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestInit & { timeout?: number }) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit & { timeout?: number }) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestInit & { timeout?: number }) =>
    fetchJSON<T>(endpoint, { ...options, method: "DELETE" }),
};

// ============================================================================
// Exports adicionales para uso externo
// ============================================================================

export { DEFAULT_TIMEOUT, UPLOAD_TIMEOUT };
