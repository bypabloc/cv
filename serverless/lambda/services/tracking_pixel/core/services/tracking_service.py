"""Service de la operacion `tracking`: enrichment + persistencia.

Concentra la logica de negocio del Lambda `tracking_pixel`:
  - parseo del User-Agent (browser / os / device type).
  - persistencia del evento en Neon PostgreSQL (escritura directa).
  - orquestacion enrichment -> persist (`process_tracking_event`).

Regla de separacion:
  - controllers/tracking/track.py : orquesta (valida -> service -> normaliza).
  - services/tracking_service.py  : logica de negocio (este archivo).
  - utils/                        : infraestructura generica.

El service NO conoce el evento Lambda ni el evento HTTP: recibe datos ya
extraidos (validated_input, ip, user_agent, country).

Decision (spec `direct-neon-writes`): escribimos a Neon directo en la
misma invocacion (sin pasar por DynamoDB + Stream + stream_processor).
La tabla `tracking_events` en Neon NO tiene PK fisica, asi que no usamos
`ON CONFLICT` — aceptamos duplicados raros (sendBeacon no reintenta y
el volumen es bajo).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from settings.config import logger
from shared.cache.decorator import cached
from shared.core.ulid import new_uuidv7
from shared.db.repository import ensure_session_and_visit, insert_tracking
from shared.db.session import db_session
from shared.queue.publisher import send_to_queue
from ua_parser import user_agent_parser

# --- Enrichment ---

# TTL del cache de UA parsing: 24h. Un mismo User-Agent string repetido en
# invocaciones warm no re-ejecuta el parser (SPEC-204).
_UA_CACHE_TTL_SECONDS = 24 * 60 * 60

# Devices considerados mobile/tablet por ua-parser (family contains).
_TABLET_HINTS = ('Tablet', 'iPad', 'Kindle')
_BOT_HINTS = ('bot', 'crawler', 'spider', 'http')


def _ua_device_type(parsed: dict[str, Any], ua_string: str) -> str:
    """Mapea el output de ua-parser a desktop|mobile|tablet|bot.

    `ua-parser` devuelve `device.family` (Apple iPhone, Generic Tablet,
    Other, etc.). Combinamos con el UA crudo para clasificacion final.
    """
    device_family = (parsed.get('device') or {}).get('family') or ''
    os_family = (parsed.get('os') or {}).get('family') or ''
    ua_lower = ua_string.lower()

    if any(hint in ua_lower for hint in _BOT_HINTS):
        return 'bot'
    if any(hint in device_family for hint in _TABLET_HINTS):
        return 'tablet'
    if os_family in {'iOS', 'Android'}:
        # ua-parser marca tablets de Android como Tablet en device.family
        return 'mobile'
    if 'Mobile' in ua_string:
        return 'mobile'
    return 'desktop'


@cached(ttl=_UA_CACHE_TTL_SECONDS, namespace='ua', tags=['user-agent'])
def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """Parsea el User-Agent con ua-parser (uap-python): browser+os+device.

    El resultado se cachea 24h via DynamoDB (`@cached`): la cache key
    deriva del string UA. ua-parser usa los regex specs mantenidos por
    la comunidad (uap-core) — mejor accuracy que el regex custom previo,
    en particular para Chrome iOS WebView, browsers embebidos y bots.

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


def save_tracking_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste sessions + session_visits + tracking_events en 1 tx.

    Spec sessions-normalize: el INSERT del tracking_event va junto con
    el UPSERT de su `session` y `session_visit` en la MISMA transaccion
    (atomicidad — si el INSERT falla, todo rollback).

    Pasos:
    1. `ensure_session_and_visit(...)` UPSERTea session + visit y
       devuelve `(session_id, visit_id)`. El helper incrementa
       `event_count` del visit en 1 (bump_event_count=True).
    2. INSERT en `tracking_events` con el `visit_id` retornado.
    3. Commit al salir del `with db_session()`.

    Genera `page_id = uuidv7()` server-side y arma el payload ORM:
    `created_at` con `datetime.now(UTC)`, `event_props` como dict
    (SQLAlchemy lo adapta a JSONB). Las columnas ip/country/ua/utm_*
    se persisten en sessions/session_visits via el helper — el ORM de
    tracking_events YA NO las tiene.

    Parameters
    ----------
    payload : dict[str, Any]
        Campos validados + enrichment del evento.

    Returns
    -------
    dict[str, Any]
        Dict con `session_id`, `page_id` y `visit_id` de la fila escrita.
    """
    page_id = new_uuidv7()
    created_at = datetime.now(UTC)

    with db_session() as session:
        # Paso 1: UPSERT session + visit (en la misma tx). El helper
        # incrementa event_count del visit en 1.
        session_id, visit_id = ensure_session_and_visit(
            session,
            session_id=payload['session_id'],
            ip=payload.get('ip'),
            country=payload.get('country'),
            user_agent=payload.get('user_agent'),
            browser=payload.get('browser'),
            browser_version=payload.get('browser_version'),
            os_name=payload.get('os'),
            device_type=payload.get('device_type'),
            utm_source=payload.get('utm_source'),
            utm_medium=payload.get('utm_medium'),
            utm_campaign=payload.get('utm_campaign'),
            utm_content=payload.get('utm_content'),
            utm_term=payload.get('utm_term'),
            referrer=payload.get('referrer'),
            landing_page_path=payload.get('landing_page_path'),
            niche=payload.get('niche'),
            bump_event_count=True,
        )

        # Paso 2: INSERT en tracking_events con visit_id.
        neon_payload: dict[str, Any] = {
            'session_id': session_id,
            'visit_id': visit_id,
            'page_id': page_id,
            'created_at': created_at,
            'event_id': payload['event_id'],
            'event_type_id': payload['event_type_id'],
            'page_path': payload.get('page_path'),
            'niche': payload.get('niche'),
            'viewport_width': payload.get('viewport_width'),
            'viewport_height': payload.get('viewport_height'),
            'event_props': payload.get('event_props'),
        }
        insert_tracking(session, neon_payload)

    return {
        'session_id': payload['session_id'],
        'page_id': page_id,
        'visit_id': visit_id,
    }


def process_tracking_event(
    *,
    validated_input: dict[str, Any],
    ip: str,
    user_agent: str | None,
    country: str | None = None,
) -> dict[str, Any]:
    """Orquesta enrichment + persistencia del evento de tracking.

    Spec sessions-normalize: el payload se enriquece con `ip`/`country`/
    UA-parser-result y se pasa entero al helper `save_tracking_event`,
    que UPSERTea session + visit y luego inserta el tracking_event.
    `landing_page_path` se deriva de `page_path` (el primer evento de
    una visit es el landing; las navegaciones internas reusan visit y
    NO actualizan `landing_page_path`).

    Parameters
    ----------
    validated_input : dict[str, Any]
        Payload de tracking validado (sin cf_token).
    ip : str
        IP del cliente.
    user_agent : str | None
        Header User-Agent de la request.
    country : str | None
        Country code (cloudfront-viewer-country o cf-ipcountry).

    Returns
    -------
    dict[str, Any]
        Dict con `session_id`, `page_id` y `visit_id` de la fila escrita.
    """
    # Enrichment: parse UA
    ua_info = parse_user_agent(user_agent)

    payload: dict[str, Any] = {
        **validated_input,
        'ip': ip,
        'user_agent': user_agent or '',
        **ua_info,
        # landing_page_path = page_path del evento. Solo se usa al
        # crear un visit nuevo (el helper ignora este campo en UPDATE).
        'landing_page_path': validated_input.get('page_path'),
    }
    if country:
        payload['country'] = country

    result = save_tracking_event(payload)
    logger.info(
        'tracking event persisted',
        extra={
            'session_id': result['session_id'],
            'page_id': result['page_id'],
            'visit_id': result['visit_id'],
            'device_type': ua_info['device_type'],
        },
    )
    return result


def enqueue_tracking_message(
    *,
    page_id: str,
    created_at: datetime,
    validated_input: dict[str, Any],
    ip: str,
    user_agent: str | None,
    country: str | None = None,
) -> str:
    """Encola un mensaje SQS hacia `tracking_worker` (modo ASYNC_MODE=true).

    NOTA: el encoder NO hace UA parsing — el worker lo hace (cacheado).
    Asi el encoder es minimo y responde rapido (TTFB ~5-15ms vs ~80ms
    del sync path). El cache del UA queda compartido (namespace='ua')
    entre encoder sync legacy y worker.

    Parameters
    ----------
    page_id : str
        UUIDv7 generado por el encoder. El worker NO lo regenera.
    created_at : datetime
        Timestamp fijado por el encoder. Evita time-skew si SQS demora.
    validated_input : dict[str, Any]
        Payload validado por TrackEventModel.tracking_payload().
    ip : str
        IP del cliente.
    user_agent : str | None
        Header User-Agent crudo. El worker lo parsea.
    country : str | None
        Country code (cloudfront-viewer-country o cf-ipcountry).

    Returns
    -------
    str
        MessageId de SQS (para correlacionar en CloudWatch).
    """
    payload: dict[str, Any] = {
        'schema_version': 1,
        'page_id': page_id,
        'created_at': created_at.isoformat(),
        'session_id': validated_input['session_id'],
        'event_id': validated_input['event_id'],
        'event_type_id': validated_input['event_type_id'],
        'page_path': validated_input.get('page_path'),
        'page_url': validated_input.get('page_url'),
        'page_title': validated_input.get('page_title'),
        'niche': validated_input.get('niche'),
        'viewport_width': validated_input['viewport_width'],
        'viewport_height': validated_input['viewport_height'],
        'device_pixel_ratio': validated_input.get('device_pixel_ratio'),
        'event_props': validated_input.get('event_props'),
        'utm_source': validated_input.get('utm_source'),
        'utm_medium': validated_input.get('utm_medium'),
        'utm_campaign': validated_input.get('utm_campaign'),
        'utm_content': validated_input.get('utm_content'),
        'utm_term': validated_input.get('utm_term'),
        'referrer': validated_input.get('referrer'),
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
    }
    return send_to_queue(
        queue_short_name='tracking-events',
        payload=payload,
    )
