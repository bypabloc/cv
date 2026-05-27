"""Service parse_user_agent — Googlebot se clasifica como device_type=bot.

Given el User-Agent oficial de Googlebot,
When se invoca parse_user_agent,
Then device_type='bot' (regex previo no detectaba bots). [AC-4]
"""

import pytest

pytestmark = pytest.mark.unit

_GOOGLEBOT_UA = (
    'Mozilla/5.0 (compatible; Googlebot/2.1; '
    '+http://www.google.com/bot.html)'
)


def test_parse_user_agent_classifies_googlebot(tracking_aws: None):
    from services.tracking_service import parse_user_agent

    info = parse_user_agent(_GOOGLEBOT_UA)

    assert info['device_type'] == 'bot'
