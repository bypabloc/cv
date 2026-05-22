"""Unit tests for serverless.venv - gestion del .venv aislado por lambda.

Path mirroring: devtools/serverless/venv.py -> this file.

Verifica que ensure_lambda_venv corre `uv sync` en el lambda y luego
`uv pip install` de las deps externas del cierre de shared/, y que
ensure_shared_venv corre `uv sync` en un subpaquete. La invocacion de
`uv` (red) se mockea: los tests verifican la logica de orquestacion, no
la descarga de wheels.
"""

from pathlib import Path
import textwrap

import pytest

from serverless import venv
from serverless.venv import VenvError
from serverless.venv import ensure_lambda_venv
from serverless.venv import venv_python


pytestmark = pytest.mark.unit


def _make_lambda(tmp_path: Path, *, imports: str, deps: list[str]) -> Path:
    """Crea un lambda con core/handler.py + pyproject.toml.

    Los imports referencian subpaquetes reales de serverless/lambda/shared/
    porque ensure_lambda_venv resuelve el cierre contra la fuente maestra.
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


@pytest.fixture
def uv_calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Captura los comandos `uv` invocados, sin ejecutarlos de verdad.

    Devuelve la lista de argv (sin el binario `uv`) de cada invocacion.
    """
    calls: list[list[str]] = []

    class _Result:
        returncode = 0
        stderr = ''

    def _fake_run(cmd, **_kwargs):
        # cmd = ['uv', <args...>]
        calls.append(list(cmd[1:]))
        return _Result()

    monkeypatch.setattr(venv.shutil, 'which', lambda _tool: '/usr/bin/uv')
    monkeypatch.setattr(venv.subprocess, 'run', _fake_run)
    return calls


def test_venv_python_path_points_to_venv_bin() -> None:
    """venv_python compone <root>/.venv/bin/python."""
    # Act
    python = venv_python(Path('/tmp/my-lambda'))

    # Assert
    assert python == Path('/tmp/my-lambda/.venv/bin/python')


def test_ensure_lambda_venv_runs_uv_sync(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_lambda_venv corre `uv sync` en la raiz del lambda."""
    # Arrange: lambda sin imports de shared -> cierre vacio
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])

    # Act
    ensure_lambda_venv(lambda_root)

    # Assert
    assert ['sync'] in uv_calls


def test_ensure_lambda_venv_returns_venv_python(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_lambda_venv devuelve el interprete del .venv del lambda."""
    # Arrange
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])

    # Act
    python = ensure_lambda_venv(lambda_root)

    # Assert
    assert python == lambda_root / '.venv' / 'bin' / 'python'


def test_ensure_lambda_venv_installs_shared_closure_deps(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_lambda_venv hace `uv pip install` de las deps del cierre.

    Un lambda que importa shared.db recibe sqlalchemy/alembic/psycopg en
    su .venv via `uv pip install`, sin declararlas en su pyproject.
    """
    # Arrange: el core/ importa shared.db -> cierre {db, aws}
    lambda_root = _make_lambda(
        tmp_path,
        imports='from shared.db.session import db_session\n',
        deps=['pydantic'],
    )

    # Act
    ensure_lambda_venv(lambda_root)

    # Assert: hay una invocacion `uv pip install` que incluye sqlalchemy
    pip_calls = [c for c in uv_calls if c[:2] == ['pip', 'install']]
    assert len(pip_calls) == 1
    installed = pip_calls[0]
    assert any('sqlalchemy' in dep for dep in installed)


def test_ensure_lambda_venv_skips_pip_install_without_shared(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """Un lambda sin imports de shared/ no dispara `uv pip install`."""
    # Arrange: core/ vacio -> cierre vacio -> sin deps de shared
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])

    # Act
    ensure_lambda_venv(lambda_root)

    # Assert
    pip_calls = [c for c in uv_calls if c[:2] == ['pip', 'install']]
    assert pip_calls == []


def test_ensure_lambda_venv_fails_without_pyproject(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_lambda_venv lanza VenvError si el lambda no tiene pyproject."""
    # Arrange: directorio sin pyproject.toml
    lambda_root = tmp_path / 'no-pyproject'
    (lambda_root / 'core').mkdir(parents=True)

    # Act + Assert
    with pytest.raises(VenvError, match=r'no tiene pyproject\.toml'):
        ensure_lambda_venv(lambda_root)


def test_ensure_lambda_venv_fails_when_uv_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ensure_lambda_venv lanza VenvError si `uv` no esta en el PATH."""
    # Arrange
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])
    monkeypatch.setattr(venv.shutil, 'which', lambda _tool: None)

    # Act + Assert
    with pytest.raises(VenvError, match='uv no esta instalado'):
        ensure_lambda_venv(lambda_root)


def test_ensure_shared_venv_runs_uv_sync(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_shared_venv corre `uv sync` en el subpaquete de shared/."""
    # Arrange
    sub = tmp_path / 'shared-sub'
    sub.mkdir()
    (sub / 'pyproject.toml').write_text(
        '[project]\nname = "shared-sub"\nversion = "0"\n',
        encoding='utf-8',
    )

    # Act
    python = venv.ensure_shared_venv(sub)

    # Assert
    assert ['sync'] in uv_calls
    assert python == sub / '.venv' / 'bin' / 'python'


def test_ensure_shared_venv_fails_without_pyproject(
    tmp_path: Path, uv_calls: list[list[str]]
) -> None:
    """ensure_shared_venv lanza VenvError si falta el pyproject."""
    # Arrange
    sub = tmp_path / 'no-pyproject'
    sub.mkdir()

    # Act + Assert
    with pytest.raises(VenvError, match=r'no tiene pyproject\.toml'):
        venv.ensure_shared_venv(sub)


def test_ensure_lambda_venv_propagates_uv_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si `uv sync` falla, ensure_lambda_venv lanza VenvError con stderr."""
    # Arrange
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])

    class _FailResult:
        returncode = 1
        stderr = 'lock conflict'

    monkeypatch.setattr(venv.shutil, 'which', lambda _tool: '/usr/bin/uv')
    monkeypatch.setattr(venv.subprocess, 'run', lambda *_a, **_k: _FailResult())

    # Act + Assert
    with pytest.raises(VenvError, match='lock conflict'):
        ensure_lambda_venv(lambda_root)
