---
description: "Estandares Django 6 para server/: estructura de app, modelos thin, admin, providers, testing y seguridad"
globs: "server/**/*.py"
---

# Django Development Standards - Rezebra

> Reglas para el proyecto Django 6 en server/.

## Estructura de app (OBLIGATORIO)

> Reglas genericas de estructura de archivos y `__init__.py`: ver `python.md`. Aqui solo Django app structure.

- Django project en `server/`, config en `server/config/`
- Apps en `server/apps/<nombre>/`
- Modelos base en `server/common/models.py` (UUIDv7Model, TimestampedModel)
- Excepciones base en `server/common/exceptions.py` (ApplicationError)
- Enums compartidos en `server/common/enums.py`
- Archivos monoliticos (`models.py`, `admin.py`, `enums.py`, `services.py`) PROHIBIDOS — usar carpetas (`models/`, `admin/`, `enums/`, `services/`, `selectors/`, `tasks/`) con `__init__.py` que solo re-exporta

### Estructura completa de una app

```
server/apps/<nombre>/
├── models/                    # Un modelo por archivo
│   ├── __init__.py            # Re-exports
│   └── <model_name>.py       # Model + QuerySet + Manager
├── services/                  # Logica de escritura (create, update, delete)
│   ├── __init__.py
│   └── <dominio>.py           # Funciones con keyword-only args (*)
├── selectors/                 # Logica de lectura (get, list, filter)
│   ├── __init__.py
│   └── <dominio>_queries.py   # Retornan QuerySet, nunca escriben
├── admin/                     # Un admin class por archivo
│   ├── __init__.py
│   └── <model_name>.py       # @admin.register(Model)
├── serializers/               # DRF serializers
│   ├── __init__.py
│   ├── input.py               # Serializer puro para validacion
│   └── output.py              # ModelSerializer read-only para respuesta
├── views/                     # Thin views (delegan a services/selectors)
│   ├── __init__.py
│   └── <dominio>.py
├── tasks/                     # Background tasks (thin wrappers de services)
│   ├── __init__.py
│   └── <dominio>.py
├── enums/                     # TextChoices/IntegerChoices
│   ├── __init__.py
│   └── <nombre>.py
├── migrations/
├── urls.py
├── apps.py
├── constants.py               # Constantes de la app (UPPER_SNAKE_CASE)
└── exceptions.py              # Excepciones custom heredando de ApplicationError
```

## Modelos (thin models)

- SIEMPRE heredar de `TimestampedModel` (UUIDv7 PK + created_at/updated_at)
- PKs son UUIDv7 nativo de PostgreSQL 18 via `db_default=Func(function="uuidv7")`
- ForeignKey a User: usar `settings.AUTH_USER_MODEL`, no `User` directo
- ForeignKey y M2M: SIEMPRE definir `related_name` explicito (ver abajo)
- `db_default` para defaults a nivel de base de datos (mejor integridad)
- Django 6: `CheckConstraint` usa `condition=` (no `check=` que fue removido)
- JSONField para datos semi-estructurados
- GeneratedField(db_persist=False) para columnas virtuales PG18

### related_name (obligatorio en FK y M2M)

Definir `related_name` explicito permite consultas reversas legibles desde el
modelo padre. Si no se necesita relacion reversa, usar `related_name='+'` para
que Django no la cree (ahorra memoria y evita ambiguedad).

```python
# Correcto
class Appointment(TimestampedModel):
    consumer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
    )

# Uso de la relacion reversa
user.appointments.all()
user.appointments.filter(status=AppointmentStatus.CONFIRMED)

# Si no se necesita reversa
class AuditLog(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
```

### Que va en el modelo

- Definicion de campos y `Meta` (constraints, indexes, ordering)
- `__str__()` obligatorio
- `clean()` para validacion a nivel de instancia
- Propiedades simples calculadas (sin queries a DB)
- Custom QuerySet y Manager

### Que NO va en el modelo (va en services)

- Logica de negocio compleja
- Llamadas a APIs externas
- Validaciones que involucran multiples modelos
- Logica de notificaciones
- Verificaciones de permisos

### Custom QuerySet pattern

```python
from django.db import models

class AppointmentQuerySet(models.QuerySet):
    def active(self) -> AppointmentQuerySet:
        return self.exclude(status=AppointmentStatus.CANCELLED)

    def for_business(self, business: Business) -> AppointmentQuerySet:
        return self.filter(business=business)

    def with_related(self) -> AppointmentQuerySet:
        return self.select_related('consumer', 'service', 'staff')

class Appointment(TimestampedModel):
    objects = AppointmentQuerySet.as_manager()
```

## QuerySet optimization (CRITICO)

```python
# SIEMPRE select_related para FK/OneToOne
queryset.select_related('author', 'category')

# SIEMPRE prefetch_related para M2M/reverse FK
queryset.prefetch_related('tags', 'comments')

# .exists() en vez de .count() > 0
if queryset.exists(): ...

# .only()/.defer() para modelos grandes
queryset.only('id', 'title', 'created_at')

# F() expressions para updates atomicos
from django.db.models import F
Model.objects.filter(pk=1).update(count=F('count') + 1)

# bulk operations con batch_size
Model.objects.bulk_create(objects, batch_size=1000)
Model.objects.bulk_update(objects, ['field1'], batch_size=1000)
```

## Admin

- `@admin.register(Model)` decorator en vez de `admin.site.register()`
- SIEMPRE definir `list_display`, `list_filter`, `search_fields`
- `readonly_fields` para campos computados/generados
- `autocomplete_fields` para FK con muchas opciones
- `list_select_related` para prevenir N+1 en lista
- `fieldsets` para agrupacion organizada
- Inlines para relaciones M2M through
- **JSONField en admin SIEMPRE con `JSONEditorWidget`** de `django-json-widget` (NUNCA Textarea plano):

```python
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

formfield_overrides = {
    models.JSONField: {
        'widget': JSONEditorWidget(
            options={'mode': 'code', 'modes': ['code', 'tree']},
        ),
    },
}
```

## Enums

- Preferir `TextChoices` sobre `IntegerChoices` (legible en DB, auto-documentado)
- `IntegerChoices` solo para columnas con millones de filas donde el rendimiento importa
- Archivo unico `enums.py` si son 3 o menos enums simples
- Carpeta `enums/` si son mas de 3 o tienen metodos custom

## Background Tasks

- Import de service functions DENTRO del body (evitar circular imports)
- Tasks son wrappers thin de services, no logica directa
- Retornar resultados serializables (dict, no model instances)

## Signals

- EVITAR signals cuando sea posible — preferir llamadas directas en services
- Usar solo para: comunicacion cross-app sin circular deps, audit logging, cache invalidation
- NUNCA para logica de negocio

## Constants

- Constantes de app en `constants.py` (no en models ni settings)
- Constantes de proyecto en `common/constants.py`
- Valores dependientes del entorno en settings (no en constants)

## Migrations

- `0001_initial` auto-generadas via `makemigrations`
- Seeds via `RunPython` en migrations numeradas (0002_seed_*)
- Seeds siempre reversibles (reverse function que borra lo insertado)
- Usar `apps.get_model()` en migrations, no imports directos
- **OBLIGATORIO**: Despues de crear/modificar migration, ejecutar `python devtools/run.py docker migrate --env=local`

## Providers (Factory Pattern)

- Base: `generation/providers/base.py` (BaseProvider ABC)
- Adapters: archivos por proveedor (wrappean APIs externas)
- Registry: `get_provider(name)` retorna el adapter correcto
- NO instanciar clients directamente, siempre via factory
- Dependency injection en services para testability

## Testing

- Infraestructura en `server/tests/` con unified runner
- Ejecutar: `cd server && python tests/run.py --type unit|integration|feature`
- pytest-django con `--import-mode=importlib`
- pytest-bdd para feature tests con flujos cross-app (Gherkin opcional)
- Settings de test: `config.settings.test` (SQLite in-memory)
- Markers estrictos: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.feature`, `@pytest.mark.slow`
- factory-boy para fixtures (composable, explicito)
- hypothesis para property-based testing en validaciones (RUT chileno, RUC peruano, slots de disponibilidad)
- Mockear APIs externas (providers) en conftest.py
- Testear services y selectors directamente (unit), views completas (integration), flujos negocio (feature con Gherkin si aplica)

### BDD-style en docstring (obligatorio)

Mantener AAA como estructura del cuerpo. El docstring describe el comportamiento
en formato Given/When/Then. Convencion completa: ver `python.md` (seccion BDD-style)
y `ai-testing-independence.md`.

### Unit tests (path mirroring)

- Ubicacion: `tests/unit/src/` espeja la estructura de `server/`
- Archivos SIN prefijo `test_` (descubiertos via `pytest_collect_file` hook)
- `pytestmark = pytest.mark.unit` obligatorio en cada archivo
- Asserts EXACTOS (enforced por hook `weak_assertion`); ver `ai-testing-independence.md`

### Integration tests (por seccion)

- Ubicacion: `tests/integration/<seccion>/`
- `pytestmark = pytest.mark.integration` obligatorio
- Ejecutar seccion: `python tests/run.py --type integration --section generation`

### Feature tests (pytest-bdd, opcional)

- Ubicacion: `tests/feature/<dominio>/` (DRF APIClient + seed_db)
- `pytestmark = pytest.mark.feature`
- Para flujos que cruzan >= 2 apps, usar Gherkin:
  - `tests/feature/<dominio>/features/<feature>.feature` (humano-redactado)
  - `tests/feature/<dominio>/test_<feature>.py` (steps via `pytest_bdd.scenarios()`)
- Para flujos atomicos en una sola app, AAA + docstring BDD del unit test es suficiente
- Convenciones detalladas en `feature-tests.md`

### Mutation testing (calidad de tests)

Coverage 80% no demuestra que los tests maten bugs. Mutation testing si.

```bash
python devtools/run.py mutation_testing --paths=apps/appointments
```

Thresholds: 85% critical (`apps/appointments`, `apps/auth`), 70% standard,
30% experimental. Config en `devtools/mutation_testing/config.py`. Pre-push step
`mutation_testing` opt-in via `.git-hooks/config.json` (default off).

## Docker

- Desarrollo: `python devtools/run.py docker up --env=local`
- Entrypoint ejecuta: makemigrations + migrate + collectstatic
- Volumes bind-mount `server/` para hot-reload
- PG18 con PGDATA custom en volume nombrado
- Multi-ambiente: local (9976), test (9977); dockerfiles para dev y prod preparados

## Seguridad

- NUNCA `|safe` en templates a menos que sea absolutamente necesario
- Validar TODO input de usuario en serializer/form layer
- Produccion: `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- NUNCA `CORS_ALLOW_ALL_ORIGINS=True` en produccion
- Rate limiting para APIs publicas
