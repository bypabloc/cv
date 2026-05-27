"""Mapeo de operaciones del Lambda `contact_worker`.

El Lambda consume mensajes SQS de la cola `portfolio-contact-form-<stage>`.
Tiene una sola operation `worker` con una sola action `process`. El handler
sintetiza el evento `{operation: 'worker', action: 'process', data: body}`
por cada record SQS y delega al controller `worker/process`.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el worker no invoca otros Lambdas).
"""

OPERATIONS = {
    'worker': {
        'controller': 'worker',
        'arn_key': '',
    },
}
