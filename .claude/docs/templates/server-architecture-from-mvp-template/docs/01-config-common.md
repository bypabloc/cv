# Config y Common - Settings, modelos base, enums

[Volver al indice](README.md)

> Configuracion Django y modelos base compartidos.

## Settings (config/settings/)

| Archivo | Proposito |
|---------|-----------|
| `base.py` | Settings comunes: INSTALLED_APPS, MIDDLEWARE, AUTH_USER_MODEL, DATABASES, REST_FRAMEWORK |
| `dev.py` | Override para desarrollo: DEBUG=True, CORS abierto, logging verbose |
| `prod.py` | Override para produccion: SECURE_SSL_REDIRECT, HSTS, cookies seguras |
| `test.py` | Override para pytest: SQLite in-memory, password hashers rapidos |

### Settings clave

```python
# base.py
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin', ..., 'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_json_widget',
    # Project
    'common',           # Necesario para management commands
    'apps.accounts',    # User custom
    'apps.items',       # Recurso ejemplo
    'apps.api',         # Router central
]

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

### URLs (config/urls.py)

- `/admin/` — Django admin
- `/api/v1/` — Router DRF (incluye apps con namespace)

## Modelos base (common/models.py)

### TimestampedModel

```python
class TimestampedModel(models.Model):
    """Abstract base model with UUIDv7 PK and timestamps."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_default=models.Func(function='uuidv7'),  # PG18 nativo
    )
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
```

**TODOS los modelos del proyecto heredan de TimestampedModel**, no de `models.Model` directamente.

## Excepciones base (common/exceptions.py)

```python
class ApplicationError(Exception):
    def __init__(self, message: str = '', extra: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra or {}
```

Cada app define excepciones propias heredando: `class ProductNotFoundError(ApplicationError): ...`

## Enums compartidos (common/enums.py)

Enums que aplican a multiples apps van aqui. Ejemplo: estados globales, roles de usuario.

## Management commands (common/management/commands/)

### seed_db

Carga fixtures con merge por ambiente.

```bash
# Carga fixtures default + overrides del ambiente
python devtools/run.py docker exec python manage.py seed_db --env=local
python devtools/run.py docker exec python manage.py seed_db --env=local --clear  # reset primero
```

Estructura de fixtures:
- `fixtures/default/*.json` — datos iniciales (14 archivos con prefijo numerico)
- `fixtures/local/*.json` — overrides para ambiente local
- `fixtures/test/*.json` — overrides para tests

Resolucion: por natural keys (e.g., User por email, Item por nombre).

## Reglas criticas

1. SIEMPRE heredar de `TimestampedModel`, nunca de `models.Model` directo
2. ForeignKey a User: SIEMPRE via `settings.AUTH_USER_MODEL`
3. Django 6: `CheckConstraint(condition=...)` (NO `check=` que fue removido)
4. `db_default=Func(function='uuidv7')` para UUIDv7 nativo PG18
5. Excepciones de dominio heredan de `common.exceptions.ApplicationError`
6. Settings sensibles SIEMPRE desde env vars (`os.environ.get(...)`)

[Volver al indice](README.md)
