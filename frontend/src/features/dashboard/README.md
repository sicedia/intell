# Dashboard Feature

Main dashboard page displaying generated visualizations and job overview.

## Structure

```
dashboard/
└── (Currently uses shared components)
```

## Current Implementation

The dashboard page (`app/[locale]/dashboard/page.tsx`) is a Server Component that:

- Displays a gallery of generated images
- Shows empty state when no images exist
- Provides quick action to create new generations
- Supports mock mode for development

## Usage

```typescript
import { PageHeader } from "@/shared/ui/PageHeader";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";

export default async function DashboardPage() {
  // Fetch jobs/images from API
  const images = await fetchImages();
  
  return (
    <div>
      <PageHeader title="Dashboard" />
      <GalleryGrid>
        {images.map(img => (
          <ImageCard key={img.id} {...img} />
        ))}
      </GalleryGrid>
    </div>
  );
}
```

## Future Enhancements

- [ ] Job history list
- [ ] Filtering and search
- [ ] Pagination
- [ ] Bulk actions
- [ ] Statistics overview
