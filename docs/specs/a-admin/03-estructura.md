# 03 — Estructura completa de archivos

[< 02-diagramas](02-diagramas.md) | [Siguiente: 04-setup-base >](04-setup-base.md)

## Aclaracion

Esta seccion lista TODOS los archivos que crea el plan. La descripcion
detallada de cada uno vive en las secciones 04-08. Aqui solo el
inventario para chequeo rapido de "que tengo que crear".

Estructura completa Hybrid Atomic Design (referencia en
`.claude/docs/admin/02-structure.md`):

## `admin/` (carpeta root nueva)

### Configs (raiz)

```
admin/
├── package.json                       # nombre @portfolio/admin, scripts, deps
├── next.config.ts                     # output: 'export', trailingSlash, images.unoptimized
├── tsconfig.json                      # strict + noUncheckedIndexedAccess + paths @/*
├── biome.json                         # extends del root + override components/ui/*
├── components.json                    # shadcn config
├── postcss.config.mjs                 # tailwindcss + autoprefixer
├── vitest.config.ts                   # happy-dom + coverage + alias
├── next-env.d.ts                      # generado por next dev (gitignored)
├── README.md                          # corto, link a knowledge tree y plan
└── .gitignore                         # .next, out, node_modules, *.tsbuildinfo
```

### `admin/src/styles/`

```
src/styles/
└── globals.css                        # @import tailwind + tokens HSL + @theme inline + base
```

### `admin/src/lib/`

```
src/lib/
├── env.ts                             # Zod schema validacion NEXT_PUBLIC_*
├── utils.ts                           # cn() de shadcn
├── api-client.ts                      # fetch wrapper + auth interceptor + mutex
├── routes.ts                          # constantes de paths (ROUTES.admin.settings, ROUTES.auth.login)
├── format/
│   ├── date.ts                        # formatDate, relativeTime
│   ├── number.ts                      # formatNumber, formatPercent
│   └── duration.ts                    # formatDurationMs (00:01:23)
└── validation/
    ├── auth.ts                        # loginSchema, registerSchema, verifyCodeSchema
    └── filters.ts                     # dateRangeSchema, paginationSchema
```

### `admin/src/types/`

```
src/types/
├── api.ts                             # types de responses /auth y /users
├── models.ts                          # User, MfaMethod, WebauthnCredential, AccountSession, AdminAction
└── env.d.ts                           # type-safe NEXT_PUBLIC_*
```

### `admin/src/providers/`

```
src/providers/
├── theme-provider.tsx                 # next-themes wrapper
├── query-provider.tsx                 # Tanstack Query + PersistQueryClient
└── root-providers.tsx                 # composicion (ThemeProvider > QueryProvider)
```

### `admin/src/hooks/`

```
src/hooks/                             # globales (no de feature)
├── use-debounce.ts
├── use-media-query.ts
├── use-local-storage.ts               # type-safe wrapper
└── use-mounted.ts                     # evitar hydration warnings
```

### `admin/src/components/ui/` — shadcn primitives + custom

```
src/components/ui/
# shadcn primitives (via pnpm dlx shadcn add):
├── alert.tsx
├── badge.tsx
├── button.tsx
├── calendar.tsx
├── card.tsx
├── chart.tsx                          # Recharts wrapper de shadcn
├── checkbox.tsx
├── command.tsx                        # cmdk
├── dialog.tsx
├── dropdown-menu.tsx
├── form.tsx
├── input.tsx
├── input-otp.tsx                      # para code 8 chars register/login
├── label.tsx
├── popover.tsx
├── select.tsx
├── separator.tsx
├── sheet.tsx                          # mobile sidebar
├── skeleton.tsx
├── sonner.tsx                         # Toaster
├── switch.tsx
├── table.tsx
├── tabs.tsx
├── tooltip.tsx

# Custom UI primitives (genericos, no shadcn):
├── metric-card.tsx                    # title/value/delta/icon
├── data-table.tsx                     # Tanstack Table wrapper
├── date-range-picker.tsx              # Popover + Calendar
├── empty-state.tsx                    # icon + title + description + action
├── error-alert.tsx                    # Alert variant=destructive con retry
├── loading-spinner.tsx
├── theme-toggle.tsx                   # ciclo dark/light/system
└── index.ts                           # barrel
```

### `admin/src/features/` — un dominio por carpeta

> Las features de METRICAS (`analytics`, `sessions` de tracking, `events`,
> `visits`, `geo`, `devices`, `funnel`, `contacts`) NO se crean en este plan.
> Viven en el plan `b-analytics-api`, que monta sus PANTALLAS dentro del app
> shell del admin (`admin-shell`) y agrega sus rutas en `app/(admin)/`. El
> plan `a-admin` crea SOLO: `auth`, `admin-shell`, `settings`,
> `sessions-mgmt` y `users-admin`.

#### `features/auth/`

```
features/auth/
├── components/
│   ├── login-form.tsx
│   ├── register-form.tsx
│   ├── verify-code-input.tsx          # InputOTP 8 chars Crockford
│   ├── magic-link-prompt.tsx          # "te enviamos un link..."
│   ├── set-password-form.tsx
│   ├── totp-setup.tsx                 # QR (del otpauth_url) + InputOTP 6 digitos
│   ├── recovery-codes-modal.tsx
│   ├── webauthn-register-button.tsx   # @simplewebauthn/browser
│   ├── auth-guard.tsx                 # HOC para proteger rutas
│   └── turnstile-widget.tsx
├── hooks/
│   ├── use-register-start.ts
│   ├── use-register-verify-code.ts
│   ├── use-login-start.ts
│   ├── use-login-verify-code.ts
│   ├── use-login-verify-totp.ts
│   ├── use-set-password.ts
│   ├── use-resend-code.ts
│   ├── use-session-refresh.ts
│   ├── use-logout.ts
│   ├── use-auth-timer.ts              # auto-refresh + PageVisibility
│   ├── use-multi-tab-sync.ts          # BroadcastChannel
│   └── use-protected-route.ts         # alternative al AuthGuard
├── api/
│   ├── auth-client.ts                 # endpoints typed
│   └── query-keys.ts
├── store/
│   └── use-auth-store.ts              # Zustand (accessToken + tempToken en memoria; refreshToken + user + refreshExpiry persist en localStorage)
├── lib/
│   ├── refresh-mutex.ts               # singleton in-flight Promise
│   ├── broadcast.ts                   # BroadcastChannel helpers
│   └── token-expiry.ts                # jwt-decode helpers
├── types.ts                           # AuthResponse, User, Method, MfaMethod
└── index.ts                           # barrel
```

#### `features/admin-shell/`

```
features/admin-shell/
├── components/
│   ├── sidebar.tsx                    # nav links + user menu
│   ├── header.tsx                     # breadcrumb + theme + logout
│   └── mobile-sidebar.tsx             # Sheet
├── lib/
│   └── nav-items.ts                   # array de items con href, icon, label.
│                                      #   Incluye SLOTS hacia las secciones de
│                                      #   metricas (b-analytics-api), settings,
│                                      #   sessions de cuenta, users-admin y el
│                                      #   placeholder de gestion CV. Las
│                                      #   PANTALLAS de metricas las agrega
│                                      #   b-analytics-api, NO este plan.
└── index.ts
```

> Las features de metricas (`analytics`, `sessions` de tracking, `events`,
> `visits`, `geo`, `devices`, `funnel`, `contacts`) que antes vivian aqui se
> MUEVEN al plan `b-analytics-api`. No se crean en `a-admin`.

#### `features/settings/`

Perfil + seguridad de la cuenta del user autenticado. Consume el Lambda
`auth` (operations `mfa` + `webauthn`) y el Lambda `users` (operation
`profile`).

```
features/settings/
├── components/
│   ├── profile-form.tsx                  # display_name (users.profile.update)
│   ├── change-email-form.tsx             # new_email (users.profile.change-email)
│   ├── confirm-email-change.tsx          # token (users.profile.confirm-email-change)
│   ├── change-password-form.tsx          # UI lista; BLOQUEADA por gap backend (ver nota)
│   ├── mfa-methods-list.tsx              # lista + set-preferred + disable (auth.mfa)
│   ├── totp-setup-section.tsx           # auth.mfa setup-totp/confirm-totp (QR del otpauth_url)
│   ├── email-code-section.tsx           # auth.mfa setup-email-code
│   ├── webauthn-credentials-list.tsx    # auth.webauthn register/list/delete-credential
│   ├── recovery-codes-section.tsx       # auth.mfa recovery-codes-generate/list
│   └── delete-account-dialog.tsx        # confirm (users.profile.delete-account)
├── hooks/
│   ├── use-profile.ts                    # users.profile.get
│   ├── use-update-profile.ts             # users.profile.update
│   ├── use-change-email.ts               # users.profile.change-email + confirm
│   ├── use-change-password.ts            # BLOQUEADA: depende de action backend nueva
│   ├── use-mfa-methods.ts                # auth.mfa (setup/confirm/set-preferred/disable)
│   ├── use-webauthn-credentials.ts       # auth.webauthn (register/list/delete)
│   ├── use-recovery-codes.ts             # auth.mfa recovery-codes
│   └── use-delete-account.ts             # users.profile.delete-account
├── api/
│   ├── settings-client.ts                # endpoints typed auth.mfa/webauthn + users.profile
│   └── query-keys.ts
├── types.ts
└── index.ts
```

> **GAP de backend — cambio de contraseña.** El backend NO tiene una action
> para que un user AUTENTICADO cambie su password (`auth.verify.set-password`
> usa `temp_token` del flujo register/login, NO el access JWT;
> `users.profile` no tiene `change-password`). La UI de `change-password-form`
> se construye en este plan pero queda BLOQUEADA por la dependencia de
> backend: una action nueva `users.profile.change-password` con
> `{current_password, new_password}` validada con el access JWT. Mientras no
> exista: MSW la mockea, NO se puede testear E2E real. Documentar como
> pre-requisito de backend del plan `c-cv-management` o un plan dedicado.

#### `features/sessions-mgmt/`

Sesiones de MI cuenta (auth): ver mis logins activos y revocar el de otro
dispositivo. Consume el Lambda `users` (operation `status`). NO confundir con
la feature `sessions` de METRICAS (tracking de visitantes) del plan
`b-analytics-api`.

```
features/sessions-mgmt/
├── components/
│   ├── account-sessions-table.tsx        # mis sesiones (users.status.list-sessions)
│   └── revoke-session-button.tsx         # users.status.revoke-session (no la actual -> 400)
├── hooks/
│   ├── use-account-status.ts             # users.status.get
│   ├── use-account-sessions.ts           # users.status.list-sessions
│   └── use-revoke-session.ts             # users.status.revoke-session
├── api/
│   ├── sessions-mgmt-client.ts
│   └── query-keys.ts
├── types.ts
└── index.ts
```

#### `features/users-admin/`

Gestionar OTROS usuarios. Consume el Lambda `users` (operation `admin`). Solo
admin (whitelist SSM `/portfolio/admin-emails`; no-admin -> 404 NOT_FOUND).

```
features/users-admin/
├── components/
│   ├── users-table.tsx                   # list-users (page/page_size)
│   ├── user-detail-dialog.tsx            # get-user
│   ├── user-actions-menu.tsx             # disable/enable/delete/force-logout
│   └── admin-actions-log.tsx             # list-admin-actions (audit)
├── hooks/
│   ├── use-users-list.ts                 # users.admin.list-users
│   ├── use-user-detail.ts                # users.admin.get-user
│   ├── use-disable-user.ts               # users.admin.disable-user
│   ├── use-enable-user.ts                # users.admin.enable-user
│   ├── use-delete-user.ts                # users.admin.delete-user
│   ├── use-force-logout.ts               # users.admin.force-logout
│   └── use-admin-actions.ts              # users.admin.list-admin-actions
├── api/
│   ├── users-admin-client.ts
│   └── query-keys.ts
├── types.ts
└── index.ts
```

### `admin/src/app/` — Next App Router

```
src/app/
├── layout.tsx                         # RootLayout: providers + Toaster + fonts
├── page.tsx                           # / -> redirect a /admin si logueado, else /login
├── error.tsx                          # error boundary global
├── global-error.tsx                   # fallback ultimo
├── not-found.tsx                      # 404
│
├── (auth)/                            # route group, sin layout compartido
│   ├── login/page.tsx
│   ├── register/page.tsx
│   ├── verify/page.tsx                # ?flow=register|login, input de code
│   ├── callback/page.tsx              # decodea fragment hash del magic link
│   └── set-password/page.tsx          # opcional post-registro
│
└── (admin)/                       # route group, layout protegido
    ├── layout.tsx                     # AuthGuard + Sidebar + Header (admin-shell)
    ├── page.tsx                       # /admin (landing del shell; el overview de
    │                                  #   metricas lo agrega b-analytics-api en /metrics)
    ├── account-sessions/page.tsx      # mis sesiones de cuenta (feature sessions-mgmt).
    │                                  #   NOMBRE distinto de la /sessions de METRICAS de
    │                                  #   b-analytics-api para NO chocar
    ├── users/page.tsx                 # gestion de otros usuarios (feature users-admin, solo admin)
    ├── cv/page.tsx                    # PLACEHOLDER gestion CV: page vacia + nota
    │                                  #   "plan futuro c-cv-management". SIN backend ni edicion
    └── settings/
        ├── page.tsx                   # perfil (display_name, change-email, eliminar cuenta)
        └── security/page.tsx          # MFA (totp/email-code/set-preferred/disable) +
                                       #   WebAuthn + recovery codes + cambio de password (UI, gap)
```

> Las rutas de METRICAS (`/metrics`, `/analytics`, `/sessions`, `/events`,
> `/visits`, `/geo`, `/devices`, `/funnel`, `/contacts`) NO las agrega este
> plan: las agrega `b-analytics-api` dentro de este mismo route group
> `(admin)/`. La `/account-sessions` de aqui (sesiones de mi cuenta) y la
> `/sessions` de metricas (tracking de visitantes) son rutas distintas.

### `admin/public/`

```
public/
├── _redirects                         # /* /index.html 200 + /api/* 404
├── _headers                           # CSP + HSTS + cache
├── favicon.ico
├── og-image.png
└── mockServiceWorker.js               # generado por `npx msw init public/`
```

### `admin/tests/`

```
tests/
├── setup.ts                           # vitest setup global
├── utils/
│   └── render.tsx                     # render wrapper con providers
├── mocks/
│   ├── server.ts                      # setupServer (Node)
│   ├── browser.ts                     # setupWorker (browser dev)
│   └── handlers/
│       ├── auth.ts                    # register/login/verify/session/mfa/webauthn
│       └── users.ts                   # profile/status/admin (incl. change-password mock del gap)
├── fixtures/
│   ├── users.ts
│   └── account-sessions.ts            # sesiones de cuenta (sessions-mgmt)
└── unit/                              # mirror de src/
    ├── lib/
    │   ├── api-client.test.ts         # crit: mutex refresh test
    │   ├── env.test.ts
    │   ├── routes.test.ts
    │   └── format/
    │       ├── date.test.ts
    │       ├── number.test.ts
    │       └── duration.test.ts
    ├── components/ui/
    │   ├── metric-card.test.tsx
    │   ├── data-table.test.tsx
    │   ├── empty-state.test.tsx
    │   └── theme-toggle.test.tsx
    └── features/
        ├── auth/
        │   ├── components/
        │   │   ├── login-form.test.tsx
        │   │   ├── register-form.test.tsx
        │   │   ├── verify-code-input.test.tsx
        │   │   ├── auth-guard.test.tsx
        │   │   └── turnstile-widget.test.tsx
        │   ├── hooks/
        │   │   ├── use-login-start.test.ts
        │   │   ├── use-logout.test.ts
        │   │   ├── use-auth-timer.test.ts
        │   │   └── use-multi-tab-sync.test.ts
        │   ├── store/
        │   │   └── use-auth-store.test.ts
        │   ├── lib/
        │   │   ├── refresh-mutex.test.ts
        │   │   ├── broadcast.test.ts
        │   │   └── token-expiry.test.ts
        │   └── api/
        │       └── auth-client.test.ts
        ├── settings/
        │   ├── components/
        │   │   ├── profile-form.test.tsx
        │   │   ├── change-email-form.test.tsx
        │   │   ├── change-password-form.test.tsx   # contra MSW (gap backend)
        │   │   ├── mfa-methods-list.test.tsx
        │   │   ├── webauthn-credentials-list.test.tsx
        │   │   └── delete-account-dialog.test.tsx
        │   └── hooks/
        │       ├── use-update-profile.test.ts
        │       └── use-mfa-methods.test.ts
        ├── sessions-mgmt/
        │   ├── components/
        │   │   ├── account-sessions-table.test.tsx
        │   │   └── revoke-session-button.test.tsx
        │   └── hooks/
        │       └── use-revoke-session.test.ts
        └── users-admin/
            ├── components/
            │   ├── users-table.test.tsx
            │   └── user-actions-menu.test.tsx
            └── hooks/
                └── use-disable-user.test.ts
```

> Las features de METRICAS (`analytics`, `sessions` de tracking, `events`,
> `visits`, `geo`, `devices`, `funnel`, `contacts`) y sus tests viven en el
> plan `b-analytics-api`.

## Cambios a archivos existentes (fuera de `admin/`)

### Root del repo

```
pnpm-workspace.yaml                    # +'admin' al array packages
.gitignore                             # +admin/.next, admin/out, etc.
```

### `docker/env/client/`

```
.example                               # +6 vars del admin: NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_ADMIN_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS, NEXT_PUBLIC_FEATURE_MFA, NEXT_PUBLIC_WEBAUTHN_RP_ID
.local                                 # (gitignored, dev local)
.dev, .stage, .prod                    # (gitignored, sync_secrets los lee)
```

### `devtools/cloudflare_setup/`

```
config.py                              # +APP_ADMIN AppConfig (app_type='nextjs', build_output_dir='out')
                                       # +funciones para custom_domain_for, env_vars_for con admin
README.md                              # mencionar el admin como 7mo app
```

### `devtools/sync_secrets/`

```
catalog.py                             # +4 entradas SecretDefinition para NEXT_PUBLIC_*
README.md                              # mencionar las nuevas keys
```

### `.github/workflows/`

```
deploy-apps.yml                        # +admin al matrix include
                                       # +env vars NEXT_PUBLIC_* al build-apps job
                                       # +admin al verify-deploy matrix
ci.yml                                 # +admin al filter del build step
```

### `.claude/docs/subdomain-standard/`

```
02-naming-rules.md                     # +'admin' a la lista de reservados
```

### `tests/feature/`

```
admin/
├── 01-login-magic-link.spec.ts
├── 02-register-verify-code.spec.ts
├── 03-callback-fragment-hash.spec.ts
├── 04-auth-guard-redirect.spec.ts
├── 05-logout-multi-tab.spec.ts
├── 06-settings-profile-update.spec.ts        # settings: display_name
├── 07-settings-mfa-totp-setup.spec.ts        # settings/security: TOTP setup
└── 08-account-sessions-revoke.spec.ts        # sessions-mgmt: revocar otra sesion
```

> Los specs de METRICAS (navegacion analytics, tabla de sessions de tracking,
> ...) los agrega el plan `b-analytics-api`.

## Conteo de archivos

| Tipo | Cantidad |
|------|----------|
| Configs raiz (admin/) | 9 |
| `src/lib/` | 8 |
| `src/types/` | 3 |
| `src/providers/` | 3 |
| `src/hooks/` (globales) | 4 |
| `src/styles/` | 1 |
| `src/components/ui/` (shadcn) | 24 |
| `src/components/ui/` (custom) | 7 |
| `src/features/auth/` | ~25 |
| `src/features/admin-shell/` | 4 |
| `src/features/settings/` | ~22 |
| `src/features/sessions-mgmt/` | ~9 |
| `src/features/users-admin/` | ~14 |
| `src/app/` (pages + layouts) | ~13 |
| `tests/` (mocks + fixtures + unit) | ~35 |
| `tests/feature/admin/` (Playwright) | 8 |
| Cambios fuera de `admin/` | ~7 |

**Total estimado**: ~150 archivos nuevos + ~7 modificados. Plan **Large**.
Las features de metricas (~70 archivos) viven en `b-analytics-api`.

[< 02-diagramas](02-diagramas.md) | [Siguiente: 04-setup-base >](04-setup-base.md)
