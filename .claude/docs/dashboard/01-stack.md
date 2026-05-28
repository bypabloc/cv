# 01 — Stack: Next.js 16 + React 18 + TypeScript + Biome

[< README](README.md) | [Siguiente: 02-structure >](02-structure.md)

## Next.js 16 — esencial 2025-2026

Release: **Octubre 2025**. Breaking changes relevantes:

| Cambio | Impacto en este dashboard |
|--------|---------------------------|
| Turbopack default | Dev server 5-10x mas rapido. Sin custom webpack config. |
| Async Request APIs (`params`, `cookies()`) | No aplica (Client Components). |
| `middleware.ts` → `proxy.ts` | No aplica (export mode no soporta ninguno). |
| React 19 compat opcional | Quedamos en React 18.3 por ecosystem (Tanstack v5, react-hook-form). |
| `output: 'export'` estable | Soportado en App Router. Funcional. NO deprecated en v17 roadmap. |

## `next.config.ts` canonico del dashboard

```typescript
import type {NextConfig} from 'next'

const nextConfig: NextConfig = {
  // SPA estatica
  output: 'export',

  // Cloudflare Pages no optimiza imagenes (no hay server runtime)
  images: {
    unoptimized: true,
  },

  // Cloudflare Pages prefiere paths con slash
  trailingSlash: true,

  // No exponer "Next.js" en headers
  poweredByHeader: false,

  // Source maps en prod opcional (helps debugging)
  productionBrowserSourceMaps: false,

  // Eslint: NO se usa (Biome lo reemplaza). Suprimir warning del build.
  eslint: {
    ignoreDuringBuilds: true,
  },

  typescript: {
    tsconfigPath: './tsconfig.json',
    // ignoreBuildErrors: false  (default — fail on TS errors)
  },
}

export default nextConfig
```

## `package.json` del dashboard

```jsonc
{
  "name": "@portfolio/dashboard",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "preview": "npx serve out -p 3000",
    "lint": "biome check .",
    "lint:fix": "biome check --write .",
    "format": "biome format --write .",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  },
  "dependencies": {
    "next": "^16.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    // UI
    "@radix-ui/react-slot": "^1.1.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.0",
    "lucide-react": "^0.479.0",
    "next-themes": "^0.4.4",
    // Data + state
    "@tanstack/react-query": "^5.62.0",
    "@tanstack/react-query-persist-client": "^5.62.0",
    "@tanstack/query-sync-storage-persister": "^5.62.0",
    "@tanstack/react-table": "^8.20.5",
    "@tanstack/react-virtual": "^3.10.8",
    "zustand": "^5.0.2",
    "lz-string": "^1.5.0",
    // Forms + validation
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^3.9.1",
    "zod": "^3.24.1",
    // Charts (via shadcn chart, depende de Recharts)
    "recharts": "^2.15.0",
    // Toasts
    "sonner": "^1.7.1",
    // JWT decode (solo para leer exp client-side, NO verificacion)
    "jwt-decode": "^4.0.0",
    // Turnstile widget React
    "@marsidev/react-turnstile": "^1.1.0"
  },
  "devDependencies": {
    "@biomejs/biome": "^2.0.0",
    "@tanstack/react-query-devtools": "^5.62.0",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/node": "^24.0.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "happy-dom": "^16.5.0",
    "msw": "^2.7.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0",
    "postcss": "^8.5.0",
    "typescript": "^6.0.0",
    "vitest": "^2.1.8"
  },
  "engines": {
    "node": ">=24",
    "pnpm": "11.0.9"
  }
}
```

## `tsconfig.json`

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "allowImportingTsExtensions": false,
    "noEmit": true,
    "isolatedModules": true,
    "incremental": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,

    // strict
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,

    "plugins": [{"name": "next"}],

    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "src/**/*",
    ".next/types/**/*.ts"
  ],
  "exclude": [
    "node_modules",
    "out",
    ".next"
  ]
}
```

> Importante: el alias `@/*` debe coincidir EXACTO con `components.json`
> de shadcn (proximo capitulo). Si divergen, shadcn CLI escribe en
> carpetas incorrectas.

## `biome.json` (override del root)

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "extends": ["../biome.json"],
  "files": {
    "ignore": [
      "node_modules",
      ".next",
      "out",
      "coverage"
    ]
  },
  "overrides": [
    {
      "include": ["src/components/ui/**/*.tsx"],
      "linter": {
        "rules": {
          "suspicious": {
            "noExplicitAny": "off",
            "noArrayIndexKey": "off"
          },
          "complexity": {
            "noUselessFragments": "off"
          },
          "style": {
            "useImportType": "off"
          }
        }
      }
    },
    {
      "include": ["src/app/**/page.tsx", "src/app/**/layout.tsx"],
      "linter": {
        "rules": {
          "style": {
            "noDefaultExport": "off"
          }
        }
      }
    }
  ]
}
```

> Por que ignorar reglas strict en `src/components/ui/**`: shadcn usa
> `any` para el Slot pattern y `noUselessFragments` falla en wrappers
> de Radix. Ignorar localmente preserva el resto strict.

## Reglas React + Next que Biome NO cubre nativamente

| Regla | Biome | Alternativa |
|-------|-------|-------------|
| `react/jsx-key` | ✅ cubierto | — |
| `react-hooks/rules-of-hooks` | ✅ cubierto | — |
| `react-hooks/exhaustive-deps` | ✅ cubierto (`useExhaustiveDependencies`) | — |
| `next/no-html-link-for-pages` | ❌ no cubierto | Review humano en PR + el lint del root puede detectar `<a href="/...">` si Biome agrega regla |
| `next/no-img-element` | ❌ no cubierto | Review humano; el dashboard casi no usa imagenes |
| `jsx-a11y/*` | ⚠ parcial | Radix da accesibilidad de base. Lighthouse a11y en review manual |

Decision: aceptable. El dashboard tiene pocos `<Link>` y casi cero
`<img>`. Las reglas faltantes se cubren en review humano + Lighthouse
en preview.

## Tailwind v4 setup minimo

`postcss.config.mjs`:

```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

`src/styles/globals.css`:

```css
@import "tailwindcss";

/* Importar fonts self-hosted (mismas del DS del monorepo) */
@import "@fontsource/space-grotesk/400.css";
@import "@fontsource/space-grotesk/500.css";
@import "@fontsource/space-grotesk/600.css";
@import "@fontsource/space-grotesk/700.css";
@import "@fontsource/space-mono/400.css";
@import "@fontsource/space-mono/700.css";

/* Tokens compartidos con el monorepo (sincronizar con design-system.md) */
@theme {
  --font-sans: "Space Grotesk", -apple-system, system-ui, sans-serif;
  --font-mono: "Space Mono", Menlo, monospace;

  /* Spacing base 4px ya viene de Tailwind v4 */

  /* Radius */
  --radius-xs: 0.375rem;
  --radius-sm: 0.5rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --radius-pill: 9999px;
}

/* Modo dark (base) + light (toggle) — usar attribute data-theme */
:root {
  color-scheme: dark;
  --background: 0 0% 4%;
  --foreground: 60 9% 98%;
  --primary: 217 91% 60%;
  --primary-foreground: 0 0% 100%;
  --secondary: 215 27% 17%;
  --secondary-foreground: 60 9% 98%;
  --muted: 215 27% 14%;
  --muted-foreground: 217 11% 65%;
  --accent: 215 27% 14%;
  --accent-foreground: 60 9% 98%;
  --destructive: 0 84% 60%;
  --destructive-foreground: 60 9% 98%;
  --border: 215 27% 17%;
  --input: 215 27% 17%;
  --ring: 217 91% 60%;
  --card: 215 27% 8%;
  --card-foreground: 60 9% 98%;
  --popover: 215 27% 8%;
  --popover-foreground: 60 9% 98%;
}

[data-theme="light"] {
  color-scheme: light;
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --primary: 217 91% 50%;
  --primary-foreground: 0 0% 100%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  --muted-foreground: 215 16% 47%;
  --accent: 210 40% 96%;
  --accent-foreground: 222 47% 11%;
  --destructive: 0 84% 60%;
  --destructive-foreground: 60 9% 98%;
  --border: 214 32% 91%;
  --input: 214 32% 91%;
  --ring: 217 91% 50%;
  --card: 0 0% 100%;
  --card-foreground: 222 47% 11%;
  --popover: 0 0% 100%;
  --popover-foreground: 222 47% 11%;
}

/* Map Tailwind utilities a los tokens HSL (compat shadcn) */
@theme inline {
  --color-background: hsl(var(--background));
  --color-foreground: hsl(var(--foreground));
  --color-primary: hsl(var(--primary));
  --color-primary-foreground: hsl(var(--primary-foreground));
  --color-secondary: hsl(var(--secondary));
  --color-secondary-foreground: hsl(var(--secondary-foreground));
  --color-muted: hsl(var(--muted));
  --color-muted-foreground: hsl(var(--muted-foreground));
  --color-accent: hsl(var(--accent));
  --color-accent-foreground: hsl(var(--accent-foreground));
  --color-destructive: hsl(var(--destructive));
  --color-destructive-foreground: hsl(var(--destructive-foreground));
  --color-border: hsl(var(--border));
  --color-input: hsl(var(--input));
  --color-ring: hsl(var(--ring));
  --color-card: hsl(var(--card));
  --color-card-foreground: hsl(var(--card-foreground));
  --color-popover: hsl(var(--popover));
  --color-popover-foreground: hsl(var(--popover-foreground));
}

@layer base {
  *, *::before, *::after {
    box-sizing: border-box;
    border-color: hsl(var(--border));
  }
  body {
    background: hsl(var(--background));
    color: hsl(var(--foreground));
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
  }
}

/* Respect prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## `src/lib/env.ts` — type-safe env vars

```typescript
import {z} from 'zod'

const envSchema = z.object({
  NEXT_PUBLIC_API_ENDPOINT: z
    .string()
    .url()
    .describe('Lambda backend base URL'),
  NEXT_PUBLIC_TURNSTILE_SITEKEY: z
    .string()
    .min(10)
    .describe('Cloudflare Turnstile sitekey (publico)'),
  NEXT_PUBLIC_DASHBOARD_URL: z
    .string()
    .url()
    .describe('Self URL del dashboard, para callbacks'),
  NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS: z.coerce
    .number()
    .int()
    .min(5_000)
    .max(300_000)
    .default(30_000)
    .describe('Cuanto antes del exp del JWT disparar el refresh proactivo'),
})

export const env = envSchema.parse({
  NEXT_PUBLIC_API_ENDPOINT: process.env.NEXT_PUBLIC_API_ENDPOINT,
  NEXT_PUBLIC_TURNSTILE_SITEKEY: process.env.NEXT_PUBLIC_TURNSTILE_SITEKEY,
  NEXT_PUBLIC_DASHBOARD_URL: process.env.NEXT_PUBLIC_DASHBOARD_URL,
  NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS: process.env.NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS,
})

export type Env = z.infer<typeof envSchema>
```

> Import `env` desde el resto del codigo: `import {env} from '@/lib/env'`.
> Si falla la validacion, Next 16 fail al build (deseado).

## `next-env.d.ts` adicional para vars

```typescript
// src/env.d.ts (complementa next-env.d.ts)
declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_API_ENDPOINT: string
    NEXT_PUBLIC_TURNSTILE_SITEKEY: string
    NEXT_PUBLIC_DASHBOARD_URL: string
    NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS?: string
  }
}
```

## `public/_redirects` para Cloudflare Pages

```text
# SPA fallback: rutas dinamicas client-side
# Excepcion: /api/* devuelve 404 explicito (no caer a SPA)
/api/* /404 404
/* /index.html 200
```

## `public/_headers` para Cloudflare Pages

```text
# Cache: assets de Next con hash en el nombre → inmutable 1 ano
/_next/static/*
  Cache-Control: public, max-age=31536000, immutable

# Fonts self-hosted
/fonts/*
  Cache-Control: public, max-age=31536000, immutable

# HTML pages: no cache (para que redeploys propaguen rapido)
/
  Cache-Control: no-cache, must-revalidate
/*.html
  Cache-Control: no-cache, must-revalidate

# Security headers (heredar politica del monorepo)
/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.portfolio.dev.the-full-stack.com https://api.portfolio.stage.the-full-stack.com https://api.portfolio.the-full-stack.com; frame-src https://challenges.cloudflare.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; require-trusted-types-for 'script'
```

> `'wasm-unsafe-eval'` se requiere para Turbopack runtime en client.
> `connect-src` lista los 3 endpoints API (dev/stage/prod). Pages
> serv el _headers per project, podriamos optimizar a 1 endpoint por
> env si necesario.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Hardcodear `process.env.NEXT_PUBLIC_*` sin validar | Build pasa, runtime crash | Import desde `@/lib/env` (Zod) |
| `appDir: false` o Pages Router | Default es App Router; no hay razon de regresar | App Router |
| Custom webpack config | Turbopack es default, requiere migrar | Aceptar Turbopack |
| `eslint` config en parallel | Biome es la decision | Solo `biome.json` |
| Olvidar `'use client'` en page con `useState` | Server Component error | Primera linea |
| Cambiar `output` a `standalone` o `default` | Necesita server runtime | Mantener `'export'` |
| Olvidar trailing slash | Cloudflare Pages redirect a slash, perf hit | `trailingSlash: true` |

## Referencias

- Next.js 16 release: https://nextjs.org/blog/next-16
- Static Exports: https://nextjs.org/docs/app/guides/static-exports
- Biome v2: https://biomejs.dev/blog/biome-v2-0-beta/
- Tailwind v4: https://tailwindcss.com/blog/tailwindcss-v4

[< README](README.md) | [Siguiente: 02-structure >](02-structure.md)
