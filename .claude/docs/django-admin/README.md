# Django Admin Avanzado

> Guia completa para crear admin custom dinamicos, escalables y reutilizables con Django 6 y JavaScript moderno.

## Contenido

| Capitulo | Archivo | Cuando leer |
|----------|---------|-------------|
| 01. Dynamic Admin Configuration | [01-dynamic-admin.md](01-dynamic-admin.md) | Cuando necesites fieldsets condicionales, list_display dinamico, readonly fields por estado, o inlines condicionales |
| 02. TypeScript Moderno en Admin | [02-typescript-moderno.md](02-typescript-moderno.md) | Cuando necesites interactividad: toggle de campos, AJAX tipado, HTMX, Alpine.js, ES modules, o widgets con TypeScript strict |
| 03. Custom Views y Templates | [03-custom-views-templates.md](03-custom-views-templates.md) | Cuando necesites dashboards, paginas wizard, vistas custom con `get_urls()`, o override de templates |
| 04. Reusable Patterns y Mixins | [04-reusable-patterns.md](04-reusable-patterns.md) | Cuando necesites mixins reutilizables, base classes, export CSV, audit log, soft delete, o admin site custom |
| 05. Performance y Security | [05-performance-security.md](05-performance-security.md) | Cuando necesites optimizar queries, prevenir N+1, permisos granulares, o field-level permissions |
| 06. Widgets, Inlines y Forms | [06-widgets-inlines-forms.md](06-widgets-inlines-forms.md) | Cuando necesites widgets custom, inlines dinamicos, formsets, sortable inlines, o nested inlines |
| 07. Third-party Libraries 2025 | [07-third-party-libraries.md](07-third-party-libraries.md) | Cuando quieras evaluar django-unfold, jazzmin, import-export, admin-sortable2, u otras librerias |

## Reglas criticas

- SIEMPRE TypeScript strict — compilar a JS via esbuild, NUNCA depender de jQuery
- SIEMPRE `format_html()` — NUNCA `mark_safe()` con datos de usuario
- SIEMPRE `self.admin_site.admin_view()` para wrappear custom views — previene acceso no autenticado
- SIEMPRE `select_related`/`prefetch_related` en `get_queryset()` — previene N+1
- NUNCA logica de negocio en el admin — delegar a services/selectors
- NUNCA inline JS en `format_html()` para logica compleja — usar archivos `.ts` compilados via `Media` class
- TS source en `static-src/<app>/src/`, JS output en `static/<app>/js/` siguiendo patron del proyecto
- Typing obligatorio en todas las funciones: parametros y retorno explicitos

## Patrones del proyecto rezebra

El proyecto ya usa admin avanzados. Referencia:

| Archivo | Patron |
|---------|--------|
| `server/apps/products/admin/product.py` | `get_urls()`, custom views, `get_fieldsets()` condicional, `get_readonly_fields()`, `Media` JS, `format_html` badges, `changeform_view` con extra context |
| `server/apps/products/admin/forms.py` | Custom `ModelForm` con validacion, `clean()` override |
| `server/apps/products/admin/category_views.py` | Vistas admin standalone con templates custom |
| `server/apps/scheduler/admin/scheduled_api_call.py` | Form con campos inline (interval/crontab), `save()` override, JS toggle, actions custom |
| `server/apps/products/admin/widgets.py` | Custom widgets (`ImageCheckboxSelect`), `create_option()` override, `data-` attributes |
| `server/apps/products/static/products/js/image_selector.js` | Vanilla JS: filter, enforce limits, event delegation, dynamic counter |
| `server/apps/scheduler/static/scheduler/js/schedule_toggle.js` | Vanilla JS: show/hide fields condicionalmente |
| `server/apps/products/static/products/admin/randomize_fields.js` | Vanilla JS: randomize form fields, inject button in fieldset header |

## Navegacion

- Proyecto: [CLAUDE.md](../../../CLAUDE.md)
- Django 6: [django-6/README.md](../django-6/README.md)
- Django rules: [rules/django.md](../../rules/django.md)
