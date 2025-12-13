# Frontend - Next.js Application

Next.js frontend application for the Intelli monorepo with TypeScript, Tailwind CSS, React Query, and Zustand.

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
frontend/
├── app/              # Next.js App Router
│   ├── page.tsx      # Home page
│   ├── layout.tsx    # Root layout
│   └── globals.css   # Global styles
├── public/           # Static files
├── package.json      # Dependencies
└── tsconfig.json     # TypeScript configuration
```

## Technologies

- **Next.js 16.0.6** - React framework with App Router
- **React 19.2.0** - UI library
- **TypeScript 5** - Static typing
- **Tailwind CSS 4** - Utility-first CSS framework
- **@tanstack/react-query 5.90.11** - Server state management
- **Zustand 5.0.9** - Client state management
- **Axios 1.13.2** - HTTP client

## API Integration

The frontend is configured to communicate with the Django backend at `http://localhost:8000/api`.

### Example: Setting up API client

Create `lib/api.ts`:

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

### Example: Using React Query

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const { data } = await api.get('/items/');
      return data;
    },
  });
}
```

### Example: Using Zustand

```typescript
import { create } from 'zustand';

interface Store {
  count: number;
  increment: () => void;
}

export const useStore = create<Store>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}));
```

## Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

## Development

- Pages and components are in the `app/` directory
- Use the App Router (not Pages Router)
- All components should use TypeScript
- Styling is done with Tailwind CSS
- Server state: React Query
- Client state: Zustand
- HTTP requests: Axios

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS](https://tailwindcss.com/docs)

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
