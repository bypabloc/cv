"""Empaquetado del artefacto de deploy de un lambda con uv.

devtools arma el zip que se sube a AWS y luego lo deploya con
`aws lambda`. El flujo (reemplaza al viejo `pip install` de build):

  1. Resuelve, via `shared_resolver`, que subpaquetes de `serverless/lambda/shared/`
     usa el lambda (cierre transitivo por AST) y la union de sus deps
     externas.
  2. Lee las deps de runtime del `pyproject.toml` del propio lambda.
  3. `uv pip install --target build/` instala TODAS esas deps (lambda +
     subpaquetes) en un directorio limpio.
  4. Copia `core/` del lambda a `build/`.
  5. Vendoriza dentro de `build/core/shared/` SOLO los subpaquetes del
     cierre resuelto.

El directorio `build/` resultante es autocontenido: el handler, la
libreria comun y las deps. devtools lo zipea tal cual y lo sube con
`aws lambda create-function` / `update-function-code`.

`build/` es efimero: esta en el `.gitignore` del lambda, se regenera en
cada deploy y se limpia despues.

devtools corre en Python 3.14 (`devtools/.venv`); `tomllib` es stdlib.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import tomllib

from serverless.shared_resolver import resolve_lambda_shared
from serverless.vendoring import shared_source


# Nombre del directorio de build efimero dentro del lambda.
_BUILD_DIRNAME = 'build'

# Nombre del archivo zip del artefacto de deploy.
_BUILD_ZIP_NAME = 'build.zip'

# Patrones que NO se copian al artefacto (basura local). CRITICO:
# excluir `.venv` y `build` — cada subpaquete de `shared/` tiene su
# propio `.venv` aislado (uv sync) que pesa >100MB; vendorizarlo
# infla el artefacto muy por encima del hard limit de 250MB de Lambda.
# El artefacto solo debe llevar el codigo fuente del subpaquete.
_IGNORE = shutil.ignore_patterns(
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.venv',
    'build',
    'build.zip',
    '*.egg-info',
    'dist',
)


class PackagingError(RuntimeError):
    """Error al empaquetar el artefacto de deploy de un lambda."""


def build_dir(lambda_root: Path) -> Path:
    """Devuelve el path del directorio de build: `<lambda_root>/build/`."""
    return lambda_root / _BUILD_DIRNAME


def build_zip_path(lambda_root: Path) -> Path:
    """Devuelve el path del zip de build: `<lambda_root>/build.zip`."""
    return lambda_root / _BUILD_ZIP_NAME


def zip_build_dir(lambda_root: Path) -> Path:
    """Comprime el directorio `build/` en `build.zip`.

    Sin SAM, devtools arma el zip que se sube a AWS:
    `aws lambda create-function --zip-file` y `update-function-code
    --zip-file` necesitan un archivo zip, no un directorio. Este helper
    produce ese `build.zip` desde el `build/` que dejo `package_lambda`.

    El zip es efimero (esta en el `.gitignore` del lambda) y se regenera
    en cada deploy.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda (con `build/` ya construido).

    Returns
    -------
    Path
        Ruta del `build.zip` generado.

    Raises
    ------
    PackagingError
        Si el directorio `build/` no existe (no se corrio el package).
    """
    target = build_dir(lambda_root)
    if not target.is_dir():
        raise PackagingError(
            f'No existe el directorio build/ en {lambda_root}. '
            f'Ejecuta package_lambda antes de zip_build_dir.',
        )
    zip_path = build_zip_path(lambda_root)
    if zip_path.exists():
        zip_path.unlink()
    base = zip_path.with_suffix('')
    archive = shutil.make_archive(
        str(base),
        'zip',
        root_dir=str(target),
    )
    archive_path = Path(archive)

    # Control de peso: con el zip ya armado tenemos ambas cifras. Avisa
    # al 80% del limite y ABORTA el build si supera un hard limit de AWS
    # Lambda (50 MB zip / 250 MB descomprimido).
    from serverless.artifact_size import ArtifactTooLargeError
    from serverless.artifact_size import check_artifact_size
    from serverless.artifact_size import format_size_report
    from serverless.artifact_size import measure_artifact
    from serverless.artifact_size import size_warning

    unzipped_mb, zip_mb = measure_artifact(target, zip_path=archive_path)
    print(format_size_report(unzipped_mb, zip_mb))
    warning = size_warning(unzipped_mb, zip_mb)
    if warning is not None:
        print(warning)
    try:
        check_artifact_size(unzipped_mb, zip_mb)
    except ArtifactTooLargeError as exc:
        raise PackagingError(str(exc)) from exc

    return archive_path


def _lambda_runtime_deps(lambda_root: Path) -> list[str]:
    """Lee `[project.dependencies]` del `pyproject.toml` del lambda.

    Raises
    ------
    PackagingError
        Si el lambda no tiene `pyproject.toml` o esta malformado.
    """
    manifest = lambda_root / 'pyproject.toml'
    if not manifest.is_file():
        raise PackagingError(
            f'El lambda {lambda_root} no tiene pyproject.toml. '
            f'Cada lambda declara sus deps de runtime ahi.',
        )
    try:
        data = tomllib.loads(manifest.read_text(encoding='utf-8'))
    except tomllib.TOMLDecodeError as exc:
        raise PackagingError(
            f'pyproject.toml invalido en {lambda_root}: {exc}',
        ) from exc
    return list(data.get('project', {}).get('dependencies', []))


def _resolve_python_target(runtime: str) -> str:
    """Traduce el runtime del manifiesto a la version `--python` de uv.

    `python3.13` -> `3.13`. uv usa esa version para resolver wheels
    compatibles con el runtime de AWS Lambda.
    """
    return runtime.removeprefix('python')


def _install_dependencies(
    deps: list[str],
    *,
    target: Path,
    python_version: str,
) -> None:
    """Instala `deps` en `target` con `uv pip install --target`.

    Usa `--python-platform` para resolver wheels del runtime de AWS
    Lambda (Amazon Linux arm64, manylinux) y no del host de build.

    `--only-binary=:all:` fuerza wheels precompilados: NUNCA construir
    desde source. Construir un wheel en el host produciria un binario de
    la plataforma del host (x86_64), incompatible con el runtime arm64
    de Lambda. Las deps con extensiones C (psycopg, greenlet, pydantic-
    core) publican wheels aarch64-manylinux — se descargan esos.

    Raises
    ------
    PackagingError
        Si uv falla la instalacion (incl. una dep sin wheel arm64).
    """
    if not deps:
        return
    cmd = [
        'uv',
        'pip',
        'install',
        '--target',
        str(target),
        '--python-version',
        python_version,
        '--python-platform',
        'aarch64-manylinux2014',
        '--only-binary=:all:',
        *deps,
    ]
    # S603: el comando lo construye devtools (binario fijo `uv` + flags
    # derivados del manifiesto), no hay input no confiable de usuario.
    result = subprocess.run(  # noqa: S603
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PackagingError(
            f'uv pip install fallo:\n{result.stderr}',
        )


# Paquetes que el runtime de AWS Lambda Python YA incluye: NO se
# bundlean (botocore solo pesa ~80MB descomprimido por los JSON de cada
# servicio AWS). Excluirlos baja el artefacto bajo el hard limit de
# 250MB sin perder funcionalidad — el `import boto3` en runtime resuelve
# al boto3 del runtime. Solo boto3 + botocore: el resto de la cadena
# (s3transfer, jmespath, urllib3, python-dateutil) la comparten otras
# libs y pesan poco, asi que se mantienen para no romper imports.
_RUNTIME_PROVIDED = ('boto3', 'botocore')


def _prune_runtime_provided(target: Path) -> list[str]:
    """Elimina del `target` los paquetes que el runtime de Lambda provee.

    Borra el paquete (carpeta `<pkg>/`) y sus metadatos
    (`<pkg>-*.dist-info/`, `<pkg>.libs/`). Devuelve la lista de entradas
    borradas (para log/auditoria). Idempotente: ignora lo que no exista.
    """
    removed: list[str] = []
    for pkg in _RUNTIME_PROVIDED:
        pkg_dir = target / pkg
        if pkg_dir.is_dir():
            shutil.rmtree(pkg_dir)
            removed.append(pkg)
        # dist-info + .libs (wheels con binarios): `<pkg>-<ver>.dist-info`,
        # `<pkg>.libs`.
        for extra in (
            *target.glob(f'{pkg}-*.dist-info'),
            *target.glob(f'{pkg}.libs'),
        ):
            if extra.is_dir():
                shutil.rmtree(extra)
                removed.append(extra.name)
    return removed


def _check_dep_dedup(lambda_root: Path) -> None:
    """Aborta el build si el lambda duplica deps del cierre de `shared/`.

    Enforcement de la regla de dedup D-3: ningun `pyproject.toml` de
    lambda declara una dep que ya le llega por el vendoring de `shared/`.

    Raises
    ------
    PackagingError
        Si hay deps duplicadas (con el detalle de cuales y que
        subpaquete de `shared/` las aporta).
    """
    from serverless.dep_validator import DepValidatorError
    from serverless.dep_validator import format_report
    from serverless.dep_validator import validate_lambda_deps

    try:
        result = validate_lambda_deps(lambda_root)
    except DepValidatorError as exc:
        # El lambda no tiene pyproject.toml o esta malformado: es un
        # error de empaquetado (lo traducimos a PackagingError).
        raise PackagingError(str(exc)) from exc
    if not result.is_valid:
        raise PackagingError(
            'Build abortado por deps duplicadas (regla de dedup D-3):\n'
            + format_report(result),
        )


def package_lambda(
    lambda_root: Path,
    *,
    runtime: str,
) -> tuple[Path, set[str], list[str]]:
    """Construye el artefacto de deploy del lambda en `<root>/build/`.

    Pasos: resuelve el cierre de subpaquetes de `shared/`, instala las
    deps (del lambda + de los subpaquetes) con uv, copia `core/` y
    vendoriza los subpaquetes resueltos.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda (con `manifest.yaml`, `pyproject.toml`,
        `core/`).
    runtime : str
        Runtime del manifiesto (`python3.13`) — fija la version de uv.

    Returns
    -------
    tuple[Path, set[str], list[str]]
        `(build_path, closure, all_deps)` — el directorio construido, los
        subpaquetes de `shared/` vendorizados y la lista de deps
        instaladas.

    Raises
    ------
    PackagingError
        Si falta `core/`, `pyproject.toml`, o la instalacion uv falla.
    """
    core_dir = lambda_root / 'core'
    if not core_dir.is_dir():
        raise PackagingError(
            f'El lambda {lambda_root} no tiene core/.',
        )

    # Gate de dedup D-3: el build aborta temprano si el lambda declara
    # una dep que ya aporta el cierre de shared/ (regla del plan
    # serverless-lambda-independence).
    _check_dep_dedup(lambda_root)

    closure, shared_deps = resolve_lambda_shared(lambda_root)
    lambda_deps = _lambda_runtime_deps(lambda_root)
    all_deps = sorted(set(lambda_deps) | set(shared_deps))

    target = build_dir(lambda_root)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    _install_dependencies(
        all_deps,
        target=target,
        python_version=_resolve_python_target(runtime),
    )

    # Poda los paquetes que el runtime de Lambda ya provee (boto3 +
    # botocore): evita ~100MB de artefacto innecesario.
    pruned = _prune_runtime_provided(target)
    if pruned:
        print(f'  poda runtime-provided: {", ".join(pruned)}')

    # Copia el codigo del lambda: core/ -> build/core/.
    shutil.copytree(
        core_dir,
        target / 'core',
        ignore=_IGNORE,
    )

    # Vendoriza los subpaquetes del cierre dentro de build/core/shared/.
    source = shared_source()
    vendor = target / 'core' / 'shared'
    if vendor.exists():
        shutil.rmtree(vendor)
    vendor.mkdir(parents=True)
    shutil.copy2(source / '__init__.py', vendor / '__init__.py')
    for subpackage in sorted(closure):
        shutil.copytree(
            source / subpackage,
            vendor / subpackage,
            ignore=_IGNORE,
        )

    # Control de peso: mide el build/ descomprimido y avisa si se acerca
    # al limite de AWS Lambda. El error duro (build abortado) se evalua
    # en `zip_build_dir`, cuando ya existen ambas cifras (zip + desc).
    from serverless.artifact_size import measure_artifact
    from serverless.artifact_size import size_warning

    unzipped_mb, _ = measure_artifact(target, zip_path=None)
    warning = size_warning(unzipped_mb, zip_mb=0.0)
    if warning is not None:
        print(warning)

    return target, closure, all_deps


def clean_build(lambda_root: Path) -> bool:
    """Elimina el directorio de build efimero si existe.

    Returns
    -------
    bool
        True si habia un build y se elimino, False si no existia.
    """
    target = build_dir(lambda_root)
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True


@contextmanager
def packaged_lambda(
    lambda_root: Path,
    *,
    runtime: str,
) -> Iterator[tuple[Path, set[str], list[str]]]:
    """Context manager: construye el artefacto, limpia al salir.

    Uso tipico en el comando `deploy`:

        with packaged_lambda(root, runtime='python3.13') as (build, _, _):
            sam_deploy(build)

    El `build/` se limpia incluso si el bloque lanza una excepcion.

    Yields
    ------
    tuple[Path, set[str], list[str]]
        `(build_path, closure, all_deps)` — ver `package_lambda`.
    """
    result = package_lambda(lambda_root, runtime=runtime)
    try:
        yield result
    finally:
        clean_build(lambda_root)
