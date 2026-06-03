"""Mapeo de operations del Lambda `auth`.

El Lambda atiende 4 operations (`register`, `login`, `verify`,
`session`) con multiples actions cada una. La estructura sigue el
contrato del lambda-controller: cada operation declara su controller
(carpeta dentro de `controllers/`) y un `arn_key` (vacio porque `auth`
NO invoca otros Lambdas).

Los controllers se descubren por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`verify-magic-link` -> module
`controllers/register/verify_magic_link.py` + clase
`VerifyMagicLink(BaseController)`. Los archivos concretos de cada
controller se agregan en PR 7 y PR 8.
"""

OPERATIONS = {
    'register': {
        'controller': 'register',
        'arn_key': '',
    },
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
