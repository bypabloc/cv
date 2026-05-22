# Commit 4 — Eliminar `db-*` + extender la Lambda `db`

> [Anterior: 02](02-commit-3-resources.md) | [README](README.md) |
> [Siguiente: 04](04-commit-5-docs.md)

## Objetivo

Eliminar los 8 comandos `db-*` del CLI. Las operaciones de base de datos
se hacen invocando la Lambda `db` con `run --lambda=db`.

## Por que

Los `db-*` que invocan la Lambda `db` (`db-migrate`, `db-rollback`,
`db-current`, `db-show-migrations`) son wrappers de `aws lambda invoke`.
Con `run` ya unificado (commit 2), son redundantes:

```bash
# antes
serverless db-migrate --stage=dev
# despues
serverless run --stage=dev --lambda=db --event=events/migrate.json
```

## El hallazgo: paridad incompleta

La Lambda `db` hoy soporta los commands: `migrate`, `downgrade`,
`current`, `show-migrations`, `stamp`. NO soporta `seed` ni `tables`.

Los comandos `db-seed` (corre un `.sql` con psql) y `db-tables` (query
psql de row counts) **no invocan ninguna Lambda** — son psql directo.
Si solo se eliminan, esa funcionalidad se pierde.

Decision tomada: **extender la Lambda `db`** con dos controllers nuevos,
`seed` y `tables`, para que SI se puedan operar con `run --lambda=db`.

`db-shell` (psql interactivo) y `db-branch` (neonctl) se eliminan sin
reemplazo en el CLI — se usan a mano (`psql`, `neonctl`).

## Cambios en la Lambda `db`

`serverless/lambda/services/db/` sigue el patron lambda-controller. El
handler mapea `{command, args}` -> `{operation, action, data}`.

### Controllers nuevos
- `core/controllers/db/seed.py` — clase `Seed(BaseController)`. Carga
  data de prueba. La logica va en el service (no en el controller).
- `core/controllers/db/tables.py` — clase `Tables(BaseController)`.
  Lista tablas + row counts (query a `pg_stat_user_tables`).

### Service
- `core/services/db_service.py` — agregar la logica de `seed` y
  `tables` (usar la sesion SQLAlchemy que ya existe para Alembic).

### Settings
- `core/settings/operations.py` — registrar las acciones nuevas si el
  patron lo requiere.

### Events
- `events/seed.json` — `{"command": "seed"}`
- `events/tables.json` — `{"command": "tables"}`

### Tests
- Un archivo por escenario en `tests/unit/` (modelo + service +
  controller + handler para `seed` y para `tables`), siguiendo el
  estandar de testing de la rule `lambda-controller`.

## Cambios en el CLI

### Eliminar
- `devtools/serverless/database.py` — el modulo entero (los 8
  `cmd_db_*`). O dejarlo vacio si algo mas lo importa (no deberia).

### Modificar
- `devtools/serverless/main.py` — quitar los 8 imports de `database` y
  las 8 entradas del `COMMAND_REGISTRY`.
- `devtools/serverless/flags.py` — quitar los 8 `db-*` de
  `VALID_COMMANDS`, `_COMMAND_SUMMARIES`, `_COMMAND_FLAGS`,
  `DESTRUCTIVE_COMMANDS` (`db-rollback`). Limpiar flags que solo usaban
  los `db-*` si no los usa nadie mas (`branch`, `parent`, `target` —
  verificar).
- `devtools/serverless/help.py` — quitar el grupo `Database (Neon PG)`.

## Criterios de aceptacion

- AC-7: invocar cualquier `db-migrate`/`db-rollback`/`db-shell`/etc. ->
  comando desconocido, lista los validos.
- AC-14: `run --stage=dev --lambda=db --event=events/seed.json` carga
  la data de prueba.
- AC-15: `run --stage=dev --lambda=db --event=events/tables.json`
  devuelve las tablas + row counts.
- AC-16: los tests unit de la Lambda `db` (incluyendo `seed` y
  `tables`) pasan.

## Verificacion

```bash
devtools/.venv/bin/python -m compileall -q devtools/serverless serverless/lambda/services/db
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless help            # sin grupo Database
python devtools/run.py serverless db-migrate 2>&1 # debe fallar: comando desconocido
```

## Definition of Done

- [ ] Los 8 `db-*` eliminados del CLI.
- [ ] La Lambda `db` tiene controllers `seed` y `tables` con tests.
- [ ] `events/seed.json` y `events/tables.json` creados.
- [ ] `serverless help` sin el grupo Database.
- [ ] Tests unit de la Lambda `db` verdes.

## Nota de actualizacion de rules

La rule `.claude/rules/neon-management.md` documenta extensamente los
comandos `db-*`. Su actualizacion va en el commit 5, pero tenerla
presente: toda la seccion "Migrations" y "Comandos via devtools CLI"
cambia a `run --lambda=db`.

---

[Anterior: 02](02-commit-3-resources.md) | [README](README.md) |
[Siguiente: 04](04-commit-5-docs.md)
