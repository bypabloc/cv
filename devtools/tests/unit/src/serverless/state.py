"""Unit tests for serverless.state - estado local del backend serverless.

Path mirroring: devtools/serverless/state.py -> this file.

Verifica el roundtrip de lectura/escritura, el diff CREATE/NOOP/UPDATE_*,
el determinismo de code_hash y la limpieza por stage. El filesystem se
mockea via STATE_DIR apuntado a tmp_path.
"""

import pytest


pytestmark = pytest.mark.unit


def _state(
    scope='contact-form', stage='dev', config='sha256:c', code='sha256:k'
):
    """Construye un LambdaState de prueba."""
    from serverless.state import LambdaState

    return LambdaState(
        scope=scope,
        stage=stage,
        config_hash=config,
        code_hash=code,
        resources={'function_arn': 'arn:aws:lambda:...:fn'},
        updated_at='2026-05-21T10:00:00Z',
    )


class TestLoadSave:
    """load_state / save_state hacen roundtrip por (scope, stage)."""

    def test_load_state_when_no_file_returns_none(self, monkeypatch, tmp_path):
        from serverless import state

        monkeypatch.setattr(state, 'STATE_DIR', tmp_path)

        assert state.load_state('contact-form', 'dev') is None

    def test_save_then_load_roundtrip(self, monkeypatch, tmp_path):
        from serverless import state

        monkeypatch.setattr(state, 'STATE_DIR', tmp_path)
        original = _state()

        state.save_state(original)
        loaded = state.load_state('contact-form', 'dev')

        assert loaded == original

    def test_save_state_creates_state_dir(self, monkeypatch, tmp_path):
        from serverless import state

        nested = tmp_path / 'sub' / '.state'
        monkeypatch.setattr(state, 'STATE_DIR', nested)

        state.save_state(_state())

        assert nested.is_dir()

    def test_state_path_includes_scope_and_stage(self, monkeypatch, tmp_path):
        from serverless import state

        monkeypatch.setattr(state, 'STATE_DIR', tmp_path)

        path = state.state_path('infra', 'prod')

        assert path.name == 'infra-prod.json'


class TestDiff:
    """diff() decide la accion comparando hashes previos vs nuevos."""

    def test_diff_when_no_previous_returns_create(self):
        from serverless.state import Action
        from serverless.state import diff

        assert diff(None, 'sha256:c', 'sha256:k') == Action.CREATE

    def test_diff_when_hashes_equal_returns_noop(self):
        from serverless.state import Action
        from serverless.state import diff

        previous = _state(config='sha256:c', code='sha256:k')

        assert diff(previous, 'sha256:c', 'sha256:k') == Action.NOOP

    def test_diff_when_code_changed_returns_update_code(self):
        from serverless.state import Action
        from serverless.state import diff

        previous = _state(config='sha256:c', code='sha256:OLD')

        assert diff(previous, 'sha256:c', 'sha256:NEW') == Action.UPDATE_CODE

    def test_diff_when_config_changed_returns_update_config(self):
        from serverless.state import Action
        from serverless.state import diff

        previous = _state(config='sha256:OLD', code='sha256:k')

        result = diff(previous, 'sha256:NEW', 'sha256:k')

        assert result == Action.UPDATE_CONFIG

    def test_diff_when_both_changed_returns_update_both(self):
        from serverless.state import Action
        from serverless.state import diff

        previous = _state(config='sha256:OLD', code='sha256:OLD')

        result = diff(previous, 'sha256:NEW', 'sha256:NEW2')

        assert result == Action.UPDATE_BOTH

    def test_diff_when_previous_is_partial_returns_create(self):
        from serverless.state import PARTIAL_MARKER
        from serverless.state import Action
        from serverless.state import diff

        # Un deploy que fallo a mitad guarda config_hash=PARTIAL_MARKER:
        # el siguiente diff debe re-ejecutar el CREATE.
        partial = _state(config=PARTIAL_MARKER, code='')

        assert diff(partial, 'sha256:c', 'sha256:k') == Action.CREATE


class TestConfigHash:
    """config_hash() es estable ante el orden de las claves."""

    def test_config_hash_is_key_order_independent(self):
        from serverless.state import config_hash

        first = config_hash({'memory': 256, 'timeout': 30})
        second = config_hash({'timeout': 30, 'memory': 256})

        assert first == second

    def test_config_hash_changes_with_content(self):
        from serverless.state import config_hash

        first = config_hash({'memory': 256})
        second = config_hash({'memory': 512})

        assert first != second


class TestCodeHash:
    """code_hash() es determinista e independiente del orden de archivos."""

    def test_code_hash_is_order_independent(self, tmp_path):
        from serverless.state import code_hash

        # Dos directorios con el mismo contenido, archivos creados en
        # distinto orden.
        dir_a = tmp_path / 'a'
        dir_a.mkdir()
        (dir_a / 'z.py').write_text('print(1)', encoding='utf-8')
        (dir_a / 'a.py').write_text('print(2)', encoding='utf-8')

        dir_b = tmp_path / 'b'
        dir_b.mkdir()
        (dir_b / 'a.py').write_text('print(2)', encoding='utf-8')
        (dir_b / 'z.py').write_text('print(1)', encoding='utf-8')

        assert code_hash(dir_a) == code_hash(dir_b)

    def test_code_hash_changes_when_content_changes(self, tmp_path):
        from serverless.state import code_hash

        code_dir = tmp_path / 'core'
        code_dir.mkdir()
        (code_dir / 'handler.py').write_text('v1', encoding='utf-8')
        before = code_hash(code_dir)

        (code_dir / 'handler.py').write_text('v2', encoding='utf-8')
        after = code_hash(code_dir)

        assert before != after

    def test_code_hash_when_dir_missing_returns_empty(self, tmp_path):
        from serverless.state import code_hash

        assert code_hash(tmp_path / 'nope') == 'sha256:empty'


class TestClearState:
    """clear_state() borra solo los archivos del stage indicado."""

    def test_clear_state_only_targets_stage(self, monkeypatch, tmp_path):
        from serverless import state

        monkeypatch.setattr(state, 'STATE_DIR', tmp_path)
        state.save_state(_state(scope='contact-form', stage='dev'))
        state.save_state(_state(scope='infra', stage='dev'))
        state.save_state(_state(scope='contact-form', stage='stage'))

        removed = state.clear_state('dev')

        assert sorted(p.name for p in removed) == [
            'contact-form-dev.json',
            'infra-dev.json',
        ]
        assert state.state_path('contact-form', 'stage').is_file()

    def test_clear_state_when_dir_missing_returns_empty(
        self, monkeypatch, tmp_path
    ):
        from serverless import state

        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / 'nope')

        assert state.clear_state('dev') == []
