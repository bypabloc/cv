"""Unit tests for test_runner.flags - module/type/env validation.

Path mirroring: devtools/test_runner/flags.py -> this file.

Junio 2026: los flags playwright-only (--project, --shard, --shard-total,
--fail-on-flaky, --screenshots, --ui-review) fueron eliminados junto con el
módulo `feature`. Los E2E del portfolio se corren con el comando dedicado
`python devtools/run.py e2e --module=<api|admin|app>`. Estos tests cubren la
validación vigente de module/type/env y el rechazo con mensaje de migración
de los módulos/tipos eliminados (feature/e2e/tests).
"""

import pytest


pytestmark = pytest.mark.unit


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
        result = flags_mod.flag({'module': 'server', 'type': 'unit'})

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
                'module': 'server',
                'type': 'unit',
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
        result = flags_mod.flag({'module': 'server', 'type': 'unit'})

        assert result['env'] == 'local'


# ---------------------------------------------------------------------------
# Migration: --module=feature/e2e/tests y --type=feature/e2e eliminados
# ---------------------------------------------------------------------------


class TestE2EMigrationErrors:
    """Junio 2026: los módulos/tipos feature, e2e y tests fueron eliminados.

    Estos tests garantizan que la API vieja produce mensajes de error claros
    que apuntan al comando dedicado `e2e` en lugar de fallar con stacktraces
    opacos.
    """

    def test_module_feature_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=(
                r'(?s)--module=feature ya no existe en test_runner.*'
                r'devtools/run\.py e2e'
            ),
        ):
            flag({'module': 'feature', 'type': 'unit'})

    def test_module_e2e_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=(
                r'(?s)--module=e2e ya no existe en test_runner.*'
                r'devtools/run\.py e2e'
            ),
        ):
            flag({'module': 'e2e', 'type': 'unit'})

    def test_module_tests_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=(
                r'(?s)--module=tests ya no existe en test_runner.*'
                r'devtools/run\.py e2e'
            ),
        ):
            flag({'module': 'tests', 'type': 'unit'})

    def test_type_feature_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=(
                r'(?s)--type=feature ya no existe en test_runner.*'
                r'devtools/run\.py e2e'
            ),
        ):
            flag({'module': 'server', 'type': 'feature'})

    def test_type_e2e_rejected_with_migration_hint(self):
        from test_runner.flags import flag

        with pytest.raises(
            ValueError,
            match=(
                r'(?s)--type=e2e ya no existe en test_runner.*'
                r'devtools/run\.py e2e'
            ),
        ):
            flag({'module': 'server', 'type': 'e2e'})


# ---------------------------------------------------------------------------
# Playwright-only flags eliminados: ya no son válidos
# ---------------------------------------------------------------------------


class TestPlaywrightFlagsRemoved:
    """Los flags playwright-only fueron eliminados de ALLOWED_FLAGS."""

    @pytest.mark.parametrize(
        'key',
        [
            'screenshots',
            'ui_review',
            'project',
            'shard',
            'shard_total',
            'fail_on_flaky',
        ],
    )
    def test_playwright_flag_is_rejected(self, key):
        from test_runner.flags import flag

        with pytest.raises(ValueError):
            flag({'module': 'server', 'type': 'unit', key: 'x'})
