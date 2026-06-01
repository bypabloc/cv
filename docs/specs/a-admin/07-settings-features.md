# 07 — App shell + features de gestion (settings, sessions, users-admin)

[< 06-auth-feature](06-auth-feature.md) | [Siguiente: 08-descomposicion >](08-descomposicion.md)

## Aclaracion

Las fases 10-14 implementan el app shell del admin + las features de
gestion de la cuenta y de usuarios. Cada feature sigue el patron Hybrid
Atomic Design: `components/`, `hooks/`, `api/`, `store/` (si aplica),
`types.ts`, `index.ts`. Tests con coverage >= 80% per-file.

> La UI de metricas (analytics, sessions de tracking, events, visits,
> geo, devices, funnel, contacts) NO vive en este plan: vive en el plan
> `docs/specs/b-analytics-api/` y se monta dentro del app shell descrito
> en la Fase 10 (ver "Slot Metricas" mas abajo). El plan a-admin solo
> entrega el shell + las features de gestion.

## Fase 10 — Feature `admin-shell/` + layout protegido

El app shell (sidebar + header + layout) es el contenedor de todas las
pantallas del admin. Provee navegacion, sesion y el slot donde el plan
`b-analytics-api` monta las pantallas de metricas.

### `src/features/admin-shell/components/sidebar.tsx`

Sidebar con links a las secciones de gestion + un slot "Metricas" cuyos
links resuelven a pantallas que aporta el plan `b-analytics-api`. Usa
`lucide-react` icons. Mobile via shadcn `Sheet`.

```tsx
'use client'

import Link from 'next/link'
import {usePathname} from 'next/navigation'
import {BarChart3, Settings, Users, Monitor, FileText} from 'lucide-react'
import {cn} from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: typeof BarChart3
}

// Links de gestion (este plan). El slot Metricas (/metrics) lo aporta
// el plan b-analytics-api: el link existe en el shell, la pantalla no.
const navItems: readonly NavItem[] = [
  {href: '/metrics', label: 'Metricas', icon: BarChart3},
  {href: '/settings', label: 'Configuracion', icon: Settings},
  {href: '/sessions', label: 'Mis sesiones', icon: Monitor},
  {href: '/users', label: 'Usuarios', icon: Users},
  {href: '/cv', label: 'Gestion CV', icon: FileText},
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="hidden h-screen w-60 border-r bg-card lg:flex lg:flex-col">
      <div className="p-6">
        <h2 className="font-mono text-sm uppercase tracking-widest text-muted-foreground">
          Admin
        </h2>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map(({href, label, icon: Icon}) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              pathname === href || pathname.startsWith(`${href}/`)
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

> **Slot Metricas**: el link `/metrics` apunta a la raiz del area de
> metricas. Las pantallas (`/metrics`, `/analytics`, `/sessions` de
> tracking, `/events`, `/visits`, `/geo`, `/devices`, `/funnel`,
> `/contacts`) las implementa el plan `b-analytics-api` montandolas en
> este shell. En este plan el link existe pero su page es el placeholder
> que entrega b-analytics-api; el shell no asume su contenido. NUNCA usar
> `/dashboard` como ruta de metricas.
>
> **Ojo con la colision de nombres**: `/sessions` del sidebar es
> `sessions-mgmt` (las sesiones de MI cuenta auth — Fase 12 de ESTE
> plan). La feature `sessions` de METRICAS (tracking de visitantes) es
> del plan b-analytics-api y cuelga del slot Metricas. Son cosas
> distintas; no mezclar.

### `src/features/admin-shell/components/header.tsx`

Header con breadcrumb dinamico + ThemeToggle + UserMenu (dropdown con
link a `/settings` + logout).

### `src/features/admin-shell/components/mobile-sidebar.tsx`

Sheet de shadcn para mobile (renderiza el mismo `Sidebar` pero dentro
de un Sheet trigger).

### `src/app/(admin)/layout.tsx`

```tsx
'use client'

import type {ReactNode} from 'react'
import {AuthGuard} from '@/features/auth/components/auth-guard'
import {Sidebar} from '@/features/admin-shell/components/sidebar'
import {Header} from '@/features/admin-shell/components/header'

export default function AdminLayout({children}: {children: ReactNode}) {
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

**Tests**: `Sidebar` resalta el item activo segun `pathname` (assert
exacto de la clase `bg-accent` en el item que matchea); `AdminLayout`
envuelve children con `AuthGuard`.

**Commit**: `feat(admin,shell): Sidebar + Header + MobileSidebar + (admin)/layout protegido`

## Fase 11 — Feature `settings/` (perfil + seguridad + cuenta)

Gestion total de la cuenta del user autenticado. Consume el Lambda
`auth` (operations `mfa` + `webauthn`) y el Lambda `users` (operation
`profile`), ambos ya desplegados (dev/stage/prod).

> Fuente de verdad de payloads y responses: el codigo desplegado
> `serverless/lambda/services/auth/` + `serverless/lambda/services/users/`,
> mas las reglas en
> [.claude/rules/auth-system.md](../../../.claude/rules/auth-system.md) y la
> doc en [.claude/docs/auth-system/](../../../.claude/docs/auth-system/).

### `src/features/settings/types.ts`

Tipos derivados del Lambda `users` (operation `profile`) y del Lambda
`auth`. TypeScript strict, sin `any`.

```typescript
// users.profile.get / users.profile.update
export interface UserProfile {
  user_id: string
  email: string
  display_name: string | null
  status: 'active' | 'pending' | 'disabled' | 'locked'
  created_at: string
}

export interface UpdateProfilePayload {
  display_name: string
}

// users.profile.change-email
export interface ChangeEmailPayload {
  new_email: string
}

export interface ConfirmEmailChangePayload {
  token: string
}

// users.profile.delete-account
export interface DeleteAccountPayload {
  confirm: boolean
}

// users.profile.change-password — DEPENDENCIA DE BACKEND (ver nota abajo)
export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}
```

### `src/features/settings/components/profile-form.tsx`

`ProfileForm`: `email` read-only (de `users.profile.get`), `display_name`
editable. react-hook-form + Zod. Submit -> `users.profile.update`
(`{display_name}`). Invalida `['profile', 'get']`.

### `src/features/settings/components/change-password-form.tsx`

`ChangePasswordForm`: `current_password` + `new_password` + `confirm` con
Zod refine (`new_password.length >= 12`, `new_password === confirm`).

> **GAP DE BACKEND (dependencia documentada)**: el backend NO tiene hoy
> una action para que un user AUTENTICADO cambie su password.
> `auth.verify.set-password` usa el `temp_token` del flujo register/login
> (NO el access JWT) y `users.profile` NO expone `change-password`. Esta
> UI requiere una action NUEVA de backend, sugerida:
> `users.profile.change-password` con `{current_password, new_password}`
> validada con el access JWT. Hasta que exista:
> - La UI se entrega y se testea unit con MSW (mock del endpoint).
> - NO se puede testear E2E real contra el backend.
> - El boton de submit queda detras del flag `NEXT_PUBLIC_FEATURE_CHANGE_PASSWORD`
>   (default `false`) o muestra un aviso "disponible proximamente" hasta
>   que la action exista. Marcar como bloqueada por esta dependencia en
>   `docs/specs/a-admin` (seccion de dependencias) y como pre-requisito
>   de backend.

### `src/features/settings/components/change-email-section.tsx`

`ChangeEmailSection`: dos pasos.

- **Iniciar** (`users.profile.change-email`, `{new_email}`): valida email
  con Zod, dispara el envio de confirmacion. Muestra estado "revisa tu
  correo".
- **Confirmar** (`users.profile.confirm-email-change`, `{token}`): se
  resuelve cuando el user vuelve con el token (input manual o deep-link
  con `?token=<...>` leido via `useSearchParams` dentro de Suspense). En
  exito invalida `['profile', 'get']`.

### `src/features/settings/components/mfa-methods-list.tsx`

`MfaMethodsList`: render de `mfa.list` (`MfaListResponse`: `methods[]` +
`webauthn_count` + `total_mfa`). Una `Card` por metodo MFA (TOTP,
email-code) con badge `is_preferred` + acciones:

- **TOTP setup** (`mfa.setup-totp`): el response (`TotpSetupResponse`:
  `{secret_b32, otpauth_url}`) abre un `Dialog` que renderiza el QR en el
  front desde `otpauth_url` (libreria de QR del bundle, p. ej. `qrcode`;
  el backend NO genera la imagen). El usuario escanea y confirma con
  `mfa.confirm-totp` (`{code}` de 6 digitos via shadcn `InputOTP`
  `maxLength={6}`). Confirmar el PRIMER metodo MFA revoca la familia de
  refresh (AC-27) — el `api-client` re-emite el access tras la respuesta.
- **Email-code setup** (`mfa.setup-email-code`, payload `{}`): activa MFA
  via email-code. Es el primer metodo MFA si no hay otros (misma
  revocacion de familia AC-27).
- **Set preferred** (`mfa.set-preferred`, `{kind: 'totp' | 'email_code'}`):
  marca el metodo preferido.
- **Disable** (`mfa.disable`, `{kind: 'totp' | 'email_code'}`): el backend
  aplica el guard transversal `MUST_KEEP_ONE_MFA_METHOD`. Si la accion
  dejaria `total_mfa === 0`, responde **409**; el front muestra el error
  inline ("debes conservar al menos un metodo MFA") y NO desactiva. El
  componente deshabilita el boton Disable cuando `total_mfa === 1`
  (defensa en profundidad; el backend es la fuente de verdad).

### `src/features/settings/components/recovery-codes-section.tsx`

`RecoveryCodesSection`: boton "Generate" -> `mfa.recovery-codes-generate`
(payload `{}`). El response (`RecoveryCodesResponse`: `{codes: string[]}`,
10 codes de 10 chars Crockford) abre un `Dialog` que los muestra UNA sola
vez, con copy + download (`.txt`). El componente advierte que regenerar
invalida los anteriores. `mfa.recovery-codes-consume` NO se usa en
settings (es del flujo de login con factor fuerte step=2, feature `auth/`).

### `src/features/settings/components/webauthn-credentials-list.tsx`

`WebAuthnCredentialsList`: render de `webauthn.list-credentials`
(`WebauthnCredential[]`: `id`, `nickname`, `last_used_at`, `created_at`).
Acciones:

- **Register** (`webauthn.register-options` -> `webauthn.register-verify`):
  el response de options (`WebauthnRegisterOptionsResponse`:
  `{challenge_id, options}`) se pasa a `startRegistration` de
  `@simplewebauthn/browser`. El `options.rp.id` viene del backend resuelto
  por env (`WEBAUTHN_RP_ID`), consistente con `NEXT_PUBLIC_WEBAUTHN_RP_ID`
  del admin. La respuesta del authenticator se manda a
  `webauthn.register-verify` (`{challenge_id, response, nickname?}`).
  Registrar el PRIMER metodo MFA revoca la familia (AC-27).
- **Delete** (`webauthn.delete-credential`, `{credential_id}`): mismo guard
  `MUST_KEEP_ONE_MFA_METHOD` -> 409 si dejaria `total_mfa === 0`. El front
  muestra el error y deshabilita Delete cuando es el ultimo factor.

`webauthn.login-options` / `webauthn.login-verify` (sin auth) son del
flujo de login (feature `auth/`), no de settings.

### `src/features/settings/components/delete-account-section.tsx`

`DeleteAccountSection`: zona de peligro. Boton "Eliminar mi cuenta" abre
un `AlertDialog` que exige re-tipear el email. Confirmar dispara
`users.profile.delete-account` (`{confirm: true}`): soft-delete +
anonimiza + blacklist de familias. En exito el `api-client` limpia tokens
y redirige a `/login`.

> Si el email del user esta en la whitelist de admins, el backend responde
> **409 `CANNOT_DELETE_ADMIN_ACCOUNT`**; el front muestra el error y no
> redirige.

### Pages

- `src/app/(admin)/settings/page.tsx`: Tabs con Perfil (ProfileForm +
  ChangeEmailSection) + Seguridad (link a `/settings/security`) + Cuenta
  (DeleteAccountSection).
- `src/app/(admin)/settings/security/page.tsx`: `ChangePasswordForm` +
  `MfaMethodsList` + `WebAuthnCredentialsList` + `RecoveryCodesSection`.

**Notas**:

- La gestion MFA + WebAuthn + recovery consume el Lambda `auth` ya
  desplegado (las 14 actions `mfa` 8 + `webauthn` 6). La gestion de perfil
  / email / delete-account consume el Lambda `users` (operation `profile`).
  MSW se usa solo para tests unit y desarrollo offline. La unica parte
  bloqueada por backend es CAMBIO DE PASSWORD (ver gap arriba).
- `NEXT_PUBLIC_WEBAUTHN_RP_ID` es **config base** (no detras de flag): el
  hostname del admin per env (`admin.portfolio.dev.the-full-stack.com`,
  `admin.portfolio.stage.the-full-stack.com`,
  `admin.portfolio.the-full-stack.com`). `@simplewebauthn/browser` lo
  espera coincidiendo con el `rp.id` de las options del backend; un
  mismatch hace que el browser rechace el flujo con `SecurityError`. Un
  passkey NO migra entre envs (esperado). Declarada en el catalogo de
  `sync_secrets`.

**Tests**: cada hook y componente con BDD-style. Critico:
`ChangePasswordForm` (Zod refine de longitud + match, mock MSW del
endpoint pendiente), `MfaMethodsList` (boton Disable deshabilitado con
`total_mfa === 1`, 409 inline), `DeleteAccountSection` (exige re-tipear el
email + maneja 409 admin).

**Commit**: `feat(admin,settings): perfil + change-email + change-password (bloqueado por backend) + MFA + WebAuthn + recovery codes + delete-account`

## Fase 12 — Feature `sessions-mgmt/` (mis sesiones de auth)

Gestion de las sesiones activas de MI cuenta (logins en otros
dispositivos). Consume el Lambda `users` (operation `status`).

> NO confundir con la feature `sessions` de METRICAS (tracking de
> visitantes), que es del plan `b-analytics-api`. Esta feature
> (`sessions-mgmt`) es sobre MI propia sesion auth.

### `src/features/sessions-mgmt/types.ts`

```typescript
// users.status.list-sessions / users.status.get
export interface AccountSession {
  session_id: string
  family_id: string
  ip: string | null
  user_agent: string | null
  created_at: string
  last_seen_at: string | null
  is_current: boolean
}

export interface AccountStatus {
  user_id: string
  status: 'active' | 'pending' | 'disabled' | 'locked'
  current_session_id: string
}

// users.status.revoke-session
export interface RevokeSessionPayload {
  session_id: string
}
```

### Hooks (`src/features/sessions-mgmt/hooks/`)

| Hook | Tipo | Action | Key | staleTime |
|------|------|--------|-----|-----------|
| `useAccountStatus` | `useQuery` | `users.status.get` | `['status', 'get']` | 30_000 |
| `useAccountSessions` | `useQuery` | `users.status.list-sessions` | `['status', 'list-sessions']` | 30_000 |
| `useRevokeSession` | `useMutation` | `users.status.revoke-session` | n/a | n/a |

### Componentes

- `SessionsTable` (DataTable: `created_at`, `ip`, `user_agent` parseado,
  `last_seen_at`, badge "Sesion actual" si `is_current`, boton Revocar).
- `RevokeSessionButton`: dispara `useRevokeSession`. Si el backend
  responde **400 `CANNOT_REVOKE_CURRENT_SESSION`** (intento de revocar la
  sesion actual), muestra el error inline y NO revoca. El boton Revocar se
  deshabilita cuando `is_current === true` (defensa en profundidad; el
  backend es la fuente de verdad). En exito invalida
  `['status', 'list-sessions']`.

### Page

- `src/app/(admin)/sessions/page.tsx`: `SessionsTable` + estado de cuenta
  (de `useAccountStatus`).

**Tests**: `RevokeSessionButton` deshabilitado en la sesion actual; 400
en intento de revocar la actual; invalidacion de la lista en revocacion
exitosa de otra sesion.

**Commit**: `feat(admin,sessions-mgmt): listar mis sesiones + revocar (no la actual -> 400)`

## Fase 13 — Feature `users-admin/` (gestionar otros usuarios)

Gestion de OTROS usuarios. Consume el Lambda `users` (operation `admin`).
Solo accesible para admins (whitelist SSM `/portfolio/admin-emails`); el
backend responde **404 `NOT_FOUND`** a un no-admin (anti-enumeration), no
403.

### `src/features/users-admin/types.ts`

```typescript
// users.admin.list-users / get-user
export interface AdminUser {
  user_id: string
  email: string
  display_name: string | null
  status: 'active' | 'pending' | 'disabled' | 'locked'
  created_at: string
  total_mfa: number
}

export interface ListUsersPayload {
  page?: number
  page_size?: number
}

export interface ListUsersResponse {
  users: AdminUser[]
  page: number
  page_size: number
  total: number
}

export interface UserIdPayload {
  user_id: string
}

// users.admin.list-admin-actions
export interface AdminAction {
  action_id: string
  actor_user_id: string
  target_user_id: string | null
  action: string
  created_at: string
}
```

### Hooks (`src/features/users-admin/hooks/`)

| Hook | Tipo | Action | Key | staleTime |
|------|------|--------|-----|-----------|
| `useUsersList` | `useQuery` | `users.admin.list-users` | `['admin', 'users', {page, page_size}]` | 30_000 |
| `useUserDetail` | `useQuery` | `users.admin.get-user` | `['admin', 'user', userId]` | 0 |
| `useDisableUser` | `useMutation` | `users.admin.disable-user` | n/a | n/a |
| `useEnableUser` | `useMutation` | `users.admin.enable-user` | n/a | n/a |
| `useDeleteUser` | `useMutation` | `users.admin.delete-user` | n/a | n/a |
| `useForceLogout` | `useMutation` | `users.admin.force-logout` | n/a | n/a |
| `useAdminActions` | `useQuery` | `users.admin.list-admin-actions` | `['admin', 'actions']` | 30_000 |

Las mutations (`disable`/`enable`/`delete`/`force-logout`) toman
`{user_id}` e invalidan `['admin', 'users']` + `['admin', 'user', userId]`
+ `['admin', 'actions']` en exito.

### Componentes

- `UsersTable` (DataTable: `email`, `display_name`, badge `status`,
  `total_mfa`, `created_at`, acciones por fila).
- `UserDetailDrawer` (shadcn `Sheet` lateral con `useUserDetail`; deep-link
  via `?user=<id>` leido con `useSearchParams` dentro de Suspense — NO ruta
  dinamica, consistente con el resto del admin en `output: 'export'`).
- `UserActionsMenu` (dropdown: Deshabilitar / Habilitar segun `status`,
  Forzar logout, Eliminar con `AlertDialog` de confirmacion).
- `AdminActionsLog` (DataTable de `useAdminActions`: `actor`, `target`,
  `action`, `created_at`).

### Page

- `src/app/(admin)/users/page.tsx`: `UsersTable` + `UserDetailDrawer` +
  Tab/seccion `AdminActionsLog`. Si el backend responde 404 (no-admin), la
  page muestra el estado vacio "No tienes acceso a esta seccion" (no filtra
  la existencia del recurso).

**Tests**: 404 de no-admin renderiza el estado de acceso denegado;
`useDisableUser`/`useEnableUser` invalidan las queries correctas;
`UserDetailDrawer` lee `?user=<id>`.

**Commit**: `feat(admin,users-admin): list/get/disable/enable/delete/force-logout + admin-actions log (404 no-admin)`

## Fase 14 — Placeholder gestion CV

Link en el sidebar + page placeholder. SIN backend ni UI de edicion en
este plan.

### `src/app/(admin)/cv/page.tsx`

Page placeholder: titulo "Gestion de CV" + `Alert` informativo "Esta
seccion estara disponible en un plan futuro" + nota interna.

```tsx
'use client'

import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert'
import {FileText} from 'lucide-react'

export default function CvManagementPage() {
  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold">Gestion de CV</h1>
      <Alert>
        <FileText className="h-4 w-4" />
        <AlertTitle>Proximamente</AlertTitle>
        <AlertDescription>
          La edicion del CV se entregara en el plan futuro c-cv-management.
        </AlertDescription>
      </Alert>
    </section>
  )
}
```

> Plan futuro: `c-cv-management` (no existe aun). En este plan solo el
> link del sidebar + el placeholder. NUNCA implementar backend ni UI de
> edicion del CV aqui.

**Tests**: la page renderiza el titulo + el `Alert` de placeholder
(assert exacto del texto "Proximamente").

**Commit**: `feat(admin,cv): page placeholder + link sidebar (plan futuro c-cv-management)`

## Verificacion al final de fase 14 (gate intermedio)

```bash
# Tests de las features de gestion
pnpm --filter @portfolio/admin test:coverage

# Build OK
pnpm --filter @portfolio/admin build
ls admin/out/

# Preview con MSW: navegar manualmente
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev &
# Visitar:
# - http://localhost:3000/login
# - flow completo login -> shell admin
# - /settings -> editar display_name, ver tab Seguridad
# - /settings/security -> MFA (TOTP setup + QR), WebAuthn, recovery codes
# - /sessions -> ver mis sesiones, intentar revocar la actual (400)
# - /users -> (como admin) listar usuarios, abrir detalle, deshabilitar
# - /cv -> placeholder
# - /metrics -> placeholder del plan b-analytics-api
# - logout -> /login
```

Si todo verde, proceder con las fases de deploy infrastructure y E2E +
cleanup (ver 08-descomposicion). La UI de metricas (analytics, sessions de
tracking, events, visits, geo, devices, funnel, contacts) se integra en el
plan `b-analytics-api`.

[< 06-auth-feature](06-auth-feature.md) | [Siguiente: 08-descomposicion >](08-descomposicion.md)
