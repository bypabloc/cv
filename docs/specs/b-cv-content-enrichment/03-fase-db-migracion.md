# Fase 2 — DB: migración Alembic para country y metrics_estimated

[← Fase 1](02-fase-schema-zod.md) · [Fase 3 →](04-fase-experiencias.md)

## Objetivo

Propagar los campos nuevos del CV (`country`, `metricsEstimated`) a la
base PostgreSQL: migración Alembic nueva + modelos SQLAlchemy + seed.
Cubre AC-3b, AC-3c, AC-3d.

## Por qué esta fase existe

El usuario pidió que la data actualizada esté también "en las
migraciones". Aclaración importante:

- `serverless/migrations/_archive/*.sql` es el runner SQL viejo,
  **archivado, no se aplica más** (regla `neon-management.md`). Esos
  `.sql` modelan solo tablas del visitante (tracking/contacts), NO el
  CV. **NO se tocan.**
- El schema real del CV lo gestiona **Alembic** en
  `serverless/lambda/shared/db/alembic/versions/`. La forma correcta de
  "que esté en las migraciones" es una **migración Alembic nueva**.

Esta fase es el equivalente del plan A cuando agregó `profile_niches`:
modelo + migración encadenada + seed.

## Estado actual

- `serverless/lambda/shared/db/models/experience.py` — modelo
  `Experience`: `slug`, `company`, `company_url`, `start_ym`, `end_ym`,
  `seniority`. Sin `country` ni `metrics_estimated`.
- `serverless/lambda/shared/db/models/project.py` — modelo `Project`:
  `slug`, `name`, `url`, `repo`, `status`, `project_type`,
  `is_confidential`. Sin `metrics_estimated`.
- Última migración Alembic: `79bacfd3c091_add_profile_niches.py` (del
  plan A). La migración de esta fase encadena a esa
  (`down_revision = '79bacfd3c091'`).

## Sub-tareas

### 2.1 — Columnas en el modelo `Experience`

En `models/experience.py`, agregar tras `company_url`:

```python
company_url: Mapped[str | None] = mapped_column(String(500))
country: Mapped[str] = mapped_column(String(120), nullable=False)
...
metrics_estimated: Mapped[bool] = mapped_column(
    Boolean, nullable=False, default=False
)
```

`Boolean` hay que importarlo de `sqlalchemy` (hoy `experience.py` no lo
importa).

> `country` es `NOT NULL`. La migración debe crear la columna con un
> `server_default` temporal (ej. `''`) para las filas existentes y luego
> el seed la rellena — o, si la DB está vacía en dev, crearla NOT NULL
> directo. Ver 2.4.

### 2.2 — Columna en el modelo `Project`

En `models/project.py`, agregar tras `is_confidential`:

```python
metrics_estimated: Mapped[bool] = mapped_column(
    Boolean, nullable=False, default=False
)
```

`Boolean` ya está importado en `project.py`.

### 2.3 — Migración Alembic nueva

Crear `serverless/lambda/shared/db/alembic/versions/<rev>_add_cv_country_metrics.py`
siguiendo el patrón de `79bacfd3c091`:

- `down_revision = '79bacfd3c091'`.
- `upgrade()`:
  ```python
  op.add_column('experiences', sa.Column(
      'country', sa.String(length=120),
      nullable=False, server_default=''))
  op.add_column('experiences', sa.Column(
      'metrics_estimated', sa.Boolean(),
      nullable=False, server_default=sa.false()))
  op.add_column('projects', sa.Column(
      'metrics_estimated', sa.Boolean(),
      nullable=False, server_default=sa.false()))
  # quitar el server_default temporal de country tras crear la columna
  op.alter_column('experiences', 'country', server_default=None)
  ```
- `downgrade()`:
  ```python
  op.drop_column('projects', 'metrics_estimated')
  op.drop_column('experiences', 'metrics_estimated')
  op.drop_column('experiences', 'country')
  ```

> El `server_default=''` temporal en `country` permite que el
> `ADD COLUMN NOT NULL` no falle si la tabla ya tiene filas. El
> `alter_column ... server_default=None` lo retira: de ahí en más el
> valor lo provee el seed/la app. `metrics_estimated` mantiene
> `server_default=false` (es un default real, no temporal).

### 2.4 — Seed: insertar los campos nuevos

En `db/cv/seed/seed_from_yaml.py`:

- `_seed_experiences`: el `_upsert_returning_id` de cada experiencia debe
  incluir `'country': data['country']` y
  `'metrics_estimated': data.get('metricsEstimated', False)`.
- `_seed_projects`: incluir
  `'metrics_estimated': data.get('metricsEstimated', False)`.

> Mapeo de nombres: el YAML/Zod usa `metricsEstimated` (camelCase); la
> columna DB es `metrics_estimated` (snake_case). El seed traduce.

## Verificación de la fase

```bash
python -m compileall -q serverless/lambda/shared/db db/cv/seed

# el modelo importa y la tabla tiene las columnas nuevas
cd serverless/lambda && PYTHONPATH=$(pwd) \
  services/db/.venv/bin/python -c "
from shared.db.base import Base
from shared.db import models  # noqa
exp = Base.metadata.tables['experiences']
assert 'country' in exp.columns and 'metrics_estimated' in exp.columns
prj = Base.metadata.tables['projects']
assert 'metrics_estimated' in prj.columns
print('columnas OK')
"

# cadena Alembic + SQL del upgrade/downgrade (offline)
#   (mismo procedimiento que el plan A — ver su 03-fase-profile-niches-db)

# tests del backend
python devtools/run.py serverless tests --type=unit --shared
```

> Igual que en el plan A: si no hay Neon en la sesión, la migración se
> valida con `alembic upgrade --sql` + `downgrade --sql`. La aplicación
> real a dev/prod la hace el usuario con la Lambda `db`.

## Definition of Done de la fase

- [ ] `Experience` tiene `country` (NOT NULL) y `metrics_estimated`.
- [ ] `Project` tiene `metrics_estimated`.
- [ ] Migración Alembic nueva encadenada a `79bacfd3c091`; `upgrade`
      agrega las 3 columnas, `downgrade` las quita.
- [ ] `_seed_experiences` y `_seed_projects` insertan los campos nuevos.
- [ ] `compileall` verde; el modelo importa; tests `shared` verdes.
- [ ] `serverless/migrations/_archive/*.sql` SIN cambios.

[← Fase 1](02-fase-schema-zod.md) · [Fase 3 →](04-fase-experiencias.md)
