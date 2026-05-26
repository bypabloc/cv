# 01 - Contexto y Decision

## 1. Contexto / Problema

Tras desplegar SnapStart en `portfolio-contact-form-{dev,stage,prod}` (PRs
#146-149), el cold start del Lambda bajo de 5.7s a ~1.3s (RESTORE 752-1043ms
+ handler ~550ms). Pero el usuario reporto que en prod el form sigue
tardando **6-7 segundos** end-to-end desde el browser.

Auditoria de las ultimas 3 invocaciones prod en CloudWatch
(`/aws/lambda/portfolio-contact-form-prod`, 26 may 2026, post-SnapStart):

| Invocacion | Restore | Preload | Validate | Execute | Total |
|------------|---------|---------|----------|---------|-------|
| #1 (16:31) | 484ms   | 1ms     | 513ms    | 2051ms  | **5460ms** |
| #2 (16:24) | 1113ms  | 51ms    | 489ms    | 3582ms  | **8755ms** |
| #3 (15:45) | 265ms   | 0ms     | 459ms    | 2370ms  | **5742ms** |

Las 3 invocaciones reportan `"cold_start":true` — el bajisimo volumen
(~200 contactos/mes) hace que cada submit pague un cold start fresco.
SnapStart restore es eficiente, pero las **fases post-restore (Validate +
Execute) suman 2.5-4 segundos** y eso es lo que el usuario percibe.

### Hallazgos de exploracion

**Que hace VALIDATE (459-513ms)**: corre `verify_turnstile_token` que hace
`POST challenges.cloudflare.com/turnstile/v0/siteverify` (HTTP a Cloudflare,
~500ms fijos — handshake TLS Cloudflare + procesamiento del token).
**Optimizable? NO** — el verify es responsabilidad de un 3er actor (Cloudflare).

**Que hace EXECUTE (2050-3580ms)**, en orden secuencial:

1. `check_or_raise` (rate_limit) — 4 lookups DynamoDB:
   - `get_ip_rule(ip)` (cacheado @cached ttl=60)
   - `get_country_rule(country)` (cacheado)
   - `get_endpoint_rule(endpoint)` (cacheado)
   - `get_effective_count(...)` (NO cacheado — DDB Query sliding window)
2. `enqueue_contact_message` -> `send_to_queue`:
   - `get_secret(SSM_CONTACT_FORM_QUEUE_URL_PATH)` (cacheado modulo-scope)
   - `sqs.send_message(...)` (~50-100ms warm, ~200-300ms cold handshake)
3. `_auto_blacklist_step(ip)` — 1 DynamoDB UpdateItem.

**Diagnostico real**: en warm path la suma de DDB serializados es ~150-300ms
(las 3 rule lookups son cache hits, ~0-50ms cada una). El resto de los
2-3.5 segundos viene de:

- **Handshakes TLS de boto3 cold** (~200-500ms primera llamada por servicio
  AWS dentro del microVM restaurado). SnapStart preserva el cliente boto3
  en memoria pero NO el TLS handshake — la primera invocacion a SSM/DDB/SQS
  post-restore paga el handshake completo.
- **`@cached` cache miss en cold** — las 3 rule lookups van a la tabla
  `cache` DynamoDB en cada microVM nuevo (la cache es DDB, no in-memory).
- **`get_secret` cache miss** para el queue URL.

## 2. Solucion Propuesta

3 optimizaciones quick wins en 1 PR atomico:

### A. Paralelizar las 4 DDB del rate_limit con ThreadPoolExecutor

`check_or_raise` deja de ejecutar las 4 lookups secuenciales y las dispara
todas en paralelo con `concurrent.futures.ThreadPoolExecutor(max_workers=4)`.
La logica condicional (si IP blacklist no eval country, si country block no
eval endpoint) se aplica DESPUES con los 4 resultados ya disponibles.

**Trade-off aceptado**: si la IP esta blacklisteada, gastamos 3 DDB reads
"inutiles" (~$0.0000001 cada uno). Beneficio: latencia = max(4) en vez de
sum(4), ahorra ~100-200ms en cold, ~50-100ms en warm.

### B. SnapStart warmup hook generico en shared/lambda_kit

Nuevo modulo `shared/lambda_kit/snap_start_warmup.py` con la API:

```python
register_warmup(clients=['sqs', 'dynamodb', 'ssm'])
```

Se invoca UNA vez en el INIT del lambda (durante `PublishVersion` cuando
SnapStart toma el snapshot). El hook:

1. Crea el cliente boto3 de cada servicio.
2. Hace una llamada read-only barata (handshake TLS + sigv4):
   - SSM: `list_parameters(MaxResults=1)`
   - DynamoDB: `describe_endpoints()`
   - SQS: `list_queues(MaxResults=1)`
3. Cada call con `try/except Exception` -> log WARNING y continua si falla.

El snapshot Firecracker captura el cliente boto3 con sus conexiones HTTPS
abiertas (keep-alive + cert chain verificada). Post-restore, la primera
invocacion real reutiliza esa conexion: handshake ya hecho, gana ~200-500ms.

**Limite**: si el snapshot dura mas que el TTL de la conexion HTTPS, el
keep-alive se cae y la primera llamada paga el handshake. AWS no documenta
el TTL exacto pero observado es 1-5 min. Para low traffic (1 req/dia), el
beneficio se diluye. Para el patron actual (varios contactos por sesion),
gana.

### C. Wire opt-in en contact_form

`services/contact_form/core/handler.py` agrega:

```python
from shared.lambda_kit.snap_start_warmup import register_warmup

register_warmup(clients=['sqs', 'dynamodb', 'ssm'])
```

Despues de los imports module-scope. El `manifest.yaml` declara
`snap_start_warmup: [sqs, dynamodb, ssm]` para documentar el wire (no es
leido por devtools — pura documentacion).

### Decisiones clave

- **Decision 1: orden de validaciones se mantiene** — rate_limit primero
  protege Turnstile de DoS (un GetItem cuesta $0.0000025; el verify HTTP a
  Cloudflare cuesta ~500ms + es la API de un 3er actor). Cambiar el orden
  esta fuera de scope.
- **Decision 2: auto_blacklist queda en encoder, secuencial al final** —
  NO se mueve al worker (preserva deteccion de bots en tiempo real). NO se
  paraleliza con el SQS publish (riesgo de inconsistencia si SQS falla).
- **Decision 3: paralelizar las 4 DDB siempre** — la logica condicional
  se aplica sobre los 4 resultados ya disponibles. Gastamos ~$0.0000001
  extra por request blacklisted, irrelevante vs el ahorro de latencia.
- **Decision 4: SnapStart hook generico opt-in** — vive en
  `shared/lambda_kit/`, cada lambda decide si lo usa. `contact_form` lo
  activa. Otros lambdas pueden adoptarlo despues sin tocar shared.
- **Decision 5: warmup con calls genericos AWS, NO recursos del proyecto** —
  `ssm list_parameters --max-items=1`, `dynamodb describe_endpoints`,
  `sqs list_queues --max-items=1`. Estos calls NO tocan tablas/queues/
  parametros que aun no existan. Cero riesgo de deploy nuevo donde el
  recurso no este creado.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un POST /contact valido con bypass Turnstile en dev,
  When el lambda procesa la request post-deploy, Then responde HTTP 202 con
  `{contact_id, created_at, accepted: true}` (sin regresion del contrato
  actual).

- **AC-2**: Given el lambda `contact_form` post-deploy, When CloudWatch
  reporta el cold start de una invocacion, Then los logs incluyen 3 lineas
  con prefijo `[snap_start_warmup]` indicando los 3 clients pre-calentados
  (sqs, dynamodb, ssm), 1 por client, con status `ok` o `failed` por cada
  uno.

- **AC-3**: Given el SnapStart warmup hook activado, When uno o mas de los
  warmup calls falla (ej: AWS retorna 5xx transitorio), Then el INIT del
  lambda completa con exito (no aborta) y CloudWatch tiene log
  `WARNING [snap_start_warmup] <client>: <error_message>` por cada fallo.

- **AC-4**: Given el `check_or_raise` paralelo en uso, When la IP del
  request esta blacklisteada (caso short-circuit antiguo), Then el lambda
  raise `IPBlacklistedError` con el mismo `retry_after_seconds` y el mismo
  shape de error que hoy (sin regresion del contrato).

- **AC-5**: Given el `check_or_raise` paralelo, When las 4 DDB lookups
  retornan exitosamente, Then la duracion total del rate_limit es <= max
  de las 4 individualmente (medido en test unitario con sleeps
  artificiales).

- **AC-6**: Given el plan deployado en los 3 envs, When se capturan 10
  mediciones de smoke `/contact` post-deploy, Then la mediana del Total
  Duration del cold start baja al menos un **20%** vs la mediana
  pre-deploy (~5500ms -> <=4400ms; objetivo realista
  considerando que Turnstile verify es 500ms fijos no optimizables).

- **AC-7**: Given los smokes post-deploy en dev/stage/prod, When se
  compara warm path (segunda invocacion del mismo microVM), Then la
  mediana baja al menos **30%** vs warm pre-deploy (~1300-1500ms ->
  <=1000ms).

- **AC-8**: Given todos los cambios, When `pytest` corre la suite completa
  de `shared/rate_limit/` + `shared/lambda_kit/` + `services/contact_form/`,
  Then todos los tests pasan (incluyendo los 8+ nuevos tests del plan).

## 4. Diagrama de Flujo

### Antes

```
RESTORE (SnapStart, 484-1113ms)
   |
   v
PRELOAD (~1-51ms)
   |
   v
VALIDATE (459-513ms)
   `--> verify_turnstile_token (HTTP a Cloudflare, ~500ms)
   |
   v
EXECUTE (2051-3582ms)
   |
   |--> check_or_raise (~600-1200ms en cold, ~150-300ms en warm)
   |     |--> get_ip_rule         (DDB GetItem, SECUENCIAL)
   |     |--> get_country_rule    (DDB GetItem, SECUENCIAL)
   |     |--> get_endpoint_rule   (DDB GetItem, SECUENCIAL)
   |     `--> get_effective_count (DDB Query, SECUENCIAL)
   |
   |--> verify_turnstile_token YA EJECUTADA EN VALIDATE
   |
   |--> enqueue_contact_message (~100-300ms)
   |     |--> get_secret(queue_url)  (SSM cached)
   |     `--> sqs.send_message       (cold ~200-300ms, warm ~50ms)
   |
   `--> _auto_blacklist_step    (DDB UpdateItem, ~50-100ms)

Total post-restore: 2500-4000ms
```

### Despues

```
INIT (en PublishVersion, antes del snapshot):
   |
   |--> [NUEVO] register_warmup(['sqs', 'dynamodb', 'ssm'])
   |     |--> boto3.client('sqs')      + sqs.list_queues(MaxResults=1)
   |     |--> boto3.client('dynamodb') + dynamodb.describe_endpoints()
   |     `--> boto3.client('ssm')      + ssm.list_parameters(MaxResults=1)
   |
   v
[Snapshot Firecracker captura clientes boto3 + handshakes TLS]
   |
   v
RESTORE (SnapStart, 484-1113ms)
   |
   v
PRELOAD (~1-51ms)
   |
   v
VALIDATE (459-513ms)  <-- SIN CAMBIOS, Turnstile verify es fijo
   |
   v
EXECUTE (objetivo: 800-1400ms)
   |
   |--> check_or_raise [PARALELO]
   |     `--> ThreadPoolExecutor(max_workers=4) lanza:
   |           - get_ip_rule         (DDB GetItem)  |
   |           - get_country_rule    (DDB GetItem)  | EN PARALELO
   |           - get_endpoint_rule   (DDB GetItem)  | max(4) ~100-200ms
   |           - get_effective_count (DDB Query)    |
   |
   |--> enqueue_contact_message (~50-100ms, handshake ya warm)
   |     |--> get_secret(queue_url)  (SSM cached)
   |     `--> sqs.send_message       (warm ~50ms, gracias al warmup hook)
   |
   `--> _auto_blacklist_step    (DDB UpdateItem, ~50-100ms)

Total post-restore: 800-1400ms
Speedup esperado: -50% a -65% en EXECUTE
```

## 5. Diagrama ER

`N/A — no hay cambios en base de datos. Las tablas `rate-limit-rules`,
`rate-limit-buckets`, `cache` y `contacts` (Neon) mantienen su shape.`

## 6. Tests Requeridos

### 6.A. TDD Flows (logica nueva en shared/)

**`shared/rate_limit/check.py` (refactor a paralelo)**:

- WHEN check_or_raise corre con 4 DDB que demoran 100ms cada una THEN total duration es <= 150ms (max + overhead) [AC-5]
- WHEN ip_rule retorna blacklist y las otras 3 retornan exito THEN raise IPBlacklistedError IGNORANDO los otros resultados [AC-4]
- WHEN country_rule retorna block y ip_rule retorna None THEN raise CountryBlockedError despues de esperar las 4 [AC-4]
- WHEN endpoint_rule retorna limit=5 y effective_count=10 THEN raise RateLimitExceededError con el limit/window correctos [AC-4]

**`shared/lambda_kit/snap_start_warmup.py` (nuevo modulo)**:

- WHEN register_warmup(['sqs']) corre y boto3.client('sqs').list_queues() exito THEN log INFO `[snap_start_warmup] sqs: ok` [AC-2]
- WHEN register_warmup(['ssm', 'dynamodb', 'sqs']) corre y dynamodb falla THEN log WARNING `[snap_start_warmup] dynamodb: <error>` y los otros 2 continuan [AC-3]
- WHEN register_warmup(['xxx']) recibe un cliente no soportado THEN raise ValueError ANTES del INIT (defensa contra typo en manifest)
- WHEN register_warmup([]) (lista vacia) THEN no-op silencioso (no falla)

### 6.B. Unit Tests (pytest)

| Test file | Coverage |
|-----------|----------|
| `serverless/lambda/shared/tests/unit/shared/rate_limit/test_check_parallel.py` | check_or_raise paralelo, 4 escenarios (AC-4, AC-5) |
| `serverless/lambda/shared/tests/unit/shared/lambda_kit/test_snap_start_warmup.py` | register_warmup, 4 escenarios (AC-2, AC-3) |
| `serverless/lambda/services/contact_form/tests/unit/test_handler_warmup_wired.py` | El handler.py importa y llama register_warmup en module-scope (AC-2) |

### 6.C. Typecheck

```bash
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --shared
```

Falla si los nuevos tests no pasan.

### 6.D. E2E Tests

N/A — los specs Playwright actuales (`tests/feature/contact/contact-form.spec.ts`)
ya cubren el flujo. El smoke real con `curl` + bypass + tabla metricas vive en
[07-verificacion-e2e.md](07-verificacion-e2e.md).

## 7. Archivos Afectados

### Crear

- `serverless/lambda/shared/lambda_kit/snap_start_warmup.py` — modulo nuevo con `register_warmup(clients)`
  - Verificar: `python devtools/run.py serverless tests --type=unit --shared` con los 4 nuevos casos del modulo
- `serverless/lambda/shared/tests/unit/shared/lambda_kit/test_snap_start_warmup.py` — 4 tests TDD
  - Verificar: pytest verde
- `serverless/lambda/shared/tests/unit/shared/rate_limit/test_check_parallel.py` — 4 tests TDD del flow paralelo
  - Verificar: pytest verde
- `serverless/lambda/services/contact_form/tests/unit/test_handler_warmup_wired.py` — 1 test que el handler llama register_warmup
  - Verificar: pytest verde

### Modificar

- `serverless/lambda/shared/rate_limit/check.py` — refactor `check_or_raise` a `ThreadPoolExecutor(max_workers=4)`
  - Verificar: tests unit AC-4 + AC-5 verdes
- `serverless/lambda/shared/rate_limit/__init__.py` — re-export si hace falta (chequear)
  - Verificar: import desde el lambda funciona
- `serverless/lambda/shared/lambda_kit/__init__.py` — re-export `register_warmup`
  - Verificar: `from shared.lambda_kit.snap_start_warmup import register_warmup` funciona
- `serverless/lambda/services/contact_form/core/handler.py` — import + invoke `register_warmup` module-scope
  - Verificar: pytest del test_handler_warmup_wired.py verde
- `serverless/lambda/services/contact_form/manifest.yaml` — agrega `snap_start_warmup: [sqs, dynamodb, ssm]` (documental)
  - Verificar: provisioner sigue parseando OK (`serverless lint-deps --lambda=contact_form`)
- `docs/specs/contact-form-latency-optim/` — la propia carpeta del plan (EFIMERA, se borra al cerrar)

### Eliminar

`N/A` — el ultimo commit del plan borra `docs/specs/contact-form-latency-optim/` (regla `plan-format.md`).
