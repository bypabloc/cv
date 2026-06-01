# 01 — Contexto, solucion y criterios de aceptacion

[Volver al README](README.md) | [Siguiente: 02-diagramas >](02-diagramas.md)

## 1. Contexto / Problema

El portfolio (the-full-stack.com) tiene 6 sitios estaticos publicos
(Astro 6 deployados a Cloudflare Pages) y un backend serverless en AWS
(8 Lambdas Python: auth, contact_form, cv, db, send_email,
tracking_pixel, tracking_writer, users; el viejo stream_processor fue
eliminado). El Lambda `auth` (6 operations / 26 actions) ya esta
implementado y desplegado en dev/stage/prod. La data generada por los
visitantes — sessions, visits, tracking events, contacts — vive en Neon
PostgreSQL (35 tablas, schema unificado).

Hoy no hay forma de **ver** esa data: las queries hay que correrlas
manualmente con `psql` o desde la consola de Neon. No hay metricas
agregadas, no hay vista de funnel, no hay panel de contactos.

Para resolverlo:

- El Lambda `auth` (registro/login/MFA/WebAuthn) ya esta implementado y
  desplegado en `serverless/lambda/services/auth/` con 6 operations / 26
  actions: register, login, verify, session, mfa, webauthn. Reglas en
  `.claude/rules/auth-system.md`, docs en `.claude/docs/auth-system/`.
  **NO esta pending**.
- El plan a-analytics-dashboard-api
  (`docs/specs/a-analytics-dashboard-api/`) entrega el Lambda
  `analytics` con 19 endpoints GET sobre la data. **Aun pending**.
- **Este plan** entrega el **dashboard frontend SPA** que consume
  ambos APIs y los presenta como panel admin.

### Hallazgos de exploracion

- El monorepo ya tiene Cloudflare Pages deploy automatizado via
  `devtools/cloudflare_setup/` + `.github/workflows/deploy-apps.yml`.
  18 projects = 6 niches x 3 envs (dev/stage/prod). Sumar el
  dashboard = 21 projects.
- El subdomain standard
  (`.claude/docs/subdomain-standard/`) cubre el caso:
  `admin.portfolio.{env}.the-full-stack.com` es valido (component
  `admin` + product `portfolio`).
- El sitekey de Turnstile (`0x4AAAAAADPSoiQA_-LcRafo`) ya cubre los 6
  subdomains. Agregar `admin.portfolio.*` al widget en Cloudflare.
- El Lambda `auth` ya esta desplegado, pero el Lambda `analytics` aun
  NO esta implementado → el dashboard no puede ser end-to-end-testeado
  contra el backend completo hasta que `analytics` se mergee. Solucion:
  **MSW (Mock Service Worker)** con handlers que reflejen exactamente el
  contrato del backend — el de auth replicado del codigo real en
  `serverless/lambda/services/auth/core/{models,controllers}/` +
  `.claude/docs/auth-system/`, el de analytics del plan
  `docs/specs/a-analytics-dashboard-api/`. MSW se mantiene tambien para
  desarrollo sin red. Cuando el backend este vivo, el flag
  `NEXT_PUBLIC_USE_MSW` se desactiva.
- 5 research files generados consolidan 7783 lineas de docs sobre
  Next.js 16.2.6 SPA, React 19.2.6 patterns, shadcn + Atomic Design hibrido,
  JWT auth security, Cloudflare Pages deploy
  (`tmp/research/dashboard/01..05-*.md`).

## 2. Solucion Propuesta

Dashboard SPA en `dashboard/` (carpeta nueva en root del repo, entra al
pnpm workspace como `@portfolio/dashboard`). Stack:

- **Next.js 16.2.6** con `output: 'export'` (estatica, Cloudflare Pages).
- **React 19.2.6** (obligatorio en Next 16.x; Compiler stable habilitado;
  `useActionState`, `useFormStatus`, `useOptimistic`, `useDeferredValue`
  con `initialValue`, ref-as-prop sin `forwardRef`, Document Metadata
  nativo, View Transitions, `useEffectEvent`, Activity Component) +
  TypeScript 6.0.6 strict + **Biome v2** (sin ESLint).
- **Tailwind v4** con `@theme` inline + tokens compartidos con el
  Design System del monorepo.
- **shadcn/ui** (Radix primitives, copy-paste) + **Tanstack Query v5**
  + **Tanstack Table v8** + **Tanstack Virtual** + **Recharts** (via
  shadcn add chart) + **lucide-react** + **sonner**.
- **Zustand 5.0.14** para auth (tokens en `localStorage` via `persist`
  — SPA cross-origin, decision detallada abajo) + theme (next-themes).
- **react-hook-form + Zod** para forms.
- **MSW** para mocks dev + tests; **Vitest + Testing Library** unit;
  **Playwright** E2E (suite del monorepo).

Estructura **Hybrid Atomic Design**:

- `src/components/ui/` — primitivos genericos (shadcn + custom como
  MetricCard, DataTable).
- `src/features/<feature>/` — un dominio por carpeta
  (`auth`, `analytics`, `sessions`, `events`, `visits`, `geo`,
  `devices`, `funnel`, `contacts`, `settings`, `dashboard-shell`),
  cada una con `components/`, `hooks/`, `api/`, `store/`, `types.ts`,
  `index.ts`.
- `src/app/` — Next App Router con dos groups:
  - `(auth)/` — `login`, `register`, `verify`, `callback`, `set-password`.
  - `(dashboard)/` — `layout.tsx` con AuthGuard + sidebar, pages para
    cada feature.

Auth:

- Access, refresh y temp JWT en `localStorage` via Zustand `persist`.
  NO HttpOnly cookies — el dashboard es SPA cross-origin (admin vs
  api). Defensa: CSP estricta + SRI + access JWT corto (15 min) +
  family_id refresh rotation.
- **Mutex** en el fetch wrapper: 1 sola `/session/refresh` in-flight,
  evita reuse detection del backend.
- Magic link callback decodifica fragment hash (`#access=...`) en
  `/auth/callback`, guarda en Zustand, limpia con
  `history.replaceState`, redirect a `/dashboard`.
- `BroadcastChannel('portfolio_auth')` para multi-tab logout sync.
- Auto-refresh proactivo: timer client-side dispara `/session/refresh`
  30s antes del `exp` del access. Page Visibility API re-check al volver
  a la tab.

Deploy:

- 3 projects Cloudflare Pages (`portfolio-dashboard-{dev,stage,}`) via
  REST API en `devtools/cloudflare_setup/config.py` (extension para
  soportar `app_type='nextjs'` + `build_output_dir='out'`).
- Branch mapping: `dev`/`stage`/`main`.
- Custom domain attached automatico, SSL via Cloudflare ACM per-hostname.
- `_redirects` (`/* /index.html 200`) + `_headers` (CSP estricta) en
  `dashboard/public/`.
- Env vars `NEXT_PUBLIC_*` sincronizadas via `sync_secrets
  --category=client` (extension de `devtools/sync_secrets/catalog.py`).
- `.github/workflows/deploy-apps.yml` matrix agrega el dashboard como
  entrada `include` con `dist-dir: dashboard/out`.

### Decisiones clave

**Decision 1: Next.js 16 SPA vs Vite + Tanstack Router** — Next gana
por consistency con el ecosystem React, file-based routing, y un
ecosystem mas grande de tutorials/libs. Trade-off: Vite es 25% mas
chico de bundle (~65KB vs ~107KB gzipped), 10x mas rapido en startup
dev. Aceptamos el trade-off porque el dashboard NO es de uso masivo
(panel admin para 1-5 users) y la DX de file-based routing es mejor
para mantenimiento futuro.

**Decision 2: React 19.2.6** — obligatorio en Next 16.x (no
negotiable). El ecosystem 2026 lo soporta plenamente: shadcn 2.x
(ref-as-prop, sin `forwardRef`), Tanstack Query v5 (con
`useSuspenseQuery` + `useOptimistic`), react-hook-form 7 (coexiste con
`useActionState` — hybrid pattern), Zustand 5.0.14, Testing Library
v16 (primer release con soporte oficial React 19). React Compiler
stable habilitado (`reactCompiler: true` en `next.config.ts`) —
auto-memoization sin `useMemo`/`useCallback` boilerplate. Hooks nuevos
que SI aplican al SPA: `useActionState`, `useFormStatus`,
`useOptimistic`, `useDeferredValue(value, initialValue)`,
`useEffectEvent`, `<Activity>`. Hooks que NO aplican (server-only):
Server Components con async fetch, Server Actions, `'use cache'`.

**Decision 3: Hybrid Atomic Design vs Atomic clasico** — Atomic
clasico (atoms/molecules/organisms/templates) genera debates infinitos
("MetricCard es molecule u organism?") sin valor. Hybrid resuelve con
2 buckets: generico vs especifico de feature. Promote a `ui/` solo
con 2+ uses reales (premature abstraction es peor que duplicar).

**Decision 4: JWT storage — `localStorage` (NO HttpOnly cookies)** —
El dashboard es SPA estatico cross-origin: vive en
`admin.portfolio.{env}.the-full-stack.com`, consume el Lambda `auth`
en `api.portfolio.{env}.the-full-stack.com`. Para que el backend
pudiera setear cookies HttpOnly accesibles desde el dashboard, la
cookie tendria que ser `SameSite=None; Secure; Domain=.the-full-stack.com`,
lo que (a) abre vectores CSRF en los 6 niches publicos del portfolio
y (b) rompe portabilidad (mobile app, embebido en widgets).
**Decision**: los tokens viajan en el body de la respuesta. El **refreshToken**,
`refreshExpiry` y `user` se persisten en `localStorage` via Zustand
`persist` (`partialize`). El **accessToken** queda solo en memoria del store
(NO persist) — rota en cada `/session/refresh`, persistirlo solo deja stale
token tras reload. El **tempToken** tambien queda solo en memoria
(efimero, 5 min). Al reload, `useAuthTimer` detecta `refreshToken` con
`refreshExpiry > now` y dispara `/session/refresh` para rehidratar el
accessToken en memoria. Mitigaciones a XSS: (1) CSP estricta `default-src 'self'`
sin `unsafe-inline`/`unsafe-eval` en scripts, (2) Subresource Integrity
(SRI) obligatorio en third-party scripts (Turnstile), (3) access JWT
corto (15 min TTL), (4) refresh rotation + family_id detection en el
backend (RFC 9700, ya implementado en el Lambda `auth`).

**Decision 5: Mutex de refresh client-side** — Sin mutex, 5 requests
concurrent con 401 disparan 5 `/session/refresh` → backend revoca
familia entera (RFC 9700 reuse detection). Mutex garantiza 1 sola call,
los 4 restantes esperan el resultado y reintentan. Critico para
correctness.

**Decision 6: Magic link UX con fragment hash** — Backend redirect
302 a `/auth/callback#access=X&user_id=Y&email=Z`. Tokens en fragment
(`#...`) NUNCA viajan al server (no van en Referer ni logs). Frontend
decodea client-side y limpia el URL con `history.replaceState` para
que ni siquiera quede en browser history.

**Decision 7: MSW como mock layer** — El Lambda `auth` ya esta
desplegado, pero `analytics` aun no. Los MSW handlers replican
EXACTAMENTE el contrato (operations/actions/data shapes): el de auth
desde el codigo real en
`serverless/lambda/services/auth/core/{models,controllers}/` +
`.claude/docs/auth-system/`, el de analytics desde
`docs/specs/a-analytics-dashboard-api/` (aun pending). MSW se mantiene
para analytics y para desarrollo sin red; cuando el backend este vivo,
basta apagar el flag `NEXT_PUBLIC_USE_MSW=true` y todo funciona contra
el real. Esto permite mergear el dashboard ANTES que `analytics` este
listo.

**Decision 8: Carpeta `dashboard/` en root (no `apps/dashboard/`)** —
User choice explicito. El usuario pidio "una nueva carpeta en el root
llamada dashboard/*". Implementamos como pidio. devtools/cloudflare_setup
maneja la diferencia (root_dir: 'dashboard' vs 'apps/<niche>').

**Decision 9: BroadcastChannel para multi-tab** — Standard 2025-2026.
SafariOS lo soporta desde 15.4 (mar 2022). Para SSR/build safety:
guard `typeof BroadcastChannel === 'undefined'`.

**Decision 10: Subdomain `admin.portfolio.{env}.the-full-stack.com`** —
Sigue el subdomain-standard. Reservar `admin` en
`.claude/docs/subdomain-standard/02-naming-rules.md`.

## 3. Criterios de Aceptacion (AC)

Numerados, formato BDD (`Given/When/Then`). Cada AC referenciado por
tests (ver seccion 08-tests).

### Setup y estructura

- **AC-1**: Given el repo con `dashboard/` creado y configurado, When
  se corre `pnpm install` desde root, Then `@portfolio/dashboard`
  aparece como package del workspace y todas las deps se instalan sin
  errores.

- **AC-2**: Given `dashboard/` con configs (next.config.ts, tsconfig,
  biome.json override, components.json), When se corre
  `pnpm --filter @portfolio/dashboard typecheck`, Then sin errores.

- **AC-3**: Given `dashboard/`, When se corre
  `pnpm --filter @portfolio/dashboard lint`, Then Biome reporta 0
  errores y 0 warnings (con override aplicado en `components/ui/*`).

- **AC-4**: Given `dashboard/` con `next.config.ts` que define
  `output: 'export'`, When se corre
  `pnpm --filter @portfolio/dashboard build`, Then se genera
  `dashboard/out/` con `index.html`, `_next/static/`, `404.html`,
  `_redirects`, `_headers`.

### UI y theming

- **AC-5**: Given el dashboard renderizado en browser, When el OS esta
  en dark mode preference, Then el dashboard arranca en modo dark sin
  flash (FOUC) y todos los tokens (`--background`, `--foreground`,
  `--primary`) reflejan los valores de la paleta dark.

- **AC-6**: Given el dashboard en dark mode, When el user clickea el
  ThemeToggle y elige "Light", Then `data-theme="light"` se setea en
  `<html>`, los tokens cambian a la paleta light, y el setting se
  persiste en `localStorage` (clave `theme`).

- **AC-7**: Given el dashboard rendered, When el user navega entre
  pages (`/dashboard`, `/dashboard/analytics`, `/dashboard/sessions`),
  Then el sidebar persiste sin remontarse (gracias al layout
  compartido del `(dashboard)` group).

### Auth — registro

- **AC-8**: Given el LoginForm rendered, When el user ingresa email
  invalido y submit, Then Zod muestra el error `"Email invalido"` en
  el FormMessage del field email y NO se llama al API.

- **AC-9**: Given el RegisterForm con email valido y Turnstile token,
  When el user submit, Then el dashboard POST a
  `/auth?operation=register&action=start` con el body correcto, el
  store guarda `tempToken`, redirige a `/verify?flow=register`, y
  muestra toast "Te enviamos un email...".

- **AC-10**: Given el RegisterForm con email ya registrado
  (`exists@test.com`), When submit, Then el response 409 muestra
  `"Email ya registrado"` en un Alert y NO redirige.

- **AC-11**: Given la page `/verify?flow=register` con tempToken en
  store, When el user ingresa el code `"12345678"` (8 chars Crockford)
  en el InputOTP y submit, Then llama
  `/auth?operation=register&action=verify-code`, recibe `access_token`
  + `user`, los guarda en store, y redirige a `/dashboard`.

### Auth — magic link callback

- **AC-12**: Given la URL
  `/auth/callback#access=<jwt>&user_id=usr_01&email=u@t.com&refresh_exp=<epoch>`,
  When la page se carga, Then: (a) decodifica el fragment, (b)
  valida el JWT shape con `jwt-decode`, (c) guarda `accessToken` +
  `user` en Zustand, (d) llama `history.replaceState(null, '',
  '/dashboard')` para limpiar el URL, (e) redirige a `/dashboard`,
  (f) muestra toast "Sesion iniciada".

- **AC-13**: Given la URL `/auth/callback` SIN fragment, Then redirige
  a `/login` con toast "Link invalido".

### Auth — refresh rotation con mutex

- **AC-14**: Given el user con `accessToken` expirado y 5 requests
  concurrent a `/analytics`, When todos los requests reciben 401,
  Then SOLO 1 call a `/session/refresh` se dispara (mutex), los 5
  requests esperan el resultado, y todos reintentan con el nuevo
  token (assert exact: `refreshCount === 1`).

- **AC-15**: Given el user con sesion activa, When el `accessToken`
  esta a 30 segundos de expirar (`NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS`),
  Then `useAuthTimer` dispara `/session/refresh` proactivamente.

- **AC-16**: Given la tab oculta por >5 min, When vuelve a foco
  (Page Visibility API), Then se valida el JWT y dispara refresh si
  esta proximo a expirar.

### Auth — logout

- **AC-17**: Given user logueado, When clickea logout, Then: (a)
  POST a `/auth?operation=session&action=logout`, (b) reset del store
  (acceso/user/temp), (c) `queryClient.clear()`, (d) emit
  `BroadcastChannel({type: 'LOGOUT'})`, (e) redirect a `/login`, (f)
  toast "Sesion cerrada".

- **AC-18**: Given 2 tabs abiertas con sesion activa, When user
  hace logout en tab A, Then tab B detecta el `LOGOUT` por
  BroadcastChannel y resetea su Zustand sin recargar la page.

### AuthGuard

- **AC-19**: Given user sin sesion, When accede a
  `/dashboard/analytics`, Then redirect a
  `/login?next=%2Fdashboard%2Fanalytics`.

- **AC-20**: Given user con sesion + `accessToken` valido, When
  accede a `/dashboard/sessions`, Then la page renderiza sin redirect.

### Analytics

- **AC-21**: Given el dashboard en `/dashboard`, When el AnalyticsCards
  monta, Then se hace `useQuery(['analytics', 'overview', {from, to}])`
  con `staleTime: 60000`, se renderizan 7 MetricCards (sessions,
  visits, events, contacts, unique_visitors, avg_duration, bounce_rate)
  con los valores del response.

- **AC-22**: Given el TimeseriesChart en `/dashboard/analytics`, When
  el user cambia el DateRangePicker, Then el `useTimeseriesQuery`
  refetch con el nuevo rango y el chart se actualiza.

### Tables (sessions, events, contacts)

- **AC-23**: Given `/dashboard/sessions`, When la page carga, Then
  llama `useSessionsList()`, renderiza el `DataTable` con columnas
  (session_id, first_seen_at formateada, country, device_type,
  event_count), permite sort por columna, y muestra paginator (Prev/Next).

- **AC-24**: Given `/dashboard/events` con 1000+ events, When la lista
  se renderiza, Then se usa `useVirtualizer` (Tanstack Virtual), solo
  los visible rows se montan (~10-20 simultaneamente).

### Contacts

- **AC-25**: Given un contact en estado `new`, When el user clickea
  "Mark as contacted" en `/dashboard/contacts`, Then se llama un
  mutation que actualiza el estado a `contacted`, el query de la
  lista invalida y refetch.

### MFA + WebAuthn (scope base del dashboard)

- **AC-26**: Given user en `/dashboard/settings/security`, When clickea
  "Setup TOTP", Then se llama `/auth?operation=mfa&action=setup-totp`,
  el response trae `{secret_b32, otpauth_url}`, y el front renderiza el
  QR desde el `otpauth_url` (genera el SVG client-side) + un InputOTP
  para confirmar el primer code.

### Build y deploy

- **AC-27**: Given el dashboard buildeado, When se inspecciona
  `dashboard/out/`, Then existen `index.html`, `404.html`,
  `_next/static/chunks/*.js`, `_next/static/css/*.css`,
  `_redirects`, `_headers`.

- **AC-28**: Given `_redirects` con `/* /index.html 200`, When un
  visitor accede a `/dashboard/sessions/sess_01`, Then Cloudflare Pages
  sirve `index.html` y el client-side router renderiza la session
  detail page.

- **AC-29**: Given `_headers` con CSP estricta, When un visitor abre
  el dashboard, Then el header `Content-Security-Policy` se sirve
  correctamente y bloquea scripts inline NO permitidos (validado con
  curl + grep).

- **AC-30**: Given `devtools/cloudflare_setup/config.py` con el
  dashboard agregado, When se corre `python devtools/run.py
  cloudflare_setup status --env=dev`, Then el project
  `portfolio-dashboard-dev` existe + custom domain
  `admin.portfolio.dev.the-full-stack.com` attached + SSL emitido.

- **AC-31**: Given push a la branch `dev`, When `deploy-apps.yml`
  corre, Then los 7 apps se buildean en paralelo (workspace concurrency
  7), el dashboard deploya a `portfolio-dashboard-dev`, y
  `verify-deploy` confirma HTTP 200 en
  `https://admin.portfolio.dev.the-full-stack.com/`.

### Verificacion E2E

- **AC-32**: Given el stack local arriba + MSW activado, When se
  corren los specs `tests/feature/dashboard/*.spec.ts` con Playwright,
  Then los 5 flujos golden path pasan: login con code, register +
  verify, magic-link callback, AuthGuard redirect, logout
  multi-tab sync.

- **AC-33**: Given el dashboard built, When se corre `pnpm --filter
  @portfolio/dashboard test:coverage`, Then coverage >= 80% per-file en
  todos los archivos modificados/creados (excluyendo `components/ui/*`
  + barrel `index.ts` + layouts).

### MFA — TOTP (scope base)

- **AC-34**: Given user en `/dashboard/settings/security` con el TOTP
  recien seteado (AC-26), When ingresa el code de 6 digitos del
  authenticator y submit, Then se llama
  `/auth?operation=mfa&action=confirm-totp` con `{code}`, el metodo
  queda confirmado, y como es el PRIMER metodo MFA del user la familia
  de refresh se revoca en el backend (AC-27 de auth) → el cliente
  dispara un `/session/refresh` para obtener un access nuevo.

- **AC-35**: Given user con TOTP y email-code activos en
  `/dashboard/settings/security`, When clickea "Marcar como preferido"
  en TOTP, Then se llama `/auth?operation=mfa&action=set-preferred` con
  `{kind: 'totp'}` y el `MfaListResponse` refetch muestra
  `is_preferred: true` en el metodo TOTP.

- **AC-36**: Given user con un solo metodo MFA activo, When clickea
  "Desactivar" en ese metodo, Then se llama
  `/auth?operation=mfa&action=disable` con `{kind}`, el backend responde
  409 (guard `MUST_KEEP_ONE_MFA_METHOD`), y el dashboard muestra un
  Alert "Debes conservar al menos un metodo MFA" sin desactivarlo.

- **AC-37**: Given user en `/dashboard/settings/security`, When clickea
  "Generar recovery codes", Then se llama
  `/auth?operation=mfa&action=recovery-codes-generate`, el response trae
  `{codes}` (10 codes de 10 chars Crockford), y se muestran UNA sola vez
  con boton de copiar/descargar y aviso de que no se volveran a mostrar.

### WebAuthn — passkeys (scope base)

- **AC-38**: Given user en `/dashboard/settings/security`, When clickea
  "Agregar passkey", Then se llama
  `/auth?operation=webauthn&action=register-options`, el response trae
  `{challenge_id, options}`, el dashboard invoca
  `navigator.credentials.create({publicKey})` (con el RP_ID de
  `NEXT_PUBLIC_WEBAUTHN_RP_ID`), y envia el resultado a
  `/auth?operation=webauthn&action=register-verify` con
  `{challenge_id, response, nickname?}`. Al ser el PRIMER metodo MFA, la
  familia de refresh se revoca → el cliente dispara `/session/refresh`.

- **AC-39**: Given user con passkeys registradas, When abre
  `/dashboard/settings/security`, Then se llama
  `/auth?operation=webauthn&action=list-credentials`, y se renderiza la
  lista de `WebauthnCredential` (nickname + last_used_at). Al clickear
  "Eliminar" se llama `/auth?operation=webauthn&action=delete-credential`
  con `{credential_id}`; si dejara `total_mfa == 0` el backend responde
  409 y el dashboard muestra el Alert del guard `MUST_KEEP_ONE`.

### Login con MFA (scope base)

- **AC-40**: Given user con password y MFA TOTP activo en
  `/login`, When ingresa email + password y submit, Then
  `/auth?operation=login&action=verify-password` responde un `temp_token`
  step=2 + `methods` que incluye `'totp'`, y el dashboard navega al paso
  de MFA pidiendo el code de 6 digitos.

- **AC-41**: Given el paso de MFA del login con `temp_token` step=2 en
  store, When el user ingresa el code de 6 digitos del authenticator y
  submit, Then se llama `/auth?operation=login&action=verify-totp` con
  `{temp_token, code}`, recibe `access_token` + `refresh_token` + `user`,
  los guarda en store, y redirige a `/dashboard`.

- **AC-42**: Given el paso de MFA del login (`temp_token` step=2,
  factor previo fuerte: password o webauthn), When el user elige "Usar
  recovery code" e ingresa un code de 10 chars, Then se llama
  `/auth?operation=mfa&action=recovery-codes-consume` con
  `{temp_token, code}`, recibe `access_token` + `refresh_token` + `user`,
  y redirige a `/dashboard`. Si el `temp_token` viniera de magic-link o
  email-code (factor debil), el backend responde 403
  `RECOVERY_REQUIRES_STRONG_FACTOR` y el dashboard muestra el Alert.

[Volver al README](README.md) | [Siguiente: 02-diagramas >](02-diagramas.md)
