"""Mapeo de operaciones del Lambda `db`.

El Lambda `db` tiene una sola operation, `db`, con una action por cada
comando de gestion del schema (migrate, current, downgrade, stamp,
show-migrations). El handler sintetiza el evento `{operation, action,
data}` a partir del payload de invocacion `{command, args}`.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el Lambda db no invoca otros Lambdas).
"""

OPERATIONS = {
    'db': {
        'controller': 'db',
        'arn_key': '',
    },
}
