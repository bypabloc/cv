"""@module services.email_service — logica de envio de email.

Lee la config del email de DynamoDB (`email-config`), baja el template html
+ txt de S3, renderiza con Jinja2 y envia por SES. NO toca Neon (Lambda
puro). Todo acceso AWS via `shared.*` (NUNCA boto3/jinja2 directo).
"""

from __future__ import annotations

import os
from typing import Any

from shared.aws.dynamodb import get_table
from shared.aws.s3 import get_object_text
from shared.aws.ses import send_email
from shared.aws.ssm import get_parameter, get_parameter_by_name
from shared.observability.logger import logger
from shared.templating.jinja import render_html, render_text

# Path SSM (env var inyectada por devtools desde uses.tables) que contiene
# el nombre fisico de la tabla email-config.
_TABLE_PATH_ENV = 'SSM_EMAIL_CONFIG_TABLE_PATH'


class EmailServiceError(Exception):
    """Error de negocio del Lambda send_email."""

    def __init__(
        self,
        message: str,
        *,
        code: int = 5000,
        error_code: str = 'EMAIL_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


def _config_table_name() -> str:
    """Resuelve el nombre fisico de la tabla email-config (SSM en cold)."""
    path = os.environ[_TABLE_PATH_ENV]
    return get_parameter(path)


def get_email_config(kind: str) -> dict[str, Any]:
    """Lee la fila `email-config[kind]`.

    Raises EmailServiceError (code 1404) si el kind no existe — sin llamar
    SES (AC del plan).
    """
    table = get_table(_config_table_name())
    response = table.get_item(Key={'kind': kind})
    item = response.get('Item')
    if not item:
        raise EmailServiceError(
            f'email kind desconocido: {kind!r}',
            code=1404,
            error_code='EMAIL_KIND_NOT_FOUND',
        )
    return item


def send(
    *,
    kind: str,
    to: list[str],
    data: dict[str, Any],
    reply_to: list[str] | None = None,
) -> str:
    """Renderiza y envia el email del `kind`. Devuelve el MessageId de SES."""
    config = get_email_config(kind)

    bucket = str(config['bucket'])
    html_tpl = get_object_text(bucket, str(config['html_path']))
    txt_tpl = get_object_text(bucket, str(config['txt_path']))

    subject = render_text(str(config['subject']), data)
    html = render_html(html_tpl, data)
    text = render_text(txt_tpl, data)

    from_address = get_parameter_by_name(
        'ses-from-address', local_env='EMAIL_FROM'
    )

    response = send_email(
        from_address=f'The Full Stack <{from_address}>',
        to_addresses=to,
        subject=subject,
        text_body=text,
        html_body=html,
        reply_to=reply_to,
    )
    message_id = str(response.get('MessageId', ''))
    logger.info('email sent', extra={'kind': kind, 'message_id': message_id})
    return message_id
