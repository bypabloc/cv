# 02 — Diagramas

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-estructura >](03-estructura.md)

## Flujo end-to-end del dashboard

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

Dashboard admin: NO EXISTE
  -> data en Neon solo se ve con `psql` o consola web
```

### Despues (estado objetivo de este plan)

```text
Admin browser (1-5 users)
  -> https://admin.portfolio.{dev|stage|prod}.the-full-stack.com
  -> Cloudflare Pages (portfolio-dashboard-{env})
       -> Next.js 16.2.6 SPA estatico (dashboard/out/)
            -> React 19.2.6 + Zustand 5 (auth, theme)
                 -> Tanstack Query (con persister + mutex refresh)
                      -> lib/api-client.ts
                           -> https://api.portfolio.{env}.the-full-stack.com
                                -> Lambda auth (planes 01-02)
                                -> Lambda analytics (plan a-analytics-dashboard-api)
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
    - history.replaceState(null, '', '/dashboard')
    - router.replace('/dashboard')
    - toast.success('Sesion iniciada')

6b. Code:
    - User vuelve a /verify, ingresa code 8 chars en InputOTP
    - POST /auth?operation=register&action=verify-code body: {code, temp_token}
    - Backend valida hash + ttl + attempts < 5
    - Response 200 {access_token, refresh_token, expires_in, user}
    - Frontend: Zustand.setTokens(access, refresh, user, refreshExpiry), redirect /dashboard
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
   git push origin feature/dashboard-frontend -> PR -> merge a dev
        |
        v
2. GitHub Actions:
   - branch-flow-guard.yml: valida cadena dev<-feature (OK)
   - ci.yml: lint + build dashboard + apps Astro (verifica que pasa)
   - deploy-apps.yml triggered en push a dev
        |
        v
3. deploy-apps.yml:
   job build-apps:
     environment: dev   <- lee GH Variables del env dev
     env:
       NEXT_PUBLIC_API_ENDPOINT: vars.NEXT_PUBLIC_API_ENDPOINT
       NEXT_PUBLIC_TURNSTILE_SITEKEY: vars.NEXT_PUBLIC_TURNSTILE_SITEKEY
       NEXT_PUBLIC_DASHBOARD_URL: vars.NEXT_PUBLIC_DASHBOARD_URL
     steps:
       - pnpm install --frozen-lockfile
       - pnpm -r --filter "./apps/*" --filter "@portfolio/dashboard" \
         --workspace-concurrency=7 run build
       - upload-artifact apps/*/dist + dashboard/out
        |
        v
4. job deploy-pages (matrix include con dashboard):
   strategy.matrix.include:
     - name: dashboard, dist-dir: dashboard/out, project: dashboard
     - name: generic, ...
     - name: hub, ...
     ...
   - cloudflare/wrangler-action: pages deploy <dist-dir> --project-name=portfolio-<project>-dev
        |
        v
5. Cloudflare Pages:
   - Recibe upload
   - Sirve en https://portfolio-dashboard-dev.pages.dev
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

## ER del state del dashboard (frontend, NO DB)

```text
[AuthStore] 1--1 [User?]
                  - id, email, status, has_password, mfa_methods

[QueryCache]
  ['analytics', 'overview', {from, to}]  -> OverviewResponse
  ['analytics', 'timeseries', {from, to, bucket}] -> TimeseriesResponse
  ['sessions', 'list', {page, page_size}] -> SessionsListResponse
  ['sessions', 'detail', sessionId] -> SessionDetailResponse
  ['events', 'list', {page, page_size}] -> EventsListResponse
  ['contacts', 'list', {page, page_size, status?}] -> ContactsListResponse
  ...

[FiltersStore] (Zustand local de cada feature)
  analytics: {date_range, niche?, event_type?}
  sessions: {date_range, country?, device_type?}
  events: {date_range, event_type?}

[ThemeProvider] (next-themes)
  theme: 'light' | 'dark' | 'system'
  data-theme: applied on <html>
```

(Este "ER" no es de DB sino de estructura de state — el dashboard NO
tiene DB propia.)

## Estructura de carpetas (vista alta)

```text
portfolio/  (repo root)
├── apps/                     # 6 apps Astro (sin cambios)
├── packages/                 # 5 packages compartidos (sin cambios)
├── dashboard/                # NUEVO — dashboard SPA
│   ├── src/
│   │   ├── app/              # Next App Router
│   │   ├── components/ui/    # shadcn primitives + custom genericos
│   │   ├── features/         # auth, analytics, sessions, ...
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
│   │   └── config.py         # +APP_DASHBOARD
│   └── sync_secrets/
│       └── catalog.py        # +NEXT_PUBLIC_* nuevas
├── .github/workflows/
│   └── deploy-apps.yml       # +dashboard al matrix
├── tests/feature/
│   └── dashboard/            # NUEVO — Playwright specs
└── docs/specs/b-dashboard/     # ESTE PLAN (efimero)
```

(Ver detalle completo en [03-estructura.md](03-estructura.md).)

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-estructura >](03-estructura.md)
