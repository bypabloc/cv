"""Mapeo de operations del Lambda `auth`.

El Lambda atiende las operations `login`, `verify`, `session`, `mfa`,
`webauthn` y `security`. La operation `register` fue ELIMINADA (el alta
ocurre dentro del flujo `login` unico: `login.start` crea el pending). La
estructura sigue el contrato del lambda-controller: cada operation declara
su controller (carpeta dentro de `controllers/`) y un `arn_key` (vacio
porque `auth` NO invoca otros Lambdas).

Los controllers se descubren por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`verify-magic-link` -> module
`controllers/login/verify_magic_link.py` + clase
`VerifyMagicLink(BaseController)`.
"""

OPERATIONS = {
    'login': {
        'controller': 'login',
        'arn_key': '',
    },
    'verify': {
        'controller': 'verify',
        'arn_key': '',
    },
    'session': {
        'controller': 'session',
        'arn_key': '',
    },
    'mfa': {
        'controller': 'mfa',
        'arn_key': '',
    },
    'webauthn': {
        'controller': 'webauthn',
        'arn_key': '',
    },
    'security': {
        'controller': 'security',
        'arn_key': '',
    },
}
