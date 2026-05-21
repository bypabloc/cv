"""Unit tests for serverless.shared_resolver - cierre de subpaquetes shared/.

Path mirroring: devtools/serverless/shared_resolver.py -> this file.

Verifica que el resolver escanea el AST del codigo de un lambda, detecta
los `from shared.<subpaquete>` que usa, y resuelve el cierre transitivo
de subpaquetes + la union de deps externas, leyendo los `pyproject.toml`
de cada subpaquete de `shared/`.
"""

import textwrap

import pytest


pytestmark = pytest.mark.unit


def _make_subpackage(
    shared_dir,
    name: str,
    *,
    external: list[str],
    internal: list[str],
) -> None:
    """Crea un subpaquete de shared/ con __init__.py + pyproject.toml."""
    sub = shared_dir / name
    sub.mkdir(parents=True)
    (sub / '__init__.py').write_text('', encoding='utf-8')
    ext_lines = ''.join(f'  "{d}",\n' for d in external)
    int_list = ', '.join(f'"{d}"' for d in internal)
    (sub / 'pyproject.toml').write_text(
        textwrap.dedent(f"""\
            [project]
            name = "shared-{name}"
            version = "0"
            dependencies = [
            {ext_lines}]

            [tool.shared]
            internal-deps = [{int_list}]
        """),
        encoding='utf-8',
    )


def _make_shared_tree(tmp_path):
    """Crea un shared/ de prueba con 4 subpaquetes y un DAG conocido.

    Grafo: http -> core, aws ; db -> aws ; core, aws son hojas.
    """
    shared_dir = tmp_path / 'shared'
    shared_dir.mkdir()
    (shared_dir / '__init__.py').write_text('', encoding='utf-8')
    _make_subpackage(shared_dir, 'core', external=['pydantic'], internal=[])
    _make_subpackage(shared_dir, 'aws', external=['boto3'], internal=[])
    _make_subpackage(
        shared_dir, 'http', external=['httpx'], internal=['core', 'aws']
    )
    _make_subpackage(
        shared_dir, 'db', external=['sqlalchemy'], internal=['aws']
    )
    return shared_dir


def _make_lambda_core(tmp_path, imports: str):
    """Crea un <lambda>/core/ con un handler.py que importa lo dado."""
    core = tmp_path / 'my-lambda' / 'core'
    core.mkdir(parents=True)
    (core / 'handler.py').write_text(imports, encoding='utf-8')
    return tmp_path / 'my-lambda'


class TestScanImports:
    """scan_imports detecta subpaquetes de shared/ importados."""

    def test_detects_from_import(self, tmp_path):
        from serverless.shared_resolver import scan_imports

        lambda_root = _make_lambda_core(
            tmp_path, 'from shared.http.cors import resolve_origin\n'
        )

        found = scan_imports(lambda_root / 'core')

        assert found == {'http'}

    def test_detects_plain_import(self, tmp_path):
        from serverless.shared_resolver import scan_imports

        lambda_root = _make_lambda_core(tmp_path, 'import shared.aws.ssm\n')

        found = scan_imports(lambda_root / 'core')

        assert found == {'aws'}

    def test_detects_multiple_subpackages(self, tmp_path):
        from serverless.shared_resolver import scan_imports

        lambda_root = _make_lambda_core(
            tmp_path,
            'from shared.core.exceptions import ValidationError\n'
            'from shared.observability.logger import logger\n',
        )

        found = scan_imports(lambda_root / 'core')

        assert found == {'core', 'observability'}

    def test_ignores_non_shared_imports(self, tmp_path):
        from serverless.shared_resolver import scan_imports

        lambda_root = _make_lambda_core(
            tmp_path, 'import os\nfrom typing import Any\n'
        )

        found = scan_imports(lambda_root / 'core')

        assert found == set()

    def test_raises_on_syntax_error(self, tmp_path):
        from serverless.shared_resolver import SharedResolverError
        from serverless.shared_resolver import scan_imports

        lambda_root = _make_lambda_core(tmp_path, 'def broken(\n')

        with pytest.raises(SharedResolverError):
            scan_imports(lambda_root / 'core')


class TestResolveClosure:
    """resolve_closure expande las internal-deps transitivamente."""

    def test_leaf_subpackage_resolves_to_itself(self, tmp_path):
        from serverless.shared_resolver import resolve_closure

        shared_dir = _make_shared_tree(tmp_path)

        closure = resolve_closure({'core'}, shared_dir=shared_dir)

        assert closure == {'core'}

    def test_transitive_closure_includes_internal_deps(self, tmp_path):
        from serverless.shared_resolver import resolve_closure

        shared_dir = _make_shared_tree(tmp_path)

        closure = resolve_closure({'http'}, shared_dir=shared_dir)

        assert closure == {'http', 'core', 'aws'}

    def test_db_closure_does_not_include_http(self, tmp_path):
        from serverless.shared_resolver import resolve_closure

        shared_dir = _make_shared_tree(tmp_path)

        closure = resolve_closure({'db'}, shared_dir=shared_dir)

        assert closure == {'db', 'aws'}

    def test_raises_on_unknown_subpackage(self, tmp_path):
        from serverless.shared_resolver import SharedResolverError
        from serverless.shared_resolver import resolve_closure

        shared_dir = _make_shared_tree(tmp_path)

        with pytest.raises(SharedResolverError):
            resolve_closure({'nonexistent'}, shared_dir=shared_dir)


class TestExternalDependencies:
    """external_dependencies une las deps PyPI del cierre."""

    def test_single_subpackage_deps(self, tmp_path):
        from serverless.shared_resolver import external_dependencies

        shared_dir = _make_shared_tree(tmp_path)

        deps = external_dependencies({'core'}, shared_dir=shared_dir)

        assert deps == ['pydantic']

    def test_closure_deps_are_union_sorted(self, tmp_path):
        from serverless.shared_resolver import external_dependencies

        shared_dir = _make_shared_tree(tmp_path)

        deps = external_dependencies(
            {'http', 'core', 'aws'}, shared_dir=shared_dir
        )

        assert deps == ['boto3', 'httpx', 'pydantic']

    def test_db_closure_has_no_httpx(self, tmp_path):
        from serverless.shared_resolver import external_dependencies

        shared_dir = _make_shared_tree(tmp_path)

        deps = external_dependencies({'db', 'aws'}, shared_dir=shared_dir)

        assert deps == ['boto3', 'sqlalchemy']


class TestAvailableSubpackages:
    """available_subpackages lista los subpaquetes presentes."""

    def test_lists_subpackages_with_init(self, tmp_path):
        from serverless.shared_resolver import available_subpackages

        shared_dir = _make_shared_tree(tmp_path)

        subpackages = available_subpackages(shared_dir=shared_dir)

        assert subpackages == {'core', 'aws', 'http', 'db'}
