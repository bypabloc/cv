"""@module persistence — UPSERT + INSERT idempotente + email SES.

Spec lambdas-async-sqs (fase 05): el contact se persiste con
`ON CONFLICT (id) DO NOTHING` via el helper compartido
`shared.db.repository.insert_contact_idempotent`. El service retorna
`persisted=True` si la fila se inserto, `persisted=False` si ya existia
(idempotencia). El controller usa ese bool para evitar mandar email
duplicado cuando SQS re-entrega el mismo mensaje.

`send_owner_email_safe` PROPAGA cualquier excepcion de SES, al
contrario del flujo sync legacy (que silenciaba el error con un log).
Asi un fallo del email re-encola el mensaje (retry SQS hasta
max_receive_count=3) en vez de perder el lead silenciosamente. Como
`save_contact_idempotent` es no-op en reintentos, el owner puede recibir
el mismo email max 3 veces — trade-off aceptable.
"""

import re
from pathlib import Path
from typing import Any

from models.message import ContactQueueMessage
from shared.aws.ses import send_email
from shared.aws.ssm import get_secret_by_name
from shared.db.repository import (
    ensure_session_and_visit,
    insert_contact_idempotent,
)
from shared.db.session import db_session
from shared.observability.logger import logger

# templates/ vive dentro de core/ para que el deploy lo incluya en el
# zip. Este archivo esta en core/services/, asi que parents[1] = core/.
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / 'templates'


def save_contact_idempotent(msg: ContactQueueMessage) -> dict[str, Any]:
    """UPSERT session + visit + INSERT contact con ON CONFLICT id DO NOTHING.

    Parameters
    ----------
    msg : ContactQueueMessage
        Mensaje validado del worker (Pydantic).

    Returns
    -------
    dict
        `{'persisted': bool, 'contact_id': str, 'created_at': str}`.
        `persisted=False` significa que `contact_id` YA existia (mensaje
        re-entregado por SQS) — el caller NO debe mandar email.

    Notes
    -----
    El `session_id` y los demas datos del visitante se UPSERTean
    SIEMPRE (sin importar la idempotencia del contact). Esto preserva
    `last_seen_at` y el contador de `event_count` del visit, que son
    datos analiticos del visitante — no del contact.
    """
    visit_niche = msg.niche or msg.origin_niche

    with db_session() as session:
        # Paso 1: UPSERT session + visit (siempre). Si SQS re-entrega el
        # mismo mensaje, el helper detecta que las 6 claves del visit no
        # cambiaron y reusa el visit existente (sin INSERT nuevo).
        ensure_session_and_visit(
            session,
            session_id=msg.session_id,
            ip=msg.ip,
            country=msg.country,
            user_agent=msg.user_agent,
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

        # Paso 2: INSERT contact con ON CONFLICT (id) DO NOTHING. El
        # helper retorna True si la fila se inserto (rowcount=1) o False
        # si ya existia (rowcount=0).
        payload: dict[str, Any] = {
            'id': msg.contact_id,
            'created_at': msg.created_at,
            'name': msg.name,
            'email': msg.email,
            'message': msg.message,
            'company': msg.company,
            'role': msg.role,
            'service_type': msg.service_type,
            'budget': msg.budget,
            'timeline': msg.timeline,
            'niche': msg.niche,
            'session_id': msg.session_id,
        }
        persisted = insert_contact_idempotent(session, payload)

    return {
        'persisted': persisted,
        'contact_id': msg.contact_id,
        'created_at': msg.created_at.isoformat(),
    }


def send_owner_email_safe(
    msg: ContactQueueMessage,
    persist_result: dict[str, Any],
) -> str:
    """Envia email al owner; si SES falla, propaga (handler marca failure).

    A diferencia del flujo sync legacy (que silenciaba el error con un
    log + metrica), aqui el fallo del email RE-ENCOLA el mensaje
    completo via `batchItemFailures` para que SQS lo reintente. Esto es
    seguro porque `save_contact_idempotent` es no-op en reintentos: el
    contact se persiste UNA vez y solo el email se reintenta hasta
    success.

    El owner puede recibir el mismo email max 3 veces
    (max_receive_count) antes del DLQ. Es un trade-off aceptable vs
    perder el lead silenciosamente.

    Parameters
    ----------
    msg : ContactQueueMessage
        Mensaje validado del worker.
    persist_result : dict
        Resultado de `save_contact_idempotent` (contact_id, created_at,
        persisted).

    Returns
    -------
    str
        SES MessageId.
    """
    from_address = get_secret_by_name(
        'ses-from-address',
        local_env='EMAIL_FROM',
    )
    recipients_raw = get_secret_by_name(
        'owner-email',
        local_env='OWNER_EMAIL',
    )
    recipients = [r.strip() for r in recipients_raw.split(',') if r.strip()]

    html_template = (_TEMPLATES_DIR / 'owner_email.html').read_text(
        encoding='utf-8',
    )
    text_template = (_TEMPLATES_DIR / 'owner_email.txt').read_text(
        encoding='utf-8',
    )

    # Render context: campos del mensaje + metadata de persistencia +
    # niche default 'generic' para los templates.
    context = msg.model_dump()
    context.update(persist_result)
    context.setdefault('niche', 'generic')
    if not context.get('niche'):
        context['niche'] = 'generic'

    html_body = _render_mustache_lite(html_template, context)
    text_body = _render_mustache_lite(text_template, context)

    subject = (
        f'Portfolio · Nuevo contacto de {msg.name} ({msg.niche or "generic"})'
    )

    response = send_email(
        from_address=f'The Full Stack <{from_address}>',
        to_addresses=recipients,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        reply_to=[msg.email],
    )

    message_id: str = response.get('MessageId', '')
    logger.info(
        'owner email sent',
        extra={
            'message_id': message_id,
            'contact_id': msg.contact_id,
            'recipient_count': len(recipients),
        },
    )
    return message_id


def _render_mustache_lite(template: str, context: dict[str, Any]) -> str:
    """Render minimo mustache-style: `{{var}}` y `{{#var}}block{{/var}}`.

    Mismo render que el `contact_form/services/contact_service` (copiado
    aqui para no acoplar el worker al encoder; si crece, mover a
    `shared/templates/`). Si el value es None/empty, el bloque se omite.

    NO se usa Jinja2 (peso adicional al zip de la Lambda). Esto basta
    para los templates planos de email transaccional.
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
