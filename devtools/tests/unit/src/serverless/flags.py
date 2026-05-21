"""Unit tests for serverless.flags - comandos lambda-controller.

Path mirroring: devtools/serverless/flags.py -> this file.

Cubre los comandos del modo lambda-controller (sam-generate, run-local,
deploy, invoke-remote, test-unit, test-integration) y la exigencia de
--path. El backend del portfolio son 5 stacks; cada Lambda se opera con
--path. NO hay modo legacy de SAM monolitico.
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
        [
            'sam-generate',
            'run-local',
            'deploy',
            'invoke-remote',
            'test-unit',
            'test-integration',
            'deploy-infra',
        ],
    )
    def test_command_is_valid(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command in VALID_COMMANDS

    @pytest.mark.parametrize(
        'command',
        ['build', 'validate', 'invoke', 'start-api', 'logs', 'smoke'],
    )
    def test_legacy_sam_commands_removed(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command not in VALID_COMMANDS


class TestPathRequired:
    """Los comandos lambda-controller exigen --path."""

    @pytest.mark.parametrize(
        'command',
        [
            'sam-generate',
            'run-local',
            'deploy',
            'invoke-remote',
            'test-unit',
            'test-integration',
        ],
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

    def test_lambda_flag_satisfies_path_requirement(self, monkeypatch):
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        result = flag({'lambda': 'contact_form'})

        assert result['command'] == 'deploy'
        assert result['lambda'] == 'contact_form'

    def test_error_message_mentions_lambda_flag(self, monkeypatch):
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--lambda'):
            flag({})


class TestDeployRequiresPath:
    """deploy y test-unit operan un Lambda: exigen --path (no hay legacy)."""

    def test_deploy_without_path_raises(self, monkeypatch):
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--path'):
            flag({})

    def test_deploy_with_path_accepted(self, monkeypatch):
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        result = flag({'path': 'serverless/src/db'})

        assert result['command'] == 'deploy'
        assert result['path'] == 'serverless/src/db'
