# Admin SPA (`admin/*`) — convenciones del portfolio

> Reglas para el panel admin del portfolio: Next.js 16.2.6 SPA
> estatico (`output: 'export'`) + React 19.2.6 + TypeScript 6 strict +
> Biome v2 + Tailwind v4 + shadcn/ui + Tanstack Query v5 + Zustand 5,
> deployado a Cloudflare Pages en
> `admin.portfolio.{dev|stage|prod}.the-full-stack.com`. Consume DOS
> Lambdas del backend serverless del repo: el Lambda `auth`
> (desplegado: 6 operations / 26 actions) y el Lambda `users`
> (desplegado: 3 operations / 15 actions — profile, status, admin). La
> UI de metricas consume ademas el Lambda `analytics`, pero esa parte
> vive en el plan `b-analytics-api`, NO en el admin base.

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

Tabla extendida en `.claude/skills/admin-stack/SKILL.md`.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo bajo `admin/` (carpeta nueva en root del repo)
- Configuracion de Cloudflare Pages del project `portfolio-admin*`
  (3 projects, uno por env)
- Subdominio `admin.portfolio.{dev|stage|prod}.the-full-stack.com`
- Env vars `NEXT_PUBLIC_*` del admin en
  `docker/env/client/.{env}` o en GH Environment Variables
- Extension de `devtools/cloudflare_setup/config.py` para incluir el
  app type `nextjs`
- Extension de `.github/workflows/deploy-apps.yml` para incluir el
  admin al matrix

NO aplica a las 6 apps Astro (`apps/{generic,hub,fintech,architect,leader,vibe}/`).
Esas siguen `.claude/rules/astro-landing.md`.

## Reglas duras (SIEMPRE / NUNCA)

### Estructura y stack

- **SIEMPRE** el admin vive en `admin/` (no en `apps/admin/`).
  Entra al pnpm workspace como `@portfolio/admin`.
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
- **SIEMPRE** Biome v2 (sin ESLint). El `biome.json` del admin
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
admin/src/
├── app/                                # Next App Router (export)
│   ├── layout.tsx                      # Root: ThemeProvider, QueryProvider, Toaster
│   ├── page.tsx                        # / -> redirect a /login o /metrics
│   ├── (auth)/                         # Route group (no layout compartido)
│   │   ├── login/page.tsx              # /login (alta + entrada: checklist)
│   │   ├── verify/page.tsx             # /verify (input de code)
│   │   ├── callback/page.tsx           # /callback (decodea fragment del magic link)
│   │   └── set-password/page.tsx       # /set-password
│   ├── (admin)/                        # Route group (protected, app shell compartido)
│   │   ├── layout.tsx                  # AuthGuard + app shell (header + sidebar)
│   │   ├── page.tsx                    # / del area protegida -> redirect a /metrics
│   │   ├── settings/                   # /settings/* (plan a-admin, feature settings)
│   │   │   ├── page.tsx                # perfil (display_name) + change-email + delete-account
│   │   │   └── security/page.tsx       # MFA (TOTP + email-code) + WebAuthn + recovery + password
│   │   ├── account-sessions/page.tsx   # /account-sessions (feature sessions-mgmt: mis sesiones auth)
│   │   ├── users/page.tsx              # /users (feature users-admin: gestionar otros users, solo admin)
│   │   ├── cv/page.tsx                 # /cv (placeholder gestion CV, plan futuro c-cv-management)
│   │   ├── metrics/page.tsx            # /metrics (UI de metricas — plan b-analytics-api)
│   │   ├── analytics/page.tsx          # /analytics (plan b-analytics-api)
│   │   ├── sessions/page.tsx           # /sessions (tracking de visitas — plan b-analytics-api)
│   │   ├── events/page.tsx             # /events (plan b-analytics-api)
│   │   ├── visits/page.tsx             # /visits (plan b-analytics-api)
│   │   ├── geo/page.tsx                # /geo (plan b-analytics-api)
│   │   ├── devices/page.tsx            # /devices (plan b-analytics-api)
│   │   ├── funnel/page.tsx             # /funnel (plan b-analytics-api)
│   │   └── contacts/page.tsx           # /contacts (plan b-analytics-api)
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
│   ├── admin-shell/                    # APP SHELL: header + sidebar + navegacion + layout protegido
│   │   ├── components/                 # AppShell, AppSidebar, AppHeader, NavLinks
│   │   ├── hooks/
│   │   └── lib/                        # routes del sidebar (slots a metrics/settings/users/cv)
│   ├── auth/
│   │   ├── components/                 # LoginForm, RegisterForm, VerifyCodeInput, MagicLinkPrompt
│   │   ├── hooks/                      # useLogin, useRegister, useVerifyCode, useLogout
│   │   ├── api/                        # auth-client.ts
│   │   ├── store/                      # use-auth-store.ts (Zustand)
│   │   ├── lib/                        # mutex.ts, broadcast.ts, token-expiry.ts
│   │   └── types.ts
│   ├── settings/                       # perfil + seguridad (MFA/WebAuthn/recovery/password) + change-email + delete-account
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/                        # users-client.ts (profile) + reuso de auth-client (mfa/webauthn)
│   │   └── types.ts
│   ├── sessions-mgmt/                  # mis sesiones auth: list/get + revoke (users.status)
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types.ts
│   ├── users-admin/                    # gestionar otros users (users.admin, solo admin via whitelist SSM)
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types.ts
│   ├── analytics/                      # overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention (plan b-analytics-api)
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types.ts
│   ├── sessions/                       # tracking de visitas: list, detail (plan b-analytics-api)
│   ├── events/                         # distribution, list, heatmap (plan b-analytics-api)
│   ├── visits/                         # list, landing-pages (plan b-analytics-api)
│   ├── geo/                            # by-country (plan b-analytics-api)
│   ├── devices/                        # breakdown (plan b-analytics-api)
│   ├── funnel/                         # conversion (plan b-analytics-api)
│   └── contacts/                       # list, by-status (plan b-analytics-api)
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
│   ├── api.ts                          # types de respuestas /auth, /users y /analytics
│   └── models.ts                       # User, Session, Event, Contact, AnalyticsMetric
└── env.d.ts                            # type-safe NEXT_PUBLIC_*
```

> Las features `metrics`/`analytics`/`sessions`/`events`/`visits`/`geo`/
> `devices`/`funnel`/`contacts` (UI de metricas) las implementa el plan
> `b-analytics-api`. El plan `a-admin` deja sus pages como placeholders
> dentro del app shell y los links en el sidebar; las pantallas reales se
> montan en el segundo plan. La feature `sessions` (tracking de visitas) NO
> es la feature `sessions-mgmt` (mis sesiones auth): son dominios distintos.

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

### Auth (consume el Lambda `auth` desplegado: 6 operations / 26 actions)

> **Contexto: el admin es un SPA estatico (Next.js `output:
> 'export'`) deployado en Cloudflare Pages**. NO hay backend bajo el
> mismo origen que pueda setear cookies HttpOnly del dominio del API
> (`api.portfolio.{env}.the-full-stack.com`) — el admin vive en
> `admin.portfolio.{env}.the-full-stack.com` y consume el Lambda
> `auth` via fetch CORS cross-subdomain. Una cookie HttpOnly del API
> tendria que ser `SameSite=None; Secure; Domain=.the-full-stack.com`,
> lo que abre vectores CSRF en todos los subdominios y limita la
> portabilidad si el admin se aloja en otro origin (mobile app,
> embebido en widgets, etc.). **Decision**: tokens viajan en el body de
> la respuesta del backend, el admin los persiste en
> `localStorage`. Mitigaciones: CSP `default-src 'self'`, `object-src
> 'none'`, `frame-ancestors 'none'`, `connect-src` acotado a los 3
> endpoints API + Turnstile; `script-src` permite `'unsafe-inline'`
> (OBLIGATORIO con Next `output:'export'`: el framework inyecta los inline
> `<script>` que hidratan el arbol RSC `self.__next_f.push([...])` + el
> anti-FOUC de next-themes; sin server runtime NO hay nonce y los hashes
> cambian por build -> sin `'unsafe-inline'` el browser bloquea esos
> scripts y la app se cuelga con "Connection closed"). `'unsafe-eval'`
> sigue prohibido (solo `'wasm-unsafe-eval'` para el runtime de Next).
> Subresource Integrity en todos los scripts third-party, access JWT
> corto (15 min), refresh rotation + family detection en el backend.

> **ACTUALIZACION (plan login-mfa-list-redesign):** el flujo de login del
> admin pasa de una maquina lineal a un **CHECKLIST de factores `required`**
> que el user completa en cualquier orden (la `password` es un factor mas,
> NO un gate). `login.check-email` ahora devuelve `methods_required` (la lista
> con su config de render); `login.start` (precheck, SIN email/password) abre
> el checklist (temp step=2 + `methods`). Cada verify rota el `temp_token`
> (rolling) y delega en `decide_mfa_step`; los tokens salen al completar todos
> los required. Actions nuevas: `login.send-email-code`,
> `security.password-set-required`. La feature vive en `login-checklist.tsx`
> + `login-form.tsx`; el detalle del contrato esta en
> [.claude/rules/auth-system.md](auth-system.md) (seccion "Login UX (modelo
> de lista de metodos)"). Ademas, el admin adopta **lazy auth**: NO verifica
> proactivamente el JWT (sin "Verificando sesion", sin timer ni bootstrapping;
> `use-session-rehydrate` hace UN refresh al reload, y el 401 reactivo del
> `api-client` es el unico validador).

El admin consume las actions del Lambda `auth` desde el
inicio (NO hay nada "pending"; MFA + WebAuthn son scope base). Todo
request va por `POST /auth` con body JSON `{operation, action, data}`
(salvo `verify-magic-link`, que es un GET callback). Distribucion:

- `login` (7): `check-email`, `start`, `verify-magic-link`, `verify-code`,
  `verify-password`, `verify-totp`, `send-email-code`. El alta ocurre aqui
  (`login.start` crea el pending); la operation `register` fue eliminada.
- `verify` (2): `set-password`, `resend-code`.
- `session` (2): `refresh`, `logout`.
- `mfa` (8): `setup-totp`, `confirm-totp`, `setup-email-code`,
  `set-preferred`, `disable`, `list`, `recovery-codes-generate`,
  `recovery-codes-consume`.
- `webauthn` (6): `register-options`, `register-verify`,
  `login-options`, `login-verify`, `list-credentials`,
  `delete-credential`.

`features/auth/api/auth-client.ts` expone las 26 actions tipadas (NO un
subconjunto). `features/settings/` implementa la gestion completa de
MFA + WebAuthn (setup/confirm TOTP, email-code, set-preferred, disable,
recovery codes, register/list/delete de passkeys). El detalle de
payloads y responses TS vive en `serverless/lambda/services/auth/` +
`.claude/rules/auth-system.md` + `.claude/docs/auth-system/`.

El admin ademas consume el Lambda `users` (3 operations / 15 actions)
para la gestion total de la cuenta y de otros usuarios — ver la seccion
"Gestion total (consume el Lambda `users`)" mas abajo.

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
  `history.replaceState`, redirect a `/metrics`.
- **SIEMPRE** Turnstile en `LoginForm` y `RegisterForm` (action
  `start`). Sitekey de `NEXT_PUBLIC_TURNSTILE_SITEKEY` (mismo de las 6
  apps; agregar hostname `admin.portfolio.*.the-full-stack.com` a la
  whitelist del widget en Cloudflare).
- **SIEMPRE** `(admin)/layout.tsx` envuelve children con
  `<AuthGuard>` + el app shell (feature `admin-shell`): si no hay
  accessToken o el JWT esta expirado, redirect a
  `/login?next=<current-path>`.
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
- **SIEMPRE** el login con MFA usa el flujo step-up del backend:
  `login.verify-password` (o `webauthn.login-verify`) emite un temp JWT
  `step=2` con `methods`; `login.verify-totp` lo cierra con el code de
  6 digitos. El recovery se hace con `mfa.recovery-codes-consume`.
- **SIEMPRE** las actions `mfa.*` (salvo `recovery-codes-consume`) y
  `webauthn.*` (salvo `login-options` / `login-verify`, que son parte
  del login y NO requieren sesion) viajan con `Authorization: Bearer
  <access JWT>`. El backend las valida con `require_active_user`.
- **SIEMPRE** `mfa.recovery-codes-consume` se invoca con un temp JWT
  `step=2` proveniente de un factor fuerte (`prev=password|webauthn`),
  NUNCA con el access JWT. Un temp de magic-link / email-code da `403
  RECOVERY_REQUIRES_STRONG_FACTOR`.
- **SIEMPRE** `mfa.setup-totp` devuelve `{secret_b32, otpauth_url}`: el
  admin renderiza el QR client-side desde `otpauth_url` (libreria
  QR del bundle), NUNCA pide el QR al backend. `mfa.confirm-totp` cierra
  el setup con el code de 6 digitos.
- **SIEMPRE** `mfa.recovery-codes-generate` muestra los 10 codes UNA
  sola vez (no se vuelven a leer): forzar al usuario a copiarlos /
  descargarlos antes de cerrar el modal.
- **SIEMPRE** `webauthn.register-options` / `register-verify` y
  `webauthn.login-options` / `login-verify` usan el WebAuthn API del
  browser (`navigator.credentials.create|get`) sobre las options
  devueltas por el backend (con su `challenge_id`, TTL 5 min single-use).
- **SIEMPRE** `NEXT_PUBLIC_WEBAUTHN_RP_ID` es config BASE por env (apex
  `the-full-stack.com` en prod, `portfolio.dev.the-full-stack.com` en
  dev, `portfolio.stage.the-full-stack.com` en stage). Un passkey NO
  migra entre envs (esperado). NO esta detras de un flag de "pending".
- **SIEMPRE** si se conserva `NEXT_PUBLIC_FEATURE_MFA`, es solo un toggle
  de UI opcional (mostrar / ocultar la seccion de seguridad de
  `settings`), NUNCA un gate de "backend pending": el backend MFA +
  WebAuthn esta desplegado.
- **SIEMPRE** CSP en `public/_headers`: `default-src 'self'; script-src
  'self' 'unsafe-inline' 'wasm-unsafe-eval' https://challenges.cloudflare.com;
  connect-src 'self' https://api.portfolio.* https://challenges.cloudflare.com;
  object-src 'none'; frame-ancestors 'none'; ...`. `script-src` lleva
  `'unsafe-inline'` por OBLIGACION de Next `output:'export'` (inline
  scripts del RSC + next-themes; sin server no hay nonce y los hashes
  cambian por build). NUNCA `'unsafe-eval'` (solo `'wasm-unsafe-eval'`).
  El resto de la defensa contra robo de tokens se mantiene estricto
  (connect-src acotado, object-src/frame-ancestors none, SRI third-party).
- **SIEMPRE** el flujo de registro/login completo: ver
  `.claude/docs/admin/04-auth.md` (10+ pages).
- **NUNCA** tokens en URL query params (`?access=...`). Solo fragment
  hash (`#access=...`) en el callback del magic link.
- **NUNCA** intentar setear HttpOnly cookies desde el backend para el
  admin: el origen es distinto, requeriria `SameSite=None` cross-
  site + `Domain=.the-full-stack.com` (vector CSRF en los 6 niches
  publicos) y rompe portabilidad. La defensa contra XSS es la CSP
  estricta, NO HttpOnly cookies cross-origin.
- **NUNCA** logear el JWT, refresh token, magic link token, email
  completo, ni el contenido del codigo 8 chars.
- **NUNCA** mostrar mensajes que filtren si un email existe o no fuera
  de lo que el backend ya expone (`login.check-email` revela existencia +
  `has_password` + `methods_required`; ese es el unico punto de
  enumeracion aceptado).
- **NUNCA** llamar al refresh sin pasar por el mutex (race condition
  garantizada con concurrent requests).
- **NUNCA** cargar scripts third-party sin SRI (`integrity` attribute).
  Lista permitida hoy: `challenges.cloudflare.com/turnstile/v0/api.js`
  (Cloudflare publica los hashes oficiales por version).
- **NUNCA** tratar MFA + WebAuthn como funcionalidad diferida: estan
  desplegados en el Lambda `auth` (dev/stage/prod) y son scope del
  admin (feature `settings`) desde el inicio. NO condicionarlos a
  "cuando se mergee X".
- **NUNCA** invocar `mfa.recovery-codes-consume` con el access JWT (usar
  el temp JWT `step=2` del factor fuerte) ni `webauthn.login-options` /
  `login-verify` con `Authorization` (son del login, sin sesion).
- **NUNCA** persistir el `secret_b32` del TOTP ni los recovery codes en
  `localStorage` ni en el store: se muestran en pantalla y se descartan.
- **NUNCA** logear el `secret_b32`, el code TOTP, los recovery codes ni
  la `response` cruda del WebAuthn API.

### Gestion total (consume el Lambda `users` desplegado: 3 operations / 15 actions)

El Lambda `users` esta desplegado (dev/stage/prod) y expone 3
operations / 15 actions, todas via `POST /users` con body JSON
`{operation, action, data}` y `Authorization: Bearer <access JWT>`:

- `profile` (5): `get`, `update` (`{display_name?}`), `change-email`
  (`{new_email}`), `confirm-email-change` (`{token}`), `delete-account`
  (`{confirm}`).
- `status` (3): `get`, `list-sessions`, `revoke-session`
  (`{session_id}`).
- `admin` (7): `list-users` (`{page?, page_size?}`), `get-user`
  (`{user_id}`), `disable-user` (`{user_id}`), `enable-user`
  (`{user_id}`), `delete-user` (`{user_id}`), `force-logout`
  (`{user_id}`), `list-admin-actions`.

El admin reparte estas actions en TRES features separados (NO mezclar
con `auth` ni con la feature de tracking `sessions`):

- **SIEMPRE** la feature `settings` cubre: perfil (`display_name` via
  `users.profile.update`), seguridad completa (MFA TOTP/email-code +
  set-preferred + disable, WebAuthn register/list/delete, recovery
  codes — via las actions `mfa.*` / `webauthn.*` del Lambda `auth`),
  cambio de contrasena (ver "GAP: cambio de contrasena" abajo),
  `change-email` (`users.profile.change-email` +
  `confirm-email-change`) y eliminar cuenta
  (`users.profile.delete-account`).
- **SIEMPRE** la feature `sessions-mgmt` (mis sesiones de auth, ruta
  `/account-sessions`) cubre: ver sesiones activas
  (`users.status.list-sessions` + `get`) y revocar una sesion
  (`users.status.revoke-session`). NO confundir con la feature
  `sessions` de tracking de visitas (plan `b-analytics-api`).
- **SIEMPRE** la feature `users-admin` (ruta `/users`) cubre la gestion
  de OTROS usuarios (`users.admin.*`: list-users, get-user,
  disable-user, enable-user, delete-user, force-logout,
  list-admin-actions). Es SOLO admin (whitelist SSM
  `/portfolio/admin-emails`): un user no-admin recibe `404 NOT_FOUND`
  (anti-enumeration), NO `403`. La UI oculta el item del sidebar para
  no-admins y trata el `404` como "no autorizado", NUNCA como "no
  existe".
- **SIEMPRE** el `require_active_user` del Lambda `users` devuelve `403
  ACCOUNT_DISABLED` / `403 ACCOUNT_LOCKED` (NO `401`) para un user con
  JWT valido pero disabled/locked. La UI mapea esos `403` a una
  pantalla de cuenta deshabilitada/bloqueada, NO a un redirect a login.
- **SIEMPRE** `users.status.revoke-session` de la sesion EN CURSO da
  `400 CANNOT_REVOKE_CURRENT_SESSION`: la UI usa el logout normal
  (`auth.session.logout`) para cerrar la sesion propia, NUNCA revoke.
- **SIEMPRE** `users.profile.delete-account` es destructivo: pedir
  confirmacion explicita (modal con `{confirm: true}`), avisar que
  anonimiza el email + blacklistea las familias. Un admin cuyo email
  esta en la whitelist NO puede borrarse a si mismo (`409
  CANNOT_DELETE_ADMIN_ACCOUNT`): la UI muestra ese error sin reintentar.
- **SIEMPRE** `change-email` es un flujo de 2 pasos: `change-email`
  inicia (envia confirmacion al nuevo email) y
  `confirm-email-change` lo cierra con el `{token}`. La UI muestra el
  estado "pendiente de confirmacion" hasta que llegue el token.
- **SIEMPRE** `features/settings/api/users-client.ts` (operation
  `profile`), `features/sessions-mgmt/api/` (operation `status`) y
  `features/users-admin/api/` (operation `admin`) van por
  `lib/api-client.ts` con el `Authorization: Bearer <access JWT>` y el
  mismo mutex de refresh que `auth`.
- **NUNCA** mezclar las features `sessions` (tracking de visitas, plan
  `b-analytics-api`) y `sessions-mgmt` (mis sesiones auth, plan
  `a-admin`): son dominios distintos con backends distintos.
- **NUNCA** mostrar el item `/users` (users-admin) ni intentar las
  actions `users.admin.*` si el user no es admin: el backend responde
  `404`, y filtrar la lista de admin a un no-admin seria enumeracion.
- **NUNCA** llamar `users.*` sin `Authorization: Bearer <access JWT>`
  (todas requieren sesion activa).

#### Cambio de contrasena (action `users.profile.change-password`)

El Lambda `users` SI tiene la action `profile.change-password`
(implementada y desplegada): un user AUTENTICADO cambia su password con
su access JWT enviando `{current_password, new_password}`.

- **SIEMPRE** la feature `settings` cablea el cambio de password a
  `users.profile.change-password` (REAL, sin flag de bloqueo): UI con su
  Zod schema (`{current_password, new_password, confirm}` con refine
  longitud >= 12 + match) + form react-hook-form. Exito -> toast; la
  sesion actual sigue viva (el backend la preserva).
- **SIEMPRE** el backend verifica `current_password` (argon2id) y, si es
  incorrecta, responde **401 `INVALID_PASSWORD`** -> la UI muestra el
  error inline/toast sin romper el form.
- **SIEMPRE** un cambio de password exitoso REVOCA las demas sesiones del
  user (blacklist de familias de refresh) y preserva SOLO la actual
  (best practice de seguridad post-cambio de credencial).
- **NUNCA** cablear la UI de cambio de password a
  `auth.verify.set-password` (esa usa el `temp_token` del flujo
  register/login, NO el access JWT del user logueado). El cambio
  autenticado va por `users.profile.change-password`.

#### App shell (feature `admin-shell`)

- **SIEMPRE** el app shell (header + sidebar + navegacion + layout
  protegido) vive en la feature `admin-shell` y se monta en
  `(admin)/layout.tsx` envolviendo `<AuthGuard>`. Usar el termino "app
  shell" o "shell" (estandar de industria), NUNCA "dashboard" para
  referirse al marco.
- **SIEMPRE** el sidebar de `admin-shell` declara los slots/links a las
  secciones: metricas (`/metrics`), settings (`/settings`),
  mis sesiones (`/account-sessions`), gestion de usuarios (`/users`,
  solo admin) y gestion CV (`/cv`, placeholder). Las PANTALLAS de
  metricas NO se implementan en el plan `a-admin`: el shell deja los
  links y pages placeholder, y el plan `b-analytics-api` monta la UI
  real dentro de este mismo shell.
- **SIEMPRE** el placeholder de gestion CV (`/cv`) es solo un link en el
  sidebar + una page con una nota "plan futuro c-cv-management". SIN
  backend ni UI de edicion.
- **NUNCA** nombrar la vista de metricas `/dashboard` ni el feature del
  marco `dashboard-shell`: la ruta es `/metrics` (o las rutas por
  feature) y el feature es `admin-shell`.

### UI (shadcn + Tailwind v4 + theming)

- **SIEMPRE** componentes shadcn via CLI: `pnpm dlx shadcn@latest add
  <component>`. Modifican/copian en `src/components/ui/`.
- **SIEMPRE** Tailwind v4 con `@theme` inline en `src/styles/globals.css`.
  NO `tailwind.config.ts` (o solo minimo para overrides).
- **SIEMPRE** los tokens CSS del admin reflejan los tokens del DS
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
  Specs nuevas en `tests/feature/admin/*.spec.ts`.
- **NUNCA** mockear `useAuthStore` directamente. Usar
  `useAuthStore.setState(...)` en `beforeEach` para preparar estado.
- **NUNCA** mockear Tanstack Query directamente. Crear un `QueryClient`
  de test + envolver el componente.
- **NUNCA** llamar al backend real en tests unit. Solo MSW.

### Env vars (categoria client)

- **SIEMPRE** las env vars del admin llevan prefijo `NEXT_PUBLIC_`
  (requisito de Next 16 para exponer al bundle). Equivalencia con las
  apps Astro (`PUBLIC_*`):

  | Astro (apps) | Next.js (admin) | Fuente |
  |--------------|---------------------|--------|
  | `PUBLIC_API_ENDPOINT` | `NEXT_PUBLIC_API_ENDPOINT` | misma URL del Lambda |
  | `PUBLIC_TURNSTILE_SITEKEY` | `NEXT_PUBLIC_TURNSTILE_SITEKEY` | mismo sitekey |
  | (no aplica) | `NEXT_PUBLIC_ADMIN_URL` | `https://admin.portfolio.{env}.the-full-stack.com` |
  | (no aplica) | `NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS` | `30000` (refresh 30s antes del exp) |

- **SIEMPRE** validar `NEXT_PUBLIC_*` en cold start con Zod en
  `src/lib/env.ts`. Si falta una, fail el build.
- **SIEMPRE** las vars se publican via `python devtools/run.py
  sync_secrets --env=<X> --category=client`. NUNCA `gh variable set` a
  mano (ver `.claude/rules/client-env-sync.md`).
- **SIEMPRE** el catalogo en `devtools/sync_secrets/catalog.py` lista
  las nuevas keys del admin.
- **NUNCA** marcar `NEXT_PUBLIC_*` como GH Secret. Son Variables
  (publicas por contrato).
- **NUNCA** leer `docker/env/client/.{env}` con Read tool. Extraer keys
  puntuales con `grep -m1 ^KEY=` (ver `.claude/rules/env-files.md`).

### Deploy (Cloudflare Pages)

- **SIEMPRE** 3 projects Cloudflare Pages: `portfolio-admin-dev`,
  `portfolio-admin-stage`, `portfolio-admin` (prod sin sufijo).
- **SIEMPRE** branch mapping: `dev` -> dev project, `stage` -> stage,
  `main` -> prod.
- **SIEMPRE** custom domain attached al provisionar:
  - `admin.portfolio.dev.the-full-stack.com` (dev)
  - `admin.portfolio.stage.the-full-stack.com` (stage)
  - `admin.portfolio.the-full-stack.com` (prod)
- **SIEMPRE** SSL cert se emite automatico por Cloudflare ACM al
  attach del custom domain (no manual).
- **SIEMPRE** build command: `pnpm install --frozen-lockfile && pnpm
  --filter @portfolio/admin... build` (`...` incluye deps del
  workspace).
- **SIEMPRE** output dir: `admin/out` (Next 16 export genera `out/`
  por default).
- **SIEMPRE** `admin/public/_redirects` con `/* /index.html 200`
  para client-side routing (rutas dinamicas).
- **SIEMPRE** `admin/public/_headers` con CSP estricta + cache
  headers + HSTS. Ver capitulo deploy del knowledge tree.
- **SIEMPRE** `devtools/cloudflare_setup/config.py` declara el
  admin como nuevo `AppConfig` con `app_type='nextjs'` y
  `build_output_dir='out'`. El comando `cloudflare_setup all
  --env=<X>` deploya los 7 apps (6 Astro + 1 Next).
- **SIEMPRE** `.github/workflows/deploy-apps.yml` extiende la matrix
  con `include` para agregar el admin (dist-dir distinto).
- **SIEMPRE** preview_branch_includes en `[<branch>]` para evitar que
  cada project construya todas las ramas (ver memory
  `cloudflare-pages-preview-branch-fix`).
- **NUNCA** wrangler para crear el project (no soporta git-connected
  con env vars correctos). Solo REST API via devtools.
- **NUNCA** modificar la config del project en la consola Cloudflare:
  el siguiente `cloudflare_setup projects` la revierte.

### CI/CD

- **SIEMPRE** el admin pasa por `ci.yml` (lint + build de las apps
  incluyendo el admin) en cada PR.
- **SIEMPRE** `deploy-apps.yml` con `environment: <stage>` para leer
  GH Variables correctas (NEXT_PUBLIC_*).
- **SIEMPRE** branch-flow-guard sigue aplicando: PR `dev -> stage` y
  `stage -> main` con merge commit (NO rebase — ver
  `.claude/rules/git-workflow.md`).
- **SIEMPRE** el admin se mergea junto a los backends que consume
  (auth + users; analytics para la UI de metricas del plan
  `b-analytics-api`) cuando esas APIs esten en el mismo env. Hasta
  entonces, el admin usa MSW.

## Comando canonico (development)

```bash
# Setup inicial (una vez)
cd admin
pnpm dlx shadcn@latest init                       # crea components.json
pnpm dlx shadcn@latest add button input form ...  # primeros componentes
cd ..

# Trabajo diario
pnpm install                                      # desde root, workspace
pnpm --filter @portfolio/admin dev                # localhost:3000
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build              # genera admin/out/

# Pre-push
pnpm --filter @portfolio/admin lint:fix
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test:coverage
pnpm --filter @portfolio/admin build

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
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck

# 2. Unit tests
pnpm --filter @portfolio/admin test:coverage  # >= 80%

# 3. Build estatico
pnpm --filter @portfolio/admin build
ls -lah admin/out/index.html admin/out/_next  # debe existir

# 4. Preview manual (al menos los flujos golden path)
pnpm --filter @portfolio/admin preview &
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
| HttpOnly cookie cross-origin del API al admin (`SameSite=None; Domain=.the-full-stack.com`) | Vector CSRF en los 6 niches publicos + rompe portabilidad | Tokens en `localStorage` + CSP estricta (decision documentada arriba) |
| `script-src 'self'` SIN `'unsafe-inline'` en Next `output:'export'` | Bloquea los inline scripts del RSC -> "Connection closed" -> app colgada en "Verificando sesion" | `script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'` (inevitable sin server/nonce) |
| `'unsafe-eval'` en `script-src` | XSS arbitrario (eval de strings) | Solo `'wasm-unsafe-eval'` (runtime de Next), NUNCA `'unsafe-eval'` |
| Promote a `components/ui/` con 1 uso | Premature abstraction | Vive en `features/<X>/components/` |
| Server Component async fetch | Build fail en export | `'use client'` + Tanstack Query |
| Importar `@radix-ui/react-*` directo | Pierde theming shadcn | Pasar por `components/ui/<comp>` |
| Framer Motion | 30KB+, no necesario | Tailwind animate + `@starting-style` |
| Hex inline (`color: '#FF0000'`) | Rompe dark mode | `text-destructive` o `var(--color-destructive)` |
| Google Fonts CDN | GDPR, CSP estricta | `@fontsource/*` |
| Nombrar la vista de metricas `/dashboard` o el route group `(dashboard)` | El producto se llama `admin`; la vista de metricas no es "dashboard" | Ruta `/metrics` (o por feature) + route group `(admin)` |
| Feature del marco llamado `dashboard-shell` | El app shell es la feature `admin-shell` | `admin-shell` (header + sidebar + nav) |
| UI de cambio de password cableada a `auth.verify.set-password` | Usa `temp_token`, no el access JWT del user logueado | Cablear a `users.profile.change-password` (action REAL, desplegada) |
| Mostrar `/users` (users-admin) a un user no-admin | El backend responde `404` y filtrar la lista seria enumeracion | Ocultar el item del sidebar; tratar `404` como no autorizado |
| Mezclar la feature `sessions` (tracking) con `sessions-mgmt` (mis sesiones auth) | Dominios distintos, backends distintos (`analytics` vs `users`) | Features separados; `sessions` es del plan `b-analytics-api` |
| `find` / `grep -E` / `grep -rn` en Bash | Aliases rotos en WSL2 | Glob/Grep/Read tools |

## Referencias cruzadas

- Skill: `/admin-stack` (resumen ejecutivo + decisiones)
- Knowledge tree: `.claude/docs/admin/` (7 capitulos)
- Plan: `docs/specs/a-admin/` (frontend, PRIMERO; efimero, se elimina al
  mergear)
- Backend auth: `serverless/lambda/services/auth/` (YA implementado y
  desplegado: 6 operations / 26 actions invocables por el cliente —
  register, login, verify, session, mfa, webauthn). Reglas:
  `.claude/rules/auth-system.md`, docs: `.claude/docs/auth-system/`
- Backend users: `serverless/lambda/services/users/` (YA implementado y
  desplegado: 3 operations / 15 actions — profile, status, admin).
  Reglas: `.claude/rules/auth-system.md`
- Backend analytics + UI de metricas: `docs/specs/b-analytics-api/`
  (full-stack, SEGUNDO; va DESPUES del plan `a-admin`). El Lambda
  `analytics` valida access JWT (no es publico)
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
