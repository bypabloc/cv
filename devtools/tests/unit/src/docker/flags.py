"""Unit tests for docker.flags - command/env validation and describe().

Path mirroring: devtools/docker/flags.py -> this file.

Validación clave: comando posicional requerido (Fase 3 cambio el default
de 'help' a error explicito), removido 'docker test' (Fase 3 dejo shim),
``describe()`` retorna inventario completo (Fase 4).
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Command extraction & validation
# ---------------------------------------------------------------------------


class TestCommandExtraction:
    """``_extract_command`` requiere comando positional explicito."""

    def test_valid_command_accepted(self, monkeypatch):
        monkeypatch.setattr(
            'sys.argv', ['run.py', 'docker', 'up', '--env=local']
        )
        from docker.flags import flag

        result = flag({})
        assert result['command'] == 'up'

    def test_missing_command_raises(self, monkeypatch):
        # Antes hacia fallback silencioso a 'help' tapando errores tipeo.
        monkeypatch.setattr('sys.argv', ['run.py', 'docker'])
        from docker.flags import flag

        with pytest.raises(ValueError, match='Falta el comando'):
            flag({})

    def test_unknown_command_raises(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['run.py', 'docker', 'totally-bogus'])
        from docker.flags import flag

        with pytest.raises(ValueError, match='Comando desconocido'):
            flag({})

    def test_test_command_still_in_registry(self, monkeypatch):
        # Fase 3: 'docker test' fue removido como funcionalidad pero queda
        # en VALID_COMMANDS para que el shim de migración (cmd_test_removed)
        # tenga oportunidad de imprimir el mensaje en lugar de un 'comando
        # desconocido'.
        monkeypatch.setattr('sys.argv', ['run.py', 'docker', 'test'])
        from docker.flags import flag

        result = flag({})
        assert result['command'] == 'test'


# ---------------------------------------------------------------------------
# Environment validation
# ---------------------------------------------------------------------------


class TestEnvFlag:
    def test_default_env_is_local(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['run.py', 'docker', 'up'])
        from docker.flags import flag

        result = flag({})
        assert result['env'] == 'local'

    def test_invalid_env_raises(self, monkeypatch):
        monkeypatch.setattr(
            'sys.argv', ['run.py', 'docker', 'up', '--env=staging']
        )
        from docker.flags import flag

        with pytest.raises(ValueError, match='Ambiente inválido'):
            flag({'env': 'staging'})


# ---------------------------------------------------------------------------
# describe() — Fase 4 introspection
# ---------------------------------------------------------------------------


class TestDescribe:
    """``describe()`` expone inventario machine-readable usado por --list-*."""

    def test_describe_returns_dict_with_required_keys(self):
        from docker.flags import describe

        d = describe()
        assert d['name'] == 'docker'
        assert d['kind'] == 'subcommand'
        assert isinstance(d['summary'], str)
        assert d['summary']  # not empty
        assert isinstance(d['commands'], list)
        assert isinstance(d['flags'], dict)

    def test_every_command_has_summary_and_flags_list(self):
        from docker.flags import describe

        d = describe()
        for cmd in d['commands']:
            assert 'name' in cmd
            assert 'summary' in cmd
            assert isinstance(cmd['flags'], list)

    def test_destructive_commands_marked(self):
        from docker.flags import describe

        d = describe()
        destructive = {c['name'] for c in d['commands'] if c['destructive']}
        # Cualquier subset de los comandos esperados debe coincidir.
        assert 'rebuild' in destructive
        assert 'clean' in destructive
        assert 'db-reset' in destructive
        assert 'db-seed' in destructive
        assert 'refresh' in destructive

    def test_test_command_marked_deprecated(self):
        from docker.flags import describe

        d = describe()
        test_cmd = next(c for c in d['commands'] if c['name'] == 'test')
        assert test_cmd['deprecated'] is True

    def test_env_flag_choices_match_valid_envs(self):
        from docker.flags import VALID_ENVS
        from docker.flags import describe

        d = describe()
        assert d['flags']['env']['choices'] == VALID_ENVS

    def test_dry_run_flag_present(self):
        # Fase 4 anadio --dry-run para comandos destructivos.
        from docker.flags import describe

        d = describe()
        assert 'dry_run' in d['flags']
        assert d['flags']['dry_run']['type'] == 'bool'

    def test_output_flag_present(self):
        # Fase 4 anadio --output=json para comandos de listado.
        from docker.flags import describe

        d = describe()
        assert 'output' in d['flags']
        assert 'json' in d['flags']['output']['choices']
