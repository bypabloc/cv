"""Mapeo de operaciones del Lambda `contact_form`.

El Lambda `contact_form` atiende un unico endpoint HTTP (`POST /contact`).
Se modela como una sola operation, `contact`, con una sola action,
`create`. El handler sintetiza el evento `{operation, action, data}` a
partir del evento HTTP de API Gateway (body + metadata de headers).

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: contact_form no invoca otros Lambdas).
"""

OPERATIONS = {
    'contact': {
        'controller': 'contact',
        'arn_key': '',
    },
}
