# Plan: direct-neon-writes

> Eliminar el flujo `tracking_pixel/contact_form -> DDB -> Stream -> stream_processor -> Neon`
> y reemplazarlo por `tracking_pixel/contact_form -> Neon` directo. Borrar
> `stream_processor`, las tablas DDB `contacts` y `tracking`, la DLQ SQS,
> la tabla Neon `processed_stream_events`, el codigo del provisioner que
> cablea `on-table-changes` triggers, y los tests asociados.

| Capitulo | Cuando leer |
|---|---|
| [README (este archivo)](README.md) | Contexto, decisiones, AC, diagramas, DoD |
| [01-refactor-tracking-pixel.md](01-refactor-tracking-pixel.md) | Refactor del lambda tracking_pixel |
| [02-refactor-contact-form.md](02-refactor-contact-form.md) | Refactor del lambda contact_form |
| [03-eliminar-stream-processor.md](03-eliminar-stream-processor.md) | Borrar el lambda stream_processor |
| [04-eliminar-recursos-ddb.md](04-eliminar-recursos-ddb.md) | Borrar tablas DDB, DLQ, migration drop processed_stream_events, provisioner cleanup |
| [05-commits-y-worktrees.md](05-commits-y-worktrees.md) | Listado de commits + paralelizacion |
| [06-verificacion-e2e.md](06-verificacion-e2e.md) | Bateria E2E iterativa (gate del PR) |

## 1. Contexto

El backend del portfolio implementa un patron fintech sobre-ingenierizado para el volumen real (~15k tracking events/mes, ~200 contactos/mes):

```text
Browser -> API GW -> tracking_pixel -> DDB.tracking -> Stream -> stream_processor -> Neon
                  -> contact_form   -> DDB.contacts -> Stream ->         |          -> SES
                                                                  on retry exhaust
                                                                      SQS DLQ
```

El stream-processor introdujo un bug (eventID vs SequenceNumber en `batchItemFailures`) que costo ~horas de debug y dejo a Neon dev con 0 filas hasta arreglarlo (memoria `Fix stream_processor: SequenceNumber + DLQ + MaxRetry`, 2026-05-24). Esa misma sesion concluyo: la arquitectura es sobre-ingenieria para un CV.

## 2. Solucion propuesta

```text
Browser -> API GW -> tracking_pixel -> Neon.tracking_events (INSERT ON CONFLICT)
                  -> contact_form   -> Neon.contacts + SES
```

Los lambdas HTTP escriben directo a Neon en la misma invocacion. Se conservan las tablas DDB `cache`, `rate-limit-rules`, `rate-limit-buckets` (sub-ms reads, uso legitimo).

### Decisiones clave (no reabribles)

1. **One-cut, sin dual-write transitorio.** El refactor reemplaza el write a DDB por write a Neon. Rollback = redeploy del commit anterior por env. Aceptable porque dev -> stage -> prod permiten verificar antes de promover.

2. **Idempotencia movida del stream a la API**:
   - `tracking_events_default`: PK natural `(session_id, event_id)`. `INSERT ... ON CONFLICT DO NOTHING`.
   - `contacts`: la API genera `id = uuid7()`. Frontend opcionalmente manda `idempotency_key` (UUID v7) que se usa como `contacts.id`. `INSERT ... ON CONFLICT (id) DO NOTHING`.

3. **Drop de `processed_stream_events`**: ya no hay streams. Migration Alembic nueva.

4. **Schema de `tracking_events` y `contacts` se mantiene**: solo cambia el actor que escribe. No se tocan columnas, indices ni FKs.

5. **shared.db.repository.{insert_contact,insert_tracking}** se reusan. Cambiamos su firma para aceptar `on_conflict='do_nothing'` y devolver bool indicando si fue una insercion real (para metricas / observabilidad).

6. **Borrar `is_event_processed`/`mark_event_processed`** del repository (solo stream_processor las usaba).

7. **Orden de deploy**: dev (verificar end-to-end) -> stage -> prod. Cada deploy con `serverless deploy --lambda=<X> --stage=<env>`. Cleanup de recursos DDB de cada env tras verificar el lambda nuevo.

## 3. Criterios de aceptacion (BDD/EARS)

- **AC-1**: Given un POST a `/track` con payload valido (`session_id`, `event_id`, `event_type_id`), When tracking_pixel lo procesa, Then aparece como fila en `tracking_events_default` en <500ms.
- **AC-2**: Given un POST a `/contact` con Turnstile valido, When contact_form lo procesa, Then aparece fila en `contacts` y se envia email via SES.
- **AC-3**: Given un POST repetido con el mismo `(session_id, event_id)` para tracking o el mismo `idempotency_key` para contact, When el lambda lo procesa, Then la 2a llamada retorna 200 sin crear duplicado.
- **AC-4**: WHEN `rg 'stream_processor|ProcessedStreamEvent|_wire_table_changes_trigger|on-table-changes'` corre sobre el repo (excluyendo este spec), THEN retorna 0 matches.
- **AC-5**: WHEN se ejecuta `aws dynamodb describe-table --table-name portfolio-{contacts,tracking}-{env}`, THEN retorna `ResourceNotFoundException` en dev/stage/prod.
- **AC-6**: Given Neon dev tiene 9 filas en `tracking_events_default`, When mergea el PR a dev, Then las 9 filas permanecen intactas y se siguen agregando nuevas.
- **AC-7**: WHEN `aws lambda get-function --function-name portfolio-stream-processor-{env}` corre, THEN retorna `ResourceNotFoundException`.

## 4. Diagrama de flujo (antes / despues)

### Antes

```text
[Browser]
   |
   v
[API GW] --POST /track---> [tracking_pixel]
   |                          |
   |                          v (PutItem)
   |                       [DDB.tracking]
   |                          | (Stream INSERT)
   |                          v
   |                       [stream_processor] --INSERT--> [Neon.tracking_events]
   |                          | (on retry exhaust)
   |                          v
   |                       [SQS DLQ]
   |
   +--POST /contact-> [contact_form]
                         |
                         v (PutItem)
                      [DDB.contacts]
                         | (Stream INSERT)
                         v
                      [stream_processor] --INSERT--> [Neon.contacts]
                                                          |
                                                          v
                                                       [SES SendEmail]
```

### Despues

```text
[Browser]
   |
   v
[API GW] --POST /track---> [tracking_pixel] --INSERT ON CONFLICT-> [Neon.tracking_events]
   |
   +--POST /contact-> [contact_form] --INSERT ON CONFLICT-> [Neon.contacts]
                            |
                            v
                         [SES SendEmail]
```

## 5. Diagrama ER

N/A para `tracking_events` y `contacts` — su schema no cambia.

Para `processed_stream_events` la migration es DROP TABLE (sin columnas nuevas). Detalle en [04-eliminar-recursos-ddb.md](04-eliminar-recursos-ddb.md).

## 6. Validacion / Definition of Done

### Pre-implementacion

- [ ] Spec commiteada en `docs/specs/direct-neon-writes/`
- [ ] Branch `feature/direct-neon-writes` desde `dev`
- [ ] `pytest serverless/lambda/services/tracking_pixel/tests/unit` verde
- [ ] `pytest serverless/lambda/services/contact_form/tests/unit` verde

### Definition of Done

- [ ] AC-1 a AC-7 verificables end-to-end en dev (luego stage, luego prod)
- [ ] `serverless tests --type=unit --lambda=tracking_pixel` verde
- [ ] `serverless tests --type=unit --lambda=contact_form` verde
- [ ] `serverless tests --type=integration` para los 2 lambdas verde
- [ ] `pnpm exec biome check .` sin errores
- [ ] `serverless deploy --lambda=tracking_pixel --stage=dev` exitoso
- [ ] `serverless deploy --lambda=contact_form --stage=dev` exitoso
- [ ] `serverless run --lambda=db --event=events/migrate.json --stage=dev` corre la migration
- [ ] DDB tables `portfolio-{contacts,tracking}-dev` borradas
- [ ] SQS `portfolio-stream-processor-dlq-dev` borrada
- [ ] Lambda `portfolio-stream-processor-dev` borrada
- [ ] SSM params huerfanos borrados (`/portfolio/dev/dynamodb/{contacts,tracking}/*`, `/portfolio/dev/sqs/stream-processor-dlq/*`)
- [ ] Mismos pasos en stage + prod
- [ ] Bateria de [06-verificacion-e2e.md](06-verificacion-e2e.md) verde en los 3 envs
- [ ] Carpeta `docs/specs/direct-neon-writes/` eliminada en el ultimo commit
- [ ] PR `feature/direct-neon-writes -> dev` mergeado con merge commit

## 7. Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| Neon cold start (~1-2s) tras pausa de 5+ dias | Tracking pixel usa `sendBeacon` (invisible). Contact form tolera 2s |
| Pico de trafico viral con Neon Free (191h compute/mes) | A 0.006 events/seg es practicamente nada — quedarian 191h libres |
| Perdida del audit trail de DDB Streams | Powertools logger estructurado captura el payload completo en CloudWatch |
| Deploy a prod con codigo no probado en stage | El plan deploya dev -> stage -> prod con verify E2E en cada uno |
| Rollback de prod si Neon falla post-deploy | `serverless deploy --lambda=<X> --stage=prod` del commit anterior |

## 8. Referencias cruzadas

- Plan-format rule: [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md)
- Lambda-controller (formato): [.claude/rules/lambda-controller.md](../../../.claude/rules/lambda-controller.md)
- Neon management (migrations Alembic): [.claude/rules/neon-management.md](../../../.claude/rules/neon-management.md)
- Memoria del bug que motivo este plan: engram `obs-9fe27dec5794e7d7` ("Fix stream_processor: SequenceNumber + DLQ + MaxRetry")
