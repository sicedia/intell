/**
 * Hook to manage image library view mode (all vs grouped by Job) with localStorage persistence.
 * 
 * Note: Uses "all" as initial state to avoid hydration mismatches between server and client.
 * The actual value from localStorage is loaded after hydration via useEffect.
 */
import { useState, useEffect } from "react";

type ViewMode = "all" | "grouped";

const STORAGE_KEY = "intell:imageLibrary:viewMode";

export function useImageLibraryViewMode() {
  // Always start with "all" to match server-side rendering and avoid hydration errors
  const [viewMode, setViewMode] = useState<ViewMode>("all");
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage after hydration (client-side only)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "all" || stored === "grouped") {
        setViewMode(stored as ViewMode);
      }
      setIsHydrated(true);
    }
  }, []);

  // Persist to localStorage whenever viewMode changes (only after hydration)
  useEffect(() => {
    if (isHydrated && typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, viewMode);
    }
  }, [viewMode, isHydrated]);

  return {
    viewMode,
    setViewMode,
  };
}
