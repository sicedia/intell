# Images Feature

Image library and management module for viewing and organizing generated visualizations.

## Structure

```
images/
├── api/
│   ├── images.ts          # Image CRUD operations
│   ├── tags.ts            # Tag management
│   ├── groups.ts          # Group management
│   └── descriptions.ts    # AI description generation
├── hooks/
│   ├── useImages.ts       # Image list, detail, update hooks
│   ├── useTags.ts         # Tag hooks
│   ├── useGroups.ts       # Group hooks
│   └── useAIDescription.ts # AI description generation with polling
├── ui/
│   ├── ImageDetailDialog.tsx    # Image detail/edit modal with tabs
│   ├── AIDescriptionDialog.tsx  # AI description generation dialog
│   ├── TagSelector.tsx          # Multi-select tag component
│   ├── GroupSelector.tsx        # Group selection component
│   └── ImageLibraryFilters.tsx # Search and filter bar
├── types.ts               # TypeScript type definitions
└── README.md
```

## Features

### Image Library
- **Gallery View**: Grid/list view of all generated images
- **Search & Filters**: Search by title, algorithm, description. Filter by status, tags, groups, date range
- **Image Detail**: View full image with metadata
- **Edit Metadata**: Update title, description, tags, and group assignment

### AI Description Generation
- **Context Input**: Textarea with 200 character minimum validation
- **Provider Selection**: Optional selection of AI provider (OpenAI, Anthropic, Mock)
- **Real-time Progress**: Polling with progress indicators
- **Error Handling**: Automatic fallback between providers with user feedback
- **Editable Results**: Edit AI-generated descriptions before saving

### Organization
- **Tags**: Create and assign tags to images with color coding
- **Groups**: Organize images into collections
- **Metadata**: Custom titles and descriptions for each image

## Usage

### Basic Image List

```typescript
import { useImages } from "@/features/images/hooks/useImages";

function MyComponent() {
  const { data: images, isLoading } = useImages({ status: "SUCCESS" }, true);
  // ...
}
```

### Generate AI Description

```typescript
import { useAIDescription } from "@/features/images/hooks/useAIDescription";

function MyComponent() {
  const { generateDescription, isGenerating, descriptionTask } = useAIDescription();
  
  const handleGenerate = () => {
    generateDescription({
      image_task_id: 1,
      user_context: "Context with at least 200 characters...",
      provider_preference: "openai" // optional
    });
  };
}
```

### Update Image Metadata

```typescript
import { useImageUpdate } from "@/features/images/hooks/useImages";

function MyComponent() {
  const updateImage = useImageUpdate();
  
  const handleUpdate = () => {
    updateImage.mutate({
      imageId: 1,
      data: {
        title: "New Title",
        user_description: "New description",
        tags: [1, 2, 3],
        group: 1
      }
    });
  };
}
```

## Error Handling

The feature includes comprehensive error handling:

- **Connection Errors**: Automatic retry with user feedback
- **Validation Errors**: Clear messages for invalid input (e.g., context < 200 chars)
- **Provider Failures**: Automatic fallback between AI providers with toast notifications
- **Server Errors**: Retry logic with exponential backoff

All errors are displayed via toast notifications (sonner) with specific, actionable messages.

## API Endpoints

- `GET /api/image-tasks/?library=true` - List images (library format)
- `GET /api/image-tasks/{id}/` - Get image detail
- `PATCH /api/image-tasks/{id}/` - Update image metadata
- `GET /api/tags/` - List tags
- `POST /api/tags/` - Create tag
- `GET /api/image-groups/` - List groups
- `POST /api/image-groups/` - Create group
- `POST /api/ai/describe/` - Generate AI description
- `GET /api/description-tasks/{id}/` - Get description task status
