# Generation Feature

Feature module for creating and managing visualization generation jobs. Handles the complete workflow from data upload to algorithm selection to job execution and progress tracking.

## Structure

```
generation/
├── api/              # API client functions (createJob, getJob, cancelJob)
├── constants/        # Constants and type definitions
│   ├── algorithms.ts # Available algorithm configurations
│   ├── events.ts     # Event type constants
│   └── job.ts        # Job-related types and transformers
├── hooks/            # Custom React hooks
│   ├── useJobCreation.ts    # Job creation logic
│   ├── useJobProgress.ts    # Main hook for job progress tracking
│   ├── useJobPolling.ts    # Polling fallback when WebSocket unavailable
│   └── useJobWebSocket.ts  # WebSocket connection management
├── stores/           # Zustand state management
│   └── useWizardStore.ts   # Wizard state with sessionStorage persistence
└── ui/               # UI components
    ├── GenerateWizard.tsx  # Main wizard container
    ├── SourceStep.tsx       # Step 1: Data source selection
    ├── VisualizationStep.tsx # Step 2: Algorithm selection
    ├── RunStep.tsx         # Step 3: Job execution and monitoring
    ├── JobProgress.tsx     # Progress display component
    └── JobResults.tsx      # Results display component
```

## API

### Hooks

#### `useJobCreation()`

Manages job creation logic including form submission, error handling, and auto-start.

```typescript
const { jobId, isCreating, createError, handleRetry, handleCancel } = useJobCreation();
```

**Returns:**
- `jobId: number | null` - Created job ID
- `isCreating: boolean` - Creation in progress
- `createError: string | null` - Error message if creation failed
- `handleRetry: () => void` - Retry job creation
- `handleCancel: () => Promise<void>` - Cancel running job

#### `useJobProgress(jobId: number | null)`

Tracks job progress via WebSocket with polling fallback.

```typescript
const { job, events, connectionStatus, isConnected } = useJobProgress(jobId);
```

**Returns:**
- `job: Job | undefined` - Current job state
- `events: JobEvent[]` - Real-time event log
- `connectionStatus: "connecting" | "connected" | "disconnected" | "failed"` - WS status
- `isConnected: boolean` - WebSocket connected

#### `useWizardStore()`

Zustand store for wizard state with sessionStorage persistence.

```typescript
const {
  currentStep,
  sourceType,
  sourceFile,
  selectedAlgorithms,
  jobId,
  setStep,
  setSourceType,
  setSourceFile,
  setSelectedAlgorithms,
  setJobId,
  reset,
} = useWizardStore();
```

**Note:** `sourceFile` is not persisted (File objects are not serializable).

### API Functions

#### `createJob(formData: FormData)`

Creates a new generation job.

```typescript
const formData = new FormData();
formData.append("source_type", "espacenet_excel");
formData.append("source_data", file);
formData.append("images", JSON.stringify(algorithms));
formData.append("idempotency_key", key);

const result = await createJob(formData);
// { job_id: number, status: string, message: string }
```

#### `getJob(jobId: number | string)`

Fetches job details.

```typescript
const job = await getJob(123);
```

#### `cancelJob(jobId: number | string)`

Cancels a running job.

```typescript
await cancelJob(123);
```

## Usage Example

```typescript
import { GenerateWizard } from "@/features/generation/ui/GenerateWizard";

export default function GeneratePage() {
  return <GenerateWizard />;
}
```

## Features

- **Multi-step wizard** for job creation
- **Real-time progress** via WebSocket with automatic polling fallback
- **Session persistence** - wizard state survives page refresh
- **Error handling** with retry mechanisms
- **Job cancellation** support
- **Throttled updates** to prevent excessive re-renders

## Constants

### Algorithms

Available algorithms are defined in `constants/algorithms.ts`:

```typescript
import { ALGORITHMS } from "@/features/generation/constants/algorithms";

ALGORITHMS.forEach(algo => {
  console.log(algo.key, algo.label, algo.defaultParams);
});
```

### Event Types

Event type constants are in `constants/events.ts`:

```typescript
import { JOB_EVENT_TYPES, ENTITY_TYPES } from "@/features/generation/constants/events";
```

## Types

All types are defined in `constants/job.ts`:

- `Job` - Frontend job representation
- `ImageTask` - Individual image generation task
- `JobEvent` - Real-time event from WebSocket/API
- `JobStatus` - Job status enum
- `BackendJob` - Raw API response format
- `BackendImageTask` - Raw API task format
