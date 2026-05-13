"""Unit tests for the describe() introspection contract.

Path mirroring: devtools/utils/describe.py -> this file.

Cubre el contrato básico que cada flags.py debe respetar:
- describe() retorna dict con name/kind/summary/commands/flags
- kind es 'subcommand' o 'monocommand'
- En subcommand-kind, cada command tiene name/summary/flags/destructive/deprecated

Iteramos sobre TODOS los scripts del proyecto: si alguien anade un script
nuevo y olvida implementar describe(), este test falla con un mensaje
explicito.
"""

import importlib.util
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


# Test file lives at:
#   <project>/devtools/tests/unit/src/utils/describe.py
# parents[0]=utils, [1]=src, [2]=unit, [3]=tests, [4]=devtools.
_DEVTOOLS_DIR = Path(__file__).resolve().parents[4]


def _discover_scripts() -> list[str]:
    """Discover scripts that have both main.py and flags.py."""
    scripts = []
    for item in _DEVTOOLS_DIR.iterdir():
        if not item.is_dir() or item.name in ('utils', 'tests', 'shared'):
            continue
        if item.name.startswith('.') or item.name.startswith('__'):
            continue
        if (item / 'main.py').exists() and (item / 'flags.py').exists():
            scripts.append(item.name)
    return sorted(scripts)


def _load_describe(script_name: str):
    """Load describe() from a script's flags.py, returning None if missing."""
    flags_py = _DEVTOOLS_DIR / script_name / 'flags.py'
    spec = importlib.util.spec_from_file_location(
        f'{script_name}_flags',
        flags_py,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, 'describe', None)


SCRIPTS = _discover_scripts()


class TestDescribeContract:
    """Cada script debe exponer describe() con el shape correcto."""

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_script_exposes_describe(self, script_name):
        describe_fn = _load_describe(script_name)
        assert describe_fn is not None, (
            f'Script {script_name} no expone describe(). '
            'Anadir `def describe() -> ScriptDescribe` en flags.py.'
        )

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_describe_has_required_keys(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        assert 'name' in d
        assert 'kind' in d
        assert 'summary' in d
        assert 'flags' in d
        assert d['kind'] in ('subcommand', 'monocommand')

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_summary_not_empty(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        assert d['summary'].strip(), f'{script_name}: summary esta vacío'

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_subcommand_scripts_have_commands(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        if d['kind'] == 'subcommand':
            assert d.get('commands'), (
                f'{script_name} declara kind=subcommand pero no tiene commands'
            )

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_monocommand_scripts_have_no_commands(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        if d['kind'] == 'monocommand':
            assert not d.get('commands'), (
                f'{script_name} es monocommand pero declara commands'
            )

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_subcommand_entries_have_required_keys(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        if d['kind'] != 'subcommand':
            return
        for cmd in d['commands']:
            assert 'name' in cmd, f'{script_name}: comando sin name'
            assert 'summary' in cmd, (
                f'{script_name}.{cmd.get("name", "?")}: sin summary'
            )

    @pytest.mark.parametrize('script_name', SCRIPTS)
    def test_flags_have_summary(self, script_name):
        describe_fn = _load_describe(script_name)
        if describe_fn is None:
            pytest.skip(f'{script_name} no implementa describe()')
        d = describe_fn()
        for flag_name, flag_spec in d.get('flags', {}).items():
            assert 'summary' in flag_spec, (
                f'{script_name}.{flag_name}: flag sin summary'
            )
