# Django 6 - Referencia Tecnica

> Framework web Python 3.12+ con Background Tasks nativo, CSP middleware, Template Partials y AsyncPaginator.

## Contenido

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| API, settings y features | [01-api-reference.md](01-api-reference.md) | Configurar proyecto, CSP, Template Partials, Email, AsyncPaginator, Lexeme |
| Background Tasks | [02-background-tasks.md](02-background-tasks.md) | @task decorator, enqueue, retry, comparacion con Celery |

## Reglas criticas

- SIEMPRE usar Python 3.12+ (minimo obligatorio en Django 6)
- SIEMPRE usar `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` (default en Django 6)
- SIEMPRE usar psycopg3 (`psycopg[binary]`) en lugar de psycopg2
- SIEMPRE usar `@task` decorator para tareas simples en background
- NUNCA usar `django.utils.encoding.force_text` (removido en Django 6)
- NUNCA usar `SafeMIMEText`/`SafeMIMEMultipart` (deprecados, usar `email.message.EmailMessage`)
- PREFERIR `AsyncPaginator` para paginacion en vistas async

## Navegacion

Contexto padre: [CLAUDE.md](../../../CLAUDE.md)
