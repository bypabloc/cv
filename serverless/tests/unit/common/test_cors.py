"""Unit tests para common.cors."""

from __future__ import annotations

import pytest

from common.cors import cors_headers, is_allowed_origin, resolve_origin

pytestmark = pytest.mark.unit


class TestIsAllowedOrigin:
    """is_allowed_origin - whitelist 6 subdominios + localhost."""

    @pytest.mark.parametrize(
        'origin',
        [
            'https://the-full-stack.com',
            'https://hub.the-full-stack.com',
            'https://fintech.the-full-stack.com',
            'https://architect.the-full-stack.com',
            'https://leader.the-full-stack.com',
            'https://vibe.the-full-stack.com',
        ],
    )
    def test_when_prod_subdomain_then_allowed(
        self, origin: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given origin de uno de los 6 subdominios, Then allowed."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        assert is_allowed_origin(origin) is True

    def test_when_localhost_and_stage_dev_then_allowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given localhost en stage dev, Then allowed."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'dev')
        assert is_allowed_origin('http://localhost:9970') is True

    def test_when_localhost_and_stage_prod_then_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given localhost en stage prod, Then denied."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        assert is_allowed_origin('http://localhost:9970') is False

    @pytest.mark.parametrize(
        'origin',
        [
            'http://hub.localhost:9970',
            'http://fintech.localhost:9970',
            'http://architect.localhost:9970',
            'http://leader.localhost:9970',
            'http://vibe.localhost:9970',
            'http://services.localhost:9970',
            'http://hub.localhost:9971',
        ],
    )
    def test_when_subdomain_localhost_and_stage_dev_then_allowed(
        self, origin: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given http://<sub>.localhost:<port> en stage dev, Then allowed."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'dev')
        assert is_allowed_origin(origin) is True

    def test_when_subdomain_localhost_and_stage_prod_then_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given http://hub.localhost:9970 en stage prod, Then denied."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        assert is_allowed_origin('http://hub.localhost:9970') is False

    def test_when_https_localhost_subdomain_then_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given https://<sub>.localhost (no http), Then denied (solo http)."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'dev')
        assert is_allowed_origin('https://hub.localhost:9970') is False

    def test_when_evil_localhost_subdomain_path_traversal_then_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given origin malformado tipo http://evil.com.localhost.evil, Then denied."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'dev')
        assert is_allowed_origin('http://evil.localhost.attacker.com') is False
        assert is_allowed_origin('http://localhost.evil.com:9970') is False

    def test_when_evil_origin_then_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given origin no en whitelist, Then denied."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        assert is_allowed_origin('https://evil.com') is False

    def test_when_none_then_denied(self) -> None:
        """Given None, Then denied."""
        assert is_allowed_origin(None) is False


class TestResolveOrigin:
    """resolve_origin - echo del Origin matcheado, fallback al apex."""

    def test_when_valid_origin_in_headers_then_returns_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given Origin en whitelist, When resolve, Then echo."""
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        headers = {'Origin': 'https://hub.the-full-stack.com'}

        assert resolve_origin(headers) == 'https://hub.the-full-stack.com'

    def test_when_invalid_origin_then_returns_apex_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given Origin no en whitelist,
        When resolve,
        Then fallback al apex.
        """
        monkeypatch.delenv('CORS_ALLOWED_ORIGINS', raising=False)
        monkeypatch.setenv('STAGE', 'prod')
        headers = {'Origin': 'https://evil.com'}

        assert resolve_origin(headers) == 'https://the-full-stack.com'

    def test_when_no_headers_then_returns_apex_default(self) -> None:
        """Given headers vacios, When resolve, Then apex default."""
        assert resolve_origin(None) == 'https://the-full-stack.com'
        assert resolve_origin({}) == 'https://the-full-stack.com'


class TestCorsHeaders:
    """cors_headers - shape de respuesta."""

    def test_returns_5_required_headers(self) -> None:
        """Given origin, When cors_headers, Then incluye 5 headers estandar."""
        headers = cors_headers('https://the-full-stack.com')

        assert headers['Access-Control-Allow-Origin'] == 'https://the-full-stack.com'
        assert 'GET' in headers['Access-Control-Allow-Methods']
        assert 'POST' in headers['Access-Control-Allow-Methods']
        assert 'X-Turnstile-Token' in headers['Access-Control-Allow-Headers']
        assert headers['Access-Control-Max-Age'] == '600'
        assert headers['Vary'] == 'Origin'
