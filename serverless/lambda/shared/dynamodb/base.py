"""`BaseModel`: ORM minimalista para DynamoDB.

Cada tabla del backend se modela como una subclase de `BaseModel`
(Pydantic) con un `Meta: TableMeta` que declara claves, TTL y GSIs. El
`BaseModel` encapsula TODO el acceso boto3, reusa el resource singleton
de `shared.dynamodb_client` y convierte `Decimal` de forma transparente.

Capas expuestas:
  - DML (datos): save/get/query/update/delete + atomicas
    (increment/put_if_absent/conditional_update).
  - DDL (esquema): table_exists/describe_table/check_schema +
    create_table/ensure_table. create_table/ensure_table son SOLO para
    tests (moto) y local — las tablas reales las crea `infra.yaml`.

Uso:
    class ContactItem(BaseModel):
        Meta = TableMeta(
            table_env_var='CONTACTS_TABLE_NAME',
            table_default='portfolio-contacts-dev',
            partition_key='id',
        )
        id: str
        created_at: str
        name: str

    ContactItem(id='...', created_at='...', name='Pablo').save()
    item = ContactItem.get('the-id')
"""

from __future__ import annotations

import os
from typing import Any, ClassVar, Self

from botocore.exceptions import ClientError
from pydantic import BaseModel as PydanticBaseModel

from shared.aws.dynamodb import get_resource, get_table
from shared.dynamodb._convert import from_dynamodb, is_empty, to_dynamodb
from shared.dynamodb._schema import (
    SchemaDiff,
    TableMeta,
    build_create_table_kwargs,
    diff_table,
)


class BaseModel(PydanticBaseModel):
    """Modelo base de una tabla DynamoDB (1 subclase = 1 tabla).

    Las subclases declaran `Meta: ClassVar[TableMeta]` y sus campos como
    atributos Pydantic tipados.
    """

    # Cada subclase sobreescribe Meta. Anotado como ClassVar para que
    # Pydantic no lo trate como un campo del modelo.
    Meta: ClassVar[TableMeta]

    # ---- resolucion de la tabla -------------------------------------------

    @classmethod
    def table_name(cls) -> str:
        """Nombre fisico de la tabla.

        Resolucion, en orden de precedencia:
          1. `table_ssm_env` seteada -> la env var lleva un PATH SSM; se
             resuelve el path via SSM (Powertools cache). Es el modo de
             AWS: el stack del recurso publica el nombre en SSM.
          2. `table_env_var` seteada directo -> el nombre fisico literal
             (tests/local, donde no hay SSM).
          3. `table_default` -> fallback.
        """
        ssm_env = cls.Meta.table_ssm_env
        if ssm_env:
            ssm_path = os.environ.get(ssm_env)
            if ssm_path:
                from shared.aws.ssm import get_parameter

                return get_parameter(ssm_path)
        return os.environ.get(cls.Meta.table_env_var, cls.Meta.table_default)

    @classmethod
    def _table(cls) -> Any:
        """boto3 Table sobre el resource singleton de `dynamodb_client`."""
        return get_table(cls.table_name())

    # ---- serializacion ----------------------------------------------------

    def to_item(self) -> dict[str, Any]:
        """Serializa el modelo a un Item DynamoDB.

        Omite los campos `None`/`''` (DynamoDB no acepta empty strings) y
        convierte `float` a `Decimal`. El `0`, el `False` y las
        colecciones vacias SI se incluyen.

        Returns
        -------
        dict[str, Any]
            Item apto para `put_item`.
        """
        raw = self.model_dump(exclude_none=True)
        return {
            key: to_dynamodb(value)
            for key, value in raw.items()
            if not is_empty(value)
        }

    @classmethod
    def _from_item(cls, item: dict[str, Any]) -> Self:
        """Construye un modelo desde un Item DynamoDB.

        Convierte los `Decimal` de DynamoDB a `int`/`float` antes de pasar
        el dict al constructor Pydantic.

        Parameters
        ----------
        item : dict[str, Any]
            Item crudo devuelto por boto3.

        Returns
        -------
        Self
            Instancia del modelo.
        """
        return cls(**from_dynamodb(item))

    @classmethod
    def _key(
        cls, partition_value: Any, sort_value: Any = None
    ) -> dict[str, Any]:
        """Arma el dict `Key` para get/update/delete."""
        key: dict[str, Any] = {cls.Meta.partition_key: partition_value}
        if cls.Meta.sort_key is not None:
            if sort_value is None:
                msg = (
                    f'{cls.__name__}: la tabla tiene sort_key '
                    f'{cls.Meta.sort_key!r}, hay que pasar sort_value'
                )
                raise ValueError(msg)
            key[cls.Meta.sort_key] = sort_value
        return key

    # ---- DML: lectura / escritura -----------------------------------------

    def save(self) -> Self:
        """Persiste el modelo con `put_item` (upsert).

        Returns
        -------
        Self
            El propio modelo, para encadenar.
        """
        self._table().put_item(Item=self.to_item())
        return self

    @classmethod
    def get(
        cls, partition_value: Any, sort_value: Any = None
    ) -> Self | None:
        """Lee un item por su key.

        Parameters
        ----------
        partition_value : Any
            Valor de la partition key.
        sort_value : Any
            Valor de la sort key (obligatorio si la tabla tiene SK).

        Returns
        -------
        Self | None
            El modelo, o `None` si el item no existe.
        """
        result = cls._table().get_item(
            Key=cls._key(partition_value, sort_value)
        )
        item = result.get('Item')
        if item is None:
            return None
        return cls._from_item(item)

    @classmethod
    def query(
        cls,
        partition_value: Any,
        *,
        sort_condition: Any = None,
        index_name: str | None = None,
        limit: int | None = None,
    ) -> list[Self]:
        """Consulta items por partition key (tabla base o GSI).

        Parameters
        ----------
        partition_value : Any
            Valor de la partition key a igualar.
        sort_condition : Any
            Condicion opcional sobre la sort key, una expresion
            `boto3.dynamodb.conditions.Key(...)` ya construida (ej.
            `Key('created_at').begins_with('2026')`).
        index_name : str | None
            Nombre del GSI a consultar, o `None` para la tabla base.
        limit : int | None
            Maximo de items a devolver.

        Returns
        -------
        list[Self]
            Items que matchean, como modelos.
        """
        from boto3.dynamodb.conditions import Key

        partition_key = cls._partition_key_for(index_name)
        key_expr = Key(partition_key).eq(partition_value)
        if sort_condition is not None:
            key_expr = key_expr & sort_condition

        kwargs: dict[str, Any] = {'KeyConditionExpression': key_expr}
        if index_name is not None:
            kwargs['IndexName'] = index_name
        if limit is not None:
            kwargs['Limit'] = limit

        result = cls._table().query(**kwargs)
        return [cls._from_item(item) for item in result.get('Items', [])]

    @classmethod
    def _partition_key_for(cls, index_name: str | None) -> str:
        """Partition key de la tabla base o del GSI indicado."""
        if index_name is None:
            return cls.Meta.partition_key
        for gsi in cls.Meta.gsis:
            if gsi.name == index_name:
                return gsi.partition_key
        msg = f'{cls.__name__}: GSI desconocido {index_name!r}'
        raise ValueError(msg)

    @classmethod
    def update(
        cls,
        partition_value: Any,
        sort_value: Any = None,
        **fields: Any,
    ) -> Self:
        """Actualiza atributos de un item con `SET` (upsert del atributo).

        Parameters
        ----------
        partition_value : Any
            Valor de la partition key.
        sort_value : Any
            Valor de la sort key (si aplica).
        **fields : Any
            Atributos a setear.

        Returns
        -------
        Self
            El item resultante (`ReturnValues='ALL_NEW'`).
        """
        if not fields:
            msg = f'{cls.__name__}.update: no se paso ningun campo'
            raise ValueError(msg)

        names = {f'#{k}': k for k in fields}
        values = {f':{k}': to_dynamodb(v) for k, v in fields.items()}
        set_expr = ', '.join(f'#{k} = :{k}' for k in fields)

        result = cls._table().update_item(
            Key=cls._key(partition_value, sort_value),
            UpdateExpression=f'SET {set_expr}',
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues='ALL_NEW',
        )
        return cls._from_item(result['Attributes'])

    @classmethod
    def delete(cls, partition_value: Any, sort_value: Any = None) -> None:
        """Elimina un item por su key (hard delete, idempotente)."""
        cls._table().delete_item(Key=cls._key(partition_value, sort_value))

    # ---- DML: operaciones atomicas ----------------------------------------

    def put_if_absent(self) -> bool:
        """Escribe el item solo si no existe ya uno con esa key.

        Genera un `ConditionExpression attribute_not_exists(PK)`.

        Returns
        -------
        bool
            `True` si escribio, `False` si ya existia.
        """
        try:
            self._table().put_item(
                Item=self.to_item(),
                ConditionExpression=(
                    f'attribute_not_exists({self.Meta.partition_key})'
                ),
            )
            return True
        except ClientError as exc:
            if (
                exc.response['Error']['Code']
                == 'ConditionalCheckFailedException'
            ):
                return False
            raise

    @classmethod
    def increment(
        cls,
        partition_value: Any,
        sort_value: Any = None,
        *,
        set_fields: dict[str, Any] | None = None,
        **deltas: int,
    ) -> dict[str, int]:
        """Incremento atomico de uno o varios contadores (`ADD`).

        Crea el item si no existe (semantica `ADD` de DynamoDB). Si se
        pasa `set_fields`, ademas setea esos atributos en el MISMO
        `UpdateExpression` (ej. refrescar `expires_at` del bucket).

        Parameters
        ----------
        partition_value : Any
            Valor de la partition key.
        sort_value : Any
            Valor de la sort key (si aplica).
        set_fields : dict[str, Any] | None
            Atributos a setear con `SET` junto al `ADD`.
        **deltas : int
            Atributo -> delta a sumar.

        Returns
        -------
        dict[str, int]
            Valores actualizados de los contadores (`ReturnValues
            ALL_NEW`), ya convertidos a `int`.
        """
        if not deltas:
            msg = f'{cls.__name__}.increment: no se paso ningun delta'
            raise ValueError(msg)

        names = {f'#{k}': k for k in deltas}
        values: dict[str, Any] = {f':{k}': v for k, v in deltas.items()}
        add_expr = ', '.join(f'#{k} :{k}' for k in deltas)
        update_expr = f'ADD {add_expr}'

        if set_fields:
            names.update({f'#set_{k}': k for k in set_fields})
            values.update(
                {f':set_{k}': to_dynamodb(v) for k, v in set_fields.items()}
            )
            set_expr = ', '.join(
                f'#set_{k} = :set_{k}' for k in set_fields
            )
            update_expr = f'{update_expr} SET {set_expr}'

        result = cls._table().update_item(
            Key=cls._key(partition_value, sort_value),
            UpdateExpression=update_expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues='ALL_NEW',
        )
        attrs = from_dynamodb(result.get('Attributes', {}))
        return {k: int(attrs.get(k, 0)) for k in deltas}

    @classmethod
    def conditional_update(
        cls,
        partition_value: Any,
        sort_value: Any = None,
        *,
        condition: str,
        condition_values: dict[str, Any] | None = None,
        condition_names: dict[str, str] | None = None,
        **fields: Any,
    ) -> Self | None:
        """Actualiza atributos solo si se cumple una condicion.

        Parameters
        ----------
        partition_value : Any
            Valor de la partition key.
        sort_value : Any
            Valor de la sort key (si aplica).
        condition : str
            `ConditionExpression` (ej. `'#value = :holder'`).
        condition_values : dict[str, Any] | None
            Valores referenciados por la condicion (ej. `{':holder': id}`).
        condition_names : dict[str, str] | None
            Alias de atributo de la condicion (ej. `{'#value': 'value'}`).
            Necesario cuando la condicion referencia una palabra reservada.
        **fields : Any
            Atributos a setear si la condicion pasa.

        Returns
        -------
        Self | None
            El item actualizado, o `None` si la condicion fallo.
        """
        if not fields:
            msg = (
                f'{cls.__name__}.conditional_update: '
                'no se paso ningun campo'
            )
            raise ValueError(msg)

        names = {f'#{k}': k for k in fields}
        names.update(condition_names or {})
        values: dict[str, Any] = {
            f':{k}': to_dynamodb(v) for k, v in fields.items()
        }
        values.update(condition_values or {})
        set_expr = ', '.join(f'#{k} = :{k}' for k in fields)

        try:
            result = cls._table().update_item(
                Key=cls._key(partition_value, sort_value),
                UpdateExpression=f'SET {set_expr}',
                ConditionExpression=condition,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ReturnValues='ALL_NEW',
            )
            return cls._from_item(result['Attributes'])
        except ClientError as exc:
            if (
                exc.response['Error']['Code']
                == 'ConditionalCheckFailedException'
            ):
                return None
            raise

    # ---- DDL: verificacion de esquema -------------------------------------

    @classmethod
    def table_exists(cls) -> bool:
        """`True` si la tabla existe en DynamoDB."""
        client = get_resource().meta.client
        try:
            client.describe_table(TableName=cls.table_name())
            return True
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise

    @classmethod
    def describe_table(cls) -> dict[str, Any] | None:
        """Descripcion de la tabla (`describe_table.Table`), o `None`."""
        client = get_resource().meta.client
        try:
            response = client.describe_table(TableName=cls.table_name())
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise
        table: dict[str, Any] = response['Table']
        return table

    @classmethod
    def _ttl_attribute(cls) -> str | None:
        """Atributo TTL activo en la tabla real, o `None`."""
        client = get_resource().meta.client
        try:
            spec = client.describe_time_to_live(TableName=cls.table_name())
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise
        desc = spec.get('TimeToLiveDescription', {})
        if desc.get('TimeToLiveStatus') in ('ENABLED', 'ENABLING'):
            attr: str | None = desc.get('AttributeName')
            return attr
        return None

    @classmethod
    def check_schema(cls) -> SchemaDiff:
        """Compara el `TableMeta` contra la tabla real en AWS.

        Llama `describe_table` + `describe_time_to_live` y reporta las
        divergencias de `KeySchema`, TTL y GSIs. Necesita credenciales
        AWS (uso operativo / CI con creds).

        Returns
        -------
        SchemaDiff
            Diff detallado; `diff.in_sync` resume el resultado.
        """
        description = cls.describe_table()
        ttl_attr = cls._ttl_attribute() if description is not None else None
        return diff_table(
            cls.Meta, cls.table_name(), description, ttl_attr
        )

    # ---- DDL: creacion (SOLO tests / local) -------------------------------

    @classmethod
    def create_table(cls) -> None:
        """Crea la tabla desde el `TableMeta`. SOLO para tests/local.

        Las tablas de dev/stage/prod las crea CloudFormation
        (`infra.yaml`). Este metodo existe para los tests con `moto` y el
        entorno local. Activa el TTL si el `TableMeta` declara `ttl_attr`.
        """
        client = get_resource().meta.client
        kwargs = build_create_table_kwargs(cls.Meta, cls.table_name())
        client.create_table(**kwargs)
        client.get_waiter('table_exists').wait(TableName=cls.table_name())
        if cls.Meta.ttl_attr:
            client.update_time_to_live(
                TableName=cls.table_name(),
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': cls.Meta.ttl_attr,
                },
            )

    @classmethod
    def ensure_table(cls) -> None:
        """Crea la tabla si no existe; no hace nada si ya existe.

        Idempotente. SOLO para tests/local (ver `create_table`).
        """
        if not cls.table_exists():
            cls.create_table()
