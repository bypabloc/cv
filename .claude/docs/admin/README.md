# Admin SPA — Knowledge Tree

> Knowledge tree del admin del portfolio
> (`admin.portfolio.{dev|stage|prod}.the-full-stack.com`). Next.js
> 16.2.6 SPA + React 19.2.6 + shadcn + Tanstack Query v5 + Cloudflare
> Pages.
>
> Esta es la **zona producto** (Knowledge Tree): cambia raramente,
> audiencia = reviewers. La zona harness del plan es efimera
> (`docs/specs/a-admin/`).

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
18. **Carpeta**: `admin/` en root (no `apps/admin/`). User
    choice explicito. Entra a pnpm workspace como `@portfolio/admin`.
19. **Subdominio**: `admin.portfolio.{env}.the-full-stack.com`. Sigue
    `subdomain-standard`.
20. **Deploy**: Cloudflare Pages via `devtools/cloudflare_setup` +
    `deploy-apps.yml`. Mismo pipeline que las 6 apps Astro.
21. **Env vars**: prefijo `NEXT_PUBLIC_*` (requisito Next 16 para
    exponer al bundle). Sincronizadas via
    `sync_secrets --category=client`.
22. **Auth — storage**: tokens (access, refresh, temp) en `localStorage`
    via Zustand `persist`. **NO HttpOnly cookies** — el admin es
    SPA cross-origin (subdomain admin vs api), una HttpOnly cookie
    requeriria `SameSite=None` cross-site + `Domain=.the-full-stack.com`
    abriendo CSRF en los 6 niches publicos y rompiendo portabilidad.
    Defensa: CSP (`script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'`;
    `'unsafe-inline'` es inevitable en Next `output:'export'` por los
    inline scripts del RSC, pero NO `'unsafe-eval'`; connect-src acotado +
    object-src/frame-ancestors none) + SRI en third-party + access JWT
    corto (15 min) + family_id refresh rotation. NUNCA tokens en URL query.
23. **Magic link UX**: backend redirect 302 a `/auth/callback#access=...`
    (fragment hash, NO query). Frontend decodea + guarda en
    `localStorage` via Zustand + limpia con `history.replaceState`.
24. **Multi-tab**: BroadcastChannel API canal `portfolio_auth` + fallback
    `storage` event de `localStorage`.
25. **React Compiler**: habilitado via `reactCompiler: true` (stable en
    Next 16). Opt-out per file con `'use no memo'` solo si rompe algo
    medido.
26. **Plan scope (a-admin)**: SOLO frontend del admin — scaffold +
    app shell (feature `admin-shell`: header + sidebar + nav + layout
    protegido) + auth (feature `auth`) + gestion total (features
    `settings`, `sessions-mgmt`, `users-admin`). La UI de metricas
    (features `analytics`, `sessions` de tracking, `events`, `visits`,
    `geo`, `devices`, `funnel`, `contacts`) NO es de este plan: se monta
    dentro del mismo app shell en el plan `b-analytics-api`. El Lambda
    `auth` (planes 01-02) y el Lambda `users` (3 operations / 15 actions)
    ya estan desplegados; el Lambda `analytics` lo provee
    `b-analytics-api`. Mientras una API no este viva, MSW v2 provee mocks.

## Versiones canonicas (mayo 2026)

Resumen — ver tabla extendida en
[.claude/skills/admin-stack/SKILL.md](../../skills/admin-stack/SKILL.md):

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

Ver [.claude/rules/admin.md](../../rules/admin.md) — esa es la
fuente de verdad enforced. Resumen aqui:

- **SIEMPRE** Client Components (`'use client'`).
- **SIEMPRE** todas las API calls del admin via `lib/api-client.ts`
  (fetch wrapper con auth interceptor + refresh mutex).
- **SIEMPRE** tokens (access, refresh, temp) en `localStorage` via
  Zustand `persist`.
- **SIEMPRE** mutex para concurrent refresh (1 sola call in-flight).
- **SIEMPRE** Hybrid Atomic: `components/ui/` (genericos, 2+ features)
  vs `features/<X>/components/` (especificos).
- **SIEMPRE** Turnstile en login.check-email (unico punto de entrada).
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
  -> Cloudflare Pages (static HTML/JS/CSS de admin/out/)
       -> Next.js 16 SPA bundle hydration
            -> React 19 (App Router, Client Components)
                 -> Zustand (auth, theme)
                 -> Tanstack Query (data fetching + persist localStorage)
                      -> lib/api-client.ts (fetch + JWT + refresh mutex)
                           -> https://api.portfolio.{env}.the-full-stack.com
                                -> Lambda auth (register/login/verify/refresh/logout/mfa/webauthn)
                                -> Lambda users (profile/status/admin)
                                -> Lambda analytics (overview/timeseries/sessions/...) [plan b-analytics-api]
                                -> Lambda contact_form (referencia)
                                -> Lambda tracking_pixel (referencia)
  
  Magic link callback:
    User clicks link en email -> GET https://api.portfolio.../auth?...&token=X
      -> Lambda auth verifica token + emite JWTs
      -> HTTP 302 Location: https://admin.portfolio.../auth/callback#access=Y&refresh=Z
        -> Browser carga callback page (SPA)
          -> page.tsx decodea hash, guarda en Zustand
          -> history.replaceState para limpiar fragment
          -> redirect al app shell (/ del area protegida)
```

## Stack — resumen visual

```
┌──────────────────────────────────────────────────────────────────────┐
│ Admin SPA Stack (mayo 2026)                                           │
├──────────────────────────────────────────────────────────────────────┤
│ Runtime          | Node 24 (build), browser (runtime)                 │
│ Framework        | Next.js 16 (App Router + output: 'export')         │
│ UI library       | React 19.2.x                                       │
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
│ Auth backend     | Lambda auth + Lambda users (desplegados)           │
│ Data backend     | Lambda analytics (plan b-analytics-api)            │
└──────────────────────────────────────────────────────────────────────┘
```

## Subdominios

| Env | Subdomain | Pages project | Branch GitHub |
|-----|-----------|---------------|---------------|
| dev | `admin.portfolio.dev.the-full-stack.com` | `portfolio-admin-dev` | `dev` |
| stage | `admin.portfolio.stage.the-full-stack.com` | `portfolio-admin-stage` | `stage` |
| prod | `admin.portfolio.the-full-stack.com` | `portfolio-admin` | `main` |

## Endpoints API consumidos

Backend en `https://api.portfolio.{env}.the-full-stack.com`. El admin
consume el Lambda `auth` (auth + MFA + WebAuthn) y el Lambda `users`
(profile / status / admin) en el plan `a-admin`; el Lambda `analytics`
es del plan `b-analytics-api`.

### POST /auth (Lambda `auth` desplegado: 6 operations / 26 actions)

> El Lambda `auth` ya esta implementado y desplegado (dev/stage/prod).
> Reglas: `.claude/rules/auth-system.md`, docs: `.claude/docs/auth-system/`.
> Todo va por `POST /auth` body `{operation, action, data}` salvo los
> `verify-magic-link` (GET callback). `_meta` lo inyecta `http_handler`.

| Operation | Action | Body (data) | Auth | Response |
|-----------|--------|-------------|------|----------|
| `register` | `start` | `{email, cf_turnstile_response, niche?}` | — | `{temp_token, user_id, expires_in: 300}` |
| `register` | `verify-magic-link` (GET) | `?token=<X>` | — | `302 -> /auth/callback#access=...&refresh=...` |
| `register` | `verify-code` | `{code, temp_token}` | — | `{access_token, refresh_token, expires_in, user}` |
| `login` | `start` | `{email, cf_turnstile_response, password?, niche?}` | — | `{temp_token, methods: [...]}` o `404 {suggest_register: true}` |
| `login` | `verify-magic-link` (GET) | `?token=<X>` | — | idem register |
| `login` | `verify-code` | `{code, temp_token}` | — | `{access_token, refresh_token, expires_in, user}` |
| `login` | `verify-password` | `{password, temp_token}` | — | `{access_token,...}` o (con MFA) `{temp_token step2, methods}` |
| `login` | `verify-totp` | `{code, temp_token step2}` | — | `{access_token, refresh_token, ...}` |
| `verify` | `set-password` | `{password, temp_token}` | — | `{access_token, ...}` |
| `verify` | `resend-code` | `{temp_token}` | — | `200` |
| `session` | `refresh` | `{refresh_token}` | — | `{access_token, refresh_token, expires_in}` (rotacion) |
| `session` | `logout` | `{access_token, refresh_token?}` | — | `204` |
| `mfa` | `setup-totp` | `{}` | access JWT | `{secret_b32, otpauth_url}` (front renderiza el QR) |
| `mfa` | `confirm-totp` | `{code}` (6 digitos) | access JWT | `204` (1er metodo revoca familia, AC-27) |
| `mfa` | `setup-email-code` | `{}` | access JWT | `204` |
| `mfa` | `set-preferred` | `{kind: 'totp'\|'email_code'}` | access JWT | `204` |
| `mfa` | `disable` | `{kind}` | access JWT | `204` o `409` (guard MUST_KEEP_ONE) |
| `mfa` | `list` | `{}` | access JWT | `{methods: [...], webauthn_count, total_mfa}` |
| `mfa` | `recovery-codes-generate` | `{}` | access JWT | `{codes: [...]}` (10, una sola vez) |
| `mfa` | `recovery-codes-consume` | `{temp_token step2, code}` (10 chars) | temp step2 | `{access_token, ...}` o `403 RECOVERY_REQUIRES_STRONG_FACTOR` |
| `webauthn` | `register-options` | `{}` | access JWT | `{challenge_id, options}` |
| `webauthn` | `register-verify` | `{challenge_id, response, nickname?}` | access JWT | `{credential_id}` (1er metodo revoca familia) |
| `webauthn` | `login-options` | `{email}` | — | `{challenge_id, options}` |
| `webauthn` | `login-verify` | `{challenge_id, response}` | — | `{access_token, refresh_token, ...}` |
| `webauthn` | `list-credentials` | `{}` | access JWT | `{credentials: [...]}` |
| `webauthn` | `delete-credential` | `{credential_id}` | access JWT | `204` o `409` (guard MUST_KEEP_ONE) |

### POST /users (Lambda `users` desplegado: 3 operations / 15 actions)

> Todas requieren access JWT. `require_active_user` de `users` devuelve
> **403** `ACCOUNT_DISABLED`/`ACCOUNT_LOCKED` (no 401) para un user con
> JWT valido pero disabled/locked. La operation `admin` valida whitelist
> SSM (`/portfolio/admin-emails`): no-admin -> **404 NOT_FOUND**.
> Las features `settings`, `sessions-mgmt` y `users-admin` del admin
> consumen estas actions.

| Operation | Action | Body (data) | Response |
|-----------|--------|-------------|----------|
| `profile` | `get` | `{}` | perfil del user autenticado |
| `profile` | `update` | `{display_name?}` | perfil actualizado |
| `profile` | `change-email` | `{new_email}` | inicia cambio (envia confirmacion) |
| `profile` | `confirm-email-change` | `{token}` | confirma el cambio |
| `profile` | `delete-account` | `{confirm}` | soft-delete + anonimiza + blacklist familias |
| `status` | `get` | `{}` | estado de la cuenta + sesion actual |
| `status` | `list-sessions` | `{}` | sesiones activas del user |
| `status` | `revoke-session` | `{session_id}` | revoca una sesion (NO la actual -> 400) |
| `admin` | `list-users` | `{page?, page_size?}` | lista usuarios |
| `admin` | `get-user` | `{user_id}` | detalle |
| `admin` | `disable-user` | `{user_id}` | status disabled |
| `admin` | `enable-user` | `{user_id}` | status active |
| `admin` | `delete-user` | `{user_id}` | soft-delete |
| `admin` | `force-logout` | `{user_id}` | blacklist sus familias |
| `admin` | `list-admin-actions` | `{}` | audit log de acciones admin |

> **GAP — cambio de contraseña.** El backend NO tiene una action para que
> un user AUTENTICADO cambie su password (`auth.verify.set-password` usa un
> temp_token del flujo register/login, NO access JWT; `users.profile` no
> tiene `change-password`). La feature `settings` del admin incluye la UI de
> "cambiar contraseña" pero esa parte queda **bloqueada por una dependencia
> de backend** (action nueva sugerida: `users.profile.change-password` con
> `{current_password, new_password}` validada con el access JWT). Mientras
> no exista, MSW la mockea; no se puede testear E2E real.

### GET /analytics (Lambda `analytics`, plan b-analytics-api — UI de metricas)

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

Ver [docs/specs/a-admin/README.md](../../../docs/specs/a-admin/README.md) — fases + estado por fase.

## Bibliografia interna

- `.claude/rules/admin.md` — reglas duras (enforced)
- `.claude/skills/admin-stack/SKILL.md` — skill invocable
- `docs/specs/a-admin/` — plan de implementacion del admin (efimero)
- `serverless/lambda/services/auth/` — backend auth (YA implementado y
  desplegado: 6 operations / 26 actions). Reglas:
  `.claude/rules/auth-system.md`, docs: `.claude/docs/auth-system/`
- `serverless/lambda/services/users/` — backend users (YA desplegado:
  3 operations / 15 actions: profile / status / admin). Reglas:
  `.claude/rules/auth-system.md`, docs: `.claude/docs/auth-system/06-users.md`
- `docs/specs/b-analytics-api/` — backend analytics + UI de metricas
  (plan posterior, se ejecuta DESPUES del admin)
- `.claude/rules/lambda-controller.md` — formato del backend
- `.claude/rules/secrets-strategy.md` + `client-env-sync.md` — env vars
- `.claude/rules/ci-cd-pipeline.md` — workflow deploy
- `.claude/docs/cloudflare/` — Cloudflare Pages knowledge
- `.claude/docs/subdomain-standard/` — patron de subdominios
- `.claude/rules/design-system.md` — tokens CSS, dark/light, fonts
- `.claude/rules/git-workflow.md` — branches, commits, PRs
- `.claude/rules/plan-format.md` — formato de plan
- `.claude/rules/verify-before-done.md` — gate de cierre
