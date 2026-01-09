import { 
    apiClient, 
    ConnectionError, 
    HttpError, 
    CancelledError,
    UPLOAD_TIMEOUT 
} from "@/shared/lib/api-client";
import { Job, BackendJob, transformJob } from "../constants/job";
import { env } from "@/shared/lib/env";

const getBaseUrl = () => {
    // Determine if API_BASE_URL already includes '/api'
    const base = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");
    return base.endsWith("/api") ? "/jobs" : "/api/jobs";
};

const BASE_URL = getBaseUrl();

export const createJob = async (formData: FormData): Promise<{ job_id: number; status: string; message: string }> => {
    // NOTE: We use raw fetch here because apiClient sets Content-Type: application/json,
    // which breaks multipart/form-data (browser needs to set boundary).

    const apiUrl = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");
    const fullUrl = `${apiUrl}${BASE_URL}/`;

    // AbortController para timeout (uploads pueden tardar más)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT);

    try {
        const response = await fetch(fullUrl, {
            method: "POST",
            body: formData,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch {
                errorData = await response.text();
            }

            console.error("API Error Response:", errorData);

            let errorMessage = `API Error: ${response.statusText}`;

            if (typeof errorData === 'object' && errorData !== null) {
                const errorObj = errorData as Record<string, unknown>;
                if ('message' in errorObj && typeof errorObj.message === 'string') {
                    errorMessage = errorObj.message;
                } else if ('detail' in errorObj && typeof errorObj.detail === 'string') {
                    errorMessage = errorObj.detail;
                } else {
                    // Flatten field errors, e.g. { source_data: ["Required"] }
                    errorMessage = JSON.stringify(errorData);
                }
            } else if (typeof errorData === 'string') {
                errorMessage = errorData;
            }

            throw new HttpError(errorMessage, response.status, errorData);
        }

        return response.json();
    } catch (error) {
        clearTimeout(timeoutId);

        // Re-throw errores ya tipados
        if (error instanceof HttpError || error instanceof ConnectionError || error instanceof CancelledError) {
            throw error;
        }

        // AbortError = cancelación o timeout (NO es error de conexión)
        if (error instanceof Error && error.name === "AbortError") {
            throw new CancelledError("Upload cancelled or timed out");
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
};

export const getJob = async (jobId: number | string): Promise<Job> => {
    const backendJob = await apiClient.get<BackendJob>(`${BASE_URL}/${jobId}/`);
    return transformJob(backendJob);
};

export const cancelJob = async (jobId: number | string): Promise<{ job_id: number; status: string; message: string }> => {
    const result = await apiClient.post<{ job_id: number; status: string; message: string }>(`${BASE_URL}/${jobId}/cancel/`);
    return result;
};

export const retryImageTask = async (imageTaskId: number | string): Promise<{ image_task_id: number; status: string; message: string; task: unknown }> => {
    // Note: apiClient already prepends NEXT_PUBLIC_API_BASE_URL which includes /api
    const result = await apiClient.post<{ image_task_id: number; status: string; message: string; task: unknown }>(
        `/image-tasks/${imageTaskId}/retry/`
    );
    return result;
};

export const cancelImageTask = async (imageTaskId: number | string): Promise<{ image_task_id: number; status: string; message: string; task: unknown }> => {
    // Note: apiClient already prepends NEXT_PUBLIC_API_BASE_URL which includes /api
    const result = await apiClient.post<{ image_task_id: number; status: string; message: string; task: unknown }>(
        `/image-tasks/${imageTaskId}/cancel/`
    );
    return result;
};
