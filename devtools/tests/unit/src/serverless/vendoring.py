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

    def test_vendored_dir_contains_shared_logger(self, tmp_path):
        from serverless.vendoring import vendor_shared

        lambda_root = _make_lambda(tmp_path)

        target = vendor_shared(lambda_root)

        assert (target / 'logger.py').is_file()

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
