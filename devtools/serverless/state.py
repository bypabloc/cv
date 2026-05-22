"""Estado local del backend serverless (reemplaza el estado de CloudFormation).

Sin SAM/CloudFormation, devtools necesita recordar que recursos AWS creo
para poder decidir create / update / no-op en el siguiente `deploy`, y
para poder destruirlos. Ese estado vive en un JSON por `(scope, stage)`
en `serverless/lambda/.state/` (gitignored, regenerable).

Un `scope` es `'infra'` (la infra compartida) o el nombre de un Lambda
(`'contact-form'`, `'tracking-pixel'`, ...).

El diff compara dos hashes:

  - `config_hash`: SHA256 de la config renderizada (IAM, env, memory...).
  - `code_hash`: SHA256 del contenido de `core/` del Lambda.

Si ambos coinciden con lo guardado, el deploy es no-op. Si solo cambia
el codigo, `update-function-code`. Si cambia la config, se re-aplica.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import Enum
from enum import auto
import hashlib
import json
from pathlib import Path
from typing import Any


# Raiz del backend serverless del portfolio.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Directorio del estado local (gitignored, efimero por entorno).
STATE_DIR = _SERVERLESS_DIR / 'lambda' / '.state'


class Action(Enum):
    """Accion que decide el diff de estado para un `deploy`.

    Members
    -------
    CREATE
        No hay estado previo: crear todos los recursos.
    NOOP
        config_hash y code_hash sin cambios: nada que hacer.
    UPDATE_CODE
        Solo cambio el codigo: `update-function-code`.
    UPDATE_CONFIG
        Solo cambio la config: `update-function-configuration` + IAM.
    UPDATE_BOTH
        Cambiaron codigo y config.
    """

    CREATE = auto()
    NOOP = auto()
    UPDATE_CODE = auto()
    UPDATE_CONFIG = auto()
    UPDATE_BOTH = auto()


@dataclass(frozen=True)
class LambdaState:
    """Estado de un scope (un Lambda o la infra) en un stage.

    Attributes
    ----------
    scope : str
        `'infra'` o el nombre del Lambda.
    stage : str
        `dev` | `stage` | `prod`.
    config_hash : str
        SHA256 de la config renderizada aplicada.
    code_hash : str
        SHA256 del contenido de `core/` (vacio para `infra`).
    resources : dict[str, str | None]
        Identificadores de lo creado (ARNs, nombres, UUIDs).
    updated_at : str
        Timestamp ISO-8601 UTC de la ultima escritura.
    """

    scope: str
    stage: str
    config_hash: str
    code_hash: str
    resources: dict[str, str | None]
    updated_at: str


def state_path(scope: str, stage: str) -> Path:
    """Devuelve la ruta del archivo de estado de `(scope, stage)`.

    Parameters
    ----------
    scope : str
        `'infra'` o el nombre del Lambda.
    stage : str
        Entorno (`dev` | `stage` | `prod`).

    Returns
    -------
    Path
        `serverless/lambda/.state/<scope>-<stage>.json`.
    """
    return STATE_DIR / f'{scope}-{stage}.json'


def load_state(scope: str, stage: str) -> LambdaState | None:
    """Lee el estado de `(scope, stage)`.

    Parameters
    ----------
    scope : str
        `'infra'` o el nombre del Lambda.
    stage : str
        Entorno.

    Returns
    -------
    LambdaState | None
        El estado guardado, o None si nunca se deployo (sin archivo).
    """
    path = state_path(scope, stage)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding='utf-8'))
    return LambdaState(
        scope=raw['scope'],
        stage=raw['stage'],
        config_hash=raw['config_hash'],
        code_hash=raw['code_hash'],
        resources=raw['resources'],
        updated_at=raw['updated_at'],
    )


def save_state(state: LambdaState) -> Path:
    """Escribe el estado a disco (crea `.state/` si no existe).

    Parameters
    ----------
    state : LambdaState
        Estado a persistir.

    Returns
    -------
    Path
        Ruta del archivo escrito.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path(state.scope, state.stage)
    path.write_text(
        json.dumps(asdict(state), indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return path


def clear_state(stage: str) -> list[Path]:
    """Borra todos los `.state/*-<stage>.json`.

    Parameters
    ----------
    stage : str
        Entorno cuyo estado se limpia.

    Returns
    -------
    list[Path]
        Rutas de los archivos borrados (ordenadas).
    """
    if not STATE_DIR.is_dir():
        return []
    removed: list[Path] = []
    for path in sorted(STATE_DIR.glob(f'*-{stage}.json')):
        path.unlink()
        removed.append(path)
    return removed


def config_hash(rendered_config: dict[str, Any]) -> str:
    """SHA256 estable de la config renderizada.

    Usa `json.dumps` con `sort_keys=True` para que el hash no dependa del
    orden de las claves.

    Parameters
    ----------
    rendered_config : dict[str, Any]
        Config renderizada (IAM, env, memory, timeout, runtime...).

    Returns
    -------
    str
        Hash con prefijo `sha256:`.
    """
    payload = json.dumps(
        rendered_config,
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return f'sha256:{digest}'


def code_hash(code_dir: Path) -> str:
    """SHA256 determinista del contenido de un directorio de codigo.

    Recorre todos los archivos de `code_dir` en orden alfabetico y mezcla
    la ruta relativa + el contenido de cada uno. El hash es identico para
    dos directorios con el mismo contenido, sin importar el orden en que
    el filesystem liste los archivos.

    Parameters
    ----------
    code_dir : Path
        Directorio de codigo (tipicamente `core/` del Lambda).

    Returns
    -------
    str
        Hash con prefijo `sha256:`. `sha256:empty` si el dir no existe.
    """
    if not code_dir.is_dir():
        return 'sha256:empty'
    hasher = hashlib.sha256()
    files = sorted(p for p in code_dir.rglob('*') if p.is_file())
    for path in files:
        rel = path.relative_to(code_dir).as_posix()
        hasher.update(rel.encode('utf-8'))
        hasher.update(b'\0')
        hasher.update(path.read_bytes())
        hasher.update(b'\0')
    return f'sha256:{hasher.hexdigest()}'


def diff(
    previous: LambdaState | None,
    new_config_hash: str,
    new_code_hash: str,
) -> Action:
    """Decide la accion comparando los hashes previos vs los nuevos.

    Parameters
    ----------
    previous : LambdaState | None
        Estado previo, o None si nunca se deployo.
    new_config_hash : str
        Hash de la config renderizada actual.
    new_code_hash : str
        Hash del codigo actual.

    Returns
    -------
    Action
        CREATE si no hay estado previo; NOOP / UPDATE_* segun que cambio.
    """
    if previous is None:
        return Action.CREATE

    config_changed = previous.config_hash != new_config_hash
    code_changed = previous.code_hash != new_code_hash

    if config_changed and code_changed:
        return Action.UPDATE_BOTH
    if code_changed:
        return Action.UPDATE_CODE
    if config_changed:
        return Action.UPDATE_CONFIG
    return Action.NOOP


def now_iso() -> str:
    """Devuelve el timestamp actual en ISO-8601 UTC (segundos).

    Returns
    -------
    str
        Ej. `'2026-05-21T10:00:00Z'`.
    """
    return datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
