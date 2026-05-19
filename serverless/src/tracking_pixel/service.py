"""Business logic del tracking pixel: enrichment + persist."""

from __future__ import annotations

from typing import Any

from _shared.logger import logger
from tracking_pixel.enrichment import parse_user_agent
from tracking_pixel.persistence import save_tracking_event


def process_tracking_event(
    *,
    validated_input: dict[str, Any],
    ip: str,
    user_agent: str | None,
    country: str | None = None,
) -> dict[str, Any]:
    """
    Orquesta enrichment + persistence.

    Args:
        validated_input: dict del Pydantic TrackingEventInput (sin cf_token).
        ip: IP del cliente.
        user_agent: User-Agent header.
        country: country code CF-IPCountry.

    Returns:
        Dict con `session_id`, `page_id`, `expires_at`.
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
