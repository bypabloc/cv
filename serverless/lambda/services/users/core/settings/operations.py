"""Mapeo de operations del Lambda `users`.

3 operations: `profile` (CRUD del perfil propio), `status` (estado +
sesiones) y `admin` (scope whitelist SSM). Cada operation declara su
carpeta de controllers y un `arn_key` vacio (users NO invoca otros
Lambdas).

Los controllers se descubren por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`list-users` -> module `controllers/admin/list_users.py` + clase
`ListUsers(BaseController)`.
"""

OPERATIONS = {
    'profile': {
        'controller': 'profile',
        'arn_key': '',
    },
    'status': {
        'controller': 'status',
        'arn_key': '',
    },
    'admin': {
        'controller': 'admin',
        'arn_key': '',
    },
}
