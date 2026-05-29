"""Subpaquete `auth`: JWT (HS256), argon2id, codes, tokens, TOTP, WebAuthn, admin.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.auth.jwt import verify_jwt, issue_access_jwt
    from shared.auth.password import hash_password
"""
