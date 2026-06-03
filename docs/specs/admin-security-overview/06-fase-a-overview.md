# 06 — Fase A: security.overview + enable + (set-required ya en B)

[<- fase C](05-fase-c-check-email.md) | [Siguiente: fase E ->](07-fase-e-frontend.md)

> Action agregadora `security.overview` (operation `security` nueva): 1 GET
> autenticado devuelve los 5 metodos con su estado completo + detalle. Mas las
> actions `mfa.enable`/`webauthn.enable` (el `set-required` ya se creo en B).
> Cubre AC-A1..AC-A11. Es la API que alimenta el panel del bloque E.

## Por que va al final del backend

`overview` agrega TODO el estado: `configured`/`enabled`/`required`/`preferred`
+ detalle. Necesita el flag `required` (B), el login fusionado (D) y los metodos
estables. Por eso es la ultima fase backend antes del frontend.

## Contrato de `security.overview`

`POST /auth` body `{operation:'security', action:'overview'}` +
`Authorization: Bearer <access>`

```jsonc
{ "is_valid": true, "code": 0, "data": { "methods": [
  { "type": "totp", "label": "App autenticadora",
    "configured": true, "enabled": true, "required": false, "preferred": true,
    "created_at": "...", "last_used_at": "...", "detail": {} },
  { "type": "email_code", "label": "Codigo por email",
    "configured": false, "enabled": false, "required": false, "preferred": false,
    "created_at": null, "last_used_at": null, "detail": {} },
  { "type": "webauthn", "label": "Llaves de acceso (passkeys)",
    "configured": true, "enabled": true, "required": false, "preferred": false,
    "detail": { "credentials": [
      { "credential_id": "...uuid...", "nickname": "iPhone",
        "transports": ["internal"], "enabled": true, "required": false,
        "created_at": "...", "last_used_at": "..." } ] } },
  { "type": "recovery_codes", "label": "Codigos de recuperacion",
    "configured": true, "enabled": true, "required": false, "preferred": false,
    "detail": { "total": 10, "remaining": 8 } },
  { "type": "password", "label": "Contrasena",
    "configured": true, "enabled": true, "required": false, "preferred": false,
    "detail": { "last_change_at": "..." } }
]}}
```

- `webauthn` es UN type con `detail.credentials` (lista de passkeys); cada
  passkey trae su `enabled`/`required` individual (el toggle/required opera
  por passkey).
- `password.enabled` siempre true si `configured` (no se desactiva); sin
  `required` toggle (factor base).
- `recovery_codes`: `configured` = tiene codes generados; `enabled` = quedan
  >0 restantes.

## 7.A Archivos afectados

### Crear — operation `security`

- `core/controllers/security/__init__.py`
- `core/controllers/security/overview.py` — `Overview(BaseController)`,
  `event_model=SecurityOverviewIn`, `require_active_user`. Orquesta:
  `mfa_svc.list_all(user_id)` (incluye desactivados + required),
  `webauthn_svc.list_all(user_id)`, `recovery_svc.counts(user_id)`,
  `password has_password + last_change_at`. Arma las 5 entradas SIEMPRE (las no
  configuradas con `configured:false`).
- `core/models/security.py` — `SecurityOverviewIn {meta}` (sin payload).
- `core/settings/operations.py` — agregar `'security': {'controller':
  'security', 'arn_key': ''}`.
  - Verificar: `tests/unit/controllers/security/test_overview_*.py`.

### Modificar — services (metodos "list_all" incl. desactivados)

- `mfa_method_service.py` — `list_all(*, user_id)`: como `list_active` pero
  SIN filtrar `disabled_at` (incluye desactivados) + agrega `enabled`
  (`disabled_at is None`), `required`, `created_at`, `last_used_at`.
- `webauthn_service.py` — `list_all(*, user_id)`: todas las passkeys (incl.
  desactivadas) con `enabled`/`required`/timestamps/nickname/transports.
- `recovery_codes_service.py` — `counts(*, user_id) -> {total, remaining}`
  (usa `count_remaining_recovery_codes` existente + un count total).
- Un helper para `password`: `has_password` + `last_change_at` (de
  `auth_credentials`; reusar la query de `ProfileService.has_password` o
  exponerla en un repo compartido).
  - Verificar: tests de cada service (list_all incluye desactivados).

### Crear — `mfa.enable` / `webauthn.enable` controllers

- `core/controllers/mfa/enable.py` — `Enable(BaseController)`,
  `event_model=MfaEnableIn {kind, meta}`. `require_active_user`. 404 si el
  metodo no existe; 204 idempotente si ya activo; setea `disabled_at=NULL`.
- `core/controllers/webauthn/enable.py` — idem por `credential_id`.
- `core/models/mfa.py` / `webauthn.py` — `MfaEnableIn`, `WebauthnEnableIn`.
  - (Las funciones repo/service `enable_*` ya se crearon en la fase B.)
  - Verificar: `tests/unit/controllers/mfa/test_enable_*.py` [AC-A6..A9].

## Nota: el guard al desactivar ya existe

`mfa.disable` y `webauthn.delete-credential` ya aplican
`MUST_KEEP_ONE_MFA_METHOD` (409). El toggle-off del panel reusa `disable`. Para
passkeys, el toggle-off del panel usa un nuevo `webauthn.disable` (soft-disable
reversible) en vez de `delete-credential` (que sigue para "eliminar del todo").

### Crear — `webauthn.disable` (soft-disable reversible de passkey)

- `core/controllers/webauthn/disable.py` — `Disable(BaseController)`,
  `event_model=WebauthnDisableIn {credential_id, meta}`. Aplica el guard
  `MUST_KEEP_ONE_MFA_METHOD` (igual que delete). Setea `disabled_at=now()` (NO
  borra). El `delete-credential` existente se mantiene para hard-delete.
  - Verificar: test disable passkey + guard 409 + re-enable (AC-A9, AC-A10).

## Tests requeridos (Bloque A)

- `tests/unit/controllers/security/test_overview_returns_five_methods.py`
  [AC-A1].
- `test_overview_empty_user.py` [AC-A2].
- `test_overview_full_user.py` — TOTP required + passkey + 8 recovery +
  password [AC-A3].
- `test_overview_disabled_method_visible.py` [AC-A4].
- `test_overview_requires_auth.py` [AC-A5].
- `tests/unit/controllers/mfa/test_enable_*.py`,
  `webauthn/test_enable_*.py`, `webauthn/test_disable_*.py` [AC-A6..A10].

[<- fase C](05-fase-c-check-email.md) | [Siguiente: fase E ->](07-fase-e-frontend.md)
