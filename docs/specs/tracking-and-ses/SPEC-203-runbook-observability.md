# SPEC-203: Revision RUNBOOK + DEPLOYMENT + smoke test

**Estado**: draft
**Fase**: 2
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/DEPLOYMENT.md`, `serverless/RUNBOOK.md`,
`serverless/scripts/smoke_test.sh`, AWS Billing
**Dependencias**: Fase 1 completa (el stack debe estar deployado y estable)
**Paralelizable con**: SPEC-202, SPEC-204

> Anterior: [SPEC-202](SPEC-202-rediseno-schema-contacts.md) | Siguiente: [SPEC-204](SPEC-204-hardening-backend.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de Fase 1 desplegada y estable.

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases |
| `serverless/DEPLOYMENT.md` | Documento existente a revisar (quitar seccion del dashboard) |
| `serverless/RUNBOOK.md` | Documento existente a revisar (quitar cron aggregator) |
| `serverless/scripts/smoke_test.sh` | Script existente a actualizar (contrato de `/track`) |
| `serverless/README.md` | Indice del backend; se le agregan enlaces |
| [SPEC-102](SPEC-102-trackingpixel-page-load.md) | El contrato de `/track` post-Fase 1 que el smoke debe reflejar |
| [SPEC-204](SPEC-204-hardening-backend.md) | Coordina la obsolescencia de migrations del dashboard |

### Rules del proyecto aplicables

- `.claude/rules/markdown-docs.md` — formato de la documentacion del backend
- `.claude/rules/verify-before-done.md` — verificar antes de declarar listo
- skill `aws-ses` / `aws-lambda-python` — referencia para el RUNBOOK

### Decisiones del interview que aplican

- Los 3 artefactos (`DEPLOYMENT.md`, `RUNBOOK.md`, `smoke_test.sh`) YA existen:
  esta spec los REVISA, no los crea.
- El dashboard fue descartado: hay que quitar su rastro de la doc operacional.
- El smoke test debe reflejar el contrato de `/track` con `event_type_id`.

## 1. Contexto

El antiguo `serverless/specs/SPEC-015` (en `draft`) planteaba CREAR la
documentacion operacional del backend. La verificacion al migrar los specs
encontro que esa documentacion **ya existe**:

- `serverless/DEPLOYMENT.md` — 325 lineas, guia completa del primer deploy.
- `serverless/RUNBOOK.md` — 295 lineas, operaciones + troubleshooting.
- `serverless/scripts/smoke_test.sh` — smoke test E2E con exit codes.

Por lo tanto esta spec NO crea esos artefactos: los **revisa y actualiza**.
La verificacion detecto dos problemas concretos:

### Hallazgos de exploracion

- `DEPLOYMENT.md` tiene una seccion "4. Activar dashboard" y `RUNBOOK.md`
  menciona el dashboard y el cron `aggregator`. El **dashboard fue descartado**
  (las specs SPEC-010 `aggregator` y SPEC-014 `dashboard_api` se descartaron).
  Esas referencias son documentacion obsoleta que confunde.
- `DEPLOYMENT.md` (paso 4) menciona migrations `daily_metrics` y
  `top_pages_daily` — tablas que servian al dashboard. Hay que verificar si
  esas tablas existen o son referencia muerta (relacionado con SPEC-204, que
  trata la obsolescencia de migrations del dashboard).
- El `smoke_test.sh` prueba `POST /track`, pero el flujo de tracking cambio en
  Fase 1: ahora el body lleva `event_id` y `event_type_id`. El smoke debe
  reflejar el contrato actualizado.
- `RUNBOOK.md` ya cubre rotar secrets, logs, DLQ, rate-limit, migrations,
  cache, DDoS — esa parte esta vigente y NO se toca.
- La AWS Billing Alarm ya esta documentada en `DEPLOYMENT.md` (paso 4 del
  setup inicial).

## 2. Solucion propuesta

Tres ajustes acotados sobre archivos existentes.

1. **`DEPLOYMENT.md`**: eliminar la seccion "Activar dashboard" y las
   referencias a `daily_metrics`/`top_pages_daily` (tablas del dashboard
   descartado). Verificar que el resto de la guia sigue siendo correcto tras
   los cambios de Fase 1.
2. **`RUNBOOK.md`**: eliminar la operacion "verificar que el cron aggregator
   corrio" y cualquier mencion al dashboard. Agregar, si falta, una entrada
   de troubleshooting para el nuevo flujo de tracking (evento sin
   `event_type_id` -> 400).
3. **`smoke_test.sh`**: actualizar el `POST /track` para enviar `event_id` y
   `event_type_id` validos (el contrato post-Fase 1). Verificar que el check
   de DynamoDB y de Neon siguen alineados con el schema actual.
4. **AWS Billing Alarm**: verificar que existe y responde (no se crea, ya esta
   documentada).

### Decisiones clave

- **Decision 1: revisar, no recrear** — los tres artefactos existen y son
  buenos; esta spec corrige lo obsoleto, no reescribe.
- **Decision 2: quitar lo del dashboard** — el dashboard se descarto; mantener
  su rastro en la doc operacional desorienta a quien despliega u opera.
- **Decision 3: el smoke test refleja el contrato actual** — tras Fase 1,
  `/track` exige `event_type_id`; un smoke con el body viejo daria un falso
  resultado (200/400 inesperado).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given `DEPLOYMENT.md` revisado, When se busca "dashboard" en el
  archivo, Then no hay ninguna seccion ni paso que instruya activar o
  configurar un dashboard.
- **AC-2**: Given `RUNBOOK.md` revisado, When se busca "dashboard" o
  "aggregator", Then no hay operaciones referidas a esos componentes
  descartados.
- **AC-3**: Given `DEPLOYMENT.md` revisado, When un desarrollador nuevo lo
  sigue paso a paso, Then llega a un stack funcional en dev sin pasos muertos.
- **AC-4**: Given `smoke_test.sh` actualizado, When ejecuta el `POST /track`,
  Then el body incluye `event_id` y `event_type_id` validos y el endpoint
  responde 204.
- **AC-5**: Given `smoke_test.sh` ejecutado contra dev tras Fase 1, When todas
  las verificaciones pasan, Then termina con exit code 0.
- **AC-6**: Given `smoke_test.sh`, When una verificacion falla, Then termina
  con exit code distinto de 0 e indica el check fallido (comportamiento ya
  presente; se verifica que sigue valido).
- **AC-7**: Given el stack desplegado, When se ejecuta `aws cloudwatch
  describe-alarms --alarm-name-prefix portfolio-`, Then retorna 0 alarmas
  operacionales (solo la billing alarm global).

## 4. Diagrama de Flujo

N/A — el cambio es revision de documentacion + ajuste de un bash script, no
altera flujos de control de la aplicacion.

## 5. Diagrama ER

N/A — no hay cambios en base de datos.

## 6. Tests Requeridos

### 6.E. Verificacion manual

- Buscar "dashboard"/"aggregator" en `DEPLOYMENT.md` y `RUNBOOK.md`: cero
  resultados `[AC-1][AC-2]`.
- Ejecutar `smoke_test.sh dev` tras Fase 1: exit 0 `[AC-5]`.
- Forzar un fallo y confirmar exit != 0 `[AC-6]`.
- Seguir `DEPLOYMENT.md` desde un entorno limpio (o re-deploy) `[AC-3]`.
- `aws cloudwatch describe-alarms --alarm-name-prefix portfolio-` -> 0
  operacionales `[AC-7]`.

> El smoke test es verificacion ejecutable post-deploy, no test unitario. No
> aplica coverage.

## 7. Archivos Afectados

### Modificar

- `serverless/DEPLOYMENT.md` — eliminar la seccion "Activar dashboard" y las
  referencias a `daily_metrics`/`top_pages_daily`; revisar que la guia sigue
  correcta post-Fase 1.
  - Por que: el dashboard fue descartado; el paso es muerto y confunde.
  - Verificar: cero coincidencias de "dashboard" `[AC-1][AC-3]`.
- `serverless/RUNBOOK.md` — eliminar la operacion del cron `aggregator` y
  cualquier mencion al dashboard; agregar (si falta) troubleshooting del
  nuevo error de tracking (`event_type_id` ausente -> 400).
  - Por que: alinear la operacion con los componentes que realmente existen.
  - Verificar: cero coincidencias de "dashboard"/"aggregator" `[AC-2]`.
- `serverless/scripts/smoke_test.sh` — actualizar el `POST /track` para
  enviar `event_id` + `event_type_id`; revisar los checks de DynamoDB y Neon.
  - Por que: el contrato de `/track` cambio en Fase 1.
  - Verificar: exit 0 contra dev `[AC-4][AC-5]`.

### Verificacion (no es archivo)

- AWS Billing Alarm: confirmar que existe en `us-east-1` y responde `[AC-7]`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ----- | -------- | --- | ---------- | ----------------- |
| T1 | `DEPLOYMENT.md` | AC-1,3 | Fase 1 | T2, T3 |
| T2 | `RUNBOOK.md` | AC-2 | Fase 1 | T1, T3 |
| T3 | `smoke_test.sh` | AC-4,5,6 | Fase 1 | T1, T2 |
| T4 | Billing alarm (verificacion) | AC-7 | — | todas |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Fase 1 desplegada y estable en dev
- [ ] Confirmado si `daily_metrics`/`top_pages_daily` existen como tablas
  (coordinar con SPEC-204, que trata las migrations obsoletas del dashboard)

### Definition of Done

- [ ] AC-1 a AC-7 verificados
- [ ] `smoke_test.sh` pasa en dev y en prod
- [ ] `DEPLOYMENT.md` validado siguiendolo desde un entorno limpio
- [ ] `DEPLOYMENT.md` y `RUNBOOK.md` sin referencias al dashboard descartado
- [ ] AWS Billing Alarm responde al test de threshold
- [ ] `aws cloudwatch describe-alarms --alarm-name-prefix portfolio-`
  retorna 0 alarmas operacionales

> Anterior: [SPEC-202](SPEC-202-rediseno-schema-contacts.md) | Siguiente: [SPEC-204](SPEC-204-hardening-backend.md)
