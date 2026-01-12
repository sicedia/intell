"use client";

/**
 * Auth Provider component.
 *
 * Initializes authentication state on mount by:
 * 1. Fetching CSRF token if missing
 * 2. Checking current auth status via /me
 *
 * This should wrap the app in the root layout.
 */
import { useEffect } from "react";
import { useAuth } from "../hooks/useAuth";

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  // useAuth hook automatically checks auth status via /me query
  const { isLoading } = useAuth();

  // The hook handles everything - CSRF fetch, /me check, store sync
  // We just need to render children

  return <>{children}</>;
}
