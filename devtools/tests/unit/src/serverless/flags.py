"""Unit tests for serverless.flags - comandos lambda-controller.

Path mirroring: devtools/serverless/flags.py -> this file.

Cubre la grilla de comandos del CLI serverless tras eliminar SAM:
`deploy`/`run`/`destroy`/`status` provisionan con AWS CLI directo,
`provision-infra` reemplaza a `deploy-infra`, y `sam-generate` ya no
existe. Los comandos del modo lambda-controller (`run`, `deploy`) exigen
--lambda o --path.
"""

import pytest


pytestmark = pytest.mark.unit


def _argv(monkeypatch, *args):
    """Setea sys.argv como `run.py serverless <args>`."""
    monkeypatch.setattr('sys.argv', ['run.py', 'serverless', *args])


class TestNewCommandsRegistered:
    """La grilla nueva (sin SAM) esta en VALID_COMMANDS; los viejos no."""

    @pytest.mark.parametrize(
        'command',
        ['tests', 'run', 'deploy', 'destroy', 'status', 'provision-infra'],
    )
    def test_command_is_valid(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command in VALID_COMMANDS

    @pytest.mark.parametrize(
        'command',
        [
            'sam-generate',
            'deploy-infra',
            'deploy-resource',
            'destroy-resource',
            'test-unit',
            'run-local',
            'invoke-remote',
        ],
    )
    def test_legacy_commands_removed(self, command):
        from serverless.flags import VALID_COMMANDS

        assert command not in VALID_COMMANDS

    def test_flags_rejects_removed_sam_generate_command(self, monkeypatch):
        """AC-5.1: `sam-generate` ya no es un comando valido."""
        _argv(monkeypatch, 'sam-generate')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='Comando desconocido'):
            flag({})


class TestPathRequired:
    """run y deploy exigen --lambda o --path."""

    @pytest.mark.parametrize('command', ['run', 'deploy'])
    def test_command_without_path_raises(self, monkeypatch, command):
        _argv(monkeypatch, command)
        from serverless.flags import flag

        with pytest.raises(ValueError, match='--lambda'):
            flag({})

    def test_command_with_path_accepted(self, monkeypatch):
        # `--path` ya viene parseado por flags_to_dict (lo hace run.py).
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        result = flag({'path': '/tmp/x', 'stage': 'dev'})

        assert result['command'] == 'deploy'
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


class TestRuntimeModeFlag:
    """`run` acepta --runtime-mode con choices rie|direct."""

    @pytest.mark.parametrize('mode', ['rie', 'direct'])
    def test_flags_runtime_mode_choices(self, monkeypatch, mode):
        _argv(monkeypatch, 'run', '--stage=local', f'--runtime-mode={mode}')
        from serverless.flags import flag

        result = flag({'lambda': 'db', 'stage': 'local', 'runtime_mode': mode})

        assert result['runtime_mode'] == mode

    def test_runtime_mode_invalid_raises(self, monkeypatch):
        _argv(monkeypatch, 'run', '--stage=local', '--runtime-mode=podman')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='runtime-mode'):
            flag({'lambda': 'db', 'stage': 'local', 'runtime_mode': 'podman'})

    def test_runtime_mode_defaults_to_rie(self, monkeypatch):
        _argv(monkeypatch, 'run', '--stage=local')
        from serverless.flags import flag

        result = flag({'lambda': 'db', 'stage': 'local'})

        assert result['runtime_mode'] == 'rie'


class TestRemovedSamFlags:
    """Los flags de SAM (--guided, --debug) ya no se aceptan."""

    @pytest.mark.parametrize('removed_flag', ['guided', 'debug'])
    def test_flags_rejects_guided_flag(self, monkeypatch, removed_flag):
        """AC-5.7: --guided / --debug eran de SAM, ya no son validos."""
        _argv(monkeypatch, 'deploy', '--stage=dev')
        from serverless.flags import flag

        with pytest.raises(ValueError, match='no permitidas'):
            flag({'lambda': 'contact_form', 'stage': 'dev', removed_flag: True})


class TestDestroyConfirmation:
    """`destroy` no es destructive-by-confirm: usa su flag --yes."""

    def test_flags_destroy_accepts_yes_flag(self, monkeypatch):
        _argv(monkeypatch, 'destroy', '--stage=dev', '--yes')
        from serverless.flags import flag

        result = flag({'stage': 'dev', 'yes': True})

        assert result['command'] == 'destroy'
        assert result['yes'] is True

    def test_flags_destroy_without_yes_still_parses(self, monkeypatch):
        # flags.py no exige --yes (lo valida cmd_destroy); el parseo pasa.
        _argv(monkeypatch, 'destroy', '--stage=dev')
        from serverless.flags import flag

        result = flag({'stage': 'dev'})

        assert result['command'] == 'destroy'
        assert result['yes'] is False


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
