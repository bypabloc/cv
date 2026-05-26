"""
Given un body valido producido por el encoder tracking_pixel,
When TrackingQueueMessage lo valida,
Then los campos quedan tipados y `extra='forbid'` no rechaza nada.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import valid_body


@pytest.mark.unit
def test_message_model_accepts_valid_event() -> None:
    # Arrange
    from models.message import TrackingQueueMessage

    body = valid_body(index=3, utm_source='twitter')

    # Act
    msg = TrackingQueueMessage(**body)

    # Assert
    assert msg.schema_version == 1
    assert msg.session_id == body['session_id']
    assert msg.event_id == body['event_id']
    assert msg.event_type_id == body['event_type_id']
    assert msg.page_path == '/projects?n=3'
    assert msg.niche == 'fintech'
    assert msg.viewport_width == 1920
    assert msg.viewport_height == 1080
    assert msg.utm_source == 'twitter'
    assert msg.utm_medium is None
    assert msg.ip == '1.2.3.4'
    assert msg.country == 'CL'
