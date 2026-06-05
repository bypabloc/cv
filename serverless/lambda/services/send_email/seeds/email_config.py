"""Fuente de verdad de las filas de la tabla `email-config`.

Cada `kind` mapea a: el bucket S3 de templates (resuelto por stage al
seedear), los paths del template html/txt dentro del bucket, y el subject
(string Jinja2 — puede llevar variables del `data`, ej. el nombre del
visitante en `contact`). La Lambda `send_email` lee estas filas en runtime.

El seed (`serverless seed-email-config`) sube los templates de
`seeds/templates/` al bucket y hace PutItem de estas filas.
"""

from __future__ import annotations

# subject por kind (Jinja2). Los 9 de auth/users son los subjects de los
# emails transaccionales; `contact` se arma con el nombre del visitante.
EMAIL_CONFIG: list[dict[str, str]] = [
    {
        'kind': 'register-magic-link',
        'subject': 'Confirma tu cuenta en The Full Stack',
    },
    {
        'kind': 'login-magic-link',
        'subject': 'Tu enlace de acceso a The Full Stack',
    },
    {
        'kind': 'password-reset',
        'subject': 'Restablece tu contraseña en The Full Stack',
    },
    {
        'kind': 'email-change-verify',
        'subject': 'Confirma tu nuevo email en The Full Stack',
    },
    {
        'kind': 'register-code',
        'subject': 'Tu código de verificación: The Full Stack',
    },
    {
        'kind': 'login-code',
        'subject': 'Tu código de acceso a The Full Stack',
    },
    {
        # Email unificado de register: magic-link + code en un solo correo.
        'kind': 'register-unified',
        'subject': 'Confirma tu cuenta en The Full Stack',
    },
    {
        # Email unificado de login: magic-link + code en un solo correo.
        'kind': 'login-unified',
        'subject': 'Tu acceso a The Full Stack',
    },
    {
        'kind': 'email-changed',
        'subject': 'Tu email fue actualizado en The Full Stack',
    },
    {
        # Notificacion tras un cambio de password (users.profile.change-password).
        'kind': 'password-changed',
        'subject': 'Tu contraseña fue actualizada en The Full Stack',
    },
    {
        'kind': 'account-disabled',
        'subject': 'Tu cuenta fue deshabilitada en The Full Stack',
    },
    {
        'kind': 'account-deleted',
        'subject': 'Tu cuenta fue eliminada en The Full Stack',
    },
    {
        'kind': 'contact',
        'subject': 'Nuevo contacto de {{ name }}',
    },
]


def build_rows(bucket: str) -> list[dict[str, str]]:
    """Construye las filas completas de `email-config` para un bucket dado.

    Cada fila: {kind, bucket, html_path, txt_path, subject}. Los paths son
    `<kind>.html` / `<kind>.txt` (los templates se suben al raiz del bucket).
    """
    return [
        {
            'kind': row['kind'],
            'bucket': bucket,
            'html_path': f'{row["kind"]}.html',
            'txt_path': f'{row["kind"]}.txt',
            'subject': row['subject'],
        }
        for row in EMAIL_CONFIG
    ]
