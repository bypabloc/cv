# Phase 4: eliminar recursos DDB, DLQ, migration drop, provisioner cleanup

> Borrar el catalogo de recursos DDB `contacts` y `tracking`, la DLQ
> SQS, la migration Alembic que dropea `processed_stream_events`, y el
> codigo del provisioner que cableaba el trigger `on-table-changes`.
> Phase 4 es PURO codigo — los recursos AWS reales se eliminan en
> Phase 5 (tras verify).

[Volver al README](README.md)

## Pre-requisito

Phase 3 commiteada: stream_processor ya no existe en el repo.

## 4.a — Migration Alembic: drop processed_stream_events

### Crear

- `serverless/lambda/shared/db/alembic/versions/<rev>_drop_processed_stream_events.py`
  - `upgrade()`: `op.drop_table('processed_stream_events')`
  - `downgrade()`: recrear la tabla (CREATE TABLE con la definicion original) por consistencia, pero no se va a usar — la tabla esta vacia

### Verificacion local

Probar en un branch Neon de prueba antes de aplicar a dev:

```bash
neon branches create --name test-drop-pse --parent main
DATABASE_URL=<branch-url> .venv/bin/alembic -c shared/db/alembic.ini upgrade head
DATABASE_URL=<branch-url> .venv/bin/alembic -c shared/db/alembic.ini downgrade -1
DATABASE_URL=<branch-url> .venv/bin/alembic -c shared/db/alembic.ini upgrade head
neon branches delete test-drop-pse
```

## 4.b — Borrar recursos del catalogo

### Borrar archivos

- `serverless/lambda/resources/dynamodb/contacts.yaml`
- `serverless/lambda/resources/dynamodb/tracking.yaml`
- `serverless/lambda/resources/sqs/stream-processor-dlq.yaml`

### Modificar el provisioner

`devtools/serverless/provisioner.py`:

- En `_TABLES` dict (linea ~55): borrar entradas `contacts` y `tracking`. Quedan solo `cache`, `rate-limit-rules`, `rate-limit-buckets`.
- En `_VALID_TRIGGERS` (linea ~47): borrar `'on-table-changes'`. Queda `('direct', 'http')`.
- Borrar la funcion `_wire_table_changes_trigger` y sus llamadas en `_wire_trigger`.
- Borrar la funcion `_table_changes_trigger_iam` (si existe).
- Borrar resolvers de stream-arn (`/portfolio/{stage}/dynamodb/{table}/stream-arn`) que solo se usaban para `on-table-changes`.

### Tests del provisioner

- Borrar `devtools/tests/serverless/test_provisioner_table_changes_*.py`
- Verificar que tests existentes siguen pasando: `python devtools/run.py test_runner --module=devtools --type=unit`

## Verificacion incremental

```bash
# Resources YAML borrados:
test ! -f serverless/lambda/resources/dynamodb/contacts.yaml && echo "OK: contacts.yaml borrado"
test ! -f serverless/lambda/resources/dynamodb/tracking.yaml && echo "OK: tracking.yaml borrado"
test ! -f serverless/lambda/resources/sqs/stream-processor-dlq.yaml && echo "OK: dlq.yaml borrado"

# Provisioner sin referencias a on-table-changes:
rg 'on-table-changes|_wire_table_changes_trigger' devtools/

# Migration existe:
ls serverless/lambda/shared/db/alembic/versions/ | grep drop_processed_stream_events

# Devtools tests pasan:
python devtools/run.py test_runner --module=devtools --type=unit
```

## Done cuando

- [ ] 3 YAMLs de resources borrados
- [ ] Provisioner sin `on-table-changes` ni `_wire_table_changes_trigger`
- [ ] Migration Alembic creada y probada en branch Neon
- [ ] `python devtools/run.py test_runner --module=devtools --type=unit` verde
- [ ] No se elimina aun en AWS — eso es Phase 5
