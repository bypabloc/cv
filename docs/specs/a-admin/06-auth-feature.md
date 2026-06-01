# 06 — Feature `auth` + pages `(auth)/`

[< 05-ui-components](05-ui-components.md) | [Siguiente: 07-settings-features >](07-settings-features.md)

## Fase 7 — Feature `auth/` completa

Codigo concreto en `.claude/docs/admin/04-auth.md` (KT). Aqui solo
el inventario ejecutable.

### `src/features/auth/store/use-auth-store.ts`

Zustand 5 store con `persist` middleware a `localStorage`. Campos:

- `accessToken: string | null` (**in-memory, NO persist** — rotado en cada refresh; persistirlo deja stale token tras reload)
- `tempToken: string | null` (in-memory, NO persist — flujo corto register/login, 5 min)
- `refreshToken: string | null` (persist en localStorage — sobrevive reload, necesario para reanudar sesion)
- `refreshExpiry: number | null` (persist; epoch ms del `exp` del refresh, evita decodear el JWT en cada render)
- `user: User | null` (persist en localStorage)
- Actions: `setTokens(access, refresh, user, refreshExpiry)`, `setTempToken`,
  `setAccessToken`, `clearTokens`, `reset`
- Derived: `isAuthenticated()`, `isAccessExpired()`

**SIEMPRE** `partialize: (state) => ({refreshToken, refreshExpiry, user})`.
NUNCA persistir `accessToken` (rota en cada `/session/refresh`; persistido queda stale).
NUNCA persistir `tempToken` (es efimero, 5 min).
**SIEMPRE** `name: 'portfolio-admin-auth'` + `storage: createJSONStorage(() => localStorage)`.

**Bootstrap al cargar la app**: el `accessToken` arranca en `null` (no persistido).
`useAuthTimer` detecta `refreshToken + refreshExpiry > now` y dispara
`/session/refresh` automaticamente para hidratar el `accessToken` en memoria.
Si el refresh esta expirado, `reset()` + redirect a `/login`.

**Tests** (`tests/unit/features/auth/store/use-auth-store.test.ts`):

- `setTokens` actualiza access (memoria) + refresh + refreshExpiry + user
- `isAuthenticated()` retorna false sin token
- `isAccessExpired()` retorna true con JWT expirado (mock con `exp` pasado)
- `clearTokens()` y `reset()` limpian estado y localStorage
- `partialize` excluye `accessToken` y `tempToken` (assert exacto: `JSON.parse(localStorage.getItem('portfolio-admin-auth')).state` solo contiene `refreshToken`, `refreshExpiry`, `user`)
- Persistencia: setTokens -> reload simulado (re-crear store) -> `accessToken === null`, `refreshToken` y `user` restaurados

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

El Lambda `auth` esta desplegado en dev/stage/prod con 6 operations / 26
actions invocables (codigo: `serverless/lambda/services/auth/`; contrato:
`.claude/rules/auth-system.md` + `.claude/docs/auth-system/`). El cliente
expone UNA funcion typed por action. Todas hacen `POST /auth` con body JSON
`{operation, action, data}`, salvo los `verify-magic-link` que son callbacks
GET (se resuelven en `(auth)/callback`, no requieren funcion en el cliente).
El handler HTTP inyecta `data._meta`; los endpoints autenticados leen el
access JWT de `_meta.authorization` (header `Authorization: Bearer <jwt>`),
que el `api-client.ts` agrega en cada request. NUNCA `any`: cada funcion
tipa su `data` de entrada y su response.

Shapes compartidos (de `serverless/lambda/services/auth/core/models/`):

```typescript
interface AuthResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}
interface TempTokenResponse {
  temp_token: string
  user_id: string
  expires_in: number
  methods?: ('magic-link' | 'email-code' | 'password' | 'totp' | 'webauthn')[]
}
interface MfaListResponse {
  methods: {
    kind: 'totp' | 'email_code'
    confirmed_at: string | null
    is_preferred: boolean
  }[]
  webauthn_count: number
  total_mfa: number
}
interface TotpSetupResponse {
  secret_b32: string
  otpauth_url: string
}
interface RecoveryCodesResponse {
  codes: string[]
}
interface WebauthnRegisterOptionsResponse {
  challenge_id: string
  options: PublicKeyCredentialCreationOptionsJSON
}
interface WebauthnLoginOptionsResponse {
  challenge_id: string
  options: PublicKeyCredentialRequestOptionsJSON
}
interface WebauthnCredential {
  id: string
  nickname: string | null
  last_used_at: string | null
  created_at: string
}
```

`PublicKeyCredentialCreationOptionsJSON` / `PublicKeyCredentialRequestOptionsJSON`
se importan de `@simplewebauthn/browser` (no se redeclaran).

#### operation `register` (3 actions)

| Funcion | action | body `data` | response |
|---------|--------|-------------|----------|
| `registerStart(data)` | `start` | `{email, cf_turnstile_response, niche?}` | `TempTokenResponse` |
| (callback GET) | `verify-magic-link` | `{token}` (opaque 32-byte b64url) | `AuthResponse` (via fragment hash en `/callback`) |
| `registerVerifyCode(data)` | `verify-code` | `{code, temp_token}` (code 8 chars Crockford A-HJ-NP-Z2-9) | `AuthResponse` |

#### operation `login` (5 actions)

| Funcion | action | body `data` | response |
|---------|--------|-------------|----------|
| `loginStart(data)` | `start` | `{email, cf_turnstile_response, password?, niche?}` | 200 `TempTokenResponse` (con `methods`) / 404 `{error: 'EMAIL_NOT_FOUND', suggest_register}` |
| (callback GET) | `verify-magic-link` | `{token}` | `AuthResponse` |
| `loginVerifyCode(data)` | `verify-code` | `{code, temp_token}` | `AuthResponse` |
| `loginVerifyPassword(data)` | `verify-password` | `{temp_token, password}` (password min 12) | `AuthResponse` (sin MFA) / `TempTokenResponse` step=2 (con MFA -> `methods`) |
| `loginVerifyTotp(data)` | `verify-totp` | `{temp_token, code}` (temp step=2 prev=password\|webauthn; code 6 digitos) | `AuthResponse` |

> `_mfa_login.py` y `_password_check.py` son helpers internos del controller
> (prefijo `_`), NO actions invocables: no se mapean en el cliente.

#### operation `verify` (2 actions)

| Funcion | action | body `data` | response |
|---------|--------|-------------|----------|
| `setPassword(data)` | `set-password` | `{password, temp_token}` (password min 12, temp step>=2) | `AuthResponse` |
| `resendCode(data)` | `resend-code` | `{temp_token}` | `{ok: true}` (rate-limit propio 1/60s, 3/5min) |

#### operation `session` (2 actions)

| Funcion | action | body `data` | response |
|---------|--------|-------------|----------|
| `sessionRefresh(data)` | `refresh` | `{refresh_token}` | `AuthResponse` (rota familia) |
| `sessionLogout(data)` | `logout` | `{access_token, refresh_token?}` | `{ok: true}` |

`sessionRefresh` siempre con `skipRefresh: true` (evitar recursion en el
mutex de `api-client.ts`).

#### operation `mfa` (8 actions)

Todas requieren access JWT salvo `recoveryCodesConsume` (que usa temp JWT
step=2, parte del flujo de login con MFA).

| Funcion | action | body `data` | auth | response |
|---------|--------|-------------|------|----------|
| `mfaSetupTotp()` | `setup-totp` | `{}` | access JWT | `TotpSetupResponse` |
| `mfaConfirmTotp(data)` | `confirm-totp` | `{code}` (6 digitos) | access JWT | `MfaListResponse` (primer metodo MFA revoca la familia de refresh, AC-27) |
| `mfaSetupEmailCode()` | `setup-email-code` | `{}` | access JWT | `MfaListResponse` |
| `mfaSetPreferred(data)` | `set-preferred` | `{kind: 'totp' \| 'email_code'}` | access JWT | `MfaListResponse` |
| `mfaDisable(data)` | `disable` | `{kind: 'totp' \| 'email_code'}` | access JWT | `MfaListResponse` (409 si deja `total_mfa == 0`) |
| `mfaList()` | `list` | `{}` | access JWT | `MfaListResponse` |
| `mfaRecoveryCodesGenerate()` | `recovery-codes-generate` | `{}` | access JWT | `RecoveryCodesResponse` (10 codes, mostrados una sola vez) |
| `recoveryCodesConsume(data)` | `recovery-codes-consume` | `{temp_token, code}` (temp step=2 prev=password\|webauthn; code 10 chars) | temp JWT step=2 (factor fuerte) | `AuthResponse` (403 `RECOVERY_REQUIRES_STRONG_FACTOR` si el temp viene de magic-link/email-code) |

#### operation `webauthn` (6 actions)

| Funcion | action | body `data` | auth | response |
|---------|--------|-------------|------|----------|
| `webauthnRegisterOptions()` | `register-options` | `{}` | access JWT | `WebauthnRegisterOptionsResponse` (challenge_id en DDB TTL 5min) |
| `webauthnRegisterVerify(data)` | `register-verify` | `{challenge_id, response, nickname?}` (`response` del browser via `startRegistration`) | access JWT | `MfaListResponse` (primer metodo MFA revoca familia, AC-27) |
| `webauthnLoginOptions(data)` | `login-options` | `{email}` | sin auth | `WebauthnLoginOptionsResponse` (passkey login passwordless) |
| `webauthnLoginVerify(data)` | `login-verify` | `{challenge_id, response}` (`response` via `startAuthentication`) | sin auth | `AuthResponse` (sign_count monotonico; clone detection -> 401) |
| `webauthnListCredentials()` | `list-credentials` | `{}` | access JWT | `WebauthnCredential[]` |
| `webauthnDeleteCredential(data)` | `delete-credential` | `{credential_id}` (UUID PK del row) | access JWT | `WebauthnCredential[]` (guard MUST_KEEP_ONE_MFA_METHOD) |

`login-options` y `login-verify` son los UNICOS de `webauthn` sin auth:
habilitan el login passwordless con passkey (sin password ni code previo).

### `src/features/auth/api/query-keys.ts`

```typescript
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  methods: (email: string) => [...authKeys.all, 'methods', email] as const,
  mfa: () => [...authKeys.all, 'mfa'] as const,
  webauthn: () => [...authKeys.all, 'webauthn'] as const,
}
```

### Hooks (`src/features/auth/hooks/`)

| Hook | Tipo | Funcion |
|------|------|---------|
| `useRegisterStart` | `useMutation` | POST register.start, setTempToken, redirect `/verify?flow=register` |
| `useRegisterVerifyCode` | `useMutation` | POST register.verify-code, setAccessToken + setUser, redirect `/admin` |
| `useLoginStart` | `useMutation` | POST login.start (con email + Turnstile), maneja 404 (suggest_register) y 200 (methods) |
| `useLoginVerifyCode` | `useMutation` | POST login.verify-code, setAccessToken + setUser, redirect |
| `useLoginVerifyPassword` | `useMutation` | POST login.verify-password. Sin MFA -> setTokens + redirect. Con MFA -> setTempToken step=2 + redirect a paso TOTP/recovery segun `methods` |
| `useLoginVerifyTotp` | `useMutation` | POST login.verify-totp, setTokens + setUser, redirect `/admin` |
| `useSetPassword` | `useMutation` | POST verify.set-password |
| `useResendCode` | `useMutation` | POST verify.resend-code |
| `useSessionRefresh` | `useMutation` | POST session.refresh (mayoria de tiempo manejado por useAuthTimer) |
| `useLogout` | `useMutation` | POST session.logout, reset store, broadcastAuth LOGOUT, queryClient.clear, redirect `/login` |
| `useAuthTimer` | `useEffect` hook | Auto-refresh proactivo basado en `exp` del access. + Page Visibility re-check |
| `useMultiTabSync` | `useEffect` hook | BroadcastChannel listener → reset al recibir LOGOUT |
| `useSetupTotp` | `useMutation` | POST mfa.setup-totp -> `TotpSetupResponse` (secret_b32 + otpauth_url) |
| `useConfirmTotp` | `useMutation` | POST mfa.confirm-totp, invalida `authKeys.mfa()` |
| `useSetupEmailCode` | `useMutation` | POST mfa.setup-email-code, invalida `authKeys.mfa()` |
| `useSetPreferredMfa` | `useMutation` | POST mfa.set-preferred, invalida `authKeys.mfa()` |
| `useDisableMfa` | `useMutation` | POST mfa.disable, invalida `authKeys.mfa()`. Maneja 409 (MUST_KEEP_ONE_MFA_METHOD) |
| `useMfaList` | `useQuery` | GET mfa.list -> `MfaListResponse` (queryKey `authKeys.mfa()`) |
| `useGenerateRecoveryCodes` | `useMutation` | POST mfa.recovery-codes-generate -> `RecoveryCodesResponse` |
| `useConsumeRecoveryCode` | `useMutation` | POST mfa.recovery-codes-consume (temp JWT step=2), setTokens + redirect. Maneja 403 RECOVERY_REQUIRES_STRONG_FACTOR |
| `useWebauthnRegisterOptions` | `useMutation` | POST webauthn.register-options -> options + challenge_id |
| `useWebauthnRegisterVerify` | `useMutation` | POST webauthn.register-verify, invalida `authKeys.webauthn()` + `authKeys.mfa()` |
| `useWebauthnLoginOptions` | `useMutation` | POST webauthn.login-options (sin auth) -> options + challenge_id |
| `useWebauthnLoginVerify` | `useMutation` | POST webauthn.login-verify (sin auth), setTokens + redirect. Maneja 401 (clone detection) |
| `useListCredentials` | `useQuery` | GET webauthn.list-credentials -> `WebauthnCredential[]` (queryKey `authKeys.webauthn()`) |
| `useDeleteCredential` | `useMutation` | POST webauthn.delete-credential, invalida `authKeys.webauthn()`. Maneja 409 (MUST_KEEP_ONE_MFA_METHOD) |

**Tests**: cada hook tiene su test mirror. Critico:
- `useLogout`: verifica reset + broadcast + queryClient.clear + redirect.
- `useAuthTimer`: usar `vi.useFakeTimers()` + `vi.advanceTimersByTime` para testear el setTimeout.
- `useMultiTabSync`: mock BroadcastChannel manual + simular postMessage.
- `useConfirmTotp` / `useWebauthnRegisterVerify`: verifica que invalida `authKeys.mfa()` on success.
- `useConsumeRecoveryCode`: 403 RECOVERY_REQUIRES_STRONG_FACTOR no setea tokens (assert exacto: store sin cambios).
- `useWebauthnLoginVerify`: 401 clone detection muestra error, no setea tokens.
- `useDisableMfa` / `useDeleteCredential`: 409 propaga el error sin invalidar la query.

### Components (`src/features/auth/components/`)

| Componente | Funcion | AC |
|-----------|---------|-----|
| `LoginForm` | email + password opcional + TurnstileWidget. Submit dispara `useLoginStart`. Maneja 404 (Alert con boton "Registrate"), 200 (redirect /verify segun `methods`), 401 (Alert error). Boton "Usar passkey" -> `WebAuthnLoginButton` | AC-8, AC-9 |
| `RegisterForm` | email + TurnstileWidget. Submit dispara `useRegisterStart`. Maneja 409 (Alert) | AC-9, AC-10 |
| `VerifyCodeInput` | shadcn InputOTP 8 chars (alfabeto Crockford: A-HJ-NP-Z2-9). Submit dispara `useRegisterVerifyCode` o `useLoginVerifyCode` segun `?flow=` query param | AC-11 |
| `MagicLinkPrompt` | Estatico: "Te enviamos un email con un link, click ahi para continuar" + Button "Reenviar email" → `useResendCode` | — |
| `SetPasswordForm` | password + confirmPassword con Zod refine | — |
| `LoginPasswordInput` | password (min 12) para el paso `login.verify-password`. Submit dispara `useLoginVerifyPassword`. Con MFA -> avanza a `LoginTotpInput` / recovery segun `methods` | — |
| `LoginTotpInput` | InputOTP de 6 digitos para `login.verify-totp` (paso final del login con MFA). Submit dispara `useLoginVerifyTotp`. Link "Usar codigo de recuperacion" -> `RecoveryCodeInput` | AC-26 |
| `RecoveryCodeInput` | Input de 10 chars (Crockford) para `mfa.recovery-codes-consume` (parte del login con MFA, requiere temp JWT step=2). Submit dispara `useConsumeRecoveryCode`. Maneja 403 RECOVERY_REQUIRES_STRONG_FACTOR | — |
| `WebAuthnLoginButton` | `@simplewebauthn/browser` `startAuthentication`. Pide email -> `useWebauthnLoginOptions` -> `startAuthentication(options)` -> `useWebauthnLoginVerify`. Login passwordless sin auth previa | — |
| `TotpSetup` | Llama `useSetupTotp`, renderiza el QR DESDE el `otpauth_url` del response con `qrcode.react` (`<QRCodeSVG value={otpauth_url} />`) — el backend NO devuelve `qr_code_svg`, devuelve `secret_b32` + `otpauth_url`. Muestra `secret_b32` como fallback manual. InputOTP de 6 digitos -> `useConfirmTotp` | AC-26 |
| `RecoveryCodesModal` | Lista los 10 codes de `useGenerateRecoveryCodes` (mostrados una sola vez) + buttons Download/Copy | — |
| `WebAuthnRegisterButton` | `@simplewebauthn/browser` `startRegistration`. `useWebauthnRegisterOptions` -> `startRegistration(options)` -> `useWebauthnRegisterVerify({challenge_id, response, nickname})` | — |
| `AuthGuard` | Hook `isAuthenticated()`. Si false, redirect a `/login?next=<path>`. Si true, render children. Hooks: useAuthTimer + useMultiTabSync | AC-19, AC-20 |
| `TurnstileWidget` | Wrapper `@marsidev/react-turnstile` con sitekey de `env.NEXT_PUBLIC_TURNSTILE_SITEKEY` | — |

> WebAuthn usa `@simplewebauthn/browser`: `startRegistration(options)` y
> `startAuthentication(options)` toman las `options` del response del backend
> y devuelven el `response` del browser, que se reenvia junto al `challenge_id`
> a `register-verify` / `login-verify`. El QR del TOTP se renderiza
> client-side desde el `otpauth_url` (lib `qrcode.react`); el backend NUNCA
> manda un SVG renderizado.

**Tests**: cada componente con BDD-style. Critico:
- `LoginForm`: simular submit con email invalido (Zod error), valido (mutation call), email no existente (Alert + redirect button).
- `AuthGuard`: simular sesion sin token → redirect. Con token → renderiza children.
- `MagicLinkPrompt`: clickear "Reenviar" llama mutation correcto.
- `TotpSetup`: con `useSetupTotp` mockeado devolviendo `{secret_b32, otpauth_url}`, el `QRCodeSVG` recibe `value={otpauth_url}` (assert exacto del prop) y `secret_b32` se muestra como texto fallback.
- `LoginTotpInput`: submit de 6 digitos dispara `useLoginVerifyTotp`; link recovery monta `RecoveryCodeInput`.
- `RecoveryCodeInput`: 403 RECOVERY_REQUIRES_STRONG_FACTOR muestra Alert, no redirige.
- `WebAuthnRegisterButton`: mock `startRegistration` -> reenvia `{challenge_id, response}` a `useWebauthnRegisterVerify`.
- `WebAuthnLoginButton`: mock `startAuthentication` -> `useWebauthnLoginVerify`; sin requerir token previo.

**Commit**: `feat(admin,auth): store Zustand + mutex refresh + auth-client 26 actions + hooks (register/login/verify/session/mfa/webauthn) + AuthGuard + Turnstile + tests`

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
> mode (ver `.claude/docs/admin/01-stack.md` limitacion 3).

### `src/app/(auth)/callback/page.tsx`

Ver codigo completo en `.claude/docs/admin/04-auth.md`. Resumen:

- Lee `window.location.hash` (fragment), parsea con `URLSearchParams`.
- Si no hay `access` → redirect `/login` + toast error.
- Decodea JWT con `jwt-decode` (solo shape, no firma).
- `setAccessToken`, `setUser`, `setRefreshExpiry`.
- `history.replaceState(null, '', '/admin')` ANTES de navegar.
- `router.replace('/admin')` + toast.success.
- `useRef(false)` para evitar doble exec en StrictMode dev.

**Cumple**: AC-12, AC-13.

### `src/app/(auth)/set-password/page.tsx`

`SetPasswordForm` que usa `useSetPassword`. Redirect a `/admin`
on success.

**Commit**: `feat(admin,auth): pages (auth)/ login/register/verify/callback/set-password`

## Fase 9 — MSW setup + Vitest setup

### `admin/tests/setup.ts`

Ver codigo completo en `.claude/docs/admin/06-testing.md`.
Resumen:

- Importa `@testing-library/jest-dom`.
- Polyfill `BroadcastChannel` (happy-dom no la tiene).
- `vi.stubEnv` para `NEXT_PUBLIC_*`.
- `beforeAll`: `server.listen()`.
- `afterEach`: `cleanup()`, `server.resetHandlers()`, reset Zustand,
  `localStorage.clear()`.
- `afterAll`: `server.close()`.

### `admin/tests/mocks/handlers/auth.ts`

Mocks de los endpoints `/auth`. Cubrir:
- `register.start` con email valido + email duplicado
- `register.verify-code` con code valido + invalido
- `login.start` con email valido + inexistente (404 + suggest_register)
- `login.verify-code`
- `session.refresh`
- `session.logout` (204)

Helper `makeJwt({sub, email, exp})` para generar JWTs fake.

### `admin/tests/mocks/handlers/analytics.ts`

Mocks de `/analytics?operation=...&action=...`. Cubrir las 19 actions
con responses representativos (fixtures sinteticos).

### `admin/tests/mocks/server.ts`

```typescript
import {setupServer} from 'msw/node'
import {authHandlers} from './handlers/auth'
import {analyticsHandlers} from './handlers/analytics'

export const server = setupServer(...authHandlers, ...analyticsHandlers)
```

### `admin/tests/mocks/browser.ts`

```typescript
import {setupWorker} from 'msw/browser'
// ...mismos handlers
export const worker = setupWorker(...)
```

Init en dev opcional via `NEXT_PUBLIC_USE_MSW=true`. El alias `@/`
apunta a `./src/*` y la carpeta `tests/` esta FUERA de `src/` — usar
import relativo (`../../tests/...`) o agregar un segundo alias dedicado.
Recomendado: agregar `"@tests/*": ["../tests/*"]` a `tsconfig.json#paths`
y al `vitest.config.ts#resolve.alias` para que el import compile en build
y en tests:

```typescript
// src/app/layout.tsx (en un Client Component wrapper con useEffect)
if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_USE_MSW === 'true') {
  const {worker} = await import('@tests/mocks/browser')
  await worker.start({onUnhandledRequest: 'bypass'})
}
```

Si NO se quiere agregar el alias, usar el path relativo explicito desde
el archivo que importa (ej. `../../tests/mocks/browser` desde
`src/app/layout.tsx`). NUNCA usar `@/tests/...` porque `@/` se resuelve
a `src/tests/` que no existe — el build de Next + el typecheck fallan
con `Module not found`.

Tambien: `npx msw init public/` para generar `mockServiceWorker.js`.

### `admin/tests/utils/render.tsx`

Render wrapper con providers (ThemeProvider + QueryClient test + Toaster).
Ver codigo en KT.

### Fixtures (`admin/tests/fixtures/`)

- `users.ts`: 3 users (active, pending, locked)
- `sessions.ts`: 50 sessions sinteticas
- `events.ts`: 200 events
- `analytics.ts`: overview, timeseries, top-pages, top-niches

**Commit**: `feat(admin,tests): MSW handlers (auth + analytics) + Vitest setup + render wrapper + fixtures`

## Verificacion al final de fase 9 (gate intermedio)

```bash
# Unit tests del auth feature deben pasar
pnpm --filter @portfolio/admin test tests/unit/features/auth

# Coverage del auth >= 80% per-file
pnpm --filter @portfolio/admin test:coverage tests/unit/features/auth

# Build estatico OK
pnpm --filter @portfolio/admin build

# Preview manual: probar login con MSW
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev &
# Abrir http://localhost:3000/login → submit con user@test.com / Turnstile success → verify code 12345678 → redirect /admin (que aun no existe, OK)
```

[< 05-ui-components](05-ui-components.md) | [Siguiente: 07-settings-features >](07-settings-features.md)

## Nota: la gestion de MFA/WebAuthn vive en el feature `settings`

Este feature `auth` PRODUCE el flujo de login/register/verify/session y el
auth-client con las 26 actions (incluyendo `mfa.*` y `webauthn.*`). La
GESTION de esos metodos — setup/disable/list de MFA (TOTP, email-code),
passkeys WebAuthn (register/list/delete), recovery codes, cambio de
contraseña, change-email y delete-account — NO se implementa aqui: vive en
el feature `settings` (pages `(admin)/settings/seguridad`). Esos hooks
(`useSetupTotp`, `useConfirmTotp`, `useDisableMfa`, `useMfaList`,
`useGenerateRecoveryCodes`, `useWebauthnRegisterOptions`,
`useWebauthnRegisterVerify`, `useListCredentials`, `useDeleteCredential`,
etc.) se definen aqui como parte del auth-client + hooks compartidos y los
CONSUME el feature `settings`. Ver [07-settings-features](07-settings-features.md)
para las pantallas de gestion.
