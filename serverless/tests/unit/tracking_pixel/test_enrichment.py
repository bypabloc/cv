"""Tests para tracking_pixel.enrichment."""

from __future__ import annotations

import pytest

from tracking_pixel.enrichment import parse_user_agent

pytestmark = pytest.mark.unit


class TestParseUserAgent:
    """parse_user_agent - browser/os/device detection."""

    def test_when_chrome_desktop_then_detects(self) -> None:
        """Given Chrome UA, When parse, Then browser=Chrome + desktop."""
        ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36'

        result = parse_user_agent(ua)

        assert result['browser'] == 'Chrome'
        assert result['browser_version'] == '118'
        assert result['os'] == 'Linux'
        assert result['device_type'] == 'desktop'

    def test_when_iphone_then_detects_ios_mobile(self) -> None:
        """Given iPhone UA, When parse, Then os=iOS + device=mobile."""
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1 Version/17.0 Mobile/15E148 Safari/604.1'

        result = parse_user_agent(ua)

        assert result['os'] == 'iOS'
        assert result['device_type'] == 'mobile'

    def test_when_bot_then_detects_bot(self) -> None:
        """Given UA con 'bot', When parse, Then device_type=bot."""
        ua = 'Googlebot/2.1 (+http://www.google.com/bot.html)'

        result = parse_user_agent(ua)

        assert result['device_type'] == 'bot'

    def test_when_none_then_returns_unknowns(self) -> None:
        """Given UA=None, When parse, Then todos unknown."""
        result = parse_user_agent(None)

        assert result['browser'] == 'unknown'
        assert result['os'] == 'unknown'
        assert result['device_type'] == 'unknown'

    def test_when_firefox_windows_then_detects(self) -> None:
        """Given Firefox Windows UA, When parse, Then ambos detectados."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64) Gecko/20100101 Firefox/120.0'

        result = parse_user_agent(ua)

        assert result['browser'] == 'Firefox'
        assert result['os'] == 'Windows'
