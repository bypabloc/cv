---
name: admin-stack
description: >
  Admin SPA stack reference for the portfolio admin panel
  (`admin.portfolio.{dev|prod}.the-full-stack.com`). Covers
  Next.js 16.2.6 static export (`output: 'export'`), React 19.2.6
  (with React Compiler stable, ref-as-prop, `useActionState`,
  `useOptimistic`, `useDeferredValue` with initialValue, Document
  Metadata nativo, View Transitions, `useEffectEvent`, Activity
  Component), TypeScript 6 strict, Biome v2 (no ESLint), Tailwind v4
  with `@tailwindcss/postcss`, shadcn/ui (Radix primitives, generated
  without `forwardRef`), Tanstack Query v5 + Tanstack Table v8 +
  Tanstack Virtual (with `useSuspenseQuery` patterns), react-hook-form
  7 + Zod (for complex forms, coexists with `useActionState` for
  simple ones), Zustand 5 (auth + theme), Recharts, sonner,
  lucide-react, MSW v2 for mocks, Vitest + Testing Library v16 +
  happy-dom + Playwright, the Hybrid Atomic Design folder layout
  (`src/components/ui/` shared + `src/features/<X>/` per domain),
  JWT auth integration with the Lambda `auth` of plans 01/02 (tokens
  in `localStorage` via Zustand persist — SPA cross-origin makes
  HttpOnly cookies non-viable; defense is strict CSP + SRI + short
  access TTL 15min + family_id refresh rotation; fragment-based magic-
  link callback + mutex refresh rotation + BroadcastChannel multi-tab
  logout sync), Cloudflare Pages deploy via the same
  `devtools/cloudflare_setup` + `deploy-apps.yml` pipeline as the 6
  Astro apps (`admin` becomes the 7th project per env, total 14
  projects = 7 apps x 2 envs), per-env env vars with `NEXT_PUBLIC_*`
  prefix synced via `sync_secrets --category=client`. ALWAYS invoke
  this skill BEFORE answering ANY question about the admin panel,
  including questions framed as "next.js spa", "next 16 export",
  "react 19 patterns", "react compiler", "useactionstate",
  "useoptimistic", "shadcn admin", "tanstack query auth",
  "atomic design react", "jwt en react", "admin auth",
  "cloudflare pages nextjs", or "admin portfolio". NEVER answer
  admin panel questions from training data alone — this project has
  consolidated 2026 patterns (React 19.2.6 + Next 16.2.6 stable +
  mutex refresh rotation + fragment magic-link callback + hybrid
  Atomic Design + shadcn + Tailwind v4 + Biome override + custom
  devtools integration) that override generic advice.
  Use when the user says "admin", "admin panel", "admin spa",
  "admin dashboard", "next 16",
  "nextjs 16", "next.js 16", "next 16.2", "spa", "static export",
  "output export", "react 19", "react 19.2", "reactjs 19",
  "react compiler", "useactionstate", "useformstatus",
  "useoptimistic", "usedeferredvalue", "use hook react 19",
  "ref as prop", "forwardref deprecated", "document metadata react",
  "view transitions react", "useeffectevent", "activity component",
  "shadcn ui dashboard", "shadcn react 19", "tanstack query",
  "tanstack table", "usesuspensequery", "zustand auth", "zustand 5",
  "jwt refresh rotation", "jwt storage spa", "magic link react",
  "refresh token mutex", "atomic design react", "atomic design
  hibrido", "feature sliced", "components ui features",
  "cloudflare pages nextjs", "admin subdomain", "admin.portfolio",
  "admin panel", "panel admin", "biome nextjs", "tailwind v4 shadcn",
  "next themes", "broadcastchannel logout", "admin auth",
  "admin estructura", "estructura admin", "componentes
  admin", "admin plan", "admin skill", "admin metrics", "vista de
  metricas", "metrics view", "app shell", "admin shell", "turbopack
  default", "proxy.ts next 16".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "optional subtopic: stack, structure, auth, ui, deploy, testing, mocks, react-19, next-16"
---

# Admin stack — admin.portfolio.the-full-stack.com

Reference completa para construir y mantener el admin del
portfolio. Stack 100% 2026 (React 19.2.6 + Next.js 16.2.6).

## Versiones canonicas (mayo 2026)

| Capa | Version | Notas |
|------|---------|-------|
| Next.js | **16.2.6** (May 7, 2026 — LTS candidato, 13 security fixes) | Turbopack default + stable, async APIs, `proxy.ts` reemplaza `middleware.ts` |
| React | **19.2.6** (May 6, 2026) | React Compiler stable, `ref` como prop, `useActionState`, `useOptimistic`, View Transitions, `useEffectEvent`, `Activity` |
| React DOM | **19.2.6** | matches React |
| TypeScript | **6.0.6** | strict + `noUncheckedIndexedAccess` |
| Biome | **2.0.0+** | sin ESLint, override en `components/ui/**` |
| Tailwind | **4.1.4** | `@tailwindcss/postcss` plugin, CSS-first config |
| shadcn/ui | latest (oct 2025+) | React 19 support, sin `forwardRef` en codegen |
| Tanstack Query | **5.52.3** | `useSuspenseQuery` patterns + `useOptimistic` |
| Tanstack Query Persist | **5.52.3** | persister + sync-storage |
| Tanstack Table | **8.20.5** | columnDef + sort + paginator |
| Tanstack Virtual | **3.5.1** | listas grandes |
| Zustand | **5.0.14** (Jan 2026 state consistency fix) | persist con partialize |
| react-hook-form | **7.53.0** | uncontrolled inputs, coexiste con `useActionState` |
| @hookform/resolvers | **3.4.2** | Zod resolver |
| Zod | **3.24.1** | schemas + inferencia TS |
| Recharts | **2.14.2** | charts (via shadcn add chart) |
| sonner | **1.7.2** | toasts |
| lucide-react | **0.416.0** | iconos |
| next-themes | **0.4.8** | dark/light con `data-theme` |
| MSW | **2.3.2** | mocks dev + tests |
| Vitest | **2.2.5** | happy-dom + coverage v8 |
| @testing-library/react | **16.1.0** | React 19 support |
| @testing-library/user-event | **14.5.2** | |
| Playwright | **1.48.2** | E2E (suite del monorepo) |
| @marsidev/react-turnstile | **1.2.5** | Turnstile widget |
| jwt-decode | **4.0.0** | solo decodificar (sin verificar firma) |
| lz-string | **1.5.0** | compresion del persister |
| babel-plugin-react-compiler | **19.0.0-beta.17** | si React Compiler habilitado |
| class-variance-authority | **0.7.0** | CVA para variants |
| clsx | **2.1.1** | helper |
| tailwind-merge | **2.4.0** | helper |
| Node | **>=24** | runtime build |
| pnpm | **11.0.9** | package manager |

## Resumen ejecutivo (decisiones cerradas)

| Tema | Decision | Razon |
|------|----------|-------|
| Framework | Next.js 16.2.6 `output: 'export'` | Monorepo consistency + ecosystem; LTS candidato |
| Runtime React | React 19.2.6 (obligatorio en Next 16.x) | Compiler stable, `useActionState`, `useOptimistic`, Document Metadata nativo |
| Bundler | **Turbopack** (default + stable en 16, sin config) | 5-10x Fast Refresh, 2-5x build, filesystem caching en dev (16.1+) |
| Routing | App Router (NO Pages Router) | Default 2026; layouts anidados; todo Client Components |
| TypeScript | 6.0.6 strict + `noUncheckedIndexedAccess` | Heredar politica del monorepo |
| Linter/Formatter | Biome v2 (sin ESLint) | Heredar `biome.json` root con override para `components/ui/*.tsx`; `eslint.ignoreDuringBuilds: true` |
| CSS | Tailwind v4 `@theme` inline + `@tailwindcss/postcss` | 5x faster builds, 100x incremental, CSS-first config |
| Componentes UI | shadcn/ui (sin `forwardRef`, ref-as-prop) | Copy-paste, full control, React 19 support |
| React Compiler | **Habilitado** via `reactCompiler: true` (stable en 16) | Auto-memoization sin `useMemo`/`useCallback` boilerplate |
| Iconos | lucide-react | 1500+ icons, tree-shakable |
| Charts | Recharts via `shadcn add chart` | Integration nativa de shadcn (req React 19 → `react-is@19.2.6` override) |
| Tablas | Tanstack Table v8 + Tanstack Virtual | Estandar 2026 |
| Data fetching | Tanstack Query v5 + **`useSuspenseQuery`** | Persister + mutex para refresh rotation |
| Forms simples (1-2 fields) | `useActionState` + `useFormStatus` | Menos boilerplate, React 19 nativo |
| Forms complejos (auth, multi-step) | react-hook-form + Zod + shadcn `<Form>` | Uncontrolled inputs, mejor DX, integracion shadcn |
| Optimistic updates | `useOptimistic` (puntuales) o Tanstack `onMutate` (con cache) | Elegir UNO por mutation, no mezclar |
| State global | Zustand 5.0.14 con `persist` middleware | auth + theme; partialize EXCLUYE `accessToken` |
| Theme dark/light | next-themes con `attribute="data-theme"` | Evita hydration mismatch |
| Document Metadata | Static: Next `metadata` export. Dynamic: React 19 `<title>`/`<meta>` nativo | React 19 hoist al `<head>` automatico |
| Toasts | sonner | Accesible, tree-shakable |
| Tests unit | Vitest 2 + Testing Library v16 + happy-dom | Reusa stack del monorepo; `act()` warnings mas estrictos en R19 |
| Tests E2E | Playwright (suite del monorepo) | Mismo runner que las apps Astro |
| Mocks API | MSW v2 (con polyfill BroadcastChannel en happy-dom) | Para dev sin backend + tests |
| Estructura | **Hibrido**: `src/components/ui/` + `src/features/<X>/` | Atomic Design sin nombres rigidos |
| Carpeta | `admin/` en root del repo | Usuario lo pidio explicito; entra a pnpm workspace |
| Subdominio | `admin.portfolio.{env}.the-full-stack.com` | Sigue subdomain-standard |
| Deploy | Cloudflare Pages (REST API via `devtools/cloudflare_setup`) | Mismo pipeline que las 6 apps Astro |
| Envs CI | dev/prod (2 Cloudflare Pages projects) | Branch `dev`/`main` mapping |
| Auth backend | Lambda `auth` planes 01-02 (aun pending) | Admin usa MSW hasta que esten deployadas |
| Auth storage | Access + refresh JWT en `localStorage` (Zustand persist). SPA cross-origin (admin → api) hace HttpOnly cookies no viables (requeriria `SameSite=None` cross-site + vector CSRF). Defensa: CSP estricta + SRI + access TTL 15min + family_id refresh rotation | OWASP JWT Cheat Sheet + RFC 9700 Jan 2025 |
| Refresh rotation | Mutex pattern (1 sola refresh in-flight) + family_id detection | Backend ya lo implementa; client previene race conditions |
| Magic link UX | Backend redirect 302 a `/auth/callback#access=X&refresh=Y` (fragment) | Tokens NO viajan a server logs ni Referer |
| Multi-tab logout | BroadcastChannel API | Logout en una tab = logout en todas |

## Features clave de React 19 que aplican al admin

| Feature | Uso | Aplicable? |
|---------|-----|-----------|
| **React Compiler** | Auto-memoization sin `useMemo`/`useCallback` | ✅ habilitar via `reactCompiler: true` |
| **`useActionState`** | Forms simples + state automatico (`isPending`, `error`, `data`) | ✅ para forms 1-2 fields |
| **`useFormStatus`** | Hook que lee el `<form>` ancestor (pending, data) | ✅ para spinners en `<button>` dentro de `<form action={...}>` |
| **`useOptimistic`** | Optimistic UI updates puntuales | ✅ para toggles, inline edits |
| **`use(promise)`** | Read promise + Suspense en Client Components | ⚠ Tanstack `useSuspenseQuery` es mejor |
| **`use(context)` condicional** | Llamar context dentro de `if` | ⚠ raro pero util cuando aplica |
| **`useDeferredValue(value, initialValue?)`** | Defer renders sin flicker | ✅ para filtros / tabs / search |
| **`useEffectEvent`** | Extraer logica no-reactiva de Effects | ✅ para handlers en effects |
| **`Activity` component** | Render "background activity" con `display: none` manteniendo state | ✅ para mantener tabs ocultas vivas |
| **View Transitions API** | Animaciones en navegacion / updates | ⚠ Nice-to-have, opcional |
| **`ref` como prop normal** | Sin `forwardRef`, ref es prop como cualquier otra | ✅ todos los componentes nuevos |
| **Document Metadata nativo** | `<title>`/`<meta>` en componentes se hoist al `<head>` | ✅ para metadata dynamic per page |
| **Asset loading APIs** (`preload`, `preinit`) | Pre-cargar fonts / scripts | ✅ para fonts self-hosted opcional |
| **`onCaughtError` / `onUncaughtError` en `createRoot`** | Error handling centralizado | ✅ para Sentry / error logging |
| **`useId` con prefix custom** | IDs estables para SSR (no aplica) | ⚠ no critico en SPA |
| **Server Components / Server Actions** | NO aplican en `output: 'export'` (no hay server runtime) | ❌ |
| **Cache Components (`'use cache'`)** | Server-only | ❌ |

## Cuando leer cada capitulo del knowledge tree

| Tema | Archivo | Cuando |
|------|---------|--------|
| Decisiones globales + diagramas | `.claude/docs/admin/README.md` | Primera lectura, decisiones no-reabribles, navegacion |
| Next.js 16.2.6 + React 19.2.6 + TypeScript + Biome + Tailwind v4 | `.claude/docs/admin/01-stack.md` | Antes de tocar config (`next.config.ts`, `tsconfig`, `biome.json`) o agregar dep |
| Estructura Hybrid Atomic Design | `.claude/docs/admin/02-structure.md` | Antes de crear/mover un componente, decidir donde vive |
| shadcn/ui + Tailwind v4 + theming + React 19 patterns (`useActionState`, `useFormStatus`, `useOptimistic`) | `.claude/docs/admin/03-ui.md` | Antes de agregar componente shadcn, modificar tema, crear variants CVA, decidir form pattern |
| Auth JWT + Tanstack Query + Zustand + React 19 | `.claude/docs/admin/04-auth.md` | Antes de tocar fetch wrapper, refresh rotation, magic link callback, protected routes |
| Cloudflare Pages deploy + env vars | `.claude/docs/admin/05-deploy.md` | Antes de cambiar deploy-apps.yml, devtools/cloudflare_setup, env vars del admin |
| Testing (Vitest 2 + Testing Library v16 + MSW v2 + Playwright) | `.claude/docs/admin/06-testing.md` | Antes de escribir un test, configurar MSW handlers, setup de fixtures |

## Reglas duras del admin (SIEMPRE / NUNCA)

- **SIEMPRE** usar Client Components (`'use client'` en cada page/layout). El export mode NO soporta async Server Components.
- **SIEMPRE** todas las API calls van a `process.env.NEXT_PUBLIC_API_ENDPOINT`. NUNCA hardcodear hostnames.
- **SIEMPRE** access + refresh + user persisten en `localStorage` via Zustand `persist`. El admin es SPA cross-origin (admin → api): HttpOnly cookies cross-site requieren `SameSite=None` + `Domain=.the-full-stack.com`, abriendo vectores CSRF en los 6 niches y rompiendo portabilidad. Defensa primaria: CSP estricta `script-src 'self'` sin `unsafe-inline`/`unsafe-eval` + SRI en third-party + access TTL 15min + refresh rotation con family_id reuse detection.
- **SIEMPRE** el fetch wrapper usa el mutex de refresh: un solo `/session/refresh` in-flight, los demas requests esperan el resultado.
- **SIEMPRE** rate-limit del client: si 429 → mostrar toast con `retry_after`, no reintentar automaticamente.
- **SIEMPRE** Turnstile en login.check-email (mismo sitekey que las 6 apps, hostname `admin.portfolio.*` se agrega a la lista en Cloudflare).
- **SIEMPRE** un componente vive en `src/features/<X>/components/` SI tiene logica de dominio. Solo se promueve a `src/components/ui/` cuando 2+ features lo usan y no depende de un API especifico.
- **SIEMPRE** componentes nuevos reciben `ref` como prop normal — **NUNCA** `forwardRef`. shadcn ya migrado.
- **SIEMPRE** Biome `components/ui/*.tsx` esta exento de reglas strict (los patterns de shadcn chocan).
- **SIEMPRE** tests unitarios espejan `src/<X>` -> `tests/unit/<X>.test.ts`.
- **SIEMPRE** Conventional Commits espanol.
- **SIEMPRE** React Compiler habilitado (`reactCompiler: true` en `next.config.ts`). Opt-out per file con `'use no memo'` solo si rompe algo medido.
- **SIEMPRE** asegurar Rules of React (pure components, no mutar props/state, side effects en useEffect, hooks unconditional) — el Compiler las enforces.
- **SIEMPRE** elegir UNO entre `useOptimistic` o Tanstack `onMutate` por mutation — NO mezclar.
- **SIEMPRE** forms de auth (login/verify) usan **react-hook-form + Zod + shadcn `<Form>` + Tanstack `useMutation`**. NO `useActionState` solo (forms complejos con multi-step).
- **SIEMPRE** `useSuspenseQuery` cuando la data es required para renderizar la page (Error Boundary cubre fails). `useQuery` cuando la data es opcional o inline.
- **SIEMPRE** `useSearchParams()` dentro de `<Suspense>` boundary (limitacion del export mode).
- **NUNCA** API routes (`app/api/*/route.ts`) — `output: 'export'` no las soporta. Todo backend = Lambdas externas.
- **NUNCA** `middleware.ts` ni `proxy.ts` — no corren en export mode. Auth guard es Client Component.
- **NUNCA** `<Image>` con optimizacion. Usar `images.unoptimized: true` en `next.config.ts`.
- **NUNCA** Server Components con `async fetch`. Cliente all the way.
- **NUNCA** `'use cache'` directive — server-only.
- **NUNCA** Server Actions — server-only.
- **NUNCA** tokens JWT en URL query params (`?access=...`). Magic link callback usa fragment hash (`#access=...`).
- **NUNCA** intentar setear HttpOnly cookies cross-origin (`SameSite=None; Domain=.the-full-stack.com`): vector CSRF + perdida de portabilidad. Tokens en localStorage con CSP estricta.
- **NUNCA** cargar scripts third-party sin `integrity` (SRI). Allowlist actual: `challenges.cloudflare.com/turnstile/v0/api.js`.
- **NUNCA** logear el JWT, refresh token, magic link token, email completo. Solo hash truncado para diagnostico.
- **NUNCA** crear "atom wrappers" sin valor (ej. `<PrimaryButton>` que solo wrappea `<Button variant="primary">`).
- **NUNCA** Framer Motion en el admin. Tailwind animate + `@starting-style` + Radix transitions built-in + View Transitions API cubren 100%.
- **NUNCA** atribucion de IA en codigo, commits, PRs.
- **NUNCA** `forwardRef` en componentes nuevos — usar `ref` como prop.

## Comando canonico (development)

```bash
# Instalar deps (desde root, pnpm workspace lo recoge)
pnpm install

# Dev server (Turbopack, HMR snappy)
pnpm --filter @portfolio/admin dev
# -> http://localhost:3000

# Dev con MSW activado (mientras backend no esta vivo)
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev

# Build estatico (Turbopack)
pnpm --filter @portfolio/admin build
# -> admin/out/

# Preview del build
pnpm --filter @portfolio/admin preview

# Lint + format (Biome v2, sin ESLint)
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin lint:fix

# Typecheck
pnpm --filter @portfolio/admin typecheck

# Unit tests (Vitest 2 + happy-dom)
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin test:coverage  # >= 80% per-file

# Agregar componente shadcn (sin forwardRef, ya con React 19)
cd admin && pnpm dlx shadcn@latest add button form input select chart

# E2E Playwright (stack local arriba)
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local

# Deploy
git push origin dev   # CI auto-deploya admin.portfolio.dev.the-full-stack.com
```

## Anti-patrones (resumen)

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Usar `app/api/*/route.ts` | Static export no las soporta | Llamar al Lambda externo via `NEXT_PUBLIC_API_ENDPOINT` |
| `middleware.ts` o `proxy.ts` para auth | No corre en SPA estatica | `AuthGuard` Client Component en `(admin)/layout.tsx` |
| `forwardRef` en componentes nuevos | Deprecado en React 19 | `ref` como prop normal |
| Mezclar `useState` para isPending con `useActionState` | Conflicto de state | Elegir uno; `useActionState` ya incluye `isPending` |
| Mezclar `useOptimistic` con Tanstack `onMutate` | Dos sources of truth | Elegir uno por mutation |
| Intentar HttpOnly cookies cross-origin del API al admin | Requiere `SameSite=None` + `Domain=.the-full-stack.com` (vector CSRF) | Tokens en localStorage con CSP estricta + SRI + access TTL 15min |
| Cargar third-party JS sin SRI | Script comprometido lee localStorage | `integrity="sha384-..."` + CSP allowlist |
| 2 refresh requests simultaneos | Backend revoca familia por reuse | Mutex pattern en fetch wrapper |
| Magic link con tokens en query (`?access=X`) | Tokens en Referer + browser history | Backend redirect 302 a `/auth/callback#access=X&refresh=Y` (fragment) |
| `useSearchParams()` sin `<Suspense>` | Build fail en export mode | Wrappear en `<Suspense>` |
| Mover componente a `components/ui/` con 1 sola feature usandolo | Premature abstraction | Vive en `features/<X>/components/` hasta que 2+ features lo usen |
| Hardcodear colores Recharts | Rompe dark mode | Usar `var(--color-*)` tokens del DS |
| Framer Motion / GSAP / Motion One | 30KB+ overhead | Tailwind animate + `@starting-style` + Radix + View Transitions |
| `useEffect(() => fetch(...))` sin Tanstack Query | Sin cache, sin retry, sin invalidation | Tanstack Query `useSuspenseQuery` o `useQuery` |
| Mockear `useAuthStore` con `vi.mock` | Acopla test a impl | Usar `useAuthStore.setState()` para preparar el estado |
| Olvidar `'use client'` en page con hooks de React 19 | Build error | Primera linea: `'use client'` |
| Atribucion IA en commits | Politica empresa | Sin co-authored, sin "generated with Claude" |
| Mutar props/state en componentes | Compiler no optimiza + bugs concurrent | Usar spread, `Object.assign`, etc. |
| Hooks en conditionals/loops | Rules of Hooks violation | Hooks top-level siempre |
| Usar `useFormState` (deprecado) | Movido a `useActionState` en react (no react-dom) | `import {useActionState} from 'react'` |

## Bibliografia interna

- `.claude/rules/admin.md` — reglas duras (este resumen extendido)
- `.claude/docs/admin/` — knowledge tree (7 capitulos)
- `docs/specs/a-admin/` — plan de implementacion (efimero, se elimina al mergear)
- `.claude/rules/lambda-controller.md` — formato del Lambda `auth` backend (referencia)
- `.claude/rules/secrets-strategy.md` + `client-env-sync.md` — env vars categoria client
- `.claude/rules/ci-cd-pipeline.md` — `deploy-apps.yml` workflow
- `.claude/docs/cloudflare/` — Cloudflare Pages knowledge
- `.claude/docs/subdomain-standard/` — patron de subdominios

## Research raw (efimero, en `tmp/research/dashboard/`)

8 archivos de research que generaron este knowledge tree:
1. `tmp/research/dashboard/01-nextjs-16-spa.md` (1,743 lineas)
2. `tmp/research/dashboard/02-react-patterns.md` (1,579 lineas)
3. `tmp/research/dashboard/03-shadcn-atomic-design.md` (1,943 lineas)
4. `tmp/research/dashboard/04-jwt-auth-spa.md` (1,533 lineas)
5. `tmp/research/dashboard/05-cloudflare-deploy.md` (985 lineas)
6. `tmp/research/dashboard/06-react-19.md` (1,368 lineas) — **React 19.2.6 deep dive**
7. `tmp/research/dashboard/07-nextjs-16.md` (1,433 lineas) — **Next.js 16.2.6 deep dive**
8. `tmp/research/dashboard/08-integrations.md` (1,418 lineas) — **Ecosystem 2026 integration**

Total: 12,002 lineas de research consolidado (mayo 2026). Se eliminan
con `rm -rf tmp/research/` cuando el plan se mergea.
