"""Resolucion del lambda objetivo (legacy SAM portfolio vs lambda-controller).

El script `serverless` opera en dos modos:

  - **legacy**: sin `--path` ni `--module`, apunta al backend SAM del
    portfolio (`serverless/` en la raiz del repo). Comportamiento historico.
  - **lambda-controller**: con `--path=<dir>` (o `--module=<dir>`), apunta
    a cualquier lambda que siga el formato `lambda-controller` y traiga un
    `lambda.yaml` (manifiesto simple) del que devtools genera el SAM.

Este modulo localiza el directorio del lambda, lee y valida `lambda.yaml`,
y expone una estructura `ResolvedLambda` para los demas comandos.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


# Path al backend SAM del portfolio (modo legacy).
_PORTFOLIO_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Campos obligatorios del manifiesto lambda.yaml.
_REQUIRED_FIELDS = ('name', 'runtime', 'handler')

# Runtimes Python soportados.
_VALID_RUNTIMES = ('python3.12', 'python3.13')

# Defaults aplicados cuando el manifiesto no los declara.
_MANIFEST_DEFAULTS: dict[str, Any] = {
    'memory': 256,
    'timeout': 30,
    'region': 'us-east-1',
}


class ManifestError(ValueError):
    """Error de validacion del manifiesto lambda.yaml (exit code 1)."""


@dataclass
class ResolvedLambda:
    """Lambda objetivo ya resuelto.

    Attributes
    ----------
    mode : str
        'legacy' (backend SAM del portfolio) o 'lambda-controller'.
    root : Path
        Directorio raiz del lambda (donde corren sam / pytest).
    manifest : dict[str, Any]
        Contenido de lambda.yaml normalizado. Vacio en modo legacy.
    """

    mode: str
    root: Path
    manifest: dict[str, Any] = field(default_factory=dict)

    @property
    def is_lambda_controller(self) -> bool:
        """True si el lambda sigue el formato lambda-controller."""
        return self.mode == 'lambda-controller'


def _read_manifest(manifest_path: Path) -> dict[str, Any]:
    """Lee y valida lambda.yaml, aplica defaults.

    Parameters
    ----------
    manifest_path : Path
        Ruta al archivo lambda.yaml.

    Returns
    -------
    dict[str, Any]
        Manifiesto normalizado (con defaults aplicados).

    Raises
    ------
    ManifestError
        Si el YAML es invalido o falta un campo obligatorio.
    """
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML esta en devtools
        raise ManifestError(
            'PyYAML no esta instalado en el entorno de devtools',
        ) from exc

    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise ManifestError(
            f'lambda.yaml mal formado ({manifest_path}): {exc}',
        ) from exc

    if not isinstance(raw, dict):
        raise ManifestError(
            f'lambda.yaml debe ser un mapa de claves ({manifest_path})',
        )

    missing = [f for f in _REQUIRED_FIELDS if not raw.get(f)]
    if missing:
        raise ManifestError(
            f'lambda.yaml ({manifest_path}) sin campos obligatorios: '
            f'{", ".join(missing)}',
        )

    runtime = raw['runtime']
    if runtime not in _VALID_RUNTIMES:
        raise ManifestError(
            f'runtime invalido {runtime!r} en {manifest_path}. '
            f'Validos: {", ".join(_VALID_RUNTIMES)}',
        )

    manifest = dict(_MANIFEST_DEFAULTS)
    manifest.update(raw)
    return manifest


def resolve_lambda(flags: dict[str, Any]) -> ResolvedLambda:
    """Resuelve el lambda objetivo a partir de los flags.

    Si `--path` o `--module` esta presente, busca `lambda.yaml` en ese
    directorio (modo lambda-controller). Sin esos flags, devuelve el
    backend SAM del portfolio (modo legacy).

    Parameters
    ----------
    flags : dict[str, Any]
        Flags ya parseados; se leen `path` y `module`.

    Returns
    -------
    ResolvedLambda
        Lambda resuelto, con modo, root y manifiesto.

    Raises
    ------
    ManifestError
        Si el path no existe o el manifiesto es invalido.
    """
    target = flags.get('path') or flags.get('module')

    if not target:
        return ResolvedLambda(
            mode='legacy',
            root=_PORTFOLIO_SERVERLESS_DIR,
        )

    root = Path(target).expanduser().resolve()
    if not root.is_dir():
        raise ManifestError(f'El path del lambda no existe: {root}')

    manifest_path = root / 'lambda.yaml'
    if not manifest_path.is_file():
        raise ManifestError(
            f'No se encuentra lambda.yaml en {root}. '
            f'Un lambda-controller debe traer su manifiesto lambda.yaml.',
        )

    manifest = _read_manifest(manifest_path)
    return ResolvedLambda(
        mode='lambda-controller',
        root=root,
        manifest=manifest,
    )
