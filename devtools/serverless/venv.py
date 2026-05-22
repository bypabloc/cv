"""Gestion del `.venv` aislado de cada lambda y subpaquete de `shared/`.

Antes del refactor de independencia de lambdas, el backend usaba UN solo
`.venv` (el workspace uv en `serverless/.venv`) con la union de las deps
de los 4 lambdas. Eso hacia que `run --stage=local` y `tests` no fueran
fieles a la realidad de AWS, donde cada lambda corre solo con SUS deps.

Este modulo da a cada lambda su propio `.venv` aislado:

  1. `uv sync` instala las deps del `pyproject.toml` del lambda (runtime
     + grupo dev) en `<lambda>/.venv`.
  2. `uv pip install` suma las deps externas que aportan los subpaquetes
     de `shared/` que el lambda usa (resueltas por `shared_resolver`).

Asi el `.venv` refleja EXACTAMENTE lo que el lambda necesita, sin
contaminacion de los otros 3. El `pyproject.toml` del lambda NO menciona
`shared/` (regla de dedup D-3): devtools resuelve el cierre y completa
el `.venv`.

`uv sync` se corre SIEMPRE antes de usar el `.venv` (idempotente, barato
si el lock no cambio): garantiza que el `.venv` refleja el `pyproject`.

devtools corre en Python 3.14 (`devtools/.venv`); este modulo solo
orquesta `uv` por subprocess.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from serverless.shared_resolver import resolve_lambda_shared


class VenvError(RuntimeError):
    """Error al preparar el `.venv` aislado de un lambda o subpaquete."""


def venv_python(root: Path) -> Path:
    """Devuelve el path del interprete del `.venv` de `root`.

    No garantiza que exista — usar `ensure_lambda_venv` /
    `ensure_shared_venv` para crearlo primero.
    """
    return root / '.venv' / 'bin' / 'python'


def _uv_available() -> bool:
    """True si el binario `uv` esta en el PATH."""
    return shutil.which('uv') is not None


def _run_uv(args: list[str], *, cwd: Path) -> None:
    """Ejecuta `uv <args>` en `cwd`; lanza `VenvError` si falla.

    Raises
    ------
    VenvError
        Si `uv` no esta instalado o el comando termina con error.
    """
    if not _uv_available():
        raise VenvError(
            'uv no esta instalado. '
            'Instalar: curl -LsSf https://astral.sh/uv/install.sh | sh',
        )
    cmd = ['uv', *args]
    # S603: comando armado por devtools (binario fijo `uv` + flags
    # derivados de los pyproject), sin input no confiable de usuario.
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise VenvError(
            f'`uv {" ".join(args)}` fallo en {cwd}:\n{result.stderr}',
        )


def _sync(root: Path) -> None:
    """Corre `uv sync` en `root` (deps del pyproject + grupo dev).

    Crea el `.venv` en `<root>/.venv` si no existe; si existe, lo
    re-sincroniza al `pyproject.toml` / `uv.lock` actuales.
    """
    _run_uv(['sync'], cwd=root)


def _pip_install(root: Path, deps: list[str]) -> None:
    """Instala `deps` extra en el `.venv` de `root` con `uv pip install`.

    Se usa para sumar las deps externas que aportan los subpaquetes de
    `shared/` que el lambda usa, sin declararlas en su `pyproject.toml`
    (regla de dedup D-3).
    """
    if not deps:
        return
    python = venv_python(root)
    _run_uv(
        ['pip', 'install', '--python', str(python), *deps],
        cwd=root,
    )


def ensure_lambda_venv(lambda_root: Path) -> Path:
    """Prepara el `.venv` aislado de un lambda y devuelve su interprete.

    Pasos:
      1. `uv sync` — instala las deps del `pyproject.toml` del lambda
         (runtime + grupo dev) en `<lambda>/.venv`.
      2. resuelve el cierre transitivo de subpaquetes de `shared/` que el
         lambda usa (via `shared_resolver`) y `uv pip install` de las
         deps externas que aportan.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda (con `manifest.yaml`, `pyproject.toml`,
        `core/`).

    Returns
    -------
    Path
        El path del `python` del `.venv` del lambda.

    Raises
    ------
    VenvError
        Si el lambda no tiene `pyproject.toml`, falta `uv`, o `uv` falla.
    """
    if not (lambda_root / 'pyproject.toml').is_file():
        raise VenvError(
            f'El lambda {lambda_root} no tiene pyproject.toml — no se '
            f'puede crear su .venv aislado.',
        )

    _sync(lambda_root)

    # Las deps externas del cierre de shared/ NO estan en el pyproject del
    # lambda (regla D-3): devtools las resuelve y las instala aparte.
    _, shared_deps = resolve_lambda_shared(lambda_root)
    _pip_install(lambda_root, shared_deps)

    return venv_python(lambda_root)


def ensure_shared_venv(subpackage_root: Path) -> Path:
    """Prepara el `.venv` aislado de un subpaquete de `shared/`.

    Un subpaquete de `shared/` (`shared/db`, `shared/lambda_kit`, ...)
    tiene su propio `pyproject.toml` y se testea aislado. `uv sync`
    instala sus deps de runtime + grupo dev.

    Parameters
    ----------
    subpackage_root : Path
        Directorio del subpaquete (con su `pyproject.toml`).

    Returns
    -------
    Path
        El path del `python` del `.venv` del subpaquete.

    Raises
    ------
    VenvError
        Si el subpaquete no tiene `pyproject.toml`, falta `uv`, o `uv`
        falla.
    """
    if not (subpackage_root / 'pyproject.toml').is_file():
        raise VenvError(
            f'El subpaquete {subpackage_root} no tiene pyproject.toml — '
            f'no se puede crear su .venv aislado.',
        )
    _sync(subpackage_root)
    return venv_python(subpackage_root)
