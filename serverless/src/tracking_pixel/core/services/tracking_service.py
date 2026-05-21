"""Service de la operacion `tracking`: enrichment + persistencia.

Concentra la logica de negocio del Lambda `tracking_pixel`:
  - parseo del User-Agent (browser / os / device type).
  - persistencia del evento en DynamoDB con TTL 60d.
  - orquestacion enrichment -> persist (`process_tracking_event`).

Regla de separacion:
  - controllers/tracking/track.py : orquesta (valida -> service -> normaliza).
  - services/tracking_service.py  : logica de negocio (este archivo).
  - utils/                        : infraestructura generica.

El service NO conoce el evento Lambda ni el evento HTTP: recibe datos ya
extraidos (validated_input, ip, user_agent, country).
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from typing import Any

from settings.config import logger

from shared.cache import cached
from shared.core.ulid import new_uuidv7
from shared.dynamodb import TrackingEventItem

# --- Persistence ---

# 60 dias en segundos. El TTL service de AWS borra el item ~48h despues
# de expires_at sin consumir WCU.
TTL_SECONDS = 60 * 24 * 60 * 60

# --- Enrichment ---

# TTL del cache de UA parsing: 24h. Un mismo User-Agent string repetido en
# invocaciones warm no re-ejecuta el regex (SPEC-204).
_UA_CACHE_TTL_SECONDS = 24 * 60 * 60

# Simple UA parser - regex patterns (sin dependencia externa para evitar bloat)
_BROWSER_PATTERNS = (
    ('Chrome', re.compile(r'Chrome/(\d+)')),
    ('Firefox', re.compile(r'Firefox/(\d+)')),
    ('Safari', re.compile(r'Version/(\d+).*Safari')),
    ('Edge', re.compile(r'Edg/(\d+)')),
)

_OS_PATTERNS = (
    ('iOS', re.compile(r'iPhone|iPad|iPod')),
    ('Android', re.compile(r'Android')),
    ('Windows', re.compile(r'Windows NT (\d+\.\d+)')),
    ('macOS', re.compile(r'Mac OS X (\d+[._]\d+)')),
    ('Linux', re.compile(r'Linux')),
)


@cached(ttl=_UA_CACHE_TTL_SECONDS, namespace='ua', tags=['user-agent'])
def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """Parsea el User-Agent: browser + os + device type.

    El resultado se cachea 24h via DynamoDB (`@cached`): la cache key se
    deriva del string User-Agent, asi UA repetidos en invocaciones warm
    no re-ejecutan el regex y UA distintos no colisionan (SPEC-204).

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

    browser, browser_version = 'unknown', ''
    for name, pattern in _BROWSER_PATTERNS:
        match = pattern.search(user_agent)
        if match:
            browser = name
            browser_version = match.group(1) if match.groups() else ''
            break

    os_name = 'unknown'
    for name, pattern in _OS_PATTERNS:
        if pattern.search(user_agent):
            os_name = name
            break

    # Device type heuristico
    if 'Mobile' in user_agent or 'iPhone' in user_agent:
        device_type = 'mobile'
    elif 'iPad' in user_agent or 'Tablet' in user_agent:
        device_type = 'tablet'
    elif 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
        device_type = 'bot'
    else:
        device_type = 'desktop'

    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'device_type': device_type,
    }


def save_tracking_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste un evento de tracking en DynamoDB con TTL +60d.

    PK: session_id, SK: page_id (UUIDv7). El TTL service de AWS borra el
    item ~48h despues de expires_at sin consumir WCU.

    Parameters
    ----------
    payload : dict[str, Any]
        Campos validados + enrichment del evento.

    Returns
    -------
    dict[str, Any]
        Dict con `session_id`, `page_id` y `expires_at` del item escrito.
    """
    page_id = new_uuidv7()
    created_at = datetime.now(UTC).isoformat()
    expires_at = int(time.time()) + TTL_SECONDS

    # TrackingEventItem (ORM) arma el Item y lo persiste: omite los campos
    # opcionales no provistos (DynamoDB no permite empty strings) y reusa
    # el resource boto3 singleton entre invocaciones warm. event_props es
    # un Map de DynamoDB (datos especificos por tipo de evento, SPEC-200).
    TrackingEventItem(
        session_id=payload['session_id'],
        page_id=page_id,
        created_at=created_at,
        expires_at=expires_at,
        page_url=payload['page_url'],
        # Identificadores del evento (SPEC-102): event_id da idempotencia,
        # event_type_id es el tipo del catalogo event_types.
        event_id=payload['event_id'],
        event_type_id=payload['event_type_id'],
        page_title=payload.get('page_title'),
        page_path=payload.get('page_path'),
        referrer=payload.get('referrer'),
        utm_source=payload.get('utm_source'),
        utm_medium=payload.get('utm_medium'),
        utm_campaign=payload.get('utm_campaign'),
        utm_content=payload.get('utm_content'),
        utm_term=payload.get('utm_term'),
        niche=payload.get('niche'),
        viewport_width=payload.get('viewport_width'),
        viewport_height=payload.get('viewport_height'),
        ip=payload.get('ip'),
        country=payload.get('country'),
        user_agent=payload.get('user_agent'),
        browser=payload.get('browser'),
        browser_version=payload.get('browser_version'),
        os=payload.get('os'),
        device_type=payload.get('device_type'),
        event_props=payload.get('event_props'),
    ).save()

    return {
        'session_id': payload['session_id'],
        'page_id': page_id,
        'expires_at': expires_at,
    }


def process_tracking_event(
    *,
    validated_input: dict[str, Any],
    ip: str,
    user_agent: str | None,
    country: str | None = None,
) -> dict[str, Any]:
    """Orquesta enrichment + persistencia del evento de tracking.

    Parameters
    ----------
    validated_input : dict[str, Any]
        Payload de tracking validado (sin cf_token).
    ip : str
        IP del cliente.
    user_agent : str | None
        Header User-Agent de la request.
    country : str | None
        Country code (CF-IPCountry).

    Returns
    -------
    dict[str, Any]
        Dict con `session_id`, `page_id` y `expires_at` del item escrito.
    """
    # Enrichment: parse UA
    ua_info = parse_user_agent(user_agent)

    payload: dict[str, Any] = {
        **validated_input,
        'ip': ip,
        'user_agent': user_agent or '',
        **ua_info,
    }
    if country:
        payload['country'] = country

    result = save_tracking_event(payload)
    logger.info(
        'tracking event persisted',
        extra={
            'session_id': result['session_id'],
            'page_id': result['page_id'],
            'device_type': ua_info['device_type'],
        },
    )
    return result
