# Fase B — devtools/serverless/state.py: backend S3 opcional

> `state.py` actual lee/escribe el JSON de estado en disco local
> (`serverless/lambda/.state/<scope>-<stage>.json`). Esta fase agrega
> un backend S3 opcional, controlado por env vars. El default sigue
> siendo local (zero impact para el dev).

## Contexto / Problema

`devtools/serverless/state.py` mantiene el estado por `(scope, stage)`:

```jsonc
// serverless/lambda/.state/db-dev.json
{
  "lambda_arn": "arn:aws:lambda:us-east-1:637423614564:function:portfolio-db-dev",
  "code_hash": "abc123...",
  "config_hash": "def456...",
  "log_group_arn": "arn:aws:logs:...",
  "role_arn": "arn:aws:iam:...:role/portfolio-db-dev-role",
  ...
}
```

`provisioner.py` lee el state al inicio del deploy, decide
`create`/`update-function-code`/`update-function-configuration`/`noop`
con el diff de hashes, y al final reescribe el state.

Hoy: local. CI no tiene acceso a ese state -> haria `create` siempre
-> falla porque el Lambda ya existe.

## Solucion

Agregar un backend S3 opcional. Comportamiento:

- **Default (local)**: lee/escribe en disco local. Cero cambio para
  el dev.
- **S3 backend activo** (`DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=portfolio-devtools-state`):
  - `read_state(scope, stage)`: `aws s3 cp` del archivo, parse JSON.
    Si no existe, retorna empty (`{}`).
  - `write_state(scope, stage, data)`: `aws s3 cp` del JSON al
    bucket. S3 versioning preserva la version anterior.
  - Operaciones atomicas: si dos jobs corren en paralelo y escriben
    al mismo archivo, gana el ultimo. El plan E (workflow
    deploy-backend.yml) usa concurrency=queue por env para evitarlo.

### Implementacion

`devtools/serverless/state.py` se refactoriza con un patron strategy:

```python
"""@module devtools.serverless.state — estado local de devtools.

Backend pluggable:
- Default: archivos en `serverless/lambda/.state/<scope>-<stage>.json`.
- S3 (CI/CD): si `DEVTOOLS_STATE_BACKEND=s3`, lee/escribe en el bucket
  configurado por `DEVTOOLS_STATE_BUCKET`. Mismo formato JSON.

El backend se elige UNA vez al cargar el modulo (no por operacion).
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


_STATE_DIR = Path(__file__).resolve().parents[2] / 'serverless' / 'lambda' / '.state'


class StateBackend(ABC):
    """Contrato del backend de estado de devtools."""

    @abstractmethod
    def read(self, scope: str, stage: str) -> dict[str, Any]:
        """Devuelve el state actual; dict vacio si no existe."""

    @abstractmethod
    def write(self, scope: str, stage: str, data: dict[str, Any]) -> None:
        """Persiste el state."""


class LocalStateBackend(StateBackend):
    """Estado en disco local. Default."""

    def _path(self, scope: str, stage: str) -> Path:
        return _STATE_DIR / f'{scope}-{stage}.json'

    def read(self, scope: str, stage: str) -> dict[str, Any]:
        path = self._path(scope, stage)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding='utf-8'))

    def write(self, scope: str, stage: str, data: dict[str, Any]) -> None:
        path = self._path(scope, stage)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')


class S3StateBackend(StateBackend):
    """Estado en S3. Activo solo en CI/CD."""

    def __init__(self, bucket: str) -> None:
        import boto3
        self._bucket = bucket
        self._client = boto3.client('s3')

    def _key(self, scope: str, stage: str) -> str:
        return f'state/{scope}-{stage}.json'

    def read(self, scope: str, stage: str) -> dict[str, Any]:
        try:
            response = self._client.get_object(
                Bucket=self._bucket, Key=self._key(scope, stage),
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except self._client.exceptions.NoSuchKey:
            return {}

    def write(self, scope: str, stage: str, data: dict[str, Any]) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=self._key(scope, stage),
            Body=json.dumps(data, indent=2).encode('utf-8'),
            ContentType='application/json',
            ServerSideEncryption='aws:kms',
        )


def _select_backend() -> StateBackend:
    """Elige el backend en base a env vars."""
    backend_name = os.environ.get('DEVTOOLS_STATE_BACKEND', 'local')
    if backend_name == 's3':
        bucket = os.environ['DEVTOOLS_STATE_BUCKET']
        return S3StateBackend(bucket)
    if backend_name == 'local':
        return LocalStateBackend()
    msg = f'Unknown DEVTOOLS_STATE_BACKEND={backend_name!r}'
    raise ValueError(msg)


_backend = _select_backend()


def read_state(scope: str, stage: str) -> dict[str, Any]:
    """Lee el state actual de un (scope, stage)."""
    return _backend.read(scope, stage)


def write_state(scope: str, stage: str, data: dict[str, Any]) -> None:
    """Persiste el state de un (scope, stage)."""
    _backend.write(scope, stage, data)
```

### Tests

`devtools/tests/unit/src/serverless/state.py` (path mirroring):

- `test_local_backend_writes_and_reads_round_trip`
- `test_local_backend_returns_empty_dict_when_file_missing`
- `test_local_backend_creates_parent_dirs`
- `test_s3_backend_writes_to_bucket_with_kms_encryption` (mock con moto)
- `test_s3_backend_returns_empty_dict_on_no_such_key` (mock con moto)
- `test_s3_backend_reads_existing_object` (mock con moto)
- `test_select_backend_default_is_local`
- `test_select_backend_picks_s3_when_env_var_set`
- `test_select_backend_raises_on_unknown_backend_name`

Cada test: BDD docstring + AAA + asserts exactos.

## Archivos afectados

### Modificar

- `devtools/serverless/state.py` — refactor con backends pluggable.
  - Verificar: `python -m compileall -q devtools/serverless`.
- `devtools/tests/unit/src/serverless/state.py` — agregar los 9 tests.

### Crear

- `serverless/lambda/.state/.gitkeep` — para que el directorio
  exista (los archivos siguen gitignored).

### Documentar

- `.claude/docs/ci-cd-pipeline/state-backend.md` — explica cuando
  usar cada backend, env vars, riesgos de drift entre local y S3.

## Criterios de aceptacion

- **AC-B1**: Given el codigo sin env vars, When `read_state('cv',
  'dev')`, Then usa el backend local (lee de `.state/cv-dev.json`).
- **AC-B2**: Given `DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=test-bucket`, When `read_state('cv', 'dev')`,
  Then hace `s3:GetObject` sobre `test-bucket/state/cv-dev.json`.
- **AC-B3**: Given `DEVTOOLS_STATE_BACKEND=s3` y el objeto NO existe,
  When `read_state`, Then retorna `{}` (no lanza).
- **AC-B4**: Given `write_state` con S3 backend, When se invoca, Then
  el `put_object` incluye `ServerSideEncryption='aws:kms'`.
- **AC-B5**: Given `DEVTOOLS_STATE_BACKEND=foo` (invalido), When se
  carga el modulo, Then lanza `ValueError` con el nombre.

## Verificacion

```bash
python -m compileall -q devtools/serverless

# Tests unit
python devtools/run.py test_runner --module=devtools --type=unit -- -k state

# Smoke local: el dev sigue funcionando sin cambios
python devtools/run.py serverless status --lambda=cv --stage=dev

# Smoke S3 (manual desde laptop):
DEVTOOLS_STATE_BACKEND=s3 DEVTOOLS_STATE_BUCKET=portfolio-devtools-state \
  AWS_PROFILE=tfs-dev \
  python devtools/run.py serverless status --lambda=cv --stage=dev
```

## Commit

```text
feat(devtools/serverless): state.py backend S3 opcional

- state.py: refactor con strategy pattern (LocalStateBackend +
  S3StateBackend). Default sigue siendo local (zero impact dev)
- Activacion: DEVTOOLS_STATE_BACKEND=s3 + DEVTOOLS_STATE_BUCKET=...
- S3 backend usa ServerSideEncryption=aws:kms y S3 versioning para
  audit trail. NoSuchKey -> dict vacio (no lanza)
- 9 tests unit con moto: round-trip local + s3, empty cuando archivo
  faltante, KMS en put_object, seleccion del backend por env var,
  ValueError en backend invalido
- Permite que el CI deploy de los workflows del plan
  e-ci-cd-deploy-pipeline use S3 como state central compartido entre
  CI y laptop del dev"
```
