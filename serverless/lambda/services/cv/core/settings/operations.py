"""Mapeo de operaciones del Lambda `cv`.

Una sola operation `cv` con N actions, una por entidad o agregado:
`get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
`education`, `languages`, `references`, `skills`.

El http_handler resuelve la action del query string del GET y la
descubre por convencion en controllers/cv/<action>.py.
"""

OPERATIONS = {
    'cv': {
        'controller': 'cv',
        'arn_key': '',
    },
}
