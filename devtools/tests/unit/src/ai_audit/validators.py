"""Unit tests for ai_audit.validators.

Path mirroring: devtools/ai_audit/validators.py -> este archivo.
"""

import pytest

from ai_audit.validators import normalize_url
from ai_audit.validators import validate_json_ld_person
from ai_audit.validators import validate_llms_txt
from ai_audit.validators import validate_robots_ai_bots
from ai_audit.validators import validate_sitemap_xml


pytestmark = pytest.mark.unit


class TestValidateLlmsTxt:
    """validate_llms_txt: spec llmstxt.org compliance."""

    def test_missing_content_returns_fail(self) -> None:
        """Given content None, When validate, Then fail con mensaje claro."""
        result = validate_llms_txt(None)

        assert result['status'] == 'fail'
        assert 'ausente' in result['message']

    def test_empty_content_returns_fail(self) -> None:
        """Given content '', When validate, Then fail."""
        result = validate_llms_txt('')

        assert result['status'] == 'fail'

    def test_no_h1_header_returns_fail(self) -> None:
        """Given content sin '# ' al inicio, When validate, Then fail."""
        content = 'Some text without header\n- [link](https://x.com)'

        result = validate_llms_txt(content)

        assert result['status'] == 'fail'
        assert 'H1' in result['message']

    def test_no_links_returns_fail(self) -> None:
        """Given H1 pero sin links markdown, When validate, Then fail."""
        content = '# Portfolio\n\nJust prose, no links.'

        result = validate_llms_txt(content)

        assert result['status'] == 'fail'
        assert 'links' in result['message']

    def test_valid_minimal_content_returns_pass(self) -> None:
        """Given H1 + 1 link, When validate, Then pass con counts."""
        content = '# Portfolio\n\n- [Home](https://example.com/)\n'

        result = validate_llms_txt(content)

        assert result['status'] == 'pass'
        assert result['details']['links_found'] == 1

    def test_oversized_content_returns_fail(self) -> None:
        """Given content > 100 KB, When validate, Then fail (tamano)."""
        big = '# Big\n\n' + ('- [a](https://x.com)\n' * 6000)

        result = validate_llms_txt(big)

        assert result['status'] == 'fail'
        assert 'tamano' in result['message']

    def test_counts_multiple_links_exactly(self) -> None:
        """Given content con 3 links, When validate, Then count==3."""
        content = (
            '# Portfolio\n\n'
            '- [Home](https://x.com/)\n'
            '- [About](https://x.com/about)\n'
            '- [CV](https://x.com/cv)\n'
        )

        result = validate_llms_txt(content)

        assert result['details']['links_found'] == 3


class TestValidateRobotsAiBots:
    """validate_robots_ai_bots: deteccion de AI bots bloqueados."""

    def test_missing_robots_returns_fail(self) -> None:
        """Given content None, When validate, Then fail."""
        result = validate_robots_ai_bots(None)

        assert result['status'] == 'fail'

    def test_default_robots_no_block_returns_pass(self) -> None:
        """Given robots.txt allow-all sin AI bots mencionados, Then pass."""
        content = 'User-agent: *\nAllow: /\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'pass'

    def test_gptbot_disallow_all_returns_fail(self) -> None:
        """Given User-agent: GPTBot + Disallow: /, Then fail."""
        content = 'User-agent: GPTBot\nDisallow: /\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'fail'
        assert 'GPTBot' in result['message']
        assert 'GPTBot' in result['details']['blocked']

    def test_claudebot_disallow_all_returns_fail(self) -> None:
        """Given User-agent: ClaudeBot + Disallow: /, Then fail."""
        content = 'User-agent: ClaudeBot\nDisallow: /\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'fail'
        assert 'ClaudeBot' in result['details']['blocked']

    def test_multiple_ai_bots_blocked_all_reported(self) -> None:
        """Given 2 AI bots con Disallow: /, Then ambos en details."""
        content = (
            'User-agent: GPTBot\nDisallow: /\n\n'
            'User-agent: PerplexityBot\nDisallow: /\n'
        )

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'fail'
        assert set(result['details']['blocked']) == {'GPTBot', 'PerplexityBot'}

    def test_ai_bot_partial_disallow_is_pass(self) -> None:
        """Given GPTBot con Disallow: /admin (parcial), Then pass."""
        content = 'User-agent: GPTBot\nDisallow: /admin\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'pass'

    def test_case_insensitive_match(self) -> None:
        """Given 'user-agent: gptbot' (minusculas), Then detecta el bloqueo."""
        content = 'user-agent: gptbot\ndisallow: /\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'fail'
        assert 'GPTBot' in result['details']['blocked']

    def test_comments_are_ignored(self) -> None:
        """Given comentarios # antes de directivas, Then parsea bien."""
        content = (
            '# my robots\nUser-agent: GPTBot # AI bot\nDisallow: / # block\n'
        )

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'fail'

    def test_wildcard_user_agent_disallow_all_does_not_trigger(self) -> None:
        """Given User-agent: * + Disallow: /, NO trigger (no es un AI bot)."""
        content = 'User-agent: *\nDisallow: /\n'

        result = validate_robots_ai_bots(content)

        assert result['status'] == 'pass'


class TestValidateSitemapXml:
    """validate_sitemap_xml: validez basica."""

    def test_missing_returns_fail(self) -> None:
        """Given None, Then fail."""
        result = validate_sitemap_xml(None)

        assert result['status'] == 'fail'

    def test_non_xml_returns_fail(self) -> None:
        """Given content no-XML, Then fail."""
        result = validate_sitemap_xml('Not XML at all')

        assert result['status'] == 'fail'
        assert 'XML' in result['message']

    def test_valid_urlset_returns_pass(self) -> None:
        """Given urlset valido con <loc>, Then pass con count."""
        content = (
            '<?xml version="1.0"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://x.com/</loc></url>'
            '</urlset>'
        )

        result = validate_sitemap_xml(content)

        assert result['status'] == 'pass'
        assert result['details']['entries'] == 1
        assert result['details']['is_index'] is False

    def test_sitemap_index_returns_pass_with_is_index_true(self) -> None:
        """Given sitemapindex, Then pass con is_index True."""
        content = (
            '<?xml version="1.0"?>'
            '<sitemapindex>'
            '<sitemap><loc>https://x.com/sitemap-0.xml</loc></sitemap>'
            '<sitemap><loc>https://x.com/sitemap-1.xml</loc></sitemap>'
            '</sitemapindex>'
        )

        result = validate_sitemap_xml(content)

        assert result['status'] == 'pass'
        assert result['details']['entries'] == 2
        assert result['details']['is_index'] is True

    def test_xml_without_loc_returns_fail(self) -> None:
        """Given urlset sin <loc>, Then fail."""
        content = '<?xml version="1.0"?><urlset></urlset>'

        result = validate_sitemap_xml(content)

        assert result['status'] == 'fail'
        assert result['details']['entries'] == 0


class TestValidateJsonLdPerson:
    """validate_json_ld_person: schema.org Person/Organization."""

    def test_missing_html_returns_fail(self) -> None:
        """Given html None, Then fail."""
        result = validate_json_ld_person(None)

        assert result['status'] == 'fail'

    def test_no_json_ld_scripts_returns_fail(self) -> None:
        """Given HTML sin <script type='application/ld+json'>, Then fail."""
        result = validate_json_ld_person('<html><body>nada</body></html>')

        assert result['status'] == 'fail'
        assert 'application/ld+json' in result['message']

    def test_person_jsonld_returns_pass(self) -> None:
        """Given Person schema, Then pass con types_found."""
        html = (
            '<html><body>'
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Person",'
            '"name":"Pablo Contreras"}'
            '</script>'
            '</body></html>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'pass'
        assert 'Person' in result['details']['types_found']

    def test_organization_jsonld_returns_pass(self) -> None:
        """Given Organization schema, Then pass (cuenta como valido)."""
        html = (
            '<script type="application/ld+json">'
            '{"@type":"Organization","name":"X"}'
            '</script>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'pass'

    def test_only_website_schema_returns_fail(self) -> None:
        """Given solo WebSite schema, Then fail (no es Person/Organization)."""
        html = (
            '<script type="application/ld+json">'
            '{"@type":"WebSite","name":"x"}'
            '</script>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'fail'
        assert 'WebSite' in result['details']['types_found']

    def test_invalid_json_inside_script_is_skipped(self) -> None:
        """Given JSON malformado en 1 script + Person en otro, Then pass."""
        html = (
            '<script type="application/ld+json">not json {{{</script>'
            '<script type="application/ld+json">'
            '{"@type":"Person"}</script>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'pass'

    def test_nested_graph_extracts_inner_types(self) -> None:
        """Given JSON-LD con @graph anidado, Then extrae types internos."""
        html = (
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org",'
            '"@graph":[{"@type":"Person","name":"X"},'
            '{"@type":"WebSite","url":"https://x.com"}]}'
            '</script>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'pass'
        assert set(result['details']['types_found']) == {'Person', 'WebSite'}

    def test_type_as_list_extracts_all_strings(self) -> None:
        """Given @type=[Person, Organization], Then incluye los 2 en details."""
        html = (
            '<script type="application/ld+json">'
            '{"@type":["Person","Organization"],"name":"X"}'
            '</script>'
        )

        result = validate_json_ld_person(html)

        assert result['status'] == 'pass'
        assert set(result['details']['types_found']) == {
            'Person',
            'Organization',
        }


class TestNormalizeUrl:
    """normalize_url: construir URL absoluta."""

    def test_target_with_path_and_absolute_path_combines_base(self) -> None:
        """Given target con path + path absoluto, Then base + path."""
        result = normalize_url('https://x.com/cv', '/robots.txt')

        assert result == 'https://x.com/robots.txt'

    def test_relative_path_gets_slash_prepended(self) -> None:
        """Given path sin slash inicial, Then se agrega."""
        result = normalize_url('https://x.com', 'sitemap.xml')

        assert result == 'https://x.com/sitemap.xml'
