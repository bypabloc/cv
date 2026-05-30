# 02 — Fase 1: subpaquete `shared.crypto`

[← 01 Contexto](01-contexto-y-decision.md) · [Siguiente: Fase 2 →](03-fase-verifier-transport.md)

> Portador único de `cryptography` para el backend + lógica de verificación
> del token Ed25519. Aislado para que solo `contact_form` y `auth` lo
> vendoricen.

## Archivos a crear

- `shared/crypto/__init__.py` — VACÍO (docstring-only, regla no-barrels).
- `shared/crypto/pyproject.toml` — `cryptography>=44` en
  `[project.dependencies]`; `[tool.shared] internal-deps = ["core",
  "observability"]`.
- `shared/crypto/ed25519.py` — primitivas (lazy import de `cryptography`):
  - `verify_signature(public_key_b64, message: bytes, signature: bytes) -> bool`
  - `sign_message(private_key_b64, message: bytes) -> bytes`
  - `generate_keypair() -> tuple[str, str]` (priv_b64, pub_b64) — para keygen.
- `shared/crypto/bypass_token.py` — contrato del token:
  - `TOKEN_VERSION = 1`, `DEFAULT_TTL_SECONDS = 300`.
  - `build_payload(*, stage, ttl=DEFAULT_TTL_SECONDS, now) -> dict`.
  - `sign_bypass_token(*, stage, private_key_b64, ttl, now) -> str` (lo usa
    devtools, no el Lambda — vive acá por una sola fuente del formato).
  - `verify_bypass_token(token, *, public_key_b64, stage, now=None) -> dict`
    → payload si válido; lanza `BypassTokenError(code=...)` si no.
- `shared/core/exceptions.py` — agregar `BypassTokenError(ApplicationError)`
  (default_code `CAPTCHA_INVALID`, status 403).

## Detalles

- **Formato**: `token = b64url(payload_json).b64url(sig)` (2 segmentos, sin
  padding). Algoritmo fijo Ed25519 (no hay header).
- **Mensaje firmado**: los bytes ASCII del primer segmento
  (`b64url(payload_json)`), NO el JSON crudo.
- **Claves**: 32 bytes raw Ed25519 transportados como base64 (`from_*_bytes`).
- **`jti`**: `secrets.token_hex(8)` — trazabilidad en logs, NO single-use.
- **Errores controlados**: token malformado → `BypassTokenError`, NUNCA
  excepción no atrapada. NUNCA el token en el mensaje/extra del error.
- **`stage`**: comparación normal de strings (no es secreto).

## Reglas

- `cryptography` SOLO dentro de funciones (lazy).
- `__init__.py` VACÍO; imports concretos `from shared.crypto.bypass_token
  import verify_bypass_token`.
- Catálogo de portadores: `cryptography → shared.crypto` (Fase 5).

## Tests (crear)

`shared/tests/unit/shared/crypto/`:

- `test_sign_and_verify_roundtrip.py` [AC-2]
- `test_verify_rejects_tampered_signature.py` [AC-3]
- `test_verify_rejects_expired.py` [AC-4]
- `test_verify_rejects_stage_mismatch.py` [AC-5]
- `test_verify_rejects_malformed_token.py` [AC-3]
- `test_verify_does_not_leak_token_in_error.py` [AC-3]

## Verificación de la fase

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless lint-deps --shared
```

[← 01 Contexto](01-contexto-y-decision.md) · [Siguiente: Fase 2 →](03-fase-verifier-transport.md)
