"""Vendoring de la libreria comun `shared/` dentro de cada lambda.

Los lambdas del backend del portfolio son autonomos en el artefacto
desplegado, pero comparten codigo de `serverless/shared/` (cors, logger,
rate_limit, db ORM, turnstile, cache). En vez de un Lambda Layer o de
duplicar el codigo en el repo, devtools **vendoriza** `serverless/shared/`
dentro del lambda antes de cada accion que necesite el codigo completo:

  - `run-local` / `test-unit` / `test-integration`: copia `shared/` a
    `<lambda>/core/shared/` para que `sam local invoke` y `pytest` lo
    resuelvan.
  - `deploy`: idem, antes de `sam build` (el zip lo incluye).

`core/shared/` es **efimero**: esta en el `.gitignore` de cada lambda, se
regenera en cada accion y se limpia despues. La fuente de verdad unica es
`serverless/shared/`.

Los imports del codigo del lambda son siempre `from shared...`: resuelven
igual en la fuente maestra (`serverless/shared/`, via el `sys.path` del
backend) y en el vendor (`<lambda>/core/shared/`, porque `core/` esta en
el `sys.path` del handler).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import shutil


# Raiz del backend serverless del portfolio (contiene shared/).
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Fuente de verdad de la libreria comun.
_SHARED_SOURCE = _SERVERLESS_DIR / 'shared'

# Nombre del directorio destino dentro de core/ del lambda.
_VENDOR_DIRNAME = 'shared'

# Patrones de archivos/dirs que NO se copian al vendor (basura local).
_IGNORE = shutil.ignore_patterns(
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.pytest_cache',
    '.mypy_cache',
)


class VendoringError(RuntimeError):
    """Error al vendorizar `shared/` dentro de un lambda (exit code 1)."""


def shared_source() -> Path:
    """Devuelve el path de la fuente maestra `serverless/shared/`.

    Raises
    ------
    VendoringError
        Si `serverless/shared/` no existe (estructura del repo rota).
    """
    if not _SHARED_SOURCE.is_dir():
        raise VendoringError(
            f'No existe la libreria comun en {_SHARED_SOURCE}. '
            f'El backend serverless debe tener serverless/shared/.',
        )
    return _SHARED_SOURCE


def vendor_target(lambda_root: Path) -> Path:
    """Devuelve el path destino del vendor: `<lambda_root>/core/shared/`.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda (donde vive `lambda.yaml`).
    """
    return lambda_root / 'core' / _VENDOR_DIRNAME


def vendor_shared(lambda_root: Path) -> Path:
    """Copia `serverless/shared/` dentro de `<lambda_root>/core/shared/`.

    Si el destino ya existe (de una corrida previa interrumpida) se borra
    primero, para que el vendor sea siempre un reflejo limpio de la
    fuente.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda.

    Returns
    -------
    Path
        El path del vendor creado (`<lambda_root>/core/shared/`).

    Raises
    ------
    VendoringError
        Si la fuente no existe o el lambda no tiene `core/`.
    """
    source = shared_source()

    core_dir = lambda_root / 'core'
    if not core_dir.is_dir():
        raise VendoringError(
            f'El lambda {lambda_root} no tiene core/. '
            f'Un lambda-controller debe tener core/ (ver el estandar).',
        )

    target = vendor_target(lambda_root)
    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(source, target, ignore=_IGNORE)
    return target


def clean_shared(lambda_root: Path) -> bool:
    """Elimina el vendor `<lambda_root>/core/shared/` si existe.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda.

    Returns
    -------
    bool
        True si habia un vendor y se elimino, False si no existia.
    """
    target = vendor_target(lambda_root)
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True


@contextmanager
def vendored_shared(lambda_root: Path) -> Iterator[Path]:
    """Context manager: vendoriza `shared/`, limpia al salir.

    Uso tipico en los comandos `run-local` / `test-unit`:

        with vendored_shared(resolved.root):
            run_pytest(...)

    El vendor se limpia incluso si el bloque lanza una excepcion.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda.

    Yields
    ------
    Path
        El path del vendor activo (`<lambda_root>/core/shared/`).
    """
    target = vendor_shared(lambda_root)
    try:
        yield target
    finally:
        clean_shared(lambda_root)
