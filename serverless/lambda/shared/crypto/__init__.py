"""Subpaquete shared.crypto — portador unico de `cryptography`.

VACIO a proposito (regla `.claude/rules/lambda-shared-imports.md`: los
`__init__.py` de `shared/*` no re-exportan nada). Importar SIEMPRE del
modulo concreto:

    from shared.crypto.bypass_token import verify_bypass_token
    from shared.crypto.captcha import verify_captcha_or_bypass
    from shared.crypto.ed25519 import generate_keypair

`cryptography` se importa de forma LAZY dentro de las funciones de
`ed25519.py` para no pagar su costo de import en el cold start de los
Lambdas que solo cargan el modulo sin ejercitar el path de bypass.
"""
