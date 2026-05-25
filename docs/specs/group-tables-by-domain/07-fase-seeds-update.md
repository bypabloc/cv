# 07 — Fase 3: Seeds + seed_service

[README](README.md) | [06-fase-migracion](06-fase-migracion-alembic.md) |
**07-fase-seeds** | [08-fase-lambdas](08-fase-lambdas-update.md)

## Objetivo

Actualizar el seeder (`services/db/core/services/seed_service.py`) para:

1. Convertir fechas YAML `YYYY-MM` a tipo `date` Python.
2. Generar slugs automaticamente para `cv_skills` y `tax_tech_tags`.
3. Usar `cv_endorsements` + `entity_type='endorsement'` (en vez de
   `references`/`'reference'`).
4. Idempotencia preservada (re-correr el seed no duplica filas).

## Pre-requisitos

- Fase 2 ejecutada en branch Neon de prueba (DB ya con tablas
  renombradas + columnas DATE + slugs columns vacios + ENUM con
  `endorsement`).

## Pasos

### Paso 3.1 — Helper `_parse_ym` y `_to_slug`

Archivo nuevo: `serverless/lambda/shared/db/seed_helpers.py`

```python
"""Helpers compartidos para el seeder del CV."""
from __future__ import annotations
from datetime import date
import re


def _parse_ym(raw: str | None) -> date | None:
    """
    YAML '2024-01' -> date(2024, 1, 1)
    YAML '2024-01-15' -> date(2024, 1, 15)
    YAML '2024' -> date(2024, 1, 1)
    YAML None -> None
    """
    if raw is None:
        return None
    parts = raw.split('-')
    if not (1 <= len(parts) <= 3):
        raise ValueError(f"Fecha invalida: {raw!r}")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) >= 2 else 1
    day = int(parts[2]) if len(parts) >= 3 else 1
    return date(year, month, day)


_SLUG_NON_ALNUM = re.compile(r'[^a-z0-9]+')
_SLUG_EDGES = re.compile(r'(^-+|-+$)')


def _to_slug(name: str) -> str:
    """
    'Python' -> 'python'
    'Node.js' -> 'node-js'
    'AWS Lambda' -> 'aws-lambda'
    'C#' -> 'c'
    """
    lowered = name.lower()
    hyphenated = _SLUG_NON_ALNUM.sub('-', lowered)
    return _SLUG_EDGES.sub('', hyphenated)
```

Verificar: `pytest serverless/lambda/shared/tests/db/test_seed_helpers.py`

### Paso 3.2 — Actualizar `seed_service.py`

Cambios:

#### a) Convertir fechas al persistir

```python
# antes
exp_data = {
    'slug': yaml_data['slug'],
    'start_ym': yaml_data['start'],  # str '2022-08'
    'end_ym':   yaml_data.get('end'), # str '2024-12' o None
    ...
}

# despues
from shared.db.seed_helpers import _parse_ym
exp_data = {
    'slug': yaml_data['slug'],
    'started_on': _parse_ym(yaml_data['start']),   # date(2022, 8, 1)
    'ended_on':   _parse_ym(yaml_data.get('end')), # date(2024, 12, 1) o None
    ...
}
```

Aplicar el mismo patron a `awards`, `cv_education_entries`,
`cv_certificates` (issued_on ya era date pero unificar el path), y
`cv_publications`.

#### b) Generar slugs

```python
from shared.db.seed_helpers import _to_slug

def _ensure_skill(session: Session, name: str) -> UUID:
    slug = _to_slug(name)
    stmt = pg_insert(Skill).values(slug=slug, name=name).on_conflict_do_nothing(
        index_elements=['slug']
    ).returning(Skill.id)
    result = session.execute(stmt).scalar_one_or_none()
    if result:
        return result
    # ya existia: query por slug
    return session.execute(select(Skill.id).where(Skill.slug == slug)).scalar_one()
```

Misma logica para `TechTag`.

#### c) Renombrar references -> endorsements

```python
# antes
def _load_references(session: Session) -> None:
    for path in _iter_yaml('references'):
        ref_data = _load_yaml(path)
        ref = _upsert_reference(session, ref_data)
        _upsert_translations(session, 'reference', ref.id, ref_data, ['relation'])

# despues
def _load_endorsements(session: Session) -> None:
    for path in _iter_yaml('endorsements'):
        end_data = _load_yaml(path)
        end = _upsert_endorsement(session, end_data)
        _upsert_translations(session, 'endorsement', end.id, end_data, ['relation'])
```

NOTA: el directorio fisico de YAMLs queda como
`services/db/core/seeds/data/references/` (no se renombra). El seeder
lo expone como `_load_endorsements` por consistencia con el modelo.
**Alternativa**: renombrar el directorio a `endorsements/`. Decision:
**SI renombrar** para coherencia. Update path en grep del seeder.

#### d) Mapeo de `entity_type` en translations + niche_priorities

```python
# antes
_ENTITY_TYPE_MAP = {
    Profile: 'profile',
    Experience: 'experience',
    ...
    Reference: 'reference',
    SkillCategory: 'skill_category',
}

# despues
_ENTITY_TYPE_MAP = {
    Profile: 'profile',
    Experience: 'experience',
    ...
    Endorsement: 'endorsement',       # ENUM tiene 'endorsement' tras la migracion
    SkillCategory: 'skill_category',
}
```

### Paso 3.3 — Renombrar directorio de YAMLs

```bash
git mv serverless/lambda/services/db/core/seeds/data/references \
       serverless/lambda/services/db/core/seeds/data/endorsements
```

Los 10 YAMLs (`alan-vergara.yaml`, `alejandra-medina.yaml`, ...)
conservan nombre y contenido.

### Paso 3.4 — Verificacion incremental

```bash
# 1. unit tests del helper
pytest serverless/lambda/shared/tests/db/test_seed_helpers.py

# 2. unit tests del seed_service (mockeado)
serverless tests --type=unit --lambda=db

# 3. integration: seed contra branch Neon de prueba
export DATABASE_URL=<branch-de-prueba>
serverless run --stage=local --lambda=db --event=events/seed.json

# 4. verificacion DB real (CRITICA):
psql "$DATABASE_URL" <<SQL
-- AC-2: fechas son DATE
SELECT pg_typeof(started_on) FROM cv_experiences LIMIT 1;
-- esperado: date

-- AC-2: valor convertido
SELECT started_on FROM cv_experiences WHERE slug = 'destacame-architect';
-- esperado: 2022-08-01 (no '2022-08')

-- AC-4: slugs en skills
SELECT slug, name FROM cv_skills WHERE name = 'Python';
-- esperado: ('python', 'Python')

-- AC-9: endorsements no references
SELECT count(*) FROM cv_endorsements;
-- esperado: 10 (10 YAMLs)

-- AC-9: ENUM value
SELECT count(*) FROM i18n_translations WHERE entity_type = 'endorsement';
-- esperado: > 0

-- Idempotencia: re-correr el seed no duplica
SELECT count(*) AS row_count_before FROM cv_experiences;
SQL
serverless run --stage=local --lambda=db --event=events/seed.json
psql "$DATABASE_URL" -c "SELECT count(*) FROM cv_experiences"
# esperado: identico a row_count_before
```

## Definition of done (Fase 3)

- [ ] `seed_helpers.py` creado con `_parse_ym` + `_to_slug` + tests verdes
- [ ] `seed_service.py` actualizado: usa helpers, persiste fechas como
  `date`, genera slugs, usa `Endorsement` + `entity_type='endorsement'`
- [ ] Directorio `seeds/data/references/` renombrado a `endorsements/`
- [ ] Seed corre 2 veces idempotente (row count constante)
- [ ] Verificacion DB real: fechas son `date`, slugs no nulos,
  `cv_endorsements` poblado, `i18n_translations` tiene
  `entity_type='endorsement'`
- [ ] Integration tests del lambda `db` verdes:
  `serverless tests --type=integration --lambda=db`

## Riesgos

- **YAML con formato inesperado**: si algun YAML tiene `start:
  "2024-08-15"` (full date), `_parse_ym` debe manejarlo (ya cubierto
  por test).
- **Skills duplicados por casing**: `Python` y `python` generan el
  mismo slug `python`; `ON CONFLICT DO NOTHING` lo absorbe. Pero
  `python` y `Python` registrados como skills separados antes de la
  migracion quedan como una sola fila — verificar manualmente en dev
  si pasa.
- **C#, .NET y otros tech names con caracteres especiales**: el slug
  los pierde (`c-net` para `.NET`). Verificar si causa colision con
  otro skill llamado `C Net`. Si pasa, agregar overrides explicitos
  en un dict `SLUG_OVERRIDES = {'C#': 'c-sharp', '.NET': 'dotnet'}`.
