"""Unit tests for upgrade_deps.parsers.

Path mirroring: devtools/upgrade_deps/parsers.py -> this file.
"""

import json
import textwrap

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# parse_requirements_txt
# ---------------------------------------------------------------------------


class TestParseRequirementsTxt:
    """Extrae paquetes Python pinneados con ==, >= o sin operador."""

    def test_extracts_pinned_packages(self, tmp_path):
        from upgrade_deps.parsers import parse_requirements_txt

        req = tmp_path / 'requirements.txt'
        req.write_text(
            textwrap.dedent("""\
            # Python deps
            httpx==0.28.1
            boto3==1.40.0
        """)
        )

        result = parse_requirements_txt(req)

        assert result == [
            {
                'name': 'httpx',
                'operator': '==',
                'version': '0.28.1',
                'extras': '',
                'line_no': 2,
            },
            {
                'name': 'boto3',
                'operator': '==',
                'version': '1.40.0',
                'extras': '',
                'line_no': 3,
            },
        ]

    def test_extracts_packages_with_extras(self, tmp_path):
        from upgrade_deps.parsers import parse_requirements_txt

        req = tmp_path / 'requirements.txt'
        req.write_text('psycopg[binary]==3.3.4\nsentry-sdk[http]==2.58.0\n')

        result = parse_requirements_txt(req)

        assert result == [
            {
                'name': 'psycopg',
                'operator': '==',
                'version': '3.3.4',
                'extras': '[binary]',
                'line_no': 1,
            },
            {
                'name': 'sentry-sdk',
                'operator': '==',
                'version': '2.58.0',
                'extras': '[http]',
                'line_no': 2,
            },
        ]

    def test_extracts_packages_with_gte(self, tmp_path):
        from upgrade_deps.parsers import parse_requirements_txt

        req = tmp_path / 'requirements.txt'
        req.write_text('ruff>=0.15.12\nGitPython>=3.1.49\n')

        result = parse_requirements_txt(req)

        assert result == [
            {
                'name': 'ruff',
                'operator': '>=',
                'version': '0.15.12',
                'extras': '',
                'line_no': 1,
            },
            {
                'name': 'GitPython',
                'operator': '>=',
                'version': '3.1.49',
                'extras': '',
                'line_no': 2,
            },
        ]

    def test_skips_comments_and_blank_lines(self, tmp_path):
        from upgrade_deps.parsers import parse_requirements_txt

        req = tmp_path / 'requirements.txt'
        req.write_text(
            textwrap.dedent("""\
            # comment line

            httpx==0.28.1
            # another comment
            pytest==9.0.3
        """)
        )

        result = parse_requirements_txt(req)

        assert [pkg['name'] for pkg in result] == ['httpx', 'pytest']

    def test_returns_empty_when_no_packages(self, tmp_path):
        from upgrade_deps.parsers import parse_requirements_txt

        req = tmp_path / 'requirements.txt'
        req.write_text('# only comments\n\n')

        assert parse_requirements_txt(req) == []


# ---------------------------------------------------------------------------
# parse_package_json
# ---------------------------------------------------------------------------


class TestParsePackageJson:
    """Extrae dependencies, devDependencies y pnpm.overrides."""

    def test_extracts_dependencies(self, tmp_path):
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(
            json.dumps(
                {
                    'dependencies': {
                        'nuxt': '^4.4.4',
                        'vue': '^3.5.33',
                    },
                }
            )
        )

        result = parse_package_json(pkg)

        names = sorted(p['name'] for p in result)
        assert names == ['nuxt', 'vue']

        nuxt = next(p for p in result if p['name'] == 'nuxt')
        assert nuxt == {
            'name': 'nuxt',
            'prefix': '^',
            'version': '4.4.4',
            'section': 'dependencies',
        }

    def test_extracts_dev_dependencies(self, tmp_path):
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(
            json.dumps(
                {
                    'devDependencies': {
                        'vitest': '^4.1.5',
                        'typescript': '~6.0.3',
                    },
                }
            )
        )

        result = parse_package_json(pkg)

        ts = next(p for p in result if p['name'] == 'typescript')
        assert ts == {
            'name': 'typescript',
            'prefix': '~',
            'version': '6.0.3',
            'section': 'devDependencies',
        }

    def test_extracts_pnpm_overrides(self, tmp_path):
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(
            json.dumps(
                {
                    'pnpm': {
                        'overrides': {
                            'unhead': '^3.1.0',
                        },
                    },
                }
            )
        )

        result = parse_package_json(pkg)

        assert result == [
            {
                'name': 'unhead',
                'prefix': '^',
                'version': '3.1.0',
                'section': 'pnpm.overrides',
            }
        ]

    def test_handles_no_prefix(self, tmp_path):
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(
            json.dumps(
                {
                    'dependencies': {'lodash': '4.17.21'},
                }
            )
        )

        result = parse_package_json(pkg)

        assert result == [
            {
                'name': 'lodash',
                'prefix': '',
                'version': '4.17.21',
                'section': 'dependencies',
            }
        ]

    def test_skips_workspace_and_file_protocols(self, tmp_path):
        """Local refs (workspace:, file:, link:) no se consultan al registry."""
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(
            json.dumps(
                {
                    'dependencies': {
                        'real-pkg': '^1.0.0',
                        'local-a': 'workspace:*',
                        'local-b': 'file:../foo',
                        'local-c': 'link:../bar',
                    },
                }
            )
        )

        result = parse_package_json(pkg)

        names = [p['name'] for p in result]
        assert names == ['real-pkg']

    def test_returns_empty_when_no_deps(self, tmp_path):
        from upgrade_deps.parsers import parse_package_json

        pkg = tmp_path / 'package.json'
        pkg.write_text(json.dumps({'name': 'foo'}))

        assert parse_package_json(pkg) == []
