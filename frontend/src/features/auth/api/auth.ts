/**
 * Authentication API functions.
 *
 * All functions use the centralized apiClient which handles:
 * - credentials: "include" for cookies
 * - X-CSRFToken header for mutating requests
 */
import { apiClient } from "@/shared/lib/api-client";
import { env } from "@/shared/lib/env";

// ============================================================================
// Types
// ============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginError {
  detail: string;
  errors?: Record<string, string[]>;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch CSRF token from the server.
 * Sets the csrftoken cookie. Call before any mutating request if cookie is missing.
 */
export async function fetchCsrfToken(): Promise<void> {
  // Use raw fetch with credentials to ensure cookie is set
  const url = `${env.NEXT_PUBLIC_API_BASE_URL}/auth/csrf/`;
  await fetch(url, {
    method: "GET",
    credentials: "include",
  });
}

/**
 * Login with username and password.
 * On success, sets sessionid cookie (HttpOnly) and returns user data.
 */
export async function login(credentials: LoginCredentials): Promise<User> {
  return apiClient.post<User>("/auth/login/", credentials);
}

/**
 * Logout current session.
 * Invalidates session and clears sessionid cookie.
 */
export async function logout(): Promise<void> {
  await apiClient.post<void>("/auth/logout/");
}

/**
 * Get current authenticated user.
 * Returns user data if authenticated, throws 401 if not.
 */
export async function getMe(): Promise<User> {
  return apiClient.get<User>("/auth/me/");
}

/**
 * Check if user is authenticated by calling /me endpoint.
 * Returns user if authenticated, null if not.
 */
export async function checkAuth(): Promise<User | null> {
  try {
    return await getMe();
  } catch {
    return null;
  }
}
