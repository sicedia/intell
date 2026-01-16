"use client";

import React, { useState } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/shared/components/ui/dialog";
import { useTags, useCreateTag } from "../hooks/useTags";
import { Tag } from "../types";
import { Plus, X } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface TagSelectorProps {
  selectedTags: number[];
  onTagsChange: (tagIds: number[]) => void;
  className?: string;
}

export function TagSelector({ selectedTags, onTagsChange, className }: TagSelectorProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const [newTagName, setNewTagName] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const selectedTagObjects = tags.filter((tag) => selectedTags.includes(tag.id));

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;

    try {
      const newTag = await createTag.mutateAsync({ name: newTagName.trim() });
      onTagsChange([...selectedTags, newTag.id]);
      setNewTagName("");
      setIsDialogOpen(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleRemoveTag = (tagId: number) => {
    onTagsChange(selectedTags.filter((id) => id !== tagId));
  };

  const handleToggleTag = (tagId: number) => {
    if (selectedTags.includes(tagId)) {
      handleRemoveTag(tagId);
    } else {
      onTagsChange([...selectedTags, tagId]);
    }
  };

  if (isLoading) {
    return <div className={cn("text-sm text-muted-foreground", className)}>Cargando tags...</div>;
  }

  if (tags.length === 0 && !isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Tags</label>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="h-7">
                <Plus className="h-3 w-3 mr-1" />
                Nuevo
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Crear nuevo tag</DialogTitle>
                <DialogDescription>
                  Crea un nuevo tag para categorizar tus imágenes. Los tags te ayudan a organizar y encontrar imágenes fácilmente.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Nombre del tag"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleCreateTag();
                    }
                  }}
                />
                <Button onClick={handleCreateTag} disabled={!newTagName.trim() || createTag.isPending}>
                  {createTag.isPending ? "Creando..." : "Crear"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        <p className="text-sm text-muted-foreground">No hay tags disponibles. Crea uno nuevo para empezar.</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Tags</label>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="h-7">
              <Plus className="h-3 w-3 mr-1" />
              Nuevo
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear nuevo tag</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Nombre del tag"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleCreateTag();
                  }
                }}
              />
              <Button onClick={handleCreateTag} disabled={!newTagName.trim() || createTag.isPending}>
                {createTag.isPending ? "Creando..." : "Crear"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Selected tags */}
      {selectedTagObjects.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedTagObjects.map((tag) => (
            <Badge
              key={tag.id}
              variant="outline"
              className="px-2 py-1"
              style={{ borderColor: tag.color, color: tag.color }}
            >
              {tag.name}
              <button
                onClick={() => handleRemoveTag(tag.id)}
                className="ml-1.5 hover:opacity-70"
                aria-label={`Remove ${tag.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Available tags to select */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags
            .filter((tag) => !selectedTags.includes(tag.id))
            .map((tag) => (
              <Badge
                key={tag.id}
                variant="outline"
                className="cursor-pointer hover:bg-accent"
                style={{ borderColor: tag.color, color: tag.color }}
                onClick={() => handleToggleTag(tag.id)}
              >
                <Plus className="h-3 w-3 mr-1" />
                {tag.name}
              </Badge>
            ))}
        </div>
      )}

    </div>
  );
}
