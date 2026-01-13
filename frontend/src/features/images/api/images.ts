import { apiClient } from "@/shared/lib/api-client";
import { ImageTask, ImageLibraryItem, ImageTaskUpdate, ImageFilters, PaginatedImageResponse } from "../types";

// Use simple paths - api-client already handles the base URL
const BASE_URL = "/image-tasks";

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
    // Pagination parameters (DRF uses 'page' for page number)
    if (filters.page) params.append("page", filters.page.toString());
    if (filters.pageSize) params.append("page_size", filters.pageSize.toString());
  }
  
  if (library) params.append("library", "true");
  
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * Get list of images with optional filters
 * Returns paginated response if backend supports it, otherwise returns array
 */
export async function getImages(
  filters?: ImageFilters,
  library: boolean = false
): Promise<PaginatedImageResponse<ImageLibraryItem | ImageTask> | (ImageLibraryItem | ImageTask)[]> {
  const queryString = buildQueryString(filters, library);
  const url = queryString ? `${BASE_URL}${queryString}` : `${BASE_URL}/`;
  const response = await apiClient.get<PaginatedImageResponse<ImageLibraryItem | ImageTask> | (ImageLibraryItem | ImageTask)[]>(url);
  
  // Handle both paginated and non-paginated responses
  if (Array.isArray(response)) {
    // Non-paginated response - return as is
    return response;
  }
  
  // Paginated response - check if it has the expected structure
  if (response && typeof response === 'object' && 'results' in response) {
    return response as PaginatedImageResponse<ImageLibraryItem | ImageTask>;
  }
  
  // Fallback: if response has results but not full pagination structure
  if (response && typeof response === 'object' && 'results' in response) {
    return {
      count: (response as any).count || (response as any).results?.length || 0,
      next: (response as any).next || null,
      previous: (response as any).previous || null,
      results: (response as any).results || [],
    };
  }
  
  // Last resort: return empty array
  return [];
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

/**
 * Delete an image
 */
export async function deleteImage(imageId: number): Promise<void> {
  await apiClient.delete(`${BASE_URL}/${imageId}/`);
}
