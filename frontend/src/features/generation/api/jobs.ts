import { apiClient } from "@/shared/lib/api-client";
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

    const response = await fetch(fullUrl, {
        method: "POST",
        body: formData,
    });

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

        throw new Error(errorMessage);
    }

    return response.json();
};

export const getJob = async (jobId: number | string): Promise<Job> => {
    const backendJob = await apiClient.get<BackendJob>(`${BASE_URL}/${jobId}/`);
    return transformJob(backendJob);
};

export const cancelJob = async (jobId: number | string): Promise<{ job_id: number; status: string; message: string }> => {
    const result = await apiClient.post<{ job_id: number; status: string; message: string }>(`${BASE_URL}/${jobId}/cancel/`);
    return result;
};
