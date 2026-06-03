# 02 — Bug 1: sesion no persiste tras reload (bootstrap race)

[<- 01](01-contexto-y-decision.md) | [Bug 2 ->](03-bug-cors-authorization.md)

Solo frontend (admin). NO redeploy backend.

## Causa raiz

`auth-guard.tsx` monta `useAuthTimer()` + `useProtectedRoute()` en el mismo
render. Tras reload `accessToken === null` (memoria) ->
`useProtectedRoute.isAuthenticated()` sincrono devuelve `false` -> su
`useEffect` hace `router.replace(loginWithNext(pathname))` ANTES de que el
`doRefresh()` async de `useAuthTimer` termine. Ademas zustand `persist`
hidrata localStorage async (primer render puede leer `refreshToken=null`).

## Diseno

Flag `bootstrapping` transient (default `true`, NO persistido). `useAuthTimer`
es el dueno del cierre del flag (ya dispara el refresh del bootstrap). Un gate
de hidratacion (`useAuthBootstrap`) espera `persist.hasHydrated()`.
`useProtectedRoute` NO redirige mientras `bootstrapping === true`.

## Archivos

- `admin/src/features/auth/store/use-auth-store.ts` — `bootstrapping: boolean`
  (default `true`) + `setBootstrapping`. NO en `partialize` (no se persiste).
- `admin/src/features/auth/hooks/use-auth-timer.ts` — en el bootstrap branch
  (`if (!accessToken)`): sin refresh vigente -> `setBootstrapping(false)`
  (return); refresh vigente -> `doRefresh().then(ok => { setBootstrapping(false);
  if (!ok) reset(); })`.
- `admin/src/features/auth/hooks/use-auth-bootstrap.ts` (NUEVO) — gate de
  hidratacion: si `persist.hasHydrated()` evaluar ya, si no suscribir
  `onFinishHydration` (con cleanup); si tras hidratar no hay refresh vigente,
  `setBootstrapping(false)`.
- `admin/src/features/auth/hooks/use-protected-route.ts` — leer `bootstrapping`;
  redirigir solo `if (!bootstrapping && !authed)`; agregar a deps.
- `admin/src/features/auth/components/auth-guard.tsx` — montar
  `useAuthBootstrap()`; placeholder mientras `bootstrapping || !authed`.

## Edge-cases

- **Hidratacion zustand**: sin `hasHydrated()`/`onFinishHydration` el primer
  render lee `refreshToken=null` y redirige por error.
- **StrictMode (doble effect en dev)**: `onFinishHydration` puede registrar 2
  callbacks; usar cleanup que des-suscribe.
- **Refresh expirado**: `useAuthTimer` ya valida `refreshExpiry > Date.now()`
  -> redirect inmediato, sin intentar refresh.
- **Multi-tab**: `useMultiTabSync` setea `accessToken` via broadcast; el flag
  se cierra igual cuando `useAuthTimer` ve el access.

## Tests (Vitest + Testing Library, mirror en `admin/tests/unit/`)

- `features/auth/store/use-auth-store.test.ts`: `bootstrapping` default true +
  setter + NO persistido [AC-4].
- `features/auth/hooks/use-protected-route.test.tsx`: bootstrapping=true sin
  access -> no redirige; false sin access -> redirige [AC-1/2].
- `features/auth/components/auth-guard.test.tsx`: reload con refresh vigente ->
  "Verificando..." + no redirect + children tras refresh OK [AC-1]; sin
  refresh -> redirect [AC-2]; refresh falla -> redirect [AC-3].
- `features/auth/hooks/use-auth-bootstrap.test.tsx` (NUEVO): hasHydrated
  true/false, refresh vigente/expirado/ausente.
- Revisar `use-auth-timer.test.tsx` + `*-branches.test.tsx`: los nuevos
  `setBootstrapping` no rompen asserts.
