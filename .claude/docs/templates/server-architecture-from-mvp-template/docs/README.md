# Server Architecture - Indice

> Referencia completa del Django 6 server en `server/`. Apps, modelos, providers, workflows y storage.

## Cuando leer cada capitulo

| Capitulo | Cuando leer |
|----------|-------------|
| [01-config-common.md](01-config-common.md) | Buscar settings, modelos base, enums compartidos, seed_db, paths |

## Arquitectura del server (overview)

```
server/
├── config/                   # Settings (base, dev, prod, test), URLs, WSGI/ASGI
├── common/                   # Modelos base, enums, utilities, management commands
│   ├── models.py             # TimestampedModel (UUIDv7 PK + timestamps)
│   ├── enums.py              # Enums compartidos
│   ├── exceptions.py         # ApplicationError base
│   └── management/commands/  # seed_db
├── apps/                     # Apps Django del dominio
│   ├── accounts/             # User model (custom AbstractUser + email login)
│   ├── items/                # Item model con Status/Category enums
│   └── api/                  # Router central /api/v1/
└── tests/                    # pytest infrastructure (unit + integration)
```

## Apps registradas

| App | Modelos principales | Descripcion |
|-----|---------------------|-------------|
| `accounts` | `User` (extends AbstractUser + TimestampedModel) | Autenticacion por email |
| `items` | `Item` (status: DRAFT/ACTIVE/ARCHIVED; category: GENERAL/TECHNOLOGY/BUSINESS/DESIGN) | Recurso de ejemplo del template |
| `api` | (sin modelos) | Router DRF central, expone `/api/v1/<app>/` |
| `common` | (abstract: TimestampedModel) | Modelos base, management commands |

## Patron de cada app

```
apps/<nombre>/
├── models/         # Un modelo por archivo
├── services/       # Logica de escritura (keyword-only args con *)
├── selectors/      # Logica de lectura (retornan QuerySet)
├── admin/          # Un admin class por archivo
├── serializers/    # input.py (validacion) y output.py (respuesta)
├── views/          # Thin views: delegan a services/selectors
├── exceptions.py   # Custom exceptions heredando de ApplicationError
└── urls.py         # URL patterns de la app
```

## Reglas criticas

- TODOS los modelos heredan de `common.models.TimestampedModel` (UUIDv7 PK)
- Services usan keyword-only args: `def create_x(*, user, name, ...)`
- Selectors NUNCA escriben — solo retornan QuerySet
- ForeignKey a User SIEMPRE via `settings.AUTH_USER_MODEL`
- Django 6: CheckConstraint usa `condition=` (NO `check=`)

## Navegacion

- [01-config-common.md](01-config-common.md) — Settings, modelos base, enums, seed_db
