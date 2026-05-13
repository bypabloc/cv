[Volver al indice](README.md) | [Siguiente: Background Tasks](02-background-tasks.md)

# Django 6 - API Reference

> Referencia completa de Django 6.0: instalacion, settings, nuevas features y guia de migracion.

## Identificacion

| Campo | Valor |
|-------|-------|
| Nombre | Django |
| Version | 6.0.3 (ultima estable) |
| Release | 3 diciembre 2025 |
| Soporte activo | Hasta agosto 2026 |
| Soporte seguridad | Hasta abril 2027 |
| Python minimo | 3.12 |
| LTS | No (5.2 es LTS hasta abril 2028) |
| Documentacion | docs.djangoproject.com |

## Instalacion

```bash
# Con pip
pip install Django==6.0.3

# Con uv (recomendado)
uv add Django==6.0.3

# Verificar version
python -c "import django; print(django.VERSION)"
```

### Dependencias recomendadas para PostgreSQL

```txt
# requirements.txt
Django==6.0.3
psycopg[binary]==3.2.6    # psycopg3, NO psycopg2
```

## Settings criticos

### DEFAULT_AUTO_FIELD

Django 6 cambia el default de `AutoField` (int32) a `BigAutoField` (int64):

```python
# settings.py - ya es el default, pero explicitar para claridad
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

**Migracion**: Si tienes proyectos con `AutoField`, agrega esto en `AppConfig`:

```python
class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"  # mantener legacy
```

### DATABASES con psycopg3

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "mydb"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "pool": True,  # connection pooling nativo de psycopg3
        },
    }
}
```

psycopg3 es auto-detectado por Django 6 si esta instalado. No requiere `ENGINE` especial.

## CSP Middleware (Content Security Policy)

Soporte nativo contra XSS. Reemplaza el paquete `django-csp`.

### Configuracion

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.security.ContentSecurityPolicyMiddleware",  # nuevo
    # ...
]

SECURE_CSP = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "https://cdn.example.com"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "connect-src": ["'self'"],
}

# Para modo report-only (no bloquea, solo reporta)
SECURE_CSP_REPORT_ONLY = {
    "default-src": ["'self'"],
    "report-uri": "/csp-report/",
}
```

### Nonces automaticos

```python
# En templates
<script nonce="{{ request.csp_nonce }}">
    // JavaScript seguro
</script>
```

### Decoradores per-view

```python
from django.views.decorators.csp import csp_override

@csp_override({"script-src": ["'self'", "'unsafe-eval'"]})
def admin_view(request):
    # Vista con CSP custom
    pass
```

## Template Partials

Definir y reutilizar fragmentos de template sin crear archivos separados:

```html
<!-- base_page.html -->
{% partialdef sidebar %}
  <nav class="sidebar">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/about/">About</a></li>
    </ul>
  </nav>
{% endpartialdef %}

<!-- Usar en el mismo template -->
<div class="layout">
  {% partial sidebar %}
  <main>{{ content }}</main>
</div>

<!-- O incluir desde otro template -->
{% partial "base_page.html:sidebar" %}
```

Util para componentes HTMX que necesitan re-renderizar solo una parte.

## Email API modernizada

Django 6 migra a `email.message.EmailMessage` de Python 3.6+:

```python
from django.core.mail import EmailMessage

# API sin cambios para uso basico
email = EmailMessage(
    subject="Bienvenido",
    body="Contenido del email",
    from_email="noreply@example.com",
    to=["user@example.com"],
)
email.send()
```

**Deprecados**: `SafeMIMEText`, `SafeMIMEMultipart`. Los argumentos opcionales de `send_mail()` ahora son keyword-only.

## AsyncPaginator

Paginacion nativa para vistas async:

```python
from django.core.paginator import AsyncPaginator

async def product_list(request):
    queryset = Product.objects.all()
    paginator = AsyncPaginator(queryset, per_page=25)
    page = await paginator.aget_page(request.GET.get("page", 1))
    return render(request, "products/list.html", {"page": page})
```

## Lexeme y Full-Text Search

Nuevo tipo `Lexeme` para full-text search en PostgreSQL:

```python
from django.contrib.postgres.search import SearchVector, SearchQuery, Lexeme

# Busqueda con lexemes personalizados
query = SearchQuery(Lexeme("python", weight="A") & Lexeme("django", weight="B"))
results = Article.objects.annotate(
    search=SearchVector("title", "body"),
).filter(search=query)
```

## GeneratedField auto-refresh

`GeneratedField` y `db_default` ahora se refrescan automaticamente despues de `save()`:

```python
from django.db import models

class Product(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.19)
    total = models.GeneratedField(
        expression=models.F("price") * (1 + models.F("tax_rate")),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )

# Despues de save(), product.total tiene el valor calculado (sin refresh_from_db)
product = Product(price=100, tax_rate=0.19)
product.save()
print(product.total)  # 119.00 -- auto-refreshed
```

Funciona en PostgreSQL, SQLite y Oracle.

## ORM: Nuevas funcionalidades

### StringAgg cross-database

```python
from django.db.models.functions import StringAgg

# Funciona en PostgreSQL, SQLite, MySQL
tags = Article.objects.values("author").annotate(
    all_tags=StringAgg("tags__name", delimiter=", ")
)
```

### AnyValue aggregate

```python
from django.db.models import AnyValue

# Obtener un valor arbitrario de un grupo (util con GROUP BY)
results = Order.objects.values("customer_id").annotate(
    sample_product=AnyValue("product__name")
)
```

### Model.NotUpdated exception

```python
try:
    updated = Product.objects.filter(id=1, version=5).update(
        name="New Name", version=6
    )
    if updated == 0:
        raise Product.NotUpdated("Concurrent modification detected")
except Product.NotUpdated:
    # Manejar conflicto de concurrencia
    pass
```

## Deprecaciones y removals

### Removido en Django 6.0

| Eliminado | Reemplazo |
|-----------|-----------|
| `force_text()` | `force_str()` |
| `smart_text()` | `smart_str()` |
| `SafeMIMEText` | `email.message.EmailMessage` |
| Python 3.10/3.11 | Python 3.12+ |
| MariaDB 10.5 | MariaDB 10.6+ |
| `as_sql()` retornando listas | Debe retornar tuplas |

### Deprecado (removido en Django 7)

| Deprecado | Reemplazo |
|-----------|-----------|
| `SafeMIMEMultipart` | `email.message.EmailMessage` |
| Argumentos posicionales en `send_mail()` | Usar keyword arguments |

## Compatibilidad

| Componente | Versiones soportadas |
|------------|---------------------|
| Python | 3.12, 3.13 |
| PostgreSQL | 14, 15, 16, 17, 18 |
| MySQL | 8.0, 8.4, 9.0 |
| MariaDB | 10.6, 10.11, 11.x |
| SQLite | 3.39+ |

## Django 6.1 (en desarrollo)

Features anticipadas para agosto 2026:

- **Field Fetch Modes**: `FETCH_PEERS` elimina N+1 queries automaticamente, `FETCH_RAISE` previene acceso lazy
- **Database-level delete**: `DB_CASCADE`, `DB_SET_NULL`, `DB_SET_DEFAULT`
- PostgreSQL 15+ minimo, MySQL 8.4+ minimo

---

[Volver al indice](README.md) | [Siguiente: Background Tasks](02-background-tasks.md)
