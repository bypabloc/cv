"""End-to-end tests for the introspection contract of the devtools CLI.

Path mirroring: devtools/run.py -> this file.

Estos tests invocan el binario `python devtools/run.py` via subprocess
para validar que las flags de introspeccion (`--list-scripts`,
`--list-commands`, `--list-flags`, `--describe`) emiten JSON parseable
con el shape esperado.

Cubre Fase 7 del refactor CLI: `--describe` retorna el `describe()`
completo (union de --list-commands + --list-flags + metadata).
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = pytest.mark.unit


# Test file lives at:
#   <project>/devtools/tests/unit/src/run.py
# parents[0]=src, [1]=unit, [2]=tests, [3]=devtools, [4]=<project>.
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_RUN_PY = _PROJECT_ROOT / 'devtools' / 'run.py'


def _run_cli(args: list[str]) -> dict:
    """Run `python devtools/run.py <args>` and parse stdout as JSON.

    stderr is discarded (devtools prints uv sync messages there).
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RUN_PY), *args],
        check=True,
        capture_output=True,
        cwd=_PROJECT_ROOT,
        text=True,
    )
    return json.loads(result.stdout)


class TestListScripts:
    """`--list-scripts` is the top-level inventory entry point."""

    def test_returns_list_of_scripts(self):
        payload = _run_cli(['--list-scripts', '--output=json'])
        assert isinstance(payload, list)
        # docker, harness_init, hooks, mutation_testing, scan, test_runner,
        # upgrade_deps, verify, weak_assertion (init se auto-destruye tras el
        # primer rename del proyecto)
        assert len(payload) >= 7

    def test_each_entry_has_required_keys(self):
        payload = _run_cli(['--list-scripts', '--output=json'])
        for entry in payload:
            assert 'name' in entry
            assert 'kind' in entry
            assert 'summary' in entry
            assert 'has_describe' in entry


class TestDescribeFlag:
    """`--describe` emits the full describe() payload for a single script.

    Es la union de --list-commands (name + kind + summary + commands) +
    --list-flags (flags). Util para que zsh/bash completions y otros
    consumidores hagan una sola llamada en vez de dos.
    """

    @pytest.mark.parametrize(
        'script',
        ['scan', 'hooks', 'verify', 'test_runner', 'upgrade_deps'],
    )
    def test_monocommand_describe_has_all_keys(self, script):
        payload = _run_cli([script, '--describe', '--output=json'])
        assert 'name' in payload
        assert 'kind' in payload
        assert 'summary' in payload
        assert 'flags' in payload
        assert 'commands' in payload
        assert payload['kind'] == 'monocommand'
        assert payload['commands'] == []

    def test_docker_describe_has_commands_and_flags(self):
        payload = _run_cli(['docker', '--describe', '--output=json'])
        assert payload['kind'] == 'subcommand'
        assert len(payload['commands']) >= 16  # up, down, ps, lint, ...
        assert len(payload['flags']) >= 1

    def test_describe_summary_not_empty(self):
        payload = _run_cli(['scan', '--describe', '--output=json'])
        assert payload['summary'].strip()

    def test_describe_does_not_execute_script(self):
        # Si --describe se procesa antes de la validacion del script,
        # un script con flags requeridas (hooks --type) no debe explotar.
        payload = _run_cli(['hooks', '--describe', '--output=json'])
        assert payload['name'] == 'hooks'


class TestListCommands:
    """`--list-commands` emits metadata sin flags."""

    def test_excludes_flags_section(self):
        payload = _run_cli(['docker', '--list-commands', '--output=json'])
        assert 'flags' not in payload
        assert 'commands' in payload

    def test_includes_name_and_summary(self):
        payload = _run_cli(['docker', '--list-commands', '--output=json'])
        assert payload['name'] == 'docker'
        assert payload['summary'].strip()


class TestListFlags:
    """`--list-flags` emits ONLY the flags dict."""

    def test_returns_flags_dict_only(self):
        payload = _run_cli(['scan', '--list-flags', '--output=json'])
        assert isinstance(payload, dict)
        # No top-level metadata, solo flags.
        assert 'name' not in payload
        assert 'commands' not in payload
        # Contenido tipico de scan flags.
        assert 'git_mode' in payload
        assert 'module' in payload

    def test_each_flag_has_summary(self):
        payload = _run_cli(['test_runner', '--list-flags', '--output=json'])
        for flag_name, spec in payload.items():
            assert 'summary' in spec, f'{flag_name} sin summary'
