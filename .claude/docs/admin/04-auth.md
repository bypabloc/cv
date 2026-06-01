# 04 — Auth: JWT + Tanstack Query + Zustand + magic link + BroadcastChannel

[< 03-ui](03-ui.md) | [Siguiente: 05-deploy >](05-deploy.md)

## Resumen del flujo

El admin consume el Lambda `auth` desplegado
(`serverless/lambda/services/auth/`): 6 operations / 26 actions. Tres
tipos de JWT (temp 5min rolling, access 15min, refresh 30dias con
family_id rotation). MFA (TOTP, email-code, recovery codes) y WebAuthn
(passkeys) son scope del admin (feature `auth`) desde el inicio. El admin
tambien consume el Lambda `users` (profile / status / admin) para la
gestion de cuenta y de usuarios (features `settings`, `sessions-mgmt`,
`users-admin`): ver el inventario de `users` en el README del KT. Contrato
y reglas en `.claude/rules/auth-system.md` + `.claude/docs/auth-system/`.

### Decision: tokens en `localStorage` (NO HttpOnly cookies)

El admin es un **SPA estatico** (Next.js `output: 'export'`)
deployado en Cloudflare Pages bajo `admin.portfolio.{env}.the-full-stack.com`.
El backend Lambda vive en `api.portfolio.{env}.the-full-stack.com` —
**otro origen**. Para que el backend pudiera setear cookies HttpOnly
accesibles desde el admin, la cookie tendria que ser
`SameSite=None; Secure; Domain=.the-full-stack.com`, lo que abre
vectores CSRF en los 6 niches publicos del portfolio y rompe
portabilidad (mobile app, embebido en widgets).

**Conclusion**: los tres tokens (access, refresh, temp) viajan en el
body de la respuesta y se persisten en `localStorage`. La defensa
contra XSS es CSP estricta + SRI en third-party + access JWT corto
(15 min) + refresh rotation con detection de reuso.

Storage:

- **access** (`localStorage['access_token']`): TTL 15 min. Persisted
  en Zustand. Reaplicado en `Authorization: Bearer` de cada request.
- **refresh** (`localStorage['refresh_token']`): TTL 30 dias.
  Persisted. Solo el wrapper `lib/api-client.ts` lo lee (jamas pasa
  por componentes UI). Cada uso lo rota (la respuesta de
  `/session/refresh` devuelve uno nuevo, el viejo queda blacklisteado
  en DynamoDB con `family_id`).
- **temp** (`localStorage['temp_token']`): TTL 5 min, rolling. Vive
  solo durante el flujo multi-step de register/login.

## Auth store (Zustand)

`src/features/auth/store/use-auth-store.ts`:

```typescript
import {create} from 'zustand'
import {persist, createJSONStorage} from 'zustand/middleware'
import {jwtDecode} from 'jwt-decode'

export interface User {
  id: string
  email: string
  status: 'pending' | 'active' | 'disabled' | 'locked' | 'deleted'
  has_password: boolean
  mfa_methods: ('totp' | 'webauthn' | 'email_code')[]
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  tempToken: string | null
  user: User | null

  // actions
  setAccessToken: (token: string | null) => void
  setRefreshToken: (token: string | null) => void
  setTempToken: (token: string | null) => void
  setUser: (user: User | null) => void
  setTokens: (access: string, refresh: string, user: User) => void
  reset: () => void

  // derived
  isAuthenticated: () => boolean
  isAccessExpired: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      tempToken: null,
      user: null,

      setAccessToken: (token) => set({accessToken: token}),
      setRefreshToken: (token) => set({refreshToken: token}),
      setTempToken: (token) => set({tempToken: token}),
      setUser: (user) => set({user}),
      setTokens: (access, refresh, user) =>
        set({accessToken: access, refreshToken: refresh, user}),

      reset: () => set({
        accessToken: null,
        refreshToken: null,
        tempToken: null,
        user: null,
      }),

      isAuthenticated: () => {
        const {accessToken, user} = get()
        if (!accessToken || !user) return false
        return !get().isAccessExpired()
      },

      isAccessExpired: () => {
        const {accessToken} = get()
        if (!accessToken) return true
        try {
          const {exp} = jwtDecode<{exp: number}>(accessToken)
          return Date.now() >= exp * 1000
        } catch {
          return true
        }
      },
    }),
    {
      name: 'portfolio-admin-auth',
      storage: createJSONStorage(() => localStorage),
      // Persistir access, refresh y user. NO persist temp (vive solo
      // durante el flujo multi-step).
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    },
  ),
)
```

## Refresh mutex

`src/features/auth/lib/refresh-mutex.ts`:

```typescript
/**
 * Mutex: asegura que solo UN /session/refresh este in-flight a la vez.
 * Si 5 requests fallan con 401 simultaneamente, solo se dispara 1 refresh;
 * los otros 4 esperan el resultado y reintentan.
 *
 * Sin esto, 5 refresh calls concurrentes harian que el backend revoque
 * la familia (RFC 9700 reuse detection).
 */
let inFlight: Promise<boolean> | null = null

export async function withRefreshMutex(
  refreshFn: () => Promise<boolean>,
): Promise<boolean> {
  if (inFlight) {
    return inFlight
  }
  inFlight = (async () => {
    try {
      return await refreshFn()
    } finally {
      inFlight = null
    }
  })()
  return inFlight
}
```

## Fetch wrapper con auth interceptor

`src/lib/api-client.ts`:

```typescript
import {env} from './env'
import {useAuthStore} from '@/features/auth/store/use-auth-store'
import {withRefreshMutex} from '@/features/auth/lib/refresh-mutex'

interface FetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  skipAuth?: boolean
  skipRefresh?: boolean
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: number,
    message: string,
    public readonly data?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T = unknown>(
  endpoint: string,
  options: FetchOptions = {},
): Promise<T> {
  const {skipAuth = false, skipRefresh = false, body, headers: extraHeaders, ...rest} = options
  const url = `${env.NEXT_PUBLIC_API_ENDPOINT}${endpoint}`

  const headers = new Headers(extraHeaders)
  headers.set('Content-Type', 'application/json')

  if (!skipAuth) {
    const token = useAuthStore.getState().accessToken
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  const init: RequestInit = {
    ...rest,
    headers,
    // SPA cross-origin: tokens viajan en localStorage + Authorization
    // header. NO se usan cookies (ver decision en encabezado de este doc).
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }

  let response = await fetch(url, init)

  // 401 + tenemos refresh -> intentar rotacion
  if (response.status === 401 && !skipAuth && !skipRefresh) {
    const refreshed = await withRefreshMutex(performRefresh)
    if (refreshed) {
      // Retry con token nuevo
      const newToken = useAuthStore.getState().accessToken
      if (newToken) headers.set('Authorization', `Bearer ${newToken}`)
      response = await fetch(url, {...init, headers})
    } else {
      // Refresh fallo -> logout
      await performLocalLogout()
      throw new ApiError(401, 4011, 'Sesion expirada', null)
    }
  }

  // Parse JSON (puede ser body vacio)
  let data: unknown = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const payload = (data ?? {}) as {error?: string; code?: number; message?: string}
    throw new ApiError(
      response.status,
      payload.code ?? response.status,
      payload.message ?? payload.error ?? `HTTP ${response.status}`,
      data,
    )
  }

  return data as T
}

async function performRefresh(): Promise<boolean> {
  try {
    const refreshToken = useAuthStore.getState().refreshToken
    if (!refreshToken) return false
    const response = await fetch(`${env.NEXT_PUBLIC_API_ENDPOINT}/auth`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        operation: 'session',
        action: 'refresh',
        data: {refresh_token: refreshToken},
      }),
    })
    if (!response.ok) return false
    const {data} = await response.json()
    // Backend rota el refresh: el viejo queda blacklisteado en DynamoDB
    // (family_id detection). Reemplazamos los dos en el store.
    useAuthStore.getState().setAccessToken(data.access_token)
    useAuthStore.getState().setRefreshToken(data.refresh_token)
    return true
  } catch {
    return false
  }
}

async function performLocalLogout(): Promise<void> {
  // Limpiar estado local (sin llamar al backend — el logout server-side
  // se hace explicitamente desde la UI con useLogout)
  useAuthStore.getState().reset()
  // Notificar otras tabs
  const channel = new BroadcastChannel('portfolio_auth')
  channel.postMessage({type: 'LOGOUT'})
  channel.close()
}
```

## Magic link callback (fragment hash)

`src/app/(auth)/callback/page.tsx`:

```tsx
'use client'

import {useEffect, useRef} from 'react'
import {useRouter} from 'next/navigation'
import {useAuthStore} from '@/features/auth/store/use-auth-store'
import {jwtDecode} from 'jwt-decode'
import {toast} from 'sonner'

export default function CallbackPage() {
  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true

    const fragment = window.location.hash.slice(1) // remove '#'
    if (!fragment) {
      toast.error('Link invalido')
      router.replace('/login')
      return
    }

    // El backend redirige con:
    //   /callback#access=<JWT>&refresh=<JWT>&user_id=<X>&email=<Y>
    const params = new URLSearchParams(fragment)
    const accessToken = params.get('access')
    const refreshToken = params.get('refresh')
    const userId = params.get('user_id')
    const email = params.get('email')

    if (!accessToken || !refreshToken || !userId || !email) {
      toast.error('Link incompleto')
      router.replace('/login')
      return
    }

    try {
      // Validar shape del JWT (no firma — eso lo hace el backend)
      jwtDecode<{sub: string; exp: number}>(accessToken)
      setTokens(accessToken, refreshToken, {
        id: userId,
        email,
        status: 'active',
        has_password: false,
        mfa_methods: [],
      })

      // CRITICO: limpiar el fragment ANTES de cualquier navegacion para
      // que el token no quede en window.location.hash ni en el history.
      window.history.replaceState(null, '', '/')
      router.replace('/')
      toast.success('Sesion iniciada')
    } catch {
      toast.error('Token invalido')
      router.replace('/login')
    }
  }, [router, setTokens])

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-muted-foreground">Iniciando sesion...</p>
    </div>
  )
}
```

> El `ran` ref evita doble ejecucion en StrictMode dev. El
> `history.replaceState` borra el fragment del URL/history para que no
> quede expuesto.

## AuthGuard

`src/features/auth/components/auth-guard.tsx`:

```tsx
'use client'

import {useEffect} from 'react'
import {useRouter, usePathname} from 'next/navigation'
import {useAuthStore} from '../store/use-auth-store'
import {useAuthTimer} from '../hooks/use-auth-timer'
import {useMultiTabSync} from '../hooks/use-multi-tab-sync'

export function AuthGuard({children}: {children: React.ReactNode}) {
  const router = useRouter()
  const pathname = usePathname()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  // hooks que mantienen la sesion viva
  useAuthTimer()
  useMultiTabSync()

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`)
    }
  }, [isAuthenticated, router, pathname])

  if (!isAuthenticated()) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Verificando sesion...</p>
      </div>
    )
  }

  return <>{children}</>
}
```

Uso en `(admin)/layout.tsx`:

```tsx
'use client'
import {AuthGuard} from '@/features/auth/components/auth-guard'
import {Sidebar} from '@/features/admin-shell/components/sidebar'
import {Header} from '@/features/admin-shell/components/header'

export default function AdminLayout({children}: {children: React.ReactNode}) {
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

## Auto-refresh proactivo

`src/features/auth/hooks/use-auth-timer.ts`:

```typescript
'use client'

import {useEffect, useRef} from 'react'
import {jwtDecode} from 'jwt-decode'
import {useAuthStore} from '../store/use-auth-store'
import {withRefreshMutex} from '../lib/refresh-mutex'
import {env} from '@/lib/env'

const REFRESH_LEAD = env.NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS

export function useAuthTimer() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const reset = useAuthStore((s) => s.reset)
  const setAccessToken = useAuthStore((s) => s.setAccessToken)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (!accessToken) return

    let exp: number
    try {
      exp = jwtDecode<{exp: number}>(accessToken).exp * 1000
    } catch {
      reset()
      return
    }

    const msUntilRefresh = exp - Date.now() - REFRESH_LEAD
    if (msUntilRefresh <= 0) {
      // Ya esta por expirar o expirado — refresh inmediato
      void doRefresh()
      return
    }

    timerRef.current = setTimeout(doRefresh, msUntilRefresh)

    async function doRefresh() {
      const ok = await withRefreshMutex(async () => {
        const r = await fetch(`${env.NEXT_PUBLIC_API_ENDPOINT}/auth`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          credentials: 'include',
          body: JSON.stringify({operation: 'session', action: 'refresh', data: {}}),
        })
        if (!r.ok) return false
        const {data} = await r.json()
        setAccessToken(data.access_token)
        return true
      })
      if (!ok) reset()
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [accessToken, reset, setAccessToken])

  // Page Visibility: re-check al volver a la tab
  useEffect(() => {
    function onVisibility() {
      if (document.visibilityState !== 'visible') return
      const token = useAuthStore.getState().accessToken
      if (!token) return
      try {
        const exp = jwtDecode<{exp: number}>(token).exp * 1000
        if (Date.now() >= exp - REFRESH_LEAD) {
          // refresh inmediato
          void withRefreshMutex(async () => {
            const r = await fetch(`${env.NEXT_PUBLIC_API_ENDPOINT}/auth`, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              credentials: 'include',
              body: JSON.stringify({operation: 'session', action: 'refresh', data: {}}),
            })
            if (!r.ok) {
              useAuthStore.getState().reset()
              return false
            }
            const {data} = await r.json()
            useAuthStore.getState().setAccessToken(data.access_token)
            return true
          })
        }
      } catch {
        useAuthStore.getState().reset()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [])
}
```

## Multi-tab sync (BroadcastChannel)

`src/features/auth/hooks/use-multi-tab-sync.ts`:

```typescript
'use client'

import {useEffect} from 'react'
import {useAuthStore} from '../store/use-auth-store'

export function useMultiTabSync() {
  useEffect(() => {
    if (typeof BroadcastChannel === 'undefined') return
    const channel = new BroadcastChannel('portfolio_auth')

    channel.onmessage = (event: MessageEvent<{type: 'LOGOUT' | 'TOKEN_REFRESH'; token?: string}>) => {
      if (event.data.type === 'LOGOUT') {
        useAuthStore.getState().reset()
      } else if (event.data.type === 'TOKEN_REFRESH' && event.data.token) {
        useAuthStore.getState().setAccessToken(event.data.token)
      }
    }

    return () => channel.close()
  }, [])
}

// Helper para emitir mensajes desde otros lugares (e.g. logout, refresh)
export function broadcastAuth(message: {type: 'LOGOUT' | 'TOKEN_REFRESH'; token?: string}) {
  if (typeof BroadcastChannel === 'undefined') return
  const channel = new BroadcastChannel('portfolio_auth')
  channel.postMessage(message)
  channel.close()
}
```

## useLogout

`src/features/auth/hooks/use-logout.ts`:

```typescript
'use client'

import {useMutation} from '@tanstack/react-query'
import {useRouter} from 'next/navigation'
import {useQueryClient} from '@tanstack/react-query'
import {apiFetch} from '@/lib/api-client'
import {useAuthStore} from '../store/use-auth-store'
import {broadcastAuth} from './use-multi-tab-sync'
import {toast} from 'sonner'

export function useLogout() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const reset = useAuthStore((s) => s.reset)

  return useMutation({
    mutationFn: async () => {
      // Backend blacklistea la familia (DynamoDB)
      await apiFetch('/auth', {
        method: 'POST',
        body: {operation: 'session', action: 'logout', data: {}},
      }).catch(() => {
        // Si el backend falla, seguimos con el logout local
      })
    },
    onSettled: () => {
      // Limpiar local SIEMPRE (incluso si la llamada al backend fallo)
      reset()
      queryClient.clear()
      // Notificar otras tabs
      broadcastAuth({type: 'LOGOUT'})
      // Redirect
      router.replace('/login')
      toast.info('Sesion cerrada')
    },
  })
}
```

## Tanstack Query setup

`src/providers/query-provider.tsx`:

```tsx
'use client'

import {QueryClient} from '@tanstack/react-query'
import {PersistQueryClientProvider} from '@tanstack/react-query-persist-client'
import {createSyncStoragePersister} from '@tanstack/query-sync-storage-persister'
import {compress, decompress} from 'lz-string'
import {useState, type ReactNode} from 'react'
import {ApiError} from '@/lib/api-client'
import {ReactQueryDevtools} from '@tanstack/react-query-devtools'

export function QueryProvider({children}: {children: ReactNode}) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // No retry en 401/403/422
          if (error instanceof ApiError && [401, 403, 422].includes(error.status)) {
            return false
          }
          return failureCount < 1
        },
      },
      mutations: {retry: 0},
    },
  }))

  const [persister] = useState(() =>
    createSyncStoragePersister({
      storage: typeof window === 'undefined' ? undefined : window.localStorage,
      key: 'portfolio-admin-query',
      serialize: (data) => compress(JSON.stringify(data)),
      deserialize: (data) => JSON.parse(decompress(data) || '{}'),
    }),
  )

  return (
    <PersistQueryClientProvider
      client={client}
      persistOptions={{
        persister,
        maxAge: 24 * 60 * 60 * 1000, // 24h
        // No persistir queries que contienen data sensible (contacts list)
        dehydrateOptions: {
          shouldDehydrateQuery: (query) => {
            if (query.state.status !== 'success') return false
            const key = query.queryKey[0]
            if (key === 'contacts') return false // PII
            if (key === 'events' && query.queryKey[1] === 'list') return false
            return true
          },
        },
      }}
    >
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </PersistQueryClientProvider>
  )
}
```

## Composicion final de providers

`src/providers/root-providers.tsx`:

```tsx
'use client'

import {ReactNode} from 'react'
import {ThemeProvider} from './theme-provider'
import {QueryProvider} from './query-provider'

export function RootProviders({children}: {children: ReactNode}) {
  return (
    <ThemeProvider>
      <QueryProvider>{children}</QueryProvider>
    </ThemeProvider>
  )
}
```

`src/app/layout.tsx`:

```tsx
import type {Metadata} from 'next'
import '@/styles/globals.css'
import {RootProviders} from '@/providers/root-providers'
import {Toaster} from '@/components/ui/sonner'

// Importante: validar env al cargar (fail-fast en build)
import '@/lib/env'

export const metadata: Metadata = {
  title: 'Admin | the-full-stack',
  description: 'Panel admin',
  robots: 'noindex, nofollow',
}

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <RootProviders>{children}</RootProviders>
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  )
}
```

## Endpoints typed (`auth-client.ts`)

Cubre las 26 actions invocables del Lambda `auth` (6 operations). Las
actions de `mfa.*` y `webauthn.*` requieren access JWT (van CON el
Bearer, sin `skipAuth`), salvo: `mfa.recovery-codes-consume` (usa un temp
JWT step=2, `skipAuth: true`) y `webauthn.login-options` /
`webauthn.login-verify` (parte del login sin sesion, `skipAuth: true`).

### Tipos de respuesta

```typescript
// src/features/auth/api/auth-types.ts

// access + refresh + user emitidos al cerrar register/login.
export interface AuthResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}

// Flujo multi-step (register/login). `methods` aparece cuando el user
// tiene MFA: el cliente decide entre totp / webauthn / recovery-codes.
export interface TempTokenResponse {
  temp_token: string
  user_id: string
  expires_in: number
  methods?: ('magic-link' | 'email-code' | 'password' | 'totp' | 'webauthn')[]
}

export interface MfaMethod {
  kind: 'totp' | 'email_code'
  confirmed_at: string | null
  is_preferred: boolean
}

export interface MfaListResponse {
  methods: MfaMethod[]
  webauthn_count: number
  total_mfa: number
}

// El front renderiza el QR desde `otpauth_url`; no llega imagen.
export interface TotpSetupResponse {
  secret_b32: string
  otpauth_url: string
}

// 10 codes Crockford de 10 chars, mostrados UNA sola vez.
export interface RecoveryCodesResponse {
  codes: string[]
}

export interface WebauthnRegisterOptionsResponse {
  challenge_id: string
  options: PublicKeyCredentialCreationOptionsJSON
}

export interface WebauthnLoginOptionsResponse {
  challenge_id: string
  options: PublicKeyCredentialRequestOptionsJSON
}

export interface WebauthnCredential {
  id: string
  nickname: string | null
  last_used_at: string | null
  created_at: string
}
```

> `PublicKeyCredentialCreationOptionsJSON` y
> `PublicKeyCredentialRequestOptionsJSON` son los tipos del DOM
> (`lib.dom.d.ts`). El browser los consume directo con
> `navigator.credentials.create()` / `.get()` tras pasar por
> `PublicKeyCredential.parseCreationOptionsFromJSON()` /
> `.parseRequestOptionsFromJSON()`.

### Cliente

```typescript
// src/features/auth/api/auth-client.ts
import {apiFetch} from '@/lib/api-client'
import type {
  AuthResponse,
  MfaListResponse,
  RecoveryCodesResponse,
  TempTokenResponse,
  TotpSetupResponse,
  WebauthnCredential,
  WebauthnLoginOptionsResponse,
  WebauthnRegisterOptionsResponse,
} from './auth-types'

export const authClient = {
  // --- operation register (3 actions) ---
  registerStart: (data: {
    email: string
    cf_turnstile_response: string
    niche?: string
  }) =>
    apiFetch<{data: TempTokenResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'register', action: 'start', data},
    }),

  // verify-magic-link es un GET callback del backend (302 -> /callback con
  // tokens en fragment hash); el cliente no lo invoca via apiFetch.
  registerVerifyCode: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'register', action: 'verify-code', data},
    }),

  // --- operation login (5 actions) ---
  loginStart: (data: {
    email: string
    cf_turnstile_response: string
    password?: string
    niche?: string
  }) =>
    apiFetch<{data: TempTokenResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'login', action: 'start', data},
    }),

  loginVerifyCode: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'login', action: 'verify-code', data},
    }),

  // Variante 2-step: valida password (argon2). Si el user tiene MFA,
  // devuelve un temp JWT step=2 + `methods` en vez del AuthResponse final.
  loginVerifyPassword: (data: {temp_token: string; password: string}) =>
    apiFetch<{data: AuthResponse | TempTokenResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'login', action: 'verify-password', data},
    }),

  // Paso final de login con MFA TOTP (temp step=2, prev=password|webauthn).
  loginVerifyTotp: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'login', action: 'verify-totp', data},
    }),

  // --- operation verify (2 actions) ---
  setPassword: (data: {password: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'verify', action: 'set-password', data},
    }),

  resendCode: (data: {temp_token: string}) =>
    apiFetch('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'verify', action: 'resend-code', data},
    }),

  // --- operation session (2 actions) ---
  sessionRefresh: (data: {refresh_token: string}) =>
    apiFetch<{data: {access_token: string; refresh_token: string; expires_in: number}}>('/auth', {
      method: 'POST',
      skipAuth: true,
      skipRefresh: true, // critico: este NUNCA debe entrar al mutex
      body: {operation: 'session', action: 'refresh', data},
    }),

  sessionLogout: () =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'session', action: 'logout', data: {}},
    }),

  // --- operation mfa (8 actions) ---
  // Todas requieren access JWT (van con el Bearer) salvo
  // recoveryCodesConsume, que usa un temp JWT step=2 (skipAuth).
  mfaSetupTotp: () =>
    apiFetch<{data: TotpSetupResponse}>('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'setup-totp', data: {}},
    }),

  // Confirma el TOTP recien seteado. El PRIMER metodo MFA revoca la
  // familia de refresh (AC-27): tras esto, refrescar la sesion.
  mfaConfirmTotp: (data: {code: string}) =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'confirm-totp', data},
    }),

  mfaSetupEmailCode: () =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'setup-email-code', data: {}},
    }),

  mfaSetPreferred: (data: {kind: 'totp' | 'email_code'}) =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'set-preferred', data},
    }),

  // Guard MUST_KEEP_ONE_MFA_METHOD: 409 si dejaria total_mfa == 0.
  mfaDisable: (data: {kind: 'totp' | 'email_code'}) =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'disable', data},
    }),

  mfaList: () =>
    apiFetch<{data: MfaListResponse}>('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'list', data: {}},
    }),

  // 10 recovery codes mostrados UNA sola vez.
  mfaRecoveryCodesGenerate: () =>
    apiFetch<{data: RecoveryCodesResponse}>('/auth', {
      method: 'POST',
      body: {operation: 'mfa', action: 'recovery-codes-generate', data: {}},
    }),

  // Consume un recovery code en el login con MFA. Exige un temp JWT
  // step=2 con factor fuerte (password|webauthn): por eso skipAuth +
  // temp_token. 403 RECOVERY_REQUIRES_STRONG_FACTOR si el temp viene de
  // magic-link/email-code.
  mfaRecoveryCodesConsume: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'mfa', action: 'recovery-codes-consume', data},
    }),

  // --- operation webauthn (6 actions) ---
  // register-* y list/delete requieren access JWT; login-* van sin sesion.
  webauthnRegisterOptions: () =>
    apiFetch<{data: WebauthnRegisterOptionsResponse}>('/auth', {
      method: 'POST',
      body: {operation: 'webauthn', action: 'register-options', data: {}},
    }),

  // El PRIMER metodo MFA revoca la familia de refresh (AC-27).
  webauthnRegisterVerify: (data: {
    challenge_id: string
    response: Record<string, unknown>
    nickname?: string
  }) =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'webauthn', action: 'register-verify', data},
    }),

  webauthnLoginOptions: (data: {email: string}) =>
    apiFetch<{data: WebauthnLoginOptionsResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'webauthn', action: 'login-options', data},
    }),

  // sign_count monotonico: clone detection -> 401 + credential disabled.
  webauthnLoginVerify: (data: {
    challenge_id: string
    response: Record<string, unknown>
  }) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'webauthn', action: 'login-verify', data},
    }),

  webauthnListCredentials: () =>
    apiFetch<{data: {credentials: WebauthnCredential[]}}>('/auth', {
      method: 'POST',
      body: {operation: 'webauthn', action: 'list-credentials', data: {}},
    }),

  // Guard MUST_KEEP_ONE_MFA_METHOD. Credential de otro user -> 404.
  webauthnDeleteCredential: (data: {credential_id: string}) =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'webauthn', action: 'delete-credential', data},
    }),
}
```

> El `User` interface (en `use-auth-store.ts`) ya expone
> `mfa_methods: ('totp' | 'webauthn' | 'email_code')[]`: el admin lo
> usa para decidir si pedir un segundo factor en el login y para pintar
> el estado de MFA en `settings/security`.

## Hooks por accion

```typescript
// src/features/auth/hooks/use-register-start.ts
import {useMutation} from '@tanstack/react-query'
import {useRouter} from 'next/navigation'
import {authClient} from '../api/auth-client'
import {useAuthStore} from '../store/use-auth-store'
import {toast} from 'sonner'
import {ApiError} from '@/lib/api-client'

export function useRegisterStart() {
  const router = useRouter()
  const setTempToken = useAuthStore((s) => s.setTempToken)

  return useMutation({
    mutationFn: authClient.registerStart,
    onSuccess: ({data}) => {
      setTempToken(data.temp_token)
      router.push('/verify?flow=register')
      toast.success('Te enviamos un email con un magic-link y un codigo')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.code === 4090) {
        toast.error('Email ya registrado', {description: 'Inicia sesion en su lugar.'})
      } else {
        toast.error(error.message)
      }
    },
  })
}
```

## Flujo de login con MFA

`login.start` (o `login.verify-password` en la variante 2-step) decide si
hay segundo factor:

1. `login.start` con `{email, cf_turnstile_response, password?}`. Si el
   user no tiene MFA y mando `password`, el backend cierra con
   `AuthResponse` (login directo).
2. Si el user tiene MFA, la respuesta es un `TempTokenResponse` step=2 con
   `methods` (subset de `totp` / `webauthn` / + recovery como fallback).
   El admin guarda el `temp_token` y muestra el selector de factor.
3. Segun el metodo elegido:
   - **TOTP** -> `login.verify-totp` con `{code (6 digitos), temp_token}`.
   - **WebAuthn** -> `webauthn.login-options` con `{email}` (devuelve
     `challenge_id` + options) -> `navigator.credentials.get()` ->
     `webauthn.login-verify` con `{challenge_id, response}`.
   - **Recovery code** -> `mfa.recovery-codes-consume` con
     `{code (10 chars), temp_token}`. El temp DEBE venir de un factor
     fuerte (password / webauthn); si viene de magic-link/email-code el
     backend responde `403 RECOVERY_REQUIRES_STRONG_FACTOR`.
4. Cualquiera de los tres devuelve el `AuthResponse` final (access +
   refresh + user). El admin hace `setTokens(...)` y navega al app shell
   (`/` del area protegida).

```text
login.start ──> { sin MFA + password } ──> AuthResponse (login directo)
            └─> { con MFA } ──> temp step=2 + methods
                                   ├─ totp     -> login.verify-totp
                                   ├─ webauthn -> login-options -> get() -> login-verify
                                   └─ recovery -> recovery-codes-consume
                                                  (temp step=2 factor fuerte)
                                   └────────────> AuthResponse final
```

## Setup de MFA en settings

`settings/security` (`/settings/security` en el app shell) gestiona los
metodos con access JWT activo. Patron por metodo:

- **TOTP**: `mfa.setup-totp` -> el front renderiza el QR desde
  `otpauth_url` -> el user ingresa el codigo -> `mfa.confirm-totp`.
- **Email-code**: `mfa.setup-email-code` (activa MFA via email-code).
- **WebAuthn / passkey**: `webauthn.register-options` ->
  `navigator.credentials.create()` -> `webauthn.register-verify` con
  `{challenge_id, response, nickname?}`.
- **Recovery codes**: `mfa.recovery-codes-generate` muestra los 10 codes
  UNA sola vez (el user debe guardarlos antes de cerrar el modal).
- **Preferencia / baja**: `mfa.set-preferred`, `mfa.disable` y
  `webauthn.delete-credential`. El guard `MUST_KEEP_ONE_MFA_METHOD`
  responde `409` si la accion dejaria al user con `total_mfa == 0`.

> AC-27: confirmar el PRIMER metodo MFA (`mfa.confirm-totp`,
> `mfa.setup-email-code` o `webauthn.register-verify`) revoca la familia
> de refresh en el backend. Tras esa accion, el admin fuerza un
> `session.refresh` para obtener un access nuevo (el viejo `iat` queda
> invalidado). `mfa.list` + `webauthn.list-credentials` pintan el estado
> actual de la pantalla.

## Threat model resumido

| Amenaza | Mitigacion implementada |
|---------|--------------------------|
| XSS roba accessToken | Access TTL 15 min. CSP estricta sin `unsafe-inline`/`unsafe-eval`. SRI en third-party scripts. Trusted Types (cuando disponible). |
| XSS roba refreshToken | Misma defensa: CSP + SRI + audit deps. Backup: family_id rotation + reuse detection invalidan el refresh apenas un atacante intenta usarlo en paralelo a la sesion legitima. |
| Refresh token reuse (token stolen) | Family_id rotation backend. Reuse detection → revoke familia entera |
| Concurrent refresh race | Mutex client-side: 1 sola call in-flight |
| CSRF | NO se usan cookies (Bearer auth en Authorization header). Sin cookies cross-origin = sin vector CSRF. |
| Phishing (evilginx MitM) | WebAuthn (passkeys) es origin-bound = inmune. JWT/TOTP NO resisten |
| Magic link leak via Referer | Tokens en fragment hash (NO query). `Referrer-Policy: strict-origin-when-cross-origin` |
| Multi-tab desync | BroadcastChannel `portfolio_auth` + `storage` event listener fallback |
| Logout incompleto | Backend blacklist familia + `queryClient.clear()` + Zustand reset + broadcast |
| Email enumeration (login.start 404 vs 200) | Decision aceptada del backend; mitigado con Turnstile + rate-limit 5/min/IP |
| Tokens persisten en `localStorage` (vector si script malicioso ejecuta) | Defensa primaria: CSP estricta + SRI. Defensa secundaria: access TTL corto + family detection. Decision documentada en encabezado. |

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Persistir `accessToken` con `name` predecible globalmente (ej. `'jwt'`) | Otros scripts del mismo origen pueden leer | Usar `name: 'portfolio-admin-auth'` (namespaced) + CSP estricta |
| Cargar script third-party sin `integrity` (SRI) | Script comprometido lee `localStorage` | SRI obligatorio + allowlist en CSP `script-src` |
| Intentar setear HttpOnly cookie cross-origin (`SameSite=None; Domain=.the-full-stack.com`) | Vector CSRF en los 6 niches publicos | Tokens en `localStorage` (decision documentada arriba) |
| 2 fetch concurrent → 2 refresh | Backend revoca familia | Mutex |
| Magic link `?access=X` | Leak Referer + history | Fragment hash `#access=X` |
| `useEffect` sin `ran` guard en callback | StrictMode dev ejecuta 2 veces | `useRef(false)` + `if (ran.current) return` |
| Olvidar `history.replaceState` post-callback | Tokens visibles en URL | `replaceState(null, '', '/')` |
| `setTimeout` para refresh sin guardar timerRef | Memory leak + dobles refresh | `useRef` + cleanup |
| `BroadcastChannel` sin check de `typeof === 'undefined'` | SSR/build crash | Guard `if (typeof BroadcastChannel === 'undefined') return` |
| Logout que NO llama al backend | Backend no revoca → token sigue valido | Llamar `/auth?session=logout` en `onSettled` |
| Refresh sin `skipRefresh: true` | Recursion infinita en 401 | Marcar `/session/refresh` con `skipRefresh: true` |
| Mostrar mensaje "Email no existe" en login | Email enumeration mas explicita | Confiar en el response del backend (404 + suggest_register) |

[< 03-ui](03-ui.md) | [Siguiente: 05-deploy >](05-deploy.md)
