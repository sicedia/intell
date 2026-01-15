import { apiClient } from "@/shared/lib/api-client";
import { AIDescriptionRequest, AIDescriptionResponse, DescriptionTask, AvailableModelsResponse } from "../types";

/**
 * Generate AI description for an image
 */
export async function generateAIDescription(
  data: AIDescriptionRequest
): Promise<AIDescriptionResponse> {
  const response = await apiClient.post<AIDescriptionResponse>(
    `/ai/describe/`,
    data
  );
  return response;
}

/**
 * Get description task by ID
 */
export async function getDescriptionTask(taskId: number): Promise<DescriptionTask> {
  const response = await apiClient.get<DescriptionTask>(
    `/description-tasks/${taskId}/`
  );
  return response;
}

/**
 * Get available AI models with cost information
 */
export async function getAvailableModels(): Promise<AvailableModelsResponse> {
  const response = await apiClient.get<AvailableModelsResponse>(
    `/ai/models/`
  );
  return response;
}
