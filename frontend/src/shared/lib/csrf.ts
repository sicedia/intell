/**
 * CSRF Token utilities for Django session authentication.
 *
 * Django sets a `csrftoken` cookie that must be sent as `X-CSRFToken` header
 * in all mutating requests (POST, PUT, PATCH, DELETE).
 */

/**
 * Get the CSRF token from cookies.
 * Returns null if not found (call fetchCsrfToken first).
 */
export function getCsrfToken(): string | null {
  if (typeof document === "undefined") {
    // Server-side rendering - no cookies available
    return null;
  }

  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "csrftoken") {
      return decodeURIComponent(value);
    }
  }
  return null;
}

/**
 * Check if we have a valid CSRF token.
 */
export function hasCsrfToken(): boolean {
  return getCsrfToken() !== null;
}
