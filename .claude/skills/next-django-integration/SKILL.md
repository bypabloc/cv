---
name: next-django-integration
description: >
  Next.js 16 SPA + Django DRF integration (JWT via SimpleJWT en localStorage,
  lib/api-client.ts CSR-only, refresh interceptor, CORS). Use when the user
  says "django integration", "JWT", "SimpleJWT", "api client",
  "lib/api-client", "access token", "refresh token", "Authorization Bearer",
  "next-django", "cors next django", "integracion django", "token JWT". More
  keywords: .claude/docs/skills/next-django-integration.md
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
argument-hint: "<endpoint-or-feature>"
---

# Next.js 16 + Django DRF — Integration Patterns

## Arquitectura de auth

```
Browser (cliente)
  ↓ HTML + JS
Next.js (app server, Node 24)
  ↓ Set-Cookie httpOnly
  ↓ fetch desde Server Components/Actions
Django API (api.localhost:9979)
  ↓ TokenAuthentication
PostgreSQL 18
```

## Cookie httpOnly como container del DRF token

NO almacenar el token en `localStorage` (vulnerable a XSS). Usar cookie con flags `__Host-`:

| Flag | Razon |
|------|-------|
| `httpOnly: true` | JS no puede leerla — no afectada por XSS |
| `secure: true` | Solo via HTTPS |
| `sameSite: 'lax'` | Permite navegacion top-level con cookie, bloquea cross-origin POST |
| `path: '/'` | Disponible en toda la app |
| `name: '__Host-auth-token'` | Prefix `__Host-` exige Secure + Path=/ + sin Domain (refuerza scope) |

## lib/api-client.ts — wrapper con auth automatica

```typescript
// dashboard/lib/api-client.ts
import { cookies } from 'next/headers'

const API_BASE = process.env.API_URL ?? 'http://api.localhost:9979/v1'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly fieldErrors?: Record<string, string[]>,
  ) {
    super(message)
  }
}

async function authedFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const cookieStore = await cookies()
  const token = cookieStore.get('__Host-auth-token')?.value
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Token ${token}` }),
      ...init.headers,
    },
    cache: 'no-store',
  })

  if (!res.ok) {
    let body: unknown
    try { body = await res.json() } catch { /* ignore */ }
    const code = (body as { code?: string })?.code ?? `HTTP_${res.status}`
    const message = (body as { error?: string })?.error ?? res.statusText
    const fieldErrors = (body as { errors?: Record<string, string[]> })?.errors
    throw new ApiError(res.status, code, message, fieldErrors)
  }

  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => authedFetch<T>(path, { method: 'GET' }),
  post: <T>(path: string, body: unknown) => authedFetch<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) => authedFetch<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => authedFetch<T>(path, { method: 'DELETE' }),
}
```

## proxy.ts — auth gate ligero

```typescript
// dashboard/proxy.ts (Next 16: REEMPLAZA middleware.ts)
import { type NextRequest, NextResponse } from 'next/server'

const PROTECTED_PREFIXES = ['/items', '/settings', '/']
const AUTH_PREFIXES = ['/auth/login', '/auth/register', '/auth/forgot-password']

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('__Host-auth-token')?.value

  const isAuth = AUTH_PREFIXES.some((p) => pathname.startsWith(p))
  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p)) && !isAuth

  if (isProtected && !token) {
    const url = new URL('/auth/login', request.url)
    url.searchParams.set('next', pathname)
    return NextResponse.redirect(url)
  }

  if (isAuth && token) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.).*)']
}
```

`proxy.ts` solo decide redirect/no-redirect basado en presencia de cookie. Validacion profunda (consultar `/api/v1/auth/verify/`) se hace en `(dashboard)/layout.tsx` server-side.

## Login Server Action setea cookie

```typescript
// modules/auth/actions/login.ts
'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { loginSchema, type LoginInput } from '../schemas/auth.schemas'

const API_BASE = process.env.API_URL ?? 'http://api.localhost:9979/v1'
const COOKIE_NAME = '__Host-auth-token'
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7  // 7 dias

type LoginResult = { ok: true } | { ok: false; error: string; fieldErrors?: Record<string, string[]> }

export async function loginAction(input: LoginInput): Promise<LoginResult> {
  const parsed = loginSchema.safeParse(input)
  if (!parsed.success) {
    return { ok: false, error: 'invalid_input', fieldErrors: parsed.error.flatten().fieldErrors }
  }

  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
    cache: 'no-store',
  })

  if (!res.ok) {
    return { ok: false, error: res.status === 401 ? 'invalid_credentials' : `api_error_${res.status}` }
  }

  const data = (await res.json()) as { token: string; user: { id: string; email: string } }
  const cookieStore = await cookies()
  cookieStore.set(COOKIE_NAME, data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: COOKIE_MAX_AGE,
  })

  redirect('/')
}
```

## Logout

```typescript
// modules/auth/actions/logout.ts
'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export async function logoutAction() {
  const cookieStore = await cookies()
  const token = cookieStore.get('__Host-auth-token')?.value

  if (token) {
    // best-effort: avisar al backend
    await fetch(`${process.env.API_URL}/v1/auth/logout/`, {
      method: 'POST',
      headers: { Authorization: `Token ${token}` },
    }).catch(() => undefined)
  }

  cookieStore.delete('__Host-auth-token')
  redirect('/auth/login')
}
```

## Validacion profunda en layout protegido

```typescript
// app/(dashboard)/layout.tsx — Server Component
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { api } from '@/lib/api-client'
import type { User } from '@/modules/auth/types/auth.types'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies()
  const token = cookieStore.get('__Host-auth-token')?.value
  if (!token) redirect('/auth/login')

  let user: User
  try {
    user = await api.get<User>('/auth/me/')
  } catch {
    cookieStore.delete('__Host-auth-token')
    redirect('/auth/login')
  }

  return <DashboardShell user={user}>{children}</DashboardShell>
}
```

## CORS en Django

`server/config/settings/local.py`:

```python
CORS_ALLOWED_ORIGINS = [
    'http://dashboard.localhost:9979',
    'http://localhost:9979',
]
CORS_ALLOW_CREDENTIALS = True  # IMPRESCINDIBLE para cookies cross-origin
CSRF_TRUSTED_ORIGINS = [
    'http://dashboard.localhost:9979',
    'http://localhost:9979',
]
```

## Variables de entorno

`dashboard/.env.local`:

```bash
API_URL=http://api.localhost:9979/v1                  # server-only
NEXT_PUBLIC_APP_URL=http://dashboard.localhost:9979   # cliente publico
NEXT_PUBLIC_SENTRY_DSN=                                # opcional
```

## Tipos crudos vs internos (snake_case ↔ camelCase)

> Patron de aislamiento del backend, adaptado de
> `debtflow-botox-n02/app/docs/conventions/typescript.md` (seccion "Tipos
> crudos vs tipos internos").

DRF serializa en snake_case (`is_active`, `created_at`). El frontend
prefiere camelCase (`isActive`, `createdAt`). Mezclar ambos en el codigo
del dashboard genera ruido visual y acopla la UI a decisiones del backend.

**Regla**: cuando un endpoint tiene MAS DE 3 campos snake_case o se consume
desde >1 lugar, separar en dos juegos de tipos + un mapper. Para endpoints
triviales (1-3 campos planos), aceptar snake_case directo es OK.

### Estructura recomendada por dominio

```
modules/<X>/
├── api/
│   └── <X>.api.ts            # llama a lib/api-client, retorna tipos crudos
├── types/
│   ├── <X>-api.types.ts      # snake_case (mirror exacto del backend)
│   └── <X>.types.ts          # camelCase (consumido por componentes/stores)
├── mappers/
│   └── <X>.mapper.ts         # mapFromApi + mapToApi
├── queries.ts                # queryOptions (consume mappers)
└── ...
```

### Estado actual del proyecto (2026-05)

Hoy `modules/items/types/item.types.ts` expone `is_active`, `created_at`
directos del backend. Esto es **aceptable mientras el modelo sea trivial**.
Cuando crezca o aparezca un segundo consumidor, refactorizar al patron de
abajo.

### Patron canonico

```ts
// modules/items/types/items-api.types.ts (CRUDO — mirror del backend)
export interface ItemApi {
  id: string
  name: string
  description: string | null
  category: 'general' | 'special'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ItemListApi {
  results: ItemApi[]
  count: number
  next: string | null
  previous: string | null
}
```

```ts
// modules/items/types/items.types.ts (INTERNO — usado por la UI)
export interface Item {
  id: string
  name: string
  description: string | null
  category: 'general' | 'special'
  isActive: boolean
  createdAt: Date           // string ISO -> Date
  updatedAt: Date
}

export interface ItemList {
  results: Item[]
  count: number
  nextPage: number | null   // url paginada -> page number
  previousPage: number | null
}
```

```ts
// modules/items/mappers/items.mapper.ts
import type { Item, ItemList } from '../types/items.types'
import type { ItemApi, ItemListApi } from '../types/items-api.types'

const extractPage = (url: string | null): number | null => {
  if (!url) return null
  const match = url.match(/[?&]page=(\d+)/)
  return match ? Number.parseInt(match[1], 10) : null
}

export function mapItemFromApi(api: ItemApi): Item {
  return {
    id: api.id,
    name: api.name,
    description: api.description,
    category: api.category,
    isActive: api.is_active,
    createdAt: new Date(api.created_at),
    updatedAt: new Date(api.updated_at),
  }
}

export function mapItemListFromApi(api: ItemListApi): ItemList {
  return {
    results: api.results.map(mapItemFromApi),
    count: api.count,
    nextPage: extractPage(api.next),
    previousPage: extractPage(api.previous),
  }
}

// Inverso (para POST/PATCH): omitir campos del backend (id, timestamps)
export type ItemInput = Pick<Item, 'name' | 'description' | 'category' | 'isActive'>

export function mapItemToApi(input: ItemInput): Partial<ItemApi> {
  return {
    name: input.name,
    description: input.description,
    category: input.category,
    is_active: input.isActive,
  }
}
```

```ts
// modules/items/api/items.api.ts (consume tipos CRUDOS)
import { api } from '@/lib/api-client'
import type { ItemApi, ItemListApi } from '../types/items-api.types'

export const itemsApi = {
  list: (page = 1) => api.get<ItemListApi>(`/items/?page=${page}`),
  get: (id: string) => api.get<ItemApi>(`/items/${id}/`),
  create: (input: Partial<ItemApi>) => api.post<ItemApi>('/items/', input),
}
```

```ts
// modules/items/queries.ts (mappea CRUDO → INTERNO via queryOptions)
import { queryOptions } from '@tanstack/react-query'
import { itemsApi } from './api/items.api'
import { mapItemFromApi, mapItemListFromApi } from './mappers/items.mapper'

export const itemsKeys = {
  all: ['items'] as const,
  lists: () => [...itemsKeys.all, 'list'] as const,
  list: (filters: { page: number }) => [...itemsKeys.lists(), filters] as const,
  detail: (id: string) => [...itemsKeys.all, 'detail', id] as const,
}

export const itemsListQuery = (page: number) =>
  queryOptions({
    queryKey: itemsKeys.list({ page }),
    queryFn: async () => mapItemListFromApi(await itemsApi.list(page)),
  })

export const itemDetailQuery = (id: string) =>
  queryOptions({
    queryKey: itemsKeys.detail(id),
    queryFn: async () => mapItemFromApi(await itemsApi.get(id)),
  })
```

```ts
// components/features/items/items-list.tsx (consume tipos INTERNOS)
'use client'
import { useSuspenseQuery } from '@tanstack/react-query'
import { itemsListQuery } from '@/modules/items/queries'

export function ItemsList({ page }: { page: number }) {
  const { data } = useSuspenseQuery(itemsListQuery(page))
  return (
    <ul>
      {data.results.map((item) => (
        <li key={item.id}>
          {item.name} — {item.isActive ? 'activo' : 'inactivo'}
          <time>{item.createdAt.toLocaleDateString('es-CL')}</time>
        </li>
      ))}
    </ul>
  )
}
```

### Beneficios

1. **Aislamiento del backend**: si Django renombra `is_active` →
   `enabled`, solo cambia el mapper y el tipo crudo. Componentes y stores
   intactos.
2. **Type safety**: TS distingue `Item` (interno) de `ItemApi` (crudo). Si
   un componente recibe `ItemApi` por error (ej: alguien hizo bypass del
   mapper), el typecheck falla.
3. **Transformaciones en un solo lugar**: parseo de fechas (`string` →
   `Date`), URLs paginadas a numeros, normalizacion de nulls (`null` ↔
   `undefined`).
4. **Mockear es trivial**: en tests de componentes consumis `Item`
   (interno). En tests de mappers, los inputs son `ItemApi` (crudos). Sin
   union type ambiguo.

### Cuando NO aplicar el patron

- Endpoint con 1-3 campos planos sin transformacion (overkill).
- Endpoint que se consume una sola vez en el codebase y no muta.
- POC / spike (refactorizar despues si la feature sobrevive).

### Convenciones internas que el mapper enforza

| Backend (DRF) | Interno (TS) |
|---------------|--------------|
| `is_active: boolean` | `isActive: boolean` |
| `created_at: string (ISO 8601)` | `createdAt: Date` |
| `next: string \| null` (url paginada) | `nextPage: number \| null` |
| `null` (DRF) | preservar como `null`, no `undefined` (consistencia) |
| `decimal_string: '1234.56'` | `amount: number` (parseo en mapper) |

**Excepcion al snake_case**: identificadores ya estandarizados culturalmente
no se traducen. `RUT`, `RFC`, `DNI` se mantienen como en el backend.

### Plan de migracion para `modules/items/`

Hoy:

```ts
// modules/items/types/item.types.ts (snake_case directo)
export interface Item {
  is_active: boolean
  created_at: string
}
```

Migracion sugerida (cuando se agregue el segundo dominio o el modelo crezca):

1. Renombrar tipo actual a `ItemApi` y mover a `items-api.types.ts`.
2. Crear `Item` (camelCase) en `items.types.ts`.
3. Crear `mappers/items.mapper.ts` con `mapItemFromApi`.
4. Actualizar `queries.ts` para mappear.
5. Buscar consumidores de `is_active`, `created_at` y reemplazar.
6. `python devtools/run.py test_runner --module=dashboard --type=typecheck`
   para confirmar.

## Anti-patterns

- ❌ Usar `localStorage` para token (XSS-vulnerable)
- ❌ `Authorization` header desde cliente (deja el token en JS bundle)
- ❌ CORS `Access-Control-Allow-Origin: *` con `Allow-Credentials: true` (rechazado por browser)
- ❌ Proxy.ts hace fetch a Django (lento, fragil — mover a layout server-side)
- ❌ Olvidar `cache: 'no-store'` en fetch a Django (cache global puede mezclar usuarios)
- ❌ Hardcodear `http://api.localhost:9979` (usar `process.env.API_URL`)
- ❌ Throw error desde la action en vez de retornar discriminated union
- ❌ Mezclar snake_case y camelCase en el mismo modulo (todo crudo o todo interno)
- ❌ Mappear dentro del componente (`item.is_active ?? item.isActive`) — eso es responsabilidad del mapper
- ❌ Usar `as ItemApi` para silenciar TS sin pasar por el mapper

## Verificacion

- [ ] Cookie tiene flags `httpOnly + secure + sameSite + __Host-` prefix
- [ ] Server Action de login setea cookie ANTES de redirect
- [ ] Server Action de logout limpia cookie
- [ ] proxy.ts solo verifica presencia, no profundidad
- [ ] Layout `(dashboard)` valida contra Django + redirect si invalido
- [ ] api-client centralizado (NO `fetch()` esparcido en components)
- [ ] Test cubre 200, 401, 403, 500 paths
