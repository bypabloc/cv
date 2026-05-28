# 06 — Feature `auth` + pages `(auth)/`

[< 05-ui-components](05-ui-components.md) | [Siguiente: 07-dashboard-features >](07-dashboard-features.md)

## Fase 7 — Feature `auth/` completa

Codigo concreto en `.claude/docs/dashboard/04-auth.md` (KT). Aqui solo
el inventario ejecutable.

### `src/features/auth/store/use-auth-store.ts`

Zustand 5 store con `persist` middleware a `localStorage`. Campos:

- `accessToken: string | null` (persist en localStorage)
- `refreshToken: string | null` (persist en localStorage)
- `tempToken: string | null` (in-memory, NO persist — flujo corto register/login)
- `user: User | null` (persist en localStorage)
- Actions: `setTokens(access, refresh, user)`, `setTempToken`,
  `setAccessToken`, `clearTokens`, `reset`
- Derived: `isAuthenticated()`, `isAccessExpired()`

**SIEMPRE** `partialize: (state) => ({accessToken, refreshToken, user})`. NUNCA persist `tempToken` (es efimero, 5 min).
**SIEMPRE** `name: 'portfolio-dashboard-auth'` + `storage: createJSONStorage(() => localStorage)`.

**Tests** (`tests/unit/features/auth/store/use-auth-store.test.ts`):

- `setTokens` actualiza access + refresh + user
- `isAuthenticated()` retorna false sin token
- `isAccessExpired()` retorna true con JWT expirado (mock con `exp` pasado)
- `clearTokens()` y `reset()` limpian estado y localStorage
- `partialize` excluye `tempToken` (verificar localStorage no contiene tempToken)
- Persistencia: setTokens -> reload pagina simulada -> tokens restaurados

### `src/features/auth/lib/refresh-mutex.ts`

Singleton in-flight Promise pattern. Ver codigo en KT.

**Tests** (`tests/unit/features/auth/lib/refresh-mutex.test.ts`):
- Single call: ejecuta `refreshFn` 1 vez
- 5 calls concurrent: ejecuta `refreshFn` 1 vez (assert exacto)
- Tras finalizar, `inFlight` vuelve a null
- Si `refreshFn` throws, `inFlight` se limpia

### `src/features/auth/lib/broadcast.ts`

```typescript
export function broadcastAuth(message: {type: 'LOGOUT' | 'TOKEN_REFRESH'; token?: string}): void
```

Guard `typeof BroadcastChannel === 'undefined'` para SSR/build safety.

### `src/features/auth/lib/token-expiry.ts`

```typescript
export function getJwtExpiry(token: string): number | null  // epoch ms
export function isJwtExpired(token: string): boolean
```

### `src/features/auth/api/auth-client.ts`

10 endpoints typed (registerStart, registerVerifyCode, loginStart,
loginVerifyCode, loginVerifyTotp, setPassword, resendCode,
sessionRefresh, sessionLogout, + plan 02: mfa*, webauthn*).

`sessionRefresh` siempre con `skipRefresh: true` (evitar recursion en
mutex).

### `src/features/auth/api/query-keys.ts`

```typescript
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  methods: (email: string) => [...authKeys.all, 'methods', email] as const,
}
```

### Hooks (`src/features/auth/hooks/`)

| Hook | Tipo | Funcion |
|------|------|---------|
| `useRegisterStart` | `useMutation` | POST register.start, setTempToken, redirect `/verify?flow=register` |
| `useRegisterVerifyCode` | `useMutation` | POST register.verify-code, setAccessToken + setUser, redirect `/dashboard` |
| `useLoginStart` | `useMutation` | POST login.start (con email + Turnstile), maneja 404 (suggest_register) y 200 (methods) |
| `useLoginVerifyCode` | `useMutation` | POST login.verify-code, setAccessToken + setUser, redirect |
| `useLoginVerifyTotp` | `useMutation` | (plan 02) POST login.verify-totp |
| `useSetPassword` | `useMutation` | POST verify.set-password |
| `useResendCode` | `useMutation` | POST verify.resend-code |
| `useSessionRefresh` | `useMutation` | POST session.refresh (mayoria de tiempo manejado por useAuthTimer) |
| `useLogout` | `useMutation` | POST session.logout, reset store, broadcastAuth LOGOUT, queryClient.clear, redirect `/login` |
| `useAuthTimer` | `useEffect` hook | Auto-refresh proactivo basado en `exp` del access. + Page Visibility re-check |
| `useMultiTabSync` | `useEffect` hook | BroadcastChannel listener → reset al recibir LOGOUT |

**Tests**: cada hook tiene su test mirror. Critico:
- `useLogout`: verifica reset + broadcast + queryClient.clear + redirect.
- `useAuthTimer`: usar `vi.useFakeTimers()` + `vi.advanceTimersByTime` para testear el setTimeout.
- `useMultiTabSync`: mock BroadcastChannel manual + simular postMessage.

### Components (`src/features/auth/components/`)

| Componente | Funcion | AC |
|-----------|---------|-----|
| `LoginForm` | email + (opcional plan 02) password + TurnstileWidget. Submit dispara `useLoginStart`. Maneja 404 (Alert con boton "Registrate"), 200 (redirect /verify), 401 (Alert error) | AC-8, AC-9 |
| `RegisterForm` | email + TurnstileWidget. Submit dispara `useRegisterStart`. Maneja 409 (Alert) | AC-9, AC-10 |
| `VerifyCodeInput` | shadcn InputOTP 8 chars (alfabeto Crockford: A-HJ-NP-Z2-9). Submit dispara `useRegisterVerifyCode` o `useLoginVerifyCode` segun `?flow=` query param | AC-11 |
| `MagicLinkPrompt` | Estatico: "Te enviamos un email con un link, click ahi para continuar" + Button "Reenviar email" → `useResendCode` | — |
| `SetPasswordForm` | password + confirmPassword con Zod refine | — |
| `TotpSetup` | (plan 02) Renderiza `qr_code_svg` del response + InputOTP de 6 digitos | AC-26 |
| `RecoveryCodesModal` | (plan 02) Lista 10 codes + buttons Download/Copy | — |
| `WebAuthnRegisterButton` | (plan 02) `@simplewebauthn/browser` + `startRegistration` | — |
| `AuthGuard` | Hook `isAuthenticated()`. Si false, redirect a `/login?next=<path>`. Si true, render children. Hooks: useAuthTimer + useMultiTabSync | AC-19, AC-20 |
| `TurnstileWidget` | Wrapper `@marsidev/react-turnstile` con sitekey de `env.NEXT_PUBLIC_TURNSTILE_SITEKEY` | — |

**Tests**: cada componente con BDD-style. Critico:
- `LoginForm`: simular submit con email invalido (Zod error), valido (mutation call), email no existente (Alert + redirect button).
- `AuthGuard`: simular sesion sin token → redirect. Con token → renderiza children.
- `MagicLinkPrompt`: clickear "Reenviar" llama mutation correcto.

**Commit**: `feat(dashboard,auth): store Zustand + mutex refresh + hooks (login/register/verify/logout) + AuthGuard + Turnstile + tests`

## Fase 8 — Pages `(auth)/`

### `src/app/(auth)/login/page.tsx`

```tsx
'use client'

import {LoginForm} from '@/features/auth/components/login-form'
import Link from 'next/link'

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold">Iniciar sesion</h1>
        <LoginForm />
        <p className="text-center text-sm text-muted-foreground">
          No tenes cuenta? <Link href="/register" className="text-primary hover:underline">Registrate</Link>
        </p>
      </div>
    </div>
  )
}
```

### `src/app/(auth)/register/page.tsx`

Mismo patron con `RegisterForm`.

### `src/app/(auth)/verify/page.tsx`

```tsx
'use client'

import {useSearchParams} from 'next/navigation'
import {Suspense} from 'react'
import {VerifyCodeInput} from '@/features/auth/components/verify-code-input'
import {MagicLinkPrompt} from '@/features/auth/components/magic-link-prompt'
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs'

function VerifyContent() {
  const params = useSearchParams()
  const flow = params.get('flow') as 'register' | 'login'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold">Verifica tu email</h1>
        <Tabs defaultValue="code">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="code">Code</TabsTrigger>
            <TabsTrigger value="magic-link">Magic link</TabsTrigger>
          </TabsList>
          <TabsContent value="code">
            <VerifyCodeInput flow={flow} />
          </TabsContent>
          <TabsContent value="magic-link">
            <MagicLinkPrompt />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div>Cargando...</div>}>
      <VerifyContent />
    </Suspense>
  )
}
```

> Importante: `useSearchParams()` necesita Suspense boundary en export
> mode (ver `.claude/docs/dashboard/01-stack.md` limitacion 3).

### `src/app/(auth)/callback/page.tsx`

Ver codigo completo en `.claude/docs/dashboard/04-auth.md`. Resumen:

- Lee `window.location.hash` (fragment), parsea con `URLSearchParams`.
- Si no hay `access` → redirect `/login` + toast error.
- Decodea JWT con `jwt-decode` (solo shape, no firma).
- `setAccessToken`, `setUser`, `setRefreshExpiry`.
- `history.replaceState(null, '', '/dashboard')` ANTES de navegar.
- `router.replace('/dashboard')` + toast.success.
- `useRef(false)` para evitar doble exec en StrictMode dev.

**Cumple**: AC-12, AC-13.

### `src/app/(auth)/set-password/page.tsx`

`SetPasswordForm` que usa `useSetPassword`. Redirect a `/dashboard`
on success.

**Commit**: `feat(dashboard,auth): pages (auth)/ login/register/verify/callback/set-password`

## Fase 9 — MSW setup + Vitest setup

### `dashboard/tests/setup.ts`

Ver codigo completo en `.claude/docs/dashboard/06-testing.md`.
Resumen:

- Importa `@testing-library/jest-dom`.
- Polyfill `BroadcastChannel` (happy-dom no la tiene).
- `vi.stubEnv` para `NEXT_PUBLIC_*`.
- `beforeAll`: `server.listen()`.
- `afterEach`: `cleanup()`, `server.resetHandlers()`, reset Zustand,
  `localStorage.clear()`.
- `afterAll`: `server.close()`.

### `dashboard/tests/mocks/handlers/auth.ts`

Mocks de los endpoints `/auth`. Cubrir:
- `register.start` con email valido + email duplicado
- `register.verify-code` con code valido + invalido
- `login.start` con email valido + inexistente (404 + suggest_register)
- `login.verify-code`
- `session.refresh`
- `session.logout` (204)

Helper `makeJwt({sub, email, exp})` para generar JWTs fake.

### `dashboard/tests/mocks/handlers/analytics.ts`

Mocks de `/analytics?operation=...&action=...`. Cubrir las 19 actions
con responses representativos (fixtures sinteticos).

### `dashboard/tests/mocks/server.ts`

```typescript
import {setupServer} from 'msw/node'
import {authHandlers} from './handlers/auth'
import {analyticsHandlers} from './handlers/analytics'

export const server = setupServer(...authHandlers, ...analyticsHandlers)
```

### `dashboard/tests/mocks/browser.ts`

```typescript
import {setupWorker} from 'msw/browser'
// ...mismos handlers
export const worker = setupWorker(...)
```

Init en dev opcional via `NEXT_PUBLIC_USE_MSW=true`:

```typescript
// src/app/layout.tsx (en useEffect del provider)
if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_USE_MSW === 'true') {
  const {worker} = await import('@/tests/mocks/browser')
  await worker.start({onUnhandledRequest: 'bypass'})
}
```

Tambien: `npx msw init public/` para generar `mockServiceWorker.js`.

### `dashboard/tests/utils/render.tsx`

Render wrapper con providers (ThemeProvider + QueryClient test + Toaster).
Ver codigo en KT.

### Fixtures (`dashboard/tests/fixtures/`)

- `users.ts`: 3 users (active, pending, locked)
- `sessions.ts`: 50 sessions sinteticas
- `events.ts`: 200 events
- `analytics.ts`: overview, timeseries, top-pages, top-niches

**Commit**: `feat(dashboard,tests): MSW handlers (auth + analytics) + Vitest setup + render wrapper + fixtures`

## Verificacion al final de fase 9 (gate intermedio)

```bash
# Unit tests del auth feature deben pasar
pnpm --filter @portfolio/dashboard test tests/unit/features/auth

# Coverage del auth >= 80% per-file
pnpm --filter @portfolio/dashboard test:coverage tests/unit/features/auth

# Build estatico OK
pnpm --filter @portfolio/dashboard build

# Preview manual: probar login con MSW
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/dashboard dev &
# Abrir http://localhost:3000/login → submit con user@test.com / Turnstile success → verify code 12345678 → redirect /dashboard (que aun no existe, OK)
```

[< 05-ui-components](05-ui-components.md) | [Siguiente: 07-dashboard-features >](07-dashboard-features.md)
