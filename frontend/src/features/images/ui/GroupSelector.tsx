"use client";

import React, { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/shared/components/ui/dialog";
import { useGroups, useCreateGroup } from "../hooks/useGroups";
import { Plus } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface GroupSelectorProps {
  selectedGroup: number | null;
  onGroupChange: (groupId: number | null) => void;
  className?: string;
}

export function GroupSelector({ selectedGroup, onGroupChange, className }: GroupSelectorProps) {
  const { data: groups = [], isLoading } = useGroups();
  const createGroup = useCreateGroup();
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDescription, setNewGroupDescription] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const selectedGroupObject = groups.find((g) => g.id === selectedGroup);

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return;

    try {
      const newGroup = await createGroup.mutateAsync({
        name: newGroupName.trim(),
        description: newGroupDescription.trim() || undefined,
      });
      onGroupChange(newGroup.id);
      setNewGroupName("");
      setNewGroupDescription("");
      setIsDialogOpen(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  if (isLoading) {
    return <div className={cn("text-sm text-muted-foreground", className)}>Cargando grupos...</div>;
  }

  return (
    <div className={cn("space-y-2", className)}>
      <label className="text-sm font-medium">Grupo</label>
      <div className="flex gap-2">
        <Select 
          value={selectedGroup?.toString() || "none"} 
          onValueChange={(value) => onGroupChange(value === "none" ? null : parseInt(value))}
        >
          <SelectTrigger className="flex-1">
            <SelectValue placeholder="Sin grupo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Sin grupo</SelectItem>
            {groups.map((group) => (
              <SelectItem key={group.id} value={group.id.toString()}>
                {group.name} {group.image_count !== undefined && `(${group.image_count})`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="icon">
              <Plus className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear nuevo grupo</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Nombre del grupo"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
              />
              <Input
                placeholder="Descripción (opcional)"
                value={newGroupDescription}
                onChange={(e) => setNewGroupDescription(e.target.value)}
              />
              <Button onClick={handleCreateGroup} disabled={!newGroupName.trim() || createGroup.isPending}>
                {createGroup.isPending ? "Creando..." : "Crear"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      {selectedGroupObject && (
        <p className="text-xs text-muted-foreground">
          {selectedGroupObject.description || "Sin descripción"}
        </p>
      )}
    </div>
  );
}
