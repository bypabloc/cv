# 01 — Contexto, solucion y criterios de aceptacion

[<- README](README.md) | [Bug 1 ->](02-bug-sesion-bootstrap.md)

## 1. Contexto / Problema

El usuario reporto 4 bugs tras usar el admin
(`admin.portfolio.dev.the-full-stack.com`) contra el backend serverless en
dev. Cada uno verificado en codigo + curl real.

1. **La sesion NO persiste tras reload.** Al recargar, el admin rebota al
   login aunque haya sesion valida. Race de bootstrap: tras reload
   `accessToken` esta solo en memoria (`null`); `AuthGuard` monta
   `useAuthTimer` (dispara `doRefresh()` ASYNC desde el refresh persistido) Y
   `useProtectedRoute` (evalua `isAuthenticated()` SINCRONO -> `false` ->
   `router.replace('/login')` INMEDIATO). El redirect sincrono gana al refresh
   async. No hay un estado "bootstrapping" que retenga el redirect. Ademas
   zustand `persist` hidrata localStorage async.

2. **`/users` da CORS.** Curl preflight real: el OPTIONS responde
   `Access-Control-Allow-Headers: Content-Type,X-Turnstile-Token,X-Turnstile-Bypass-Token`
   — **falta `Authorization`**. El admin manda `Authorization: Bearer <JWT>`
   a `/users` (todas las operations lo requieren) -> el browser bloquea.
   `/auth` funciona en login/register (mandan Turnstile, no Bearer) pero sus
   endpoints autenticados (`mfa.*`, `webauthn.*` con sesion) tienen el mismo
   bug latente. Hardcodeado en DOS lugares: `cors.py` (respuestas del Lambda)
   y `provisioner.py` (MOCK del OPTIONS preflight, que NO ejecuta el Lambda).

3. **email-code y magic-link en 2 correos.** Deben ir en UN solo correo como
   alternativa. Hoy `register.start`/`login.start`/`verify.resend-code` envian
   2 emails (kind `*-code` + `*-magic-link`). Ambos artefactos se generan en
   el MISMO request -> unirlos es directo.

4. **`/metrics` da 404.** El admin NO tiene page `/metrics` ni query de
   metricas (plan `b-analytics-api`, PENDING). El sidebar tiene un link
   "Metricas" -> `/metrics` 404 (SPA fallback).

**Outcome:** la sesion sobrevive al reload; `/users` (y endpoints autenticados
de `/auth`) ya no fallan por CORS; registro/login manda 1 email con link+code;
el sidebar no navega a `/metrics`.

### Hallazgos de exploracion (cerrados)
- CORS en `serverless/lambda/shared/http/cors.py:165-167` Y
  `devtools/serverless/provisioner.py:999`. OPTIONS es MOCK -> tocar ambos +
  reprovisionar (`_wire_cors_options` generico cubre los 4 endpoints).
- `CODE_TTL_MINUTES == LINK_TTL_MINUTES == 15` -> `expires_in_min=15` unico.
- `verify/resend_code.py` usa `claims.flow` -> `f'{flow}-unified'` resuelve a
  `register-unified`/`login-unified`; sin tercer kind.
- `users` email service usa otros kinds, NO combina code+link -> bug 3 no lo
  toca.
- Unicos callers de `publish_magic_link`/`publish_code`: los 3 controllers de
  auth + tests -> seguro migrar (metodos viejos se mantienen por compat).
- `(admin)/page.tsx` y `(admin)/layout.tsx` NO redirigen a `/metrics`.

## 2. Solucion Propuesta

Cuatro fixes independientes. Dos solo-frontend (1, 4), dos backend con
deploy/reprovision (2, 3).

### Decisiones clave
- **D1 (bug 1)**: flag `bootstrapping` transient en el store + gate en
  `useProtectedRoute`. `useAuthTimer` (ya dispara el refresh) cierra el flag;
  gate de hidratacion con `persist.hasHydrated()`. Default `true`.
- **D2 (bug 2)**: agregar `Authorization` en AMBOS strings (`cors.py` +
  `provisioner.py`) en un commit + reprovisionar el API GW.
- **D3 (bug 3)**: kinds `register-unified`/`login-unified` + 1 template c/u
  (boton link + code). `publish_unified(data={verify_url, code,
  expires_in_min})`. 3 controllers: 2 invokes -> 1. Kinds viejos por compat.
- **D4 (bug 4)**: quitar el nav-item `metrics` de `nav-items.ts`.
  `ROUTES.admin.metrics` se conserva.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: reload con refresh vigente (access null) -> "Verificando
  sesion...", NO redirige, tras `session.refresh` OK renderiza children.
- **AC-2**: reload SIN refresh (o expirado) -> redirige a `/login?next=<path>`.
- **AC-3**: reload con refresh vigente pero `session.refresh` FALLA -> redirige
  a `/login?next=<path>`.
- **AC-4**: store recien creado -> `bootstrapping === true` y NO en
  `partialize`.
- **AC-5**: `cors_headers(origin)` -> `Access-Control-Allow-Headers` incluye
  `Authorization`.
- **AC-6**: OPTIONS preflight de `/users` y `/auth` (tras reprovision) con
  `Access-Control-Request-Headers: authorization` -> respuesta incluye
  `Authorization` (HTTP 200).
- **AC-7**: `publish_unified(...)` -> UN solo `invoke_async` a `send_email` con
  `data == {verify_url, code, expires_in_min}`.
- **AC-8**: `register.start` con email nuevo -> `publish_unified` UNA vez (kind
  `register-unified`), no llama los viejos.
- **AC-9**: `login.start` (active sin password) y `verify.resend-code` -> 1
  invoke con kind `login-unified` / `f'{flow}-unified'`.
- **AC-10**: casos anti-enumeration (active/locked en start, resend throttled)
  -> `publish_unified.assert_not_called()`.
- **AC-11**: `seed-email-config` -> filas `register-unified`/`login-unified` +
  4 templates en S3.
- **AC-12**: sidebar (desktop + mobile) -> NINGUN nav-item apunta a `/metrics`.
- **AC-13** (E2E post-deploy): registro/login en dev manda UN email con boton
  link + code; click al link -> 302 a admin/callback; code en `/verify` -> OK.

## 4. Diagrama de flujo (bug 1)

### Antes
```
reload -> AuthGuard monta
  useAuthTimer:  !access + refresh vigente -> doRefresh() [ASYNC, en vuelo]
  useProtectedRoute: isAuthenticated()==false -> router.replace('/login') [SINCRONO, gana]
=> rebota a /login aunque el refresh hubiera funcionado
```

### Despues
```
reload -> AuthGuard monta
  bootstrapping = true (default)
  gate hidratacion: espera persist.hasHydrated()
  useAuthTimer (bootstrap branch):
     sin refresh / expirado -> setBootstrapping(false) -> redirect
     refresh vigente -> doRefresh().then(ok): setBootstrapping(false); if(!ok) reset()
  useProtectedRoute: if (!bootstrapping && !authed) router.replace('/login')
  AuthGuard render: (bootstrapping || !authed) ? "Verificando sesion..." : children
=> el redirect espera al refresh; solo rebota si no hay refresh o falla
```

## 5. Diagrama ER

N/A — sin cambios de schema. Los kinds de email son filas nuevas en la tabla
DynamoDB `email-config` (el schema no cambia).
