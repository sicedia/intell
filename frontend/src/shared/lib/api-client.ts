import { env } from "./env";

export interface ApiError {
  message: string;
  status: number;
  data?: unknown;
}

export class ApiClientError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.data = data;
  }
}

async function fetchJSON<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${env.NEXT_PUBLIC_API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  // Read response as text first (can only be read once)
  const text = await response.text();
  
  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = text ? JSON.parse(text) : `Error ${response.status}: ${response.statusText}`;
    } catch {
      errorData = text || `Error ${response.status}: ${response.statusText}`;
    }

    throw new ApiClientError(
      `API Error: ${response.statusText}`,
      response.status,
      errorData
    );
  }

  // If response is OK but empty, return empty object
  if (!text || text.trim() === "") {
    return {} as T;
  }

  // Try to parse as JSON
  try {
    const parsed = JSON.parse(text);
    return parsed as T;
  } catch (parseError) {
    // If JSON parsing fails but response is OK, return empty object
    console.warn("Failed to parse JSON response:", parseError);
    return {} as T;
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    fetchJSON<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchJSON<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    fetchJSON<T>(endpoint, { ...options, method: "DELETE" }),
};
