# 02 — Diagramas

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-estructura >](03-estructura.md)

## Flujo end-to-end del admin

### Antes (estado actual)

```text
Visitor browser
  -> apps/generic/...     -> Cloudflare Pages -> Astro estatico
  -> apps/hub/...
  -> apps/fintech/...
  -> apps/architect/...
  -> apps/leader/...
  -> apps/vibe/...

Backend Lambdas:
  -> contact_form
  -> tracking_pixel
  -> stream_processor
  -> db (migrations)

Data:
  -> DynamoDB (contacts, tracking, cache, rate-limit-*)
  -> Neon PostgreSQL (35 tablas, schema unificado)

Admin SPA: NO EXISTE
  -> data en Neon solo se ve con `psql` o consola web
```

### Despues (estado objetivo de este plan)

```text
Admin browser (1-5 users)
  -> https://admin.portfolio.{dev|stage|prod}.the-full-stack.com
  -> Cloudflare Pages (portfolio-admin-{env})
       -> Next.js 16.2.6 SPA estatico (admin/out/)
            -> React 19.2.6 + Zustand 5 (auth, theme)
                 -> Tanstack Query (con persister + mutex refresh)
                      -> lib/api-client.ts
                           -> https://api.portfolio.{env}.the-full-stack.com
                                -> Lambda auth (planes 01-02)
                                -> Lambda analytics (plan b-analytics-api)
                                -> Lambdas existentes (contact_form, tracking_pixel)

Las 6 apps Astro: SIN CAMBIOS (continuan en sus subdominios)
```

## Flujo de auth: registro con magic link

```text
1. User en /register llena email + Turnstile -> submit
        |
        v
2. POST /auth?operation=register&action=start
   body: {email, cf_turnstile_response}
        |
   [Backend Lambda auth]
        |
        v
3. Backend:
   - Valida Turnstile
   - Crea row auth_users(status=pending)
   - Genera magic-link token (32 bytes b64url, hash en Neon)
   - Genera code 8 chars Crockford (hash en Neon + espejo en DDB)
   - Publica 2 mensajes SQS (magic-link email + code email)
   - Issue temp_token (JWT typ=temp, exp=5min)
        |
        v
4. Response 201 {temp_token, user_id, expires_in: 300}
        |
        v
5. Frontend:
   - Zustand.setTempToken(token)
   - router.push('/verify?flow=register')
   - toast.success('Te enviamos un link y un code...')
        |
        v
6. ramificacion: el user elige magic-link O code

6a. Magic link:
    - User clickea link en email
    - URL: https://api.portfolio.../auth?operation=register&action=verify-magic-link&token=<X>
    - Backend valida token_hash, marca consumed, issue access+refresh
    - HTTP 302 Location: https://admin.portfolio.../auth/callback#access=<jwt>&user_id=<id>&email=<x>&refresh_exp=<epoch>
    - Browser carga /auth/callback (Next SPA)
    - useEffect decodifica fragment hash
    - Zustand.setAccessToken + setUser
    - history.replaceState(null, '', '/admin')
    - router.replace('/admin')
    - toast.success('Sesion iniciada')

6b. Code:
    - User vuelve a /verify, ingresa code 8 chars en InputOTP
    - POST /auth?operation=register&action=verify-code body: {code, temp_token}
    - Backend valida hash + ttl + attempts < 5
    - Response 200 {access_token, refresh_token, expires_in, user}
    - Frontend: Zustand.setTokens(access, refresh, user, refreshExpiry), redirect /admin
      (accessToken queda en memoria; refreshToken + refreshExpiry + user persistidos en localStorage)
```

## Flujo de auth: login con magic link / code

```text
1. /login - email + Turnstile (+ password opcional, login directo)
   POST /auth?operation=login&action=start
        |
        v
2. Backend:
   - Si email NO existe: 404 {error: EMAIL_NOT_FOUND, suggest_register: true}
   - Si email existe (status=active sin MFA): 200 {temp_token, methods: ['magic-link', 'email-code']}
   - Si email existe + password match + MFA configurado: 200 {temp_token, methods: ['totp', 'webauthn', 'email-code']}
        |
        v
3. Frontend:
   - Si 404: muestra Alert "Email no esta registrado" + boton "Registrate"
   - Si 200 sin MFA: redirect /verify?flow=login + similar a register
   - Si 200 con MFA: redirect /verify?flow=login + render input segun method preferred
```

## Flujo de refresh con mutex

```text
                    [5 requests concurrent]
                       /      |      \
                  GET /A   GET /B   GET /C
                     |        |        |
                     v        v        v
                  [HTTP 401] (access expirado)
                     |        |        |
                     +---+----+----+---+
                         |
                         v
              ┌────[ mutex check ]────┐
              |   inFlight === null?  |
              └──────────┬────────────┘
                         |
            ┌────────────┴────────────┐
            |                         |
        [primer caller]          [otros callers]
            |                         |
            v                         v
    inFlight = refresh()      await inFlight
            |                         |
            v                         |
   POST /session/refresh              |
   (backend rota familia)             |
            |                         |
    accessToken nuevo                 |
            |                         |
            v                         v
       inFlight = null         (resuelve)
            |                         |
            v                         v
    retry GET /A           retry GET /B y /C
                           (con accessToken nuevo)

  Sin mutex: 5 calls a /session/refresh
  -> backend ve 4 reuse -> revoca familia -> logout forzado
  Con mutex: 1 call -> 5 requests reintentan -> todo verde
```

## Flujo deploy a Cloudflare Pages

```text
1. Dev push a branch `dev`:
   git push origin feature/admin-frontend -> PR -> merge a dev
        |
        v
2. GitHub Actions:
   - branch-flow-guard.yml: valida cadena dev<-feature (OK)
   - ci.yml: lint + build admin + apps Astro (verifica que pasa)
   - deploy-apps.yml triggered en push a dev
        |
        v
3. deploy-apps.yml:
   job build-apps:
     environment: dev   <- lee GH Variables del env dev
     env:
       NEXT_PUBLIC_API_ENDPOINT: vars.NEXT_PUBLIC_API_ENDPOINT
       NEXT_PUBLIC_TURNSTILE_SITEKEY: vars.NEXT_PUBLIC_TURNSTILE_SITEKEY
       NEXT_PUBLIC_ADMIN_URL: vars.NEXT_PUBLIC_ADMIN_URL
     steps:
       - pnpm install --frozen-lockfile
       - pnpm -r --filter "./apps/*" --filter "@portfolio/admin" \
         --workspace-concurrency=7 run build
       - upload-artifact apps/*/dist + admin/out
        |
        v
4. job deploy-pages (matrix include con admin):
   strategy.matrix.include:
     - name: admin, dist-dir: admin/out, project: admin
     - name: generic, ...
     - name: hub, ...
     ...
   - cloudflare/wrangler-action: pages deploy <dist-dir> --project-name=portfolio-<project>-dev
        |
        v
5. Cloudflare Pages:
   - Recibe upload
   - Sirve en https://portfolio-admin-dev.pages.dev
   - Custom domain admin.portfolio.dev.the-full-stack.com -> CNAME -> pages.dev
        |
        v
6. job verify-deploy:
   - curl -sI https://admin.portfolio.dev.the-full-stack.com/ | head -1 | grep 200
        |
        v
7. Done. Promocion: PR dev->stage->main, mismo flujo en cada env.
```

## Arquitectura de auth state (frontend)

```text
┌────────────────────────────────────────────────────────────────┐
│                       Zustand auth store                       │
│                                                                │
│  EN MEMORIA (NO persist) — rotan / expiran:                    │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  accessToken         │         │  tempToken           │     │
│  │  null | JWT (15 min) │         │  null | JWT (5 min)  │     │
│  └──────────────────────┘         └──────────────────────┘     │
│                                                                │
│  PERSISTIDO en localStorage (partialize):                      │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  refreshToken        │         │  refreshExpiry       │     │
│  │  null | JWT (rot.)   │         │  null | epoch ms     │     │
│  └──────────────────────┘         └──────────────────────┘     │
│  ┌──────────────────────┐                                      │
│  │  user                │                                      │
│  │  {id, email, status} │                                      │
│  └──────────────────────┘                                      │
│                                                                │
│  Actions: setTokens, setAccessToken, setUser, setTempToken,    │
│           setRefreshExpiry, clearTokens, reset                 │
│  Derived: isAuthenticated(), isAccessExpired()                 │
│                                                                │
│  Bootstrap on reload: accessToken arranca null. useAuthTimer   │
│  detecta refreshToken + refreshExpiry > now -> dispara         │
│  /session/refresh para hidratar accessToken en memoria.        │
└────────────────────────────────────────────────────────────────┘
                       ▲              ▲
                       |              |
       ┌───────────────┴────┐  ┌──────┴──────────────────┐
       │                    │  │                         │
┌──────┴──────┐   ┌─────────┴──┴────────┐   ┌────────────┴──────┐
│ useLogout   │   │ useAuthTimer        │   │ useMultiTabSync   │
│ - reset     │   │ - jwt-decode exp    │   │ - BroadcastChannel│
│ - broadcast │   │ - setTimeout refresh│   │   ('portfolio_auth│
│ - clear()   │   │ - PageVisibility    │   │   '): LOGOUT      │
│ - redirect  │   │   re-check          │   │   TOKEN_REFRESH   │
└─────────────┘   └─────────────────────┘   └───────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              fetch wrapper (lib/api-client.ts)                    │
│  1. Read accessToken de Zustand                                   │
│  2. fetch(url, {Authorization: Bearer <token>, credentials: incl})│
│  3. Si 401 && !skipRefresh:                                       │
│       refreshed = await withRefreshMutex(performRefresh)          │
│       if refreshed: retry con token nuevo                          │
│       else: performLocalLogout (reset + broadcast)                │
│  4. Parse JSON + throw ApiError si !ok                            │
└──────────────────────────────────────────────────────────────────┘
                       ▲
                       |  (mutex: 1 sola call a /session/refresh)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│            refresh-mutex.ts (singleton in-flight Promise)         │
│  let inFlight: Promise<boolean> | null = null                     │
│  export async function withRefreshMutex(fn) {                     │
│    if (inFlight) return inFlight                                  │
│    inFlight = (async () => { ... }).finally(() => inFlight=null) │
│    return inFlight                                                │
│  }                                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## ER del state del admin (frontend, NO DB)

```text
[AuthStore] 1--1 [User?]
                  - id, email, status, has_password, mfa_methods

[QueryCache] (a-admin — auth + gestion)
  ['users', 'profile', 'get']            -> ProfileResponse
  ['users', 'status', 'list-sessions']   -> SessionsMgmtResponse (sesiones de MI cuenta)
  ['users', 'admin', 'list-users', {page, page_size}] -> UsersListResponse
  ['auth', 'mfa', 'list']                -> MfaMethodsResponse
  ['auth', 'webauthn', 'list']           -> PasskeysResponse

[QueryCache] (las keys de METRICAS las aporta b-analytics-api)
  ['analytics', 'overview', {from, to}]  -> OverviewResponse
  ['sessions', 'list', {page, page_size}] -> SessionsListResponse (tracking de visitantes)
  ['events', 'list', {page, page_size}]  -> EventsListResponse
  ['contacts', 'list', {page, page_size, status?}] -> ContactsListResponse
  ...

[FiltersStore] (Zustand local de cada feature; las de metricas en b-analytics-api)
  analytics: {date_range, niche?, event_type?}
  sessions: {date_range, country?, device_type?}
  events: {date_range, event_type?}

[ThemeProvider] (next-themes)
  theme: 'light' | 'dark' | 'system'
  data-theme: applied on <html>
```

(Este "ER" no es de DB sino de estructura de state — el admin NO
tiene DB propia. Las `[QueryCache]` de metricas las define el plan
b-analytics-api; aqui se listan solo para contexto.)

## Estructura de carpetas (vista alta)

```text
portfolio/  (repo root)
├── apps/                     # 6 apps Astro (sin cambios)
├── packages/                 # 5 packages compartidos (sin cambios)
├── admin/                # NUEVO — Admin SPA (Next.js export)
│   ├── src/
│   │   ├── app/              # Next App Router
│   │   ├── components/ui/    # shadcn primitives + custom genericos
│   │   ├── features/         # a-admin: auth, admin-shell, settings,
│   │   │                     #   sessions-mgmt, users-admin
│   │   │                     # b-analytics-api: analytics, sessions, events, ...
│   │   ├── lib/              # api-client, env, utils
│   │   ├── providers/        # query, theme, root
│   │   ├── hooks/            # globales
│   │   ├── styles/
│   │   └── types/
│   ├── public/               # _redirects, _headers, favicon
│   ├── tests/                # unit (Vitest) + mocks (MSW)
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── biome.json
│   ├── components.json
│   └── postcss.config.mjs
├── docker/
│   └── env/client/.example   # +NEXT_PUBLIC_* nuevas
├── devtools/
│   ├── cloudflare_setup/
│   │   └── config.py         # +APP_ADMIN
│   └── sync_secrets/
│       └── catalog.py        # +NEXT_PUBLIC_* nuevas
├── .github/workflows/
│   └── deploy-apps.yml       # +admin al matrix
├── tests/feature/
│   └── admin/            # NUEVO — Playwright specs
└── docs/specs/a-admin/     # ESTE PLAN (efimero)
```

(Ver detalle completo en [03-estructura.md](03-estructura.md).)

## Navegacion del admin shell (feature `admin-shell`)

El app shell (header + sidebar + `(admin)/layout.tsx` con AuthGuard) lo
aporta el plan a-admin. El sidebar declara los links/slots a todas las
areas, pero las PANTALLAS de metricas las implementa el plan
b-analytics-api: se montan en este mismo shell. Las marcadas
`(plan b-analytics-api)` NO se construyen aqui (en a-admin son links a
un placeholder o quedan ocultas hasta que b-analytics-api las monte).

```text
                  ┌──────────────────────────────────────────────┐
                  │  (admin)/layout.tsx  (a-admin)               │
                  │  AuthGuard -> Header + Sidebar  [persistente] │
                  └───────────────────┬──────────────────────────┘
                                      │ <slot> = children del route group
                                      v
   Sidebar nav-items                  Pantallas montadas en el slot
   ─────────────────                  ────────────────────────────────
   • Metricas (grupo)
       - /metrics    (overview)  ───> (plan b-analytics-api)
       - /analytics              ───> (plan b-analytics-api)
       - /sessions   (visitantes)───> (plan b-analytics-api)  [tracking]
       - /events                 ───> (plan b-analytics-api)
       - /visits                 ───> (plan b-analytics-api)
       - /geo                    ───> (plan b-analytics-api)
       - /devices                ───> (plan b-analytics-api)
       - /funnel                 ───> (plan b-analytics-api)
       - /contacts               ───> (plan b-analytics-api)
   • Settings
       - /settings               ───> perfil          (a-admin)
       - /settings/security      ───> MFA + WebAuthn + recovery codes
                                      + cambiar password (gap: dep backend)
                                      + change-email + delete-account  (a-admin)
   • Mis sesiones
       - /sessions-mgmt          ───> sesiones de MI cuenta auth
                                      (revocar login en otro dispositivo) (a-admin)
   • Usuarios (solo admin, whitelist SSM)
       - /users-admin            ───> gestionar OTROS usuarios  (a-admin)
   • Gestion CV
       - /cv                     ───> placeholder, plan futuro c-cv-management
                                      (sin backend ni UI de edicion)  (a-admin)
   • Cuenta (user menu)
       - logout                  ───> useLogout (reset + broadcast)  (a-admin)
```

Notas:

- "Mis sesiones" (`/sessions-mgmt`, feature `sessions-mgmt` de a-admin)
  son las sesiones de MI cuenta auth. NO confundir con `/sessions` de
  METRICAS (tracking de visitantes), que es del plan b-analytics-api.
- La ruta raiz del area de metricas es `/metrics`; el resto son rutas por
  feature. NO existe la ruta `/dashboard`.

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-estructura >](03-estructura.md)
