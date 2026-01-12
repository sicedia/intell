"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import { useImageDetail, useImageUpdate, usePublishImage } from "../hooks/useImages";
import { TagSelector } from "./TagSelector";
import { GroupSelector } from "./GroupSelector";
import { AIDescriptionDialog } from "./AIDescriptionDialog";
import { ImageTask } from "../types";
import { Save, Sparkles, BookmarkPlus, BookmarkCheck } from "lucide-react";
import { Spinner } from "@/shared/components/ui/spinner";
import { Badge } from "@/shared/components/ui/badge";

interface ImageDetailDialogProps {
  imageId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ImageDetailDialog({ imageId, open, onOpenChange }: ImageDetailDialogProps) {
  const { data: image, isLoading, refetch } = useImageDetail(imageId);
  const updateImage = useImageUpdate();
  const publishImage = usePublishImage();
  const [activeTab, setActiveTab] = useState("view");
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);

  // Initialize form when image loads
  useEffect(() => {
    if (image) {
      setTitle(image.title || "");
      setDescription(image.user_description || "");
      setSelectedTags(image.tags || []);
      setSelectedGroup(image.group);
    }
  }, [image]);

  const handleSave = async () => {
    if (!image) return;

    try {
      await updateImage.mutateAsync({
        imageId: image.id,
        data: {
          title: title.trim() || undefined,
          user_description: description.trim() || undefined,
          tags: selectedTags,
          group: selectedGroup,
        },
      });
      onOpenChange(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const hasChanges =
    image &&
    (title !== (image.title || "") ||
      description !== (image.user_description || "") ||
      JSON.stringify(selectedTags.sort()) !== JSON.stringify((image.tags || []).sort()) ||
      selectedGroup !== image.group);

  if (isLoading || !image) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Cargando imagen...</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {image.title || `Imagen ${image.id}`} - {image.algorithm_key}
            </DialogTitle>
          </DialogHeader>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="view">Vista</TabsTrigger>
              <TabsTrigger value="edit">Editar Metadata</TabsTrigger>
              <TabsTrigger value="ai">Descripción IA</TabsTrigger>
            </TabsList>

            {/* View Tab */}
            <TabsContent value="view" className="space-y-4 mt-4">
              <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden">
                {image.artifact_png_url ? (
                  // Use native img for external URLs to avoid Next.js Image optimization issues
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={image.artifact_png_url}
                    alt={image.title || `Image ${image.id}`}
                    className="absolute inset-0 w-full h-full object-contain"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    Imagen no disponible
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div>
                  <Label className="text-muted-foreground">Título</Label>
                  <p className="text-sm font-medium">{image.title || "Sin título"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Algoritmo</Label>
                  <p className="text-sm">{image.algorithm_key} v{image.algorithm_version}</p>
                </div>
                {image.user_description && (
                  <div>
                    <Label className="text-muted-foreground">Descripción</Label>
                    <p className="text-sm whitespace-pre-wrap">{image.user_description}</p>
                  </div>
                )}
                <div>
                  <Label className="text-muted-foreground">Estado</Label>
                  <div className="flex items-center gap-2">
                    <p className="text-sm">{image.status}</p>
                    <Badge variant={image.is_published ? "default" : "secondary"}>
                      {image.is_published ? "Publicado" : "Borrador"}
                    </Badge>
                  </div>
                </div>
                {image.is_published && image.published_at && (
                  <div>
                    <Label className="text-muted-foreground">Publicado el</Label>
                    <p className="text-sm">{new Date(image.published_at).toLocaleString()}</p>
                  </div>
                )}
                <div>
                  <Label className="text-muted-foreground">Creado</Label>
                  <p className="text-sm">{new Date(image.created_at).toLocaleString()}</p>
                </div>
                {image.status === "SUCCESS" && (
                  <div className="pt-4 border-t">
                    <Button
                      variant={image.is_published ? "outline" : "default"}
                      onClick={async () => {
                        try {
                          await publishImage.mutateAsync({
                            imageId: image.id,
                            publish: !image.is_published,
                          });
                          refetch();
                        } catch (error) {
                          // Error handled by hook
                        }
                      }}
                      disabled={publishImage.isPending}
                      className="w-full"
                    >
                      {publishImage.isPending ? (
                        <>
                          <Spinner className="mr-2 h-4 w-4" />
                          {image.is_published ? "Despublicando..." : "Publicando..."}
                        </>
                      ) : image.is_published ? (
                        <>
                          <BookmarkCheck className="mr-2 h-4 w-4" />
                          Despublicar (convertir a borrador)
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="mr-2 h-4 w-4" />
                          Publicar en librería
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Edit Tab */}
            <TabsContent value="edit" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Título</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Título de la imagen"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Descripción</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Descripción de la imagen"
                    rows={4}
                  />
                </div>

                <TagSelector
                  selectedTags={selectedTags}
                  onTagsChange={setSelectedTags}
                />

                <GroupSelector
                  selectedGroup={selectedGroup}
                  onGroupChange={setSelectedGroup}
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleSave} disabled={!hasChanges || updateImage.isPending}>
                  {updateImage.isPending ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Guardar cambios
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>

            {/* AI Description Tab */}
            <TabsContent value="ai" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div className="rounded-lg border p-4 space-y-2">
                  <h3 className="font-medium">Generar descripción con IA</h3>
                  <p className="text-sm text-muted-foreground">
                    Usa inteligencia artificial para generar una descripción detallada de esta
                    imagen basada en los datos del gráfico y contexto que proporciones.
                  </p>
                  <Button onClick={() => setIsAIDialogOpen(true)} className="w-full">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Solicitar descripción con IA
                  </Button>
                </div>

                {image.user_description && (
                  <div className="space-y-2">
                    <Label>Descripción actual</Label>
                    <div className="rounded-md border p-3 bg-muted/50">
                      <p className="text-sm whitespace-pre-wrap">{image.user_description}</p>
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* AI Description Dialog */}
      {image && (
        <AIDescriptionDialog
          image={image}
          open={isAIDialogOpen}
          onOpenChange={setIsAIDialogOpen}
          onDescriptionSaved={() => {
            setIsAIDialogOpen(false);
            setActiveTab("view");
            // Refresh image data
            refetch();
          }}
        />
      )}
    </>
  );
}
