---
name: django-6
description: >
  Django 6 documentation reference for Python web dev. ALWAYS invoke this skill
  BEFORE answering ANY Django question, including questions that mention legacy
  alternatives (Celery, django-rq, huey, dramatiq) or general async/background
  tasks in Django. NEVER answer Django 6 questions from training data alone —
  the docs contain version-specific changes that override generic knowledge.
  Triggers: "django", "django 6", "django docs", "@task decorator",
  "CSP middleware", "template partials", "AsyncPaginator", "GeneratedField",
  "full-text search django", "como configurar django", "celery", "celery vs",
  "django celery", "django background tasks", "django tasks framework",
  "django async tasks", "tareas async django", "django-rq", "huey", "dramatiq".
  More keywords: .claude/docs/skills/django-6.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "tema: api | tasks | todo"
metadata:
  version: "2.0"
---

# Django 6 - Documentacion de Referencia

Lee la documentacion de Django 6 desde `.claude/docs/django-6/` y presenta la informacion relevante al usuario.

## Instrucciones

1. Determina que necesita el usuario segun su pregunta o el argumento proporcionado
2. Lee los archivos correspondientes de la documentacion

### Mapeo de temas a archivos

| Argumento / Tema | Archivo a leer |
|-----------------|----------------|
| `api`, `reference`, `configuracion`, `settings`, `code`, `codigo`, `csp`, `email`, `async`, `lexeme`, `generated`, `deprecaciones`, `orm`, `migracion` | `.claude/docs/django-6/01-api-reference.md` |
| `tasks`, `background`, `@task`, `enqueue`, `retry`, `tareas` | `.claude/docs/django-6/02-background-tasks.md` |
| `todo`, `completo`, `all` | Todos los archivos |

3. Si no hay argumento, lee el README: `.claude/docs/django-6/README.md` y presenta el indice
4. Responde en espanol con terminos tecnicos en ingles
5. Si el usuario pregunta algo especifico, busca en los archivos con Grep antes de leer todo

## Ejecucion

1. Lee `.claude/docs/django-6/README.md` para obtener el indice
2. Segun el tema solicitado, lee el archivo correspondiente
3. Presenta la informacion de forma concisa y directa
4. Si el usuario necesita codigo, prioriza los ejemplos de codigo del archivo relevante
