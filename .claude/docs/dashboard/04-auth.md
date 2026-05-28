# 04 — Auth: JWT + Tanstack Query + Zustand + magic link + BroadcastChannel

[< 03-ui](03-ui.md) | [Siguiente: 05-deploy >](05-deploy.md)

## Resumen del flujo

El dashboard consume el Lambda `auth` de los planes 01-02 del repo. Tres
tipos de JWT (temp 5min rolling, access 15min, refresh 30dias con
family_id rotation). Storage:

- **access**: Zustand in-memory (NO persistido — XSS = 15 min de exposicion max).
- **refresh**: HttpOnly cookie (preferido — backend setea
  `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/`)
  o `localStorage` con CSP estricta (fallback documentado).
- **temp**: in-memory durante el flujo de registro/login multi-step.

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
  // in-memory ONLY (no persist)
  accessToken: string | null
  tempToken: string | null
  refreshExpiry: number | null  // epoch ms del exp del refresh actual

  // persisted (solo el user, para skeleton inicial)
  user: User | null

  // actions
  setAccessToken: (token: string | null) => void
  setTempToken: (token: string | null) => void
  setUser: (user: User | null) => void
  setRefreshExpiry: (exp: number | null) => void
  reset: () => void

  // derived
  isAuthenticated: () => boolean
  isAccessExpired: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      tempToken: null,
      refreshExpiry: null,
      user: null,

      setAccessToken: (token) => set({accessToken: token}),
      setTempToken: (token) => set({tempToken: token}),
      setUser: (user) => set({user}),
      setRefreshExpiry: (exp) => set({refreshExpiry: exp}),

      reset: () => set({
        accessToken: null,
        tempToken: null,
        refreshExpiry: null,
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
      name: 'portfolio-dashboard-auth',
      storage: createJSONStorage(() => localStorage),
      // Solo persistir el user (UI skeleton). NUNCA accessToken ni tempToken.
      partialize: (state) => ({user: state.user, refreshExpiry: state.refreshExpiry}),
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
    credentials: 'include', // para HttpOnly cookies (refresh token)
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
    const response = await fetch(`${env.NEXT_PUBLIC_API_ENDPOINT}/auth`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'include', // cookie HttpOnly refresh_token
      body: JSON.stringify({operation: 'session', action: 'refresh', data: {}}),
    })
    if (!response.ok) return false
    const {data} = await response.json()
    useAuthStore.getState().setAccessToken(data.access_token)
    // El backend ya rotaria la HttpOnly cookie del refresh
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
  const setAccessToken = useAuthStore((s) => s.setAccessToken)
  const setUser = useAuthStore((s) => s.setUser)
  const setRefreshExpiry = useAuthStore((s) => s.setRefreshExpiry)
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

    const params = new URLSearchParams(fragment)
    const accessToken = params.get('access')
    const userId = params.get('user_id')
    const email = params.get('email')
    const refreshExp = params.get('refresh_exp') // epoch seconds

    if (!accessToken) {
      toast.error('Link sin token')
      router.replace('/login')
      return
    }

    try {
      // Validar shape del JWT (no firma — eso lo hace el backend)
      const payload = jwtDecode<{sub: string; email: string; exp: number}>(accessToken)
      setAccessToken(accessToken)
      setUser({
        id: payload.sub,
        email: payload.email,
        status: 'active',
        has_password: false,
        mfa_methods: [],
      })
      if (refreshExp) {
        setRefreshExpiry(Number.parseInt(refreshExp, 10) * 1000)
      }

      // CRITICO: limpiar el fragment ANTES de cualquier navegacion
      window.history.replaceState(null, '', '/dashboard')
      router.replace('/dashboard')
      toast.success('Sesion iniciada')
    } catch {
      toast.error('Token invalido')
      router.replace('/login')
    }
  }, [router, setAccessToken, setUser, setRefreshExpiry])

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

Uso en `(dashboard)/layout.tsx`:

```tsx
'use client'
import {AuthGuard} from '@/features/auth/components/auth-guard'
import {Sidebar} from '@/features/dashboard-shell/components/sidebar'
import {Header} from '@/features/dashboard-shell/components/header'

export default function DashboardLayout({children}: {children: React.ReactNode}) {
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
      key: 'portfolio-dashboard-query',
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
  title: 'Dashboard | the-full-stack',
  description: 'Admin dashboard',
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

```typescript
// src/features/auth/api/auth-client.ts
import {apiFetch} from '@/lib/api-client'
import type {User} from '../store/use-auth-store'

export interface AuthResponse {
  access_token: string
  expires_in: number
  user: User
}

export interface TempTokenResponse {
  temp_token: string
  user_id: string
  expires_in: number
  methods?: ('magic-link' | 'email-code' | 'password' | 'totp' | 'webauthn')[]
}

export const authClient = {
  registerStart: (data: {email: string; cf_turnstile_response: string}) =>
    apiFetch<{data: TempTokenResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'register', action: 'start', data},
    }),

  registerVerifyCode: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'register', action: 'verify-code', data},
    }),

  loginStart: (data: {email: string; cf_turnstile_response: string; password?: string}) =>
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

  loginVerifyTotp: (data: {code: string; temp_token: string}) =>
    apiFetch<{data: AuthResponse}>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: {operation: 'login', action: 'verify-totp', data},
    }),

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

  sessionRefresh: () =>
    apiFetch<{data: {access_token: string; expires_in: number}}>('/auth', {
      method: 'POST',
      skipAuth: true,
      skipRefresh: true, // critico: este NUNCA debe entrar al mutex
      body: {operation: 'session', action: 'refresh', data: {}},
    }),

  sessionLogout: () =>
    apiFetch('/auth', {
      method: 'POST',
      body: {operation: 'session', action: 'logout', data: {}},
    }),
}
```

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

## Threat model resumido

| Amenaza | Mitigacion implementada |
|---------|--------------------------|
| XSS roba accessToken | Access in-memory, 15 min TTL. CSP estricta sin `unsafe-inline` (scripts) |
| XSS roba refreshToken | HttpOnly cookie inaccesible a JS (preferido). Fallback: localStorage + Trusted Types + audit deps |
| Refresh token reuse (token stolen) | Family_id rotation backend. Reuse detection → revoke familia entera |
| Concurrent refresh race | Mutex client-side: 1 sola call in-flight |
| CSRF | Bearer auth (no cookies para access). Refresh cookie `SameSite=Strict` |
| Phishing (evilginx MitM) | WebAuthn (plan 02) es origin-bound = inmune. JWT/TOTP NO resisten |
| Magic link leak via Referer | Tokens en fragment hash (NO query). `Referrer-Policy: strict-origin-when-cross-origin` |
| Multi-tab desync | BroadcastChannel `portfolio_auth` |
| Logout incompleto | Backend blacklist familia + `queryClient.clear()` + Zustand reset + broadcast |
| Email enumeration (login.start 404 vs 200) | Decision aceptada del backend; mitigado con Turnstile + rate-limit 5/min/IP |

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Persistir `accessToken` en Zustand `persist()` | XSS = robo total | Solo `user` y `refreshExpiry` en partialize |
| `localStorage.setItem('jwt', token)` | XSS roba | Zustand in-memory |
| 2 fetch concurrent → 2 refresh | Backend revoca familia | Mutex |
| Magic link `?access=X` | Leak Referer + history | Fragment hash `#access=X` |
| `useEffect` sin `ran` guard en callback | StrictMode dev ejecuta 2 veces | `useRef(false)` + `if (ran.current) return` |
| Olvidar `history.replaceState` post-callback | Tokens visibles en URL | `replaceState(null, '', '/dashboard')` |
| `setTimeout` para refresh sin guardar timerRef | Memory leak + dobles refresh | `useRef` + cleanup |
| `BroadcastChannel` sin check de `typeof === 'undefined'` | SSR/build crash | Guard `if (typeof BroadcastChannel === 'undefined') return` |
| Logout que NO llama al backend | Backend no revoca → token sigue valido | Llamar `/auth?session=logout` en `onSettled` |
| Refresh sin `skipRefresh: true` | Recursion infinita en 401 | Marcar `/session/refresh` con `skipRefresh: true` |
| Mostrar mensaje "Email no existe" en login | Email enumeration mas explicita | Confiar en el response del backend (404 + suggest_register) |

[< 03-ui](03-ui.md) | [Siguiente: 05-deploy >](05-deploy.md)
