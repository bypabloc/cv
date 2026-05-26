"""Detecta los lambdas afectados por un diff de git.

Dado `base_sha` y `head_sha`, devuelve la lista de lambdas cuyo deploy
hay que disparar. Reglas:

1. `serverless/lambda/services/<X>/**` cambia -> redeploy `<X>` (excepto
   subpaths excluidos: `tests/`, `events/`, `build/`,
   `core/seeds/data/`).
2. `serverless/lambda/shared/<Y>/**` cambia -> redeploy TODOS los
   lambdas cuyo cierre transitivo incluye `shared.<Y>` (resuelto via
   `shared_resolver`). Excluye `shared/<Y>/tests/`.
3. `devtools/serverless/{provisioner,packaging,vendoring,
   shared_resolver,state}.py` cambia -> redeploy TODOS los lambdas:
   son el motor del deploy, un cambio en como se renderizan/empaquetan
   se debe materializar en AWS. Sin este caso, fixes al provisioner
   (ej. limpieza de permission legacy) quedan dormidos hasta que algun
   otro cambio dispare un redeploy.

El comando CLI `serverless detect-changes --base=<sha> --head=<sha>`
imprime JSON `{"affected": ["cv", ...]}` para que GitHub Actions lo
consuma como matrix.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import subprocess


# Paths dentro de services/<X>/ que NO disparan redeploy.
_EXCLUDED_SERVICE_SUBPATHS: tuple[str, ...] = (
    'tests/',
    'events/',
    'build/',
    'core/seeds/data/',
)

# Paths dentro de shared/<Y>/ que NO disparan redeploy.
_EXCLUDED_SHARED_SUBPATHS: tuple[str, ...] = ('tests/',)

# Archivos en devtools/serverless/ que tocan el motor del deploy: un
# cambio aqui se debe materializar en TODOS los lambdas (redeploy
# completo). Lista cerrada — agregar archivos solo si su comportamiento
# afecta el shape del artefacto, del wiring o del state.
_DEVTOOLS_DEPLOY_ENGINE_FILES: frozenset[str] = frozenset(
    {
        'devtools/serverless/provisioner.py',
        'devtools/serverless/packaging.py',
        'devtools/serverless/vendoring.py',
        'devtools/serverless/shared_resolver.py',
        'devtools/serverless/state.py',
    }
)


@dataclass(frozen=True)
class ChangeKind:
    """Resultado de clasificar un path modificado.

    Attributes
    ----------
    kind : str
        'service' | 'shared' | 'ignore'.
    name : str | None
        Para `service`: nombre del lambda. Para `shared`: nombre del
        subpaquete. Para `ignore`: None.
    """

    kind: str
    name: str | None = None


def classify_path(path: str) -> ChangeKind:
    """Clasifica un path del repo como 'service', 'shared' o 'ignore'.

    Parameters
    ----------
    path : str
        Path relativo desde la raiz del repo.

    Returns
    -------
    ChangeKind
        Resultado clasificado.
    """
    parts = path.split('/')
    if len(parts) < 4 or parts[0] != 'serverless' or parts[1] != 'lambda':
        return ChangeKind(kind='ignore')

    # parts[3] vacio significa que el path termina en 'serverless/lambda/<X>/'
    # (un slash final). Lo tratamos como ignore.
    if not parts[3]:
        return ChangeKind(kind='ignore')

    if parts[2] == 'services':
        service_name = parts[3]
        rest = '/'.join(parts[4:])
        if any(
            rest.startswith(excluded) for excluded in _EXCLUDED_SERVICE_SUBPATHS
        ):
            return ChangeKind(kind='ignore')
        return ChangeKind(kind='service', name=service_name)

    if parts[2] == 'shared':
        subpackage = parts[3]
        # shared/tests/ es la suite centralizada de los subpaquetes, no
        # un subpaquete shared real — no dispara redeploy.
        if subpackage == 'tests':
            return ChangeKind(kind='ignore')
        rest = '/'.join(parts[4:])
        if any(
            rest.startswith(excluded) for excluded in _EXCLUDED_SHARED_SUBPATHS
        ):
            return ChangeKind(kind='ignore')
        return ChangeKind(kind='shared', name=subpackage)

    return ChangeKind(kind='ignore')


def _git_diff_files(base_sha: str, head_sha: str) -> list[str]:
    """Devuelve la lista de archivos modificados entre `base_sha` y `head_sha`.

    Raises
    ------
    subprocess.CalledProcessError
        Si `git diff` falla (sha invalido, repo corrupto, etc.).
    """
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'{base_sha}..{head_sha}'],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _consumers_of_shared(
    subpackages: set[str], lambdas_root: Path, lambda_names: list[str]
) -> set[str]:
    """Devuelve los lambdas cuyo cierre transitivo incluye CUALQUIERA de
    los subpaquetes shared en `subpackages`.
    """
    from serverless.shared_resolver import resolve_lambda_shared

    consumers: set[str] = set()
    for name in lambda_names:
        lambda_root = lambdas_root / name
        try:
            closure, _ = resolve_lambda_shared(lambda_root)
        except Exception:
            # Si un lambda falla la resolucion (ej. core/ vacio), lo
            # omitimos en la deteccion: no es candidato a redeploy.
            continue
        if closure & subpackages:
            consumers.add(name)
    return consumers


def detect_affected_lambdas(
    base_sha: str,
    head_sha: str,
    lambdas_root: Path,
    *,
    files: Iterable[str] | None = None,
) -> set[str]:
    """Devuelve el conjunto de lambdas a redeployar entre dos shas.

    Parameters
    ----------
    base_sha : str
        SHA base de la comparacion (ej. el sha previo al push).
    head_sha : str
        SHA al que se quiere deployar.
    lambdas_root : Path
        `serverless/lambda/services/`.
    files : Iterable[str] | None
        Override opcional de la lista de archivos modificados (para
        tests). Si es None, se invoca `git diff` real.

    Returns
    -------
    set[str]
        Nombres de los lambdas afectados.
    """
    from serverless.resolve import available_lambdas

    file_list = (
        list(files)
        if files is not None
        else _git_diff_files(base_sha, head_sha)
    )

    affected: set[str] = set()
    affected_shared: set[str] = set()
    engine_changed = any(
        path in _DEVTOOLS_DEPLOY_ENGINE_FILES for path in file_list
    )

    for path in file_list:
        kind = classify_path(path)
        if kind.kind == 'service' and kind.name is not None:
            affected.add(kind.name)
        elif kind.kind == 'shared' and kind.name is not None:
            affected_shared.add(kind.name)

    # Si cambio el motor del deploy (provisioner, packaging, vendoring,
    # shared_resolver, state) hay que redeployar TODOS los lambdas: un
    # cambio en como se renderizan/empaquetan se debe materializar en
    # AWS y el detector por-archivo no lo capta solo. Tambien se carga
    # la lista de lambdas si hay shared o service afectado (logica vieja).
    lambda_names = (
        available_lambdas()
        if affected_shared or affected or engine_changed
        else []
    )

    if engine_changed:
        affected.update(lambda_names)

    if affected_shared:
        consumers = _consumers_of_shared(
            affected_shared, lambdas_root, lambda_names
        )
        affected.update(consumers)

    # Filtrar lambdas que ya no existen en el repo (ej. un lambda
    # eliminado: el diff lo lista como service pero `services/<name>/`
    # ya no existe). Sin este filtro, el CI matrix intentaria deployar
    # un lambda inexistente y fallaria con "No existe el lambda".
    valid = set(lambda_names)
    return {name for name in affected if name in valid}


# ---------------------------------------------------------------------------
# CLI wrapper.
# ---------------------------------------------------------------------------


def _lambdas_root() -> Path:
    """Resuelve la carpeta `serverless/lambda/services/` desde devtools/."""
    return (
        Path(__file__).resolve().parents[2]
        / 'serverless'
        / 'lambda'
        / 'services'
    )


def cmd_detect_changes(flags: dict) -> int:
    """Comando: `serverless detect-changes --base=<sha> --head=<sha>`.

    Imprime a stdout un JSON `{"affected": [...]}` con los lambdas
    afectados, para que GitHub Actions lo consuma como matrix via
    `fromJSON(...).affected`.

    Exit codes:
    - 0: exito (afectados puede ser lista vacia).
    - 1: error de usuario (falta --base, sha invalido, repo corrupto).
    """
    import json
    import sys

    from shared.console import RED
    from shared.console import _c

    base = flags.get('base')
    head = flags.get('head') or 'HEAD'
    if not base:
        print(_c(RED, 'ERROR: --base=<sha> requerido'), file=sys.stderr)
        return 1

    try:
        affected = detect_affected_lambdas(
            base_sha=str(base),
            head_sha=str(head),
            lambdas_root=_lambdas_root(),
        )
    except subprocess.CalledProcessError as exc:
        print(
            _c(RED, f'ERROR: git diff fallo (exit {exc.returncode})'),
            file=sys.stderr,
        )
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return 1

    print(json.dumps({'affected': sorted(affected)}))
    return 0
