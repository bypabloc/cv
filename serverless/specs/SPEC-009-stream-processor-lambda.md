# SPEC-009: Lambda `stream_processor` (Streams -> Neon) + DLQ

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/stream_processor/`,
`serverless/template.yaml`
**Dependencias**: SPEC-005, SPEC-006, SPEC-008
**Paralelizable con**: ninguna (depende de las 2 Lambdas hot path + Neon)

## 1. Contexto

Procesa eventos de DynamoDB Streams (cuando `contacts` o `tracking`
reciben INSERT/MODIFY/REMOVE) y replica el cambio a Neon PostgreSQL.
Esto permite que Dynamo siga siendo source of truth del hot path
(rapido, free tier) mientras Neon recibe los datos para queries
analiticas SQL.

### Hallazgos de exploracion

- Flujo completo en `serverless/ARCHITECTURE.md` seccion 4.5
- Idempotency via `processed_stream_events` (PK=event_id)
- Decision: ReservedConcurrentExecutions=2 para no saturar conn pool Neon

## 2. Solucion propuesta

Crear `serverless/src/stream_processor/` con 7 archivos + DLQ SQS:

```text
stream_processor/
├── __init__.py
├── handler.py             # event['Records'] -> batch process
├── service.py             # orquesta transform + upsert + idempotency
├── transformers.py        # DynamoDB Item dict -> PG row mapping (contacts y tracking)
├── pg_writer.py           # psycopg3 conn cached + UPSERT prepared
├── retries.py             # DLQ classification + idempotency check
├── schemas.py
└── requirements.txt
```

### Decisiones clave

- **Decision 1: Batch processing con Powertools `BatchProcessor`** —
  procesa hasta 100 records por invocacion. Errores parciales se
  reportan al Stream para retry (Lambda Powertools maneja esto).
- **Decision 2: psycopg3 connection cached en module scope** —
  conexion inicializa ~150-250ms (TLS handshake), reusada entre
  invocaciones warm baja a ~5ms por write.
- **Decision 3: UPSERT con ON CONFLICT (stream_event_id) DO NOTHING** —
  idempotente a nivel SQL. Si event_id ya fue procesado, no se hace
  trabajo. Backup del idempotency en `processed_stream_events`.
- **Decision 4: Sin retry manual de items individuales** — Lambda
  recibe el batch; si falla un item, todo el batch va a DLQ. Razon:
  simplicidad y robustez. Trade-off: 1 item malo retrasa 99 buenos.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given INSERT en `contacts` (Dynamo), When stream_processor
  procesa el evento, Then existe row en PG `contacts` con mismos campos
  + `stream_event_id` matching `eventID`
- **AC-2**: Given INSERT en `tracking`, When procesado, Then row en PG
  `tracking_events` en la particion correcta del mes
- **AC-3**: Given mismo evento procesado 2 veces (retry del Stream),
  When 2do procesamiento, Then NO se duplica row en PG (idempotency
  via ON CONFLICT + processed_stream_events)
- **AC-4**: Given Lambda falla 3 veces para mismo batch, When AWS
  decide enviarlo a DLQ, Then mensaje aparece en SQS `StreamProcessorDLQ`
- **AC-5**: Given DLQ tiene mensajes, When llamo `serverless metrics`,
  Then output incluye `ApproximateNumberOfMessages` de DLQ
- **AC-6**: Given Neon caido temporalmente, When procesa batch, Then
  Lambda falla con conexion error y AWS retries 3 veces antes de DLQ
- **AC-7**: Given 100 events INSERT en burst, When stream_processor
  procesa, Then todos los 100 llegan a PG en <60s (lag tipico
  documentado 5-30s)

## 4. Diagrama de Flujo

Documentado en `serverless/ARCHITECTURE.md` seccion 4.5.

## 5. Diagrama ER

Sin cambios. Replica items de `contacts`/`tracking` (Dynamo) a tablas PG
con mismo schema mas `stream_event_id` UNIQUE para idempotency.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN record INSERT contacts THEN UPSERT a PG contacts [AC-1]
- WHEN record INSERT tracking THEN UPSERT a PG tracking_events [AC-2]
- WHEN mismo eventID 2 veces THEN ON CONFLICT no duplica [AC-3]
- WHEN psycopg falla 3 veces THEN batch va a DLQ [AC-4]

### 6.B. Unit Tests

Path mirror `tests/unit/stream_processor/test_<X>.py`:

- `test_handler.py` — Powertools BatchProcessor con records mock
- `test_service.py` — orquestacion idempotency + transform + upsert
- `test_transformers.py` — DynamoDB Item -> PG row mapping (todos los tipos)
- `test_pg_writer.py` — UPSERT con testcontainers PG18
- `test_retries.py` — clasificacion errores transient vs permanent

Coverage minimo: 85% per-file.

### 6.D. Integration test

- Stack dev con DynamoDB Streams habilitados + Neon dev branch
- Insertar 50 contacts y 100 tracking events en Dynamo via boto3
- Esperar 60s
- Query PG para verificar los 150 items existen + sin duplicados

## 7. Archivos Afectados

### Crear

- `serverless/src/stream_processor/handler.py`
- `serverless/src/stream_processor/service.py`
- `serverless/src/stream_processor/transformers.py`
- `serverless/src/stream_processor/pg_writer.py`
- `serverless/src/stream_processor/retries.py`
- `serverless/src/stream_processor/schemas.py`
- `serverless/src/stream_processor/requirements.txt` — sin deps extra
  (psycopg via PostgresLayer)
- `serverless/events/stream_record_contact_insert.json`
- `serverless/events/stream_record_tracking_insert.json`
- `serverless/events/stream_record_tracking_remove.json`

### Modificar

- `serverless/template.yaml` — agregar `StreamProcessorFunction`:
  - CodeUri: src/stream_processor/
  - Layers: [CommonLayer, PostgresLayer]
  - ReservedConcurrentExecutions: 2
  - MemorySize: 512, Timeout: 60
  - Policies: DynamoDBStreamReadPolicy + DynamoDBCrudPolicy
    processed_stream_events table + ssm:GetParameter neon-url
  - Events: ContactsStream + TrackingStream (DynamoDB triggers)
  - DLQ: !GetAtt StreamProcessorDLQ.Arn
- `serverless/template.yaml` — agregar `StreamProcessorDLQ`
  AWS::SQS::Queue (MessageRetentionPeriod 14d, sin alarma porque
  decidimos no usar AWS::CloudWatch::Alarm)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | schemas.py + transformers.py | — | T2 |
| T2 | pg_writer.py | — | T1 |
| T3 | retries.py | T1 | T1, T2 |
| T4 | service.py | T1, T2, T3 | — |
| T5 | handler.py | T4 | — |
| T6 | template.yaml + DLQ + deploy | T5 | — |
| T7 | Integration test stack dev | T6 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-005, SPEC-006 done (las Lambdas hot path escriben a Dynamo
      con Streams habilitados)
- [ ] SPEC-008 done (Neon + migrations + psycopg3 layer)

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Coverage >= 85% per-file
- [ ] Integration test 150 items end-to-end pasa
- [ ] Lag p99 entre write Dynamo y read PG < 30s
- [ ] DLQ vacio despues de smoke test (sin errores transients)
- [ ] CloudWatch metric `ProcessedRecords` aumenta con cada batch
