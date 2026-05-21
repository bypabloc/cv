"""Unit tests for serverless.resolve - resolucion del lambda objetivo.

Path mirroring: devtools/serverless/resolve.py -> this file.

Verifica los dos modos (legacy / lambda-controller) y la validacion del
manifiesto lambda.yaml: campos obligatorios, runtime, defaults.
"""

import textwrap

import pytest


pytestmark = pytest.mark.unit


_VALID_MANIFEST = textwrap.dedent(
    """
    name: payment-router
    runtime: python3.13
    handler: core.handler.lambda_handler
    """,
).strip()


def _write_lambda(tmp_path, manifest_text):
    """Crea un dir de lambda con lambda.yaml y devuelve el path."""
    lambda_dir = tmp_path / 'my-lambda'
    lambda_dir.mkdir()
    (lambda_dir / 'lambda.yaml').write_text(manifest_text, encoding='utf-8')
    return lambda_dir


class TestResolveMode:
    """resolve_lambda elige modo legacy vs lambda-controller."""

    def test_no_path_returns_legacy_mode(self):
        from serverless.resolve import resolve_lambda

        resolved = resolve_lambda({})

        assert resolved.mode == 'legacy'

    def test_legacy_mode_is_not_lambda_controller(self):
        from serverless.resolve import resolve_lambda

        resolved = resolve_lambda({})

        assert resolved.is_lambda_controller is False

    def test_path_with_manifest_returns_lambda_controller(self, tmp_path):
        from serverless.resolve import resolve_lambda

        lambda_dir = _write_lambda(tmp_path, _VALID_MANIFEST)

        resolved = resolve_lambda({'path': str(lambda_dir)})

        assert resolved.mode == 'lambda-controller'

    def test_module_flag_is_alias_of_path(self, tmp_path):
        from serverless.resolve import resolve_lambda

        lambda_dir = _write_lambda(tmp_path, _VALID_MANIFEST)

        resolved = resolve_lambda({'module': str(lambda_dir)})

        assert resolved.is_lambda_controller is True


class TestResolveByLambdaName:
    """resolve_lambda con --lambda resuelve un nombre corto contra src/."""

    def test_lambda_name_resolves_to_src_directory(self):
        from serverless.resolve import resolve_lambda

        resolved = resolve_lambda({'lambda': 'contact_form'})

        assert resolved.mode == 'lambda-controller'
        assert resolved.root.name == 'contact_form'

    def test_lambda_name_reads_the_manifest(self):
        from serverless.resolve import resolve_lambda

        resolved = resolve_lambda({'lambda': 'db'})

        assert resolved.manifest['name'] == 'db'

    def test_unknown_lambda_name_raises_listing_valid_ones(self):
        from serverless.resolve import ManifestError
        from serverless.resolve import resolve_lambda

        with pytest.raises(ManifestError, match='No existe el lambda'):
            resolve_lambda({'lambda': 'nonexistent-lambda'})

    def test_directory_without_manifest_raises_structure_error(
        self, monkeypatch, tmp_path
    ):
        from serverless import resolve

        # Apunta el resolver a un src/ de prueba con una carpeta que NO
        # cumple la estructura lambda-controller (sin lambda.yaml).
        fake_src = tmp_path / 'src'
        (fake_src / 'broken').mkdir(parents=True)
        monkeypatch.setattr(resolve, '_PORTFOLIO_LAMBDAS_DIR', fake_src)

        with pytest.raises(resolve.ManifestError, match='NO cumple'):
            resolve.resolve_lambda({'lambda': 'broken'})

    def test_available_lambdas_lists_real_lambdas(self):
        from serverless.resolve import available_lambdas

        names = available_lambdas()

        assert names == [
            'contact_form',
            'db',
            'stream_processor',
            'tracking_pixel',
        ]


class TestManifestValidation:
    """_read_manifest valida campos obligatorios, runtime y defaults."""

    def test_missing_runtime_raises_naming_the_field(self, tmp_path):
        from serverless.resolve import ManifestError
        from serverless.resolve import resolve_lambda

        lambda_dir = _write_lambda(
            tmp_path,
            'name: x\nhandler: core.handler.lambda_handler\n',
        )

        with pytest.raises(ManifestError, match='runtime'):
            resolve_lambda({'path': str(lambda_dir)})

    def test_invalid_runtime_raises(self, tmp_path):
        from serverless.resolve import ManifestError
        from serverless.resolve import resolve_lambda

        lambda_dir = _write_lambda(
            tmp_path,
            'name: x\nruntime: python3.8\n'
            'handler: core.handler.lambda_handler\n',
        )

        with pytest.raises(ManifestError, match='runtime invalido'):
            resolve_lambda({'path': str(lambda_dir)})

    def test_defaults_applied_when_omitted(self, tmp_path):
        from serverless.resolve import resolve_lambda

        lambda_dir = _write_lambda(tmp_path, _VALID_MANIFEST)

        resolved = resolve_lambda({'path': str(lambda_dir)})

        assert resolved.manifest['memory'] == 256
        assert resolved.manifest['timeout'] == 30
        assert resolved.manifest['region'] == 'us-east-1'

    def test_missing_manifest_raises(self, tmp_path):
        from serverless.resolve import ManifestError
        from serverless.resolve import resolve_lambda

        empty_dir = tmp_path / 'empty'
        empty_dir.mkdir()

        with pytest.raises(ManifestError, match=r'lambda\.yaml'):
            resolve_lambda({'path': str(empty_dir)})

    def test_nonexistent_path_raises(self, tmp_path):
        from serverless.resolve import ManifestError
        from serverless.resolve import resolve_lambda

        with pytest.raises(ManifestError, match='no existe'):
            resolve_lambda({'path': str(tmp_path / 'nope')})
