# 02 — Estructura: Hybrid Atomic Design

[< 01-stack](01-stack.md) | [Siguiente: 03-ui >](03-ui.md)

## Filosofia

Atomic Design clasico (atoms/molecules/organisms/templates/pages) genera
debate sin valor para dashboards: ¿`MetricCard` es molecule u organism?
¿el form de login es organism o template?

**Decision**: estructura **hibrida** inspirada en shadcn + Feature-Sliced
Design.

- **`src/components/ui/`** — componentes **genericos** (sin conocimiento
  de dominio). Equivalente a atoms+molecules sin distinguir. Lo que
  agrega `pnpm dlx shadcn add <X>`.
- **`src/features/<feature>/components/`** — componentes **especificos**
  por dominio. Equivalente a organisms+templates. Composen los `ui/`
  primitives + acceden a hooks/api de la feature.
- **`src/app/`** — Pages (Next App Router). Solo composicion final +
  layout.

## Decision tree: donde vive un componente?

```
┌─ Es generico (sin conocimiento de dominio)?
│  ├─ SI → src/components/ui/
│  └─ NO
│     ├─ Usa hooks/api/store de UNA feature?
│     │  ├─ SI → src/features/<X>/components/
│     │  └─ NO → src/components/ui/ (es generico, abstraerlo)
│     └─ Lo usan 2+ features?
│        ├─ SI → promote a src/components/ui/ (genericalo)
│        └─ NO → quedate en src/features/<X>/components/
└─
```

Ejemplos resueltos:

| Componente | Donde | Por que |
|-----------|-------|---------|
| `<Button>` | `ui/` | shadcn primitive, sin dominio |
| `<Card>` | `ui/` | shadcn primitive |
| `<Form>`, `<FormField>` | `ui/` | shadcn primitives |
| `<MetricCard title value delta>` | `ui/` | Generico, lo puede usar cualquier feature |
| `<AnalyticsOverviewCards>` | `features/analytics/components/` | Wrappea 4 `<MetricCard>` con `useOverviewQuery` |
| `<LoginForm>` | `features/auth/components/` | Usa `useLogin` (Tanstack mutation) |
| `<SessionsTable>` | `features/sessions/components/` | Usa `useSessionsQuery` + columns especificas |
| `<DataTable>` (Tanstack wrapper generico) | `ui/` | Lo usan sessions, events, contacts |
| `<DateRangePicker>` | `ui/` | Lo usan analytics, sessions, events |
| `<ThemeToggle>` | `ui/` | Solo lee/escribe `next-themes`, sin dominio |
| `<AuthGuard>` | `features/auth/components/` | Logica especifica de auth |
| `<Sidebar>` (del app shell) | `features/admin-shell/components/` o `app/(admin)/_components/` | Especifico del app shell del admin |

## Cuando promover de `features/` a `ui/`?

Reglas:

1. **Dos features lo usan** (no una). Premature abstraction es peor que
   duplicar.
2. **Sin dependencia a una feature especifica** (sin imports de
   `@/features/<X>/...`).
3. **API estable**: props bien definidas, sin "todo lo de analytics".

Si el componente parece generico pero importa un hook de Tanstack Query
de una feature, NO lo promuevas. Refactoriza: el componente generico
recibe `data` por prop, la feature le pasa lo que vino del hook.

```typescript
// MAL (acopla MetricCard a analytics)
// src/components/ui/metric-card.tsx
import {useOverviewQuery} from '@/features/analytics/hooks/use-overview-query'

export function MetricCard({metric}: {metric: 'sessions' | 'visits'}) {
  const {data} = useOverviewQuery()
  return <div>{data?.[metric]}</div>
}

// BIEN (MetricCard generico)
// src/components/ui/metric-card.tsx
export function MetricCard({title, value, delta}: {title: string; value: string; delta?: number}) {
  return <div>...</div>
}

// src/features/analytics/components/analytics-overview-cards.tsx
import {MetricCard} from '@/components/ui/metric-card'
import {useOverviewQuery} from '../hooks/use-overview-query'

export function AnalyticsOverviewCards() {
  const {data} = useOverviewQuery()
  return (
    <>
      <MetricCard title="Sessions" value={String(data?.sessions ?? 0)} delta={data?.sessions_delta} />
      <MetricCard title="Visits" value={String(data?.visits ?? 0)} delta={data?.visits_delta} />
    </>
  )
}
```

## Estructura completa de `admin/src/`

> **Scope.** Este arbol es el del plan `a-admin`: app shell + auth +
> gestion total (settings, sessions-mgmt, users-admin). Las features y
> rutas de METRICAS (`analytics`, `sessions` de tracking, `events`,
> `visits`, `geo`, `devices`, `funnel`, `contacts`) NO se implementan
> aca: se montan dentro del MISMO app shell en el plan `b-analytics-api`
> (ver la nota al final del arbol). El sidebar deja slots/links a esas
> secciones desde a-admin, pero las pantallas llegan con b-analytics-api.

```
admin/
├── src/
│   ├── app/                                    # Next App Router (output: 'export')
│   │   ├── layout.tsx                          # RootLayout: providers, fonts, theme
│   │   ├── page.tsx                            # / → redirect a /login o al app shell
│   │   ├── error.tsx                           # error boundary global
│   │   ├── global-error.tsx                    # fallback ultimo
│   │   ├── not-found.tsx                       # 404
│   │   │
│   │   ├── (auth)/                             # Route group, sin layout compartido
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── verify/page.tsx                 # input de code o magic-link prompt
│   │   │   ├── callback/page.tsx               # decodifica fragment del magic-link
│   │   │   └── set-password/page.tsx
│   │   │
│   │   └── (admin)/                            # Route group, layout protegido (app shell)
│   │       ├── layout.tsx                      # AuthGuard + Sidebar + Header
│   │       ├── page.tsx                        # / del area protegida (landing del shell)
│   │       ├── settings/
│   │       │   ├── page.tsx                    # profile (display_name, change-email, delete)
│   │       │   └── security/page.tsx           # MFA + WebAuthn + recovery + change-password
│   │       ├── sessions-mgmt/page.tsx          # mis sesiones activas (auth) + revocar
│   │       ├── users-admin/                    # gestion de OTROS users (solo admin)
│   │       │   ├── page.tsx                    # list-users
│   │       │   └── [id]/page.tsx               # get-user + acciones admin
│   │       ├── cv/page.tsx                     # placeholder gestion CV (plan futuro c-cv-management)
│   │       │
│   │       # Rutas de METRICAS (plan b-analytics-api, NO en a-admin):
│   │       #   /metrics (overview) + /analytics + /sessions (tracking) +
│   │       #   /events + /visits + /geo + /devices + /funnel + /contacts
│   │
│   ├── components/
│   │   └── ui/                                 # shadcn primitives (copy-paste)
│   │       ├── alert.tsx
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── chart.tsx                       # Recharts wrapper de shadcn
│   │       ├── checkbox.tsx
│   │       ├── dialog.tsx
│   │       ├── dropdown-menu.tsx
│   │       ├── form.tsx
│   │       ├── input.tsx
│   │       ├── input-otp.tsx                   # para code 8 chars
│   │       ├── label.tsx
│   │       ├── popover.tsx
│   │       ├── select.tsx
│   │       ├── separator.tsx
│   │       ├── sheet.tsx                       # mobile sidebar
│   │       ├── skeleton.tsx
│   │       ├── sonner.tsx                      # Toaster wrapper
│   │       ├── switch.tsx
│   │       ├── table.tsx
│   │       ├── tabs.tsx
│   │       ├── tooltip.tsx
│   │       │
│   │       # Genericos custom (no shadcn, pero candidatos a promote)
│   │       ├── metric-card.tsx                 # title/value/delta/icon
│   │       ├── date-range-picker.tsx           # Popover + Calendar
│   │       ├── data-table.tsx                  # wrapper Tanstack Table + paginator
│   │       ├── empty-state.tsx                 # icon + title + description + action
│   │       ├── theme-toggle.tsx                # next-themes ciclo dark/light/system
│   │       ├── error-alert.tsx
│   │       └── loading-spinner.tsx
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── login-form.tsx              # email + (opcional) password + Turnstile
│   │   │   │   ├── register-form.tsx           # email + Turnstile
│   │   │   │   ├── verify-code-input.tsx       # InputOTP 8 chars
│   │   │   │   ├── magic-link-prompt.tsx       # "te enviamos un link..."
│   │   │   │   ├── set-password-form.tsx
│   │   │   │   ├── totp-setup.tsx              # QR (otpauth_url) + InputOTP 6 digitos
│   │   │   │   ├── recovery-codes-modal.tsx    # download + copy
│   │   │   │   ├── webauthn-register-button.tsx
│   │   │   │   ├── auth-guard.tsx              # HOC/Component para proteger rutas
│   │   │   │   └── turnstile-widget.tsx        # wrapper @marsidev/react-turnstile
│   │   │   ├── hooks/
│   │   │   │   ├── use-register-start.ts       # useMutation
│   │   │   │   ├── use-verify-code.ts
│   │   │   │   ├── use-login-start.ts
│   │   │   │   ├── use-logout.ts
│   │   │   │   ├── use-session-refresh.ts
│   │   │   │   ├── use-auth-timer.ts           # auto-refresh proactivo + Page Visibility
│   │   │   │   ├── use-multi-tab-sync.ts       # BroadcastChannel
│   │   │   │   └── use-protected-route.ts
│   │   │   ├── api/
│   │   │   │   ├── auth-client.ts              # endpoints typed
│   │   │   │   └── query-keys.ts
│   │   │   ├── store/
│   │   │   │   └── use-auth-store.ts           # Zustand: accessToken (mem), user, status
│   │   │   ├── lib/
│   │   │   │   ├── refresh-mutex.ts            # mutex para concurrent 401s
│   │   │   │   ├── broadcast.ts                # BroadcastChannel helpers
│   │   │   │   └── token-expiry.ts             # jwt-decode + timing
│   │   │   ├── types.ts                        # User, AuthResponse, Method, MfaMethod
│   │   │   └── index.ts                        # barrel
│   │   │
│   │   ├── admin-shell/                        # APP SHELL de las pages protegidas
│   │   │   ├── components/
│   │   │   │   ├── sidebar.tsx                 # nav links + user menu
│   │   │   │   ├── header.tsx                  # breadcrumb, theme toggle, logout
│   │   │   │   └── mobile-sidebar.tsx          # Sheet en mobile
│   │   │   ├── lib/
│   │   │   │   └── nav-items.ts                # links: settings, sessions-mgmt,
│   │   │   │                                   #   users-admin, cv (placeholder) +
│   │   │   │                                   #   slots de metricas (plan b-analytics-api)
│   │   │   └── index.ts
│   │   │
│   │   ├── settings/                           # perfil + seguridad (Lambda auth + users)
│   │   │   ├── components/
│   │   │   │   ├── profile-form.tsx            # display_name (users.profile.update)
│   │   │   │   ├── change-email-form.tsx       # users.profile.change-email + confirm
│   │   │   │   ├── delete-account-section.tsx  # users.profile.delete-account
│   │   │   │   ├── change-password-form.tsx    # BLOQUEADO por dependencia de backend (ver GAP)
│   │   │   │   ├── mfa-methods-list.tsx        # totp, email-code (auth.mfa)
│   │   │   │   ├── totp-setup.tsx              # auth.mfa setup/confirm
│   │   │   │   ├── webauthn-credentials-list.tsx  # auth.webauthn register/list/delete
│   │   │   │   └── recovery-codes-section.tsx  # auth.mfa recovery-codes-generate
│   │   │   ├── hooks/, api/, types.ts, index.ts
│   │   │
│   │   ├── sessions-mgmt/                      # MIS sesiones de auth (NO tracking)
│   │   │   ├── components/
│   │   │   │   ├── my-sessions-table.tsx       # users.status.list-sessions + get
│   │   │   │   └── revoke-session-button.tsx   # users.status.revoke-session
│   │   │   ├── hooks/, api/, types.ts, index.ts
│   │   │
│   │   └── users-admin/                        # gestion de OTROS users (solo admin)
│   │       ├── components/
│   │       │   ├── users-table.tsx             # users.admin.list-users
│   │       │   ├── user-detail-dialog.tsx      # users.admin.get-user
│   │       │   ├── user-status-actions.tsx     # disable/enable/delete/force-logout
│   │       │   └── admin-actions-log.tsx       # users.admin.list-admin-actions
│   │       ├── hooks/, api/, types.ts, index.ts
│   │
│   │   # Features de METRICAS (analytics, sessions de tracking, events,
│   │   #   visits, geo, devices, funnel, contacts): plan b-analytics-api,
│   │   #   consumen el Lambda analytics. NO se crean en a-admin.
│   │
│   ├── lib/
│   │   ├── api-client.ts                       # fetch wrapper (JWT + mutex refresh)
│   │   ├── utils.ts                            # cn(), formatters helpers
│   │   ├── env.ts                              # validate NEXT_PUBLIC_* con Zod
│   │   ├── routes.ts                           # ROUTES.admin.settings, etc.
│   │   ├── format/
│   │   │   ├── date.ts                         # formatDate, relativeTime
│   │   │   ├── number.ts                       # formatNumber, formatPercent
│   │   │   └── duration.ts                     # formatDurationMs
│   │   └── validation/                         # Zod schemas compartidos
│   │       ├── auth.ts                         # loginSchema, registerSchema
│   │       └── filters.ts                      # dateRangeSchema, paginationSchema
│   │
│   ├── hooks/                                  # globales (no de feature)
│   │   ├── use-debounce.ts
│   │   ├── use-media-query.ts
│   │   ├── use-local-storage.ts                # type-safe wrapper
│   │   └── use-mounted.ts                      # para evitar hydration warnings
│   │
│   ├── providers/
│   │   ├── theme-provider.tsx                  # next-themes
│   │   ├── query-provider.tsx                  # Tanstack Query + persister
│   │   └── root-providers.tsx                  # composicion
│   │
│   ├── styles/
│   │   ├── globals.css                         # tailwind + tokens + base
│   │   └── (opcional) animations.css
│   │
│   ├── types/
│   │   ├── api.ts                              # types de responses /auth y /analytics
│   │   └── models.ts                           # User, Session, Event, Contact (domain)
│   │
│   └── env.d.ts                                # type-safe NEXT_PUBLIC_*
│
├── public/
│   ├── _redirects                              # /* /index.html 200
│   ├── _headers                                # CSP + HSTS + cache
│   ├── favicon.ico
│   └── og-image.png
│
├── tests/
│   ├── unit/                                   # mirror de src/
│   │   ├── lib/
│   │   ├── components/ui/
│   │   └── features/
│   │       ├── auth/
│   │       └── analytics/
│   ├── mocks/                                  # MSW handlers + server
│   │   ├── handlers/
│   │   │   ├── auth.ts
│   │   │   └── analytics.ts
│   │   ├── server.ts                           # setupServer (Node)
│   │   └── browser.ts                          # setupWorker (browser dev)
│   ├── fixtures/                               # data sintetica
│   │   ├── users.ts
│   │   ├── sessions.ts
│   │   ├── events.ts
│   │   └── analytics.ts
│   └── setup.ts                                # vitest setup
│
├── components.json                             # shadcn config
├── next.config.ts
├── tsconfig.json
├── biome.json                                  # override del root
├── postcss.config.mjs
├── vitest.config.ts
├── package.json
└── README.md
```

## Reglas de imports entre carpetas

| Direccion | Permitido? | Notas |
|-----------|-----------|-------|
| `src/app/` → `src/components/ui/` | ✅ | OK |
| `src/app/` → `src/features/<X>/` | ✅ | OK (las pages componen features) |
| `src/app/` → `src/lib/` | ✅ | OK |
| `src/features/A/` → `src/features/B/` | ❌ | Forbidden. Si necesitas compartir, promove a `lib/` o `components/ui/` |
| `src/features/<X>/` → `src/components/ui/` | ✅ | OK (features consumen genericos) |
| `src/features/<X>/` → `src/lib/` | ✅ | OK |
| `src/features/<X>/` → `src/hooks/` | ✅ | OK (hooks globales) |
| `src/components/ui/` → `src/features/<X>/` | ❌ | Forbidden. Romperia la abstraccion |
| `src/components/ui/` → `src/lib/` | ✅ | Solo a `utils.ts`, `format/*`. No a `api-client.ts` |
| `src/lib/` → `src/features/<X>/` | ❌ | Forbidden |
| `src/hooks/` → `src/features/<X>/` | ❌ | Forbidden |

## Naming conventions

- **Files**: `kebab-case.tsx` (sigue convencion shadcn: `metric-card.tsx`, no `MetricCard.tsx`)
- **Components**: `PascalCase` (export const MetricCard)
- **Hooks**: `use<Name>` en camelCase, archivo `use-<name>.ts`
- **Types/Interfaces**: `PascalCase` (export type User, export interface ApiResponse)
- **Constants**: `UPPER_SNAKE` (export const MAX_PAGE_SIZE = 200)
- **Zod schemas**: `<name>Schema` y type inferido `<Name>`:
  ```typescript
  export const loginSchema = z.object({...})
  export type Login = z.infer<typeof loginSchema>
  ```
- **Stores Zustand**: `use<Name>Store` (`useAuthStore`, `useAnalyticsFiltersStore`)

## Barrel exports (`index.ts` por feature)

Cada feature exporta un publico via `index.ts`:

```typescript
// src/features/auth/index.ts
export {LoginForm} from './components/login-form'
export {RegisterForm} from './components/register-form'
export {AuthGuard} from './components/auth-guard'
export {useAuthStore} from './store/use-auth-store'
export {useLogin, useRegister, useLogout, useSessionRefresh} from './hooks'
export type {User, AuthResponse} from './types'
```

NO exportar lo "interno" (lib helpers, hooks privados). Mantener la
superficie publica chica para reducir acoplamiento.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `src/components/atoms/`, `molecules/`, `organisms/` | Atomic Design clasico genera debates | Hybrid: `ui/` + `features/<X>/components/` |
| Crear `<PrimaryButton>` wrappeando `<Button variant="primary">` | Sin valor | `<Button variant="primary">` directo |
| Importar `features/B` desde `features/A` | Cross-feature coupling | Mover lo compartido a `lib/` o `ui/` |
| Hook `useAnalyticsQuery` en `src/hooks/` | Feature-specific, no global | `src/features/analytics/hooks/` |
| Premature promote a `ui/` con 1 use case | Premature abstraction | Quedate en `features/<X>/` hasta 2+ uses |
| `MetricCard` que llama `useOverviewQuery` | Acopla generic a especifico | Recibe `data` por prop |
| `default export` en componentes (excepto pages/layouts) | Reduce auto-rename, mas verbose en imports | `export const Component = ...` |
| `index.ts` con `export *` | Dificulta tree-shaking + crea ciclos | Export explicito |

[< 01-stack](01-stack.md) | [Siguiente: 03-ui >](03-ui.md)
