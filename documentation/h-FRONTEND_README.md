# Intell.AI Frontend

Next.js application with TypeScript, App Router, and modern tooling for the Intell.AI patent analysis platform.

## Features

- ⚡ **Next.js 16** with App Router
- 🎨 **Tailwind CSS** + **shadcn/ui** components
- 🌐 **i18n** (English/Spanish) with next-intl
- 🌓 **Dark mode** with next-themes
- 🔄 **TanStack Query** for server state (with intelligent retry)
- 🐻 **Zustand** for client state
- 📝 **React Hook Form** + **Zod** for forms
- 📊 **Excel upload** (react-dropzone + xlsx)
- 🔌 **WebSocket client** for real-time updates
- 🔒 **Connection handling** with global error management
- 🔔 **Toast notifications** (Sonner)
- ✅ **Testing** (Vitest + Playwright)
- 🎯 **Code quality** (ESLint + Prettier + Husky)
- 🐳 **Docker** production-ready

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── [locale]/           # Localized routes
│   │   │   ├── dashboard/      # Dashboard page
│   │   │   ├── generate/       # Job generation wizard
│   │   │   ├── images/         # Image gallery
│   │   │   ├── themes/         # Theme settings
│   │   │   ├── reports/        # Reports
│   │   │   └── settings/       # App settings
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles
│   ├── features/               # Feature modules
│   │   └── generation/         # Job generation feature
│   │       ├── api/            # API functions (jobs.ts)
│   │       ├── constants/      # Types & constants
│   │       ├── hooks/          # Custom hooks (WebSocket, polling)
│   │       ├── stores/         # Feature-specific stores
│   │       └── ui/             # UI components (wizard, results)
│   ├── shared/                 # Shared utilities and components
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui + custom components
│   │   │   │   └── connection-banner.tsx  # Global connection status
│   │   │   ├── layout/         # AppShell, Sidebar, Topbar
│   │   │   └── providers/      # QueryProvider, ThemeProvider
│   │   ├── lib/
│   │   │   ├── api-client.ts   # API client with error handling
│   │   │   ├── ws.ts           # WebSocket client
│   │   │   ├── env.ts          # Environment validation (Zod)
│   │   │   └── utils.ts        # Helper functions
│   │   ├── store/
│   │   │   ├── connection-store.ts  # Connection state (Zustand)
│   │   │   └── ui-store.ts     # UI state
│   │   └── ui/                 # Shared UI components
│   ├── i18n/                   # Internationalization config
│   └── test/                   # Test setup
├── messages/                   # Translation files (en.json, es.json)
├── e2e/                        # Playwright e2e tests
├── Dockerfile                  # Development Dockerfile
├── Dockerfile.prod             # Production Dockerfile (multi-stage)
└── public/                     # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm, yarn, or pnpm

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp env.development.example .env.local
   ```
   
   Edit `.env.local` with your configuration:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
   NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/ws
   NEXT_PUBLIC_APP_ENV=development
   ```

3. **Set up Git hooks (Husky):**
   ```bash
   npm run prepare
   ```

### Development

```bash
# Start development server
npm run dev

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Docker Production Build

The production Dockerfile (`Dockerfile.prod`) uses multi-stage builds:

```bash
# Build and run with Docker
docker build -f Dockerfile.prod \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api \
  --build-arg NEXT_PUBLIC_WS_BASE_URL=wss://your-domain.com/ws \
  -t intell-frontend .

docker run -p 3000:3000 intell-frontend
```

Or use docker-compose from the `infrastructure/` directory:

```bash
cd ../infrastructure
docker-compose -f docker-compose.prod.yml up frontend
```

## Testing

### Unit & Component Tests (Vitest)

```bash
# Run tests once
npm run test

# Run tests in watch mode
npm run test:watch
```

Tests are located in:
- `src/**/*.test.tsx` - Component tests
- `src/**/*.spec.tsx` - Unit tests

### E2E Tests (Playwright)

```bash
# Run e2e tests
npm run test:e2e

# Run e2e tests with UI
npm run test:e2e:ui
```

E2E tests are located in `e2e/`.

## Code Quality

### Pre-commit Hooks

Husky is configured to run lint-staged before each commit:
- ESLint checks and fixes
- Prettier formatting
- Test execution (if configured)

### Linting & Formatting

- **ESLint**: Configured with Next.js rules
- **Prettier**: Code formatting with Tailwind plugin
- **lint-staged**: Runs on staged files before commit

## Configuration

### Environment Variables

All environment variables are validated using Zod in `src/shared/lib/env.ts`:

- `NEXT_PUBLIC_API_BASE_URL` - Backend API base URL
- `NEXT_PUBLIC_WS_BASE_URL` - WebSocket base URL
- `NEXT_PUBLIC_APP_ENV` - Environment (development|staging|production)

### API Client

The API client (`src/shared/lib/api-client.ts`) includes typed errors and connection handling:

#### Error Types

```typescript
import { 
  ApiError,           // Base error class (status, data)
  ConnectionError,    // Network errors (status = 0)
  HttpError,          // HTTP errors (4xx, 5xx)
  CancelledError,     // Request cancelled/timeout (status = -1)
  isConnectionError,  // Type guard
  isCancelledError,   // Type guard
  getConnectionErrorMessage  // User-friendly message
} from "@/shared/lib/api-client";
```

#### Basic Usage

```typescript
import { apiClient } from "@/shared/lib/api-client";

// GET request
const data = await apiClient.get<User[]>("/users/");

// POST request
const newUser = await apiClient.post<User>("/users/", { name: "John" });

// With custom timeout
const data = await apiClient.get<Data>("/slow-endpoint/", { timeout: 30000 });
```

#### Error Handling

```typescript
import { isConnectionError, getConnectionErrorMessage } from "@/shared/lib/api-client";

try {
  await apiClient.post("/jobs/", data);
} catch (error) {
  if (isConnectionError(error)) {
    // Network error - server unreachable
    console.warn(getConnectionErrorMessage(error));
  } else if (isCancelledError(error)) {
    // Request was cancelled or timed out
  } else {
    // HTTP error (4xx, 5xx)
    console.error(error);
  }
}
```

#### Features

- **Automatic timeout**: 15s default, 60s for uploads
- **204/Empty responses**: Handled gracefully
- **JSON parse errors**: Safe fallback
- **Connection detection**: TypeError/DOMException → ConnectionError

### Connection State Management

Global connection state is managed with Zustand (`src/shared/store/connection-store.ts`):

```typescript
import { useConnectionStore } from "@/shared/store/connection-store";

function MyComponent() {
  const { isConnected, lastError, clearError } = useConnectionStore();
  
  // isConnected: true | false | null (unknown)
  // lastError: Error | null
  // clearError: () => void - resets to unknown state
}
```

The `ConnectionBanner` component (`src/shared/components/ui/connection-banner.tsx`) automatically shows when the backend is unreachable:

- Displays at the top of the page when `isConnected === false`
- Includes "Retry" button to manually check connection
- Auto-hides when a successful request is made

### React Query Configuration

React Query is configured in `src/shared/components/providers/query-provider.tsx` with:

- **Intelligent retry logic**:
  - Connection errors: 2 retries (queries), 1 retry (mutations)
  - Server errors (500+): 1 retry
  - Client errors (4xx): No retry
  - Cancelled: No retry
- **Global error handling**: Updates connection store on errors
- **Global success handling**: Marks connection as active on success

### WebSocket Client

WebSocket utility is in `src/shared/lib/ws.ts`:

```typescript
import { WSClient } from "@/shared/lib/ws";

const ws = new WSClient("/jobs/123/", {
  onMessage: (data) => {
    console.log("Received:", data);
  },
  onError: (error) => {
    console.error("Error:", error);
  },
});

ws.connect();
ws.send({ action: "subscribe" });
ws.disconnect();
```

### Job Generation Feature

The main feature (`src/features/generation/`) handles patent chart generation:

#### API Functions (`api/jobs.ts`)

```typescript
import { createJob, getJob, retryImageTask, cancelImageTask } from "@/features/generation/api/jobs";

// Create a new job with Excel file
const result = await createJob(formData);

// Get job details
const job = await getJob(jobId);

// Retry a failed image task
await retryImageTask(taskId);

// Cancel a running image task
await cancelImageTask(taskId);
```

#### Hooks

```typescript
import { useJobProgress } from "@/features/generation/hooks/useJobProgress";

function JobPage({ jobId }: { jobId: number }) {
  const { job, events, connectionStatus, isConnected } = useJobProgress(jobId);
  
  // job: Current job state (auto-updates via WebSocket)
  // events: Array of job events (START, PROGRESS, DONE, ERROR, etc.)
  // connectionStatus: "connecting" | "connected" | "disconnected" | "failed"
}
```

#### Components

- `GenerateWizard` - Multi-step wizard for job creation
- `JobProgress` - Real-time progress display
- `JobResults` - Display generated images with retry/cancel buttons

### Internationalization

i18n is configured with next-intl. Translations are in `messages/`:

```typescript
import { useTranslations } from "next-intl";

function MyComponent() {
  const t = useTranslations("common");
  return <h1>{t("appName")}</h1>;
}
```

### Theme (Dark Mode)

Theme is managed with next-themes:

```typescript
import { useTheme } from "next-themes";

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      Toggle theme
    </button>
  );
}
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Fix ESLint issues |
| `npm run format` | Format code with Prettier |
| `npm run format:check` | Check code formatting |
| `npm run test` | Run unit/component tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:e2e` | Run e2e tests |
| `npm run test:e2e:ui` | Run e2e tests with UI |
| `npm run prepare` | Set up Husky hooks |

## Technologies

| Category | Technology | Purpose |
|----------|------------|---------|
| Framework | **Next.js 16** | React framework with App Router |
| Language | **TypeScript 5** | Static typing |
| Styling | **Tailwind CSS 4** | Utility-first CSS |
| Components | **shadcn/ui** | Component library |
| Server State | **TanStack Query** | Data fetching, caching, retry logic |
| Client State | **Zustand** | Global state (connection, UI) |
| Forms | **React Hook Form + Zod** | Form handling with validation |
| i18n | **next-intl** | Internationalization |
| Theming | **next-themes** | Dark/light mode |
| Notifications | **Sonner** | Toast notifications |
| Testing | **Vitest + Playwright** | Unit, component, E2E tests |
| Code Quality | **ESLint + Prettier + Husky** | Linting, formatting, git hooks |
| Container | **Docker** | Production deployment |

## Development Guidelines

1. **Feature-first structure**: Organize code by feature in `src/features/`
2. **Shared code**: Put reusable code in `src/shared/`
3. **TypeScript**: Use TypeScript for all components and utilities
4. **Components**: Use shadcn/ui components from `src/shared/components/ui/`
5. **State**: Use TanStack Query for server state, Zustand for client state
6. **Forms**: Use React Hook Form with Zod validation
7. **Styling**: Use Tailwind CSS classes
8. **i18n**: All user-facing text should be translated

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [next-intl](https://next-intl-docs.vercel.app/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod](https://zod.dev/)

## License

Private - Intell.AI Project

## Design & UX Patterns

### Design System (`src/shared/design-system/`)
- **tokens.ts**: Central design tokens (colors, typography, spacing, shadows)
- **patterns.ts**: Documented UI/UX patterns with code examples

### Tokens & Styles
- **Breakpoints**: Desktop-first optimizations (max-w-7xl)
- **Colors**: Defined in `globals.css` (HSL variables) + Tailwind config
- **Spacing**: Standard layout padding `p-4 md:p-6`
- **Terminal colors**: Dedicated palette for log displays (slate-950 bg, colored levels)
- **Status colors**: Consistent border/bg tints for running/success/failed states

### Shared Components (`src/shared/ui/`)
- `PageHeader`: Standard top-of-page header.
- `StateBlock`: Feedback states (loading, empty, error, success).
- `StatusBadge`: Consistent status coloring (PENDING, RUNNING, SUCCESS, etc).
- `ProgressPanel`: Progress bar with step info.
- `EventTimeline`: Vertical list of logs/events.
- `GalleryGrid`: Responsive grid for image cards.
- `Stepper`: Multi-step wizard indicator with completion state.

### Feature Components (`src/features/generation/ui/`)
- `ActivityLog`: Collapsible terminal-style event log.
- `JobProgress`: Progress card with task summary badges.
- `JobResults`: Generated images with actions.

### UI/UX Patterns (see `design-system/patterns.ts`)

#### Progressive Disclosure
Order content by priority:
1. **Primary**: Always visible (status, progress, results)
2. **Secondary**: Visible but de-emphasized (task details)
3. **Tertiary**: Collapsed by default (logs, debug info)

#### Collapsible Sections
For secondary information users may want to see:
- Default: collapsed
- Full-width clickable toggle
- ChevronRight/ChevronDown icons
- "Click to expand/collapse" hint

#### Status Headers
For page/section headers with status:
- Icon in colored circle
- Title with tracking-tight
- Status badges inline
- Action buttons aligned right

#### Task Items
List items with status indication:
- Border color changes by status
- Background tint by status
- Progress bar only when running

#### Terminal Log
For event/log output:
- Dark background (slate-950)
- Monospace font, small text
- Colored levels (ERROR=red, WARNING=amber, INFO=blue)
- Auto-scroll with manual override

#### Badge Variants
- `default`: Success, completed
- `secondary`: Neutral, in-progress, counts
- `destructive`: Errors, failures
- `outline`: Supplementary info

### App Shell
Responsive sidebar + topbar layout using `AppShell` component.
- **Desktop**: Fixed sidebar.
- **Mobile**: Collapsible sidebar (Sheet).

## Mock Mode

For development without a backend, enable mock mode:
1. Create/Edit `.env.local`
2. Set `NEXT_PUBLIC_USE_MOCKS=true`
3. Restart dev server

This will activate `mockJob.ts` data in Dashboard and Generate pages.

## Conventions for New Features

1. **Feature structure**: Create directory in `src/features/[feature-name]/` with:
   - `api/` - API functions
   - `hooks/` - Custom hooks
   - `ui/` - UI components
   - `constants/` - Types, enums, constants
   - `stores/` - Feature-specific Zustand stores (if needed)

2. **Page components**: Use `PageHeader` for title.

3. **Shared imports**: Import from `@/shared/ui`, `@/shared/lib`, `@/shared/store`.

4. **Error handling**: 
   - Use `isConnectionError()` and `isCancelledError()` for error checks
   - Connection errors are handled globally (banner + toast)
   - Add local try/catch only for specific UX needs

5. **Types**: Define in `src/shared/types/backend.ts` for backend entities.

6. **API calls**: Use `apiClient` from `@/shared/lib/api-client.ts`.

7. **Real-time updates**: Use WebSocket hooks for progress tracking.
