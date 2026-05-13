"""Unit tests for upgrade_deps.registry.

Path mirroring: devtools/upgrade_deps/registry.py -> this file.

Mockea httpx para no hacer requests reales en tests unitarios.
"""

from unittest.mock import AsyncMock

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# fetch_pypi_versions
# ---------------------------------------------------------------------------


class TestFetchPypiVersions:
    """Consulta JSON de PyPI y extrae lista de versiones."""

    @pytest.mark.asyncio
    async def test_returns_versions_list(self):
        from upgrade_deps.registry import fetch_pypi_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {
            'releases': {
                '2.58.0': [{'yanked': False}],
                '2.57.0': [{'yanked': False}],
                '1.0.0': [{'yanked': False}],
            },
        }

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_pypi_versions(client, 'sentry-sdk')

        assert sorted(result) == ['1.0.0', '2.57.0', '2.58.0']
        client.get.assert_called_once_with(
            'https://pypi.org/pypi/sentry-sdk/json',
            timeout=30.0,
        )

    @pytest.mark.asyncio
    async def test_skips_yanked_versions(self):
        from upgrade_deps.registry import fetch_pypi_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {
            'releases': {
                '2.58.0': [{'yanked': False}],
                '2.57.5': [{'yanked': True}],  # debe ser excluido
            },
        }

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_pypi_versions(client, 'pkg')

        assert result == ['2.58.0']

    @pytest.mark.asyncio
    async def test_returns_empty_when_releases_missing(self):
        from upgrade_deps.registry import fetch_pypi_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = dict

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_pypi_versions(client, 'pkg')

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_404(self):
        from upgrade_deps.registry import fetch_pypi_versions

        fake_response = AsyncMock()
        fake_response.status_code = 404

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_pypi_versions(client, 'nonexistent-pkg')

        assert result == []

    @pytest.mark.asyncio
    async def test_skips_releases_with_no_files(self):
        """Versiones sin archivos publicados se ignoran."""
        from upgrade_deps.registry import fetch_pypi_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {
            'releases': {
                '1.0.0': [{'yanked': False}],
                '0.5.0': [],  # sin archivos
            },
        }

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_pypi_versions(client, 'pkg')

        assert result == ['1.0.0']


# ---------------------------------------------------------------------------
# fetch_npm_versions
# ---------------------------------------------------------------------------


class TestFetchNpmVersions:
    """Consulta registry.npmjs.org y extrae lista de versiones."""

    @pytest.mark.asyncio
    async def test_returns_versions_list(self):
        from upgrade_deps.registry import fetch_npm_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {
            'versions': {
                '4.4.4': {'name': 'nuxt', 'version': '4.4.4'},
                '4.4.3': {'name': 'nuxt', 'version': '4.4.3'},
                '4.0.0': {'name': 'nuxt', 'version': '4.0.0'},
            },
        }

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_npm_versions(client, 'nuxt')

        assert sorted(result) == ['4.0.0', '4.4.3', '4.4.4']
        client.get.assert_called_once_with(
            'https://registry.npmjs.org/nuxt',
            timeout=30.0,
        )

    @pytest.mark.asyncio
    async def test_handles_scoped_package(self):
        """Paquetes @scope/name se URL-encodean correctamente."""
        from upgrade_deps.registry import fetch_npm_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {'versions': {'1.0.0': {}}}

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        await fetch_npm_versions(client, '@nuxt/test-utils')

        # npm permite @ y / sin encode en este endpoint
        client.get.assert_called_once_with(
            'https://registry.npmjs.org/@nuxt/test-utils',
            timeout=30.0,
        )

    @pytest.mark.asyncio
    async def test_returns_empty_on_404(self):
        from upgrade_deps.registry import fetch_npm_versions

        fake_response = AsyncMock()
        fake_response.status_code = 404

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_npm_versions(client, 'nonexistent-pkg')

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_versions_missing(self):
        from upgrade_deps.registry import fetch_npm_versions

        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = dict

        client = AsyncMock()
        client.get = AsyncMock(return_value=fake_response)

        result = await fetch_npm_versions(client, 'pkg')

        assert result == []
