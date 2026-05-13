"""Unit tests for test_runner.flags - sharding/project flags for CI.

Path mirroring: devtools/test_runner/flags.py -> this file.

Cubre las flags de Playwright (--project, --shard, --shard-total,
--fail-on-flaky) que requieren --module=dashboard|landing y --type=feature
(mayo 2026: el módulo top-level `e2e` fue eliminado y cada producto
tiene su `--type=feature`). La validación existente de module/type/env
ya esta probada implicitamente al usarse en cada invocacion.
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# --project flag
# ---------------------------------------------------------------------------


class TestProjectFlag:
    """--project filtra el playwright project a ejecutar."""

    def test_accepts_project_flag(self):
        from test_runner.flags import flag

        result = flag(
            {
                'module': 'dashboard',
                'type': 'feature',
                'project': 'desktop-chromium',
            },
        )

        assert result['project'] == 'desktop-chromium'

    def test_project_defaults_to_empty(self):
        from test_runner.flags import flag

        result = flag({'module': 'dashboard', 'type': 'feature'})

        assert result.get('project', '') == ''

    def test_project_requires_feature_context(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=r'--project requiere --module=dashboard\|landing y --type=feature',
        ):
            flag(
                {
                    'module': 'server',
                    'type': 'unit',
                    'project': 'desktop-chromium',
                },
            )


# ---------------------------------------------------------------------------
# --shard / --shard-total flags
# ---------------------------------------------------------------------------


class TestShardFlags:
    """--shard y --shard-total particionan los tests para paralelismo en CI."""

    def test_accepts_shard_and_shard_total(self):
        from test_runner.flags import flag

        result = flag(
            {
                'module': 'landing',
                'type': 'feature',
                'shard': '1',
                'shard_total': '4',
            },
        )

        # Convertidos a int
        assert result['shard'] == 1
        assert result['shard_total'] == 4

    def test_shard_requires_shard_total(self):
        from test_runner.flags import flag

        with pytest.raises(ValueError, match='--shard requiere --shard-total'):
            flag({'module': 'dashboard', 'type': 'feature', 'shard': '1'})

    def test_shard_total_requires_shard(self):
        from test_runner.flags import flag

        with pytest.raises(ValueError, match='--shard-total requiere --shard'):
            flag({'module': 'dashboard', 'type': 'feature', 'shard_total': '4'})

    def test_shard_must_be_positive(self):
        from test_runner.flags import flag

        with pytest.raises(ValueError, match='--shard debe ser >= 1'):
            flag(
                {
                    'module': 'dashboard',
                    'type': 'feature',
                    'shard': '0',
                    'shard_total': '4',
                },
            )

    def test_shard_must_not_exceed_shard_total(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=r'--shard .* no puede exceder --shard-total',
        ):
            flag(
                {
                    'module': 'dashboard',
                    'type': 'feature',
                    'shard': '5',
                    'shard_total': '4',
                },
            )

    def test_shard_requires_feature_context(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=r'--shard requiere --module=dashboard\|landing y --type=feature',
        ):
            flag(
                {
                    'module': 'server',
                    'type': 'unit',
                    'shard': '1',
                    'shard_total': '4',
                },
            )


# ---------------------------------------------------------------------------
# --fail-on-flaky flag
# ---------------------------------------------------------------------------


class TestFailOnFlakyFlag:
    """--fail-on-flaky hace que un test flaky cuente como failure (modo CI)."""

    def test_accepts_fail_on_flaky(self):
        from test_runner.flags import flag

        result = flag(
            {
                'module': 'dashboard',
                'type': 'feature',
                'fail_on_flaky': True,
            },
        )

        assert result['fail_on_flaky'] is True

    def test_defaults_to_false(self):
        from test_runner.flags import flag

        result = flag({'module': 'dashboard', 'type': 'feature'})

        assert result.get('fail_on_flaky', False) is False

    def test_requires_feature_context(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=r'--fail-on-flaky requiere --module=dashboard\|landing y --type=feature',
        ):
            flag(
                {
                    'module': 'server',
                    'type': 'unit',
                    'fail_on_flaky': True,
                },
            )


# ---------------------------------------------------------------------------
# DOCKER_ENV env var como default del flag --env
# ---------------------------------------------------------------------------


class TestDockerEnvDefault:
    """El flag --env honra la env var DOCKER_ENV cuando esta seteada."""

    def test_uses_docker_env_var_as_default(self, monkeypatch):
        # Forzar reload del módulo flags para que recompute _DEFAULT_ENV
        import importlib

        monkeypatch.setenv('DOCKER_ENV', 'test')
        import test_runner.flags as flags_mod

        importlib.reload(flags_mod)
        result = flags_mod.flag({'module': 'dashboard', 'type': 'feature'})

        assert result['env'] == 'test'

        # Restore default for other tests
        monkeypatch.setenv('DOCKER_ENV', 'local')
        importlib.reload(flags_mod)

    def test_explicit_env_overrides_docker_env_var(self, monkeypatch):
        import importlib

        monkeypatch.setenv('DOCKER_ENV', 'test')
        import test_runner.flags as flags_mod

        importlib.reload(flags_mod)
        result = flags_mod.flag(
            {
                'module': 'dashboard',
                'type': 'feature',
                'env': 'local',
            },
        )

        assert result['env'] == 'local'

        monkeypatch.setenv('DOCKER_ENV', 'local')
        importlib.reload(flags_mod)

    def test_defaults_to_local_when_no_env_var(self, monkeypatch):
        import importlib

        monkeypatch.delenv('DOCKER_ENV', raising=False)
        import test_runner.flags as flags_mod

        importlib.reload(flags_mod)
        result = flags_mod.flag({'module': 'dashboard', 'type': 'feature'})

        assert result['env'] == 'local'


# ---------------------------------------------------------------------------
# Composability: mismo set de flags usadas por el CI
# ---------------------------------------------------------------------------


class TestCIFlagCombination:
    """El workflow CI invoca con las 4 flags juntas."""

    def test_full_ci_invocation_passes(self):
        from test_runner.flags import flag

        result = flag(
            {
                'module': 'dashboard',
                'type': 'feature',
                'project': 'desktop-chromium',
                'shard': '2',
                'shard_total': '4',
                'fail_on_flaky': True,
            },
        )

        assert result['module'] == 'dashboard'
        assert result['type'] == 'feature'
        assert result['project'] == 'desktop-chromium'
        assert result['shard'] == 2
        assert result['shard_total'] == 4
        assert result['fail_on_flaky'] is True


# ---------------------------------------------------------------------------
# Migration from --module=e2e (old API)
# ---------------------------------------------------------------------------


class TestE2EMigrationErrors:
    """Mayo 2026: --module=e2e y --type=e2e fueron eliminados.

    Estos tests garantizan que la API vieja produce mensajes de error claros
    sugiriendo --type=feature en lugar de fallar con stacktraces opacos.
    """

    def test_module_e2e_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match='--module=e2e fue eliminado',
        ):
            flag({'module': 'e2e', 'type': 'feature'})

    def test_module_tests_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match='--module=tests fue eliminado',
        ):
            flag({'module': 'tests', 'type': 'feature'})

    def test_type_e2e_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match='--type=e2e fue eliminado',
        ):
            flag({'module': 'dashboard', 'type': 'e2e'})
