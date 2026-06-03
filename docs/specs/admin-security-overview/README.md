# Plan: Seguridad de cuenta unificada + login fusionado (admin + backend auth)

> Rediseño de autenticacion y seguridad de cuenta del portfolio. Cinco bloques:
> (A) panel unificado de seguridad con API agregadora `security.overview`,
> toggle on/off reversible por metodo y switch "requerido al loguear";
> (B) metodo MFA **requerido estricto** (flag nuevo + login multi-factor +
> fallback recovery/email-code); (C) `login.check-email` que expone si el email
> existe y sus metodos (decision consciente: rompe anti-enumeration);
> (D) **fusion register -> login** (se elimina la operation `register` y su UI;
> el login crea la cuenta si el email no existe); (E) frontend del panel + login
> rediseñado + eliminacion de la UI de register + nav-item + actualizacion de la
> rule `auth-system.md`.

## Alcance: 5 bloques

| Bloque | Que | Backend | Frontend |
|--------|-----|---------|----------|
| **A** | Panel de seguridad unificado | `security.overview`, `mfa.enable`, `webauthn.enable`, `mfa.set-required` (+ webauthn) | `SecurityOverviewPanel`, `useSecurityOverview`, toggles, switch "requerido", nav-item |
| **B** | MFA requerido estricto | flag `required` en `auth_mfa_methods` + `auth_webauthn_credentials` + migration + login multi-factor + fallback | UI del switch + advertencias de lockout |
| **C** | Login expone existencia + metodos | `login.check-email` | UI: paso email -> metodos disponibles |
| **D** | Fusion register -> login | borrar `register/*`, `login.start` crea pending, flow unico `login` | borrar UI register, login rediseñado |
| **E** | Cierre transversal | actualizar rule `auth-system.md` | nav, rutas, tests, limpieza |

## Indice (cuando leer cada archivo)

| Archivo | Cuando leer |
|---------|-------------|
| Este README | Contexto, solucion, las decisiones por bloque, riesgos de seguridad |
| [02-criterios-aceptacion.md](02-criterios-aceptacion.md) | Todos los AC numerados (fuente de verdad de tests) |
| [03-fase-b-required-login.md](03-fase-b-required-login.md) | Bloque B: flag `required` + migration + login multi-factor + fallback |
| [04-fase-d-fusion-login.md](04-fase-d-fusion-login.md) | Bloque D: borrar register + `login.start` crea pending + flow unico |
| [05-fase-c-check-email.md](05-fase-c-check-email.md) | Bloque C: `login.check-email` + anti-enumeration tradeoff |
| [06-fase-a-overview.md](06-fase-a-overview.md) | Bloque A: `security.overview` + `enable` + `set-required` |
| [07-fase-e-frontend.md](07-fase-e-frontend.md) | Bloque E: panel + login UI + borrar UI register + nav + rule |
| [08-commits.md](08-commits.md) | Seccion 9: commits incrementales |
| [09-verificacion-e2e.md](09-verificacion-e2e.md) | Seccion 11: verificacion E2E (A/B/C) |

## Estado por fase

| Fase | Estado |
|------|--------|
| 0. Plan (esta carpeta) | pending |
| B. Backend: required + migration + login multi-factor | pending |
| D. Backend: fusion register -> login | pending |
| C. Backend: login.check-email | pending |
| A. Backend: security.overview + enable + set-required | pending |
| E. Frontend: panel + login + borrar register UI + nav + rule | pending |
| Z. Verificacion E2E + limpieza del plan | pending |

> Orden de ejecucion = B -> D -> C -> A -> E -> Z. Razon: B cambia el modelo
> (migration), del que dependen el login (D) y el overview (A); D limpia
> register antes de tocar check-email (C); A consume todo lo anterior; E es el
> frontend que consume las APIs ya estables.

## Decisiones (no reabrir — confirmadas con el usuario)

### Bloque A — panel unificado
1. **API agregadora** `security.overview` (operation `security`): 1 GET
   autenticado devuelve los 5 metodos (TOTP, email-code, passkeys, recovery,
   password) con `configured`/`enabled`/`required`/`preferred` + timestamps +
   detalle. Reemplaza los 4 queries separados de la UI actual.
2. **Toggle on/off reversible**: `mfa.enable` (revierte `disabled_at` sin
   re-confirmar) + `webauthn.enable`. Passkeys pasan de hard-delete a
   soft-disable reversible (el delete sigue como accion "eliminar").
3. **Password read-only**: fila con estado + `last_change_at` + boton "Cambiar
   contrasena" (reusa el form actual). Sin toggle (es el factor base).

### Bloque B — requerido estricto
4. **Requerido estricto, multiple**: flag `required` nuevo en
   `auth_mfa_methods` Y `auth_webauthn_credentials`. El user marca 1 o varios.
   El login EXIGE todos los metodos marcados `required` (MFA multi-factor real).
5. **Fallback anti-lockout** (OBLIGATORIO): aunque haya metodos requeridos, el
   login SIEMPRE acepta como escape un **recovery code** o el **email-code de
   emergencia**. La UI advierte fuerte al marcar "requerido" (guardar recovery).
6. **Switch en el panel**: cada fila MFA activa tiene un control "requerido al
   loguear" ademas del toggle on/off. `set-required` reemplaza/extiende a
   `set-preferred` (preferred queda como "default sugerido"; required es el
   nuevo concepto fuerte).

### Bloque C — login.check-email (gated por password)
7. **`login.check-email`** devuelve `{exists, has_password}` (+ flags
   pending/unavailable). Expone la EXISTENCIA del email (ya enumerable hoy via
   register 409 / login 404 -> sin perdida real) y si tiene password, pero NO
   la lista de metodos MFA. Action separada, liviana, con Turnstile +
   rate-limit. NO crea user ni envia email.
8. **El dato sensible (lista de metodos MFA) queda detras de un factor.** Si el
   user tiene password, la lista se revela tras `verify-password`; si no, va
   passwordless (los metodos extra aparecen en el step-up tras el primer
   factor). Asi se evita el reconnaissance pre-auth de "que 2FA usa cada
   cuenta". La existencia se expone deliberadamente (trade-off aceptado) -> la
   rule `auth-system.md` se actualiza en el bloque E. Mitigacion del scraping de
   existencia: Turnstile + rate-limit estricto (la lista NO es la defensa
   principal — el gating por factor lo es).

### Bloque D — fusion register -> login
9. **Eliminar la operation `register` completa** (3 actions + controllers +
   OPERATIONS entry + tests + UI). Su logica se mueve a `login`.
10. **`login.start` unificado**: si el email existe -> flujo login normal; si NO
    existe -> crea el user `pending` + envia magic-link+code (lo que hoy hace
    `register.start`). El `verify-code`/`verify-magic-link` detecta
    `pending -> active` por el STATUS del user (flow unico `login`), no por el
    flow del token.
11. **Passwordless por defecto, password opcional**: el flujo de entrada es
    siempre magic-link + code. El password es un metodo MAS (configurable en el
    panel) y se ofrece en login solo si el user lo tiene.

## Riesgos de seguridad (explicitos)

| Riesgo | Bloque | Mitigacion |
|--------|--------|------------|
| Enumeracion de cuentas (saber que emails existen + su MFA) | C | Rate-limit estricto en `check-email` + Turnstile; trade-off aceptado por el dueño |
| Lockout permanente si el user pierde el metodo requerido | B | Fallback recovery code + email-code SIEMPRE; UI advierte guardar recovery |
| Crear cuentas sin confirmacion (login crea pending) | D | El user `pending` no es funcional hasta verificar el email (magic-link/code) |
| Romper el contrato del admin (consume register) | D/E | Migrar la UI y los api-client en el mismo PR; tests E2E |

## Reglas criticas (de las rules del repo)

- Backend: `lambda-controller` (handler genérico; operation+action en el body;
  NO tocar `manifest.yaml`). Imports externos SOLO via `shared.<subpaquete>`
  (`lambda-shared-imports`). Re-enable/required = nuevas funciones repo +
  service + action + **migration Alembic** (la corre la Lambda `db`).
- Backend: migration nueva, NUNCA editar una aplicada (`neon-management.md`).
  El flag `required` se agrega con `00000005_*` (siguiente revision).
- Backend: la rule `auth-system.md` se ACTUALIZA en el bloque E (el anti-
  enumeration deja de ser absoluto; el flow `register` desaparece).
- Frontend: TS 6 strict sin `any`. Tanstack Query. shadcn (`Switch`,
  `AlertDialog`, `RadioGroup`, `Card`, `Badge`, `Skeleton`). Mirror de tests.
  Coverage >= 80% per-file. SPA estatico (todo Client Component).
- Tests del lambda auth: un archivo por escenario; mockear `require_active_user`
  + el Service; helpers en `_helpers.py`.

## Matriz de verificacion (resumen — detalle en 09)

| Que | Comando |
|-----|---------|
| Migration (upgrade+downgrade en branch Neon) | `serverless run --stage=dev --lambda=db --event=events/migrate.json` |
| Backend auth unit + coverage | `serverless tests --type=unit/coverage --lambda=auth` |
| Backend lint-deps | `serverless lint-deps --lambda=auth --shared` |
| Frontend lint/typecheck/test/build | `pnpm --filter @portfolio/admin <script>` |
| E2E real (post-merge) | `api_e2e --env=dev` (actualizado sin register) + curl `check-email`/`overview` + flujo login real |
