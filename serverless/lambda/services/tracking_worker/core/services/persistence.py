"""@module persistence — INSERT idempotente de un tracking_event.

`process_tracking_message` recibe la session SQLAlchemy compartida
del batch y un mensaje validado. Hace `ensure_session_and_visit` +
`insert_tracking_idempotent` (ON CONFLICT (created_at, visit_id,
page_id) DO NOTHING).

Usa savepoint Postgres (`session.begin_nested`) para aislar el
commit/rollback de ESTE mensaje sin afectar al resto del batch: si un
INSERT falla por FK violation u otra excepcion del backend, el
savepoint se revierte y la transaccion exterior sigue viva — los
otros 9 mensajes del batch se persisten igual.

Decision de cache: `parse_user_agent` reusa el namespace `ua` con
tags `['user-agent']` para que el cache de UA parsing sea compartido
con el encoder `tracking_pixel` (mismo paquete `ua_parser`, mismo
TTL 24h). En invocaciones warm donde un mismo User-Agent se repite
entre encoder y worker, el segundo lookup es un hit.
"""

from __future__ import annotations

from typing import Any

from models.message import TrackingQueueMessage
from settings.config import logger
from shared.cache import cached
from shared.db.repository import (
    ensure_session_and_visit,
    insert_tracking_idempotent,
)
from shared.db import Session as OrmSession
from ua_parser import user_agent_parser

# TTL del cache de UA parsing: 24h. Un mismo User-Agent string
# repetido en invocaciones warm no re-ejecuta el parser.
_UA_CACHE_TTL_SECONDS = 24 * 60 * 60

# Devices considerados tablet/bot por device.family + UA crudo.
_TABLET_HINTS = ('Tablet', 'iPad', 'Kindle')
_BOT_HINTS = ('bot', 'crawler', 'spider', 'http')


def _ua_device_type(parsed: dict[str, Any], ua_string: str) -> str:
    """Mapea el output de ua-parser a desktop|mobile|tablet|bot.

    Misma logica que `tracking_pixel.services.tracking_service`. Se
    duplica aqui (subpaquete del worker) para no acoplar el worker al
    Lambda encoder; ambos son consumers del mismo paquete `ua_parser`.
    """
    device_family = (parsed.get('device') or {}).get('family') or ''
    os_family = (parsed.get('os') or {}).get('family') or ''
    ua_lower = ua_string.lower()

    if any(hint in ua_lower for hint in _BOT_HINTS):
        return 'bot'
    if any(hint in device_family for hint in _TABLET_HINTS):
        return 'tablet'
    if os_family in {'iOS', 'Android'}:
        return 'mobile'
    if 'Mobile' in ua_string:
        return 'mobile'
    return 'desktop'


@cached(ttl=_UA_CACHE_TTL_SECONDS, namespace='ua', tags=['user-agent'])
def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """Parsea el User-Agent con ua-parser: browser+os+device.

    Cacheada en DynamoDB con namespace `ua` + tag `user-agent` — el
    cache key deriva del string UA. La eleccion de namespace y tags
    es deliberada: el encoder `tracking_pixel` cachea con la misma
    combinacion, por lo que los hits cruzados se reusan entre los dos
    Lambdas.

    Parameters
    ----------
    user_agent : str | None
        El header User-Agent de la request (o None si ausente).

    Returns
    -------
    dict[str, str]
        Dict con `browser`, `browser_version`, `os`, `device_type`.
    """
    if not user_agent:
        return {
            'browser': 'unknown',
            'browser_version': '',
            'os': 'unknown',
            'device_type': 'unknown',
        }

    parsed = user_agent_parser.Parse(user_agent)
    ua_block = parsed.get('user_agent') or {}
    os_block = parsed.get('os') or {}

    browser = ua_block.get('family') or 'unknown'
    browser_version = ua_block.get('major') or ''
    os_name = os_block.get('family') or 'unknown'
    device_type = _ua_device_type(parsed, user_agent)

    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'device_type': device_type,
    }


def process_tracking_message(
    session: OrmSession,
    msg: TrackingQueueMessage,
) -> bool:
    """Persiste 1 tracking_event dentro de un savepoint Postgres.

    El savepoint (`session.begin_nested`) permite que ESTE mensaje
    falle (FK violation, constraint, etc.) sin abortar la transaccion
    exterior — los demas mensajes del batch siguen procesando.

    Idempotencia: si el PK `(created_at, visit_id, page_id)` ya
    existe, el INSERT es no-op y `insert_tracking_idempotent` devuelve
    False. `visit_id` lo resuelve `ensure_session_and_visit` (UPSERT
    idempotente) — el mismo mensaje re-entregado obtiene el MISMO
    visit_id porque las 6 keys del visit-trigger coinciden.

    Parameters
    ----------
    session : OrmSession
        Session SQLAlchemy compartida del batch.
    msg : TrackingQueueMessage
        Mensaje SQS validado.

    Returns
    -------
    bool
        True si la fila se inserto; False si ya existia (no-op por
        ON CONFLICT DO NOTHING). El handler NO usa el bool hoy — se
        retorna para tests + metricas futuras.
    """
    with session.begin_nested():
        ua_info = parse_user_agent(msg.user_agent)

        # 1. UPSERT session + visit (idempotente). El helper hace
        #    bump_event_count=True; si el mensaje se re-procesa, el
        #    visit reusa y event_count se incrementa de nuevo: esto
        #    es un sobrecount conocido y aceptado en retries SQS
        #    (la PK compuesta del INSERT siguiente evita duplicados
        #    en tracking_events, que es lo que mas importa).
        _session_id, visit_id = ensure_session_and_visit(
            session,
            session_id=msg.session_id,
            ip=msg.ip,
            country=msg.country,
            user_agent=msg.user_agent,
            browser=ua_info['browser'],
            browser_version=ua_info['browser_version'],
            os_name=ua_info['os'],
            device_type=ua_info['device_type'],
            utm_source=msg.utm_source,
            utm_medium=msg.utm_medium,
            utm_campaign=msg.utm_campaign,
            utm_content=msg.utm_content,
            utm_term=msg.utm_term,
            referrer=msg.referrer,
            landing_page_path=msg.page_path,
            niche=msg.niche,
            bump_event_count=True,
        )

        # 2. INSERT tracking_event con ON CONFLICT DO NOTHING sobre la
        #    PK compuesta. Es idempotente bajo retries SQS porque
        #    page_id + created_at los pre-genera el encoder.
        payload: dict[str, Any] = {
            'session_id': msg.session_id,
            'visit_id': visit_id,
            'page_id': msg.page_id,
            'created_at': msg.created_at,
            'event_id': msg.event_id,
            'event_type_id': msg.event_type_id,
            'page_path': msg.page_path,
            'niche': msg.niche,
            'viewport_width': msg.viewport_width,
            'viewport_height': msg.viewport_height,
            'event_props': msg.event_props,
        }
        inserted = insert_tracking_idempotent(session, payload)

    # NO logear event_props (puede ser grande y opaco).
    logger.debug(
        'tracking event persisted',
        extra={
            'page_id': msg.page_id,
            'session_id': msg.session_id,
            'inserted': inserted,
        },
    )
    return inserted
