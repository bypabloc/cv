# Plan: 4 bug-fixes admin + backend

> Sesion que no persiste tras reload, CORS en `/users`, email-code +
> magic-link en un solo correo, y el nav-item `/metrics` que da 404.
> Carpeta efimera: se elimina al mergear (ver
> [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md)).

## Cuando leer

| Tema | Archivo | Cuando |
|------|---------|--------|
| Contexto, solucion, AC | [01-contexto-y-decision.md](01-contexto-y-decision.md) | Antes de tocar nada |
| Bug 1 — sesion (bootstrap) | [02-bug-sesion-bootstrap.md](02-bug-sesion-bootstrap.md) | Admin: store + auth-guard + hooks |
| Bug 2 — CORS Authorization | [03-bug-cors-authorization.md](03-bug-cors-authorization.md) | cors.py + provisioner.py + reprovision |
| Bug 3 — email unificado | [04-bug-email-unificado.md](04-bug-email-unificado.md) | auth controllers + send_email seeds |
| Bug 4 — nav-item /metrics | [05-bug-metrics-navitem.md](05-bug-metrics-navitem.md) | nav-items.ts |
| Commits | [06-commits.md](06-commits.md) | Secuencia de commits + PR |
| Verificacion E2E | [07-verificacion-e2e.md](07-verificacion-e2e.md) | Fase final (Partes A/B/C) |

## Estado por fase

| Fase | Estado |
|------|--------|
| Bug 4 (nav-item) | pending |
| Bug 1 (sesion) | pending |
| Bug 2 (CORS) | pending |
| Bug 3 (email) | pending |
| Verificacion E2E | pending |

## Decisiones (no reabrir)

1. **Bug 1**: flag `bootstrapping` transient en el store (default `true`, NO
   persistido). `useAuthTimer` cierra el flag; `useProtectedRoute` no redirige
   mientras `bootstrapping === true`. Gate de hidratacion con
   `persist.hasHydrated()`.
2. **Bug 2**: agregar `Authorization` en AMBOS strings (`cors.py:165` +
   `provisioner.py:999`). El OPTIONS es MOCK -> reprovisionar el API GW.
3. **Bug 3**: kinds nuevos `register-unified`/`login-unified` + 1 template c/u
   (boton link + code). `publish_unified(...)`. 3 controllers pasan de 2
   invokes a 1. Kinds viejos se mantienen por compat. TTL unico = 15 min.
4. **Bug 4**: quitar el nav-item `metrics` de `nav-items.ts`.
   `ROUTES.admin.metrics` se conserva para `b-analytics-api`.

## Reglas criticas

- Rama de trabajo `fix/admin-session-cors-email-metrics` desde `dev`.
- Bugs 2 y 3 requieren REDEPLOY/REPROVISION backend; bugs 1 y 4 solo frontend.
- `git push` + PR SOLO con la bateria de la fase 07 (Partes A+B) en verde.
- Parte C (post-merge, reprovision + seed + curl/email/reload real) es el gate
  para declarar el plan "listo".

## Matriz de verificacion

| Bug | Capa | Redeploy Lambda | Reprovision API GW | Seed | Solo frontend |
|-----|------|-----------------|--------------------|------|---------------|
| 1 sesion | Frontend | — | — | — | si |
| 2 CORS | Backend + Infra | si | **si** (MOCK OPTIONS) | — | no |
| 3 email | Backend | si (`auth`) | — | **si** (email-config) | no |
| 4 /metrics | Frontend | — | — | — | si |
