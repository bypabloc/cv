"""Parser del catalogo de secretos / parametros SSM.

Lee `serverless/lambda/resources/secrets/*.yaml` y expone una coleccion
inmutable de `SecretSpec`. Reemplaza los diccionarios hardcodeados
`_SECRETS` (provisioner.py) y `_SSM_PARAMETERS` (secrets.py).

Schema del YAML (uno por secreto/parametro):

```yaml
kind: ssm-parameter
name: turnstile-secret
description: Cloudflare Turnstile secret key (siteverify)
path: /portfolio/${stage}/turnstile-secret
ssm_type: SecureString          # SecureString | String
kms_key_alias: alias/portfolio-lambdas   # solo si SecureString
source_env_var: TURNSTILE_SECRET_KEY     # KEY en docker/env/server/.{stage}
target_env_var: SSM_TURNSTILE_SECRET_PATH  # env var del Lambda
stages: [dev, stage, prod]
required: true

# opcional
rotation: { interval_days: 90, last_rotated: 2026-05-22 }
owners: [pacg1991@gmail.com]
consumed_by: [contact_form]
tags: { Project: portfolio, ManagedBy: devtools }
```

Reglas duras:

- `kind` debe ser exactamente `ssm-parameter`.
- `name` debe coincidir con el stem del archivo
  (`turnstile-secret.yaml` -> `name: turnstile-secret`).
- `path` debe contener `${stage}` literal SOLO si declara mas de un
  stage o uno diferente al "global". Path sin `${stage}` -> parametro
  global compartido por todos los stages listados.
- `stages` no puede contener `local` (local NO usa SSM).
- `ssm_type` en {`SecureString`, `String`}.
- Para `SecureString`, `kms_key_alias` default a
  `alias/portfolio-lambdas`.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


# Path al directorio del catalogo, relativo al repo.
_CATALOG_DIR = (
    Path(__file__).resolve().parents[2]
    / 'serverless'
    / 'lambda'
    / 'resources'
    / 'secrets'
)

# Stages permitidos en el campo `stages` del YAML. `local` queda
# explicitamente fuera (modo offline-dev sin AWS).
_VALID_STAGES: frozenset[str] = frozenset({'dev', 'prod'})

# Tipos SSM permitidos.
_VALID_SSM_TYPES: frozenset[str] = frozenset({'SecureString', 'String'})

# Default de KMS key alias para SecureString del portfolio.
_DEFAULT_KMS_ALIAS = 'alias/portfolio-lambdas'

# Discriminador del tipo de recurso. Otros recursos en `resources/`
# usan kinds distintos (dynamodb-table, sqs-queue, rest-api).
_EXPECTED_KIND = 'ssm-parameter'

# Campos obligatorios del YAML.
_REQUIRED_FIELDS: tuple[str, ...] = (
    'kind',
    'name',
    'description',
    'path',
    'ssm_type',
    'source_env_var',
    'target_env_var',
    'stages',
    'required',
)


class CatalogError(ValueError):
    """Error en el catalogo (YAML invalido o inconsistente)."""


@dataclass(frozen=True)
class SecretSpec:
    """Una entrada del catalogo, ya validada y normalizada."""

    name: str
    description: str
    path_template: str
    ssm_type: str
    kms_key_alias: str | None
    source_env_var: str
    target_env_var: str
    stages: frozenset[str]
    required: bool
    rotation: dict[str, Any] | None
    owners: tuple[str, ...]
    consumed_by: tuple[str, ...]
    tags: dict[str, str]
    source_file: Path

    def path_for(self, stage: str) -> str:
        """Resuelve el path SSM concreto para un stage."""
        if stage not in self.stages:
            raise CatalogError(
                f'secreto {self.name!r} no esta declarado en stage '
                f'{stage!r} (stages={sorted(self.stages)})',
            )
        return self.path_template.replace('${stage}', stage)


@dataclass(frozen=True)
class Catalog:
    """Catalogo cargado en memoria."""

    by_name: dict[str, SecretSpec] = field(default_factory=dict)

    @classmethod
    def load(cls, directory: Path | None = None) -> Catalog:
        """Carga todos los YAML del directorio."""
        target = directory if directory is not None else _CATALOG_DIR
        if not target.exists():
            raise CatalogError(
                f'directorio del catalogo no existe: {target}',
            )
        by_name: dict[str, SecretSpec] = {}
        for yaml_path in sorted(target.glob('*.yaml')):
            spec = _load_one(yaml_path)
            if spec.name in by_name:
                raise CatalogError(
                    f'secreto duplicado {spec.name!r}: '
                    f'{by_name[spec.name].source_file} vs {yaml_path}',
                )
            by_name[spec.name] = spec
        return cls(by_name=by_name)

    def get(self, name: str) -> SecretSpec:
        """Devuelve un secreto por nombre corto."""
        spec = self.by_name.get(name)
        if spec is None:
            known = sorted(self.by_name)
            raise CatalogError(
                f'secreto desconocido {name!r}. Conocidos: {known}',
            )
        return spec

    def for_stage(self, stage: str) -> tuple[SecretSpec, ...]:
        """Devuelve los secretos publicables en el stage dado."""
        return tuple(s for s in self.by_name.values() if stage in s.stages)

    def __len__(self) -> int:
        return len(self.by_name)


def _parse_yaml_file(yaml_path: Path) -> dict[str, Any]:
    """Lee el YAML del catalogo y valida que sea un mapa."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise CatalogError(
            'PyYAML no esta instalado en el entorno de devtools',
        ) from exc

    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise CatalogError(
            f'YAML mal formado ({yaml_path}): {exc}',
        ) from exc

    if not isinstance(raw, dict):
        raise CatalogError(
            f'el YAML del catalogo debe ser un mapa ({yaml_path})',
        )
    return raw


def _validate_required_fields(yaml_path: Path, raw: dict[str, Any]) -> None:
    missing = [f for f in _REQUIRED_FIELDS if f not in raw]
    if missing:
        raise CatalogError(
            f'{yaml_path.name}: faltan campos obligatorios: '
            f'{", ".join(missing)}',
        )


def _validate_kind_and_name(yaml_path: Path, raw: dict[str, Any]) -> str:
    """Valida `kind` y que `name` coincida con el filename stem."""
    if raw['kind'] != _EXPECTED_KIND:
        raise CatalogError(
            f'{yaml_path.name}: kind invalido {raw["kind"]!r}, '
            f'esperado {_EXPECTED_KIND!r}',
        )
    name = raw['name']
    if name != yaml_path.stem:
        raise CatalogError(
            f'{yaml_path.name}: name {name!r} no coincide con el '
            f'filename stem {yaml_path.stem!r}',
        )
    return name


def _validate_ssm_type(yaml_path: Path, raw: dict[str, Any]) -> str:
    ssm_type = raw['ssm_type']
    if ssm_type not in _VALID_SSM_TYPES:
        raise CatalogError(
            f'{yaml_path.name}: ssm_type invalido {ssm_type!r}. '
            f'Validos: {sorted(_VALID_SSM_TYPES)}',
        )
    return ssm_type


def _validate_stages(
    yaml_path: Path,
    raw: dict[str, Any],
) -> frozenset[str]:
    stages_raw = raw['stages']
    if not isinstance(stages_raw, list) or not stages_raw:
        raise CatalogError(
            f'{yaml_path.name}: stages debe ser una lista no vacia',
        )
    stages = frozenset(stages_raw)
    invalid_stages = stages - _VALID_STAGES
    if invalid_stages:
        raise CatalogError(
            f'{yaml_path.name}: stages invalidos {sorted(invalid_stages)}. '
            f'Validos: {sorted(_VALID_STAGES)}',
        )
    return stages


def _validate_required_flag(yaml_path: Path, raw: dict[str, Any]) -> bool:
    required = raw['required']
    if not isinstance(required, bool):
        raise CatalogError(
            f'{yaml_path.name}: required debe ser bool (true/false), '
            f'got {type(required).__name__}',
        )
    return required


def _validate_optional_collections(
    yaml_path: Path,
    raw: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[Any], list[Any], dict[str, Any]]:
    """Valida y devuelve los bloques opcionales (rotation/owners/consumed_by/tags)."""
    rotation = raw.get('rotation')
    if rotation is not None and not isinstance(rotation, dict):
        raise CatalogError(
            f'{yaml_path.name}: rotation debe ser un mapa',
        )
    owners_raw = raw.get('owners') or []
    if not isinstance(owners_raw, list):
        raise CatalogError(
            f'{yaml_path.name}: owners debe ser una lista',
        )
    consumed_raw = raw.get('consumed_by') or []
    if not isinstance(consumed_raw, list):
        raise CatalogError(
            f'{yaml_path.name}: consumed_by debe ser una lista',
        )
    tags_raw = raw.get('tags') or {}
    if not isinstance(tags_raw, dict):
        raise CatalogError(
            f'{yaml_path.name}: tags debe ser un mapa',
        )
    return rotation, owners_raw, consumed_raw, tags_raw


def _load_one(yaml_path: Path) -> SecretSpec:
    """Lee y valida un YAML individual."""
    raw = _parse_yaml_file(yaml_path)
    _validate_required_fields(yaml_path, raw)
    name = _validate_kind_and_name(yaml_path, raw)
    ssm_type = _validate_ssm_type(yaml_path, raw)
    stages = _validate_stages(yaml_path, raw)
    required = _validate_required_flag(yaml_path, raw)
    rotation, owners_raw, consumed_raw, tags_raw = (
        _validate_optional_collections(yaml_path, raw)
    )
    kms_alias: str | None = None
    if ssm_type == 'SecureString':
        kms_alias = raw.get('kms_key_alias', _DEFAULT_KMS_ALIAS)
    path = raw['path']

    return SecretSpec(
        name=name,
        description=raw['description'],
        path_template=path,
        ssm_type=ssm_type,
        kms_key_alias=kms_alias,
        source_env_var=raw['source_env_var'],
        target_env_var=raw['target_env_var'],
        stages=stages,
        required=required,
        rotation=rotation,
        owners=tuple(owners_raw),
        consumed_by=tuple(consumed_raw),
        tags=dict(tags_raw),
        source_file=yaml_path,
    )
