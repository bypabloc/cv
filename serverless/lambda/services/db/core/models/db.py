"""Modelos Pydantic de la operacion `db`.

Un modelo por action. Cada modelo valida el campo `data` del evento
(que el handler sintetiza desde `args` del payload de invocacion).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict


class MigrateModel(BaseModel):
    """Valida el payload de db/migrate.

    `target` es opcional (default `head`).
    """

    target: str = 'head'

    model_config = ConfigDict(extra='forbid')


class CurrentModel(BaseModel):
    """Valida el payload de db/current (sin campos)."""

    model_config = ConfigDict(extra='forbid')


class ShowMigrationsModel(BaseModel):
    """Valida el payload de db/show_migrations (sin campos)."""

    model_config = ConfigDict(extra='forbid')


class StampModel(BaseModel):
    """Valida el payload de db/stamp.

    `target` es opcional (default `head`).
    """

    target: str = 'head'

    model_config = ConfigDict(extra='forbid')


class DowngradeModel(BaseModel):
    """Valida el payload de db/downgrade.

    Operacion destructiva: `target` es obligatorio y `confirm` debe ser
    `true`. La validacion de `confirm` la hace el controller (es una
    regla de negocio, no de estructura), no este modelo.
    """

    target: str
    confirm: bool = False

    model_config = ConfigDict(extra='forbid')


class TablesModel(BaseModel):
    """Valida el payload de db/tables (sin campos)."""

    model_config = ConfigDict(extra='forbid')


class SeedModel(BaseModel):
    """Valida el payload de db/seed (restore de un snapshot).

    `source` es opcional: prefijo S3 `s3://bucket/prefix/` o path local;
    None usa el `latest/` del bucket de backups del stage.
    `confirm_overwrite` es obligatorio en `true` cuando las tablas CV ya
    tienen datos (la validacion es del service: regla de negocio).
    """

    source: str | None = None
    confirm_overwrite: bool = False

    model_config = ConfigDict(extra='forbid')
