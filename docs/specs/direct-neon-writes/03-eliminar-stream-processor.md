# Phase 3: eliminar el lambda stream_processor

> Una vez que tracking_pixel y contact_form escriben a Neon directo,
> stream_processor ya no tiene que hacer. Se borra: lambda + tests +
> codigo shared exclusivo + funciones de repository asociadas.

[Volver al README](README.md)

## Pre-requisito

Las Phases 1 y 2 deben estar commiteadas (los lambdas ya no dependen de la propagacion via stream). NO destruir el lambda en AWS aun — eso es Phase 5 (verify primero).

## Archivos a eliminar

### Lambda

- `serverless/lambda/services/stream_processor/` (toda la carpeta)
  - core/ (handler, controllers, services, models, settings)
  - tests/ (unit + integration)
  - manifest.yaml
  - pyproject.toml
  - uv.lock
  - events/
  - README.md

### Shared (solo usado por stream_processor)

- `serverless/lambda/shared/db/models/stream.py` (modelo `ProcessedStreamEvent`)
- Funciones del repository (`is_event_processed`, `mark_event_processed`):
  - Borrar de `serverless/lambda/shared/db/repository.py`
- En `serverless/lambda/shared/db/models/__init__.py`: borrar re-export de `ProcessedStreamEvent`

### Tests shared

- Tests en `serverless/lambda/shared/tests/` que cubran `stream.py`, `is_event_processed`, `mark_event_processed` — borrar

## Modificar

- `serverless/lambda/shared/db/repository.py`:
  - Borrar `is_event_processed()` y `mark_event_processed()`
  - Mantener `insert_contact()`, `insert_tracking()`, `list_tables()`
  - Agregar `on_conflict='do_nothing'` semantic: ambas insert_* devuelven `bool` (True si inserto, False si skip por conflict)

- `serverless/lambda/services/db/`:
  - Si el lambda `db` tenia un command para query el estado del stream_processor, removerlo
  - Verificar que `list_tables` sigue funcionando

## Verificacion incremental

```bash
# La carpeta del lambda ya no existe:
test ! -d serverless/lambda/services/stream_processor && echo "OK: stream_processor borrado"

# No quedan imports del lambda en el resto del codigo:
rg 'stream_processor|ProcessedStreamEvent|is_event_processed|mark_event_processed' \
  serverless/ devtools/ packages/ apps/ \
  --glob '!docs/specs/direct-neon-writes/**'

# Resto del backend compila:
python -m compileall -q serverless/lambda/services/contact_form/core
python -m compileall -q serverless/lambda/services/tracking_pixel/core
python -m compileall -q serverless/lambda/services/db/core
python -m compileall -q serverless/lambda/services/cv/core
python -m compileall -q serverless/lambda/shared

# Tests del backend pasan:
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=db
```

## Done cuando

- [ ] Carpeta `services/stream_processor/` no existe
- [ ] `rg` confirma 0 referencias a stream_processor en el codigo (salvo el spec)
- [ ] `compileall` verde para los 3 lambdas restantes + shared
- [ ] Suite unit + integration de los 3 lambdas verde
- [ ] No se elimina aun el lambda en AWS (Phase 5)
