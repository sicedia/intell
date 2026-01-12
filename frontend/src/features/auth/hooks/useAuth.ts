"use client";

/**
 * Authentication hook using TanStack Query + Zustand.
 *
 * Provides:
 * - login/logout mutations
 * - auth state from store
 * - automatic auth check on mount
 */
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../stores/useAuthStore";
import {
  login as apiLogin,
  logout as apiLogout,
  getMe,
  fetchCsrfToken,
  type LoginCredentials,
  type User,
} from "../api/auth";
import { hasCsrfToken } from "@/shared/lib/csrf";
import { HttpError } from "@/shared/lib/api-client";

// ============================================================================
// Query Keys
// ============================================================================

export const authKeys = {
  all: ["auth"] as const,
  me: () => [...authKeys.all, "me"] as const,
};

// ============================================================================
// Hook
// ============================================================================

export function useAuth() {
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading, setUser, clearAuth, setLoading } =
    useAuthStore();

  // Query to check current auth status
  const meQuery = useQuery({
    queryKey: authKeys.me(),
    queryFn: async () => {
      // Ensure we have CSRF token before any request
      if (!hasCsrfToken()) {
        await fetchCsrfToken();
      }
      try {
        return await getMe();
      } catch (error) {
        // 401/403 means not authenticated - this is expected, not an error
        if (error instanceof HttpError && (error.status === 401 || error.status === 403)) {
          return null;
        }
        // Re-throw other errors (network issues, server errors, etc.)
        throw error;
      }
    },
    retry: false, // Don't retry on auth errors
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });

  // Sync query result with store (using useEffect to avoid side effects in render)
  useEffect(() => {
    if (meQuery.isSuccess) {
      if (meQuery.data) {
        setUser(meQuery.data);
      } else {
        // null means not authenticated (401/403 was returned)
        clearAuth();
      }
    }
  }, [meQuery.isSuccess, meQuery.data, setUser, clearAuth]);

  useEffect(() => {
    if (meQuery.isError) {
      // Only clear auth on actual errors (not 401/403 which return null)
      clearAuth();
    }
  }, [meQuery.isError, clearAuth]);

  useEffect(() => {
    setLoading(meQuery.isLoading);
  }, [meQuery.isLoading, setLoading]);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      // Ensure CSRF token is set before login
      if (!hasCsrfToken()) {
        await fetchCsrfToken();
      }
      return apiLogin(credentials);
    },
    onSuccess: (data: User) => {
      setUser(data);
      // Invalidate and refetch me query
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: apiLogout,
    onSuccess: () => {
      clearAuth();
      // Clear all queries on logout
      queryClient.clear();
    },
    onError: () => {
      // Even if logout fails on server, clear local state
      clearAuth();
      queryClient.clear();
    },
  });

  return {
    // State
    user,
    isAuthenticated,
    isLoading: isLoading || meQuery.isLoading,

    // Actions
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    refetchUser: () => queryClient.invalidateQueries({ queryKey: authKeys.me() }),

    // Mutation states
    loginError: loginMutation.error as HttpError | null,
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
  };
}
