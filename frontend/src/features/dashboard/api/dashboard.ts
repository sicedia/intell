import { apiClient } from "@/shared/lib/api-client";
import { ImageLibraryItem } from "@/features/images/types";

/**
 * Dashboard statistics response
 */
export interface DashboardStats {
  total_images: number;
  total_published_images: number;
  total_ai_described_images: number;
  total_active_users_this_month: number;
  images_this_month: number;
  published_this_month: number;
}

/**
 * Get dashboard statistics
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>("/dashboard/stats/");
  return response;
}

/**
 * Get latest published images
 */
export async function getLatestPublishedImages(limit: number = 8): Promise<ImageLibraryItem[]> {
  const response = await apiClient.get<ImageLibraryItem[]>(
    `/dashboard/latest-images/?limit=${limit}`
  );
  return response;
}
