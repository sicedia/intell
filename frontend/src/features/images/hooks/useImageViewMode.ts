/**
 * Hook to manage image view mode (grid vs list) with localStorage persistence.
 */
import { useState, useEffect } from "react";

type ViewMode = "grid" | "list";

const STORAGE_KEY = "intell:imageLibrary:viewMode";

export function useImageViewMode() {
  // Always start with "grid" to match server-side rendering and avoid hydration errors
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage after hydration (client-side only)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "grid" || stored === "list") {
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
