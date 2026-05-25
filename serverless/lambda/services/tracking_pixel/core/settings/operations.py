"""Mapeo de operaciones del Lambda `tracking_pixel`.

El Lambda `tracking_pixel` tiene una sola operation, `tracking`, con una
sola action, `track`. El handler sintetiza el evento `{operation,
action, data}` a partir del evento HTTP de API Gateway (`POST /track`).

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el Lambda tracking_pixel no invoca otros Lambdas).
"""

OPERATIONS = {
    'tracking': {
        'controller': 'tracking',
        'arn_key': '',
    },
}
