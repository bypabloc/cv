# Fase B — shared.db re-exporta SQLAlchemy

> shared.db es el portador unico de SQLAlchemy. Re-exporta el subset que el
> seeder usa hoy: `select`, `func`, `insert` (postgresql con `on_conflict_do_update`),
> `Session`, mas `Base` y `db_session` que ya estaban.

## Contexto / Problema

- `db/core/services/seed_service.py` importa directo de `sqlalchemy`:
  - `from sqlalchemy import select, func`
  - `from sqlalchemy.dialects.postgresql import insert`
  - `from sqlalchemy.orm import Session`
- `shared.db.__init__` exporta `Base`, `db_session`, `get_engine`, helpers
  del repository (`insert_contact`, `mark_event_processed`, etc.) pero NO
  re-exporta los simbolos crudos de SQLAlchemy.

## Solucion

1. Editar `shared/db/__init__.py`:
   - `from sqlalchemy import func, select`
   - `from sqlalchemy.dialects.postgresql import insert as pg_insert`
   - `from sqlalchemy.orm import Session`
   - Extender `__all__` con `func`, `select`, `pg_insert`, `Session`.
2. Decision de naming: re-exportar `insert` de postgresql como `pg_insert`
   para evitar shadowing con un futuro `insert` SQL plano. El seeder cambia
   `from sqlalchemy.dialects.postgresql import insert` a `from shared.db
   import pg_insert as insert` (alias local opcional).
3. NO modificar `seed_service.py` aqui (Fase E).

## Archivos afectados

### Modificar

- `serverless/lambda/shared/db/__init__.py` — agrega re-exports SQLAlchemy.
  - Verificar: `python -c "from shared.db import select, func, pg_insert, Session"` desde `serverless/lambda/`.

## Criterios de aceptacion

- **AC-B1**: Given la fase B aplicada, When importo `from shared.db import
  select, func, pg_insert, Session`, Then importacion exitosa.
- **AC-B2**: Given el `pg_insert` re-exportado, When llamo
  `pg_insert(MyModel).values(...).on_conflict_do_update(...)`, Then funciona
  identico a `from sqlalchemy.dialects.postgresql import insert`.
- **AC-B3**: Given los 5 lambdas, When ejecuto `serverless lint-deps`, Then
  exit 0 (sqlalchemy/alembic/psycopg viven solo en shared.db).

## Verificacion

```bash
python -m compileall -q serverless/lambda/shared/db

# Validar que el alias funciona como esperado
cd serverless/lambda && uv run python -c "
from shared.db import select, func, pg_insert, Session
print('OK:', select, func, pg_insert, Session)
"

python devtools/run.py serverless tests --type=unit --shared
```

## Commit

```text
feat(shared/db): re-exporta subset de SQLAlchemy via __init__

- Re-exporta select, func, Session y pg_insert (postgresql.insert con
  on_conflict_do_update) para que los services importen desde shared.db
  en vez de sqlalchemy directo
- pg_insert es alias del insert de dialects.postgresql; evita shadowing
  con el insert SQL plano que se podria re-exportar en el futuro
- seed_service del lambda db migra sus imports en Fase E
```
