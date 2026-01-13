"use client";

import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useTranslations } from "next-intl";
import { Input } from "@/shared/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Search, Filter, Grid, List, X, Layers, LayoutGrid } from "lucide-react";
import { ImageFilters, ImageTaskStatus } from "../types";
import { useTags } from "../hooks/useTags";
import { useGroups } from "../hooks/useGroups";
import { cn } from "@/shared/lib/utils";
import { useImageLibraryViewMode } from "../hooks/useImageLibraryViewMode";

interface ImageLibraryFiltersProps {
  filters: ImageFilters;
  onFiltersChange: (filters: ImageFilters) => void;
  viewMode?: "grid" | "list";
  onViewModeChange?: (mode: "grid" | "list") => void;
  libraryViewMode?: "all" | "grouped";
  onLibraryViewModeChange?: (mode: "all" | "grouped") => void;
  className?: string;
}

export function ImageLibraryFilters({
  filters,
  onFiltersChange,
  viewMode = "grid",
  onViewModeChange,
  libraryViewMode: externalLibraryViewMode,
  onLibraryViewModeChange,
  className,
}: ImageLibraryFiltersProps) {
  const [searchValue, setSearchValue] = useState(filters.search || "");
  const { data: tags = [], isLoading: tagsLoading } = useTags();
  const { data: groups = [], isLoading: groupsLoading } = useGroups();
  const t = useTranslations('images');
  const tCommon = useTranslations('common');
  
  // Use external libraryViewMode if provided (from parent), otherwise use hook
  const { viewMode: internalLibraryViewMode, setViewMode: setInternalLibraryViewMode } = useImageLibraryViewMode();
  const libraryViewMode = externalLibraryViewMode ?? internalLibraryViewMode;
  
  const handleLibraryViewModeChange = useCallback((mode: "all" | "grouped") => {
    if (onLibraryViewModeChange) {
      // Use external handler if provided (for immediate sync)
      onLibraryViewModeChange(mode);
    } else {
      // Fallback to internal hook
      setInternalLibraryViewMode(mode);
    }
  }, [onLibraryViewModeChange, setInternalLibraryViewMode]);

  // Debounce search - use ref to avoid stale closure issues
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filtersRef.current, search: searchValue || undefined });
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue, onFiltersChange]);

  const handleFilterChange = useCallback((key: keyof ImageFilters, value: string | number[] | undefined) => {
    onFiltersChange({ ...filtersRef.current, [key]: value });
  }, [onFiltersChange]);

  const clearFilters = useCallback(() => {
    setSearchValue("");
    onFiltersChange({});
  }, [onFiltersChange]);

  const hasActiveFilters =
    filters.status || filters.tags?.length || filters.group || filters.search || filters.date_from || filters.date_to;

  // Get active filter count for badge
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.status) count++;
    if (filters.tags?.length) count++;
    if (filters.group) count++;
    if (filters.search) count++;
    if (filters.date_from || filters.date_to) count++;
    return count;
  }, [filters.status, filters.tags, filters.group, filters.search, filters.date_from, filters.date_to]);

  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="flex flex-col gap-4">
          {/* Search and Status Filter */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search 
                className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" 
                aria-hidden="true"
              />
              <Input
                placeholder="Buscar por título, algoritmo o descripción..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="pl-10"
                aria-label="Buscar imágenes"
              />
            </div>
            <Select
              value={filters.status || "all"}
              onValueChange={(value) =>
                handleFilterChange("status", value === "all" ? undefined : (value as ImageTaskStatus))
              }
            >
              <SelectTrigger className="w-full sm:w-[180px]" aria-label={t('filterByStatus')}>
                <Filter className="mr-2 h-4 w-4" aria-hidden="true" />
                <SelectValue placeholder={tCommon('status')} />
                {filters.status && (
                  <span className="ml-2 h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
                )}
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allStatuses')}</SelectItem>
                <SelectItem value="SUCCESS">{t('successful')}</SelectItem>
                <SelectItem value="PENDING">{t('pending')}</SelectItem>
                <SelectItem value="RUNNING">{t('running')}</SelectItem>
                <SelectItem value="FAILED">{t('failed')}</SelectItem>
                <SelectItem value="CANCELLED">{t('cancelled')}</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2 flex-shrink-0">
              {/* Library View Mode Toggle */}
              <div className="flex gap-1 border rounded-md p-1" role="group" aria-label="Modo de visualización de librería">
                <Button
                  variant={libraryViewMode === "all" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleLibraryViewModeChange("all")}
                  className="h-8"
                  aria-label="Ver todas las imágenes"
                  aria-pressed={libraryViewMode === "all"}
                >
                  <LayoutGrid className="h-3 w-3 mr-1" aria-hidden="true" />
                  <span className="hidden sm:inline">Todas</span>
                </Button>
                <Button
                  variant={libraryViewMode === "grouped" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleLibraryViewModeChange("grouped")}
                  className="h-8"
                  aria-label="Ver imágenes agrupadas por lote"
                  aria-pressed={libraryViewMode === "grouped"}
                >
                  <Layers className="h-3 w-3 mr-1" aria-hidden="true" />
                  <span className="hidden sm:inline">Por lote</span>
                </Button>
              </div>
              {/* Grid/List Toggle */}
              {onViewModeChange && (
                <div className="flex gap-1 border rounded-md p-1" role="group" aria-label="Vista de imágenes">
                  <Button
                    variant={viewMode === "grid" ? "default" : "ghost"}
                    size="icon"
                    onClick={() => onViewModeChange("grid")}
                    className="h-8 w-8"
                    aria-label={t('gridView')}
                    aria-pressed={viewMode === "grid"}
                  >
                    <Grid className="h-4 w-4" aria-hidden="true" />
                  </Button>
                  <Button
                    variant={viewMode === "list" ? "default" : "ghost"}
                    size="icon"
                    onClick={() => onViewModeChange("list")}
                    className="h-8 w-8"
                    aria-label={t('listView')}
                    aria-pressed={viewMode === "list"}
                  >
                    <List className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Additional Filters */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <Select
              value={filters.group?.toString() || "all"}
              onValueChange={(value) =>
                handleFilterChange("group", value === "all" ? undefined : parseInt(value))
              }
            >
              <SelectTrigger className="w-full sm:w-[180px]" aria-label="Filtrar por grupo">
                <SelectValue placeholder="Grupo" />
                {filters.group && (
                  <span className="ml-2 h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
                )}
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los grupos</SelectItem>
                {!groupsLoading && groups.map((group) => (
                  <SelectItem key={group.id} value={group.id.toString()}>
                    {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.tags && filters.tags.length > 0 ? filters.tags[0].toString() : "all"}
              onValueChange={(value) =>
                handleFilterChange("tags", value === "all" ? undefined : [parseInt(value)])
              }
            >
              <SelectTrigger className="w-full sm:w-[180px]" aria-label={t('filterByTag')}>
                <SelectValue placeholder={t('tag')} />
                {filters.tags && filters.tags.length > 0 && (
                  <span className="ml-2 h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
                )}
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allTags')}</SelectItem>
                {!tagsLoading && tags.map((tag) => (
                  <SelectItem key={tag.id} value={tag.id.toString()}>
                    {tag.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {hasActiveFilters && (
              <Button 
                variant="outline" 
                onClick={clearFilters} 
                className="sm:ml-auto w-full sm:w-auto"
                aria-label={t('clearFiltersWithCount', { count: activeFilterCount })}
              >
                <X className="h-4 w-4 mr-2" aria-hidden="true" />
                {t('clearFilters')}
                {activeFilterCount > 0 && (
                  <span className="ml-2 h-5 w-5 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
