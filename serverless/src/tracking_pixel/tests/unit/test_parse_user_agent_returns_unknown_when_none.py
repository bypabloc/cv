"""Service parse_user_agent — User-Agent ausente.

Given user_agent=None,
When se invoca parse_user_agent,
Then devuelve el enrichment con todos los campos en 'unknown'.
"""

import pytest

pytestmark = pytest.mark.unit


def test_parse_user_agent_returns_unknown_when_none(tracking_aws: None):
    from services.tracking_service import parse_user_agent

    # Act
    info = parse_user_agent(None)

    # Assert
    assert info == {
        'browser': 'unknown',
        'browser_version': '',
        'os': 'unknown',
        'device_type': 'unknown',
    }
