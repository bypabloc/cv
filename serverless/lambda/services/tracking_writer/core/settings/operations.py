"""Mapeo de operaciones del Lambda `tracking_writer`.

El Lambda `tracking_writer` tiene una sola operation, `tracking`, con una
sola action, `write`. Lo invoca async el encoder `tracking_pixel`
(`InvocationType='Event'`, sin SQS) con el contrato estandar
`{operation: 'tracking', action: 'write', data: {...}}`, y el handler lo
enruta via `run_controller` -> controller `tracking/write`.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el writer no invoca otros Lambdas).
"""

OPERATIONS = {
    'tracking': {
        'controller': 'writer',
        'arn_key': '',
    },
}
