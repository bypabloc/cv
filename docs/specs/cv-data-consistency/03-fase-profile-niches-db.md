# Fase 2 — Persistir profile.niches en la DB

[← Fase 1](02-fase-stats-summary.md) · [Fase 3 →](04-fase-cv-generico.md)

## Objetivo

`profile.niches` es campo Zod obligatorio que hoy no se persiste. Crear la
tabla `profile_niches`, su modelo SQLAlchemy, una migración Alembic nueva
encadenada, y hacer que `_seed_profile` la pueble. Cubre AC-5..AC-8.

## Estado actual

- Modelo `Profile` + `ProfileStats` en
  `serverless/lambda/shared/db/models/profile.py`. NO hay `ProfileNiche`.
- Las otras 9 entidades filtrables tienen su junction `*_niches` en
  `models/junctions.py` (patrón: unión pura, PK compuesta, FK CASCADE).
- `_seed_profile` (`db/cv/seed/seed_from_yaml.py`) inserta `profile` +
  `profile_stats` + 3 traducciones, pero NO lee `p['niches']`.
- Migración actual: `81c2cc51db34_init_unified_schema.py`,
  `down_revision = None` (es la inicial).

## Sub-tareas

### 2.1 — Modelo `ProfileNiche`

En `serverless/lambda/shared/db/models/profile.py`, agregar la clase
siguiendo el patrón EXACTO de `ExperienceNiche` en `junctions.py`:

```python
class ProfileNiche(Base):
    """Unión profile <-> niche. El profile es singleton, pero sus niches
    se persisten igual para que la DB sea fuente de verdad completa.
    """

    __tablename__ = 'profile_niches'

    profile_id: Mapped[str] = mapped_column(
        ForeignKey('profile.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('profile_id', 'niche_id'),)
```

Imports a agregar en `profile.py`: `ForeignKey` ya está; agregar
`PrimaryKeyConstraint` desde `sqlalchemy`.

> Decisión: `ProfileNiche` vive en `profile.py` (junto a `Profile` y
> `ProfileStats`, su entidad) y NO en `junctions.py`. Las otras
> `*_niches` están en `junctions.py` porque sus entidades están
> dispersas; `profile.py` ya es el módulo del profile y sus tablas
> satélite. Coherente con que `ProfileStats` también esté ahí.

### 2.2 — Exportar el modelo

En `serverless/lambda/shared/db/models/__init__.py`:

- Agregar `ProfileNiche` al import desde `.profile`.
- Agregarlo al `__all__`.
- Actualizar el conteo del docstring (de "35 tablas" a "36 tablas").

### 2.3 — Corregir el conteo en base.py

En `serverless/lambda/shared/db/base.py`, el docstring dice "37 tablas"
(ya estaba mal: el conteo real era 35). Tras esta fase son **36**.
Corregir las dos menciones a "36 tablas". Esto cierra de paso la
discrepancia BAJA documental detectada en la auditoría.

### 2.4 — Migración Alembic NUEVA

Generar la migración. NO editar la 81c2cc51db34.

```bash
cd serverless/lambda
# con DATABASE_URL apuntando a un branch Neon de prueba:
.venv/bin/alembic -c shared/db/alembic.ini revision \
  --autogenerate -m "add profile_niches"
```

El archivo generado en `shared/db/alembic/versions/`:

- `down_revision` debe ser `'81c2cc51db34'` (encadenada). Alembic lo
  setea solo al autogenerar; verificar.
- `upgrade()`: `op.create_table('profile_niches', ...)` con las 2
  columnas FK + PK compuesta. Revisar que Alembic capturó el
  `ondelete='CASCADE'`.
- `downgrade()`: `op.drop_table('profile_niches')` — debe revertir
  EXACTAMENTE el `upgrade()` (AC-6).

Revisar el archivo a mano: Alembic autogenera el `create_table` bien
para una junction simple, pero confirmar que no arrastra `op.execute()`
espurios ni toca otras tablas.

### 2.5 — Seed: `_seed_profile` puebla profile_niches

En `db/cv/seed/seed_from_yaml.py`, dentro de `_seed_profile`, tras
insertar `profile` y antes/después de `profile_stats`, agregar la llamada
a `_link_niches` (el helper ya existe, línea ~202):

```python
# tras obtener profile_id y niche_ids
_link_niches(
    cur,
    'profile_niches',
    'profile_id',
    profile_id,
    p.get('niches'),
    niche_ids,
)
```

`_seed_profile` necesita el mapa `niche_ids`. Hoy `_seed_profile(cur)`
no lo recibe. Opciones:

- **Preferida**: pasar `niche_ids` como parámetro a `_seed_profile`
  (`run_seed` ya lo resuelve en la línea 733: `niche_ids =
  _resolve_vocabulary(cur, 'niches', set(_NICHES))`). Cambiar la firma a
  `_seed_profile(cur, niche_ids)` y la llamada en `run_seed`.

Esto mantiene `_seed_profile` consistente con `_seed_experiences` etc.,
que ya reciben `niche_ids`.

## Verificación de la fase

```bash
# 1. Sintaxis de todo el codigo Python tocado
python -m compileall -q serverless/lambda/shared/db db/cv/seed

# 2. El modelo importa y el __all__ es coherente
cd serverless/lambda && .venv/bin/python -c \
  "from shared.db.models import ProfileNiche; print(ProfileNiche.__tablename__)"

# 3. Migración: upgrade + downgrade + upgrade en un branch Neon de prueba
neon branches create --name test-profile-niches --parent main
#   apuntar DATABASE_URL al branch y correr:
.venv/bin/alembic -c shared/db/alembic.ini upgrade head
.venv/bin/alembic -c shared/db/alembic.ini downgrade -1
.venv/bin/alembic -c shared/db/alembic.ini upgrade head
neon branches delete test-profile-niches

# 4. (opcional, si el entorno lo permite) seed en el branch de prueba
#    y verificar 5 filas en profile_niches
```

> Si no hay acceso a Neon en la sesión, la migración igual se verifica
> con `alembic upgrade --sql` (genera el SQL sin aplicar) para confirmar
> que el `CREATE TABLE` es correcto, y el `downgrade` con
> `alembic downgrade --sql`. La aplicación real a dev/prod la hace el
> usuario vía la Lambda `db` (`serverless run --lambda=db`).

## Definition of Done de la fase

- [ ] Clase `ProfileNiche` en `models/profile.py`, patrón junction
      correcto (PK compuesta, FK CASCADE).
- [ ] `ProfileNiche` exportado en `models/__init__.py` + conteo
      actualizado (36).
- [ ] `base.py` docstring corregido a 36 tablas.
- [ ] Migración nueva con `down_revision = '81c2cc51db34'`, `upgrade`
      crea `profile_niches`, `downgrade` la elimina.
- [ ] `_seed_profile` recibe `niche_ids` y puebla `profile_niches` con
      `_link_niches`.
- [ ] `compileall` verde; el modelo importa.
- [ ] Migración aplica `upgrade` + `downgrade` + `upgrade` sin error (o
      `--sql` validado si no hay Neon en la sesión).

[← Fase 1](02-fase-stats-summary.md) · [Fase 3 →](04-fase-cv-generico.md)
