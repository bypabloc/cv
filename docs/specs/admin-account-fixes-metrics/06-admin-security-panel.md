# 06 — Admin: panel de seguridad (passkey, set-password, email-code) + change-email

[← settings tabs](05-admin-settings-tabs.md) · [Siguiente: metrics →](07-admin-metrics.md)

> Cubre AC-12, AC-13, AC-14, AC-15. Solo frontend admin (consume backend de
> fases 2-3).

## Estado actual

- `security-overview-panel.tsx`: lista los métodos del `security.overview`.
  Incluye una fila para email-code (el usuario no la quiere). El `WebauthnRow`
  muestra "No tienes passkeys registrados" SIN botón de registro.
- `change-password-form.tsx`: siempre pide `current_password` (no consulta
  `has_password`).
- `webauthn-credentials-list.tsx` (dead code): ya tiene
  `<WebAuthnRegisterButton />` funcional — reutilizable.
- `change-email-form.tsx` + `confirm-email-change.tsx`: flujo correcto
  (token al nuevo email, single-use). Solo falta confirmar copy en la UI.

## Solución

### AC-12 — quitar email-code del panel (D-2)

`security-overview-panel.tsx`: el `security.overview` puede seguir
devolviendo email-code, pero el panel NO renderiza su fila. Filtrar la lista
de métodos para excluir `kind === 'email_code'` (o el id que use). El
email-code sigue siendo el fallback de entrada en el login — no se toca el
backend, solo deja de listarse como configurable.

### AC-13 — botón "Registrar passkey" (D-3)

En el `WebauthnRow` del panel (cuando `configured === false` o siempre, para
agregar otra passkey), agregar un botón "Registrar passkey" que dispare el
flujo WebAuthn ya implementado:

1. `webauthn.register-options` → recibe options con `challenge_id`.
2. `navigator.credentials.create({ publicKey })` (browser).
3. `webauthn.register-verify` con la attestation → 200.
4. Invalida `security.overview` (refetch).

Reutilizar la lógica de `WebAuthnRegisterButton` (hoy dead code en
`webauthn-credentials-list.tsx`): mover/integrar ese botón dentro del
`WebauthnRow` del panel. El hook que dispara `register-options`/
`register-verify` ya existe en `features/settings/hooks` o `auth/api` —
confirmar y reutilizar.

### AC-14 — set-password condicional por has_password (D-4)

`change-password-form.tsx` consume `has_password` (de `profile.get`, fase 3,
expuesto en el tipo `UserProfile`):

- `has_password === true`: flujo actual (campo "contraseña actual" + nueva +
  confirmar → `users.profile.change-password`).
- `has_password === false`: título "Establecer contraseña", SIN campo
  "contraseña actual", solo nueva + confirmar → `auth.verify.set-password`?
  NO — el set-password de `auth.verify` usa el `temp_token` del flujo
  register/login. Para un user AUTENTICADO sin password, usar
  `users.profile.change-password` con `current_password` omitido/vacío SI el
  backend lo permite, o exponer una variante. **Verificar en backend**: el
  `change-password` de users, ¿acepta setear el primer password sin
  `current_password`? Si NO, hay que extender el backend (action
  `set-password` autenticada en users, o `change-password` con
  `current_password` opcional cuando `has_password` es false).

> NOTA DE ALCANCE: si el backend `users.profile.change-password` exige
> `current_password` siempre, esta AC requiere un fix backend menor (permitir
> el primer set sin current cuando no hay credential). Documentarlo aquí y
> agregarlo a la fase 3 (users) si el diagnóstico lo confirma. El plan ya
> toca `users`, así que cabe en el mismo commit de backend.

El Zod schema del form se vuelve condicional (con/sin `current_password`).

### AC-15 — change-email verificado (D-10)

El flujo ya valida posesión del nuevo email (token single-use, 15 min). La UI
ya dispara `change-email` → toast "revisa tu correo" y `confirm-email-change`
con el `?token`. Solo:
- Confirmar/mejorar el copy: "Te enviamos un enlace al NUEVO correo; el cambio
  se aplica al confirmarlo."
- Agregar un test que verifique el flujo (mock MSW: change-email → request_id;
  confirm-email-change con token → 200).

## 7. Archivos afectados (fase 6)

### Modificar
- `admin/src/features/settings/components/security-overview-panel.tsx` —
  filtrar email-code (AC-12); botón "Registrar passkey" en WebauthnRow
  (AC-13).
  - Verificar: `pnpm --filter @portfolio/admin test`.
- `admin/src/features/settings/components/change-password-form.tsx` —
  condicional por `has_password`: oculta "contraseña actual", título
  "Establecer contraseña", llama el endpoint correcto (AC-14).
  - Verificar: test del form (con/sin password).
- `admin/src/features/settings/validation.ts` — schema condicional de
  password.
- `admin/src/features/settings/hooks/use-change-password.ts` — soportar el
  caso set-password (sin current).
- `admin/src/types/models.ts` — `UserProfile` agrega `has_password: boolean`
  (viene de profile.get tras fase 3).
- `admin/src/features/settings/components/change-email-form.tsx` — copy de
  verificación del nuevo email (AC-15).
- (si aplica backend) `serverless/lambda/services/users/.../change_password.py`
  — permitir primer set sin `current_password` cuando no hay credential.
  Ver "NOTA DE ALCANCE" arriba; si se confirma, se agrega a la fase 3.

### Crear
- `admin/tests/unit/features/settings/components/security-overview-no-emailcode.test.tsx`
  [AC-12]
- `admin/tests/unit/features/settings/components/security-overview-passkey-register.test.tsx`
  [AC-13]
- `admin/tests/unit/features/settings/components/change-password-set.test.tsx`
  [AC-14]
- `admin/tests/unit/features/settings/components/change-email-flow.test.tsx`
  [AC-15]

### Limpiar (dead code)
- `webauthn-credentials-list.tsx`, `mfa-methods-list.tsx`,
  `email-code-section.tsx` — si quedan sin uso tras el refactor, eliminarlos
  del `index.ts` y del árbol (no dejar código muerto). El botón de registro
  de passkey se integra al panel.

## Verificación (fase 6)

```bash
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build
# si tocó backend users:
python devtools/run.py serverless tests --type=unit --lambda=users
```

Parte C (dev real): en `/settings/security` no hay email-code; passkey con
botón de registro funcional; user passwordless ve "Establecer contraseña" sin
"actual"; change-email envía link al nuevo correo. [AC-12..AC-15]

[← settings tabs](05-admin-settings-tabs.md) · [Siguiente: metrics →](07-admin-metrics.md)
