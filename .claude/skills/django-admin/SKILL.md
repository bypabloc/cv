---
name: django-admin
description: >
  Django 6 admin customization docs (dynamic admin, JS, mixins, widgets,
  inlines, performance, security). ALWAYS invoke for Django admin reference.
  Triggers: "django admin", "admin custom", "admin dinamico", "admin
  javascript", "admin mixin", "admin widget", "admin inline", "admin
  permissions", "mejorar admin", "admin avanzado". More keywords:
  .claude/docs/skills/django-admin.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "tema: dynamic | js | views | mixins | performance | widgets | libraries | all"
metadata:
  version: "1.0"
---

# Django Admin Avanzado - Documentacion de Referencia

Lee la documentacion de Django Admin avanzado desde `.claude/docs/django-admin/` y presenta la informacion relevante al usuario.

## Instrucciones

1. Determina que necesita el usuario segun su pregunta o el argumento proporcionado
2. Lee los archivos correspondientes de la documentacion

### Mapeo de temas a archivos

| Argumento / Tema | Archivo a leer |
|-----------------|----------------|
| `dynamic`, `dinamico`, `fieldsets`, `list_display`, `get_`, `conditional` | `.claude/docs/django-admin/01-dynamic-admin.md` |
| `ts`, `typescript`, `vanilla`, `fetch`, `htmx`, `alpine`, `es modules`, `esbuild` | `.claude/docs/django-admin/02-typescript-moderno.md` |
| `views`, `vistas`, `custom views`, `dashboard`, `get_urls`, `templates` | `.claude/docs/django-admin/03-custom-views-templates.md` |
| `mixins`, `reusable`, `reutilizable`, `base class`, `patterns`, `escalable` | `.claude/docs/django-admin/04-reusable-patterns.md` |
| `performance`, `security`, `seguridad`, `permissions`, `N+1`, `optimize` | `.claude/docs/django-admin/05-performance-security.md` |
| `widgets`, `inlines`, `forms`, `formsets`, `sortable`, `nested` | `.claude/docs/django-admin/06-widgets-inlines-forms.md` |
| `libraries`, `librerias`, `unfold`, `jazzmin`, `import-export`, `third-party` | `.claude/docs/django-admin/07-third-party-libraries.md` |
| `all`, `todo`, `completo` | Todos los archivos en orden |

3. Si no hay argumento, lee el README: `.claude/docs/django-admin/README.md` y presenta el indice
4. Responde en espanol con terminos tecnicos en ingles
5. Si el usuario pregunta algo especifico, busca en los archivos con Grep antes de leer todo
6. Cuando muestres ejemplos de codigo, adaptalos al contexto del proyecto rezebra (TimestampedModel, UUIDv7, etc.)
7. Para patrones JavaScript, SIEMPRE mostrar vanilla JS (NO jQuery) compatible con Django admin
