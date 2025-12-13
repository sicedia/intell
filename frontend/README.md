# Intell.AI Frontend

Next.js application with TypeScript, App Router, and modern tooling for the Intell.AI platform.

## Features

- ⚡ **Next.js 16** with App Router
- 🎨 **Tailwind CSS** + **shadcn/ui** components
- 🌐 **i18n** (English/Spanish) with next-intl
- 🌓 **Dark mode** with next-themes
- 🔄 **TanStack Query** for server state
- 🐻 **Zustand** for client state
- 📝 **React Hook Form** + **Zod** for forms
- 📊 **Excel upload** (react-dropzone + xlsx)
- 🔌 **WebSocket client** utility
- ✅ **Testing** (Vitest + Playwright)
- 🎯 **Code quality** (ESLint + Prettier + Husky)

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── [locale]/           # Localized routes
│   │   │   ├── dashboard/
│   │   │   ├── generate/
│   │   │   ├── images/
│   │   │   ├── themes/
│   │   │   ├── reports/
│   │   │   └── settings/
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles
│   ├── features/               # Feature modules (to be implemented)
│   ├── shared/                 # Shared utilities and components
│   │   ├── components/         # Reusable components
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── layout/         # Layout components
│   │   │   └── providers/      # Context providers
│   │   ├── lib/                # Utilities
│   │   │   ├── api-client.ts   # API client
│   │   │   ├── ws.ts           # WebSocket client
│   │   │   ├── env.ts          # Environment validation
│   │   │   └── utils.ts        # Helper functions
│   │   └── store/              # Zustand stores
│   ├── i18n/                   # Internationalization config
│   └── test/                     # Test setup
├── messages/                    # Translation files
├── e2e/                        # Playwright e2e tests
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
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
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

The API client is configured in `src/shared/lib/api-client.ts`:

```typescript
import { apiClient } from "@/shared/lib/api-client";

// GET request
const data = await apiClient.get<User[]>("/users/");

// POST request
const newUser = await apiClient.post<User>("/users/", { name: "John" });
```

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

- **Next.js 16** - React framework with App Router
- **TypeScript** - Static typing
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Component library
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **next-intl** - Internationalization
- **next-themes** - Theme management
- **Vitest** - Unit testing
- **Playwright** - E2E testing
- **ESLint** - Linting
- **Prettier** - Code formatting
- **Husky** - Git hooks

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

### Tokens & Styles
- **Breakpoints**: Desktop-first optimizations (max-w-7xl)
- **Colors**: Defined in `globals.css` (HSL variables) + Tailwind config
- **Spacing**: Standard layout padding `p-4 md:p-6`

### Shared Components (`src/shared/ui/`)
- `PageHeader`: Standard top-of-page header.
- `StateBlock`: Feedback states (loading, empty, error, success).
- `StatusBadge`: Consistent status coloring (PENDING, RUNNING, SUCCESS, etc).
- `ProgressPanel`: Progress bar with step info.
- `EventTimeline`: Vertical list of logs/events.
- `GalleryGrid`: Responsive grid for image cards.

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

## Conv Conventions for New Features

1. Create feature directory in `src/features/[feature-name]`.
2. Use `PageHeader` for title.
3. Import shared UI from `@/shared/ui`.
4. If logic is complex, create a dedicated component (e.g. `Wizard`).
5. define types in `src/shared/types/backend.ts` if they match backend entities.
