"""Service parse_user_agent — Chrome iOS (CriOS).

Given el User-Agent de Chrome en iOS (CriOS),
When se invoca parse_user_agent,
Then browser='Chrome Mobile iOS' / 'Mobile Safari'-family con os='iOS'
y device_type='mobile'. El regex previo NO detectaba CriOS. [AC-4]
"""

import pytest

pytestmark = pytest.mark.unit

_CHROME_IOS_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) '
    'CriOS/118.0.5993.92 Mobile/15E148 Safari/604.1'
)


def test_parse_user_agent_extracts_chrome_ios(tracking_aws: None):
    from services.tracking_service import parse_user_agent

    info = parse_user_agent(_CHROME_IOS_UA)

    assert info['os'] == 'iOS'
    assert info['device_type'] == 'mobile'
    # ua-parser identifica este UA como 'Chrome Mobile iOS' family
    assert 'Chrome' in info['browser']
