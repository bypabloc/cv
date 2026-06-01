# Dashboard SPA — Knowledge Tree

> Knowledge tree del dashboard admin del portfolio
> (`admin.portfolio.{dev|stage|prod}.the-full-stack.com`). Next.js
> 16.2.6 SPA + React 19.2.6 + shadcn + Tanstack Query v5 + Cloudflare
> Pages.
>
> Esta es la **zona producto** (Knowledge Tree): cambia raramente,
> audiencia = reviewers. La zona harness del plan es efimera
> (`docs/specs/dashboard/`).

## Cuando leer

| Tema | Archivo | Cuando |
|------|---------|--------|
| Decisiones globales + esta tabla de navegacion | [README.md](README.md) | Primera lectura, decisiones no-reabribles |
| Stack: Next.js 16.2.6 + React 19.2.6 + TS 6 + Biome + configs base | [01-stack.md](01-stack.md) | Antes de tocar `next.config.ts`, `tsconfig.json`, `biome.json`, `package.json` |
| Estructura Hybrid Atomic Design (folders, decision tree) | [02-structure.md](02-structure.md) | Antes de crear o mover un componente |
| UI: shadcn + Tailwind v4 + theming + Radix + lucide + charts + React 19 patterns | [03-ui.md](03-ui.md) | Antes de agregar componente shadcn, definir token, crear variant, decidir form pattern |
| Auth: JWT en `localStorage` + Tanstack Query mutex + Zustand + magic link + BroadcastChannel | [04-auth.md](04-auth.md) | Antes de tocar fetch wrapper, auth store, protected routes, callback |
| Deploy: Cloudflare Pages + devtools + GH Actions + env vars | [05-deploy.md](05-deploy.md) | Antes de cambiar `deploy-apps.yml`, `cloudflare_setup`, `sync_secrets` |
| Testing: Vitest 2 + Testing Library v16 + MSW v2 + Playwright | [06-testing.md](06-testing.md) | Antes de escribir un test, configurar MSW handlers, fixtures |

## Decisiones no-reabribles

Estas decisiones se cerraron en el dialogo previo (Q&A inicial) y NO se
vuelven a discutir en la fase de implementacion:

1. **Framework**: Next.js 16.2.6 con `output: 'export'` estricto. NO
   Vite, NO Astro, NO Next con SSR/RSC. Razon: monorepo consistency +
   ecosystem; user choice.
2. **React 19.2.6** (obligatorio en Next 16.x). Compiler stable habilitado.
   Hooks nuevos disponibles (`useActionState`, `useFormStatus`,
   `useOptimistic`, `useDeferredValue` con `initialValue`, `useEffectEvent`).
   `ref` como prop normal (sin `forwardRef`). Document Metadata nativo.
3. **Routing**: App Router. NO Pages Router. Todas las pages Client
   Components.
4. **TypeScript**: 6.x strict + `noUncheckedIndexedAccess`. NO `any`.
5. **Linter**: Biome v2 (sin ESLint). Override para `src/components/ui/*`.
6. **CSS**: Tailwind v4 (CSS-first config via `@theme` inline + plugin
   `@tailwindcss/postcss`). NO `tailwind.config.ts`.
7. **Componentes**: shadcn/ui (Radix primitives, copy-paste; codegen
   sin `forwardRef`).
8. **Data fetching**: Tanstack Query v5 + `useSuspenseQuery` para data
   required + persister `localStorage` con compresion lz-string.
9. **State global**: Zustand 5 (auth + theme). Tanstack Query para
   data. useState local para UI ephemeral.
10. **Forms**: react-hook-form 7 + Zod + shadcn `<Form>` para forms
    complejos (auth, multi-step). `useActionState` + `useFormStatus`
    para forms simples (1-2 fields, single submit).
11. **Theme**: next-themes con `attribute="data-theme"` (evita
    hydration mismatch).
12. **Iconos**: lucide-react.
13. **Charts**: `pnpm dlx shadcn add chart` (Recharts wrapper). Requiere
    override `react-is@19.2.6` en `package.json`.
14. **Tablas**: Tanstack Table v8 + shadcn primitives + Tanstack Virtual
    para listas grandes.
15. **Toasts**: sonner.
16. **Tests**: Vitest 2 + Testing Library v16 (React 19 support) + MSW
    v2 (con polyfill BroadcastChannel en happy-dom). Playwright E2E
    (suite del monorepo).
17. **Estructura**: **Hybrid Atomic Design** —
    `src/components/ui/` (genericos, 2+ features) +
    `src/features/<X>/components/` (especificos por dominio). NO Atomic
    Design clasico con `atoms/molecules/organisms`.
18. **Carpeta**: `dashboard/` en root (no `apps/dashboard/`). User
    choice explicito. Entra a pnpm workspace como `@portfolio/dashboard`.
19. **Subdominio**: `admin.portfolio.{env}.the-full-stack.com`. Sigue
    `subdomain-standard`.
20. **Deploy**: Cloudflare Pages via `devtools/cloudflare_setup` +
    `deploy-apps.yml`. Mismo pipeline que las 6 apps Astro.
21. **Env vars**: prefijo `NEXT_PUBLIC_*` (requisito Next 16 para
    exponer al bundle). Sincronizadas via
    `sync_secrets --category=client`.
22. **Auth — storage**: tokens (access, refresh, temp) en `localStorage`
    via Zustand `persist`. **NO HttpOnly cookies** — el dashboard es
    SPA cross-origin (subdomain admin vs api), una HttpOnly cookie
    requeriria `SameSite=None` cross-site + `Domain=.the-full-stack.com`
    abriendo CSRF en los 6 niches publicos y rompiendo portabilidad.
    Defensa: CSP estricta sin `unsafe-inline`/`unsafe-eval` + SRI en
    third-party + access JWT corto (15 min) + family_id refresh rotation.
    NUNCA tokens en URL query.
23. **Magic link UX**: backend redirect 302 a `/auth/callback#access=...`
    (fragment hash, NO query). Frontend decodea + guarda en
    `localStorage` via Zustand + limpia con `history.replaceState`.
24. **Multi-tab**: BroadcastChannel API canal `portfolio_auth` + fallback
    `storage` event de `localStorage`.
25. **React Compiler**: habilitado via `reactCompiler: true` (stable en
    Next 16). Opt-out per file con `'use no memo'` solo si rompe algo
    medido.
26. **Plan scope**: SOLO frontend dashboard. Las APIs `/auth` y
    `/analytics` se asumen existentes. Mientras no esten deployadas,
    MSW v2 provee mocks.

## Versiones canonicas (mayo 2026)

Resumen — ver tabla extendida en
[.claude/skills/dashboard-stack/SKILL.md](../../skills/dashboard-stack/SKILL.md):

- Next.js **16.2.6** | React + React DOM **19.2.6** | TypeScript **6.0.6**
- Biome **2.0.0+** | Tailwind **4.1.4** + `@tailwindcss/postcss`
- shadcn/ui latest (React 19 support, sin `forwardRef`)
- Tanstack Query/Persist/Table/Virtual **5.52.3** / **8.20.5** / **3.5.1**
- Zustand **5.0.14** (Jan 2026 state consistency fix)
- react-hook-form **7.53.0** | Zod **3.24.1** | @hookform/resolvers **3.4.2**
- Recharts **2.14.2** + override `react-is@19.2.6`
- next-themes **0.4.8** | sonner **1.7.2** | lucide-react **0.416.0**
- MSW **2.3.2** | Vitest **2.2.5** + Testing Library **16.1.0** + happy-dom **16.5.1**
- Playwright **1.48.2**
- babel-plugin-react-compiler **19.0.0-beta.17**
- Node >=24, pnpm 11.0.9

## Reglas duras (siempre activas)

Ver [.claude/rules/dashboard.md](../../rules/dashboard.md) — esa es la
fuente de verdad enforced. Resumen aqui:

- **SIEMPRE** Client Components (`'use client'`).
- **SIEMPRE** todas las API calls via `lib/api-client.ts` (fetch wrapper
  con auth interceptor + refresh mutex).
- **SIEMPRE** tokens (access, refresh, temp) en `localStorage` via
  Zustand `persist`.
- **SIEMPRE** mutex para concurrent refresh (1 sola call in-flight).
- **SIEMPRE** Hybrid Atomic: `components/ui/` (genericos, 2+ features)
  vs `features/<X>/components/` (especificos).
- **SIEMPRE** Turnstile en register.start y login.start.
- **SIEMPRE** `ref` como prop normal (NO `forwardRef`) en componentes
  nuevos. shadcn 2.x ya migrado.
- **SIEMPRE** React Compiler habilitado (`reactCompiler: true`).
- **SIEMPRE** Rules of React (el Compiler las enforces).
- **SIEMPRE** forms complejos con react-hook-form + Zod + shadcn
  `<Form>` + Tanstack `useMutation`. Forms simples con `useActionState`.
- **NUNCA** API routes, middleware/proxy, Server Components con async
  fetch, Server Actions, `'use cache'`.
- **NUNCA** tokens en URL query (magic link usa fragment hash).
- **NUNCA** logear JWT, refresh, magic link token, codigo.
- **NUNCA** `forwardRef` en componentes nuevos.
- **NUNCA** Framer Motion, Google Fonts CDN, hex inline.

## Diagrama de alto nivel

```text
Browser (admin.portfolio.{env}.the-full-stack.com)
  -> Cloudflare Pages (static HTML/JS/CSS de dashboard/out/)
       -> Next.js 16 SPA bundle hydration
            -> React 18 (App Router, Client Components)
                 -> Zustand (auth, theme)
                 -> Tanstack Query (data fetching + persist localStorage)
                      -> lib/api-client.ts (fetch + JWT + refresh mutex)
                           -> https://api.portfolio.{env}.the-full-stack.com
                                -> Lambda auth (register/login/verify/refresh/logout)
                                -> Lambda analytics (overview/timeseries/sessions/...)
                                -> Lambda contact_form (referencia)
                                -> Lambda tracking_pixel (referencia)
  
  Magic link callback:
    User clicks link en email -> GET https://api.portfolio.../auth?...&token=X
      -> Lambda auth verifica token + emite JWTs
      -> HTTP 302 Location: https://admin.portfolio.../auth/callback#access=Y&refresh=Z
        -> Browser carga callback page (SPA)
          -> page.tsx decodea hash, guarda en Zustand
          -> history.replaceState para limpiar fragment
          -> redirect a /dashboard
```

## Stack — resumen visual

```
┌──────────────────────────────────────────────────────────────────────┐
│ Dashboard SPA Stack (mayo 2026)                                       │
├──────────────────────────────────────────────────────────────────────┤
│ Runtime          | Node 24 (build), browser (runtime)                 │
│ Framework        | Next.js 16 (App Router + output: 'export')         │
│ UI library       | React 18.3.x                                       │
│ Language         | TypeScript 6.x strict                              │
│ Linter/Formatter | Biome v2 (sin ESLint)                              │
│ CSS              | Tailwind v4 (@theme inline)                        │
│ Components       | shadcn/ui (Radix primitives, copy-paste)           │
│ Icons            | lucide-react                                       │
│ Charts           | Recharts (via shadcn add chart)                    │
│ Tables           | Tanstack Table v8 + Tanstack Virtual               │
│ Data fetching    | Tanstack Query v5 + persist (lz-string)            │
│ Forms            | react-hook-form + Zod + shadcn <Form>              │
│ State (auth)     | Zustand 5 (in-memory access, persist refresh)      │
│ State (theme)    | next-themes (data-theme attribute)                 │
│ Toasts           | sonner                                             │
│ Date helpers     | date-fns o Temporal API si estable                 │
│ Tests (unit)     | Vitest + Testing Library + happy-dom               │
│ Tests (mocks)    | MSW (Mock Service Worker)                          │
│ Tests (E2E)      | Playwright (suite del monorepo)                    │
│ Deploy           | Cloudflare Pages (REST API via devtools)           │
│ CI               | GitHub Actions (deploy-apps.yml matrix +1 entry)   │
│ Auth backend     | Lambda auth (planes 01-02, pending)                │
│ Data backend     | Lambda analytics (plan analytics-dashboard-api)    │
└──────────────────────────────────────────────────────────────────────┘
```

## Subdominios

| Env | Subdomain | Pages project | Branch GitHub |
|-----|-----------|---------------|---------------|
| dev | `admin.portfolio.dev.the-full-stack.com` | `portfolio-dashboard-dev` | `dev` |
| stage | `admin.portfolio.stage.the-full-stack.com` | `portfolio-dashboard-stage` | `stage` |
| prod | `admin.portfolio.the-full-stack.com` | `portfolio-dashboard` | `main` |

## Endpoints API consumidos

Backend en `https://api.portfolio.{env}.the-full-stack.com`:

### POST /auth (Lambda `auth`, plan 01)

| Operation | Action | Body | Response |
|-----------|--------|------|----------|
| `register` | `start` | `{email, cf_turnstile_response}` | `201 {temp_token, user_id, expires_in: 300}` |
| `register` | `verify-magic-link` (GET) | query `?token=<X>` | `302 -> /auth/callback#access=...&refresh=...` |
| `register` | `verify-code` | `{code, temp_token}` | `200 {access_token, refresh_token, expires_in, user}` |
| `login` | `start` | `{email, cf_turnstile_response, password?}` | `200 {temp_token, methods: [...]}` o `404 {suggest_register: true}` |
| `login` | `verify-magic-link` (GET) | idem | idem |
| `login` | `verify-code` | `{code, temp_token}` | `200 {access_token, refresh_token, expires_in, user}` |
| `login` | `verify-password` | `{password, temp_token}` | `200` (con MFA si configurado) |
| `login` | `verify-totp` | `{code, temp_token}` (plan 02) | `200` |
| `verify` | `set-password` | `{password, temp_token}` | `204` |
| `verify` | `resend-code` | `{temp_token}` | `200` |
| `session` | `refresh` | refresh JWT (HttpOnly cookie o body) | `200 {access_token, refresh_token, expires_in}` |
| `session` | `logout` | access JWT | `204` |
| `mfa` | `setup-totp` (plan 02) | access JWT | `200 {secret, otpauth_url, qr_code_svg}` |
| `mfa` | `confirm-totp` (plan 02) | `{code}` | `204` |
| `mfa` | `recovery-codes-generate` (plan 02) | access JWT | `200 {codes: [...]}` |
| `webauthn` | `register-options` (plan 02) | access JWT | `200 {challenge, rp, user, pubKeyCredParams, ...}` |
| `webauthn` | `register-verify` (plan 02) | attestation | `201 {credential_id}` |
| `webauthn` | `login-options` (plan 02) | `{email}` | `200 {challenge, allowCredentials}` |
| `webauthn` | `login-verify` (plan 02) | assertion | `200 {access_token, refresh_token, ...}` |

### GET /analytics (Lambda `analytics`, plan analytics-dashboard-api)

| Operation | Action | Query | Response |
|-----------|--------|-------|----------|
| `analytics` | `overview` | `from, to` | `{sessions, visits, events, contacts, unique_visitors, ...}` |
| `analytics` | `timeseries` | `from, to, bucket, niche?, event_type?` | `[{ts, count}, ...]` |
| `analytics` | `top-pages` | `from, to, limit, niche?` | `[{path, views, ...}, ...]` |
| `analytics` | `top-referrers` | `from, to, limit` | `[{referrer, sessions, ...}, ...]` |
| `analytics` | `top-niches` | `from, to` | `[{niche, sessions, ...}, ...]` |
| `analytics` | `active-now` | (none) | `{count, sessions: [...]}` |
| `analytics` | `retention` | `from, to` | `{new, returning, ...}` |
| `events` | `distribution` | `from, to` | `[{event_type, count, share}, ...]` |
| `events` | `list` | `from, to, page, page_size` | `{items, total, page, page_size}` |
| `events` | `heatmap` | `from, to` | `[[dia_semana, hora, count], ...]` |
| `sessions` | `list` | `from, to, page, page_size` | `{items, total, ...}` |
| `sessions` | `detail` | `session_id` | `{session, visits, event_count}` |
| `visits` | `list` | idem sessions | idem |
| `visits` | `landing-pages` | `from, to, limit` | `[{path, count, ...}, ...]` |
| `geo` | `by-country` | `from, to` | `[{country, sessions, ...}, ...]` |
| `devices` | `breakdown` | `from, to` | `{device, browser, os: [...]}` |
| `funnel` | `conversion` | `from, to` | `{session, visit, contact: {...}}` |
| `contacts` | `list` | `from, to, page, page_size, status?` | `{items, total, ...}` |
| `contacts` | `by-status` | `from, to` | `[{status, count}, ...]` |

## Estado del plan

Ver [docs/specs/dashboard/README.md](../../../docs/specs/dashboard/README.md) — fases + estado por fase.

## Bibliografia interna

- `.claude/rules/dashboard.md` — reglas duras (enforced)
- `.claude/skills/dashboard-stack/SKILL.md` — skill invocable
- `docs/specs/dashboard/` — plan de implementacion (efimero)
- `docs/specs/01-auth-infra-basics/` — backend auth (plan 01, pending)
- `docs/specs/02-auth-mfa/` — backend auth MFA (plan 02, pending)
- `docs/specs/analytics-dashboard-api/` — backend analytics (pending)
- `.claude/rules/lambda-controller.md` — formato del backend
- `.claude/rules/secrets-strategy.md` + `client-env-sync.md` — env vars
- `.claude/rules/ci-cd-pipeline.md` — workflow deploy
- `.claude/docs/cloudflare/` — Cloudflare Pages knowledge
- `.claude/docs/subdomain-standard/` — patron de subdominios
- `.claude/rules/design-system.md` — tokens CSS, dark/light, fonts
- `.claude/rules/git-workflow.md` — branches, commits, PRs
- `.claude/rules/plan-format.md` — formato de plan
- `.claude/rules/verify-before-done.md` — gate de cierre
