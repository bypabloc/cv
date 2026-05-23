"""Service de la operacion `contact`: procesamiento del form de contacto.

Concentra la logica de negocio del Lambda `contact_form`: persistir el
contacto en DynamoDB y notificar al owner por email (SES v2 con render
de un template HTML/txt).

El service es agnostico al transport (evento Lambda / API Gateway):
recibe dicts ya validados y devuelve el resultado. La validacion
Turnstile y el rate-limit NO viven aqui — necesitan la metadata de la
request HTTP y los orquesta el controller.

Regla de separacion:
  - controllers/contact/create.py : orquesta (rate-limit -> Turnstile ->
    service -> auto-blacklist -> normaliza).
  - services/contact_service.py   : logica de negocio (este archivo).
  - utils/                        : infraestructura generica.

Este archivo fusiona los antiguos modulos planos `service.py`,
`persistence.py` y `notification.py`.

`templates/` (los HTML/txt del email) vive dentro de `core/` para que el
packaging del deploy lo incluya en el zip (`packaging.py` solo copia
`core/` al artefacto). Este archivo esta en `core/services/`, asi que
`templates/` es `../templates` (parents[1]).
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
from aws_lambda_powertools.metrics import MetricUnit
from shared.aws.ssm import get_parameter
from shared.core.ulid import new_uuidv7
from shared.dynamodb import ContactItem
from shared.observability.logger import logger
from shared.observability.metrics import metrics

# templates/ vive dentro de core/ para que el deploy lo incluya en el zip.
# Este archivo esta en core/services/, asi que parents[1] = core/.
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / 'templates'


class ServiceError(Exception):
    """Error de negocio del Lambda `contact_form`.

    El controller lo captura y lo traduce a la respuesta normalizada
    `{is_valid: False, data, code}`.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int,
        error_code: str = 'SERVICE_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


# ---------------------------------------------------------------------------
# Persistencia DynamoDB (antes persistence.py)
# ---------------------------------------------------------------------------


def save_contact(payload: dict[str, Any]) -> dict[str, str]:
    """Persiste un contact submission en DynamoDB.

    Parameters
    ----------
    payload : dict[str, Any]
        Campos validados del form.

    Returns
    -------
    dict[str, str]
        Dict con `contact_id` y `created_at` (ISO 8601 UTC).
    """
    contact_id = new_uuidv7()
    created_at = datetime.now(UTC).isoformat()

    # ContactItem (ORM) arma el Item: omite los campos opcionales no
    # provistos (DynamoDB no permite empty strings) y reusa el resource
    # boto3 singleton. session_id enlaza el contacto con tracking_events;
    # el origen (ip/country/user_agent) NO se duplica aqui — se consulta
    # en tracking via JOIN por session_id.
    ContactItem(
        id=contact_id,
        created_at=created_at,
        name=payload['name'],
        email=payload['email'],
        message=payload['message'],
        company=payload.get('company'),
        role=payload.get('role'),
        service_type=payload.get('service_type'),
        budget=payload.get('budget'),
        timeline=payload.get('timeline'),
        niche=payload.get('niche'),
        session_id=payload.get('session_id'),
    ).save()

    return {'contact_id': contact_id, 'created_at': created_at}


# ---------------------------------------------------------------------------
# Notificacion SES (antes notification.py)
# ---------------------------------------------------------------------------


def _ses_client() -> Any:
    """Cliente SES lazy (no module-scope, para compat con moto)."""
    return boto3.client(
        'sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1')
    )


def _render_mustache_lite(template: str, context: dict[str, Any]) -> str:
    """Render minimo mustache-style: {{var}} y {{#var}}block{{/var}}.

    NO se usa Jinja2 (peso adicional al zip de la Lambda). Esto basta
    para el template plano. Si el value es None/empty, el bloque se omite.
    """

    def conditional_replacer(match: re.Match[str]) -> str:
        var = match.group(1)
        block = match.group(2)
        value = context.get(var)
        if value:
            return block.replace(f'{{{{{var}}}}}', str(value))
        return ''

    rendered = re.sub(
        r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}',
        conditional_replacer,
        template,
        flags=re.DOTALL,
    )

    def simple_replacer(match: re.Match[str]) -> str:
        var = match.group(1)
        value = context.get(var, '')
        return str(value) if value else ''

    return re.sub(r'\{\{(\w+)\}\}', simple_replacer, rendered)


def parse_recipients(raw: str) -> list[str]:
    """Parsea el parametro SSM `owner-email` como lista CSV de destinatarios.

    El parametro puede contener uno o varios correos separados por coma. Se
    aplica trim a cada entrada y se descartan las vacias (tolera comas
    sobrantes o espacios alrededor).

    Parameters
    ----------
    raw : str
        Valor crudo del parametro SSM (ej. ' a@x.com , b@y.com ').

    Returns
    -------
    list[str]
        Lista de direcciones limpias, sin entradas vacias.
    """
    return [item.strip() for item in raw.split(',') if item.strip()]


def send_owner_email(contact: dict[str, Any]) -> str:
    """Envia un email transaccional al owner del portfolio.

    Parameters
    ----------
    contact : dict[str, Any]
        Dict con name, email, message, contact_id, created_at, etc.

    Returns
    -------
    str
        SES MessageId.
    """
    from_address_path = os.environ.get(
        'SSM_SES_FROM_PATH', '/portfolio/ses-from-address'
    )
    owner_email_path = os.environ.get(
        'SSM_OWNER_EMAIL_PATH', '/portfolio/owner-email'
    )

    from_address = get_parameter(from_address_path)
    recipients = parse_recipients(get_parameter(owner_email_path))

    html_template = (_TEMPLATES_DIR / 'owner_email.html').read_text(
        encoding='utf-8'
    )
    text_template = (_TEMPLATES_DIR / 'owner_email.txt').read_text(
        encoding='utf-8'
    )

    context = {**contact, 'niche': contact.get('niche', 'generic')}
    html_body = _render_mustache_lite(html_template, context)
    text_body = _render_mustache_lite(text_template, context)

    subject = (
        f'Portfolio · Nuevo contacto de {contact.get("name", "")} '
        f'({contact.get("niche", "generic")})'
    )

    response = _ses_client().send_email(
        FromEmailAddress=f'The Full Stack <{from_address}>',
        Destination={'ToAddresses': recipients},
        ReplyToAddresses=[contact.get('email', from_address)],
        Content={
            'Simple': {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                },
            },
        },
    )

    message_id: str = response.get('MessageId', '')
    logger.info(
        'owner email sent',
        extra={
            'message_id': message_id,
            'contact_id': contact.get('contact_id'),
            'recipient_count': len(recipients),
        },
    )
    return message_id


# ---------------------------------------------------------------------------
# Orquestacion del dominio (antes service.process_contact_form)
# ---------------------------------------------------------------------------


def process_contact_form(*, form_fields: dict[str, Any]) -> dict[str, str]:
    """Persiste el contacto y notifica al owner por email.

    Logica de negocio del Lambda: a esta altura la verificacion Turnstile
    y el rate-limit YA pasaron (los orquesta el controller). El service
    persiste en DynamoDB y dispara el email.

    Parameters
    ----------
    form_fields : dict[str, Any]
        Campos del form ya validados (sin `cf_token` ni metadata de
        transporte). Incluye `session_id` opcional, clave de correlacion
        con tracking_events.

    Returns
    -------
    dict[str, str]
        Dict con `contact_id` y `created_at` (ISO 8601 UTC).

    Notes
    -----
    contacts NO duplica datos de origen (ip/country/user_agent): se
    consultan en tracking_events via JOIN por session_id (SPEC-202).

    El fallo del email NO se propaga: el contacto ya quedo persistido en
    DynamoDB y el lead no se pierde. El fallo se hace visible con la
    metrica CloudWatch `OwnerEmailFailed`, sin romper la respuesta 201.
    """
    payload = dict(form_fields)
    result = save_contact(payload)
    logger.info(
        'contact persisted',
        extra={'contact_id': result['contact_id']},
    )

    try:
        contact_with_meta = {**payload, **result}
        send_owner_email(contact_with_meta)
    except Exception:
        logger.exception(
            'failed to send owner email (contact already persisted)',
            extra={'contact_id': result['contact_id']},
        )
        # NO re-raise: el form se guardo en DynamoDB. El fallo se hace
        # visible con una metrica para detectarlo sin romper el 201.
        metrics.add_metric(
            name='OwnerEmailFailed',
            unit=MetricUnit.Count,
            value=1,
        )

    return result
