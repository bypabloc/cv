# 03 — Backend: profile.get (has_password) + status.get (current_session_id)

[← TOTP](02-backend-totp.md) · [Siguiente: analytics →](04-backend-analytics.md)

> Cubre AC-5, AC-6, AC-7. Lambda `users`. Sin migration (solo respuestas).

## Solución

### AC-5 — `profile.get` expone `has_password`

`ProfileService.has_password(user_id)` ya existe
(`serverless/lambda/services/users/core/services/profile_service.py:69-72`,
lee `auth_credentials` por PK). Solo falta exponerlo en la respuesta del
controller `profile.get`.

```python
# serverless/lambda/services/users/core/controllers/profile/get.py
# en el dict de respuesta (junto a mfa_configured):
'has_password': svc.has_password(user_id=user.id),
```

Test: `tests/unit/controllers/profile/test_profile_get_ok.py` (o nuevo)
asserta `has_password` presente y bool. Cubrir ambos: con credential → True,
sin credential → False.

### AC-6 / AC-7 — `status.get` agrega `current_session_id`

El controller `status.get`
(`serverless/lambda/services/users/core/controllers/status/get.py`) NO
devuelve `current_session_id`. El access JWT lleva `family_id` (siempre, vía
`issue_access_jwt`). El `family_id` ES el identificador de la sesión física
(agrupa los refresh). `status.list_sessions` ya lo usa como
`current_family_id` para marcar la sesión actual.

Fix: en `status.get`, leer el `family_id` del JWT verificado y devolverlo
como `current_session_id`.

```python
# status/get.py
# require_active_user devuelve user; necesitamos también el claim family_id.
# Opción: verificar el JWT y extraer claims.family_id (como hace list_sessions).
# Devolver en la respuesta:
'current_session_id': claims.family_id,  # str | None (None si legacy sin family_id)
```

Revisar cómo `status/list_sessions.py` obtiene `current_family_id` y replicar
el mismo patrón (verificar el JWT una vez, extraer `family_id`).

Tests:
- `test_status_get_ok.py`: JWT con `family_id` → `current_session_id` ==
  ese valor. [AC-6]
- `test_status_get_no_family_id.py` (nuevo): JWT sin `family_id` →
  `current_session_id` is None. [AC-7]

## 7. Archivos afectados (fase 3)

### Modificar
- `serverless/lambda/services/users/core/controllers/profile/get.py` —
  agregar `has_password` a la respuesta.
  - Verificar: `serverless tests --type=unit --lambda=users`.
- `serverless/lambda/services/users/core/controllers/status/get.py` —
  agregar `current_session_id` (del `family_id` del JWT). Replicar el patrón
  de `list_sessions.py` para extraer el claim.
  - Verificar: idem.
- (posible) el model de respuesta si hay un Pydantic de salida tipado para
  status/profile — agregar el campo.

### Crear
- `serverless/lambda/services/users/tests/unit/controllers/profile/test_profile_get_has_password.py`
  [AC-5]
- `serverless/lambda/services/users/tests/unit/controllers/status/test_status_get_current_session.py`
  [AC-6, AC-7]

### AC-14 (backend) — primer set de password sin current_password

CONFIRMADO en código: `profile.change-password` SIEMPRE verifica
`current_password` (`update_password(current_password=...)` → 401
`INVALID_PASSWORD` si no matchea). Un user **passwordless** (sin row en
`auth_credentials`) no tiene hash contra qué verificar → no puede setear su
primer password. Fix (parte backend de AC-14, en este mismo commit de
`users`):

- `ProfileService.update_password` (o un método nuevo `set_password`): si el
  user NO tiene credential (`has_password() is False`), permitir setear el
  password SIN `current_password` (no hay nada que verificar). Si SÍ tiene,
  exigir `current_password` como hoy.
- `change_password.py`: cuando el user es passwordless, omitir la
  verificación de current y proceder al set (mismas revocaciones de sesión).
  `ProfileChangePasswordIn` hace `current_password` opcional.
- Tests: passwordless + `new_password` sin current → 200 + credential creada;
  con password + current incorrecto → 401 (sin cambio).

Esto evita exponer una action nueva: el mismo `change-password` cubre el
primer set y el cambio. La UI (fase 6) decide el copy según `has_password`.

### NO se toca
- `ProfileService.has_password` (ya existe).
- `change_email.py` / `confirm_email_change.py` (el flujo ya valida posesión
  del nuevo email; solo se documenta en la UI — fase 6, AC-15).
- Schema / migration (ninguno).

## Verificación (fase 3)

```bash
python devtools/run.py serverless lint-deps --lambda=users
python devtools/run.py serverless tests --type=unit --lambda=users
python devtools/run.py serverless tests --type=coverage --lambda=users  # >=80%
```

Parte C (dev real): tras redeploy de `users`, invoke `profile.get` →
`has_password` presente; `status.get` con un access JWT → `current_session_id`
no vacío. [AC-5, AC-6]

[← TOTP](02-backend-totp.md) · [Siguiente: analytics →](04-backend-analytics.md)
