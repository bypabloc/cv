# 01 — Stack: Next.js 16.2.6 + React 19.2.6 + TypeScript + Biome

[< README](README.md) | [Siguiente: 02-structure >](02-structure.md)

## Next.js 16.2.6 — esencial mayo 2026

| Release    | Fecha                                  | Highlights |
| ---------- | -------------------------------------- | ---------- |
| **16.0**   | Oct 21, 2025 (GA)                      | Turbopack stable + default, `proxy.ts` reemplaza `middleware.ts`, React 19 forzado, async APIs (`cookies()`, `headers()`, `params`), Cache Components (`'use cache'`) |
| **16.1**   | Dec 2025                               | Filesystem caching en Turbopack dev, bundle analyzer built-in, Node debugger mejorado, React Compiler pasa de experimental a estable |
| **16.2**   | Mar 2026                               | ~400% faster `next dev` startup, ~50% faster rendering, Build Adapters API stable, browser log forwarding |
| **16.2.6** | **May 7, 2026** (latest, LTS candidato) | 13 security fixes (7 high, 4 moderate, 2 low), upstream React patches, DoS mitigations, proxy bypass fixes |

### Cambios relevantes al admin SPA

| Cambio | Impacto |
|--------|---------|
| **Turbopack default** | Dev server 5-10x mas rapido. Sin custom webpack config. |
| **React 19.2 obligatorio** | Hooks nuevos disponibles (`useActionState`, `useFormStatus`, `useOptimistic`, etc.). Compiler stable. |
| **Async Request APIs** | NO aplica (Client Components only). `useSearchParams()` necesita `<Suspense>` boundary. |
| **`middleware.ts` → `proxy.ts`** | NO aplica (export mode no corre ninguno). Auth guard es Client Component. |
| **`'use cache'` directive** | Server-only, NO aplica al admin. |
| **`output: 'export'` estable** | Soportado en App Router. NO deprecated en v17 roadmap. |

### React 19.2 features integrados en Next.js 16

- **View Transitions API**: animaciones en navegacion / updates dentro de `<Transition>`.
- **`useEffectEvent()`**: extrae logica no-reactiva de Effects.
- **Activity Component**: render "background activity" con `display: none` while maintaining state.
- **React Compiler stable**: auto-memoization sin `useMemo`/`useCallback` boilerplate.

## `next.config.ts` canonico del admin

```typescript
import type {NextConfig} from 'next'

const nextConfig: NextConfig = {
  // SPA estatica para Cloudflare Pages
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

  // React Compiler stable en Next 16 — auto-memoization
  reactCompiler: true,
}

export default nextConfig
```

> **Nota**: el flag `reactCompiler: true` en Next 16.2.x es estable
> (paso de `experimental.reactCompiler` en 16.1 a campo top-level en
> 16.2). Internamente Next.js SWC aplica `babel-plugin-react-compiler`
> selectivamente, mas eficiente que correr Babel directo.

## `package.json` del admin

Versiones exactas mayo 2026 (ver tabla en
`.claude/skills/admin-stack/SKILL.md` para fuente):

```jsonc
{
  "name": "@portfolio/admin",
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
    "next": "^16.2.6",
    "react": "^19.2.6",
    "react-dom": "^19.2.6",

    // UI / Radix / shadcn helpers
    "@radix-ui/react-slot": "^1.1.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.4.0",
    "lucide-react": "^0.416.0",
    "next-themes": "^0.4.8",

    // Tanstack stack
    "@tanstack/react-query": "^5.52.3",
    "@tanstack/react-query-persist-client": "^5.52.3",
    "@tanstack/query-sync-storage-persister": "^5.52.3",
    "@tanstack/react-table": "^8.20.5",
    "@tanstack/react-virtual": "^3.5.1",

    // State
    "zustand": "^5.0.14",
    "lz-string": "^1.5.0",

    // Forms + validation
    "react-hook-form": "^7.53.0",
    "@hookform/resolvers": "^3.4.2",
    "zod": "^3.24.1",

    // Charts (via shadcn add chart) — Recharts requiere react-is matcheado
    "recharts": "^2.14.2",
    "react-is": "19.2.6",

    // Toasts
    "sonner": "^1.7.2",

    // JWT decode (solo client-side para leer exp)
    "jwt-decode": "^4.0.0",

    // Turnstile widget React
    "@marsidev/react-turnstile": "^1.2.5"
  },
  "devDependencies": {
    "@biomejs/biome": "^2.0.0",
    "@tanstack/react-query-devtools": "^5.52.3",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/node": "^20.18.2",
    "@types/react": "^19.0.7",
    "@types/react-dom": "^19.0.7",
    "@vitejs/plugin-react": "^4.3.3",
    "babel-plugin-react-compiler": "^19.0.0-beta.17",
    "happy-dom": "^16.5.1",
    "msw": "^2.3.2",
    "playwright": "^1.48.2",
    "@playwright/test": "^1.48.2",
    "tailwindcss": "^4.1.4",
    "@tailwindcss/postcss": "^4.1.4",
    "postcss": "^8.4.50",
    "typescript": "^6.0.6",
    "vitest": "^2.2.5"
  },
  "engines": {
    "node": ">=24",
    "pnpm": "11.0.9"
  },
  // Critico: Recharts internamente importa react-is.
  // Force el alias a 19.2.6 para evitar mismatch con React 19.
  "pnpm": {
    "overrides": {
      "react-is": "19.2.6"
    }
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

> Por que ignorar reglas strict en `src/components/ui/**`: shadcn 2.x
> (oct 2025+) ya genera componentes **sin `forwardRef`** (React 19
> ref-as-prop), pero algunos patterns todavia chocan con reglas strict
> de Biome (Slot composition con `any` en types polimorficos, fragments
> en wrappers de Radix). Ignorar localmente preserva el resto strict.

## React 19 + Biome v2 — reglas relevantes

| Regla | Biome v2 | Notas para React 19 |
|-------|----------|---------------------|
| `react/jsx-key` | ✅ cubierto | — |
| `react-hooks/rules-of-hooks` | ✅ cubierto | El Compiler las enforces tambien |
| `react-hooks/exhaustive-deps` | ✅ cubierto (`useExhaustiveDependencies`) | Compiler analiza esto automaticamente |
| `next/no-html-link-for-pages` | ❌ no cubierto | Review humano en PR (el admin tiene pocos `<Link>` candidatos a error) |
| `next/no-img-element` | ❌ no cubierto | Review humano (casi cero `<img>` en el admin) |
| `jsx-a11y/*` | ⚠ parcial | Radix da accesibilidad base; Lighthouse a11y en review manual |
| `noForwardRef` (custom) | ❌ no cubierto | Review humano — toda creacion de component nuevo debe ser sin `forwardRef` |

## React Compiler — habilitar

`reactCompiler: true` en `next.config.ts` activa el compiler. Lo que
hace:

1. Analisis estatico de cada funcion componente + hooks.
2. Emite equivalentes memoizados (memo slots manejados internamente).
3. Reemplaza la necesidad de `React.memo`, `useMemo`, `useCallback` en
   90%+ de los casos.

**Requisitos**:
- Strict Mode activo en root (lo cumple Next 16 por default).
- Rules of React respetadas (Compiler las enforces — si no, omite el
  componente).
- `babel-plugin-react-compiler` instalado como devDep.

**Opt-out per file** (solo si rompe algo medido):

```tsx
'use no memo'

export function ComponenteRaro() {
  // Compiler NO lo optimiza
}
```

**Benefits esperados en el admin**:
- –20–40% re-renders innecesarios en tabs con filtros + Tanstack Table
  + Tanstack Virtual (medido en dashboards 2026).
- +5–15% build time (overhead de Babel; menor con Next SWC).

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

/* Tokens compartidos con el monorepo */
@theme {
  --font-sans: "Space Grotesk", -apple-system, system-ui, sans-serif;
  --font-mono: "Space Mono", Menlo, monospace;

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

> Tailwind v4 (4.1.4 mayo 2026) es **5x mas rapido en full builds** y
> **100x en incrementales** (medido en microsegundos) vs v3. Config
> CSS-first (sin `tailwind.config.ts`).

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
    .describe('Self URL del admin, para callbacks'),
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
    NEXT_PUBLIC_USE_MSW?: string
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
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.portfolio.dev.the-full-stack.com https://api.portfolio.stage.the-full-stack.com https://api.portfolio.the-full-stack.com https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'
```

> `'wasm-unsafe-eval'` se requiere para el runtime de Next/Turbopack en
> client. `'unsafe-inline'` en `script-src` es OBLIGATORIO con
> `output:'export'`: Next inyecta los inline `<script>` que hidratan el
> arbol RSC (`self.__next_f.push([...])`) + el anti-FOUC de next-themes.
> Sin server runtime NO hay nonce y los hashes cambian por build; sin
> `'unsafe-inline'` el browser bloquea esos scripts -> el RSC stream se
> corta con "Connection closed" -> la app se cuelga. `'unsafe-eval'` (eval
> de strings arbitrarios) sigue prohibido. NO usar
> `require-trusted-types-for 'script'`: Next/Turbopack inyecta scripts sin
> Trusted Types policy y romperia la hidratacion.
> `connect-src` lista los 3 endpoints API + `challenges.cloudflare.com`
> (Turnstile). CSP estricta sin `'unsafe-inline'` ni `'unsafe-eval'` en
> scripts — defense in depth para auth en `localStorage`.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Pinear `react@^18.x` en `package.json` | Next 16.x requiere React 19 minimo | `react@^19.2.6` |
| Hardcodear `process.env.NEXT_PUBLIC_*` sin validar | Build pasa, runtime crash | Import desde `@/lib/env` (Zod) |
| `appDir: false` o Pages Router | Default es App Router; no hay razon de regresar | App Router |
| Custom webpack config | Turbopack es default, requiere migrar | Aceptar Turbopack |
| `eslint` config en parallel | Biome es la decision | Solo `biome.json` |
| Olvidar `'use client'` en page con `useState` | Server Component error | Primera linea |
| Cambiar `output` a `standalone` o `default` | Necesita server runtime | Mantener `'export'` |
| Olvidar trailing slash | Cloudflare Pages redirect a slash, perf hit | `trailingSlash: true` |
| Olvidar `reactCompiler: true` | Sin auto-memoization, peor perf | Habilitarlo (stable en 16) |
| Olvidar `react-is` override | Recharts internamente importa, falla por mismatch | `"pnpm.overrides": {"react-is": "19.2.6"}` |
| `experimental.reactCompiler` (sintaxis vieja) | En 16.2 paso a campo top-level | `reactCompiler: true` (sin `experimental`) |

## Referencias

- Next.js 16: https://nextjs.org/blog/next-16
- Next.js 16.1: https://nextjs.org/blog/next-16-1
- Next.js 16.2: https://nextjs.org/blog/next-16-2
- Static Exports: https://nextjs.org/docs/app/guides/static-exports
- React 19 blog: https://react.dev/blog
- React Compiler: https://react.dev/learn/react-compiler/installation
- Biome v2: https://biomejs.dev/blog/biome-v2-0-beta/
- Tailwind v4: https://tailwindcss.com/blog/tailwindcss-v4

[< README](README.md) | [Siguiente: 02-structure >](02-structure.md)
