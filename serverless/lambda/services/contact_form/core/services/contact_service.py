"""Service de la operacion `contact`: procesamiento del form de contacto.

Concentra la logica de negocio del Lambda `contact_form`: persistir el
contacto en Neon (sessions + visit + contact, misma tx) y notificar al
owner por email invocando el Lambda `send_email` de forma asincrona
(`InvocationType='Event'`).

El service es agnostico al transport (evento Lambda / API Gateway):
recibe dicts ya validados y devuelve el resultado. La validacion
Turnstile y el rate-limit NO viven aqui — necesitan la metadata de la
request HTTP y los orquesta el controller.

Tras el refactor cold-start (sin SQS, sin ASYNC_MODE): el contacto se
escribe INLINE a Neon (un INSERT pooled caliente ~10-25ms) y el email se
delega a `send_email` con un invoke async best-effort (el render Jinja2 +
SES viven en ese Lambda; este ya no arma templates ni habla con SES).

Regla de separacion:
  - controllers/contact/create.py : orquesta (rate-limit -> Turnstile ->
    service -> auto-blacklist -> normaliza).
  - services/contact_service.py   : logica de negocio (este archivo).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from shared.aws.lambda_invoke import LambdaInvokeError, invoke_async
from shared.aws.ssm import get_parameter_by_name
from shared.core.ulid import new_uuidv7
from shared.db.repository import ensure_session_and_visit, insert_contact
from shared.db.session import db_session
from shared.observability.logger import logger
from shared.observability.metrics import MetricUnit, metrics


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
# Persistencia Neon (inline, sin SQS)
# ---------------------------------------------------------------------------


def save_contact(payload: dict[str, Any]) -> dict[str, str]:
    """Persiste un contact submission en Neon (sessions + visits + contact).

    - `session_id` es OBLIGATORIO en el payload (lo resuelve el controller).
    - UPSERTea `sessions` + `session_visits` via `ensure_session_and_visit`
      en la MISMA tx del INSERT del contact.
    - `bump_event_count=True`: cada contact suma 1 al event_count del visit.
    - ip/country/user_agent NO se persisten en `contacts` (viven en
      sessions/session_visits via FK).
    - El `niche` del visit se infiere del Origin si no hay visit previa
      (lo calcula el controller con `niche_from_origin`).

    Returns
    -------
    dict[str, str]
        Dict con `contact_id` (UUID v7) y `created_at` (ISO 8601 UTC).
    """
    contact_id = new_uuidv7()
    created_at = datetime.now(UTC)
    session_id = payload['session_id']

    visit_niche = payload.get('niche') or payload.get('origin_niche')

    with db_session() as session:
        ensure_session_and_visit(
            session,
            session_id=session_id,
            ip=payload.get('ip'),
            country=payload.get('country'),
            user_agent=payload.get('user_agent'),
            browser=None,
            browser_version=None,
            os_name=None,
            device_type=None,
            utm_source=None,
            utm_medium=None,
            utm_campaign=None,
            utm_content=None,
            utm_term=None,
            referrer=None,
            landing_page_path=None,
            niche=visit_niche,
            bump_event_count=True,
        )

        neon_payload: dict[str, Any] = {
            'id': contact_id,
            'created_at': created_at,
            'name': payload['name'],
            'email': payload['email'],
            'message': payload['message'],
            'company': payload.get('company'),
            'role': payload.get('role'),
            'service_type': payload.get('service_type'),
            'budget': payload.get('budget'),
            'timeline': payload.get('timeline'),
            'niche': payload.get('niche'),
            'session_id': session_id,
        }
        insert_contact(session, neon_payload)

    return {'contact_id': contact_id, 'created_at': created_at.isoformat()}


# ---------------------------------------------------------------------------
# Notificacion: invoke async al Lambda send_email (kind=contact)
# ---------------------------------------------------------------------------


def parse_recipients(raw: str) -> list[str]:
    """Parsea el parametro SSM `owner-email` como lista CSV de destinatarios."""
    return [item.strip() for item in raw.split(',') if item.strip()]


def notify_owner(contact: dict[str, Any]) -> None:
    """Invoca `send_email` async para notificar al owner del nuevo contacto.

    Best-effort: el invoke async (`InvocationType='Event'`) no espera el
    resultado. Si falla (red/permisos), se loggea + metrica y NO se
    propaga — el contacto YA quedo persistido en Neon, el lead no se pierde.
    El render del template + SES viven en el Lambda `send_email` (kind=contact).
    """
    recipients = parse_recipients(
        get_parameter_by_name('owner-email', local_env='OWNER_EMAIL'),
    )
    function_name = os.environ['LAMBDA_SEND_EMAIL_FUNCTION_NAME']
    reply_to = [contact['email']] if contact.get('email') else None
    payload = {
        'operation': 'email',
        'action': 'send',
        'data': {
            'kind': 'contact',
            'to': recipients,
            'reply_to': reply_to,
            'data': {
                'name': contact.get('name', ''),
                'email': contact.get('email', ''),
                'message': contact.get('message', ''),
                'company': contact.get('company'),
                'role': contact.get('role'),
                'service_type': contact.get('service_type'),
                'budget': contact.get('budget'),
                'timeline': contact.get('timeline'),
                'niche': contact.get('niche') or contact.get('origin_niche'),
            },
        },
    }
    try:
        invoke_async(function_name=function_name, payload=payload)
    except LambdaInvokeError:
        logger.exception(
            'failed to invoke send_email (contact already persisted)',
            extra={'contact_id': contact.get('contact_id')},
        )
        metrics.add_metric(
            name='OwnerEmailFailed', unit=MetricUnit.Count, value=1
        )


# ---------------------------------------------------------------------------
# Orquestacion del dominio
# ---------------------------------------------------------------------------


def process_contact_form(
    *,
    form_fields: dict[str, Any],
    session_id: str,
    ip: str,
    country: str | None,
    user_agent: str | None,
    origin_niche: str | None,
) -> dict[str, str]:
    """Persiste el contacto (sessions + visit + contact) y notifica al owner.

    A esta altura la verificacion Turnstile y el rate-limit YA pasaron (los
    orquesta el controller). Escribe inline a Neon e invoca `send_email`
    async. El fallo del email NO se propaga (el contacto ya quedo en Neon).

    Returns
    -------
    dict[str, str]
        Dict con `contact_id` y `created_at` (ISO 8601 UTC).
    """
    payload = {
        **form_fields,
        'session_id': session_id,
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'origin_niche': origin_niche,
    }
    result = save_contact(payload)
    logger.info(
        'contact persisted',
        extra={'contact_id': result['contact_id'], 'session_id': session_id},
    )

    notify_owner({**payload, **result})
    return result
