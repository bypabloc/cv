"""Unit tests for serverless.vendoring - vendoring de shared/ en lambdas.

Path mirroring: devtools/serverless/vendoring.py -> this file.

Verifica que vendor_shared copia la libreria comun dentro de core/shared/,
que clean_shared la elimina, y que el context manager vendored_shared
limpia incluso ante excepciones.
"""

import pytest


pytestmark = pytest.mark.unit


def _make_lambda(tmp_path):
    """Crea un dir de lambda con core/ y devuelve su path."""
    lambda_dir = tmp_path / 'my-lambda'
    (lambda_dir / 'core').mkdir(parents=True)
    return lambda_dir


def _make_lambda_importing(tmp_path, imports: str):
    """Crea un lambda con core/handler.py que importa lo dado.

    Los imports deben referenciar subpaquetes reales de serverless/shared/
    porque vendor_shared_selective resuelve contra la fuente maestra.
    """
    lambda_dir = tmp_path / 'my-lambda'
    core = lambda_dir / 'core'
    core.mkdir(parents=True)
    (core / 'handler.py').write_text(imports, encoding='utf-8')
    return lambda_dir


class TestVendorTarget:
    """vendor_target resuelve el destino del vendor."""

    def test_target_is_core_shared_under_lambda_root(self, tmp_path):
        from serverless.vendoring import vendor_target

        target = vendor_target(tmp_path / 'lambda-x')

        assert target == tmp_path / 'lambda-x' / 'core' / 'shared'


class TestVendorShared:
    """vendor_shared copia serverless/shared/ a core/shared/."""

    def test_creates_core_shared_directory(self, tmp_path):
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)

        target = vendor_shared(lambda_root)

        assert target.is_dir()

    def test_vendored_dir_contains_shared_init(self, tmp_path):
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)

        target = vendor_shared(lambda_root)

        assert (target / '__init__.py').is_file()

    def test_vendored_dir_contains_observability_subpackage(self, tmp_path):
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)

        target = vendor_shared(lambda_root)

        assert (target / 'observability' / 'logger.py').is_file()

    def test_raises_when_lambda_has_no_core_dir(self, tmp_path):
        from serverless.vendoring import VendoringError
        from serverless.vendoring import vendor_shared

        lambda_root = tmp_path / 'no-core-lambda'
        lambda_root.mkdir()

        with pytest.raises(VendoringError):
            vendor_shared(lambda_root)

    def test_overwrites_existing_vendor(self, tmp_path):
        from serverless.vendoring import vendor_shared
        from serverless.vendoring import vendor_target

        lambda_root = _make_lambda(tmp_path)
        stale = vendor_target(lambda_root)
        stale.mkdir(parents=True)
        (stale / 'stale.py').write_text('# leftover', encoding='utf-8')

        vendor_shared(lambda_root)

        assert not (vendor_target(lambda_root) / 'stale.py').exists()

    def test_does_not_copy_pycache(self, tmp_path):
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)

        target = vendor_shared(lambda_root)

        assert not (target / '__pycache__').exists()


class TestCleanShared:
    """clean_shared elimina el vendor efimero."""

    def test_returns_true_when_vendor_existed(self, tmp_path):
        from serverless.vendoring import clean_shared
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)
        vendor_shared(lambda_root)

        removed = clean_shared(lambda_root)

        assert removed is True

    def test_returns_false_when_no_vendor(self, tmp_path):
        from serverless.vendoring import clean_shared

        lambda_root = _make_lambda(tmp_path)

        removed = clean_shared(lambda_root)

        assert removed is False

    def test_vendor_dir_gone_after_clean(self, tmp_path):
        from serverless.vendoring import clean_shared
        from serverless.vendoring import vendor_shared
        from serverless.vendoring import vendor_target

        lambda_root = _make_lambda(tmp_path)
        vendor_shared(lambda_root)

        clean_shared(lambda_root)

        assert not vendor_target(lambda_root).exists()


class TestVendoredSharedContextManager:
    """vendored_shared vendoriza al entrar, limpia al salir."""

    def test_vendor_present_inside_block(self, tmp_path):
        from serverless.vendoring import vendored_shared

        lambda_root = _make_lambda(tmp_path)

        with vendored_shared(lambda_root) as target:
            assert target.is_dir()

    def test_vendor_removed_after_block(self, tmp_path):
        from serverless.vendoring import vendor_target
        from serverless.vendoring import vendored_shared

        lambda_root = _make_lambda(tmp_path)

        with vendored_shared(lambda_root):
            pass

        assert not vendor_target(lambda_root).exists()

    def test_vendor_removed_even_on_exception(self, tmp_path):
        from serverless.vendoring import vendor_target
        from serverless.vendoring import vendored_shared

        lambda_root = _make_lambda(tmp_path)

        with pytest.raises(ValueError, match='boom'):
            with vendored_shared(lambda_root):
                raise ValueError('boom')

        assert not vendor_target(lambda_root).exists()


class TestVendorSharedSelective:
    """vendor_shared_selective copia solo el cierre de subpaquetes."""

    def test_copies_only_resolved_closure(self, tmp_path):
        from serverless.vendoring import vendor_shared_selective

        lambda_root = _make_lambda_importing(
            tmp_path, 'from shared.observability.logger import logger\n'
        )

        _, closure = vendor_shared_selective(lambda_root)

        assert closure == {'observability'}

    def test_vendor_has_resolved_subpackage(self, tmp_path):
        from serverless.vendoring import vendor_shared_selective

        lambda_root = _make_lambda_importing(
            tmp_path, 'from shared.observability.logger import logger\n'
        )

        target, _ = vendor_shared_selective(lambda_root)

        assert (target / 'observability' / 'logger.py').is_file()

    def test_vendor_omits_unused_subpackage(self, tmp_path):
        from serverless.vendoring import vendor_shared_selective

        lambda_root = _make_lambda_importing(
            tmp_path, 'from shared.observability.logger import logger\n'
        )

        target, _ = vendor_shared_selective(lambda_root)

        assert not (target / 'db').exists()

    def test_vendor_always_includes_root_init(self, tmp_path):
        from serverless.vendoring import vendor_shared_selective

        lambda_root = _make_lambda_importing(
            tmp_path, 'from shared.core.exceptions import ApplicationError\n'
        )

        target, _ = vendor_shared_selective(lambda_root)

        assert (target / '__init__.py').is_file()

    def test_transitive_closure_pulls_internal_deps(self, tmp_path):
        from serverless.vendoring import vendor_shared_selective

        lambda_root = _make_lambda_importing(
            tmp_path, 'from shared.http.responses import json_response\n'
        )

        _, closure = vendor_shared_selective(lambda_root)

        assert closure == {'http', 'core', 'aws', 'observability'}
