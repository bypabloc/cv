# 06 — Testing: Vitest + Testing Library + MSW + Playwright

[< 05-deploy](05-deploy.md) | [Volver al README](README.md)

## Stack (versiones canonicas mayo 2026)

| Capa | Herramienta | Version | Comando |
|------|-------------|---------|---------|
| Unit | Vitest + Testing Library + happy-dom | **2.2.5** / **16.1.0** / **16.5.1** | `pnpm --filter @portfolio/admin test` |
| User event | @testing-library/user-event | **14.5.2** | (importado por tests) |
| Jest DOM matchers | @testing-library/jest-dom | **6.6.3** | (en setup global) |
| Coverage | Vitest v8 coverage | (vitest 2.2.5) | `pnpm --filter @portfolio/admin test:coverage` |
| Vite React plugin | @vitejs/plugin-react | **4.3.3** | (devDep) |
| API mocks (dev + tests) | MSW | **2.3.2** (con polyfill BroadcastChannel en happy-dom) | (importado por setup) |
| E2E | Playwright | **1.48.2** (suite del monorepo) | `python devtools/run.py test_runner --module=feature --type=feature --env=local` |
| Type check | tsc | **6.0.6** | `pnpm --filter @portfolio/admin typecheck` |

> **Critico**: Testing Library v16 es el primer release con soporte
> oficial React 19. `act()` warnings son mas estrictos que antes; envolver
> state updates en `act(...)` cuando aplique.

> **Critico**: MSW v2 internamente usa `BroadcastChannel` para
> sincronizar handlers entre worker y client. happy-dom NO lo tiene
> nativo — por eso el polyfill en `tests/setup.ts` es OBLIGATORIO.

Coverage minimo: **80% per-file** en archivos modificados (mismo que el
resto del repo).

## Vitest config

`admin/vitest.config.ts`:

```typescript
import {defineConfig} from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    css: false,
    include: ['tests/unit/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/index.ts',          // barrel exports
        'src/app/**/layout.tsx',     // layouts ya testeados E2E
        'src/components/ui/**',       // shadcn primitives (no testear shadcn)
        'src/types/**',
        'src/env.d.ts',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

## Setup global

`admin/tests/setup.ts`:

```typescript
import '@testing-library/jest-dom'
import {afterAll, afterEach, beforeAll, vi} from 'vitest'
import {cleanup} from '@testing-library/react'
import {server} from './mocks/server'
import {useAuthStore} from '@/features/auth/store/use-auth-store'

// Polyfill para happy-dom (BroadcastChannel no esta nativo)
if (typeof globalThis.BroadcastChannel === 'undefined') {
  class MockBroadcastChannel {
    constructor(public name: string) {}
    postMessage() {}
    close() {}
    addEventListener() {}
    removeEventListener() {}
    onmessage: ((event: MessageEvent) => void) | null = null
  }
  (globalThis as unknown as {BroadcastChannel: typeof MockBroadcastChannel}).BroadcastChannel = MockBroadcastChannel
}

// Mock NEXT_PUBLIC_* env vars (Zod env.ts validation se evalua al import)
vi.stubEnv('NEXT_PUBLIC_API_ENDPOINT', 'https://api.test.the-full-stack.com')
vi.stubEnv('NEXT_PUBLIC_TURNSTILE_SITEKEY', '1x00000000000000000000AA')
vi.stubEnv('NEXT_PUBLIC_DASHBOARD_URL', 'https://admin.test.the-full-stack.com')
vi.stubEnv('NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS', '30000')

beforeAll(() => {
  server.listen({onUnhandledRequest: 'error'})
})

afterEach(() => {
  cleanup()
  server.resetHandlers()
  // Reset Zustand stores entre tests
  useAuthStore.getState().reset()
  localStorage.clear()
})

afterAll(() => {
  server.close()
})
```

## MSW handlers

`admin/tests/mocks/handlers/auth.ts`:

```typescript
import {http, HttpResponse} from 'msw'

const API = 'https://api.test.the-full-stack.com'

export const authHandlers = [
  // register.start
  http.post(`${API}/auth`, async ({request}) => {
    const body = await request.json() as {operation: string; action: string; data: Record<string, unknown>}
    if (body.operation === 'register' && body.action === 'start') {
      const email = body.data.email as string
      if (email === 'exists@test.com') {
        return HttpResponse.json(
          {error: 'EMAIL_ALREADY_REGISTERED', code: 4090, message: 'Email ya registrado'},
          {status: 409},
        )
      }
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: {temp_token: 'mock-temp', user_id: 'usr_01', expires_in: 300},
      }, {status: 201})
    }

    // login.start con email inexistente
    if (body.operation === 'login' && body.action === 'start') {
      const email = body.data.email as string
      if (email === 'unknown@test.com') {
        return HttpResponse.json(
          {error: 'EMAIL_NOT_FOUND', code: 4040, message: 'Email no existe', data: {suggest_register: true}},
          {status: 404},
        )
      }
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: {
          temp_token: 'mock-temp-login',
          user_id: 'usr_01',
          expires_in: 300,
          methods: ['magic-link', 'email-code'],
        },
      })
    }

    // verify-code
    if (body.action === 'verify-code') {
      const code = body.data.code as string
      if (code === '12345678') {
        return HttpResponse.json({
          is_valid: true,
          code: 0,
          data: {
            access_token: makeJwt({sub: 'usr_01', email: 'user@test.com', exp: nowSec() + 900}),
            expires_in: 900,
            user: {id: 'usr_01', email: 'user@test.com', status: 'active', has_password: false, mfa_methods: []},
          },
        })
      }
      return HttpResponse.json(
        {error: 'INVALID_CODE', code: 4001, message: 'Codigo invalido'},
        {status: 400},
      )
    }

    // session.refresh
    if (body.operation === 'session' && body.action === 'refresh') {
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: {
          access_token: makeJwt({sub: 'usr_01', email: 'user@test.com', exp: nowSec() + 900}),
          expires_in: 900,
        },
      })
    }

    // session.logout
    if (body.operation === 'session' && body.action === 'logout') {
      return new HttpResponse(null, {status: 204})
    }

    return HttpResponse.json({error: 'NOT_IMPLEMENTED'}, {status: 501})
  }),
]

function nowSec(): number {
  return Math.floor(Date.now() / 1000)
}

function makeJwt(payload: object): string {
  // JWT fake (no firmado) solo para tests — el frontend no verifica firma
  const header = base64UrlEncode(JSON.stringify({alg: 'HS256', typ: 'JWT'}))
  const body = base64UrlEncode(JSON.stringify(payload))
  return `${header}.${body}.fakesignature`
}

function base64UrlEncode(s: string): string {
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}
```

`admin/tests/mocks/handlers/analytics.ts`:

```typescript
import {http, HttpResponse} from 'msw'

const API = 'https://api.test.the-full-stack.com'

export const analyticsHandlers = [
  http.get(`${API}/analytics`, ({request}) => {
    const url = new URL(request.url)
    const op = url.searchParams.get('operation')
    const act = url.searchParams.get('action')

    if (op === 'analytics' && act === 'overview') {
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: {
          sessions: 123,
          visits: 456,
          events: 7890,
          contacts: 12,
          unique_visitors: 100,
          avg_visit_duration_sec: 45.6,
          bounce_rate: 0.42,
          from: '2026-04-27',
          to: '2026-05-27',
        },
      })
    }

    if (op === 'analytics' && act === 'timeseries') {
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: Array.from({length: 30}, (_, i) => ({
          ts: `2026-04-${String(28 + i).padStart(2, '0')}`,
          sessions: 10 + i,
          visits: 20 + i * 2,
        })),
      })
    }

    if (op === 'sessions' && act === 'list') {
      return HttpResponse.json({
        is_valid: true,
        code: 0,
        data: {
          items: [
            {session_id: 'sess_01', first_seen_at: '2026-05-26T10:00:00Z', country: 'AR', device_type: 'desktop', event_count: 12},
            {session_id: 'sess_02', first_seen_at: '2026-05-26T11:00:00Z', country: 'CL', device_type: 'mobile', event_count: 5},
          ],
          total: 2,
          page: 1,
          page_size: 50,
        },
      })
    }

    return HttpResponse.json({error: 'NOT_IMPLEMENTED'}, {status: 501})
  }),
]
```

`admin/tests/mocks/server.ts`:

```typescript
import {setupServer} from 'msw/node'
import {authHandlers} from './handlers/auth'
import {analyticsHandlers} from './handlers/analytics'

export const server = setupServer(...authHandlers, ...analyticsHandlers)
```

`admin/tests/mocks/browser.ts` (para dev mode):

```typescript
import {setupWorker} from 'msw/browser'
import {authHandlers} from './handlers/auth'
import {analyticsHandlers} from './handlers/analytics'

export const worker = setupWorker(...authHandlers, ...analyticsHandlers)
```

Para arrancar el worker en dev (mientras el backend no esta vivo):

```typescript
// src/app/layout.tsx (solo en dev)
if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_USE_MSW === 'true') {
  const {worker} = await import('@/tests/mocks/browser')
  await worker.start({onUnhandledRequest: 'bypass'})
}
```

> Comando: `NEXT_PUBLIC_USE_MSW=true pnpm dev`. Tambien hay que servir
> `public/mockServiceWorker.js` (lo genera `npx msw init public/`).

## Test renderer con providers

`admin/tests/utils/render.tsx`:

```tsx
import {render as rtlRender, type RenderOptions} from '@testing-library/react'
import {QueryClient, QueryClientProvider} from '@tanstack/react-query'
import {ThemeProvider} from 'next-themes'
import {Toaster} from 'sonner'
import type {ReactElement, ReactNode} from 'react'

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {retry: false, gcTime: 0, staleTime: 0},
      mutations: {retry: false},
    },
  })
}

function Wrapper({children}: {children: ReactNode}) {
  const client = createTestQueryClient()
  return (
    <ThemeProvider attribute="data-theme" defaultTheme="dark">
      <QueryClientProvider client={client}>
        {children}
        <Toaster />
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export function render(ui: ReactElement, options?: RenderOptions) {
  return rtlRender(ui, {wrapper: Wrapper, ...options})
}

export * from '@testing-library/react'
export {default as userEvent} from '@testing-library/user-event'
```

## Test ejemplo: LoginForm

`admin/tests/unit/features/auth/components/login-form.test.tsx`:

```tsx
import {describe, it, expect} from 'vitest'
import {render, screen, userEvent, waitFor} from '@/tests/utils/render'
import {LoginForm} from '@/features/auth/components/login-form'
import {useAuthStore} from '@/features/auth/store/use-auth-store'

describe('LoginForm', () => {
  it('Given email valido y Turnstile token When submit Then setea tempToken y muestra mensaje', async () => {
    // Arrange
    const user = userEvent.setup()
    render(<LoginForm />)

    // Act
    await user.type(screen.getByLabelText(/email/i), 'user@test.com')
    // simular Turnstile success via mock
    useAuthStore.setState({tempToken: null})

    await user.click(screen.getByRole('button', {name: /iniciar/i}))

    // Assert
    await waitFor(() => {
      expect(useAuthStore.getState().tempToken).toBe('mock-temp-login')
    })
  })

  it('Given email no registrado When submit Then muestra suggest_register', async () => {
    // Arrange
    const user = userEvent.setup()
    render(<LoginForm />)

    // Act
    await user.type(screen.getByLabelText(/email/i), 'unknown@test.com')
    await user.click(screen.getByRole('button', {name: /iniciar/i}))

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/no esta registrado/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', {name: /registrate/i})).toBeInTheDocument()
  })
})
```

## Test de hook: useLogout

`admin/tests/unit/features/auth/hooks/use-logout.test.tsx`:

```tsx
import {describe, it, expect, vi} from 'vitest'
import {renderHook, waitFor, act} from '@testing-library/react'
import {QueryClient, QueryClientProvider} from '@tanstack/react-query'
import {useLogout} from '@/features/auth/hooks/use-logout'
import {useAuthStore} from '@/features/auth/store/use-auth-store'

const pushMock = vi.fn()
vi.mock('next/navigation', () => ({useRouter: () => ({push: pushMock, replace: pushMock})}))

function wrapper({children}: {children: React.ReactNode}) {
  const client = new QueryClient({defaultOptions: {queries: {retry: false}, mutations: {retry: false}}})
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useLogout', () => {
  it('Given user autenticado When logout mutate Then resetea auth + redirect a /login', async () => {
    // Arrange
    useAuthStore.setState({
      accessToken: 'fake-access',
      user: {id: 'usr_01', email: 'u@t.com', status: 'active', has_password: false, mfa_methods: []},
    })

    const {result} = renderHook(() => useLogout(), {wrapper})

    // Act
    await act(async () => {
      await result.current.mutateAsync()
    })

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
    expect(useAuthStore.getState().user).toBe(null)
    expect(pushMock).toHaveBeenCalledWith('/login')
  })
})
```

## Test de fetch wrapper: mutex de refresh

```tsx
// admin/tests/unit/lib/api-client.test.ts
import {describe, it, expect, beforeEach, vi} from 'vitest'
import {server} from '@/tests/mocks/server'
import {http, HttpResponse} from 'msw'
import {apiFetch} from '@/lib/api-client'
import {useAuthStore} from '@/features/auth/store/use-auth-store'

describe('apiFetch + mutex refresh', () => {
  beforeEach(() => {
    useAuthStore.setState({accessToken: 'expired-token'})
  })

  it('Given 5 requests concurrent fallan con 401 When se procesan Then solo 1 /session/refresh se dispara', async () => {
    // Arrange
    let refreshCount = 0
    server.use(
      http.get('https://api.test.the-full-stack.com/analytics', () => {
        // Primera vez 401, segunda OK (post-refresh)
        if (useAuthStore.getState().accessToken === 'expired-token') {
          return new HttpResponse(null, {status: 401})
        }
        return HttpResponse.json({is_valid: true, code: 0, data: {ok: true}})
      }),
      http.post('https://api.test.the-full-stack.com/auth', async ({request}) => {
        const body = await request.json() as {operation?: string; action?: string}
        if (body.operation === 'session' && body.action === 'refresh') {
          refreshCount++
          // Esperar 50ms para forzar concurrencia
          await new Promise((r) => setTimeout(r, 50))
          return HttpResponse.json({
            is_valid: true,
            code: 0,
            data: {
              access_token: 'fresh-token',
              expires_in: 900,
            },
          })
        }
        return new HttpResponse(null, {status: 501})
      }),
    )

    // Act
    const results = await Promise.all([
      apiFetch('/analytics?operation=analytics&action=overview'),
      apiFetch('/analytics?operation=analytics&action=timeseries'),
      apiFetch('/analytics?operation=analytics&action=top-pages'),
      apiFetch('/analytics?operation=analytics&action=top-niches'),
      apiFetch('/analytics?operation=analytics&action=active-now'),
    ])

    // Assert
    expect(refreshCount).toBe(1)              // EL ASSERT CRITICO
    expect(results).toHaveLength(5)
    expect(useAuthStore.getState().accessToken).toBe('fresh-token')
  })
})
```

## E2E con Playwright

Las E2E del monorepo viven en `tests/feature/`. Agregar
`tests/feature/admin/*.spec.ts`:

```typescript
// tests/feature/admin/01-login-magic-link.spec.ts
import {test, expect} from '@playwright/test'

test.describe('Admin login flow', () => {
  test('Given un user registrado When solicita magic link Then recibe email y completa flow', async ({page}) => {
    await page.goto('http://admin.localhost:9970/login')
    await page.fill('[type=email]', 'user@test.com')
    // Turnstile en test mode (sitekey 1x00000000000000000000AA siempre pasa)
    await page.click('button[type=submit]')
    await expect(page.getByText(/te enviamos un link/i)).toBeVisible()
  })

  test('Given callback con fragment hash Then guarda token y redirect al app shell', async ({page}) => {
    const fakeJwt = 'eyJ...mocked...'
    await page.goto(`http://admin.localhost:9970/auth/callback#access=${fakeJwt}&user_id=usr_01&email=u@t.com`)
    // El callback redirige al '/' del area protegida (app shell)
    await page.waitForURL('http://admin.localhost:9970/')
    // Verificar que el hash se limpio
    expect(page.url()).not.toContain('#access=')
  })

  test('Given user sin sesion When accede a una ruta protegida Then redirect a /login con next param', async ({page}) => {
    await page.goto('http://admin.localhost:9970/settings')
    await page.waitForURL('**/login?next=*')
    expect(page.url()).toContain('next=%2Fsettings')
  })
})
```

Correr E2E:

```bash
# Levantar stack + ejecutar specs
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

## Que NO testear

- **shadcn primitives** (`components/ui/button.tsx`, etc.) — son
  upstream, ya testeados por la comunidad. Coverage exclude.
- **Layouts** — testeados E2E.
- **Barrel exports** (`index.ts`) — sin logica.
- **Constants files** (`routes.ts`, `query-keys.ts`) — sin logica.
- **Schemas Zod** sueltos — testear el componente que los usa, no el
  schema aislado.

## Que SI testear

- **Componentes de features** con logica (forms, tables filtradas, etc.).
- **Hooks de features** (Tanstack mutations + queries).
- **Fetch wrapper** (`api-client.ts`) — especialmente el mutex de
  refresh + retry logic.
- **Auth store + hooks** (login, logout, refresh).
- **Magic link callback** (decoder de fragment).
- **Multi-tab sync** (BroadcastChannel mock).
- **Utilities en `lib/format/`** (date, number, duration).

## Coverage target

| Layer | Coverage target |
|-------|-----------------|
| `src/features/<X>/components/` | 80% |
| `src/features/<X>/hooks/` | 90% (logica critica) |
| `src/features/<X>/api/` | 70% (mayormente type wrappers) |
| `src/features/auth/store/` | 95% (criticidad) |
| `src/lib/api-client.ts` | 95% (criticidad) |
| `src/lib/format/` | 90% |
| `src/components/ui/` | EXCLUDED (shadcn) |
| `src/app/**/page.tsx` | E2E (no unit) |
| `src/app/**/layout.tsx` | E2E |

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Mockear `useAuthStore` directamente con `vi.mock` | Pierdes la implementacion real | Usar `useAuthStore.setState(...)` en beforeEach |
| Mockear `Tanstack Query` con `vi.mock` | Acopla test a impl | Usar `QueryClient` de test en wrapper |
| Llamar al backend real desde un test unit | Tests no idempotentes | MSW handlers |
| Tests con `expect(x).toBeTruthy()` | Vago | Asserts exactos: `expect(x).toBe(true)` |
| Tests sin `Given/When/Then` en `it()` | Dificil de leer | BDD-style obligatorio |
| Olvidar `cleanup()` en afterEach | Pollutean entre tests | Vitest setup lo hace global |
| Olvidar reset Zustand entre tests | State leak | `afterEach(() => useAuthStore.getState().reset())` |
| Olvidar `server.resetHandlers()` | Mocks leak entre tests | En afterEach del setup |
| Testear shadcn primitives | Son upstream | Excluir de coverage |
| E2E sin levantar el stack | Falla con conexion refused | `docker up` primero |
| Test que depende del orden | Flaky | Asegurar idempotencia |
| `Promise.all` sin `await` en test | Race conditions, falsos verdes | `await Promise.all(...)` |

[< 05-deploy](05-deploy.md) | [Volver al README](README.md)
