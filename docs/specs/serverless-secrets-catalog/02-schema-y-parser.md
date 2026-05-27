# Fase 1 — Schema del YAML + parser

> Define el esquema del archivo YAML del catálogo, escribe el parser
> en `devtools/serverless/secrets_catalog.py` y sus tests.

## Schema del YAML

```yaml
# serverless/lambda/resources/secrets/<short-name>.yaml
# Esquema devtools — NO CloudFormation. devtools lo lee y emite las
# llamadas AWS CLI necesarias.
kind: ssm-parameter

# Identidad del parametro (el manifest.yaml de cada Lambda lo referencia
# por este nombre corto).
name: turnstile-secret
description: Cloudflare Turnstile secret key (siteverify)

# Path SSM interpolado por stage. ${stage} se reemplaza en runtime por el
# stage objetivo (dev | stage | prod). Local NO publica a SSM.
path: /portfolio/${stage}/turnstile-secret

# Tipo de parametro SSM. SecureString requiere KMS key.
# Valores: SecureString | String
ssm_type: SecureString

# Si SecureString, alias de la KMS key. Default: alias/portfolio-lambdas
kms_key_alias: alias/portfolio-lambdas

# Mapeo .env -> Lambda:
#   source_env_var: KEY que devtools busca en docker/env/server/.{stage}
#   target_env_var: KEY de env var que el codigo de la Lambda lee con
#                   os.environ. Suele ser SSM_<X>_PATH (el path SSM), pero
#                   en modo --stage=local recibe el VALOR directo.
source_env_var: TURNSTILE_SECRET_KEY
target_env_var: SSM_TURNSTILE_SECRET_PATH

# Stages donde existe el parametro (subset de [dev, stage, prod]).
stages: [dev, stage, prod]

# Si true, el deploy falla cuando source_env_var no esta en el .env del
# stage objetivo. Si false, skip silencioso (solo log nombre, no valor).
required: true

# --- BLOQUE OPCIONAL: rotation (audit) ---
rotation:
  interval_days: 90
  last_rotated: 2026-05-22

# --- BLOQUE OPCIONAL: owners (audit) ---
owners:
  - pacg1991@gmail.com

# --- BLOQUE OPCIONAL: consumed_by (informativo) ---
consumed_by:
  - contact_form

# --- BLOQUE OPCIONAL: tags ---
tags:
  Project: portfolio
  ManagedBy: devtools
```

### Reglas del schema

1. Campos **obligatorios**: `kind`, `name`, `path`, `ssm_type`,
   `source_env_var`, `target_env_var`, `stages`, `required`, `description`.
2. `kind` debe ser exactamente `ssm-parameter`.
3. `ssm_type` debe ser `SecureString` o `String`. Si `SecureString` y
   falta `kms_key_alias`, default a `alias/portfolio-lambdas`.
4. `path` debe contener `${stage}` literal (interpolación obligatoria
   para evitar publicar accidentalmente con el placeholder).
5. `stages` no puede contener `local` (local NO usa SSM).
6. `name` debe coincidir con el filename: `turnstile-secret.yaml` -> `name:
   turnstile-secret`. Patrón idéntico al `loadYamlEntries` del frontend.
7. Bloques opcionales no rompen el parser si faltan, pero si están deben
   matchear el sub-schema correspondiente.

## Parser: `devtools/serverless/secrets_catalog.py`

```python
"""Parser del catalogo de secretos/parametros SSM.

Lee serverless/lambda/resources/secrets/*.yaml y devuelve una coleccion
de SecretSpec inmutables. Reemplaza los diccionarios hardcodeados
_SECRETS (provisioner.py) y _SSM_PARAMETERS (secrets.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Path al directorio del catalogo, relativo al repo.
_CATALOG_DIR = (
    Path(__file__).resolve().parents[2]
    / 'serverless' / 'lambda' / 'resources' / 'secrets'
)

# Stages permitidos en el campo `stages` del YAML (local excluido).
_VALID_STAGES = frozenset({'dev', 'stage', 'prod'})

# Tipos SSM permitidos.
_VALID_SSM_TYPES = frozenset({'SecureString', 'String'})

# Default de KMS key alias para SecureString.
_DEFAULT_KMS_ALIAS = 'alias/portfolio-lambdas'

# Campos obligatorios del YAML.
_REQUIRED_FIELDS = (
    'kind', 'name', 'path', 'ssm_type', 'source_env_var',
    'target_env_var', 'stages', 'required', 'description',
)


class CatalogError(ValueError):
    """Error en el catalogo (YAML invalido o inconsistente)."""


@dataclass(frozen=True)
class SecretSpec:
    """Una entrada del catalogo, ya validada y normalizada."""

    name: str
    description: str
    path_template: str  # con ${stage} literal
    ssm_type: str       # SecureString | String
    kms_key_alias: str | None  # solo si SecureString
    source_env_var: str
    target_env_var: str
    stages: frozenset[str]
    required: bool
    rotation: dict[str, Any] | None
    owners: tuple[str, ...]
    consumed_by: tuple[str, ...]
    tags: dict[str, str]
    source_file: Path   # path del YAML (para mensajes de error)

    def path_for(self, stage: str) -> str:
        """Resuelve el path SSM para un stage dado."""
        if stage not in self.stages:
            raise CatalogError(
                f'secreto {self.name!r} no se publica en stage {stage!r} '
                f'(stages={sorted(self.stages)})',
            )
        return self.path_template.replace('${stage}', stage)


@dataclass(frozen=True)
class Catalog:
    """Catalogo cargado en memoria."""

    by_name: dict[str, SecretSpec]

    @classmethod
    def load(cls, directory: Path | None = None) -> Catalog:
        """Carga todos los YAML del directorio."""
        directory = directory or _CATALOG_DIR
        if not directory.exists():
            raise CatalogError(f'catalogo no existe: {directory}')
        by_name: dict[str, SecretSpec] = {}
        for yaml_path in sorted(directory.glob('*.yaml')):
            spec = _load_one(yaml_path)
            if spec.name in by_name:
                raise CatalogError(
                    f'secreto duplicado {spec.name!r}: '
                    f'{by_name[spec.name].source_file} vs {yaml_path}',
                )
            by_name[spec.name] = spec
        return cls(by_name=by_name)

    def get(self, name: str) -> SecretSpec:
        spec = self.by_name.get(name)
        if spec is None:
            raise CatalogError(
                f'secreto desconocido {name!r}. Conocidos: '
                f'{sorted(self.by_name)}',
            )
        return spec

    def for_stage(self, stage: str) -> tuple[SecretSpec, ...]:
        """Devuelve los secretos publicables en el stage dado."""
        return tuple(s for s in self.by_name.values() if stage in s.stages)


def _load_one(yaml_path: Path) -> SecretSpec:
    """Lee y valida un YAML individual."""
    # ... implementacion: yaml.safe_load, validar required fields,
    # validar enums, validar name == filename stem, validar ${stage}
    # en path, normalizar tags/owners/consumed_by, devolver SecretSpec.
    ...
```

### Tests obligatorios (TDD)

Suite en `devtools/tests/serverless/test_secrets_catalog.py`:

| Test | Cubre AC |
|------|----------|
| `test_load_when_directory_empty_returns_empty_catalog` | AC-1 |
| `test_load_when_yaml_valid_returns_secret_spec_normalized` | AC-1 |
| `test_load_when_field_missing_raises_with_path_and_field` | AC-2 |
| `test_load_when_kind_invalid_raises` | AC-2 |
| `test_load_when_name_filename_mismatch_raises` | AC-2 |
| `test_load_when_path_lacks_stage_interpolation_raises` | AC-2 |
| `test_load_when_stages_contains_local_raises` | AC-2 |
| `test_load_when_ssm_type_invalid_raises` | AC-2 |
| `test_load_when_secret_duplicated_raises` | AC-2 |
| `test_get_when_unknown_raises_with_known_list` | AC-2 |
| `test_for_stage_filters_by_stage_membership` | AC-1 |
| `test_path_for_when_stage_not_in_stages_raises` | AC-1 |

Fixtures de YAML válido/inválido en `devtools/tests/serverless/_fixtures/secrets_catalog/`.

## Archivos afectados

### Crear

- `devtools/serverless/secrets_catalog.py` — parser + dataclasses
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`
- `devtools/tests/serverless/test_secrets_catalog.py` — suite TDD
  - Verificar: `pytest devtools/tests/serverless/test_secrets_catalog.py -v`
- `devtools/tests/serverless/_fixtures/secrets_catalog/*.yaml` — fixtures
  - Verificar: tests pasan

### Modificar

- `devtools/serverless/__init__.py` — re-exportar `Catalog`, `SecretSpec`, `CatalogError`
  - Verificar: `python -c "from devtools.serverless import Catalog"` (import OK)

## Verify-before-done

```bash
python devtools/run.py serverless tests --type=unit --lambda=devtools  # si aplica
# o directo:
pytest devtools/tests/serverless/test_secrets_catalog.py -v
ruff check devtools/serverless/secrets_catalog.py
```
