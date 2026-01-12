/**
 * Authentication store using Zustand.
 *
 * Manages:
 * - Current user state
 * - Authentication status
 * - Loading state during auth checks
 */
import { create } from "zustand";
import type { User } from "../api/auth";

// ============================================================================
// Types
// ============================================================================

interface AuthState {
  /** Current authenticated user, null if not authenticated */
  user: User | null;

  /** Whether auth check is in progress */
  isLoading: boolean;

  /** Whether user is authenticated */
  isAuthenticated: boolean;

  /** Set user after successful login or auth check */
  setUser: (user: User | null) => void;

  /** Set loading state */
  setLoading: (loading: boolean) => void;

  /** Clear auth state (on logout) */
  clearAuth: () => void;
}

// ============================================================================
// Store
// ============================================================================

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true, // Start as loading until we check auth
  isAuthenticated: false,

  setUser: (user) =>
    set({
      user,
      isAuthenticated: user !== null,
      isLoading: false,
    }),

  setLoading: (isLoading) => set({ isLoading }),

  clearAuth: () =>
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }),
}));

// ============================================================================
// Selectors
// ============================================================================

export const selectUser = (state: AuthState) => state.user;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectIsLoading = (state: AuthState) => state.isLoading;
