# 02 — Shared foundations (portadores nuevos)

[← 01 contexto](01-contexto-y-decision.md) · [siguiente: 03 devtools →](03-devtools-provisioning.md)

> Fase 1. Crea los dos portadores `shared.*` que faltan para que el `core/`
> de los Lambdas nunca importe `boto3`/`jinja2` directo (provider-swappable).
> `shared.aws.s3` y `shared.aws.ses` YA existen y se reutilizan.

## 2.1 `shared.aws.lambda_invoke` (NUEVO)

Portador del cliente Lambda de boto3 para invocación async. Mismo patrón
lazy (PEP 562) que `shared.aws.ses`/`shared.aws.s3`.

### Crear
- `serverless/lambda/shared/aws/lambda_invoke.py`
  - `_client()` — `boto3.client('lambda', region_name=...)` lazy.
  - `__getattr__('lambda_client')` — PEP 562, crea al primer acceso.
  - `invoke_async(*, function_name: str, payload: dict) -> None` — hace
    `client.invoke(FunctionName=function_name, InvocationType='Event',
    Payload=json.dumps(payload, default=str).encode())`. NO espera respuesta;
    loggea `event_invoked` + métrica `LambdaInvokeOk`/`LambdaInvokeFailed`.
    Una excepción se loggea y se **re-lanza** como `LambdaInvokeError` para
    que el caller decida (en `contact_form`/`tracking_pixel` se captura y se
    degrada a un log — best-effort, NO rompe el 202).
  - `LambdaInvokeError(Exception)` — error tipado.
  - Verificar: `serverless tests --type=unit --shared` (test con moto/stub).

### Tests (TDD primero)
- `shared/tests/unit/shared/aws/test_lambda_invoke_async.py` — Given un
  function_name + payload, When `invoke_async`, Then llama `client.invoke`
  con `InvocationType='Event'` y el Payload JSON exacto (assert exacto sobre
  los kwargs con un stub/mock del cliente).
- `shared/tests/unit/shared/aws/test_lambda_invoke_reexport.py` — el módulo
  expone `invoke_async` + `LambdaInvokeError`.

## 2.2 `shared.templating` (NUEVO — Jinja2)

Portador único de Jinja2. El `core/` de `send_email` NUNCA importa `jinja2`.

### Crear
- `serverless/lambda/shared/templating/__init__.py` — VACÍO (docstring-only).
- `serverless/lambda/shared/templating/jinja.py`
  - `render(template_str: str, context: dict) -> str` — usa
    `jinja2.Environment(autoescape=...)`. Para HTML: `autoescape=True`
    (anti-XSS en las vars del visitante). Para TXT/subject: render con
    `autoescape=False` o un Environment separado. Exponer dos helpers:
    `render_html(template, ctx)` y `render_text(template, ctx)`.
  - `TemplateRenderError(Exception)` — envuelve `jinja2.TemplateError`.
  - Jinja2 se importa LAZY dentro de `render_*` (no en el top del módulo)
    para no penalizar el cold de un Lambda que importe `shared.templating`
    sin renderizar.
- `serverless/lambda/shared/templating/pyproject.toml` — declara
  `jinja2>=3.1` en `[project.dependencies]`. Sin `internal-deps` (no depende
  de otros shared salvo observability si loggea).

### Tests (TDD primero)
- `shared/tests/unit/shared/templating/test_render_html_substitutes_vars.py`
  — Given `'<p>Hola {{ name }}</p>'` + `{name:'Pablo'}`, When `render_html`,
  Then `'<p>Hola Pablo</p>'`.
- `..._escapes_html_in_html.py` — Given `{name:'<script>'}`, When
  `render_html`, Then la var queda escapada (`&lt;script&gt;`).
- `..._text_does_not_escape.py` — Given `render_text` con `&`, Then no
  escapa.
- `..._missing_var_raises_or_blank.py` — define el comportamiento (Jinja2
  por default deja `''` en undefined; assert exacto del contrato elegido:
  usar `StrictUndefined` → `TemplateRenderError` si falta una var, para
  fallar ruidoso en `send_email`).

## 2.3 `shared.db.read_async` (NUEVO — patrón de read concurrente)

> Decisión del usuario: "agregar patrón de read async". La investigación
> mostró que async NO sirve para las ESCRITURAS de estos encoders (1 request
> por container, escritura síncrona ~10-25ms). Pero los **reads multi-query**
> (varias agregaciones independientes, caso del dashboard analytics) SÍ se
> benefician de `asyncio.gather` cuando van por **conexiones separadas**.
> Este helper es la utilidad canónica para esos reads.

**Aviso de honestidad**: en ESTE plan NO hay consumidor (contact_form,
tracking_pixel, send_email sólo escriben/envían). El consumidor real es el
Lambda de lectura del dashboard (`docs/specs/analytics-dashboard-api`, otro
plan). Se agrega aquí porque el usuario lo pidió explícitamente y para fijar
el patrón antes de que el dashboard lo necesite. Si se prefiere evitar código
sin consumidor, esta sub-fase (T2b) puede diferirse al plan del dashboard —
queda anotado como decisión revisable.

### Crear
- `serverless/lambda/shared/db/read_async.py`
  - `gather_reads(*coros) -> tuple` — wrapper sobre `asyncio.gather` que
    ejecuta N corutinas de lectura concurrentes y devuelve sus resultados en
    orden. Cada corutina abre su propia `AsyncConnection` de psycopg3 al
    endpoint pooled (las conexiones separadas son lo que permite el
    paralelismo real; sobre una sola conexión PgBouncer serializa).
  - `run_reads(builder) -> result` — helper sync-friendly que hace
    `asyncio.run(...)` para invocar `gather_reads` desde un handler Lambda
    sync (el runtime no soporta handler async nativo).
  - psycopg3 `AsyncConnection` se importa LAZY (no penaliza el cold de un
    Lambda que no lea async).
- Documentar que es para READS (idempotentes, sin efectos); NUNCA para
  escrituras (serializan + no se benefician).

### Tests (TDD primero)
- `shared/tests/unit/shared/db/test_read_async_gathers_results_in_order.py`
  — Given 3 corutinas read mockeadas, When `gather_reads`, Then devuelve los
  3 resultados en el orden de entrada (assert exacto).
- `..._run_reads_executes_via_asyncio_run.py` — `run_reads` corre el builder
  bajo un loop nuevo y devuelve el resultado.

## 2.4 Catálogo de portadores (actualizar la rule)

Agregar a la tabla de `.claude/rules/lambda-shared-imports.md` (lo hace la
fase 6, archivo 07, pero se referencia aquí):

| Paquete externo | Portador | Import |
|---|---|---|
| `boto3` lambda client | `shared.aws.lambda_invoke` | `from shared.aws.lambda_invoke import invoke_async` |
| `jinja2` | `shared.templating.jinja` | `from shared.templating.jinja import render_html, render_text` |
| `psycopg` AsyncConnection (reads) | `shared.db.read_async` | `from shared.db.read_async import gather_reads, run_reads` |

## 2.5 Reglas

- **SIEMPRE** los `__init__.py` nuevos quedan VACÍOS (sin barrels).
- **SIEMPRE** boto3/jinja2/psycopg-async se importan LAZY dentro de la función.
- **SIEMPRE** `read_async` es SÓLO para reads (idempotentes); NUNCA escrituras.
- **NUNCA** `import boto3` / `import jinja2` en ningún `core/` de service.

## Archivos afectados (fase 1)

### Crear
- `serverless/lambda/shared/aws/lambda_invoke.py` — invoke async + error.
  - Verificar: `serverless tests --type=unit --shared`
- `serverless/lambda/shared/templating/__init__.py` (vacío)
- `serverless/lambda/shared/templating/jinja.py` — render html/text.
- `serverless/lambda/shared/templating/pyproject.toml` — dep jinja2.
- `serverless/lambda/shared/db/read_async.py` — `gather_reads` + `run_reads`
  (patrón read concurrente; sin consumidor en este plan — ver §2.3).
- tests unit de los tres (ver arriba).
  - Verificar: `serverless lint-deps --shared` exit 0.

### Modificar
- (ninguno en esta fase; `shared.aws.s3` y `shared.aws.ses` se reutilizan
  tal cual).

[← 01 contexto](01-contexto-y-decision.md) · [siguiente: 03 devtools →](03-devtools-provisioning.md)
