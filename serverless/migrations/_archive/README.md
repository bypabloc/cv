# migrations/_archive — runner SQL viejo (historico)

> Estos archivos NO se aplican mas. Se conservan solo como referencia
> historica del schema previo.

## Que era esto

Hasta mayo de 2026 el schema PostgreSQL del backend se versionaba con un
runner SQL casero: archivos numerados `NNN_<nombre>.sql` (+ su par
`.down.sql`) aplicados por `serverless/scripts/migrate.py`, con la tabla
`schema_migrations` como registro.

## Que lo reemplazo

Todo el schema PostgreSQL del portfolio (las tablas del backend + las del
CV) se unifico en un solo set de modelos SQLAlchemy 2.x en
`serverless/shared/db/`, gestionado por **un solo Alembic**. La
migracion inicial de Alembic (`shared/db/alembic/versions/`) reproduce el
schema que estos `.sql` construian.

La Lambda `db` (`serverless/src/db/`) corre Alembic dentro de AWS:
`{"command": "migrate"}`, `{"command": "downgrade"}`, etc. La tabla de
versiones pasa a ser la estandar `alembic_version`.

## Adopcion en prod

En la DB de produccion (que ya tiene el schema creado por estos `.sql`) NO
se corre `migrate` — se corre `{"command": "stamp"}` una vez, que marca la
revision de Alembic como aplicada SIN recrear nada. La tabla
`schema_migrations` vieja se elimina en una migracion Alembic posterior.

## Por que se conservan

Trazabilidad: el `git log` de estos archivos documenta como evoluciono el
schema antes de la unificacion. No borrarlos.
