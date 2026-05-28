---
name: dashboard-stack
description: >
  Dashboard SPA stack reference for the portfolio admin dashboard
  (`admin.portfolio.{dev|stage|prod}.the-full-stack.com`). Covers
  Next.js 16 static export (`output: 'export'`), React 18, TypeScript 6
  strict, Biome v2 (no ESLint), Tailwind v4, shadcn/ui (Radix
  primitives), Tanstack Query v5 + Tanstack Table v8 + Tanstack
  Virtual, react-hook-form + Zod, Zustand (auth + theme), Recharts,
  sonner, lucide-react, MSW for mocks, Vitest + Testing Library, the
  Hybrid Atomic Design folder layout (`src/components/ui/` shared +
  `src/features/<X>/` per domain), JWT auth integration with the
  Lambda `auth` of plans 01/02 (access in-memory Zustand + refresh in
  HttpOnly cookie OR fragment-based magic-link callback + mutex
  refresh rotation + BroadcastChannel multi-tab logout sync),
  Cloudflare Pages deploy via the same `devtools/cloudflare_setup` +
  `deploy-apps.yml` pipeline as the 6 Astro apps (4th env: `admin`
  becomes the 7th project per env, total 21 projects = 7 apps x 3
  envs), per-env env vars with `NEXT_PUBLIC_*` prefix synced via
  `sync_secrets --category=client`. ALWAYS invoke this skill BEFORE
  answering ANY question about the dashboard, including questions
  framed as "next.js spa", "static export", "shadcn dashboard",
  "tanstack query auth", "atomic design react", "jwt en react",
  "dashboard auth", "cloudflare pages nextjs", or "admin portfolio".
  NEVER answer dashboard questions from training data alone — this
  project has consolidated 2026 patterns (mutex refresh rotation,
  fragment magic-link callback, hybrid Atomic Design, shadcn + Tailwind
  v4 + Biome override, Next.js 16 SPA quirks, custom devtools
  integration) that override generic advice.
  Use when the user says "dashboard", "admin dashboard", "next 16",
  "nextjs 16", "next.js 16", "spa", "static export", "output export",
  "react 18 dashboard", "shadcn ui dashboard", "tanstack query",
  "tanstack table", "zustand auth", "jwt refresh rotation", "jwt
  storage spa", "magic link react", "refresh token mutex", "atomic
  design react", "atomic design hibrido", "feature sliced",
  "components ui features", "cloudflare pages nextjs", "admin
  subdomain", "admin.portfolio", "dashboard analytics", "biome
  nextjs", "tailwind v4 shadcn", "next themes", "broadcastchannel
  logout", "dashboard auth", "dashboard estructura", "estructura
  dashboard", "componentes dashboard", "dashboard plan",
  "dashboard skill".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "optional subtopic: stack, structure, auth, ui, deploy, testing, mocks"
---

# Dashboard stack — admin.portfolio.the-full-stack.com

Reference completa para construir y mantener el dashboard admin del
portfolio. Si el subtopic no encaja, leer el indice completo.

## Resumen ejecutivo (decisiones cerradas)

| Tema | Decision | Razon |
|------|----------|-------|
| Framework | Next.js 16 con `output: 'export'` | Monorepo consistency + ecosystem; usuario lo eligio |
| Runtime React | React 18.3.x (NO React 19) | `use()`, Server Actions hooks no aplican a SPA; libs (Tanstack) mas maduras en 18 |
| Routing | App Router (NO Pages Router) | Default 2026; layouts anidados; todo Client Components |
| TypeScript | 6.x strict + `noUncheckedIndexedAccess` | Heredar politica del monorepo |
| Linter/Formatter | Biome v2 (sin ESLint) | Heredar `biome.json` root con override para `components/ui/*.tsx` |
| CSS | Tailwind v4 con `@theme` inline en CSS | v4 official desde feb 2025; shadcn lo soporta |
| Componentes UI | shadcn/ui + Radix primitives | Copy-paste, no library; full control |
| Iconos | lucide-react | 1500+ icons, tree-shakable, default de shadcn |
| Charts | Recharts via `shadcn add chart` | Integration nativa de shadcn |
| Tablas | Tanstack Table v8 + Tanstack Virtual | Estandar 2026; virtualizacion para listas grandes |
| Data fetching | Tanstack Query v5 | Persister + mutex para refresh rotation |
| Forms | react-hook-form + `@hookform/resolvers/zod` + Zod | shadcn `Form` component lo integra mejor que Tanstack Form |
| State global | Zustand 5.x con `persist` middleware | auth (access in-memory, refresh persist) + theme |
| Theme dark/light | next-themes con `attribute="data-theme"` | Evita hydration mismatch |
| Toasts | sonner | Accesible, 9.1KB, tree-shakable |
| Tests unit | Vitest + Testing Library + happy-dom | Reusa stack del monorepo |
| Tests E2E | Playwright (suite del monorepo) | Mismo runner que las apps Astro |
| Mocks API | MSW (Mock Service Worker) | Para dev (sin backend live) + tests |
| Estructura | **Hibrido**: `src/components/ui/` + `src/features/<X>/` | Atomic Design sin nombres rigidos |
| Carpeta | `dashboard/` en root del repo | Usuario lo pidio explicito; entra a pnpm workspace |
| Subdominio | `admin.portfolio.{env}.the-full-stack.com` | Sigue subdomain-standard |
| Deploy | Cloudflare Pages (REST API via `devtools/cloudflare_setup`) | Mismo pipeline que las 6 apps Astro |
| Envs CI | dev/stage/prod (3 Cloudflare Pages projects) | Branch `dev`/`stage`/`main` mapping |
| Auth backend | Lambda `auth` planes 01-02 (aun pending) | Dashboard usa MSW hasta que esten deployadas |
| Auth storage | Access JWT in-memory (Zustand) + refresh HttpOnly cookie (preferido) o localStorage+CSP (fallback) | OWASP JWT Cheat Sheet + RFC 9700 Jan 2025 |
| Refresh rotation | Mutex pattern (1 sola refresh in-flight) + family_id detection | Backend ya lo implementa; client previene race conditions |
| Magic link UX | Backend redirect 302 a `/auth/callback#access=X&refresh=Y` (fragment) | Tokens NO viajan a server logs ni Referer |
| Multi-tab logout | BroadcastChannel API | Logout en una tab = logout en todas |

## Cuando leer cada capitulo del knowledge tree

| Tema | Archivo | Cuando |
|------|---------|--------|
| Decisiones globales + diagramas | `.claude/docs/dashboard/README.md` | Primera lectura, decisiones no-reabribles, navegacion |
| Next.js 16 + React 18 + TypeScript + Biome | `.claude/docs/dashboard/01-stack.md` | Antes de tocar config (next.config.ts, tsconfig, biome.json) o agregar dep |
| Estructura Hybrid Atomic Design | `.claude/docs/dashboard/02-structure.md` | Antes de crear/mover un componente, decidir donde vive |
| shadcn/ui + Tailwind v4 + theming | `.claude/docs/dashboard/03-ui.md` | Antes de agregar componente shadcn, modificar tema, crear variants CVA |
| Auth JWT + Tanstack Query + Zustand | `.claude/docs/dashboard/04-auth.md` | Antes de tocar fetch wrapper, refresh rotation, magic link callback, protected routes |
| Cloudflare Pages deploy + env vars | `.claude/docs/dashboard/05-deploy.md` | Antes de cambiar deploy-apps.yml, devtools/cloudflare_setup, env vars del dashboard |
| Testing (Vitest + MSW + Playwright) | `.claude/docs/dashboard/06-testing.md` | Antes de escribir un test, configurar MSW handlers, setup de fixtures |

## Reglas duras del dashboard (SIEMPRE / NUNCA)

- **SIEMPRE** usar Client Components (`'use client'` en cada page/layout). El export mode NO soporta async Server Components.
- **SIEMPRE** todas las API calls van a `process.env.NEXT_PUBLIC_API_ENDPOINT`. NUNCA hardcodear hostnames.
- **SIEMPRE** el access JWT vive en memoria (Zustand store sin `persist` del campo `accessToken`). El refresh va en HttpOnly cookie (preferido) o en `localStorage` con CSP estricta (fallback explicito).
- **SIEMPRE** el fetch wrapper usa el mutex de refresh: un solo `/session/refresh` in-flight, los demas requests esperan el resultado.
- **SIEMPRE** rate-limit del client: si 429 → mostrar toast con `retry_after`, no reintentar automaticamente.
- **SIEMPRE** Turnstile en register.start y login.start (mismo sitekey que las 6 apps, hostname `admin.portfolio.*` se agrega a la lista en Cloudflare).
- **SIEMPRE** un componente vive en `src/features/<X>/components/` SI tiene logica de dominio. Solo se promueve a `src/components/ui/` cuando 2+ features lo usan y no depende de un API especifico.
- **SIEMPRE** Biome `components/ui/*.tsx` esta exento de reglas strict (los patterns de shadcn con `any` para Slot composition chocan).
- **SIEMPRE** tests unitarios espejan `src/<X>` -> `tests/unit/<X>.test.ts` (mismo patron que las apps Astro).
- **SIEMPRE** Conventional Commits espanol (sigue rule git-workflow).
- **NUNCA** API routes (`app/api/*/route.ts`) — `output: 'export'` no las soporta. Todo backend = Lambdas externas.
- **NUNCA** `middleware.ts` ni `proxy.ts` — no corren en export mode. Auth guard es Client Component.
- **NUNCA** `<Image>` con optimizacion. Usar `images.unoptimized: true` en `next.config.ts` o `<img>` regular.
- **NUNCA** Server Components con `async fetch`. Cliente all the way.
- **NUNCA** tokens JWT en URL query params (`?access=...`). Magic link callback usa fragment hash (`#access=...`).
- **NUNCA** persistir el `accessToken` en localStorage. Solo refreshToken (si fallback) o nada (si HttpOnly cookie).
- **NUNCA** logear el JWT, refresh token, magic link token, email completo. Solo hash truncado para diagnostico.
- **NUNCA** crear "atom wrappers" sin valor (ej. `<PrimaryButton>` que solo wrappea `<Button variant="primary">`).
- **NUNCA** Framer Motion en el dashboard. Tailwind animate + `@starting-style` + Radix transitions built-in cubren 100%.
- **NUNCA** atribucion de IA en codigo, commits, PRs (sigue rule global del repo).

## Comando canonico (development)

```bash
# Instalar deps (desde root, pnpm workspace lo recoge)
pnpm install

# Dev server (HMR via Turbopack)
pnpm --filter @portfolio/dashboard dev
# -> http://localhost:3000

# Build estatico
pnpm --filter @portfolio/dashboard build
# -> dashboard/out/

# Preview del build
pnpm --filter @portfolio/dashboard preview
# (next start sirve dashboard/out/ como static)

# Lint + format
pnpm --filter @portfolio/dashboard lint
pnpm --filter @portfolio/dashboard lint:fix

# Typecheck
pnpm --filter @portfolio/dashboard typecheck

# Unit tests
pnpm --filter @portfolio/dashboard test
pnpm --filter @portfolio/dashboard test:coverage

# Agregar componente shadcn
cd dashboard && pnpm dlx shadcn@latest add button form input select

# Deploy
git push origin dev   # CI auto-deploya admin.portfolio.dev.the-full-stack.com
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Usar `app/api/*/route.ts` | Static export no las soporta | Llamar al Lambda externo via `NEXT_PUBLIC_API_ENDPOINT` |
| `middleware.ts` para auth | No corre en SPA estatica | `AuthGuard` Client Component en `(dashboard)/layout.tsx` |
| Persistir accessToken en localStorage | XSS = token robado por 15 min completos | Zustand sin persist + refresh en HttpOnly cookie |
| 2 refresh requests simultaneos | Race condition, backend revoca familia por reuse | Mutex pattern en fetch wrapper |
| Magic link con tokens en query (`?access=X`) | Tokens en Referer + browser history | Backend redirect 302 a `/auth/callback#access=X&refresh=Y` (fragment) |
| Crear `<PrimaryButton>` que wrappea `<Button variant="primary">` | Sin valor, fragmenta | Usar `<Button variant="primary">` directo |
| Mover componente a `components/ui/` con 1 sola feature usandolo | Premature abstraction | Vive en `features/<X>/components/` hasta que 2+ features lo usen |
| Hardcodear colores Recharts | Rompe dark mode | Usar `var(--color-*)` tokens del DS |
| Framer Motion / GSAP | 30KB+ overhead, no necesario | Tailwind animate + `@starting-style` |
| `useEffect(() => fetch(...))` sin Tanstack Query | Sin cache, sin retry, sin invalidation | Tanstack Query `useQuery` |
| Mockear `useAuthStore` en tests | Acopla test a impl | Usar `useAuthStore.setState()` para preparar el estado |
| Olvidar `'use client'` en page con hooks | Build error (Server Component con useState) | Primera linea: `'use client'` |
| Atribucion IA en commits | Politica empresa | Sin co-authored, sin "generated with Claude" |

## Bibliografia interna

- `.claude/rules/dashboard.md` — reglas duras (este resumen extendido)
- `.claude/docs/dashboard/` — knowledge tree (7 capitulos)
- `docs/specs/dashboard/` — plan de implementacion (efimero, se elimina al mergear)
- `.claude/rules/lambda-controller.md` — formato del Lambda `auth` backend (referencia)
- `.claude/rules/secrets-strategy.md` + `client-env-sync.md` — env vars categoria client
- `.claude/rules/ci-cd-pipeline.md` — `deploy-apps.yml` workflow
- `.claude/docs/cloudflare/` — Cloudflare Pages knowledge
- `.claude/docs/subdomain-standard/` — patron de subdominios

## Research raw (efimero, en `tmp/research/dashboard/`)

Los 5 archivos de research que generaron este knowledge tree:
1. `tmp/research/dashboard/01-nextjs-16-spa.md` (1743 lineas)
2. `tmp/research/dashboard/02-react-patterns.md` (1579 lineas)
3. `tmp/research/dashboard/03-shadcn-atomic-design.md` (1943 lineas)
4. `tmp/research/dashboard/04-jwt-auth-spa.md` (1533 lineas)
5. `tmp/research/dashboard/05-cloudflare-deploy.md` (985 lineas)

Total: 7783 lineas de research consolidado (mayo 2026). Se eliminan
con `rm -rf tmp/research/` cuando el plan se mergea.
