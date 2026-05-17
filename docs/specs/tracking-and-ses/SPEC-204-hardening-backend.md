# SPEC-204: Hardening del backend — tests + cache UA + limpieza

**Estado**: draft
**Fase**: 2
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/src/tracking_pixel/`,
`serverless/src/stream_processor/`, `serverless/tests/`,
`serverless/migrations/`
**Dependencias**: Fase 1 (SPEC-102 toca `tracking_pixel` y `stream_processor`)
**Paralelizable con**: SPEC-203

> Anterior: [SPEC-203](SPEC-203-runbook-observability.md) | Siguiente: [README](README.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de Fase 1 (SPEC-102 toca los mismos archivos backend).

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Mapa de las 2 fases, historial de migracion de `serverless/specs/` |
| `serverless/src/tracking_pixel/enrichment.py` | Parsing de UA con regex; se le aplica `@cached` |
| `serverless/src/common/cache/` | El decorador `@cached` reutilizable (modulo existente) |
| `serverless/src/tracking_pixel/` (service/persistence/schemas) | Archivos sin tests suficientes |
| `serverless/src/stream_processor/` (handler/pg_writer) | Archivos sin tests suficientes |
| `serverless/tests/tracking_pixel/`, `serverless/tests/stream_processor/` | Tests existentes; ver el patron + que falta |
| `serverless/migrations/005_migrations_log.sql` | Tiene un `INSERT` que referencia migrations 003/004 inexistentes |
| [SPEC-102](SPEC-102-trackingpixel-page-load.md) | Pudo haber creado parte de los tests; coordinar para no duplicar |

### Rules del proyecto aplicables

- `.claude/rules/python.md` — Python 3.13/3.14, pytest, asserts EXACTOS,
  coverage >= 80 % per-file, BDD-style en docstring
- `.claude/rules/neon-management.md` — NUNCA editar una migration aplicada;
  si el `005` ya esta aplicado, la limpieza va via migration nueva
- skill `dynamodb-cache` — patrones del decorador `@cached`
- `.claude/rules/verify-before-done.md` — verificar antes de declarar listo

### Decisiones del interview / verificacion que aplican

- Solo se migra la deuda real verificada: tests faltantes + `@cached` en el
  UA parsing + limpieza del `005`.
- NO se crean migrations 003/004 (obsoletas: el dashboard fue descartado).
- NO se crea `service.py`/`retries.py`/`schemas.py` en `stream_processor`
  (el Lambda funciona; separar la logica es cosmetico).
- NO se agrega la libreria `user-agents` (el regex propio es suficiente).

## 1. Contexto

Al migrar los specs del antiguo `serverless/specs/` se verifico el codigo real
contra los AC. Resultado: tres specs draft (SPEC-006 tracking_pixel, SPEC-008
Neon, SPEC-009 stream_processor) tienen huecos. La verificacion los clasifico:

- **Migrations 003/004 (SPEC-008)** — OBSOLETAS. Las materialized views y
  tablas de agregados servian al dashboard, que fue descartado (SPEC-010/014
  descartadas). No se reimplementan.
- **`stream_processor` service.py/retries.py/schemas.py (SPEC-009)** — REFACTOR
  COSMETICO. El Lambda YA funciona: `handler.py` hace batch processing con
  Powertools, `pg_writer.py` tiene idempotencia (`ON CONFLICT`), el DLQ esta
  configurado. La logica solo no esta separada en esos archivos. No aporta
  valor reorganizarla.
- **Tests faltantes + cache UA (SPEC-006, SPEC-009)** — DEUDA REAL. Esto si se
  migra: son los unicos huecos con valor.

Esta spec consolida la deuda real verificada en un solo trabajo de hardening.

### Hallazgos de exploracion

- `serverless/src/tracking_pixel/enrichment.py` parsea el User-Agent con regex
  propio (~20 lineas). NO usa la libreria `user-agents`; el spec viejo la
  recomendaba pero la implementacion self-contained es preferible (sin
  dependencia externa). `user-agents` NO se agrega a ningun requirements.
- `enrichment.py` NO cachea el parsing: cada invocacion re-ejecuta el regex.
  SPEC-006 pedia `@cached(24h)`. Existe `common.cache` con un decorador
  `@cached` reutilizable.
- Tests de `tracking_pixel` presentes: `test_handler.py`, `test_enrichment.py`.
  Faltan: `test_service.py`, `test_persistence.py`, `test_schemas.py`.
- Tests de `stream_processor` presentes: `test_transformers.py`. Faltan:
  `test_handler.py`, `test_pg_writer.py`.
- `serverless/migrations/005_migrations_log.sql` contiene un `INSERT` que
  referencia las migrations 003/004 inexistentes — induce a confusion.

## 2. Solucion propuesta

Solo deuda real verificada. Nada de reorganizar codigo que ya funciona.

1. **Cache del UA parsing**: aplicar el decorador `@cached` (de
   `common.cache`, TTL 24h) a la funcion de parsing de `enrichment.py`, con
   key derivada del string User-Agent. UA repetidos en invocaciones warm no
   re-ejecutan el regex.
2. **Tests faltantes de `tracking_pixel`**: crear `test_service.py`,
   `test_persistence.py`, `test_schemas.py` hasta cubrir >= 80 % per-file.
3. **Tests faltantes de `stream_processor`**: crear `test_handler.py` y
   `test_pg_writer.py` (batch processing, idempotencia, manejo de error que
   reporta `batchItemFailures`) hasta >= 80 % per-file.
4. **Limpieza de `005_migrations_log.sql`**: quitar del `INSERT` las filas que
   referencian migrations 003/004 que nunca van a existir.

Lo que esta spec **NO hace** (y por que):

- NO crea migrations 003/004 — obsoletas, el dashboard fue descartado.
- NO crea `service.py`/`retries.py`/`schemas.py` en `stream_processor` — el
  Lambda funciona; separar la logica es cosmetico y sin valor.
- NO agrega la libreria `user-agents` — el regex propio es suficiente y evita
  una dependencia.

### Decisiones clave

- **Decision 1: solo se migra la deuda con valor verificado** — la
  verificacion separo obsoleto / cosmetico / deuda real. Solo lo ultimo entra.
- **Decision 2: `@cached` reutiliza el modulo existente** — no se escribe un
  mecanismo de cache nuevo; se usa `common.cache`.
- **Decision 3: cobertura como cierre, no como objetivo inflado** — los tests
  cubren el comportamiento real de los archivos sin tests; el umbral es el
  estandar del proyecto (80 % per-file), no mas.
- **Decision 4: la limpieza del `005` es parte del hardening** — una migration
  ya aplicada NO se edita en su SQL ejecutable; aqui solo se corrige un
  `INSERT` de bookkeeping que nombra archivos inexistentes. Si el `005` ya
  esta aplicado en algun stage, evaluar hacerlo via migration nueva en vez de
  editar el archivo (ver Validacion).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el mismo string User-Agent procesado dos veces en una Lambda
  warm, When se invoca el parsing, Then la segunda invocacion devuelve el
  resultado cacheado sin re-ejecutar el regex.
- **AC-2**: Given dos User-Agent distintos, When se procesan, Then cada uno
  produce su propio resultado (la cache no colisiona keys).
- **AC-3**: Given los tests de `tracking_pixel`, When se corre la suite con
  coverage, Then `service.py`, `persistence.py` y `schemas.py` alcanzan
  >= 80 % per-file.
- **AC-4**: Given los tests de `stream_processor`, When se corre la suite con
  coverage, Then `handler.py` y `pg_writer.py` alcanzan >= 80 % per-file.
- **AC-5**: Given el test de `stream_processor` para un evento ya procesado,
  When el handler lo recibe de nuevo, Then NO se duplica la fila en
  PostgreSQL (idempotencia verificada por test).
- **AC-6**: Given `005_migrations_log.sql`, When se inspecciona su `INSERT`,
  Then no contiene referencias a las migrations 003 ni 004.
- **AC-7**: Given el estado del codigo tras esta spec, When se revisan los
  requirements, Then la libreria `user-agents` NO esta declarada como
  dependencia (el parsing sigue siendo regex propio).

## 4. Diagrama de Flujo

N/A — el cambio no altera flujos de control. El `@cached` es transparente:
misma entrada, misma salida, solo evita recomputo.

## 5. Diagrama ER

N/A — no hay cambios de schema. La limpieza del `005` solo toca un `INSERT`
de bookkeeping, no la estructura de ninguna tabla.

## 6. Tests Requeridos

### 6.B. Unit Tests (pytest)

**`serverless/tests/tracking_pixel/`:**

- `test_enrichment.py` (ampliar): el parsing cacheado devuelve el mismo
  resultado sin recomputo; UA distintos no colisionan `[AC-1][AC-2]`.
- `test_service.py` (crear): orquestacion `process_tracking_event` —
  enrichment + persist, payload correcto `[AC-3]`.
- `test_persistence.py` (crear): el item escrito en DynamoDB tiene los
  atributos esperados, TTL, `event_id`/`event_type_id` (de SPEC-102) `[AC-3]`.
- `test_schemas.py` (crear): validacion de `TrackingEventInput` — campos
  requeridos, limites, UUID `[AC-3]`.

**`serverless/tests/stream_processor/`:**

- `test_handler.py` (crear): batch processing, un record OK + un record que
  falla -> `batchItemFailures` reporta solo el fallido `[AC-4][AC-5]`.
- `test_pg_writer.py` (crear): `INSERT`/`ON CONFLICT`; evento repetido no
  duplica `[AC-4][AC-5]`.

### 6.C. Typecheck

- `serverless typecheck` sin errores.

## 7. Archivos Afectados

### Modificar

- `serverless/src/tracking_pixel/enrichment.py` — aplicar `@cached` (de
  `common.cache`, TTL 24h) a la funcion de parsing del User-Agent.
  - Por que: evitar re-ejecutar el regex en invocaciones warm con UA repetido.
  - Verificar: `test_enrichment.py` `[AC-1][AC-2]`.
- `serverless/migrations/005_migrations_log.sql` — quitar del `INSERT` las
  filas que nombran las migrations 003/004 inexistentes.
  - Por que: el archivo induce a pensar que esas migrations existen.
  - Verificar: inspeccion del `INSERT` `[AC-6]`.

### Crear

- `serverless/tests/tracking_pixel/test_service.py` — tests de `service.py`.
  - Verificar: suite verde, coverage `service.py` >= 80 % `[AC-3]`.
- `serverless/tests/tracking_pixel/test_persistence.py` — tests de
  `persistence.py`.
  - Verificar: coverage `persistence.py` >= 80 % `[AC-3]`.
- `serverless/tests/tracking_pixel/test_schemas.py` — tests de `schemas.py`.
  - Verificar: coverage `schemas.py` >= 80 % `[AC-3]`.
- `serverless/tests/stream_processor/test_handler.py` — tests del handler de
  streams (batch + `batchItemFailures`).
  - Verificar: coverage `handler.py` >= 80 % `[AC-4][AC-5]`.
- `serverless/tests/stream_processor/test_pg_writer.py` — tests de escritura a
  PG (idempotencia).
  - Verificar: coverage `pg_writer.py` >= 80 % `[AC-4][AC-5]`.

> Nota: si SPEC-102 ya creo o amplio `test_schemas.py`/`test_persistence.py`
> de `tracking_pixel` y `test_pg_writer.py` de `stream_processor`, esta spec
> los completa hasta el umbral en vez de duplicarlos. Coordinar con SPEC-102.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `enrichment.py` + `test_enrichment.py` | AC-1,2,7 | Fase 1 | T2, T3, T4 |
| T2 | tests `tracking_pixel` (service/persistence/schemas) | AC-3 | Fase 1 | T1, T3, T4 |
| T3 | tests `stream_processor` (handler/pg_writer) | AC-4,5 | Fase 1 | T1, T2, T4 |
| T4 | `005_migrations_log.sql` | AC-6 | — | T1, T2, T3 |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Fase 1 en `main` (SPEC-102 ya toco `tracking_pixel`/`stream_processor`)
- [ ] Confirmar si `005` esta aplicado en dev/prod: si lo esta, la limpieza se
  hace via migration nueva de bookkeeping, NO editando el `.sql` aplicado
  (ver `.claude/rules/neon-management.md`: no editar migrations aplicadas)
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-7 cubiertos por tests/verificaciones que pasan
- [ ] Coverage >= 80 % per-file en todos los archivos backend tocados
- [ ] `serverless lint`, `serverless format`, `serverless typecheck` pasan
- [ ] `serverless validate` pasa
- [ ] La suite completa de `serverless/tests/` verde
- [ ] `user-agents` confirmada ausente de los requirements

> Anterior: [SPEC-203](SPEC-203-runbook-observability.md) | Siguiente: [README](README.md)
