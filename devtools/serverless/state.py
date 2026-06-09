"""Estado local del backend serverless (reemplaza el estado de CloudFormation).

Sin SAM/CloudFormation, devtools necesita recordar que recursos AWS creo
para poder decidir create / update / no-op en el siguiente `deploy`, y
para poder destruirlos. Ese estado vive en un JSON por `(scope, stage)`.

Un `scope` es `'infra'` (la infra compartida) o el nombre de un Lambda
(`'contact-form'`, `'tracking-pixel'`, ...).

El diff compara dos hashes:

  - `config_hash`: SHA256 de la config renderizada (IAM, env, memory...).
  - `code_hash`: SHA256 del contenido de `core/` del Lambda.

Si ambos coinciden con lo guardado, el deploy es no-op. Si solo cambia
el codigo, `update-function-code`. Si cambia la config, se re-aplica.

Backend pluggable (default: local; opcional: S3):

  - Default: archivos en `serverless/lambda/.state/<scope>-<stage>.json`
    (gitignored, regenerable). Es lo que usa el laptop del dev.
  - S3: si `DEVTOOLS_STATE_BACKEND=s3` y `DEVTOOLS_STATE_BUCKET=<bucket>`,
    lee/escribe el JSON en `s3://<bucket>/state/<scope>-<stage>.json`. Es
    lo que usa CI para compartir el estado entre runs.

Cero cambio API para los callers existentes (`load_state`, `save_state`,
`clear_state`): el backend se selecciona una sola vez al cargar el modulo.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import Enum
from enum import auto
import hashlib
import json
import os
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
        `dev` | `prod`.
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


def _serialize_state(state: LambdaState) -> bytes:
    """Serializa un LambdaState a JSON bytes (UTF-8, indentado)."""
    return (json.dumps(asdict(state), indent=2, sort_keys=True) + '\n').encode(
        'utf-8'
    )


def _deserialize_state(raw_bytes: bytes) -> LambdaState:
    """Deserializa JSON bytes a LambdaState."""
    raw = json.loads(raw_bytes.decode('utf-8'))
    return LambdaState(
        scope=raw['scope'],
        stage=raw['stage'],
        config_hash=raw['config_hash'],
        code_hash=raw['code_hash'],
        resources=raw['resources'],
        updated_at=raw['updated_at'],
    )


# ---------------------------------------------------------------------------
# Backend pluggable: local (default) | s3 (opt-in via env var)
# ---------------------------------------------------------------------------


class StateBackend(ABC):
    """Contrato del backend de estado de devtools."""

    @abstractmethod
    def load(self, scope: str, stage: str) -> LambdaState | None:
        """Devuelve el estado de `(scope, stage)`, o None si no existe."""

    @abstractmethod
    def save(self, state: LambdaState) -> str:
        """Persiste el estado. Devuelve un identificador (path o key)."""

    @abstractmethod
    def clear(self, stage: str) -> list[Path]:
        """Borra todos los estados del stage. Devuelve los identificadores
        borrados (ordenados) como Path. Para el backend S3 el Path es
        un wrapper sintetico — solo `.name` y `.stem` son significativos."""


class LocalStateBackend(StateBackend):
    """Estado en disco local. Default — lo que usa el laptop del dev."""

    def load(self, scope: str, stage: str) -> LambdaState | None:
        path = state_path(scope, stage)
        if not path.is_file():
            return None
        return _deserialize_state(path.read_bytes())

    def save(self, state: LambdaState) -> str:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        path = state_path(state.scope, state.stage)
        path.write_bytes(_serialize_state(state))
        return str(path)

    def clear(self, stage: str) -> list[Path]:
        if not STATE_DIR.is_dir():
            return []
        removed: list[Path] = []
        for path in sorted(STATE_DIR.glob(f'*-{stage}.json')):
            path.unlink()
            removed.append(path)
        return removed


class S3StateBackend(StateBackend):
    """Estado en S3. Opt-in via env vars; usado por CI.

    Layout: `s3://<bucket>/state/<scope>-<stage>.json`. Cada PUT crea una
    nueva version (versioning habilitado en el bucket). Encryption KMS
    automatica por el bucket policy — no hace falta especificar
    `ServerSideEncryption` en la request.
    """

    def __init__(self, bucket: str, *, client: Any = None) -> None:
        # Import lazy: boto3 no es dep de devtools en tiempo de carga
        # general. Solo se importa cuando el backend S3 esta activo y
        # no se inyecto un cliente fake (tests).
        self._bucket = bucket
        if client is not None:
            self._client = client
        else:
            import boto3

            self._client = boto3.client('s3')

    def _key(self, scope: str, stage: str) -> str:
        return f'state/{scope}-{stage}.json'

    def load(self, scope: str, stage: str) -> LambdaState | None:
        try:
            response = self._client.get_object(
                Bucket=self._bucket,
                Key=self._key(scope, stage),
            )
        except self._client.exceptions.NoSuchKey:
            return None
        return _deserialize_state(response['Body'].read())

    def save(self, state: LambdaState) -> str:
        key = self._key(state.scope, state.stage)
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=_serialize_state(state),
            ContentType='application/json',
        )
        return f's3://{self._bucket}/{key}'

    def clear(self, stage: str) -> list[Path]:
        # Listar los objetos del stage y borrarlos uno por uno. S3 NO
        # tiene un "delete by prefix" atomico, pero para limpiar un stage
        # es ok (pocos objetos). Devolvemos Path sinteticos
        # (Path('state/<scope>-<stage>.json')) para que el caller use
        # `.name` y `.stem` uniformemente con el backend local.
        paginator = self._client.get_paginator('list_objects_v2')
        suffix = f'-{stage}.json'
        removed: list[Path] = []
        for page in paginator.paginate(
            Bucket=self._bucket,
            Prefix='state/',
        ):
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key.endswith(suffix):
                    self._client.delete_object(
                        Bucket=self._bucket,
                        Key=key,
                    )
                    removed.append(Path(key))
        return sorted(removed)


def _select_backend() -> StateBackend:
    """Elige el backend en base a env vars (una sola vez al cargar)."""
    backend_name = os.environ.get('DEVTOOLS_STATE_BACKEND', 'local')
    if backend_name == 'local':
        return LocalStateBackend()
    if backend_name == 's3':
        bucket = os.environ.get('DEVTOOLS_STATE_BUCKET')
        if not bucket:
            msg = (
                'DEVTOOLS_STATE_BACKEND=s3 requiere '
                'DEVTOOLS_STATE_BUCKET=<bucket-name>.'
            )
            raise ValueError(msg)
        return S3StateBackend(bucket)
    msg = (
        f'DEVTOOLS_STATE_BACKEND={backend_name!r} invalido. '
        f"Valores aceptados: 'local', 's3'."
    )
    raise ValueError(msg)


_backend: StateBackend = _select_backend()


# ---------------------------------------------------------------------------
# API publica (cero cambio para los callers existentes).
# ---------------------------------------------------------------------------


def load_state(scope: str, stage: str) -> LambdaState | None:
    """Lee el estado de `(scope, stage)`.

    Usa el backend seleccionado por `DEVTOOLS_STATE_BACKEND` (default:
    local).

    Parameters
    ----------
    scope : str
        `'infra'` o el nombre del Lambda.
    stage : str
        Entorno.

    Returns
    -------
    LambdaState | None
        El estado guardado, o None si nunca se deployo.
    """
    return _backend.load(scope, stage)


def save_state(state: LambdaState) -> str:
    """Persiste el estado.

    Usa el backend seleccionado por `DEVTOOLS_STATE_BACKEND`. Devuelve
    el identificador donde se guardo (path local o URI S3).

    Parameters
    ----------
    state : LambdaState
        Estado a persistir.

    Returns
    -------
    str
        Path local (ej. `serverless/lambda/.state/cv-dev.json`) o URI S3
        (ej. `s3://portfolio-devtools-state/state/cv-dev.json`).
    """
    return _backend.save(state)


def clear_state(stage: str) -> list[Path]:
    """Borra todos los estados de un stage.

    Usa el backend seleccionado por `DEVTOOLS_STATE_BACKEND`. Devuelve
    los identificadores borrados (ordenados). Para el backend S3 los
    Path son sinteticos: solo `.name` y `.stem` son significativos.

    Parameters
    ----------
    stage : str
        Entorno cuyo estado se limpia.

    Returns
    -------
    list[Path]
        Identificadores de los estados borrados.
    """
    return _backend.clear(stage)


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


# Marca de un estado parcial: un `deploy` que fallo a mitad de camino
# guarda el estado con este `config_hash` para registrar los recursos ya
# creados sin marcar el deploy como completo. El siguiente `diff` lo
# trata como CREATE para re-ejecutar la secuencia (idempotente).
PARTIAL_MARKER = 'sha256:partial'


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
        CREATE si no hay estado previo o si el estado previo es parcial
        (deploy incompleto); NOOP / UPDATE_* segun que cambio.
    """
    if previous is None or previous.config_hash == PARTIAL_MARKER:
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
