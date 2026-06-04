# 02 — Backend: fix del TOTP confirm (INVALID_TOTP_CODE)

[← Contexto](01-contexto-y-decision.md) · [Siguiente: users →](03-backend-users.md)

> Cubre AC-1, AC-2. Lambda `auth`. **Primer paso obligatorio: diagnóstico
> en runtime** — el fix depende del hallazgo.

## Diagnóstico (antes de tocar código)

El flujo setup→confirm parece correcto en lectura estática:

- `setup_totp.py`: genera `secret_b32`, lo cifra (`kms_encrypt`,
  EncryptionContext `{user_id, purpose:totp}`), persiste como BYTEA, devuelve
  `otpauth_url` (pyotp defaults SHA1/6/30).
- `confirm_totp.py`: lee el ciphertext, `kms_decrypt` con el MISMO context,
  `verify_totp_code(valid_window=1)`.
- `db_session()` auto-commitea (`shared/db/session.py`).
- `get_totp_ciphertext` envuelve con `bytes(...)` (maneja memoryview de
  psycopg3).

**Hecho clave:** existe un test E2E (`tests/api/_flows.py:_setup_totp_confirmed`)
que ejercita setup→confirm con el `secret_b32` en claro + `totp_now(b32)`. Si
ese test pasa contra dev, el round-trip KMS+DB+pyotp funciona y el
INVALID_TOTP_CODE del usuario es **timing/clock-drift** (un code de 30s que
expiró antes del submit; `valid_window=1` cubre solo ±30s).

**NO existe** un test unit que cubra el round-trip COMPLETO
(cifrar→persistir BYTEA→leer→descifrar→verificar con un code real).

### Paso D-1 — reproducir en dev (runtime)

```bash
# 1) mint bypass token (firma Ed25519 local)
TOKEN=$(python devtools/run.py bypass_token mint --env=dev 2>/dev/null | tail -1)

# 2) crear/obtener un user active con access JWT (ver tests/api o seed Neon)
#    luego: setup-totp -> obtener secret_b32 + otpauth_url
#    generar el code con pyotp del secret_b32 EN EL ACTO y confirmar.
#    Comparar: confirm con code recién generado (debe dar 204) vs un code
#    de hace 60s (debe dar INVALID). Esto aísla timing vs bug real.
```

Resultado del diagnóstico decide el fix:

- **Caso A (timing):** el round-trip funciona; el usuario tipeó un code
  expirado. Fix: subir `valid_window` a `2` (±60s) en `confirm-totp` (más
  tolerante al lag humano de tipear) + el admin debe mostrar el contador de
  expiración del code. NO es un bug de cifrado.
- **Caso B (round-trip roto):** el `secret_b32` descifrado NO coincide con el
  original. Fix según el punto exacto (EncryptionContext, BYTEA, encoding).

## Solución (cubre ambos casos)

### Test de round-trip COMPLETO (siempre, independiente del caso)

Crear `serverless/lambda/services/auth/tests/unit/services/test_totp_roundtrip.py`
(o en `shared/tests` si encaja mejor): cifra un secret conocido con moto KMS,
lo persiste vía `upsert_totp_method` en una sesión real (sqlite/pg de test),
lo lee con `get_totp_ciphertext`, lo descifra con `verify`, y asserta que
`pyotp.TOTP(original).now()` verifica OK. Cubre **AC-1** (round-trip
bit-idéntico) + **AC-2** (confirm 204 con code válido).

### Fix Caso A — tolerancia de tiempo

`confirm_totp.py` (o `totp_service.verify`): subir el `valid_window` del
verify a `2` SOLO para el confirm (el setup acaba de mostrar el code; ±60s
absorbe el tiempo de escanear el QR + tipear). El login (`verify-totp`)
mantiene `valid_window=1` (más estricto en producción). Documentar el porqué.

```python
# shared/auth/totp.py — verify_totp_code ya acepta valid_window param.
# confirm: totp_svc.verify(..., valid_window=2)  (nuevo param opcional)
# login verify-totp: sin cambio (valid_window=1 default)
```

### Fix Caso B — según hallazgo

Si el round-trip está roto, el test de arriba falla y señala el punto:
- EncryptionContext: forzar `str(user.id)` idéntico (mismo tipo) — ya lo es.
- BYTEA: confirmar `bytes(memoryview)` correcto (el wrapper ya está).
- encoding: confirmar que `kms_encrypt`/`kms_decrypt` no meten base64.

## 7. Archivos afectados (fase 2)

### Modificar
- `serverless/lambda/shared/auth/totp.py` — (si Caso A) ya acepta
  `valid_window`; sin cambio salvo doc.
  - Verificar: `serverless tests --type=unit --shared`.
- `serverless/lambda/services/auth/core/services/totp_service.py` — `verify`
  acepta `valid_window` param (default 1), lo pasa a `verify_totp_code`.
  - Verificar: `serverless tests --type=unit --lambda=auth`.
- `serverless/lambda/services/auth/core/controllers/mfa/confirm_totp.py` —
  llama `totp_svc.verify(..., valid_window=2)`.
  - Verificar: idem.

### Crear
- `serverless/lambda/services/auth/tests/unit/services/test_totp_roundtrip.py`
  — round-trip completo (moto KMS + sesión real). [AC-1, AC-2]
  - Verificar: `serverless tests --type=unit --lambda=auth`.

### NO se toca
- `setup_totp.py` (el setup es correcto).
- El schema (sin migration: los defaults SHA1/6/30 ya existen).

## Verificación (fase 2)

```bash
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth  # >=80%
python devtools/run.py serverless tests --type=unit --shared
```

Parte C (dev real): tras redeploy de `auth`, reproducir setup→confirm con
bypass token y un code recién generado → 204. [AC-2]

[← Contexto](01-contexto-y-decision.md) · [Siguiente: users →](03-backend-users.md)
