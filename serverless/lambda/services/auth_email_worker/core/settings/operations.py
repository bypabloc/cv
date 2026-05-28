"""Mapeo de operaciones del Lambda `auth_email_worker`.

El Lambda consume mensajes SQS de la cola `portfolio-auth-email-<stage>`.
Tiene una sola operation `email` con una sola action `process`. El handler
sintetiza el evento `{operation: 'email', action: 'process', data: body}`
por cada record SQS y delega al controller `email/process`. El
dispatching por `kind` (register-magic-link, register-code, ...) es
INTERNO al controller via el template_service.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el worker no invoca otros Lambdas).
"""

OPERATIONS = {
    'email': {
        'controller': 'email',
        'arn_key': '',
    },
}
