# 03 — Shared foundations (portadores nuevos)

[← 02 fase 0](02-fase-0-medicion-coldstart.md) · [siguiente: 04 devtools →](04-devtools-provisioning.md)

> Fase 1. Crea los dos portadores `shared.*` que faltan para que el `core/` de
> los Lambdas nunca importe `boto3`/`jinja2` directo (provider-swappable).
> `shared.aws.s3` y `shared.aws.ses` YA existen y se reutilizan.

## 2.1 `shared.aws.lambda_invoke` (NUEVO)

Portador del cliente Lambda de boto3 para invocación async. Mismo patrón lazy
(PEP 562) que `shared.aws.ses`/`shared.aws.s3`.

### Crear
- `serverless/lambda/shared/aws/lambda_invoke.py`
  - `_client()` — `boto3.client('lambda', region_name=...)` lazy.
  - `__getattr__('lambda_client')` — PEP 562, crea al primer acceso.
  - `invoke_async(*, function_name: str, payload: dict) -> None` — hace
    `client.invoke(FunctionName=function_name, InvocationType='Event',
    Payload=json.dumps(payload, default=str).encode())`. NO espera respuesta;
    loggea `event_invoked` + métrica `LambdaInvokeOk`/`LambdaInvokeFailed`.
  - Una excepción se loggea y se **re-lanza** como `LambdaInvokeError` para que
    el caller decida (en `contact_form`/`auth`/`users` se captura y se degrada a
    un log — best-effort, NO rompe el request).
  - `LambdaInvokeError(Exception)` — error tipado.

### Tests (TDD primero)
- `shared/tests/unit/shared/aws/test_lambda_invoke_async.py` — Given un
  `function_name` + payload, When `invoke_async`, Then llama `client.invoke` con
  `InvocationType='Event'` y el Payload JSON exacto (assert exacto sobre los
  kwargs con un stub/mock del cliente).
- `shared/tests/unit/shared/aws/test_lambda_invoke_reexport.py` — el módulo
  expone `invoke_async` + `LambdaInvokeError`.

## 2.2 `shared.templating` (NUEVO — Jinja2)

Portador único de Jinja2. El `core/` de `send_email` NUNCA importa `jinja2`.

### Crear
- `serverless/lambda/shared/templating/__init__.py` — VACÍO (docstring-only).
- `serverless/lambda/shared/templating/jinja.py`
  - `render_html(template, ctx)` — `jinja2.Environment(autoescape=True)`
    (anti-XSS en las vars del visitante).
  - `render_text(template, ctx)` — Environment con `autoescape=False` para
    TXT/subject.
  - `StrictUndefined` → si falta una var del contexto, lanza
    `TemplateRenderError` (falla ruidoso en `send_email`, no envía un email con
    huecos).
  - `TemplateRenderError(Exception)` — envuelve `jinja2.TemplateError`.
  - Jinja2 se importa LAZY dentro de `render_*` (no en el top del módulo) para
    no penalizar el cold de un Lambda que importe `shared.templating` sin
    renderizar.
- `serverless/lambda/shared/templating/pyproject.toml` — declara `jinja2>=3.1`
  en `[project.dependencies]`. Sin `internal-deps` (salvo observability si
  loggea).

### Tests (TDD primero)
- `..._render_html_substitutes_vars.py` — `'<p>Hola {{ name }}</p>'` +
  `{name:'Pablo'}` → `'<p>Hola Pablo</p>'`.
- `..._escapes_html_in_html.py` — `{name:'<script>'}` → `&lt;script&gt;`.
- `..._text_does_not_escape.py` — `render_text` con `&` no escapa.
- `..._missing_var_raises.py` — `StrictUndefined` con var faltante →
  `TemplateRenderError` (assert exacto).

## 2.3 `shared.db.read_async` — DIFERIDO al plan del dashboard

> El read-async (gather de reads multi-query concurrentes) **se difiere**: NO
> tiene consumidor en este plan (contact_form/tracking_writer/send_email sólo
> escriben/envían; cv usa `@cached`, no reads concurrentes). El diagnóstico de
> cold start, además, confirmó que el cuello NO es la concurrencia de queries
> sino el wake de Neon + el fan-out de cv (atacado con cache, [07](07-cv-cache.md)).
> El consumidor real es el Lambda de lectura del dashboard
> (`docs/specs/analytics-dashboard-api`). **Se crea allí**, no aquí — evita
> código sin consumidor. Decisión revisable si surge un read multi-query en
> este scope.

## 2.4 Catálogo de portadores (actualizar la rule)

Agregar a la tabla de `.claude/rules/lambda-shared-imports.md` (lo hace la fase
7, archivo 09, pero se referencia aquí):

| Paquete externo | Portador | Import |
|---|---|---|
| `boto3` lambda client | `shared.aws.lambda_invoke` | `from shared.aws.lambda_invoke import invoke_async` |
| `jinja2` | `shared.templating.jinja` | `from shared.templating.jinja import render_html, render_text` |

## 2.5 Reglas

- **SIEMPRE** los `__init__.py` nuevos quedan VACÍOS (sin barrels).
- **SIEMPRE** boto3/jinja2 se importan LAZY dentro de la función portadora.
- **NUNCA** `import boto3` / `import jinja2` en ningún `core/` de service.

## Archivos afectados (fase 1)

### Crear
- `serverless/lambda/shared/aws/lambda_invoke.py` + tests.
- `serverless/lambda/shared/templating/{__init__.py,jinja.py,pyproject.toml}`
  + tests.
  - Verificar: `serverless tests --type=unit --shared` + `lint-deps --shared`.

### Modificar
- (ninguno; `shared.aws.s3`/`ses` se reutilizan tal cual).

[← 02 fase 0](02-fase-0-medicion-coldstart.md) · [siguiente: 04 devtools →](04-devtools-provisioning.md)
