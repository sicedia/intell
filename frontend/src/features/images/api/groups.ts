import { apiClient } from "@/shared/lib/api-client";
import { ImageGroup } from "../types";

// Use simple paths - api-client already handles the base URL
const BASE_URL = "/image-groups";

// DRF paginated response type
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Get all groups for current user
 */
export async function getGroups(): Promise<ImageGroup[]> {
  const response = await apiClient.get<PaginatedResponse<ImageGroup> | ImageGroup[]>(`${BASE_URL}/`);
  // Handle both paginated and non-paginated responses
  if (Array.isArray(response)) {
    return response;
  }
  return response.results || [];
}

/**
 * Get single group by ID
 */
export async function getGroup(groupId: number): Promise<ImageGroup> {
  const response = await apiClient.get<ImageGroup>(`${BASE_URL}/${groupId}/`);
  return response;
}

/**
 * Create a new group
 */
export async function createGroup(data: { name: string; description?: string }): Promise<ImageGroup> {
  const response = await apiClient.post<ImageGroup>(`${BASE_URL}/`, data);
  return response;
}

/**
 * Update a group
 */
export async function updateGroup(
  groupId: number,
  data: { name?: string; description?: string }
): Promise<ImageGroup> {
  const response = await apiClient.patch<ImageGroup>(`${BASE_URL}/${groupId}/`, data);
  return response;
}

/**
 * Delete a group
 */
export async function deleteGroup(groupId: number): Promise<void> {
  await apiClient.delete(`${BASE_URL}/${groupId}/`);
}
