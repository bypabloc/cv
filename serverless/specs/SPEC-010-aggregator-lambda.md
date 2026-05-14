# SPEC-010: Lambda `aggregator` (cron 03:00 UTC) + materialized views

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/aggregator/`,
`serverless/template.yaml`
**Dependencias**: SPEC-008, SPEC-009
**Paralelizable con**: SPEC-012, SPEC-013 (frontend)

## 1. Contexto

Lambda cron diario que computa agregaciones sobre `tracking_events` (PG)
y las guarda en `tracking_daily_aggregates` + `daily_metrics`. Tambien
refresca materialized views y dispara `pg_partman.run_maintenance()`
para crear nueva particion mensual + drop particiones > 60d.

### Hallazgos de exploracion

- Flujo completo en `serverless/ARCHITECTURE.md` seccion 4.6
- 10 queries listas para dashboard documentadas en
  `.claude/docs/postgresql-18-analytics/08-queries-dashboard.md`
- pg_partman.run_maintenance() debe correr regular para auto-drop

## 2. Solucion propuesta

Crear `serverless/src/aggregator/` con 4 archivos:

```text
aggregator/
├── __init__.py
├── handler.py             # EventBridge scheduled trigger
├── service.py             # orquesta queries en orden
├── queries.py             # SQL queries para agregar tracking_events
└── requirements.txt
```

### Decisiones clave

- **Decision 1: EventBridge Scheduled Rule** — vs CloudWatch Events
  legacy. Same thing en AWS, naming nuevo.
- **Decision 2: Cron 03:00 UTC** — hora valle (LATAM dormida, EU
  empezando). Lab Neon scale-up al cron, scale-to-zero auto despues.
- **Decision 3: Timeout 5min** — agregaciones sobre ~15k events del
  mes anterior deberian tomar <30s. Margen para crecimiento 10x.
- **Decision 4: `REFRESH MATERIALIZED VIEW CONCURRENTLY`** — no
  bloquea reads del dashboard mientras se refresca. Requiere unique
  index en la MV (incluido en migration 003).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el cron dispara a 03:00 UTC, When la Lambda completa,
  Then existe 1 row en `daily_metrics` con date=YESTERDAY + KPIs
  computed (total_pageviews, unique_sessions, total_contacts, conversion_rate)
- **AC-2**: Given aggregator se ejecuta, When inspecciono
  `tracking_daily_aggregates`, Then hay rows agrupadas por
  (date, path, utm_source) con counts correctos
- **AC-3**: Given materialized views existian con datos viejos, When
  aggregator ejecuta, Then `mv_contacts_by_month_niche` y
  `mv_session_journey` y `mv_top_landing_pages` tienen datos refrescados
- **AC-4**: Given mes nuevo empieza, When aggregator ejecuta el dia 1,
  Then `pg_partman.run_maintenance()` crea automaticamente la particion
  `tracking_events_<YYYY_MM>` del proximo mes
- **AC-5**: Given particiones > 60d, When aggregator ejecuta, Then
  pg_partman drop automatico (verificable con `\d+ tracking_events`)
- **AC-6**: Given aggregator falla por Neon timeout, When AWS detecta
  error, Then Lambda emite log ERROR sin alertar (decidimos no usar
  alarms; revisamos con `serverless logs`)
- **AC-7**: Given aggregator ejecuta exitoso, When llamo
  `cache.invalidate(tag='analytics')`, Then queries del dashboard
  consultan datos frescos en siguiente request

## 4. Diagrama de Flujo

Documentado en `serverless/ARCHITECTURE.md` seccion 4.6.

## 5. Diagrama ER

Sin cambios. Usa tablas creadas en SPEC-008 migration 004.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN aggregator ejecuta con 100 events de ayer THEN daily_metrics tiene 1 row [AC-1]
- WHEN aggregator ejecuta THEN tracking_daily_aggregates tiene rows por (date, path, utm) [AC-2]
- WHEN aggregator ejecuta THEN 3 MVs refrescadas [AC-3]
- WHEN dia 1 del mes THEN nueva particion creada [AC-4]
- WHEN particion > 60d THEN dropped [AC-5]

### 6.B. Unit Tests

- `tests/unit/aggregator/test_handler.py`
- `tests/unit/aggregator/test_service.py`
- `tests/unit/aggregator/test_queries.py` — con testcontainers PG18

Coverage minimo: 80%.

### 6.D. Integration test

- Insertar 500 mock tracking events distribuidos en 7 dias en PG dev
- Invocar Lambda manual via `serverless invoke --function=aggregator`
- Verificar daily_metrics tiene 7 rows + tracking_daily_aggregates
  poblada

## 7. Archivos Afectados

### Crear

- `serverless/src/aggregator/handler.py`
- `serverless/src/aggregator/service.py`
- `serverless/src/aggregator/queries.py` — 10+ SQL queries con
  parametros (yesterday, today)
- `serverless/src/aggregator/requirements.txt`
- `serverless/events/aggregator_scheduled.json`

### Modificar

- `serverless/template.yaml` — agregar `AggregatorFunction`:
  - CodeUri: src/aggregator/
  - Layers: [CommonLayer, PostgresLayer]
  - MemorySize: 1024, Timeout: 300
  - Policies: ssm:GetParameter (neon-url) + DynamoDBCrudPolicy cache (invalidar tag)
  - Events: DailySchedule (Schedule cron(0 3 * * ? *))

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | queries.py | — | T2 |
| T2 | service.py | T1 | — |
| T3 | handler.py | T2 | — |
| T4 | template.yaml + deploy + EventBridge | T3 | — |
| T5 | Integration test | T4 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-008 done
- [ ] SPEC-009 done (datos llegan a PG)

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Coverage >= 80%
- [ ] Primer cron real ejecuta (esperar a las 03:00 UTC despues del deploy)
- [ ] Logs CloudWatch muestran `AggregationCompleted` metric
- [ ] Duracion p99 < 60s con datos actuales (margen para crecimiento)
- [ ] Particion del mes proximo creada automaticamente
