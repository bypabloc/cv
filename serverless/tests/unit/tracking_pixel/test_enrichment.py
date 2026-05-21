"""Tests para tracking_pixel.enrichment (parse UA + cache @cached SPEC-204)."""

from __future__ import annotations

import pytest

from tracking_pixel import enrichment
from tracking_pixel.enrichment import parse_user_agent

pytestmark = pytest.mark.unit

_CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    'Chrome/118.0.0.0 Safari/537.36'
)
_FIREFOX_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64) Gecko/20100101 Firefox/120.0'
)
_IPHONE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1 Version/17.0 Mobile/15E148 Safari/604.1'
)


class TestParseUserAgent:
    """parse_user_agent - browser/os/device detection."""

    def test_when_chrome_desktop_then_detects(self, tracking_aws: None) -> None:
        """
        Given un User-Agent de Chrome en desktop,
        When se invoca parse_user_agent,
        Then detecta browser=Chrome, version=118, os=Linux, device=desktop.
        """
        # Arrange / Act
        result = parse_user_agent(_CHROME_UA)

        # Assert
        assert result == {
            'browser': 'Chrome',
            'browser_version': '118',
            'os': 'Linux',
            'device_type': 'desktop',
        }

    def test_when_iphone_then_detects_ios_mobile(
        self, tracking_aws: None
    ) -> None:
        """
        Given un User-Agent de iPhone,
        When se invoca parse_user_agent,
        Then detecta os=iOS y device_type=mobile.
        """
        # Arrange / Act
        result = parse_user_agent(_IPHONE_UA)

        # Assert
        assert result['os'] == 'iOS'
        assert result['device_type'] == 'mobile'

    def test_when_ipad_then_detects_tablet(self, tracking_aws: None) -> None:
        """
        Given un User-Agent de iPad,
        When se invoca parse_user_agent,
        Then device_type=tablet.
        """
        # Arrange
        ua = (
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) '
            'AppleWebKit/605.1 Version/17.0 Safari/604.1'
        )

        # Act
        result = parse_user_agent(ua)

        # Assert
        assert result['device_type'] == 'tablet'

    def test_when_bot_then_detects_bot(self, tracking_aws: None) -> None:
        """
        Given un User-Agent que contiene 'bot',
        When se invoca parse_user_agent,
        Then device_type=bot.
        """
        # Arrange
        ua = 'Googlebot/2.1 (+http://www.google.com/bot.html)'

        # Act
        result = parse_user_agent(ua)

        # Assert
        assert result['device_type'] == 'bot'

    def test_when_macos_safari_then_detects(self, tracking_aws: None) -> None:
        """
        Given un User-Agent de Safari en macOS,
        When se invoca parse_user_agent,
        Then browser=Safari y os=macOS.
        """
        # Arrange
        ua = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) '
            'AppleWebKit/605.1 Version/17.0 Safari/605.1.15'
        )

        # Act
        result = parse_user_agent(ua)

        # Assert
        assert result['browser'] == 'Safari'
        assert result['os'] == 'macOS'

    def test_when_none_then_returns_unknowns(self, tracking_aws: None) -> None:
        """
        Given user_agent=None,
        When se invoca parse_user_agent,
        Then todos los campos son 'unknown' / ''.
        """
        # Arrange / Act
        result = parse_user_agent(None)

        # Assert
        assert result == {
            'browser': 'unknown',
            'browser_version': '',
            'os': 'unknown',
            'device_type': 'unknown',
        }

    def test_when_empty_string_then_returns_unknowns(
        self, tracking_aws: None
    ) -> None:
        """
        Given user_agent='' (string vacio),
        When se invoca parse_user_agent,
        Then todos los campos son 'unknown' / ''.
        """
        # Arrange / Act
        result = parse_user_agent('')

        # Assert
        assert result == {
            'browser': 'unknown',
            'browser_version': '',
            'os': 'unknown',
            'device_type': 'unknown',
        }

    def test_when_firefox_windows_then_detects(
        self, tracking_aws: None
    ) -> None:
        """
        Given un User-Agent de Firefox en Windows,
        When se invoca parse_user_agent,
        Then browser=Firefox y os=Windows.
        """
        # Arrange / Act
        result = parse_user_agent(_FIREFOX_UA)

        # Assert
        assert result['browser'] == 'Firefox'
        assert result['os'] == 'Windows'


class TestParseUserAgentCache:
    """parse_user_agent - el @cached evita re-ejecutar el regex (SPEC-204)."""

    def test_when_same_ua_twice_then_second_call_skips_regex(
        self, tracking_aws: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given el mismo User-Agent procesado dos veces en una Lambda warm [AC-1],
        When se invoca parse_user_agent la segunda vez,
        Then el resultado viene del cache y el regex de browser no se
        re-ejecuta (el .search del patron Chrome solo corre una vez).
        """

        # Arrange: proxy contador alrededor del patron Chrome (re.Pattern
        # tiene atributos read-only, asi que se sustituye el patron entero).
        class _CountingPattern:
            def __init__(self, real: object) -> None:
                self._real = real
                self.calls: list[str] = []

            def search(self, text: str) -> object:
                self.calls.append(text)
                return self._real.search(text)

        chrome_name, chrome_pattern = enrichment._BROWSER_PATTERNS[0]
        counter = _CountingPattern(chrome_pattern)
        patched = (
            (chrome_name, counter),
            *enrichment._BROWSER_PATTERNS[1:],
        )
        monkeypatch.setattr(enrichment, '_BROWSER_PATTERNS', patched)

        # Act: dos invocaciones con el MISMO User-Agent
        first = parse_user_agent(_CHROME_UA)
        second = parse_user_agent(_CHROME_UA)

        # Assert: la 2a invocacion sirvio del cache, sin re-ejecutar el regex
        assert first == second
        assert counter.calls == [_CHROME_UA]

    def test_when_same_ua_twice_then_same_result(
        self, tracking_aws: None
    ) -> None:
        """
        Given el mismo User-Agent procesado dos veces [AC-1],
        When se invoca parse_user_agent,
        Then ambas invocaciones devuelven exactamente el mismo dict.
        """
        # Arrange / Act
        first = parse_user_agent(_IPHONE_UA)
        second = parse_user_agent(_IPHONE_UA)

        # Assert
        assert first == second
        assert second == {
            'browser': 'Safari',
            'browser_version': '17',
            'os': 'iOS',
            'device_type': 'mobile',
        }

    def test_when_distinct_ua_then_no_cache_collision(
        self, tracking_aws: None
    ) -> None:
        """
        Given dos User-Agent distintos [AC-2],
        When se procesan ambos,
        Then cada uno produce su propio resultado (la cache no colisiona keys).
        """
        # Arrange / Act
        chrome = parse_user_agent(_CHROME_UA)
        firefox = parse_user_agent(_FIREFOX_UA)

        # Assert: keys distintas -> resultados distintos, sin contaminacion
        assert chrome['browser'] == 'Chrome'
        assert firefox['browser'] == 'Firefox'

    def test_when_ua_cached_then_entry_persisted_in_cache_table(
        self, tracking_aws: None
    ) -> None:
        """
        Given un User-Agent procesado una vez [AC-1],
        When se inspecciona la tabla de cache,
        Then existe una entry bajo el namespace 'ua' con el resultado.
        """
        # Arrange
        from shared.cache import DynamoDBCache

        # Act
        parse_user_agent(_FIREFOX_UA)
        cache = DynamoDBCache()

        # Assert: la entry vive bajo el namespace 'ua' del decorator
        scan = cache.table.scan()['Items']
        ua_keys = [
            item['cache_key']
            for item in scan
            if str(item['cache_key']).startswith('ua:parse_user_agent:')
        ]
        assert len(ua_keys) == 1
