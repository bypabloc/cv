"""Descriptores de esquema del ORM DynamoDB.

`TableMeta` declara el esquema MINIMO que el ORM necesita para operar y
para detectar drift: claves (PK/SK), atributo TTL y GSIs. NO declara
`BillingMode`/`SSE`/`PITR`/`StreamSpecification` — esos quedan como
responsabilidad exclusiva de `serverless/infra/infra.yaml` (el stack
CloudFormation es el dueno del DDL real de dev/prod).

`create_table`/`ensure_table` del `BaseModel` usan `TableMeta` SOLO para
tests (moto) y entorno local. `check_schema` lo usa para comparar contra
la tabla real en AWS y reportar divergencias.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GSIMeta:
    """Descriptor de un Global Secondary Index.

    Parameters
    ----------
    name : str
        Nombre del indice (ej. `niche-created_at-index`).
    partition_key : str
        Atributo HASH del indice.
    sort_key : str | None
        Atributo RANGE del indice, o `None` si el GSI es solo-HASH.
    """

    name: str
    partition_key: str
    sort_key: str | None = None


@dataclass(frozen=True, slots=True)
class TableMeta:
    """Descriptor declarativo de una tabla DynamoDB.

    Parameters
    ----------
    table_env_var : str
        Nombre de la env var con el nombre fisico de la tabla
        (ej. `CONTACTS_TABLE_NAME`). Se usa en tests/local.
    table_default : str
        Nombre fisico por defecto si no se resuelve por SSM ni env var.
    partition_key : str
        Atributo HASH de la tabla.
    sort_key : str | None
        Atributo RANGE de la tabla, o `None` si la PK es simple.
    ttl_attr : str | None
        Atributo usado por el TTL service de AWS, o `None` si no hay TTL.
    gsis : tuple[GSIMeta, ...]
        Indices secundarios globales declarados (vacio si no hay).
    table_ssm_env : str
        Nombre de la env var que lleva el PATH SSM del nombre de tabla
        (ej. `SSM_CONTACTS_TABLE_PATH`). En AWS el template SAM la
        inyecta; el codigo resuelve el path via SSM en el cold start.
        Vacio en los modelos que no usan resolucion por SSM.
    """

    table_env_var: str
    table_default: str
    partition_key: str
    sort_key: str | None = None
    ttl_attr: str | None = None
    gsis: tuple[GSIMeta, ...] = ()
    table_ssm_env: str = ''

    def key_attributes(self) -> set[str]:
        """Conjunto de atributos que participan en alguna key (tabla + GSI).

        Returns
        -------
        set[str]
            Nombres de atributos referenciados por la PK/SK de la tabla y
            de cada GSI. Sirve para armar las `AttributeDefinitions`.
        """
        attrs: set[str] = {self.partition_key}
        if self.sort_key:
            attrs.add(self.sort_key)
        for gsi in self.gsis:
            attrs.add(gsi.partition_key)
            if gsi.sort_key:
                attrs.add(gsi.sort_key)
        return attrs


@dataclass(slots=True)
class SchemaDiff:
    """Resultado de comparar un `TableMeta` contra una tabla real en AWS.

    El diff esta `in_sync` cuando todas las listas de divergencia estan
    vacias y `keys_match`/`ttl_match` son `True`.

    Parameters
    ----------
    table_name : str
        Nombre fisico de la tabla comparada.
    exists : bool
        `True` si la tabla existe en AWS.
    keys_match : bool
        `True` si el `KeySchema` real coincide con el `TableMeta`.
    ttl_match : bool
        `True` si el atributo TTL real coincide con el `TableMeta`.
    gsi_missing : list[str]
        GSIs declarados en `TableMeta` ausentes en la tabla real.
    gsi_unexpected : list[str]
        GSIs presentes en la tabla real no declarados en `TableMeta`.
    notes : list[str]
        Observaciones legibles (ej. detalle de un mismatch de key).
    """

    table_name: str
    exists: bool
    keys_match: bool = False
    ttl_match: bool = False
    gsi_missing: list[str] = field(default_factory=list)
    gsi_unexpected: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def in_sync(self) -> bool:
        """`True` si la tabla real coincide exactamente con el `TableMeta`."""
        return (
            self.exists
            and self.keys_match
            and self.ttl_match
            and not self.gsi_missing
            and not self.gsi_unexpected
        )


def _key_schema(partition_key: str, sort_key: str | None) -> list[dict[str, str]]:
    """Construye el `KeySchema` de boto3 para una PK + SK opcional."""
    schema = [{'AttributeName': partition_key, 'KeyType': 'HASH'}]
    if sort_key:
        schema.append({'AttributeName': sort_key, 'KeyType': 'RANGE'})
    return schema


def build_create_table_kwargs(meta: TableMeta, table_name: str) -> dict[str, Any]:
    """Arma los kwargs de `create_table` desde un `TableMeta`.

    Pensado SOLO para tests (moto) y local: las tablas reales las crea
    CloudFormation. Usa `BillingMode=PAY_PER_REQUEST` (mismo modo que
    `infra.yaml`); el TTL se activa aparte con `update_time_to_live`.

    Parameters
    ----------
    meta : TableMeta
        Descriptor de la tabla.
    table_name : str
        Nombre fisico resuelto de la tabla.

    Returns
    -------
    dict[str, Any]
        kwargs listos para `client.create_table(**kwargs)`.
    """
    attr_defs = [
        {'AttributeName': name, 'AttributeType': 'S'}
        for name in sorted(meta.key_attributes())
    ]
    kwargs: dict[str, Any] = {
        'TableName': table_name,
        'AttributeDefinitions': attr_defs,
        'KeySchema': _key_schema(meta.partition_key, meta.sort_key),
        'BillingMode': 'PAY_PER_REQUEST',
    }
    if meta.gsis:
        kwargs['GlobalSecondaryIndexes'] = [
            {
                'IndexName': gsi.name,
                'KeySchema': _key_schema(gsi.partition_key, gsi.sort_key),
                'Projection': {'ProjectionType': 'ALL'},
            }
            for gsi in meta.gsis
        ]
    return kwargs


def diff_table(
    meta: TableMeta,
    table_name: str,
    description: dict[str, Any] | None,
    ttl_attr: str | None,
) -> SchemaDiff:
    """Compara un `TableMeta` contra la descripcion real de una tabla.

    Parameters
    ----------
    meta : TableMeta
        Esquema esperado.
    table_name : str
        Nombre fisico de la tabla.
    description : dict[str, Any] | None
        Salida de `describe_table` (la clave `Table`), o `None` si la
        tabla no existe.
    ttl_attr : str | None
        Atributo TTL activo segun `describe_time_to_live`, o `None`.

    Returns
    -------
    SchemaDiff
        Diff detallado.
    """
    if description is None:
        return SchemaDiff(table_name=table_name, exists=False)

    diff = SchemaDiff(table_name=table_name, exists=True)

    expected_keys = _key_schema(meta.partition_key, meta.sort_key)
    real_keys = description.get('KeySchema', [])
    diff.keys_match = expected_keys == real_keys
    if not diff.keys_match:
        diff.notes.append(
            f'KeySchema esperado {expected_keys}, real {real_keys}',
        )

    diff.ttl_match = meta.ttl_attr == ttl_attr
    if not diff.ttl_match:
        diff.notes.append(
            f'TTL esperado {meta.ttl_attr!r}, real {ttl_attr!r}',
        )

    expected_gsi = {gsi.name for gsi in meta.gsis}
    real_gsi = {
        idx['IndexName']
        for idx in description.get('GlobalSecondaryIndexes', [])
    }
    diff.gsi_missing = sorted(expected_gsi - real_gsi)
    diff.gsi_unexpected = sorted(real_gsi - expected_gsi)

    return diff
