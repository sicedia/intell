import { apiClient } from "@/shared/lib/api-client";
import { Tag } from "../types";

// Use simple paths - api-client already handles the base URL
const BASE_URL = "/tags";

// DRF paginated response type
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Get all tags
 */
export async function getTags(): Promise<Tag[]> {
  const response = await apiClient.get<PaginatedResponse<Tag> | Tag[]>(`${BASE_URL}/`);
  // Handle both paginated and non-paginated responses
  if (Array.isArray(response)) {
    return response;
  }
  return response.results || [];
}

/**
 * Create a new tag
 */
export async function createTag(data: { name: string; color?: string }): Promise<Tag> {
  const response = await apiClient.post<Tag>(`${BASE_URL}/`, data);
  return response;
}
