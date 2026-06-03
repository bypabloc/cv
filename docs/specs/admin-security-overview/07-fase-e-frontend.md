# 07 — Fase E: Frontend (panel + login rediseñado + borrar UI register + nav + rule)

[<- fase A](06-fase-a-overview.md) | [Siguiente: commits ->](08-commits.md)

> Frontend que consume las APIs ya estables: panel unificado de seguridad
> (`security.overview` + toggles + switch "requerido"), login rediseñado
> (paso email -> `check-email` -> metodos o crear cuenta), eliminacion de toda
> la UI de register, nav-item "Seguridad", y la actualizacion de la rule
> `auth-system.md`. Cubre AC-E1..AC-E12.

## 7.E.1 — Panel de seguridad unificado (Bloque A en el front)

### Crear/Modificar — api-client + tipos + hooks

- `admin/src/features/auth/api/auth-client.ts` — agregar wrappers:
  `securityOverview()`, `mfaEnable(kind)`, `mfaSetRequired(kind, required)`,
  `webauthnEnable(credential_id)`, `webauthnDisable(credential_id)`,
  `webauthnSetRequired(credential_id, required)`, `loginCheckEmail(email, cf)`.
- `admin/src/types/api.ts` — `SecurityOverviewResponse`, `SecurityMethod`
  (`type`, `label`, `configured`, `enabled`, `required`, `preferred`,
  `created_at`, `last_used_at`, `detail`), tipos del `detail` por type.
- `admin/src/features/settings/hooks/use-security-overview.ts` — `useQuery`
  (queryKey `securityKeys.overview()`, staleTime razonable). Reemplaza el uso
  de `useMfaList`+`useListCredentials`+... en el panel [AC-E1].
- `admin/src/features/settings/hooks/use-toggle-method.ts` — `useMutation`:
  segun `type` + estado destino llama `enable`/`disable`/`webauthnEnable`/
  `webauthnDisable`; invalida `securityKeys.overview()`. Maneja 409
  `MUST_KEEP_ONE_MFA_METHOD` con toast [AC-E3..E5].
- `admin/src/features/settings/hooks/use-set-required.ts` — `useMutation`:
  `mfaSetRequired`/`webauthnSetRequired`; invalida overview [AC-E6].
- `admin/src/features/settings/api/query-keys.ts` — `securityKeys.overview()`.
  - Verificar: tests de hooks (MSW) + `pnpm --filter @portfolio/admin test`.

### Crear — componente del panel

- `admin/src/features/settings/components/security-overview-panel.tsx` —
  consume `useSecurityOverview`. Por cada metodo una fila/`Card`:
  - `Badge` de estado (Activo / Desactivado / No configurado).
  - `Switch` on/off (excepto password) -> `useToggleMethod` [AC-E2..E4].
  - `Switch`/control "Requerido al loguear" (excepto password) ->
    `useSetRequired`, con `AlertDialog` de advertencia (guardar recovery) al
    activar [AC-E6].
  - Si `configured:false` -> CTA "Configurar" (enlaza al setup existente)
    [AC-E7].
  - Passkeys: el `detail.credentials` se expande en sub-filas, cada una con su
    on/off + required + boton "Eliminar" (hard-delete) [AC-E2].
  - Password: estado + last_change_at + boton "Cambiar contrasena" (reusa
    `ChangePasswordForm`), sin toggles [AC-E8].
- `admin/src/app/(admin)/settings/security/page.tsx` — reemplazar los 5
  componentes sueltos por `<SecurityOverviewPanel />` (+ mantener los
  componentes de setup como modales/CTAs que el panel invoca).
  - Verificar: `tests/unit/features/settings/components/
    security-overview-panel.test.tsx` (1 sola query, filas, toggles, 409,
    required-warning).

### Conservar (reusados por el panel)

- `ChangePasswordForm`, `TotpSetup`, `WebAuthnRegisterButton`,
  `RecoveryCodesModal`, `EmailCodeSection` — se mantienen como acciones de
  setup que el panel dispara; lo que se reemplaza es el LISTADO (ahora 1 query).

## 7.E.2 — Login rediseñado + eliminar register (Bloques C + D en el front)

### Modificar — login (paso email -> check-email -> metodos / crear)

- `admin/src/app/(auth)/login/page.tsx` + `features/auth/components/
  login-form.tsx` (flujo gated por password):
  - Paso 1: input email + Turnstile -> `loginCheckEmail` [AC-E10].
  - Si `exists:true` + `has_password:true` -> pedir la **password**; al
    verificar (`login.start` con password / `verify-password`), el backend
    revela los metodos requeridos -> step-up multi-factor (TOTP/passkey/...).
    La lista de metodos NO se muestra antes de la password.
  - Si `exists:true` + `has_password:false` -> flujo **passwordless** directo:
    `login.start` manda magic-link + code; los metodos extra (si hay) aparecen
    en el step-up tras el primer factor.
  - Si `exists:false` -> "No existe una cuenta con ese email. Crear cuenta?"
    -> al confirmar, `login.start` (que crea el pending + manda el email).
  - Si `pending` -> "Termina de verificar tu email" -> reenviar (passwordless).
  - Si `unavailable` -> mensaje generico "no se puede iniciar sesion" (sin
    revelar disabled/locked).
- `admin/src/features/auth/hooks/use-login-start.ts` (existente) — adaptar al
  `created`/`pending` que ahora devuelve `login.start`.
- `admin/src/features/auth/hooks/use-check-email.ts` (NUEVO) — `useMutation`
  de `loginCheckEmail`.
  - Verificar: `tests/unit/features/auth/.../login-form.test.tsx` (existe ->
    metodos; no existe -> crear; pending -> reenviar).

### Eliminar — toda la UI de register [AC-E11, AC-D9]

- `admin/src/app/(auth)/register/page.tsx` (carpeta).
- `admin/src/features/auth/components/register-form.tsx`.
- `admin/src/features/auth/hooks/use-register-start.ts`.
- `admin/src/features/auth/hooks/use-register-verify-code.ts`.
- `admin/src/features/auth/api/auth-client.ts` — quitar `registerStart`,
  `registerVerifyCode`.
- `admin/src/lib/routes.ts` — quitar `ROUTES.auth.register`.
- `admin/src/lib/validation/auth.ts` — quitar `registerSchema`.
- Sus tests.
  - Conservar: `verify-code-input.tsx`, `magic-link-prompt.tsx`,
    `callback/page.tsx`, `set-password/page.tsx` (compartidos por el flujo
    login).
  - Verificar: `rg -l "register" admin/src` -> solo refs validas (ej.
    `webauthn.register-options` que NO es la operation register, o copy
    "registrarse" en el login). `pnpm --filter @portfolio/admin build`.

## 7.E.3 — Nav-item "Seguridad" [AC-E9]

- `admin/src/features/admin-shell/lib/nav-items.ts` — agregar
  `{ href: ROUTES.admin.settingsSecurity, label: "Seguridad", icon: ShieldCheck }`
  (o anidar bajo Configuracion). Visible en desktop + mobile.
  - Verificar: `nav-items.test.ts` (incluye `/settings/security`).

## 7.E.4 — Actualizar la rule auth-system.md [AC-E12]

- `.claude/rules/auth-system.md`:
  - Seccion "Login UX (anti enumeration)": documentar que `login.check-email` y
    `login.start` exponen la EXISTENCIA del email (trade-off aceptado) y
    ofrecen crear cuenta; disabled/locked siguen sin revelar el estado real.
  - Eliminar las referencias a la operation `register` (ya no existe); el flujo
    de entrada es `login` unico (crea pending si no existe).
  - Agregar el concepto `required` (metodo requerido al loguear, multi-factor)
    + el fallback recovery/email-code anti-lockout.
  - Agregar las nuevas actions: `login.check-email`, `mfa.enable`,
    `mfa.set-required`, `webauthn.enable`, `webauthn.disable`,
    `webauthn.set-required`, `security.overview`.
  - Validar la rule con `claude -p` (ver `claude-config-testing.md`).

## Tests requeridos (Bloque E)

- `security-overview-panel.test.tsx` [AC-E1..E8].
- `login-form.test.tsx` (check-email -> metodos / crear / pending) [AC-E10].
- `nav-items.test.ts` (incluye Seguridad) [AC-E9].
- Barrido: `rg -l "registerStart|/register|RegisterForm" admin/src admin/tests`
  -> cero [AC-E11].

[<- fase A](06-fase-a-overview.md) | [Siguiente: commits ->](08-commits.md)
