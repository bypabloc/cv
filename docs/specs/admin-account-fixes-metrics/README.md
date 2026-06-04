# Plan: fixes de cuenta/seguridad del admin + mejoras de /metrics

> Plan Large (1 PR) que corrige ~11 issues reportados tras usar el admin
> desplegado contra dev: bug del TOTP confirm, reestructura de `/settings`
> en tabs (Perfil | Seguridad | Sesiones), set-password para users
> passwordless, registro de passkey desde el panel, fix del campo "nombre
> para mostrar", `current_session_id` en la vista de sesiones, gráfica de
> timeseries vacía, tooltip de retención, selector de rango estilo
> CloudWatch (Relative/Absolute) con backend extendido a timestamps +
> bucket minute/hour, y reemplazo del polling por un botón "Actualizar".

## Estado por fase

| # | Fase | Archivo | Estado |
|---|------|---------|--------|
| 1 | Contexto, solución, AC | [01-contexto-y-decision.md](01-contexto-y-decision.md) | redactado |
| 2 | Backend: TOTP confirm fix | [02-backend-totp.md](02-backend-totp.md) | redactado |
| 3 | Backend: profile.get + status.get | [03-backend-users.md](03-backend-users.md) | redactado |
| 4 | Backend: analytics timestamps + bucket | [04-backend-analytics.md](04-backend-analytics.md) | redactado |
| 5 | Admin: tabs de /settings | [05-admin-settings-tabs.md](05-admin-settings-tabs.md) | redactado |
| 6 | Admin: panel seguridad (passkey, set-password, email-code) | [06-admin-security-panel.md](06-admin-security-panel.md) | redactado |
| 7 | Admin: /metrics (gráfica, rango, refresh) | [07-admin-metrics.md](07-admin-metrics.md) | redactado |
| 8 | Descomposición + commits + worktrees | [08-ejecucion.md](08-ejecucion.md) | redactado |
| 9 | Verificación E2E iterativa | [09-verificacion-e2e.md](09-verificacion-e2e.md) | redactado |

## Decisiones (no reabrir)

| # | Decisión | Razón |
|---|----------|-------|
| D-1 | `/settings`, `/settings/security`, `/settings/sessions` son **rutas reales por tab** (mismo layout con tabs) | El usuario eligió "3 tabs, rutas reales por tab". Mantiene URLs navegables. |
| D-2 | El método **email-code se quita** del panel de seguridad | Es el fallback de entrada (login); no es un método configurable/toggleable. Backend NO se toca, solo la UI deja de listarlo. |
| D-3 | El panel de seguridad gana un **botón "Registrar passkey"** | WebAuthn ya está en el backend; el panel unificado debe permitir configurarlo. |
| D-4 | **`profile.get` expone `has_password`**; la UI muestra "Establecer contraseña" (sin campo "actual") si es false | El método `ProfileService.has_password()` ya existe; solo se expone. UI condicional → llama `set-password` o `change-password`. |
| D-5 | **`status.get` agrega `current_session_id`** resuelto desde el `family_id` del access JWT | Hoy no lo devuelve → la vista "sesión actual" sale vacía. El JWT siempre lleva `family_id`. |
| D-6 | El backend de analytics **extiende `from`/`to` a datetime + bucket `minute`/`hour`** | El selector estilo CloudWatch necesita granularidad sub-día; el usuario eligió "extender backend". |
| D-7 | El selector de rango replica **idéntico la imagen** (Relative chips 5m/30m/1h/3h/12h/Custom + grid Minutes/Hours/Days/Weeks + Absolute con 2 calendarios + Start/End date+time + Apply) | Decisión explícita del usuario. |
| D-8 | **Sin polling**: se quita `refetchInterval`; un botón "Actualizar" invalida todas las queries de analytics (incl. active-now) | El usuario: "no hagas polling a la API". |
| D-9 | La **retención NO se compara con correos**; 0% = ningún visitante previo volvió en el rango. Se agrega tooltip explicativo, sin tocar el backend | La lógica backend (new vs returning por `first_seen_at`) es correcta. |
| D-10 | **change-email NO es bug**: ya valida posesión del nuevo email por magic-link single-use (15 min). Solo se verifica/documenta en la UI | El flujo backend ya está completo. |
| D-11 | **TODO en 1 PR** (`feature/admin-account-fixes-metrics -> dev`) | Decisión explícita del usuario. |

## Reglas críticas (siempre activas)

- Rama de trabajo `feature/admin-account-fixes-metrics` (la actual `dev` es
  protegida). Push + PR SOLO con la sección 11 (fase 9) verde.
- Backend: imports shared-only (`serverless lint-deps`), TS 6 strict sin
  `any`, Biome v2 en el admin.
- Backend deploy + reprovision son **Parte C** (post-merge, dev real):
  migration de analytics si aplica, redeploy de auth/users/analytics,
  verificación con curl + bypass token Ed25519.
- Coverage >= 80% per-file en archivos modificados (admin + lambdas).
- Carpeta del plan es **efímera**: el último commit la elimina con
  `git rm -r`.

## Matriz issue -> fase -> AC

| Issue reportado | Fase | AC |
|---|---|---|
| TOTP confirm da INVALID_TOTP_CODE | 2 | AC-1, AC-2 |
| email-code no debe estar en /settings/security | 6 | AC-12 |
| passkey "no configurado" sin botón | 6 | AC-13 |
| change-password exige "actual" sin password | 3, 6 | AC-5, AC-14 |
| /settings/security y /sessions como tabs | 5 | AC-8, AC-9 |
| "usuario" y "sesión actual" vacíos en sesiones | 3, 5 | AC-6, AC-10 |
| change-email valida por magic-link (verificar) | 6 | AC-15 |
| "nombre para mostrar" no deja tipear | 5 | AC-11 |
| gráfica "Eventos en el tiempo" vacía | 7 | AC-16 |
| retención 0% confuso | 7 | AC-17 |
| dropdown de rango estilo CloudWatch | 4, 7 | AC-3, AC-4, AC-18, AC-19 |
| polling -> botón "Actualizar" | 7 | AC-20 |
