import { apiClient } from "@/shared/lib/api-client";
import { ImageTask, ImageLibraryItem, ImageTaskUpdate, ImageFilters } from "../types";

// Use simple paths - api-client already handles the base URL
const BASE_URL = "/image-tasks";

// DRF paginated response type
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Build query string from filters
 */
function buildQueryString(filters?: ImageFilters, library?: boolean): string {
  const params = new URLSearchParams();
  
  if (filters) {
    if (filters.status) params.append("status", filters.status);
    if (filters.tags && filters.tags.length > 0) {
      params.append("tags", filters.tags.join(","));
    }
    if (filters.group) params.append("group", filters.group.toString());
    if (filters.search) params.append("search", filters.search);
    if (filters.date_from) params.append("date_from", filters.date_from);
    if (filters.date_to) params.append("date_to", filters.date_to);
    if (filters.group_by) params.append("group_by", filters.group_by);
  }
  
  if (library) params.append("library", "true");
  
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * Get list of images with optional filters
 */
export async function getImages(
  filters?: ImageFilters,
  library: boolean = false
): Promise<ImageLibraryItem[] | ImageTask[]> {
  const queryString = buildQueryString(filters, library);
  const url = queryString ? `${BASE_URL}${queryString}` : `${BASE_URL}/`;
  const response = await apiClient.get<PaginatedResponse<ImageLibraryItem | ImageTask> | (ImageLibraryItem | ImageTask)[]>(url);
  // Handle both paginated and non-paginated responses
  if (Array.isArray(response)) {
    return response;
  }
  return response.results || [];
}

/**
 * Get single image by ID
 */
export async function getImage(imageId: number): Promise<ImageTask> {
  const response = await apiClient.get<ImageTask>(`${BASE_URL}/${imageId}/`);
  return response;
}

/**
 * Update image metadata
 */
export async function updateImageMetadata(
  imageId: number,
  data: ImageTaskUpdate
): Promise<ImageTask> {
  const response = await apiClient.patch<ImageTask>(`${BASE_URL}/${imageId}/`, data);
  return response;
}

/**
 * Publish or unpublish an image
 */
export async function publishImage(
  imageId: number,
  publish: boolean = true
): Promise<{ id: number; is_published: boolean; published_at: string | null; message: string }> {
  const response = await apiClient.post<{ id: number; is_published: boolean; published_at: string | null; message: string }>(
    `${BASE_URL}/${imageId}/publish/`,
    { publish }
  );
  return response;
}
