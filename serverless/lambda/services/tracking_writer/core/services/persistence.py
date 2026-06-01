"""@module persistence — INSERT idempotente de un tracking_event.

`process_tracking_message` recibe la session SQLAlchemy del invoke y un
evento validado. Hace `ensure_session_and_visit` +
`insert_tracking_idempotent` (ON CONFLICT (created_at, visit_id, page_id)
DO NOTHING).

Idempotencia bajo reintentos del invoke async: AWS reintenta un invoke
`Event` hasta 2 veces si el handler lanza. El INSERT con ON CONFLICT
sobre la PK compuesta es no-op si el evento ya se persistio (el encoder
pre-genera `page_id` + `created_at`, asi que un reintento trae los mismos
valores).

Decision de cache: `parse_user_agent` reusa el namespace `ua` con tags
`['user-agent']` para que el cache de UA parsing sea compartido con el
encoder `tracking_pixel` (mismo paquete `ua_parser`, mismo TTL 24h). En
invocaciones warm donde un mismo User-Agent se repite entre encoder
(sync legacy) y writer, el segundo lookup es un hit.
"""

from __future__ import annotations

from typing import Any

from models.message import TrackingWriteModel
from settings.config import logger
from shared.cache.decorator import cached
from shared.db.repository import (
    ensure_session_and_visit,
    insert_tracking_idempotent,
)
from shared.db.sa import Session as OrmSession
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
    duplica aqui (subpaquete del writer) para no acoplar el writer al
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
    msg: TrackingWriteModel,
) -> bool:
    """Persiste 1 tracking_event (UPSERT session+visit + INSERT idempotente).

    Pasos (en la `session` que abre el controller):
    1. `ensure_session_and_visit` UPSERTea session + visit (idempotente,
       `bump_event_count=True`) y devuelve `(session_id, visit_id)`.
    2. INSERT en `tracking_events` con ON CONFLICT DO NOTHING sobre la PK
       compuesta `(created_at, visit_id, page_id)`.

    Idempotencia bajo reintentos del invoke async: el mismo evento
    re-entregado obtiene el MISMO `visit_id` (las 6 keys del visit-trigger
    coinciden) y el INSERT es no-op (PK ya existe).

    Parameters
    ----------
    session : OrmSession
        Session SQLAlchemy del invoke (la abre el controller).
    msg : TrackingWriteModel
        Evento validado.

    Returns
    -------
    bool
        True si la fila se inserto; False si ya existia (no-op por
        ON CONFLICT DO NOTHING).
    """
    ua_info = parse_user_agent(msg.user_agent)

    # 1. UPSERT session + visit (idempotente). bump_event_count=True; si
    #    el evento se re-procesa (reintento async), el visit reusa y
    #    event_count se incrementa de nuevo: sobrecount conocido y
    #    aceptado (la PK compuesta del INSERT siguiente evita duplicados
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

    # 2. INSERT tracking_event con ON CONFLICT DO NOTHING sobre la PK
    #    compuesta. Idempotente bajo reintentos del invoke async porque
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
