# 03 — Estructura completa de archivos

[< 02-diagramas](02-diagramas.md) | [Siguiente: 04-setup-base >](04-setup-base.md)

## Aclaracion

Esta seccion lista TODOS los archivos que crea el plan. La descripcion
detallada de cada uno vive en las secciones 04-08. Aqui solo el
inventario para chequeo rapido de "que tengo que crear".

Estructura completa Hybrid Atomic Design (referencia en
`.claude/docs/dashboard/02-structure.md`):

## `dashboard/` (carpeta root nueva)

### Configs (raiz)

```
dashboard/
├── package.json                       # nombre @portfolio/dashboard, scripts, deps
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

### `dashboard/src/styles/`

```
src/styles/
└── globals.css                        # @import tailwind + tokens HSL + @theme inline + base
```

### `dashboard/src/lib/`

```
src/lib/
├── env.ts                             # Zod schema validacion NEXT_PUBLIC_*
├── utils.ts                           # cn() de shadcn
├── api-client.ts                      # fetch wrapper + auth interceptor + mutex
├── routes.ts                          # constantes de paths (ROUTES.dashboard.analytics)
├── format/
│   ├── date.ts                        # formatDate, relativeTime
│   ├── number.ts                      # formatNumber, formatPercent
│   └── duration.ts                    # formatDurationMs (00:01:23)
└── validation/
    ├── auth.ts                        # loginSchema, registerSchema, verifyCodeSchema
    └── filters.ts                     # dateRangeSchema, paginationSchema
```

### `dashboard/src/types/`

```
src/types/
├── api.ts                             # types de responses /auth y /analytics
├── models.ts                          # User, Session, Visit, Event, Contact
└── env.d.ts                           # type-safe NEXT_PUBLIC_*
```

### `dashboard/src/providers/`

```
src/providers/
├── theme-provider.tsx                 # next-themes wrapper
├── query-provider.tsx                 # Tanstack Query + PersistQueryClient
└── root-providers.tsx                 # composicion (ThemeProvider > QueryProvider)
```

### `dashboard/src/hooks/`

```
src/hooks/                             # globales (no de feature)
├── use-debounce.ts
├── use-media-query.ts
├── use-local-storage.ts               # type-safe wrapper
└── use-mounted.ts                     # evitar hydration warnings
```

### `dashboard/src/components/ui/` — shadcn primitives + custom

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

### `dashboard/src/features/` — un dominio por carpeta

#### `features/auth/`

```
features/auth/
├── components/
│   ├── login-form.tsx
│   ├── register-form.tsx
│   ├── verify-code-input.tsx          # InputOTP 8 chars Crockford
│   ├── magic-link-prompt.tsx          # "te enviamos un link..."
│   ├── set-password-form.tsx
│   ├── totp-setup.tsx                 # QR + InputOTP (plan 02)
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

#### `features/dashboard-shell/`

```
features/dashboard-shell/
├── components/
│   ├── sidebar.tsx                    # nav links + user menu
│   ├── header.tsx                     # breadcrumb + theme + logout
│   └── mobile-sidebar.tsx             # Sheet
├── lib/
│   └── nav-items.ts                   # array de items con href, icon, label
└── index.ts
```

#### `features/analytics/`

```
features/analytics/
├── components/
│   ├── overview-cards.tsx             # 7 MetricCard
│   ├── timeseries-chart.tsx           # AreaChart
│   ├── top-pages-chart.tsx            # BarChart
│   ├── top-referrers-table.tsx        # DataTable
│   ├── top-niches-chart.tsx           # BarChart
│   ├── active-now-card.tsx            # refetchInterval 15s
│   ├── retention-chart.tsx
│   └── analytics-filters.tsx          # DateRangePicker + niche Select
├── hooks/
│   ├── use-overview-query.ts
│   ├── use-timeseries-query.ts
│   ├── use-top-pages-query.ts
│   ├── use-top-referrers-query.ts
│   ├── use-top-niches-query.ts
│   ├── use-active-now-query.ts
│   ├── use-retention-query.ts
│   └── use-analytics-filters.ts       # Zustand local
├── api/
│   ├── analytics-client.ts
│   └── query-keys.ts
├── store/
│   └── use-analytics-filters.ts       # date_range, niche
├── types.ts
└── index.ts
```

#### `features/sessions/`

```
features/sessions/
├── components/
│   ├── sessions-table.tsx
│   ├── session-detail-drawer.tsx     # Sheet lateral, lee ?session=<id> con useSearchParams
│   └── sessions-filters.tsx
├── hooks/
│   ├── use-sessions-list.ts
│   ├── use-session-detail.ts
│   └── use-sessions-filters.ts
├── api/
│   ├── sessions-client.ts
│   └── query-keys.ts
├── store/
│   └── use-sessions-filters.ts
├── types.ts
└── index.ts
```

#### `features/events/`

```
features/events/
├── components/
│   ├── events-distribution-chart.tsx
│   ├── events-list-table.tsx          # con Tanstack Virtual
│   └── events-heatmap.tsx             # dia_semana x hora
├── hooks/
│   ├── use-events-distribution.ts
│   ├── use-events-list.ts
│   └── use-events-heatmap.ts
├── api/
│   ├── events-client.ts
│   └── query-keys.ts
├── types.ts
└── index.ts
```

#### `features/visits/`

```
features/visits/
├── components/
│   ├── visits-list-table.tsx
│   └── landing-pages-chart.tsx
├── hooks/
├── api/
├── types.ts
└── index.ts
```

#### `features/geo/`

```
features/geo/
├── components/
│   └── geo-by-country-chart.tsx
├── hooks/
├── api/
├── types.ts
└── index.ts
```

#### `features/devices/`

```
features/devices/
├── components/
│   ├── device-pie-chart.tsx
│   ├── browser-bar-chart.tsx
│   └── os-bar-chart.tsx
├── hooks/
├── api/
├── types.ts
└── index.ts
```

#### `features/funnel/`

```
features/funnel/
├── components/
│   └── funnel-chart.tsx
├── hooks/
├── api/
├── types.ts
└── index.ts
```

#### `features/contacts/`

```
features/contacts/
├── components/
│   ├── contacts-table.tsx
│   ├── contacts-by-status-chart.tsx
│   ├── contact-detail-dialog.tsx
│   └── update-status-button.tsx       # mutation
├── hooks/
│   ├── use-contacts-list.ts
│   ├── use-contacts-by-status.ts
│   └── use-update-contact-status.ts
├── api/
│   ├── contacts-client.ts
│   └── query-keys.ts
├── types.ts
└── index.ts
```

#### `features/settings/`

```
features/settings/
├── components/
│   ├── profile-form.tsx
│   ├── change-password-form.tsx
│   ├── mfa-methods-list.tsx
│   ├── webauthn-credentials-list.tsx
│   └── recovery-codes-section.tsx
├── hooks/
├── api/
├── types.ts
└── index.ts
```

### `dashboard/src/app/` — Next App Router

```
src/app/
├── layout.tsx                         # RootLayout: providers + Toaster + fonts
├── page.tsx                           # / -> redirect a /dashboard si logueado, else /login
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
└── (dashboard)/                       # route group, layout protegido
    ├── layout.tsx                     # AuthGuard + Sidebar + Header
    ├── page.tsx                       # /dashboard (overview)
    ├── analytics/page.tsx
    ├── sessions/page.tsx              # list + SessionDetailDrawer (deep-link via ?session=<id>; NO ruta dinamica [id], incompatible con output: 'export')
    ├── events/page.tsx
    ├── visits/page.tsx
    ├── geo/page.tsx
    ├── devices/page.tsx
    ├── funnel/page.tsx
    ├── contacts/page.tsx
    └── settings/
        ├── page.tsx                   # profile
        └── security/page.tsx          # MFA setup
```

### `dashboard/public/`

```
public/
├── _redirects                         # /* /index.html 200 + /api/* 404
├── _headers                           # CSP + HSTS + cache
├── favicon.ico
├── og-image.png
└── mockServiceWorker.js               # generado por `npx msw init public/`
```

### `dashboard/tests/`

```
tests/
├── setup.ts                           # vitest setup global
├── utils/
│   └── render.tsx                     # render wrapper con providers
├── mocks/
│   ├── server.ts                      # setupServer (Node)
│   ├── browser.ts                     # setupWorker (browser dev)
│   └── handlers/
│       ├── auth.ts
│       ├── analytics.ts
│       ├── sessions.ts
│       ├── events.ts
│       ├── visits.ts
│       ├── geo.ts
│       ├── devices.ts
│       ├── funnel.ts
│       └── contacts.ts
├── fixtures/
│   ├── users.ts
│   ├── sessions.ts
│   ├── events.ts
│   └── analytics.ts
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
        ├── analytics/
        │   ├── components/
        │   │   ├── overview-cards.test.tsx
        │   │   ├── timeseries-chart.test.tsx
        │   │   └── analytics-filters.test.tsx
        │   ├── hooks/
        │   │   ├── use-overview-query.test.ts
        │   │   └── use-analytics-filters.test.ts
        │   └── store/
        │       └── use-analytics-filters.test.ts
        ├── sessions/
        │   ├── components/
        │   │   ├── sessions-table.test.tsx
        │   │   └── session-detail-drawer.test.tsx
        │   └── hooks/
        ├── events/
        ├── visits/
        ├── geo/
        ├── devices/
        ├── funnel/
        ├── contacts/
        │   ├── components/
        │   │   ├── contacts-table.test.tsx
        │   │   └── update-status-button.test.tsx
        │   └── hooks/
        └── settings/
```

## Cambios a archivos existentes (no del dashboard)

### Root del repo

```
pnpm-workspace.yaml                    # +'dashboard' al array packages
.gitignore                             # +dashboard/.next, dashboard/out, etc.
```

### `docker/env/client/`

```
.example                               # +6 vars del dashboard: NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_DASHBOARD_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS, NEXT_PUBLIC_FEATURE_MFA, NEXT_PUBLIC_WEBAUTHN_RP_ID
.local                                 # (gitignored, dev local)
.dev, .stage, .prod                    # (gitignored, sync_secrets los lee)
```

### `devtools/cloudflare_setup/`

```
config.py                              # +APP_DASHBOARD AppConfig (app_type='nextjs', build_output_dir='out')
                                       # +funciones para custom_domain_for, env_vars_for con dashboard
README.md                              # mencionar el dashboard como 7mo app
```

### `devtools/sync_secrets/`

```
catalog.py                             # +4 entradas SecretDefinition para NEXT_PUBLIC_*
README.md                              # mencionar las nuevas keys
```

### `.github/workflows/`

```
deploy-apps.yml                        # +dashboard al matrix include
                                       # +env vars NEXT_PUBLIC_* al build-apps job
                                       # +dashboard al verify-deploy matrix
ci.yml                                 # +dashboard al filter del build step
```

### `.claude/docs/subdomain-standard/`

```
02-naming-rules.md                     # +'admin' a la lista de reservados
```

### `tests/feature/`

```
dashboard/
├── 01-login-magic-link.spec.ts
├── 02-register-verify-code.spec.ts
├── 03-callback-fragment-hash.spec.ts
├── 04-auth-guard-redirect.spec.ts
├── 05-logout-multi-tab.spec.ts
├── 06-analytics-navigation.spec.ts
└── 07-sessions-table-pagination.spec.ts
```

## Conteo de archivos

| Tipo | Cantidad |
|------|----------|
| Configs raiz (dashboard/) | 9 |
| `src/lib/` | 8 |
| `src/types/` | 3 |
| `src/providers/` | 3 |
| `src/hooks/` (globales) | 4 |
| `src/styles/` | 1 |
| `src/components/ui/` (shadcn) | 24 |
| `src/components/ui/` (custom) | 7 |
| `src/features/auth/` | ~25 |
| `src/features/dashboard-shell/` | 4 |
| `src/features/analytics/` | ~17 |
| `src/features/sessions/` | ~10 |
| `src/features/events/` | ~10 |
| `src/features/visits/` | ~6 |
| `src/features/geo/` | ~4 |
| `src/features/devices/` | ~7 |
| `src/features/funnel/` | ~4 |
| `src/features/contacts/` | ~11 |
| `src/features/settings/` | ~10 |
| `src/app/` (pages + layouts) | ~17 |
| `tests/` (mocks + fixtures + unit) | ~50 |
| `tests/feature/dashboard/` (Playwright) | 7 |
| Cambios fuera de `dashboard/` | ~7 |

**Total estimado**: ~250 archivos nuevos + ~7 modificados. Plan **Large**.

[< 02-diagramas](02-diagramas.md) | [Siguiente: 04-setup-base >](04-setup-base.md)
