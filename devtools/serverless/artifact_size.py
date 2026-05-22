"""Control de peso del artefacto de deploy de un lambda.

AWS Lambda impone limites HARD (no ajustables) al paquete de deploy:

  - 50 MB  : tamano del `.zip` para subida DIRECTA (sin S3).
  - 250 MB : tamano del paquete DESCOMPRIMIDO (codigo + deps + layers).

(Fuente: docs.aws.amazon.com/lambda gettingstarted-limits, 2026-05.)

Este modulo mide el artefacto que arma `packaging.py` y:

  - emite un `[WARN]` al acercarse al limite (80%): zip > 40 MB o
    descomprimido > 200 MB;
  - lanza `ArtifactTooLargeError` si supera un hard limit — el
    `deploy`/`build` aborta antes de subir a AWS.

El backend del portfolio sube el `.zip` por subida directa
(`aws lambda update-function-code --zip-file`), asi que el limite de
50 MB comprimido SI aplica. Si un lambda lo supera, las salidas son
Amazon S3 o una imagen de contenedor OCI (hasta 10 GB) — fuera del
scope de este modulo, pero el mensaje de error las menciona.
"""

from __future__ import annotations

from pathlib import Path


# Hard limits de AWS Lambda (MB). NO son ajustables por soporte.
AWS_ZIP_LIMIT_MB = 50
AWS_UNZIPPED_LIMIT_MB = 250

# El warning salta al 80% del limite.
_WARN_RATIO = 0.80

_MB = 1024 * 1024


class ArtifactTooLargeError(RuntimeError):
    """El artefacto supera un hard limit de AWS Lambda (build abortado)."""


def _dir_size_bytes(path: Path) -> int:
    """Devuelve el tamano total en bytes del arbol de `path`."""
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def measure_artifact(
    build_dir: Path,
    zip_path: Path | None = None,
) -> tuple[float, float]:
    """Mide el artefacto: descomprimido (`build/`) y comprimido (`.zip`).

    Parameters
    ----------
    build_dir : Path
        Directorio `build/` que armo `package_lambda` (codigo + deps).
    zip_path : Path | None
        Ruta del `build.zip` si ya se comprimio; None si todavia no.

    Returns
    -------
    tuple[float, float]
        `(unzipped_mb, zip_mb)` — tamanos en MB. `zip_mb` es 0.0 si
        `zip_path` es None o no existe aun.
    """
    unzipped_mb = _dir_size_bytes(build_dir) / _MB
    zip_mb = 0.0
    if zip_path is not None and zip_path.is_file():
        zip_mb = zip_path.stat().st_size / _MB
    return unzipped_mb, zip_mb


def format_size_report(unzipped_mb: float, zip_mb: float) -> str:
    """Formatea las dos cifras del artefacto contra los limites de AWS."""
    parts = [
        f'descomprimido {unzipped_mb:.1f} MB / {AWS_UNZIPPED_LIMIT_MB} MB',
    ]
    if zip_mb > 0:
        parts.append(f'zip {zip_mb:.1f} MB / {AWS_ZIP_LIMIT_MB} MB')
    return 'Artefacto: ' + ', '.join(parts)


def size_warning(unzipped_mb: float, zip_mb: float) -> str | None:
    """Devuelve un mensaje de WARN si el artefacto se acerca al limite.

    Salta al 80% de cualquiera de los dos limites de AWS. Devuelve None
    si el artefacto esta holgado.

    Parameters
    ----------
    unzipped_mb : float
        Tamano del paquete descomprimido en MB.
    zip_mb : float
        Tamano del `.zip` en MB (0.0 si todavia no se comprimio).

    Returns
    -------
    str | None
        Mensaje de warning con ambas cifras, o None.
    """
    warns: list[str] = []
    if unzipped_mb > AWS_UNZIPPED_LIMIT_MB * _WARN_RATIO:
        warns.append(
            f'descomprimido {unzipped_mb:.1f} MB supera el 80% del '
            f'limite de {AWS_UNZIPPED_LIMIT_MB} MB',
        )
    if zip_mb > AWS_ZIP_LIMIT_MB * _WARN_RATIO:
        warns.append(
            f'zip {zip_mb:.1f} MB supera el 80% del limite de '
            f'{AWS_ZIP_LIMIT_MB} MB',
        )
    if not warns:
        return None
    return (
        '[WARN] artefacto cerca del limite de AWS Lambda: '
        + '; '.join(warns)
        + f'. {format_size_report(unzipped_mb, zip_mb)}'
    )


def check_artifact_size(unzipped_mb: float, zip_mb: float) -> None:
    """Aborta el build si el artefacto supera un hard limit de AWS.

    Parameters
    ----------
    unzipped_mb : float
        Tamano del paquete descomprimido en MB.
    zip_mb : float
        Tamano del `.zip` en MB (0.0 si todavia no se comprimio).

    Raises
    ------
    ArtifactTooLargeError
        Si el descomprimido supera 250 MB o el `.zip` supera 50 MB.
    """
    errors: list[str] = []
    if unzipped_mb > AWS_UNZIPPED_LIMIT_MB:
        errors.append(
            f'el paquete descomprimido ({unzipped_mb:.1f} MB) supera el '
            f'hard limit de AWS Lambda ({AWS_UNZIPPED_LIMIT_MB} MB)',
        )
    if zip_mb > AWS_ZIP_LIMIT_MB:
        errors.append(
            f'el .zip ({zip_mb:.1f} MB) supera el hard limit de subida '
            f'directa de AWS Lambda ({AWS_ZIP_LIMIT_MB} MB)',
        )
    if not errors:
        return
    raise ArtifactTooLargeError(
        'Build abortado — '
        + '; '.join(errors)
        + '. Salidas: subir el .zip via Amazon S3, o migrar a una '
        + 'imagen de contenedor OCI (hasta 10 GB). '
        + format_size_report(unzipped_mb, zip_mb),
    )
