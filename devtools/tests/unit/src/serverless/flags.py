"""Unit tests for serverless.flags - comandos lambda-controller.

Path mirroring: devtools/serverless/flags.py -> this file.

Cubre los comandos nuevos (sam-generate, run-local, invoke-remote), la
exigencia de --path y la coexistencia con el modo legacy del backend SAM.
"""

import pytest


pytestmark = pytest.mark.unit


def _argv(monkeypatch, *args):
    """Setea sys.argv como `run.py serverless <args>`."""
    monkeypatch.setattr('sys.argv', ['run.py', 'serverless', *args])


class TestNewCommandsRegistered:
    """Los comandos lambda-controller estan en VALID_COMMANDS."""

    @pytest.mark.parametrize(
        'command',
        ['sam-generate', 'run-local', 'invoke-remote'],
    )
    def test_command_is_valid(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command in VALID_COMMANDS

    def test_legacy_commands_still_valid(self):
        from serverless.flags import VALID_COMMANDS

        assert 'deploy' in VALID_COMMANDS
        assert 'test-unit' in VALID_COMMANDS
        assert 'build' in VALID_COMMANDS


class TestPathRequired:
    """sam-generate / run-local / invoke-remote exigen --path."""

    @pytest.mark.parametrize(
        'command',
        ['sam-generate', 'run-local', 'invoke-remote'],
    )
    def test_command_without_path_raises(self, monkeypatch, command):
        _argv(monkeypatch, command)
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--path'):
            flag({})

    def test_command_with_path_accepted(self, monkeypatch):
        # `--path` ya viene parseado por flags_to_dict (lo hace run.py).
        _argv(monkeypatch, 'sam-generate')
        from serverless.flags import flag

        result = flag({'path': '/tmp/x'})

        assert result['command'] == 'sam-generate'
        assert result['path'] == '/tmp/x'

    def test_module_flag_satisfies_path_requirement(self, monkeypatch):
        _argv(monkeypatch, 'run-local')
        from serverless.flags import flag

        result = flag({'module': '/tmp/x'})

        assert result['command'] == 'run-local'


class TestLegacyModeUnaffected:
    """El modo legacy (backend SAM del portfolio) sigue sin --path."""

    def test_deploy_without_path_is_valid_legacy(self, monkeypatch):
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        result = flag({})

        assert result['command'] == 'deploy'
        assert result.get('path') is None

    def test_test_unit_without_path_is_valid_legacy(self, monkeypatch):
        _argv(monkeypatch, 'test-unit')
        from serverless.flags import flag

        result = flag({})

        assert result['command'] == 'test-unit'
