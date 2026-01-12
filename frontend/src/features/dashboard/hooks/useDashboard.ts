import { useQuery } from "@tanstack/react-query";
import { getDashboardStats, getLatestPublishedImages } from "../api/dashboard";

/**
 * Hook to fetch dashboard statistics
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => getDashboardStats(),
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch latest published images
 */
export function useLatestPublishedImages(limit: number = 8) {
  return useQuery({
    queryKey: ["dashboard", "latest-images", limit],
    queryFn: () => getLatestPublishedImages(limit),
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}
