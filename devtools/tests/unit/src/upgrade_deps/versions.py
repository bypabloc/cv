"""Unit tests for upgrade_deps.versions.

Path mirroring: devtools/upgrade_deps/versions.py -> this file.
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# is_prerelease
# ---------------------------------------------------------------------------


class TestIsPrerelease:
    """Detecta versiones inestables: alpha, beta, rc, dev, a/b/rc embebidos."""

    @pytest.mark.parametrize(
        'version,expected',
        [
            ('1.0.0', False),
            ('6.2.1', False),
            ('0.15.12', False),
            ('1.0.0-alpha', True),
            ('1.0.0-alpha.1', True),
            ('1.0.0-beta', True),
            ('1.0.0-beta.2', True),
            ('1.0.0-rc.1', True),
            ('1.0.0a1', True),  # PEP 440 alpha
            ('1.0.0b2', True),  # PEP 440 beta
            ('1.0.0rc1', True),  # PEP 440 rc
            ('1.0.0.dev0', True),  # PEP 440 dev
            ('1.0.0.post1', False),  # post-release SI es estable
            ('2.0.0+build.123', False),  # build metadata SI es estable
        ],
    )
    def test_classifies_versions(self, version, expected):
        from upgrade_deps.versions import is_prerelease

        assert is_prerelease(version) is expected


# ---------------------------------------------------------------------------
# pick_latest_stable
# ---------------------------------------------------------------------------


class TestPickLatestStable:
    """Selecciona la version mas alta excluyendo pre-releases."""

    def test_picks_highest_stable(self):
        from upgrade_deps.versions import pick_latest_stable

        result = pick_latest_stable(['1.0.0', '2.0.0', '1.5.0'])
        assert result == '2.0.0'

    def test_excludes_prereleases(self):
        from upgrade_deps.versions import pick_latest_stable

        # 3.0.0-rc.1 deberia ser excluido pese a ser "mayor"
        result = pick_latest_stable(['2.5.0', '3.0.0-rc.1', '2.6.0'])
        assert result == '2.6.0'

    def test_returns_none_when_only_prereleases(self):
        from upgrade_deps.versions import pick_latest_stable

        result = pick_latest_stable(['1.0.0-alpha', '1.0.0-beta'])
        assert result is None

    def test_returns_none_when_empty(self):
        from upgrade_deps.versions import pick_latest_stable

        assert pick_latest_stable([]) is None

    def test_handles_pep440_pre_releases(self):
        from upgrade_deps.versions import pick_latest_stable

        # PEP 440 pattern: 6.0.4 stable, 6.1a1 alpha
        result = pick_latest_stable(['6.0.4', '6.1a1', '5.2.0'])
        assert result == '6.0.4'

    def test_compares_versions_numerically_not_lexicographically(self):
        """1.10.0 > 1.9.0 (lexicograficamente seria al reves)."""
        from upgrade_deps.versions import pick_latest_stable

        result = pick_latest_stable(['1.9.0', '1.10.0', '1.2.0'])
        assert result == '1.10.0'


# ---------------------------------------------------------------------------
# is_newer
# ---------------------------------------------------------------------------


class TestIsNewer:
    """Compara dos versiones: True si la candidata es mayor."""

    @pytest.mark.parametrize(
        'current,candidate,expected',
        [
            ('1.0.0', '2.0.0', True),
            ('2.0.0', '1.0.0', False),
            ('1.0.0', '1.0.0', False),
            ('1.9.0', '1.10.0', True),  # numeric comparison
            ('6.0.4', '6.0.5', True),
            ('2.58.0', '2.58.0', False),
        ],
    )
    def test_compares(self, current, candidate, expected):
        from upgrade_deps.versions import is_newer

        assert is_newer(current=current, candidate=candidate) is expected


# ---------------------------------------------------------------------------
# format_with_prefix
# ---------------------------------------------------------------------------


class TestFormatWithPrefix:
    """Reaplica el prefijo original a la nueva version."""

    @pytest.mark.parametrize(
        'prefix,version,expected',
        [
            ('^', '6.2.1', '^6.2.1'),
            ('~', '6.0.3', '~6.0.3'),
            ('', '4.17.21', '4.17.21'),
            ('==', '6.0.4', '==6.0.4'),
            ('>=', '0.15.12', '>=0.15.12'),
        ],
    )
    def test_reapplies_prefix(self, prefix, version, expected):
        from upgrade_deps.versions import format_with_prefix

        assert format_with_prefix(prefix=prefix, version=version) == expected
