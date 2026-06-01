# 07 — Dashboard features (analytics, sessions, events, ...)

[< 06-auth-feature](06-auth-feature.md) | [Siguiente: 08-descomposicion >](08-descomposicion.md)

## Aclaracion

Las fases 10-16 implementan las features del dashboard. Cada feature
sigue el patron Hybrid Atomic Design: `components/`, `hooks/`, `api/`,
`store/` (si aplica), `types.ts`, `index.ts`. Tests con coverage >= 80%
per-file.

## Fase 10 — Feature `dashboard-shell/` + layout protegido

### `src/features/dashboard-shell/components/sidebar.tsx`

Sidebar con links a cada feature. Usa `lucide-react` icons. Mobile via
shadcn `Sheet`.

```tsx
'use client'

import Link from 'next/link'
import {usePathname} from 'next/navigation'
import {BarChart3, Users, MousePointer, MapPin, Smartphone, GitBranch, MessageSquare, Settings, Home} from 'lucide-react'
import {cn} from '@/lib/utils'

const navItems = [
  {href: '/dashboard', label: 'Overview', icon: Home},
  {href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3},
  {href: '/dashboard/sessions', label: 'Sessions', icon: Users},
  {href: '/dashboard/events', label: 'Events', icon: MousePointer},
  {href: '/dashboard/visits', label: 'Visits', icon: Home},
  {href: '/dashboard/geo', label: 'Geo', icon: MapPin},
  {href: '/dashboard/devices', label: 'Devices', icon: Smartphone},
  {href: '/dashboard/funnel', label: 'Funnel', icon: GitBranch},
  {href: '/dashboard/contacts', label: 'Contacts', icon: MessageSquare},
  {href: '/dashboard/settings', label: 'Settings', icon: Settings},
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="hidden h-screen w-60 border-r bg-card lg:flex lg:flex-col">
      <div className="p-6">
        <h2 className="font-mono text-sm uppercase tracking-widest text-muted-foreground">Admin</h2>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map(({href, label, icon: Icon}) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
```

### `src/features/dashboard-shell/components/header.tsx`

Header con breadcrumb dinamico + ThemeToggle + UserMenu (dropdown con
logout).

### `src/features/dashboard-shell/components/mobile-sidebar.tsx`

Sheet de shadcn para mobile (renderiza el mismo `Sidebar` pero dentro
de un Sheet trigger).

### `src/app/(dashboard)/layout.tsx`

```tsx
'use client'

import type {ReactNode} from 'react'
import {AuthGuard} from '@/features/auth/components/auth-guard'
import {Sidebar} from '@/features/dashboard-shell/components/sidebar'
import {Header} from '@/features/dashboard-shell/components/header'

export default function DashboardLayout({children}: {children: ReactNode}) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <Header />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  )
}
```

**Commit**: `feat(dashboard,shell): Sidebar + Header + MobileSidebar + (dashboard)/layout protegido`

## Fases 11-15 — Nota de seguridad sobre el backend `/analytics`

> **GAP CONOCIDO** — el plan `docs/specs/analytics-dashboard-api/`
> (Decision 1) declara explicitamente que el Lambda `analytics` NO
> valida el JWT en su primera entrega: solo aplica rate-limit por IP.
> El dashboard manda `Authorization: Bearer <accessToken>` en todos
> los requests a `/analytics` (consistencia con el resto del API y
> compatibilidad forward cuando el plan agregue auth), pero el backend
> lo ignora hasta que se mergee la fase posterior del plan analytics.
>
> Implicacion: cualquier cliente que conozca el endpoint puede leer la
> data analitica del portfolio (sessions, visits, geo, devices,
> events, contacts) sin auth.
>
> **Bloqueante para merge a `main`**: si los datos de la feature
> `contacts/` (Fase 15) incluyen PII real (email del visitante,
> mensaje), el cutover a prod del dashboard DEBE esperar a que la fase
> de auth del plan analytics-dashboard-api este mergeada. Mientras
> tanto, prod queda capada al subset publico-safe (analytics
> agregadas, no contacts).
>
> No requiere cambios en el codigo del dashboard mas alla de mandar el
> Bearer; cuando el backend habilite la validacion, el flujo ya esta
> listo y no cambia el contrato cliente.

## Fase 11 — Feature `analytics/` (7 endpoints)

Hooks (Tanstack Query):

| Hook | Endpoint | Key | staleTime |
|------|----------|-----|-----------|
| `useOverviewQuery` | `analytics.overview` | `['analytics', 'overview', range]` | 60_000 |
| `useTimeseriesQuery` | `analytics.timeseries` | `['analytics', 'timeseries', {range, bucket, niche, event_type}]` | 60_000 |
| `useTopPagesQuery` | `analytics.top-pages` | `['analytics', 'top-pages', {range, limit, niche}]` | 60_000 |
| `useTopReferrersQuery` | `analytics.top-referrers` | `['analytics', 'top-referrers', {range, limit}]` | 60_000 |
| `useTopNichesQuery` | `analytics.top-niches` | `['analytics', 'top-niches', range]` | 60_000 |
| `useActiveNowQuery` | `analytics.active-now` | `['analytics', 'active-now']` | 10_000 + refetchInterval: 15_000 |
| `useRetentionQuery` | `analytics.retention` | `['analytics', 'retention', range]` | 60_000 |

Componentes:
- `OverviewCards` (7 MetricCards) — usa `useOverviewQuery`
- `TimeseriesChart` (Recharts AreaChart)
- `TopPagesChart` (BarChart horizontal)
- `TopReferrersTable` (DataTable)
- `TopNichesChart` (BarChart)
- `ActiveNowCard` (live count + last sessions list)
- `RetentionChart` (BarChart new vs returning)
- `AnalyticsFilters` (DateRangePicker + niche Select + event_type Select)

Store (Zustand local):
- `useAnalyticsFiltersStore`: `dateRange: {from, to}`, `niche: string | null`, `eventType: string | null`. Persist en sessionStorage (no localStorage — filtros son ephimeros).

Pages:
- `src/app/(dashboard)/page.tsx`: solo `OverviewCards`.
- `src/app/(dashboard)/analytics/page.tsx`: AnalyticsFilters + OverviewCards + TimeseriesChart + grid de Top* + ActiveNow + Retention.

**Tests**: cada hook y componente con BDD-style.

**Commit**: `feat(dashboard,analytics): 7 hooks + componentes (Overview, Timeseries, TopPages, TopReferrers, TopNiches, ActiveNow, Retention) + filters store`

## Fase 12 — Feature `sessions/` (2 endpoints)

| Hook | Endpoint | Key | staleTime |
|------|----------|-----|-----------|
| `useSessionsList` | `sessions.list` | `['sessions', 'list', {page, page_size, range, country, device}]` | 30_000 |
| `useSessionDetail` | `sessions.detail` | `['sessions', 'detail', sessionId]` | 0 (siempre fresh) |

Componentes:
- `SessionsTable` (DataTable con columnas: session_id, first_seen_at, country, device_type, event_count, action)
- `SessionDetailDrawer` (shadcn Sheet lateral right con info de session + lista de visits + event_count; abre desde la fila + URL search param `?session=<id>` para deep-link sin ruta dinamica)
- `SessionsFilters` (DateRangePicker + country/device Select)

Pages:
- `src/app/(dashboard)/sessions/page.tsx`: SessionsFilters + SessionsTable + SessionDetailDrawer. El drawer lee `?session=<id>` (via `useSearchParams`, dentro de Suspense boundary). Clickear una fila ejecuta `router.push('/sessions/?session=<id>', {scroll: false})`. Cerrar el drawer hace `router.push('/sessions/')`.

> Decision: NO usar ruta dinamica `sessions/[id]/page.tsx`. Next 16 con
> `output: 'export'` rechaza rutas dinamicas sin `generateStaticParams()`
> (build fail fatal). Como las sessions son data-driven (no pre-renderizables
> a build time), el detalle vive en un drawer lateral con deep-link via
> query param. Patron consistente con el resto del dashboard (SPA puro,
> sin rutas dinamicas estaticas).

**Commit**: `feat(dashboard,sessions): hooks list + detail + tabla + dialog detail`

## Fase 13 — Feature `events/` (3 endpoints)

| Hook | Endpoint | staleTime |
|------|----------|-----------|
| `useEventsDistribution` | `events.distribution` | 60_000 |
| `useEventsList` | `events.list` | 30_000 |
| `useEventsHeatmap` | `events.heatmap` | 60_000 |

Componentes:
- `EventsDistributionChart` (Recharts BarChart con event_type + count + share)
- `EventsListTable` con **Tanstack Virtual** (lista 500+ rows)
- `EventsHeatmap` (grid 7x24 dia_semana x hora, intensidad por color)

Page: `src/app/(dashboard)/events/page.tsx` (Tabs con 3 vistas)

**Commit**: `feat(dashboard,events): distribution + list virtualizada + heatmap`

## Fase 14 — Features `visits/`, `geo/`, `devices/`, `funnel/`

### `visits/` (2 endpoints)
- `useVisitsList`, `useVisitsLandingPages`
- `VisitsListTable`, `LandingPagesChart`
- Page `visits/page.tsx`

### `geo/` (1 endpoint)
- `useGeoByCountry`
- `GeoByCountryChart` (BarChart top 10 countries)
- Page `geo/page.tsx`

### `devices/` (1 endpoint que devuelve 3 breakdowns)
- `useDevicesBreakdown`
- `DevicePieChart`, `BrowserBarChart`, `OsBarChart`
- Page `devices/page.tsx` con 3 charts side-by-side

### `funnel/` (1 endpoint)
- `useFunnelConversion`
- `FunnelChart` (sessions → visits → contacts con conversion rate %)
- Page `funnel/page.tsx`

**Commit**: `feat(dashboard,visits-geo-devices-funnel): 4 features con 5 endpoints`

## Fase 15 — Feature `contacts/` (3 endpoints + mutation)

| Hook | Tipo | Endpoint |
|------|------|----------|
| `useContactsList` | `useQuery` | `contacts.list` |
| `useContactsByStatus` | `useQuery` | `contacts.by-status` |
| `useUpdateContactStatus` | `useMutation` | (POST custom action, ej. `contacts.update-status` — depende del backend) |

Componentes:
- `ContactsTable` (DataTable con columnas: created_at, email, message preview, status badge, action)
- `ContactsByStatusChart` (BarChart conteo por status)
- `ContactDetailDialog` (Dialog con full message + metadata)
- `UpdateStatusButton` (Select con statuses: new → contacted → qualified → converted | rejected. onSelect dispara mutation + invalidates list)

Page: `src/app/(dashboard)/contacts/page.tsx`.

**Tests**: critico el mutation (verifica optimistic update + invalidation).

**Commit**: `feat(dashboard,contacts): list + by-status + detail dialog + mutation update-status`

## Fase 16 — Feature `settings/` (profile + MFA setup)

Componentes:
- `ProfileForm` (email read-only, display_name editable)
- `ChangePasswordForm` (current + new + confirm con Zod refine)
- `MfaMethodsList` (Card por metodo: TOTP, WebAuthn, Email-code. Cada uno con botones Enable/Disable/SetPreferred)
- `WebAuthnCredentialsList` (lista de credentials registradas con nickname + last_used_at + boton Delete)
- `RecoveryCodesSection` (boton "Generate" → modal con 10 codes + download/copy)

Pages:
- `src/app/(dashboard)/settings/page.tsx`: Tabs con Profile + Security
- `src/app/(dashboard)/settings/security/page.tsx`: MfaMethodsList + WebAuthnCredentialsList + RecoveryCodesSection

**Notas**:

- Las acciones MFA (TOTP setup, WebAuthn registration) son del plan 02.
  Mientras `02-auth-mfa` no este mergeado, MSW provee mocks O el flag
  `NEXT_PUBLIC_FEATURE_MFA=false` esconde las pages de MFA. El flag esta
  declarado en el catalogo de `sync_secrets` (commit 23) con valor `false`
  por env en dev/stage/prod hasta el cutover.
- WebAuthn requiere `NEXT_PUBLIC_WEBAUTHN_RP_ID` (hostname del dashboard
  per env: `admin.portfolio.dev.the-full-stack.com`,
  `admin.portfolio.stage.the-full-stack.com`,
  `admin.portfolio.the-full-stack.com`). Se pasa a `navigator.credentials.create({publicKey: {rp: {id}}})`.
  Sin esta var, el browser rechaza el flujo con `SecurityError`. Declarada
  en el catalogo de `sync_secrets` junto con `NEXT_PUBLIC_FEATURE_MFA`.

**Commit**: `feat(dashboard,settings): profile + change-password + MFA management + recovery codes`

## Verificacion al final de fase 16 (gate intermedio)

```bash
# Tests de TODAS las features
pnpm --filter @portfolio/dashboard test:coverage

# Build OK
pnpm --filter @portfolio/dashboard build
ls dashboard/out/

# Preview con MSW: navegar manualmente
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/dashboard dev &
# Visitar:
# - http://localhost:3000/login
# - flow completo login → /dashboard
# - navegar a /dashboard/analytics
# - cambiar DateRangePicker
# - navegar a /dashboard/sessions
# - clickear una row → ver detail dialog
# - navegar a /dashboard/events → verificar virtualizacion
# - logout → /login
```

Si todo verde, proceder con fases 17-19 (deploy infrastructure) y 20-21
(E2E + cleanup).

[< 06-auth-feature](06-auth-feature.md) | [Siguiente: 08-descomposicion >](08-descomposicion.md)
