"""Unit tests for serverless.packaging - empaquetado del artefacto con uv.

Path mirroring: devtools/serverless/packaging.py -> this file.

Verifica que package_lambda lee las deps del pyproject.toml del lambda,
resuelve el cierre de subpaquetes de shared/, copia core/ y vendoriza el
cierre dentro de build/core/shared/. La instalacion uv (red) se mockea:
los tests verifican la logica de empaquetado, no la descarga de wheels.
"""

import textwrap

import pytest


pytestmark = pytest.mark.unit


def _make_lambda(tmp_path, *, imports: str, deps: list[str]):
    """Crea un lambda con core/handler.py + pyproject.toml.

    Los imports deben referenciar subpaquetes reales de serverless/shared/
    porque package_lambda resuelve contra la fuente maestra.
    """
    lambda_root = tmp_path / 'my-lambda'
    core = lambda_root / 'core'
    core.mkdir(parents=True)
    (core / 'handler.py').write_text(imports, encoding='utf-8')
    dep_lines = ''.join(f'  "{d}",\n' for d in deps)
    (lambda_root / 'pyproject.toml').write_text(
        textwrap.dedent(f"""\
            [project]
            name = "my-lambda"
            version = "0.1.0"
            dependencies = [
            {dep_lines}]
        """),
        encoding='utf-8',
    )
    return lambda_root


@pytest.fixture(autouse=True)
def _stub_uv_install(monkeypatch):
    """Mockea _install_dependencies para no descargar wheels en los tests."""
    from serverless import packaging

    monkeypatch.setattr(
        packaging,
        '_install_dependencies',
        lambda deps, *, target, python_version: None,
    )


class TestBuildDir:
    """build_dir resuelve el directorio de build efimero."""

    def test_build_dir_is_under_lambda_root(self, tmp_path):
        from serverless.packaging import build_dir

        target = build_dir(tmp_path / 'lambda-x')

        assert target == tmp_path / 'lambda-x' / 'build'


class TestPackageLambda:
    """package_lambda arma el artefacto en build/."""

    def test_creates_build_directory(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.observability.logger import logger\n',
            deps=['boto3>=1.34.0,<2.0'],
        )

        build, _, _ = package_lambda(lambda_root, runtime='python3.13')

        assert build.is_dir()

    def test_copies_lambda_core(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.observability.logger import logger\n',
            deps=[],
        )

        build, _, _ = package_lambda(lambda_root, runtime='python3.13')

        assert (build / 'core' / 'handler.py').is_file()

    def test_vendors_resolved_subpackage(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.observability.logger import logger\n',
            deps=[],
        )

        build, _, _ = package_lambda(lambda_root, runtime='python3.13')

        vendored = build / 'core' / 'shared' / 'observability' / 'logger.py'
        assert vendored.is_file()

    def test_omits_unused_subpackage(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.observability.logger import logger\n',
            deps=[],
        )

        build, _, _ = package_lambda(lambda_root, runtime='python3.13')

        assert not (build / 'core' / 'shared' / 'db').exists()

    def test_closure_includes_transitive_deps(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.http.responses import json_response\n',
            deps=[],
        )

        _, closure, _ = package_lambda(lambda_root, runtime='python3.13')

        assert closure == {'http', 'core', 'aws', 'observability'}

    def test_all_deps_merges_lambda_and_shared(self, tmp_path):
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.core.exceptions import ApplicationError\n',
            deps=['some-extra-pkg>=1.0'],
        )

        _, _, all_deps = package_lambda(lambda_root, runtime='python3.13')

        # shared.core aporta pydantic[email] + pydantic-settings; el lambda
        # aporta some-extra-pkg. Union ordenada.
        assert all_deps == [
            'pydantic-settings>=2.0,<3.0',
            'pydantic[email]>=2.5,<3.0',
            'some-extra-pkg>=1.0',
        ]

    def test_raises_when_no_pyproject(self, tmp_path):
        from serverless.packaging import PackagingError
        from serverless.packaging import package_lambda

        lambda_root = tmp_path / 'bad-lambda'
        (lambda_root / 'core').mkdir(parents=True)
        (lambda_root / 'core' / 'handler.py').write_text(
            'import os\n', encoding='utf-8'
        )

        with pytest.raises(PackagingError):
            package_lambda(lambda_root, runtime='python3.13')

    def test_raises_when_no_core(self, tmp_path):
        from serverless.packaging import PackagingError
        from serverless.packaging import package_lambda

        lambda_root = tmp_path / 'no-core'
        lambda_root.mkdir()

        with pytest.raises(PackagingError):
            package_lambda(lambda_root, runtime='python3.13')


class TestCleanBuild:
    """clean_build elimina el directorio de build efimero."""

    def test_returns_true_when_build_existed(self, tmp_path):
        from serverless.packaging import clean_build
        from serverless.packaging import package_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.core.ulid import new_uuidv7\n',
            deps=[],
        )
        package_lambda(lambda_root, runtime='python3.13')

        removed = clean_build(lambda_root)

        assert removed is True

    def test_returns_false_when_no_build(self, tmp_path):
        from serverless.packaging import clean_build

        lambda_root = tmp_path / 'lambda-y'
        lambda_root.mkdir()

        removed = clean_build(lambda_root)

        assert removed is False


class TestPackagedLambdaContextManager:
    """packaged_lambda construye al entrar, limpia al salir."""

    def test_build_present_inside_block(self, tmp_path):
        from serverless.packaging import packaged_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.core.ulid import new_uuidv7\n',
            deps=[],
        )

        with packaged_lambda(lambda_root, runtime='python3.13') as result:
            build, _, _ = result
            assert build.is_dir()

    def test_build_removed_after_block(self, tmp_path):
        from serverless.packaging import build_dir
        from serverless.packaging import packaged_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.core.ulid import new_uuidv7\n',
            deps=[],
        )

        with packaged_lambda(lambda_root, runtime='python3.13'):
            pass

        assert not build_dir(lambda_root).exists()

    def test_build_removed_even_on_exception(self, tmp_path):
        from serverless.packaging import build_dir
        from serverless.packaging import packaged_lambda

        lambda_root = _make_lambda(
            tmp_path,
            imports='from shared.core.ulid import new_uuidv7\n',
            deps=[],
        )

        with pytest.raises(ValueError, match='boom'):
            with packaged_lambda(lambda_root, runtime='python3.13'):
                raise ValueError('boom')

        assert not build_dir(lambda_root).exists()


class TestZipBuildDir:
    """zip_build_dir comprime build/ en build.zip para el deploy AWS."""

    def test_zip_build_dir_creates_build_zip(self, tmp_path):
        from serverless.packaging import build_zip_path
        from serverless.packaging import zip_build_dir

        build = tmp_path / 'build'
        build.mkdir()
        (build / 'handler.py').write_text('x = 1', encoding='utf-8')

        result = zip_build_dir(tmp_path)

        assert result == build_zip_path(tmp_path)
        assert result.is_file()
        assert result.name == 'build.zip'

    def test_zip_build_dir_when_no_build_raises(self, tmp_path):
        from serverless.packaging import PackagingError
        from serverless.packaging import zip_build_dir

        with pytest.raises(PackagingError, match='build/'):
            zip_build_dir(tmp_path)

    def test_zip_build_dir_overwrites_existing_zip(self, tmp_path):
        from serverless.packaging import build_zip_path
        from serverless.packaging import zip_build_dir

        build = tmp_path / 'build'
        build.mkdir()
        (build / 'handler.py').write_text('v1', encoding='utf-8')
        stale = build_zip_path(tmp_path)
        stale.write_text('stale', encoding='utf-8')

        result = zip_build_dir(tmp_path)

        assert result.is_file()
        # El zip nuevo reemplaza al stale: ya no es el texto plano.
        assert result.read_bytes()[:2] == b'PK'
