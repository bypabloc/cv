"""
Given el mismo input de un evento de tracking,
When se arma el Item con TrackingEventItem.to_item() y con la logica
  vieja de save_tracking_event (3 loops por grupos de campos),
Then ambos Items son identicos clave-a-clave (AC-7).

Garantiza que migrar tracking_service a TrackingEventItem NO cambia el
item escrito en DynamoDB.
"""

from __future__ import annotations

from typing import Any

from shared.dynamodb.models.tracking import TrackingEventItem

_LEGACY_OPTIONAL_FIELDS = (
    'page_title',
    'page_path',
    'referrer',
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_content',
    'utm_term',
    'niche',
)
_LEGACY_VIEWPORT_FIELDS = ('viewport_width', 'viewport_height')
_LEGACY_META_FIELDS = (
    'ip',
    'country',
    'user_agent',
    'browser',
    'browser_version',
    'os',
    'device_type',
)


def _legacy_build_item(
    page_id: str,
    created_at: str,
    expires_at: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Replica EXACTA del armado de Item de save_tracking_event."""
    item: dict[str, Any] = {
        'session_id': payload['session_id'],
        'page_id': page_id,
        'created_at': created_at,
        'expires_at': expires_at,
        'page_url': payload['page_url'],
        'event_id': payload['event_id'],
        'event_type_id': payload['event_type_id'],
    }
    for optional_field in _LEGACY_OPTIONAL_FIELDS:
        value = payload.get(optional_field)
        if value:
            item[optional_field] = value
    for vp_field in _LEGACY_VIEWPORT_FIELDS:
        value = payload.get(vp_field)
        if value is not None:
            item[vp_field] = value
    for meta_field in _LEGACY_META_FIELDS:
        if payload.get(meta_field):
            item[meta_field] = payload[meta_field]
    event_props = payload.get('event_props')
    if event_props:
        item['event_props'] = event_props
    return item


def test_tracking_item_to_item_matches_legacy_minimal() -> None:
    """Item identico cuando solo hay campos obligatorios."""
    # Arrange
    payload = {
        'session_id': 's1',
        'page_url': 'https://x.com',
        'event_id': 'e1',
        'event_type_id': 'page_view',
    }
    page_id = 'p1'
    created_at = '2026-05-21T10:00:00+00:00'
    expires_at = 1720000000

    # Act
    orm_item = TrackingEventItem(
        page_id=page_id,
        created_at=created_at,
        expires_at=expires_at,
        **payload,
    ).to_item()
    legacy_item = _legacy_build_item(page_id, created_at, expires_at, payload)

    # Assert
    assert orm_item == legacy_item


def test_tracking_item_to_item_matches_legacy_full() -> None:
    """Item identico con todos los campos opcionales + enrichment."""
    # Arrange
    payload = {
        'session_id': 's1',
        'page_url': 'https://x.com',
        'event_id': 'e1',
        'event_type_id': 'click',
        'page_title': 'Home',
        'page_path': '/',
        'referrer': 'https://google.com',
        'utm_source': 'newsletter',
        'utm_medium': 'email',
        'utm_campaign': 'launch',
        'utm_content': 'cta',
        'utm_term': 'fintech',
        'niche': 'fintech',
        'viewport_width': 1920,
        'viewport_height': 1080,
        'ip': '1.2.3.4',
        'country': 'CL',
        'user_agent': 'Mozilla/5.0',
        'browser': 'Chrome',
        'browser_version': '120',
        'os': 'macOS',
        'device_type': 'desktop',
        'event_props': {'scroll_pct': 80},
    }
    page_id = 'p1'
    created_at = '2026-05-21T10:00:00+00:00'
    expires_at = 1720000000

    # Act
    orm_item = TrackingEventItem(
        page_id=page_id,
        created_at=created_at,
        expires_at=expires_at,
        **payload,
    ).to_item()
    legacy_item = _legacy_build_item(page_id, created_at, expires_at, payload)

    # Assert
    assert orm_item == legacy_item
