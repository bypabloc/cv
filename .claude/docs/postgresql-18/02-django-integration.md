[Anterior: API Reference](01-api-reference.md) | [Volver al indice](README.md)

# PostgreSQL 18 - Integracion con Django

> Configuracion de Django 6 con PostgreSQL 18: psycopg3, UUIDv7, GeneratedField, full-text search y performance.

## DATABASES config con psycopg3

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "mydb"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "pool": True,           # connection pooling nativo
            "pool_min_size": 4,     # conexiones minimas en pool
            "pool_max_size": 10,    # conexiones maximas en pool
        },
    }
}
```

Django 6 auto-detecta psycopg3 si esta instalado. No requiere cambiar `ENGINE`.

## psycopg3 vs psycopg2

| Aspecto | psycopg2 | psycopg3 |
|---------|----------|----------|
| Paquete | `psycopg2-binary` | `psycopg[binary]` |
| Python | 3.7+ | 3.8+ |
| Async | No nativo | Nativo (`AsyncConnection`) |
| Connection pool | Externo (pgbouncer) | Built-in |
| COPY | `copy_expert()` | `copy()` con streaming |
| Pipeline mode | No | Si (batch queries) |
| Prepared statements | Limitado | Automatico |
| Mantenimiento | Legacy (solo security fixes) | Activo |
| Django support | Django 3.2+ | Django 4.2+ |
| Recomendacion | Proyectos legacy | **Proyectos nuevos** |

### Migracion psycopg2 a psycopg3

```bash
# 1. Cambiar dependencia
uv remove psycopg2-binary
uv add "psycopg[binary]>=3.2"

# 2. No se necesitan cambios en settings.py (auto-detectado)
# 3. Ejecutar tests para verificar
pytest tests/ -v
```

## UUIDv7 como Primary Key

### Custom field para Django

```python
# myapp/fields.py
import uuid
from django.db import models


class UUIDv7Field(models.UUIDField):
    """UUID v7 field que usa la funcion nativa de PostgreSQL 18."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", uuid.uuid7)  # Python 3.14+
        kwargs.setdefault("editable", False)
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return "uuid"

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        return str(value)
```

### Alternativa con db_default (PostgreSQL nativo)

```python
from django.db import models
from django.db.models.functions import Random

class Event(models.Model):
    # Usa uuidv7() de PostgreSQL 18 directamente
    id = models.UUIDField(
        primary_key=True,
        db_default=models.Func(function="uuidv7"),
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]  # uuidv7 es cronologico, ordering por id = ordering por tiempo
```

### Modelo base reutilizable

```python
# myapp/models/base.py
from django.db import models


class UUIDv7Model(models.Model):
    """Modelo base con UUIDv7 como primary key."""

    id = models.UUIDField(
        primary_key=True,
        db_default=models.Func(function="uuidv7"),
        editable=False,
    )

    class Meta:
        abstract = True


# Uso
class Product(UUIDv7Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

## GeneratedField + Virtual Columns

Django `GeneratedField` con PostgreSQL 18 virtual generated columns:

```python
from django.db import models

class Invoice(models.Model):
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.19)

    # Virtual: calculado al leer, no almacenado en disco
    total = models.GeneratedField(
        expression=models.F("subtotal") * (1 + models.F("tax_rate")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=False,  # False = virtual (PG 18+), True = stored
    )

    # Stored: calculado al escribir, almacenado, indexable
    search_text = models.GeneratedField(
        expression=models.functions.Concat(
            "customer_name", models.Value(" "), "invoice_number"
        ),
        output_field=models.CharField(max_length=500),
        db_persist=True,  # stored = permite crear indice
    )
```

| `db_persist` | Tipo | Almacenamiento | Indexable | PG minimo |
|-------------|------|---------------|-----------|-----------|
| `False` | Virtual | No | No | 18 |
| `True` | Stored | Si | Si | 12 |

**Auto-refresh en Django 6**: Despues de `save()`, los `GeneratedField` se refrescan automaticamente (sin necesidad de `refresh_from_db()`).

## Full-Text Search con Lexeme

```python
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
    Lexeme,
)

# Busqueda basica
results = Article.objects.annotate(
    search=SearchVector("title", "body", config="spanish"),
).filter(
    search=SearchQuery("django postgresql", config="spanish"),
)

# Con ranking
results = Article.objects.annotate(
    search=SearchVector("title", weight="A") + SearchVector("body", weight="B"),
    rank=SearchRank(
        SearchVector("title", weight="A") + SearchVector("body", weight="B"),
        SearchQuery("django"),
    ),
).filter(rank__gte=0.1).order_by("-rank")

# Con Lexeme (nuevo en Django 6)
query = SearchQuery(
    Lexeme("python", weight="A", prefix=True)
    & Lexeme("django", weight="B")
)
results = Article.objects.annotate(
    search=SearchVector("title", "body"),
).filter(search=query)
```

### Indice GIN para full-text search

```python
from django.contrib.postgres.indexes import GinIndex

class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        indexes = [
            GinIndex(
                SearchVector("title", "body", config="spanish"),
                name="article_search_idx",
            ),
        ]
```

## Indices y Skip Scan

```python
from django.db import models

class Order(models.Model):
    status = models.CharField(max_length=20, db_index=True)  # baja cardinalidad
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            # PG 18 skip scan optimiza queries que no filtran por 'status'
            models.Index(fields=["status", "created_at"], name="idx_order_status_date"),

            # BRIN para tablas grandes con datos cronologicos
            # BrinIndex no existe en Django, usar raw SQL o RunSQL
        ]
```

## Extensiones utiles

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.postgres",  # Requerido para features PG
    # ...
]
```

### Habilitar extensiones via migracion

```python
from django.contrib.postgres.operations import (
    CreateExtension,
    BloomExtension,
    BtreeGinExtension,
    TrigramExtension,
)
from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        CreateExtension("pgcrypto"),       # Encriptacion
        TrigramExtension(),                # pg_trgm para busqueda fuzzy
        BtreeGinExtension(),               # btree_gin para indices compuestos
        CreateExtension("hstore"),         # Key-value pairs
    ]
```

| Extension | Uso | Django support |
|-----------|-----|---------------|
| `pgcrypto` | UUIDs, encriptacion | `CryptoExtension` |
| `pg_trgm` | Busqueda fuzzy, similarity | `TrigramExtension` |
| `btree_gin` | Indices GIN en columnas btree | `BtreeGinExtension` |
| `hstore` | Key-value store | `HStoreExtension` |
| `PostGIS` | Datos geograficos | `django.contrib.gis` |

## Performance tips

```python
# 1. select_related para FK (JOIN)
orders = Order.objects.select_related("customer", "product").all()

# 2. prefetch_related para M2M (query separada)
articles = Article.objects.prefetch_related("tags", "comments").all()

# 3. only/defer para campos grandes
products = Product.objects.only("id", "name", "price").all()

# 4. iterator para datasets grandes
for order in Order.objects.all().iterator(chunk_size=1000):
    process(order)

# 5. bulk operations
Product.objects.bulk_create(products, batch_size=500)
Product.objects.bulk_update(products, ["price", "stock"], batch_size=500)

# 6. explain() para analizar queries
qs = Product.objects.filter(price__gt=100)
print(qs.explain(analyze=True, verbose=True))
```

---

[Anterior: API Reference](01-api-reference.md) | [Volver al indice](README.md)
