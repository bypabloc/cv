"""Unit tests for ai_audit.tools.validators (la tool wrapper).

Path mirroring: devtools/ai_audit/tools/validators.py -> este archivo.

Las funciones puras (validate_*) viven en `ai_audit.validators` y tienen
su propio archivo de tests. Aca probamos la integracion:
`Validators._run_validators` que combina los 4 puros + suma score.
"""

import pytest

from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.validators import Validators


pytestmark = pytest.mark.unit


_VALID_LLMS = '# Portfolio\n\n- [Home](https://x.com/)\n'
_VALID_ROBOTS = 'User-agent: *\nAllow: /\n'
_VALID_SITEMAP = (
    '<?xml version="1.0"?><urlset><url><loc>https://x.com/</loc></url></urlset>'
)
_VALID_HOME = (
    '<html><script type="application/ld+json">'
    '{"@type":"Person","name":"Pablo"}</script></html>'
)


class TestRunValidators:
    """_run_validators arma el ToolResult final desde los recursos."""

    def test_all_pass_then_score_100(self) -> None:
        """
        Given los 4 recursos validos,
        When _run_validators,
        Then score=100 y fixes vacios.
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': _VALID_ROBOTS,
            'sitemap.xml': _VALID_SITEMAP,
            'home': _VALID_HOME,
        }

        result = tool._run_validators('https://x.com', fetched)

        assert result.score == 100
        assert result.fixes == ()
        assert result.status == Status.OK

    def test_all_missing_then_score_0(self) -> None:
        """
        Given los 4 recursos ausentes (None),
        When _run_validators,
        Then score=0 y 4 fixes.
        """
        tool = Validators()
        fetched = {
            'llms.txt': None,
            'robots.txt': None,
            'sitemap.xml': None,
            'home': None,
        }

        result = tool._run_validators('https://x.com', fetched)

        assert result.score == 0
        assert len(result.fixes) == 4

    def test_categories_one_per_check(self) -> None:
        """
        Given los 4 recursos en mix pass/fail,
        When _run_validators,
        Then categories tiene 4 keys con valores 0 o 100.
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': None,
            'sitemap.xml': _VALID_SITEMAP,
            'home': None,
        }

        result = tool._run_validators('https://x.com', fetched)

        assert set(result.categories) == {
            'llms.txt',
            'robots.txt',
            'sitemap.xml',
            'json-ld',
        }
        assert result.categories['llms.txt'] == 100
        assert result.categories['sitemap.xml'] == 100
        assert result.categories['robots.txt'] == 0
        assert result.categories['json-ld'] == 0

    def test_partial_pass_score_proporcional(self) -> None:
        """
        Given 2 de 4 pass,
        When _run_validators,
        Then score == 50.
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': _VALID_ROBOTS,
            'sitemap.xml': None,
            'home': None,
        }

        result = tool._run_validators('https://x.com', fetched)

        assert result.score == 50

    def test_robots_fail_carries_high_severity(self) -> None:
        """
        Given robots.txt con AI bots bloqueados,
        When _run_validators,
        Then el Fix correspondiente es severity HIGH (reach 8).
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': 'User-agent: GPTBot\nDisallow: /\n',
            'sitemap.xml': _VALID_SITEMAP,
            'home': _VALID_HOME,
        }

        result = tool._run_validators('https://x.com', fetched)

        robots_fix = next(f for f in result.fixes if f.category == 'robots.txt')
        assert robots_fix.severity == Severity.HIGH
        assert robots_fix.reach == 8

    def test_json_ld_fail_carries_high_severity(self) -> None:
        """
        Given home sin JSON-LD,
        When _run_validators,
        Then el Fix de json-ld es severity HIGH.
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': _VALID_ROBOTS,
            'sitemap.xml': _VALID_SITEMAP,
            'home': '<html><body>sin json-ld</body></html>',
        }

        result = tool._run_validators('https://x.com', fetched)

        json_fix = next(f for f in result.fixes if f.category == 'json-ld')
        assert json_fix.severity == Severity.HIGH

    def test_target_preserved_in_result(self) -> None:
        """
        Given un target arbitrario,
        When _run_validators,
        Then result.target == target.
        """
        tool = Validators()
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': _VALID_ROBOTS,
            'sitemap.xml': _VALID_SITEMAP,
            'home': _VALID_HOME,
        }

        result = tool._run_validators(
            'https://the-full-stack.com/cv',
            fetched,
        )

        assert result.target == 'https://the-full-stack.com/cv'


class TestRunValidatorsNeutralStatus:
    """Scoring con status='neutral' (intencional, ej. Cloudflare managed)."""

    def test_neutral_robots_counts_as_half(self) -> None:
        """
        Given robots Cloudflare-managed (status=neutral) + otros 3 pass,
        When _run_validators,
        Then score=(1+0.5+1+1)/4*100=88, category robots=50.
        """
        tool = Validators()
        cloudflare_managed = (
            '# BEGIN Cloudflare Managed content\n'
            'User-agent: GPTBot\nDisallow: /\n'
        )
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': cloudflare_managed,
            'sitemap.xml': _VALID_SITEMAP,
            'home': _VALID_HOME,
        }

        result = tool._run_validators(
            'https://x.com',
            fetched,
        )

        assert result.score == 88
        assert result.categories['robots.txt'] == 50

    def test_neutral_does_not_generate_fix(self) -> None:
        """
        Given robots Cloudflare-managed + sitemap fail,
        When _run_validators,
        Then fixes incluye sitemap pero NO robots (neutral no genera Fix).
        """
        tool = Validators()
        cloudflare_managed = (
            '# BEGIN Cloudflare Managed content\n'
            'User-agent: GPTBot\nDisallow: /\n'
        )
        fetched = {
            'llms.txt': _VALID_LLMS,
            'robots.txt': cloudflare_managed,
            'sitemap.xml': None,
            'home': _VALID_HOME,
        }

        result = tool._run_validators(
            'https://x.com',
            fetched,
        )

        fix_categories = {f.category for f in result.fixes}
        assert 'sitemap.xml' in fix_categories
        assert 'robots.txt' not in fix_categories


class TestNeedsSitemapFallback:
    """_needs_sitemap_fallback detecta sitemap.xml ausente o no-XML."""

    def test_none_content_returns_true(self) -> None:
        """Given content None (HTTP 4xx), Then fallback necesario."""
        from ai_audit.tools.validators import _needs_sitemap_fallback

        assert _needs_sitemap_fallback(None) is True

    def test_html_content_returns_true(self) -> None:
        """Given catch-all HTML del 404 de Astro, Then fallback necesario."""
        from ai_audit.tools.validators import _needs_sitemap_fallback

        assert _needs_sitemap_fallback('<!DOCTYPE html><html>...') is True

    def test_xml_urlset_returns_false(self) -> None:
        """Given XML valido (urlset), Then fallback NO necesario."""
        from ai_audit.tools.validators import _needs_sitemap_fallback

        assert (
            _needs_sitemap_fallback(
                '<?xml version="1.0"?><urlset>...</urlset>',
            )
            is False
        )

    def test_xml_sitemapindex_returns_false(self) -> None:
        """Given sitemapindex valido, Then fallback NO necesario."""
        from ai_audit.tools.validators import _needs_sitemap_fallback

        assert (
            _needs_sitemap_fallback(
                '<?xml version="1.0"?><sitemapindex>...</sitemapindex>',
            )
            is False
        )


class TestMetadata:
    """Metadata estatica del tool."""

    def test_tool_name_and_no_auth(self) -> None:
        """Given Validators(), Then TOOL_NAME y REQUIRES_AUTH esperados."""
        tool = Validators()

        assert tool.TOOL_NAME == 'validators'
        assert tool.REQUIRES_AUTH is False
        assert tool.BASE_URL == 'local'
