---
applyTo: "frontend/**"
---

# Frontend Instructions

## Architecture

Pages → Components → Hooks → Services → Types. Components never call API directly.

- Pages (`src/app/`): App Router routes (landing, dashboard, results/[id])
- Components (`src/components/`): Feature-based folders (upload/, results/, documents/)
- Hooks (`src/hooks/`): TanStack Query wrappers — one hook per data operation
- Services (`src/services/api.ts`): Centralized Axios client, all HTTP calls go through here
- Types (`src/types/document.ts`): TypeScript interfaces mirroring backend Pydantic schemas exactly

## TypeScript Rules

- No `any` types ever — use `unknown` if truly unknown
- Every variable, parameter, and return value must be explicitly typed
- Union types as string literals: `"pending" | "processing" | "completed" | "failed"`
- Import alias: `@/*` maps to `src/*`

## Data Fetching Patterns

Use TanStack React Query for all server state. Components never call API functions directly — always through hooks.

### Query Hook (polling)

```typescript
"use client";
import { useQuery } from "@tanstack/react-query";

export function useMyData(id: string) {
  return useQuery({
    queryKey: ["my-data", id],
    queryFn: () => fetchMyData(id),
    enabled: Boolean(id),
    refetchInterval: (data) => {
      const status = data?.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });
}
```

### Mutation Hook

```typescript
"use client";
import { useMutation } from "@tanstack/react-query";

export function useMyAction() {
  const mutation = useMutation({ mutationFn: myApiCall });
  return {
    execute: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: (mutation.error as Error | null) ?? null,
    result: mutation.data ?? null,
  };
}
```

## Component Rules

- Single responsibility: UploadZone only handles upload UI, TableRenderer only renders tables, FieldsRenderer only renders key-value fields
- ResultViewer accepts optional `renderers` prop to swap rendering implementations (Open/Closed principle)
- Use shadcn/ui components for consistency (button, card, badge, progress, table, dialog, toast)
- Use `react-dropzone` for file uploads, accept only `application/pdf`
- Use `lucide-react` for icons
- Use `sonner` for toast notifications

## Adding a New Component

1. Create in appropriate `src/components/` subdirectory
2. One component, one concern (single responsibility)
3. Use shadcn/ui for UI consistency
4. If data-fetching needed → create hook in `src/hooks/`
5. Never call API directly from component

## Adding a New Data Operation

1. Add TypeScript types in `src/types/` mirroring backend schemas
2. Add API function in `src/services/api.ts`
3. Create custom hook in `src/hooks/`
4. Use hook in component

## Naming Conventions

- Component files: `PascalCase` (`UploadZone.tsx`)
- Hook files: `camelCase` with `use` prefix (`useUpload.ts`)
- Service files: `camelCase` (`api.ts`)
- Type files: `camelCase` (`document.ts`)
- Interfaces/Types: `PascalCase` (`Document`, `DocumentStatus`)
- Functions/Hooks: `camelCase` (`useDocumentStatus()`)
- CSS classes: `kebab-case` (`.upload-zone`)

## Layout

`src/app/layout.tsx` wraps children in `QueryClientProvider`. All pages inherit this provider.

## Package Manager

This project uses `pnpm`. Always use `pnpm install`, `pnpm add`, `pnpm dev`.

## Environment

`NEXT_PUBLIC_API_URL` in `.env.local` — points to backend (default `http://localhost:8000`). Never commit `.env.local`.

## Troubleshooting

- Can't reach backend → verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`
- `node_modules` conflict → anonymous volume `/app/node_modules` in docker-compose prevents host overwrite
- Hydration errors → ensure `"use client"` directive on components using hooks/state
