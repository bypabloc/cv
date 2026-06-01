# 01 — Contexto, solucion y criterios de aceptacion

[Volver al README](README.md) | [Siguiente: 02-diagramas >](02-diagramas.md)

## 1. Contexto / Problema

El portfolio (the-full-stack.com) tiene 6 sitios estaticos publicos
(Astro 6 deployados a Cloudflare Pages) y un backend serverless en AWS
(8 Lambdas Python: auth, contact_form, cv, db, send_email,
tracking_pixel, tracking_writer, users; el viejo stream_processor fue
eliminado). Los Lambdas `auth` (6 operations / 26 actions) y `users`
(3 operations / 15 actions) ya estan implementados y desplegados en
dev/stage/prod. La data generada por los visitantes — sessions, visits,
tracking events, contacts — vive en Neon PostgreSQL (35 tablas, schema
unificado).

Hoy no hay un **panel** para que el owner se autentique, gestione su
cuenta (perfil, seguridad MFA/WebAuthn, contraseña, email, sesiones) ni
administre otros usuarios. Tampoco hay forma de **ver** la data de
visitantes salvo correr queries a mano con `psql` o la consola de Neon.

Para resolverlo:

- El Lambda `auth` (registro/login/MFA/WebAuthn) ya esta implementado y
  desplegado en `serverless/lambda/services/auth/` con 6 operations / 26
  actions: register, login, verify, session, mfa, webauthn. Reglas en
  `.claude/rules/auth-system.md`, docs en `.claude/docs/auth-system/`.
  **NO esta pending**.
- El Lambda `users` (gestion de cuenta) ya esta implementado y
  desplegado en `serverless/lambda/services/users/` con 3 operations /
  15 actions: profile (get, update, change-email, confirm-email-change,
  delete-account), status (get, list-sessions, revoke-session), admin
  (list-users, get-user, disable-user, enable-user, delete-user,
  force-logout, list-admin-actions). **NO esta pending**.
- El plan b-analytics-api (`docs/specs/b-analytics-api/`) entrega el
  Lambda `analytics` (con auth de access JWT) y la **UI de metricas**
  montada dentro del app shell de este admin. **Aun pending**.
- **Este plan** entrega el **admin frontend SPA**: el app shell
  (header + sidebar + nav + layout protegido), auth completo y la
  gestion total de cuenta/usuarios. SIN UI de metricas (esa va al plan
  b-analytics-api).

### Hallazgos de exploracion

- El monorepo ya tiene Cloudflare Pages deploy automatizado via
  `devtools/cloudflare_setup/` + `.github/workflows/deploy-apps.yml`.
  18 projects = 6 niches x 3 envs (dev/stage/prod). Sumar el
  admin = 21 projects.
- El subdomain standard
  (`.claude/docs/subdomain-standard/`) cubre el caso:
  `admin.portfolio.{env}.the-full-stack.com` es valido (component
  `admin` + product `portfolio`).
- El sitekey de Turnstile (`0x4AAAAAADPSoiQA_-LcRafo`) ya cubre los 6
  subdomains. Agregar `admin.portfolio.*` al widget en Cloudflare.
- Los Lambdas `auth` y `users` ya estan desplegados → este plan se
  testea E2E real contra ese backend. El Lambda `analytics` aun NO
  esta implementado (es del plan b-analytics-api), pero este plan NO
  entrega UI de metricas, asi que no lo necesita. Para desarrollo sin
  red y para los flujos aun no cubiertos por backend, se usa
  **MSW (Mock Service Worker)** con handlers que replican exactamente
  el contrato del codigo real en
  `serverless/lambda/services/{auth,users}/core/{models,controllers}/`
  + `.claude/docs/auth-system/`. Cuando se quiere correr contra el
  backend real, el flag `NEXT_PUBLIC_USE_MSW` se desactiva.
- 5 research files generados consolidan 7783 lineas de docs sobre
  Next.js 16.2.6 SPA, React 19.2.6 patterns, shadcn + Atomic Design hibrido,
  JWT auth security, Cloudflare Pages deploy
  (`tmp/research/dashboard/01..05-*.md`).

## 2. Solucion Propuesta

Admin SPA en `admin/` (carpeta nueva en root del repo, entra al
pnpm workspace como `@portfolio/admin`). Entrega el app shell, el auth
completo y la gestion total de cuenta/usuarios; la UI de metricas se
monta despues en este mismo shell desde el plan b-analytics-api. Stack:

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
  DataTable).
- `src/features/<feature>/` — un dominio por carpeta. Las features de
  ESTE plan son `admin-shell`, `auth`, `settings`, `sessions-mgmt`,
  `users-admin` (mas un placeholder `cv` sin backend), cada una con
  `components/`, `hooks/`, `api/`, `store/`, `types.ts`, `index.ts`.
  Las features de metricas (`analytics`, `sessions` de tracking,
  `events`, `visits`, `geo`, `devices`, `funnel`, `contacts`) NO se
  implementan aca: se agregan en el plan b-analytics-api dentro de este
  mismo shell.
- `src/app/` — Next App Router con dos groups:
  - `(auth)/` — `login`, `register`, `verify`, `callback`, `set-password`.
  - `(admin)/` — `layout.tsx` con AuthGuard + sidebar, pages para cada
    feature de este plan (settings, sessions-mgmt, users-admin,
    placeholder cv). El sidebar reserva slots/links para las secciones
    de metricas, pero esas pantallas las entrega b-analytics-api.

Auth:

- Access, refresh y temp JWT en `localStorage` via Zustand `persist`.
  NO HttpOnly cookies — el admin es SPA cross-origin (admin vs
  api). Defensa: CSP estricta + SRI + access JWT corto (15 min) +
  family_id refresh rotation.
- **Mutex** en el fetch wrapper: 1 sola `/session/refresh` in-flight,
  evita reuse detection del backend.
- Magic link callback decodifica fragment hash (`#access=...`) en
  `/auth/callback`, guarda en Zustand, limpia con
  `history.replaceState`, redirect a `/admin`.
- `BroadcastChannel('portfolio_auth')` para multi-tab logout sync.
- Auto-refresh proactivo: timer client-side dispara `/session/refresh`
  30s antes del `exp` del access. Page Visibility API re-check al volver
  a la tab.

Deploy:

- 3 projects Cloudflare Pages (`portfolio-admin-{dev,stage,}`) via
  REST API en `devtools/cloudflare_setup/config.py` (extension para
  soportar `app_type='nextjs'` + `build_output_dir='out'`).
- Branch mapping: `dev`/`stage`/`main`.
- Custom domain attached automatico, SSL via Cloudflare ACM per-hostname.
- `_redirects` (`/* /index.html 200`) + `_headers` (CSP estricta) en
  `admin/public/`.
- Env vars `NEXT_PUBLIC_*` sincronizadas via `sync_secrets
  --category=client` (extension de `devtools/sync_secrets/catalog.py`).
- `.github/workflows/deploy-apps.yml` matrix agrega el admin como
  entrada `include` con `dist-dir: admin/out`.

### Decisiones clave

**Decision 1: Next.js 16 SPA vs Vite + Tanstack Router** — Next gana
por consistency con el ecosystem React, file-based routing, y un
ecosystem mas grande de tutorials/libs. Trade-off: Vite es 25% mas
chico de bundle (~65KB vs ~107KB gzipped), 10x mas rapido en startup
dev. Aceptamos el trade-off porque el admin NO es de uso masivo
(panel para 1-5 users) y la DX de file-based routing es mejor
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
El admin es SPA estatico cross-origin: vive en
`admin.portfolio.{env}.the-full-stack.com`, consume el Lambda `auth`
en `api.portfolio.{env}.the-full-stack.com`. Para que el backend
pudiera setear cookies HttpOnly accesibles desde el admin, la
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

**Decision 7: MSW como mock layer** — Los Lambdas `auth` y `users` ya
estan desplegados, asi que este plan se testea E2E real contra ellos.
Los MSW handlers replican EXACTAMENTE el contrato del codigo real
(operations/actions/data shapes) desde
`serverless/lambda/services/{auth,users}/core/{models,controllers}/` y
`.claude/docs/auth-system/`, y sirven para desarrollo sin red y para
la UI bloqueada por la action `users.profile.change-password` que aun
no existe (ver seccion 5 del insumo + AC del cambio de contraseña). El
Lambda `analytics` sigue pending, pero este plan NO entrega UI de
metricas, asi que su contrato MSW se define en b-analytics-api, no
aca. Con `NEXT_PUBLIC_USE_MSW=true` se corre contra los mocks; al
apagar el flag, contra el backend real.

**Decision 8: Carpeta `admin/` en root (no `apps/admin/`)** —
User choice explicito. El usuario pidio "una nueva carpeta en el root
llamada admin/*". Implementamos como pidio. devtools/cloudflare_setup
maneja la diferencia (root_dir: 'admin' vs `apps/<niche>`).

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

- **AC-1**: Given el repo con `admin/` creado y configurado, When
  se corre `pnpm install` desde root, Then `@portfolio/admin`
  aparece como package del workspace y todas las deps se instalan sin
  errores.

- **AC-2**: Given `admin/` con configs (next.config.ts, tsconfig,
  biome.json override, components.json), When se corre
  `pnpm --filter @portfolio/admin typecheck`, Then sin errores.

- **AC-3**: Given `admin/`, When se corre
  `pnpm --filter @portfolio/admin lint`, Then Biome reporta 0
  errores y 0 warnings (con override aplicado en `components/ui/*`).

- **AC-4**: Given `admin/` con `next.config.ts` que define
  `output: 'export'`, When se corre
  `pnpm --filter @portfolio/admin build`, Then se genera
  `admin/out/` con `index.html`, `_next/static/`, `404.html`,
  `_redirects`, `_headers`.

### UI y theming

- **AC-5**: Given el admin renderizado en browser, When el OS esta
  en dark mode preference, Then el admin arranca en modo dark sin
  flash (FOUC) y todos los tokens (`--background`, `--foreground`,
  `--primary`) reflejan los valores de la paleta dark.

- **AC-6**: Given el admin en dark mode, When el user clickea el
  ThemeToggle y elige "Light", Then `data-theme="light"` se setea en
  `<html>`, los tokens cambian a la paleta light, y el setting se
  persiste en `localStorage` (clave `theme`).

- **AC-7**: Given el admin rendered, When el user navega entre
  pages (`/admin`, `/admin/settings`, `/admin/sessions`),
  Then el sidebar (app shell `admin-shell`) persiste sin remontarse
  (gracias al layout compartido del `(admin)` group).

### Auth — registro

- **AC-8**: Given el LoginForm rendered, When el user ingresa email
  invalido y submit, Then Zod muestra el error `"Email invalido"` en
  el FormMessage del field email y NO se llama al API.

- **AC-9**: Given el RegisterForm con email valido y Turnstile token,
  When el user submit, Then el admin POST a
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
  + `user`, los guarda en store, y redirige a `/admin`.

### Auth — magic link callback

- **AC-12**: Given la URL
  `/auth/callback#access=<jwt>&user_id=usr_01&email=u@t.com&refresh_exp=<epoch>`,
  When la page se carga, Then: (a) decodifica el fragment, (b)
  valida el JWT shape con `jwt-decode`, (c) guarda `accessToken` +
  `user` en Zustand, (d) llama `history.replaceState(null, '',
  '/admin')` para limpiar el URL, (e) redirige a `/admin`,
  (f) muestra toast "Sesion iniciada".

- **AC-13**: Given la URL `/auth/callback` SIN fragment, Then redirige
  a `/login` con toast "Link invalido".

### Auth — refresh rotation con mutex

- **AC-14**: Given el user con `accessToken` expirado y 5 requests
  concurrent a `/users` (operation `status` o `profile`), When todos
  los requests reciben 401, Then SOLO 1 call a `/session/refresh` se
  dispara (mutex), los 5 requests esperan el resultado, y todos
  reintentan con el nuevo token (assert exact: `refreshCount === 1`).

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
  `/admin/settings`, Then redirect a
  `/login?next=%2Fadmin%2Fsettings`.

- **AC-20**: Given user con sesion + `accessToken` valido, When
  accede a `/admin/sessions`, Then la page renderiza sin redirect.

> Las AC de la UI de metricas (overview/timeseries de analytics, tablas
> de sessions de tracking, events, contacts) NO viven en este plan: se
> entregan en `docs/specs/b-analytics-api/` junto al Lambda `analytics`.

### MFA — TOTP (scope base)

- **AC-21**: Given user en `/admin/settings/security`, When clickea
  "Setup TOTP", Then se llama `/auth?operation=mfa&action=setup-totp`,
  el response trae `{secret_b32, otpauth_url}`, y el front renderiza el
  QR desde el `otpauth_url` (genera el SVG client-side) + un InputOTP
  para confirmar el primer code.

- **AC-22**: Given user en `/admin/settings/security` con el TOTP
  recien seteado (AC-21), When ingresa el code de 6 digitos del
  authenticator y submit, Then se llama
  `/auth?operation=mfa&action=confirm-totp` con `{code}`, el metodo
  queda confirmado, y como es el PRIMER metodo MFA del user la familia
  de refresh se revoca en el backend (AC-27 de auth) → el cliente
  dispara un `/session/refresh` para obtener un access nuevo.

- **AC-23**: Given user con TOTP y email-code activos en
  `/admin/settings/security`, When clickea "Marcar como preferido"
  en TOTP, Then se llama `/auth?operation=mfa&action=set-preferred` con
  `{kind: 'totp'}` y el `MfaListResponse` refetch muestra
  `is_preferred: true` en el metodo TOTP.

- **AC-24**: Given user con un solo metodo MFA activo, When clickea
  "Desactivar" en ese metodo, Then se llama
  `/auth?operation=mfa&action=disable` con `{kind}`, el backend responde
  409 (guard `MUST_KEEP_ONE_MFA_METHOD`), y el admin muestra un
  Alert "Debes conservar al menos un metodo MFA" sin desactivarlo.

- **AC-25**: Given user en `/admin/settings/security`, When clickea
  "Generar recovery codes", Then se llama
  `/auth?operation=mfa&action=recovery-codes-generate`, el response trae
  `{codes}` (10 codes de 10 chars Crockford), y se muestran UNA sola vez
  con boton de copiar/descargar y aviso de que no se volveran a mostrar.

### WebAuthn — passkeys (scope base)

- **AC-26**: Given user en `/admin/settings/security`, When clickea
  "Agregar passkey", Then se llama
  `/auth?operation=webauthn&action=register-options`, el response trae
  `{challenge_id, options}`, el admin invoca
  `navigator.credentials.create({publicKey})` (con el RP_ID de
  `NEXT_PUBLIC_WEBAUTHN_RP_ID`), y envia el resultado a
  `/auth?operation=webauthn&action=register-verify` con
  `{challenge_id, response, nickname?}`. Al ser el PRIMER metodo MFA, la
  familia de refresh se revoca → el cliente dispara `/session/refresh`.

- **AC-27**: Given user con passkeys registradas, When abre
  `/admin/settings/security`, Then se llama
  `/auth?operation=webauthn&action=list-credentials`, y se renderiza la
  lista de `WebauthnCredential` (nickname + last_used_at). Al clickear
  "Eliminar" se llama `/auth?operation=webauthn&action=delete-credential`
  con `{credential_id}`; si dejara `total_mfa == 0` el backend responde
  409 y el admin muestra el Alert del guard `MUST_KEEP_ONE`.

### Login con MFA (scope base)

- **AC-28**: Given user con password y MFA TOTP activo en
  `/login`, When ingresa email + password y submit, Then
  `/auth?operation=login&action=verify-password` responde un `temp_token`
  step=2 + `methods` que incluye `'totp'`, y el admin navega al paso
  de MFA pidiendo el code de 6 digitos.

- **AC-29**: Given el paso de MFA del login con `temp_token` step=2 en
  store, When el user ingresa el code de 6 digitos del authenticator y
  submit, Then se llama `/auth?operation=login&action=verify-totp` con
  `{temp_token, code}`, recibe `access_token` + `refresh_token` + `user`,
  los guarda en store, y redirige a `/admin`.

- **AC-30**: Given el paso de MFA del login (`temp_token` step=2,
  factor previo fuerte: password o webauthn), When el user elige "Usar
  recovery code" e ingresa un code de 10 chars, Then se llama
  `/auth?operation=mfa&action=recovery-codes-consume` con
  `{temp_token, code}`, recibe `access_token` + `refresh_token` + `user`,
  y redirige a `/admin`. Si el `temp_token` viniera de magic-link o
  email-code (factor debil), el backend responde 403
  `RECOVERY_REQUIRES_STRONG_FACTOR` y el admin muestra el Alert.

### Settings — perfil

- **AC-31**: Given user en `/admin/settings`, When la page monta,
  Then se llama `/users?operation=profile&action=get` (access JWT en
  `_meta.authorization`) y el formulario de perfil se rellena con el
  `display_name` actual del response.

- **AC-32**: Given user en `/admin/settings` con un `display_name`
  nuevo valido, When submit, Then se llama
  `/users?operation=profile&action=update` con `{display_name}`, el
  query de perfil invalida y refetch, y se muestra toast "Perfil
  actualizado".

### Settings — cambio de contraseña (DEPENDE de action backend nueva)

> **Dependencia de backend**: el cambio de contraseña requiere una
> action que AUN NO EXISTE. El backend no tiene forma de que un user
> AUTENTICADO cambie su password: `auth.verify.set-password` usa el
> temp_token del flujo register/login (NO el access JWT), y
> `users.profile` no expone `change-password` (ver seccion 5 del
> insumo). El plan a-admin implementa la UI + el MSW handler, pero la
> action real `users.profile.change-password`
> ({current_password, new_password} validada con el access JWT) queda
> como pre-requisito de backend de un plan futuro. La parte E2E real
> de este AC esta BLOQUEADA hasta que esa action exista; mientras
> tanto se valida contra MSW.

- **AC-33**: Given user en `/admin/settings/security`, When ingresa
  `current_password` + `new_password` (validado con Zod: minimo de
  longitud, confirmacion coincide) y submit, Then se llama
  `/users?operation=profile&action=change-password` con
  `{current_password, new_password}` (action backend NUEVA, aun no
  desplegada → mockeada con MSW), y se muestra toast "Contraseña
  actualizada". DEPENDE de la action backend
  `users.profile.change-password` (ver nota arriba).

### Settings — cambio de email

- **AC-34**: Given user en `/admin/settings` con un email nuevo
  valido, When submit "Cambiar email", Then se llama
  `/users?operation=profile&action=change-email` con `{new_email}`,
  el backend envia el email de confirmacion, y se muestra toast "Te
  enviamos un enlace de confirmacion".

- **AC-35**: Given user que abre el enlace de confirmacion de cambio
  de email con un `token` en el fragment/query, When la page de
  confirmacion monta, Then se llama
  `/users?operation=profile&action=confirm-email-change` con `{token}`,
  el email queda actualizado, y se muestra toast "Email confirmado".

### Settings — eliminar cuenta

- **AC-36**: Given user en `/admin/settings` que clickea "Eliminar
  cuenta" y confirma en el dialog, When submit, Then se llama
  `/users?operation=profile&action=delete-account` con `{confirm:
  true}`, el backend hace soft-delete + anonimiza + blacklist de
  familias, el cliente resetea el store + `queryClient.clear()` y
  redirige a `/login` con toast "Cuenta eliminada". Si el user es
  admin (su email esta en la whitelist), el backend responde 409
  `CANNOT_DELETE_ADMIN_ACCOUNT` y el admin muestra el Alert sin
  redirigir.

### Sessions-mgmt — mis sesiones

> No confundir con la feature `sessions` de METRICAS (tracking de
> visitantes) del plan b-analytics-api. Aca son las sesiones de MI
> cuenta auth.

- **AC-37**: Given user en `/admin/sessions`, When la page monta,
  Then se llama `/users?operation=status&action=list-sessions`
  (access JWT en `_meta.authorization`), y se renderiza la lista de
  sesiones activas (device, last_seen_at, marca de "sesion actual").

- **AC-38**: Given user en `/admin/sessions` con 2+ sesiones, When
  clickea "Revocar" en una sesion que NO es la actual, Then se llama
  `/users?operation=status&action=revoke-session` con `{session_id}`,
  el query de la lista invalida y refetch, y la sesion desaparece. Si
  intentara revocar la sesion actual, el backend responde 400
  `CANNOT_REVOKE_CURRENT_SESSION` y el admin muestra el Alert (usar
  logout en su lugar).

### Users-admin — gestionar otros usuarios (solo admin)

> Solo accesible para users en la whitelist SSM `/portfolio/admin-emails`.
> Para un user NO admin, las actions `admin.*` responden 404 NOT_FOUND
> (anti-enumeration), por lo que el sidebar oculta la seccion.

- **AC-39**: Given un user admin en `/admin/users`, When la page
  monta, Then se llama `/users?operation=admin&action=list-users` con
  `{page?, page_size?}`, y se renderiza el `DataTable` de usuarios
  (email, status, fecha de registro) con paginator. Al clickear una
  fila se llama `/users?operation=admin&action=get-user` con
  `{user_id}` y se muestra el detalle.

- **AC-40**: Given un user admin viendo el detalle de otro usuario
  activo, When clickea "Deshabilitar", Then se llama
  `/users?operation=admin&action=disable-user` con `{user_id}`, el
  query invalida y el status pasa a `disabled`. "Habilitar" llama
  `enable-user` (status → `active`) y "Eliminar" llama `delete-user`
  (soft-delete).

- **AC-41**: Given un user admin viendo el detalle de otro usuario,
  When clickea "Forzar logout", Then se llama
  `/users?operation=admin&action=force-logout` con `{user_id}`, el
  backend blacklistea las familias de ese usuario, y se muestra toast
  "Sesiones del usuario revocadas".

- **AC-42**: Given un user admin en `/admin/users`, When abre el tab
  de auditoria, Then se llama
  `/users?operation=admin&action=list-admin-actions`, y se renderiza
  el audit log de acciones admin (accion, actor, target, fecha).

- **AC-43**: Given un user NO admin, When intenta acceder a
  `/admin/users` (o el cliente llama una action `admin.*`), Then el
  backend responde 404 NOT_FOUND y el admin no muestra la seccion en
  el sidebar (o redirige a `/admin` con un Alert).

### Build y deploy

- **AC-44**: Given el admin buildeado, When se inspecciona
  `admin/out/`, Then existen `index.html`, `404.html`,
  `_next/static/chunks/*.js`, `_next/static/css/*.css`,
  `_redirects`, `_headers`.

- **AC-45**: Given `_redirects` con `/* /index.html 200`, When un
  visitor accede a `/admin/users/usr_01`, Then Cloudflare Pages
  sirve `index.html` y el client-side router renderiza la page de
  detalle del usuario.

- **AC-46**: Given `_headers` con CSP estricta, When un visitor abre
  el admin, Then el header `Content-Security-Policy` se sirve
  correctamente y bloquea scripts inline NO permitidos (validado con
  curl + grep).

- **AC-47**: Given `devtools/cloudflare_setup/config.py` con el
  admin agregado, When se corre `python devtools/run.py
  cloudflare_setup status --env=dev`, Then el project
  `portfolio-admin-dev` existe + custom domain
  `admin.portfolio.dev.the-full-stack.com` attached + SSL emitido.

- **AC-48**: Given push a la branch `dev`, When `deploy-apps.yml`
  corre, Then los 7 apps se buildean en paralelo (workspace concurrency
  7), el admin deploya a `portfolio-admin-dev`, y
  `verify-deploy` confirma HTTP 200 en
  `https://admin.portfolio.dev.the-full-stack.com/`.

### Verificacion E2E

- **AC-49**: Given el stack local arriba + MSW activado, When se
  corren los specs `tests/feature/admin/*.spec.ts` con Playwright,
  Then los flujos golden path pasan: login con code, register +
  verify, magic-link callback, AuthGuard redirect, logout
  multi-tab sync, editar perfil en settings, revocar una sesion en
  sessions-mgmt.

- **AC-50**: Given el admin built, When se corre `pnpm --filter
  @portfolio/admin test:coverage`, Then coverage >= 80% per-file en
  todos los archivos modificados/creados (excluyendo `components/ui/*`,
  el barrel `index.ts` y los layouts).

[Volver al README](README.md) | [Siguiente: 02-diagramas >](02-diagramas.md)
