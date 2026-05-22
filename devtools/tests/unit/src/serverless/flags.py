"""Unit tests for serverless.flags - comandos lambda-controller.

Path mirroring: devtools/serverless/flags.py -> this file.

Cubre la grilla de comandos del CLI serverless tras la unificacion:
`tests` (un comando con --type) y `run` (un comando con --stage)
reemplazan a `test-unit`/`test-integration`/`test`/`test-coverage` y a
`run-local`/`invoke-remote`. Los comandos del modo lambda-controller
exigen --lambda o --path.
"""

import pytest


pytestmark = pytest.mark.unit


def _argv(monkeypatch, *args):
    """Setea sys.argv como `run.py serverless <args>`."""
    monkeypatch.setattr('sys.argv', ['run.py', 'serverless', *args])


class TestNewCommandsRegistered:
    """`tests` y `run` estan en VALID_COMMANDS; los viejos no."""

    @pytest.mark.parametrize(
        'command',
        ['tests', 'run', 'sam-generate', 'deploy', 'deploy-infra'],
    )
    def test_command_is_valid(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command in VALID_COMMANDS

    @pytest.mark.parametrize(
        'command',
        [
            'test-unit',
            'test-integration',
            'test',
            'test-coverage',
            'run-local',
            'invoke-remote',
        ],
    )
    def test_legacy_commands_removed(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command not in VALID_COMMANDS


class TestPathRequired:
    """sam-generate, run y deploy exigen --lambda o --path."""

    @pytest.mark.parametrize('command', ['sam-generate', 'run', 'deploy'])
    def test_command_without_path_raises(self, monkeypatch, command):
        _argv(monkeypatch, command)
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--lambda'):
            flag({})

    def test_command_with_path_accepted(self, monkeypatch):
        # `--path` ya viene parseado por flags_to_dict (lo hace run.py).
        _argv(monkeypatch, 'sam-generate')
        from serverless.flags import flag

        result = flag({'path': '/tmp/x'})

        assert result['command'] == 'sam-generate'
        assert result['path'] == '/tmp/x'

    def test_module_flag_satisfies_path_requirement(self, monkeypatch):
        _argv(monkeypatch, 'run', '--stage=dev')
        from serverless.flags import flag

        result = flag({'module': '/tmp/x'})

        assert result['command'] == 'run'

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

    def test_tests_command_does_not_require_path(self, monkeypatch):
        # `tests` sin target corre toda la suite: no exige --lambda/--path.
        _argv(monkeypatch, 'tests', '--type=unit')
        from serverless.flags import flag

        result = flag({'type': 'unit'})

        assert result['command'] == 'tests'


class TestTestsTypeFlag:
    """El comando `tests` exige --type valido."""

    def test_tests_without_type_raises(self, monkeypatch):
        _argv(monkeypatch, 'tests')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--type'):
            flag({})

    def test_tests_with_invalid_type_raises(self, monkeypatch):
        _argv(monkeypatch, 'tests', '--type=smoke')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--type'):
            flag({'type': 'smoke'})

    @pytest.mark.parametrize('test_type', ['unit', 'integration', 'coverage'])
    def test_tests_with_valid_type_accepted(self, monkeypatch, test_type):
        _argv(monkeypatch, 'tests', f'--type={test_type}')
        from serverless.flags import flag

        result = flag({'type': test_type})

        assert result['command'] == 'tests'
        assert result['type'] == test_type

    def test_tests_with_shared_target_accepted(self, monkeypatch):
        _argv(monkeypatch, 'tests', '--type=unit', '--shared')
        from serverless.flags import flag

        result = flag({'type': 'unit', 'shared': True})

        assert result['command'] == 'tests'
        assert result['shared'] is True


class TestRunStage:
    """`run` acepta --stage local y deployado."""

    @pytest.mark.parametrize('stage', ['local', 'dev', 'stage', 'prod'])
    def test_run_accepts_all_stages(self, monkeypatch, stage):
        _argv(monkeypatch, 'run', f'--stage={stage}')
        from serverless.flags import flag

        result = flag({'lambda': 'db', 'stage': stage})

        assert result['command'] == 'run'
        assert result['stage'] == stage


class TestDbCommandsRemoved:
    """Los comandos db-* se eliminaron: las ops de DB van via `run`."""

    @pytest.mark.parametrize(
        'command',
        [
            'db-shell',
            'db-migrate',
            'db-rollback',
            'db-current',
            'db-show-migrations',
            'db-seed',
            'db-branch',
            'db-tables',
        ],
    )
    def test_db_command_is_not_valid(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command not in VALID_COMMANDS

    def test_unknown_db_command_raises(self, monkeypatch):
        _argv(monkeypatch, 'db-migrate')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='Comando desconocido'):
            flag({})
