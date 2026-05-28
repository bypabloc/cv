# Dashboard SPA (`dashboard/*`) — convenciones del portfolio

> Reglas para el dashboard admin del portfolio: Next.js 16.2.6 SPA
> estatico (`output: 'export'`) + React 19.2.6 + TypeScript 6 strict +
> Biome v2 + Tailwind v4 + shadcn/ui + Tanstack Query v5 + Zustand 5,
> deployado a Cloudflare Pages en
> `admin.portfolio.{dev|stage|prod}.the-full-stack.com`. Consume el
> Lambda `auth` (planes 01-02) + Lambda `analytics` (plan
> analytics-dashboard-api) del backend serverless del repo.

## Versiones canonicas (mayo 2026)

| Capa | Version |
|------|---------|
| Next.js | **16.2.6** (May 7, 2026) — Turbopack default, async APIs, `proxy.ts` reemplaza `middleware.ts` |
| React + React DOM | **19.2.6** (May 6, 2026) — obligatorio en Next 16.x |
| TypeScript | **6.0.6** strict + `noUncheckedIndexedAccess` |
| Biome | **2.0.0+** sin ESLint, override en `components/ui/**` |
| Tailwind | **4.1.4** con `@tailwindcss/postcss` |
| shadcn/ui | latest oct 2025+ (React 19 support, sin `forwardRef` en codegen) |
| Tanstack Query / Persist / Table / Virtual | **5.52.3** / **8.20.5** / **3.5.1** |
| Zustand | **5.0.14** (Jan 2026 state consistency fix) |
| react-hook-form | **7.53.0** |
| Zod | **3.24.1** |
| Recharts | **2.14.2** (override `react-is@19.2.6` necesario) |
| sonner | **1.7.2** |
| lucide-react | **0.416.0** |
| next-themes | **0.4.8** |
| MSW | **2.3.2** |
| Vitest | **2.2.5** + Testing Library v16 + happy-dom 16 |
| Node | >=24, pnpm 11.0.9 |

Tabla extendida en `.claude/skills/dashboard-stack/SKILL.md`.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo bajo `dashboard/` (carpeta nueva en root del repo)
- Configuracion de Cloudflare Pages del project `portfolio-dashboard*`
  (3 projects, uno por env)
- Subdominio `admin.portfolio.{dev|stage|prod}.the-full-stack.com`
- Env vars `NEXT_PUBLIC_*` del dashboard en
  `docker/env/client/.{env}` o en GH Environment Variables
- Extension de `devtools/cloudflare_setup/config.py` para incluir el
  app type `nextjs`
- Extension de `.github/workflows/deploy-apps.yml` para incluir el
  dashboard al matrix

NO aplica a las 6 apps Astro (`apps/{generic,hub,fintech,architect,leader,vibe}/`).
Esas siguen `.claude/rules/astro-landing.md`.

## Reglas duras (SIEMPRE / NUNCA)

### Estructura y stack

- **SIEMPRE** el dashboard vive en `dashboard/` (no en `apps/dashboard/`).
  Entra al pnpm workspace como `@portfolio/dashboard`.
- **SIEMPRE** Next.js 16.2.6 con `output: 'export'` en `next.config.ts`.
  Sin SSR, sin RSC server-only, sin Server Actions, sin ISR, sin
  middleware/proxy, sin Route Handlers.
- **SIEMPRE** React 19.2.6 (obligatorio en Next 16.x). NUNCA pinear a
  React 18 — Next 16 requiere React 19 minimo.
- **SIEMPRE** TypeScript 6.x con `strict: true`,
  `noUncheckedIndexedAccess`, `noUnusedLocals`, `noUnusedParameters`.
  NO `any`; usar `unknown` con narrow.
- **SIEMPRE** App Router (`src/app/`), NO Pages Router. Todas las pages
  y layouts son Client Components (`'use client'` en primera linea).
- **SIEMPRE** Biome v2 (sin ESLint). El `biome.json` del dashboard
  extiende del root con override para `src/components/ui/*.tsx`. En
  `next.config.ts`: `eslint.ignoreDuringBuilds: true`.
- **SIEMPRE** Turbopack (default en Next 16, sin config).
- **SIEMPRE** `reactCompiler: true` en `next.config.ts` (Compiler stable
  en Next 16). Opt-out per file con `'use no memo'` solo si rompe algo
  medido.
- **NUNCA** API routes (`app/api/*/route.ts`) — fail build en export mode.
- **NUNCA** `middleware.ts`, `proxy.ts`, Server Components con `async
  fetch`, Server Actions, `'use cache'`. Todo server-only.
- **NUNCA** `<Image>` con optimizacion. `images.unoptimized: true` en
  config; usar `<img>` regular para casos simples.
- **NUNCA** mezclar npm/yarn con pnpm. Solo pnpm 11.0.9.

### React 19 patterns (obligatorios)

- **SIEMPRE** componentes nuevos reciben `ref` como prop normal — NUNCA
  `forwardRef`. shadcn 2.x ya migrado.
- **SIEMPRE** Rules of React (el Compiler las enforces): components
  pure, no mutar props/state, side effects en useEffect, hooks
  unconditional.
- **SIEMPRE** `useFormState` esta DEPRECADO: usar `useActionState` de
  `react` (NO `react-dom`).
- **SIEMPRE** forms simples (1-2 fields, single submit): usar
  `useActionState` + `useFormStatus`. Forms complejos (auth, multi-step,
  validation custom): react-hook-form + Zod + shadcn `<Form>` + Tanstack
  `useMutation`.
- **SIEMPRE** elegir UNO por mutation: `useOptimistic` (puntual, local)
  O Tanstack `onMutate` (con cache, refetch, invalidation). NO mezclar.
- **SIEMPRE** `useSuspenseQuery` cuando la data es required para
  renderizar (Error Boundary cubre fails). `useQuery` cuando es
  opcional o inline.
- **SIEMPRE** `useDeferredValue(value, initialValue)` con
  `initialValue` para evitar flicker en filtros / tabs.
- **SIEMPRE** Document Metadata:
  - Static metadata (titulo fijo): Next `metadata` export en pages.
  - Dynamic metadata (depende de state/data): React 19 `<title>` /
    `<meta>` dentro del componente (auto-hoist al `<head>`).
- **SIEMPRE** `useSearchParams()` dentro de `<Suspense>` boundary (req
  del export mode — sin Suspense, build fail).
- **NUNCA** `forwardRef` en componentes nuevos.
- **NUNCA** mezclar `useState` para `isPending` con `useActionState`
  (conflict, doble state).
- **NUNCA** mutar props/state ni en handlers ni en helpers (el Compiler
  no optimiza + bugs de concurrent rendering).
- **NUNCA** hooks en conditionals/loops/after early returns.
- **NUNCA** `'use server'` (Server Actions, no aplican en export).
- **NUNCA** `'use cache'` (Cache Components, server-only).

### Estructura de componentes — Hybrid Atomic Design

```text
dashboard/src/
├── app/                                # Next App Router (export)
│   ├── layout.tsx                      # Root: ThemeProvider, QueryProvider, Toaster
│   ├── page.tsx                        # / -> redirect a /login o /dashboard
│   ├── (auth)/                         # Route group (no layout compartido)
│   │   ├── login/page.tsx              # /login
│   │   ├── register/page.tsx           # /register
│   │   ├── verify/page.tsx             # /verify (input de code)
│   │   ├── callback/page.tsx           # /callback (decodea fragment del magic link)
│   │   └── set-password/page.tsx       # /set-password
│   ├── (dashboard)/                    # Route group (protected, layout compartido)
│   │   ├── layout.tsx                  # AuthGuard + sidebar + header
│   │   ├── page.tsx                    # /dashboard (overview)
│   │   ├── analytics/page.tsx          # /dashboard/analytics
│   │   ├── sessions/page.tsx           # /dashboard/sessions
│   │   ├── events/page.tsx             # /dashboard/events
│   │   ├── visits/page.tsx             # /dashboard/visits
│   │   ├── geo/page.tsx                # /dashboard/geo
│   │   ├── devices/page.tsx            # /dashboard/devices
│   │   ├── funnel/page.tsx             # /dashboard/funnel
│   │   ├── contacts/page.tsx           # /dashboard/contacts
│   │   └── settings/                   # /dashboard/settings/*
│   │       ├── page.tsx                # perfil
│   │       └── security/page.tsx       # MFA setup (TOTP + WebAuthn)
│   ├── error.tsx                       # global error boundary
│   ├── not-found.tsx                   # 404
│   └── global-error.tsx                # fallback ultimo
├── components/
│   └── ui/                             # shadcn primitives (copy-paste)
│       ├── button.tsx                  # via `pnpm dlx shadcn add button`
│       ├── input.tsx
│       ├── form.tsx
│       ├── table.tsx
│       ├── chart.tsx                   # Recharts wrapper
│       ├── ...
│       └── index.ts                    # barrel export
├── features/                           # 1 carpeta por dominio
│   ├── auth/
│   │   ├── components/                 # LoginForm, RegisterForm, VerifyCodeInput, MagicLinkPrompt
│   │   ├── hooks/                      # useLogin, useRegister, useVerifyCode, useLogout
│   │   ├── api/                        # auth-client.ts
│   │   ├── store/                      # use-auth-store.ts (Zustand)
│   │   ├── lib/                        # mutex.ts, broadcast.ts, token-expiry.ts
│   │   └── types.ts
│   ├── analytics/                      # overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types.ts
│   ├── sessions/                       # list, detail
│   ├── events/                         # distribution, list, heatmap
│   ├── visits/                         # list, landing-pages
│   ├── geo/                            # by-country
│   ├── devices/                        # breakdown
│   ├── funnel/                         # conversion
│   ├── contacts/                       # list, by-status
│   └── settings/                       # profile, mfa
├── lib/
│   ├── api-client.ts                   # fetch wrapper con JWT + refresh rotation + mutex
│   ├── utils.ts                        # cn() de shadcn
│   ├── env.ts                          # valida NEXT_PUBLIC_* con Zod
│   ├── routes.ts                       # constantes de rutas
│   ├── format/                         # date, number, currency helpers
│   └── validation/                     # Zod schemas compartidos
├── hooks/                              # globales (no de feature)
│   ├── use-theme.ts                    # next-themes wrapper
│   ├── use-media-query.ts
│   ├── use-debounce.ts
│   └── use-protected-route.ts
├── providers/
│   ├── theme-provider.tsx              # next-themes
│   ├── query-provider.tsx              # Tanstack Query + PersistQueryClient
│   └── root-providers.tsx              # composicion de todos
├── styles/
│   ├── globals.css                     # @import tailwind + @theme + @layer base
│   └── fonts.css                       # @fontsource/* (mismas fonts del DS)
├── types/
│   ├── api.ts                          # types de respuestas /auth y /analytics
│   └── models.ts                       # User, Session, Event, Contact, AnalyticsMetric
└── env.d.ts                            # type-safe NEXT_PUBLIC_*
```

Reglas duras del layout:

- **SIEMPRE** un componente vive en `features/<X>/components/` SI tiene
  conocimiento de dominio (referencia un API especifico, un hook de
  Tanstack Query de la feature, un Zustand store de la feature).
- **SIEMPRE** un componente se promueve a `components/ui/` SOLO cuando
  2+ features lo usan Y no depende de un API especifico.
- **SIEMPRE** state de feature en `features/<X>/store/` (Zustand).
  Solo `auth` y `theme` son globales (viven en `features/auth/store/`
  y `providers/theme-provider.tsx`).
- **NUNCA** crear `components/atoms/`, `components/molecules/`,
  `components/organisms/`. La estructura es Hybrid (ui + features), no
  Atomic Design clasico.
- **NUNCA** importar de `features/A/...` desde `features/B/...`. Si
  necesitas compartir, mover a `lib/` o `components/ui/`.
- **NUNCA** Server Components con `async`/`fetch` directo. Todo Client
  Component con Tanstack Query.

### Auth (consume Lambda `auth` de planes 01-02)

> **Contexto: el dashboard es un SPA estatico (Next.js `output:
> 'export'`) deployado en Cloudflare Pages**. NO hay backend bajo el
> mismo origen que pueda setear cookies HttpOnly del dominio del API
> (`api.portfolio.{env}.the-full-stack.com`) — el dashboard vive en
> `admin.portfolio.{env}.the-full-stack.com` y consume el Lambda
> `auth` via fetch CORS cross-subdomain. Una cookie HttpOnly del API
> tendria que ser `SameSite=None; Secure; Domain=.the-full-stack.com`,
> lo que abre vectores CSRF en todos los subdominios y limita la
> portabilidad si el dashboard se aloja en otro origin (mobile app,
> embebido en widgets, etc.). **Decision**: tokens viajan en el body de
> la respuesta del backend, el dashboard los persiste en
> `localStorage`. Mitigaciones: CSP estricta `default-src 'self'` sin
> `unsafe-inline`/`unsafe-eval` (Next 16 export lo soporta),
> Subresource Integrity en todos los scripts third-party, access JWT
> corto (15 min), refresh rotation + family detection en el backend.

- **SIEMPRE** access JWT y refresh JWT en `localStorage`
  (`access_token`, `refresh_token`, `user` como JSON). El store
  Zustand espeja el valor para que `useAuthStore` lo exponga
  reactivamente, con `persist({storage: localStorage})` o lectura
  manual de `localStorage` en el bootstrap del provider.
- **SIEMPRE** fetch wrapper (`lib/api-client.ts`) implementa el mutex
  de refresh: solo UN `/session/refresh` en vuelo a la vez; los demas
  requests con 401 esperan el resultado y reintentan.
- **SIEMPRE** el access token viaja en `Authorization: Bearer <JWT>`
  (header). NUNCA como query param.
- **SIEMPRE** magic link callback en `/callback`: decodifica
  `window.location.hash` (fragment), extrae `access` y `refresh`,
  guarda en `localStorage` via Zustand, limpia el hash con
  `history.replaceState`, redirect a `/dashboard`.
- **SIEMPRE** Turnstile en `LoginForm` y `RegisterForm` (action
  `start`). Sitekey de `NEXT_PUBLIC_TURNSTILE_SITEKEY` (mismo de las 6
  apps; agregar hostname `admin.portfolio.*.the-full-stack.com` a la
  whitelist del widget en Cloudflare).
- **SIEMPRE** `(dashboard)/layout.tsx` envuelve children con
  `<AuthGuard>`: si no hay accessToken o el JWT esta expirado, redirect
  a `/login?next=<current-path>`.
- **SIEMPRE** auto-refresh proactivo: timer client-side que dispara
  `/session/refresh` 30s antes del `exp` del access. Si el refresh
  falla → forzar logout.
- **SIEMPRE** Page Visibility API: si la tab vuelve a foco y pasaron
  >5 min, verificar JWT + refresh si hace falta.
- **SIEMPRE** BroadcastChannel API: canal `portfolio_auth`, mensajes
  `LOGOUT` y `TOKEN_REFRESH`. Logout en una tab = logout en todas.
  Tambien escuchar `storage` event de `localStorage` para tabs en
  navegadores que no soportan BroadcastChannel.
- **SIEMPRE** logout llama POST `/auth?operation=session&action=logout`
  ANTES de limpiar el estado local (backend blacklistea la familia en
  DynamoDB). Si la llamada al backend falla, igual se limpia el estado
  local + redirect.
- **SIEMPRE** CSP estricta en `public/_headers`: `default-src 'self';
  script-src 'self'; connect-src 'self' https://api.portfolio.*
  https://challenges.cloudflare.com; ...`. Sin `unsafe-inline` ni
  `unsafe-eval`. Bloquea robo de tokens via XSS de inline scripts.
- **SIEMPRE** el flujo de registro/login completo: ver
  `.claude/docs/dashboard/04-auth.md` (10+ pages).
- **NUNCA** tokens en URL query params (`?access=...`). Solo fragment
  hash (`#access=...`) en el callback del magic link.
- **NUNCA** intentar setear HttpOnly cookies desde el backend para el
  dashboard: el origen es distinto, requeriria `SameSite=None` cross-
  site + `Domain=.the-full-stack.com` (vector CSRF en los 6 niches
  publicos) y rompe portabilidad. La defensa contra XSS es la CSP
  estricta, NO HttpOnly cookies cross-origin.
- **NUNCA** logear el JWT, refresh token, magic link token, email
  completo, ni el contenido del codigo 8 chars.
- **NUNCA** mostrar mensajes que filtren si un email existe o no fuera
  de los endpoints permitidos (`register.start` 409 vs `login.start`
  404 con `suggest_register: true` ya lo hace explicito el backend).
- **NUNCA** llamar al refresh sin pasar por el mutex (race condition
  garantizada con concurrent requests).
- **NUNCA** cargar scripts third-party sin SRI (`integrity` attribute).
  Lista permitida hoy: `challenges.cloudflare.com/turnstile/v0/api.js`
  (Cloudflare publica los hashes oficiales por version).

### UI (shadcn + Tailwind v4 + theming)

- **SIEMPRE** componentes shadcn via CLI: `pnpm dlx shadcn@latest add
  <component>`. Modifican/copian en `src/components/ui/`.
- **SIEMPRE** Tailwind v4 con `@theme` inline en `src/styles/globals.css`.
  NO `tailwind.config.ts` (o solo minimo para overrides).
- **SIEMPRE** los tokens CSS del dashboard reflejan los tokens del DS
  del monorepo (`.claude/rules/design-system.md`). Mismos colores
  neutrales, mismas escalas tipograficas, misma logica dark/light.
- **SIEMPRE** dark/light via `next-themes` con `attribute="data-theme"`
  (evita hydration mismatch). Default: `system`. Toggle ciclo
  `dark -> light -> system`.
- **SIEMPRE** iconografia `lucide-react`. NO heroicons, NO radix-icons.
- **SIEMPRE** charts via `pnpm dlx shadcn add chart` (basa en Recharts).
  Tokens de color via CSS vars para respetar dark/light.
- **SIEMPRE** tablas: shadcn `Table` primitives + Tanstack Table v8.
  Para listas grandes (events list, sessions list), agregar Tanstack
  Virtual.
- **SIEMPRE** forms: react-hook-form + Zod + shadcn `Form`,
  `FormField`, `FormControl`, `FormMessage` components.
- **SIEMPRE** toasts via `sonner` (Toaster en root layout).
- **SIEMPRE** loading states con shadcn `Skeleton`. Layouts esqueleto
  realistas (no spinner generico).
- **SIEMPRE** errores con shadcn `Alert` (variant `destructive`) o
  toast.
- **NUNCA** crear `<PrimaryButton>` o wrappers triviales sobre primitivos
  shadcn. Usar `<Button variant="primary">` directo.
- **NUNCA** estilizar shadcn primitives inline con `className`
  modificando comportamiento base. Crear nueva variant CVA si necesario.
- **NUNCA** importar Radix directo (`@radix-ui/react-*`). Pasar por
  shadcn (perdes el theming consistente).
- **NUNCA** Framer Motion / GSAP / Motion One. Tailwind animate +
  `@starting-style` + Radix transitions cubren 100%.
- **NUNCA** hex colors inline en componentes. Usar `var(--color-*)` o
  Tailwind class (`bg-primary`, `text-muted-foreground`).
- **NUNCA** Google Fonts CDN. Self-hosted via `@fontsource/*` (mismas
  fonts del DS: Space Grotesk + Space Mono).

### Data fetching (Tanstack Query v5)

- **SIEMPRE** todo data fetching via `useQuery` / `useMutation` de
  Tanstack Query. NO `useEffect(() => fetch(...))`.
- **SIEMPRE** queryKey estructurado: `['analytics', 'overview', {from,
  to}]`, `['sessions', 'list', {page, page_size}]`. Helpers en
  `features/<X>/api/query-keys.ts`.
- **SIEMPRE** `staleTime` y `gcTime` definidos por endpoint segun cache
  del backend:
  - Analytics agregadas (overview, timeseries, top-pages, etc.):
    `staleTime: 60_000` (matchea TTL backend).
  - `analytics.active-now`: `staleTime: 10_000` + `refetchInterval:
    15_000`.
  - Listados crudos (sessions, events, contacts list): `staleTime:
    30_000`.
  - Detail (sessions/detail): `staleTime: 0` (siempre fresh).
- **SIEMPRE** `refetchOnWindowFocus: false` por default (SPA, no
  background refetches automaticos). Excepcion: queries que usan
  `active-now` o similares.
- **SIEMPRE** persister: `@tanstack/query-sync-storage-persister` con
  compresion `lz-string` para queries `success`. Maxima edad 24h.
- **SIEMPRE** `useMutation` con `onSuccess` que invalida queries
  relacionadas (`queryClient.invalidateQueries`).
- **SIEMPRE** errores rendered via `error` del hook + toast (sonner).
- **NUNCA** llamar `fetch()` directo desde componentes. Pasar siempre
  por `lib/api-client.ts` (que tiene auth interceptor + retry).
- **NUNCA** persistir queries con datos sensibles (lista de contacts).
  Usar `hydrateOptions.defaultShouldDehydrateQuery` para filtrar.

### Forms (react-hook-form + Zod)

- **SIEMPRE** Zod schema en `lib/validation/<feature>.ts` por form.
  Inferir tipo TS con `z.infer<typeof schema>`.
- **SIEMPRE** shadcn `<Form>` + `useForm({ resolver: zodResolver(...) })`.
- **SIEMPRE** validacion async (ej. email unico en register) via
  `mode: 'onBlur'` + `useMutation`.
- **SIEMPRE** mostrar errores via `FormMessage` (shadcn).
- **NUNCA** validacion inline con if/else. Solo Zod.

### Tests

- **SIEMPRE** mirror de `src/` en `tests/unit/`: `src/features/auth/
  components/LoginForm.tsx` → `tests/unit/features/auth/components/
  LoginForm.test.tsx`.
- **SIEMPRE** Vitest + Testing Library + happy-dom.
- **SIEMPRE** MSW para mockear el backend en dev y tests
  (`tests/mocks/handlers.ts`).
- **SIEMPRE** coverage >= 80% per-file en archivos modificados (igual
  que el resto del repo).
- **SIEMPRE** asserts exactos (`expect(x).toBe(42)`, NO
  `toBeGreaterThan(0)`).
- **SIEMPRE** patron AAA + BDD-style en `it()` (`Given/When/Then`).
- **SIEMPRE** E2E con Playwright (suite del repo, `tests/feature/`).
  Specs nuevas en `tests/feature/dashboard/*.spec.ts`.
- **NUNCA** mockear `useAuthStore` directamente. Usar
  `useAuthStore.setState(...)` en `beforeEach` para preparar estado.
- **NUNCA** mockear Tanstack Query directamente. Crear un `QueryClient`
  de test + envolver el componente.
- **NUNCA** llamar al backend real en tests unit. Solo MSW.

### Env vars (categoria client)

- **SIEMPRE** las env vars del dashboard llevan prefijo `NEXT_PUBLIC_`
  (requisito de Next 16 para exponer al bundle). Equivalencia con las
  apps Astro (`PUBLIC_*`):

  | Astro (apps) | Next.js (dashboard) | Fuente |
  |--------------|---------------------|--------|
  | `PUBLIC_API_ENDPOINT` | `NEXT_PUBLIC_API_ENDPOINT` | misma URL del Lambda |
  | `PUBLIC_TURNSTILE_SITEKEY` | `NEXT_PUBLIC_TURNSTILE_SITEKEY` | mismo sitekey |
  | (no aplica) | `NEXT_PUBLIC_DASHBOARD_URL` | `https://admin.portfolio.{env}.the-full-stack.com` |
  | (no aplica) | `NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS` | `30000` (refresh 30s antes del exp) |

- **SIEMPRE** validar `NEXT_PUBLIC_*` en cold start con Zod en
  `src/lib/env.ts`. Si falta una, fail el build.
- **SIEMPRE** las vars se publican via `python devtools/run.py
  sync_secrets --env=<X> --category=client`. NUNCA `gh variable set` a
  mano (ver `.claude/rules/client-env-sync.md`).
- **SIEMPRE** el catalogo en `devtools/sync_secrets/catalog.py` lista
  las nuevas keys del dashboard.
- **NUNCA** marcar `NEXT_PUBLIC_*` como GH Secret. Son Variables
  (publicas por contrato).
- **NUNCA** leer `docker/env/client/.{env}` con Read tool. Extraer keys
  puntuales con `grep -m1 ^KEY=` (ver `.claude/rules/env-files.md`).

### Deploy (Cloudflare Pages)

- **SIEMPRE** 3 projects Cloudflare Pages: `portfolio-dashboard-dev`,
  `portfolio-dashboard-stage`, `portfolio-dashboard` (prod sin sufijo).
- **SIEMPRE** branch mapping: `dev` -> dev project, `stage` -> stage,
  `main` -> prod.
- **SIEMPRE** custom domain attached al provisionar:
  - `admin.portfolio.dev.the-full-stack.com` (dev)
  - `admin.portfolio.stage.the-full-stack.com` (stage)
  - `admin.portfolio.the-full-stack.com` (prod)
- **SIEMPRE** SSL cert se emite automatico por Cloudflare ACM al
  attach del custom domain (no manual).
- **SIEMPRE** build command: `pnpm install --frozen-lockfile && pnpm
  --filter @portfolio/dashboard... build` (`...` incluye deps del
  workspace).
- **SIEMPRE** output dir: `dashboard/out` (Next 16 export genera `out/`
  por default).
- **SIEMPRE** `dashboard/public/_redirects` con `/* /index.html 200`
  para client-side routing (rutas dinamicas).
- **SIEMPRE** `dashboard/public/_headers` con CSP estricta + cache
  headers + HSTS. Ver capitulo deploy del knowledge tree.
- **SIEMPRE** `devtools/cloudflare_setup/config.py` declara el
  dashboard como nuevo `AppConfig` con `app_type='nextjs'` y
  `build_output_dir='out'`. El comando `cloudflare_setup all
  --env=<X>` deploya los 7 apps (6 Astro + 1 Next).
- **SIEMPRE** `.github/workflows/deploy-apps.yml` extiende la matrix
  con `include` para agregar el dashboard (dist-dir distinto).
- **SIEMPRE** preview_branch_includes en `[<branch>]` para evitar que
  cada project construya todas las ramas (ver memory
  `cloudflare-pages-preview-branch-fix`).
- **NUNCA** wrangler para crear el project (no soporta git-connected
  con env vars correctos). Solo REST API via devtools.
- **NUNCA** modificar la config del project en la consola Cloudflare:
  el siguiente `cloudflare_setup projects` la revierte.

### CI/CD

- **SIEMPRE** el dashboard pasa por `ci.yml` (lint + build de las apps
  incluyendo dashboard) en cada PR.
- **SIEMPRE** `deploy-apps.yml` con `environment: <stage>` para leer
  GH Variables correctas (NEXT_PUBLIC_*).
- **SIEMPRE** branch-flow-guard sigue aplicando: PR `dev -> stage` y
  `stage -> main` con merge commit (NO rebase — ver
  `.claude/rules/git-workflow.md`).
- **SIEMPRE** el dashboard se mergea junto al backend que consume
  (auth + analytics) cuando ambas APIs esten en el mismo env. Hasta
  entonces, el dashboard usa MSW.

## Comando canonico (development)

```bash
# Setup inicial (una vez)
cd dashboard
pnpm dlx shadcn@latest init                       # crea components.json
pnpm dlx shadcn@latest add button input form ...  # primeros componentes
cd ..

# Trabajo diario
pnpm install                                      # desde root, workspace
pnpm --filter @portfolio/dashboard dev            # localhost:3000
pnpm --filter @portfolio/dashboard typecheck
pnpm --filter @portfolio/dashboard lint
pnpm --filter @portfolio/dashboard test
pnpm --filter @portfolio/dashboard build          # genera dashboard/out/

# Pre-push
pnpm --filter @portfolio/dashboard lint:fix
pnpm --filter @portfolio/dashboard typecheck
pnpm --filter @portfolio/dashboard test:coverage
pnpm --filter @portfolio/dashboard build

# Sync env vars
python devtools/run.py sync_secrets --env=dev --category=client --dry-run
python devtools/run.py sync_secrets --env=dev --category=client

# Provisionar Cloudflare Pages (primera vez por env)
export CLOUDFLARE_API_TOKEN=$(grep -m1 ^CLOUDFLARE_API_TOKEN= docker/env/dev-cli/.prod | cut -d= -f2-)
export ACCOUNT_ID=$(grep -m1 ^CLOUDFLARE_ACCOUNT_ID= docker/env/dev-cli/.prod | cut -d= -f2-)
python devtools/run.py cloudflare_setup all --env=dev

# Deploy diario
git push origin dev   # auto-deploya via deploy-apps.yml
```

## Verificacion (antes de declarar listo)

```bash
# 1. Lint + format + typecheck
pnpm --filter @portfolio/dashboard lint
pnpm --filter @portfolio/dashboard typecheck

# 2. Unit tests
pnpm --filter @portfolio/dashboard test:coverage  # >= 80%

# 3. Build estatico
pnpm --filter @portfolio/dashboard build
ls -lah dashboard/out/index.html dashboard/out/_next  # debe existir

# 4. Preview manual (al menos los flujos golden path)
pnpm --filter @portfolio/dashboard preview &
curl -sI http://localhost:3000/ | head -3        # 200
curl -sI http://localhost:3000/login/ | head -3  # 200 (trailingSlash)

# 5. E2E si aplica (cuando el backend este vivo)
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `app/api/*/route.ts` | Static export fail al build | Llamar Lambda externo |
| `middleware.ts` para auth | No corre en SPA | `AuthGuard` Client Component |
| `<Image src=... unoptimized={false}>` | Necesita server runtime | `images.unoptimized: true` global |
| `useEffect(() => fetch(...))` | Sin cache, sin invalidation, sin retry | Tanstack Query `useQuery` |
| Concurrent refresh requests | Backend revoca familia por reuse | Mutex en `lib/api-client.ts` |
| Tokens en query (`?access=...`) | Leak via Referer + browser history | Fragment hash en callback |
| Cargar script third-party sin `integrity` (SRI) | Script comprometido roba el token de localStorage | SRI obligatorio + CSP `script-src 'self' + allowlist con hash` |
| HttpOnly cookie cross-origin del API al dashboard (`SameSite=None; Domain=.the-full-stack.com`) | Vector CSRF en los 6 niches publicos + rompe portabilidad | Tokens en `localStorage` + CSP estricta (decision documentada arriba) |
| CSP con `unsafe-inline` o `unsafe-eval` | XSS de inline scripts = robo de tokens | CSP `script-src 'self'` con SRI para third-party |
| Promote a `components/ui/` con 1 uso | Premature abstraction | Vive en `features/<X>/components/` |
| Server Component async fetch | Build fail en export | `'use client'` + Tanstack Query |
| Importar `@radix-ui/react-*` directo | Pierde theming shadcn | Pasar por `components/ui/<comp>` |
| Framer Motion | 30KB+, no necesario | Tailwind animate + `@starting-style` |
| Hex inline (`color: '#FF0000'`) | Rompe dark mode | `text-destructive` o `var(--color-destructive)` |
| Google Fonts CDN | GDPR, CSP estricta | `@fontsource/*` |
| `find` / `grep -E` / `grep -rn` en Bash | Aliases rotos en WSL2 | Glob/Grep/Read tools |

## Referencias cruzadas

- Skill: `/dashboard-stack` (resumen ejecutivo + decisiones)
- Knowledge tree: `.claude/docs/dashboard/` (7 capitulos)
- Plan: `docs/specs/dashboard/` (efimero, se elimina al mergear)
- Backend auth: `docs/specs/01-auth-infra-basics/` + `02-auth-mfa/`
  (pending de implementar)
- Backend analytics: `docs/specs/analytics-dashboard-api/` (pending)
- Estandar de subdominios: `.claude/docs/subdomain-standard/`
- Cloudflare Pages: `.claude/docs/cloudflare/` + skill
  `cloudflare-deploy`
- Sync secrets categoria client: `.claude/rules/client-env-sync.md`
- CI/CD pipeline: `.claude/rules/ci-cd-pipeline.md`
- Design system: `.claude/rules/design-system.md`
- Git workflow + branches: `.claude/rules/git-workflow.md`
- Plan format: `.claude/rules/plan-format.md`
- TDD obligatorio: `.claude/rules/tdd-workflow.md` (heredado)
- Verify-before-done: `.claude/rules/verify-before-done.md`
