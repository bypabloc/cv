# 00 — Fase 0: migrar `db/cv/` al Lambda `db` + seeds en su arbol

[README](README.md) | [Siguiente: 01 Contexto ->](01-contexto-y-decision.md)

## Objetivo

Que el Lambda `db` (`serverless/lambda/services/db/`) sea el UNICO con acceso
a los seeds del CV y a los modelos SQLAlchemy. Migrar el seeder legacy
`db/cv/seed/seed_from_yaml.py` al `core/` del Lambda `db` y copiar los datos
del CV (YAML + `profile.ts`) dentro del arbol del Lambda para que sea
autocontenido (los seeds se vendorizan al zip de deploy).

Esta fase NO depende de las fases A/B/C/D. Es la primera porque puebla la DB
que la Fase C necesita.

## Estado actual

- `db/cv/` es un arbol legacy: modelos SQLAlchemy duplicados (ya unificados en
  `shared/db/models/`), alembic propio (ya unificado), `ddl/`, y
  `seed/seed_from_yaml.py` — el seeder que SI funciona y NO esta migrado.
- El Lambda `db` tiene un controller `db/seed.py` cuyo service `run_seed()`
  hoy devuelve `{'seeded': False, 'reason': 'no hay seed disponible...'}`.
- Los 71 YAML del CV + `profile.ts` viven en `packages/content/src/data/`.

## Que se hace

### 1. Copiar los datos del CV al arbol del Lambda `db`

Crear `serverless/lambda/services/db/seeds/data/` con copia de:
- los 71 `*.yaml` de `packages/content/src/data/**` (todas las subcarpetas:
  awards, certificates, education, experiences, languages, projects,
  publications, references, skills).
- `packages/content/src/data/profile.ts` (el profile vive en TS).

> Los YAML siguen siendo fuente para las apps Astro en `packages/content`
> HASTA la Fase D. La copia en `seeds/data/` es la fuente del seeder del
> Lambda. Tras la Fase D, `packages/content/src/data/` queda deprecado (su
> eliminacion es trabajo posterior, fuera de scope — ver TODO de la Fase D).
> Durante la vida del plan ambas copias coexisten; son identicas.

### 2. Migrar el seeder a `core/services/`

`db/cv/seed/seed_from_yaml.py` -> `services/db/core/services/seed_service.py`:
- La logica de insercion idempotente (`_upsert_returning_id`,
  `_set_translation`, `_link_niches`, los `_seed_*`, `run_seed`) se mueve tal
  cual — es logica probada.
- El path de los datos cambia: de `packages/content/src/data` a
  `seeds/data/` relativo a la raiz del Lambda (resuelto con `Path(__file__)`).
- Usa `psycopg` directo (igual que hoy) — `psycopg` ya llega por el cierre de
  `shared/`. El seeder NO necesita SQLAlchemy.
- La connection string se resuelve con `shared.db.url` (la misma
  `DATABASE_URL` que ya usa el Lambda `db`), NO con `CV_DATABASE_URL`.

### 3. Conectar el controller `db/seed`

`services/db/core/services/db_service.py` -> `run_seed()` deja de devolver
"no disponible": delega en `seed_service.run_seed()`. El controller
`db/seed.py` no cambia (ya delega en `db_service.run_seed`).

### 4. `pyproject.toml` del Lambda `db`

Agregar `pyyaml` a `[project.dependencies]` — el seeder parsea YAML y
`pyyaml` no llega por el cierre de `shared/`. `psycopg` ya esta (via
`shared.db`).

### 5. Tests

Migrar `db/cv/tests/test_seed.py` y `test_load_profile.py` a
`services/db/tests/unit/` adaptados al estandar lambda-controller (un archivo
por escenario). Cubren: carga de YAML, parseo de `profile.ts`, idempotencia
del upsert, conteos por tabla.

### 6. Eliminar `db/cv/`

El arbol `db/cv/` queda obsoleto por completo: modelos, alembic y DDL ya estan
unificados en `shared/db/`; el seeder y sus tests se migraron. Se elimina
`db/cv/` entero en el ultimo commit de esta fase.

> El `db/` raiz queda vacio tras esto. Si no hay nada mas en `db/`, eliminar
> tambien `db/`. Verificar con `eza db/` antes.

## Verificacion de la fase

```bash
python -m compileall -q serverless/lambda/services/db/core
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless lint-deps --lambda=db

# poblar la DB dev (requiere AWS): invoca el Lambda db con el event seed
python devtools/run.py serverless deploy --lambda=db --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/tables.json --aws-profile=tfs-dev
```

Criterio: suite unit verde; tras el `seed`, `tables` reporta `rows > 0` en
las tablas del CV (`profile`, `experiences`, `projects`, `translations`,
`niches`, ...). El seed es idempotente: correrlo 2 veces deja el mismo estado.

## Done

- [ ] `services/db/seeds/data/` con los 71 YAML + `profile.ts`
- [ ] `seed_service.py` en `core/services/` (seeder migrado, path local)
- [ ] `db_service.run_seed()` delega en `seed_service.run_seed()`
- [ ] `pyproject.toml` del Lambda `db` declara `pyyaml`
- [ ] tests del seed migrados a `services/db/tests/unit/`, verdes
- [ ] `serverless run --lambda=db --event=events/seed.json` puebla la DB dev
- [ ] `db/cv/` (y `db/` si queda vacio) eliminado
- [ ] `serverless lint-deps --lambda=db` sin deps faltantes

Continua en [01-contexto-y-decision.md](01-contexto-y-decision.md).
