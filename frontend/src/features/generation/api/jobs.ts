import { 
    apiClient, 
    ConnectionError, 
    HttpError, 
    CancelledError,
    UPLOAD_TIMEOUT 
} from "@/shared/lib/api-client";
import { getCsrfToken } from "@/shared/lib/csrf";
import { Job, BackendJob, transformJob } from "../constants/job";
import { env } from "@/shared/lib/env";
import { createLogger } from "@/shared/lib/logger";

const log = createLogger("JobsAPI");

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

    // Get CSRF token for POST request
    const csrfToken = getCsrfToken();
    const headers: HeadersInit = {};
    if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
    }

    try {
        const response = await fetch(fullUrl, {
            method: "POST",
            body: formData,
            signal: controller.signal,
            credentials: "include", // Send cookies (sessionid, csrftoken)
            headers,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch {
                errorData = await response.text();
            }

            log.error("API Error Response:", errorData);

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

/**
 * Retry all failed image tasks for a job
 * @returns Array of results for each retry attempt
 */
export const retryAllFailedTasks = async (
    failedTaskIds: number[]
): Promise<{ successes: number; failures: number }> => {
    let successes = 0;
    let failures = 0;
    
    // Execute retries in parallel for better performance
    const results = await Promise.allSettled(
        failedTaskIds.map(id => retryImageTask(id))
    );
    
    results.forEach(result => {
        if (result.status === "fulfilled") {
            successes++;
        } else {
            failures++;
        }
    });
    
    return { successes, failures };
};

export const cancelImageTask = async (imageTaskId: number | string): Promise<{ image_task_id: number; status: string; message: string; task: unknown }> => {
    // Note: apiClient already prepends NEXT_PUBLIC_API_BASE_URL which includes /api
    const result = await apiClient.post<{ image_task_id: number; status: string; message: string; task: unknown }>(
        `/image-tasks/${imageTaskId}/cancel/`
    );
    return result;
};

export type ZipFormat = "both" | "png" | "svg";

/**
 * Download all successful job images as a ZIP file.
 * 
 * @param jobId - The job ID
 * @param format - Format to include: "both" (PNG + SVG), "png", or "svg"
 */
export const downloadJobZip = async (
    jobId: number | string,
    format: ZipFormat = "both"
): Promise<void> => {
    const apiUrl = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");
    // Use 'image_format' param (not 'format' to avoid conflict with DRF's format negotiation)
    const url = `${apiUrl}${BASE_URL}/${jobId}/download-zip/?image_format=${format}`;

    const response = await fetch(url, {
        credentials: "include", // Send cookies for authenticated downloads
    });

    if (!response.ok) {
        let errorMessage = `Download failed: ${response.statusText}`;
        try {
            const errorData = await response.json();
            if (errorData.error) {
                errorMessage = errorData.error;
            }
        } catch {
            // Ignore JSON parse errors
        }
        throw new HttpError(errorMessage, response.status);
    }

    const blob = await response.blob();
    
    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `job_${jobId}_images.zip`;
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1];
        }
    }

    // Trigger browser download
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
};
