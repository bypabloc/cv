[Anterior: 06-widgets-inlines-forms](06-widgets-inlines-forms.md) | [Volver: README](README.md)

# 07. Third-party Libraries 2025

> Librerias de terceros para mejorar el admin de Django: UI moderna, import/export, sorting, nested inlines, y mas.

## django-unfold (UI moderna)

La opcion mas popular en 2025 para modernizar la UI del admin sin cambiar la logica.

```
pip install django-unfold
```

```python
# settings.py
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.import_export',  # Si usas django-import-export
    'django.contrib.admin',
    # ...
]
```

Caracteristicas:
- UI moderna con Tailwind CSS (dark mode incluido)
- Sidebar responsive y customizable
- Dashboard con widgets y charts
- Compatible con todos los features nativos de Django admin
- Tabs en fieldsets
- Formularios mejorados (Select2, date pickers, toggles)
- No requiere cambiar ModelAdmin — funciona con lo existente

```python
from unfold.admin import ModelAdmin

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    # Misma API que django.contrib.admin.ModelAdmin
    list_display = ('name', 'status', 'created_at')

    # Feature de unfold: tabs en fieldsets
    fieldsets_tabs = True
```

Evaluacion:
- Pro: drop-in replacement, UX profesional, mantenido activamente
- Contra: agrega dependencia de Tailwind, puede conflictuar con CSS custom
- Ideal para: proyectos que necesitan admin presentable para stakeholders
- Evitar si: el admin es solo para devs y funciona bien con el default

## django-import-export

Import/export CSV, Excel, JSON desde el admin.

```
pip install django-import-export
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'import_export',
]

# admin.py
from import_export.admin import ImportExportModelAdmin
from import_export import resources

class CostRecordResource(resources.ModelResource):
    class Meta:
        model = CostRecord
        fields = ('id', 'user__username', 'provider__name',
                  'amount', 'currency', 'billed_date')
        export_order = fields

@admin.register(CostRecord)
class CostRecordAdmin(ImportExportModelAdmin):
    resource_classes = [CostRecordResource]
    list_display = ('user', 'provider', 'amount', 'billed_date')
```

Caracteristicas:
- Export a CSV, XLSX, JSON, YAML, TSV, HTML
- Import con preview y validacion antes de confirmar
- Dry run para validar sin guardar
- Hook `before_import_row()`, `after_import_row()` para transformaciones
- Soporte para FK (resolucion por natural key o PK)

```python
class CostRecordResource(resources.ModelResource):
    class Meta:
        model = CostRecord
        import_id_fields = ('id',)  # Campo para identificar updates vs creates
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Transformar datos antes de importar."""
        if 'amount' in row:
            row['amount'] = str(row['amount']).replace(',', '.')
```

Evaluacion:
- Pro: robusto, flexible, bien mantenido, formatos multiples
- Contra: import de archivos grandes puede ser lento (no async)
- Ideal para: migrar datos, exports para reportes, bulk updates

## django-admin-sortable2

Drag-and-drop reordering en list view e inlines.

```
pip install django-admin-sortable2
```

```python
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'scope', 'is_active')
    # Requiere campo de orden en el modelo (e.g., 'order' o 'position')

class OrderItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = OrderItem
    extra = 0
```

Modelo requiere campo de orden:

```python
class Category(TimestampedModel):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ['order']
```

Evaluacion:
- Pro: drag-and-drop nativo, funciona en list view e inlines
- Contra: requiere campo de orden en modelo, JS incluido puede conflictuar
- Ideal para: categories, items, cualquier cosa con orden manual

## django-nested-admin

Inlines dentro de inlines (multi-nivel).

```
pip install django-nested-admin
```

```python
import nested_admin

class OrderItemInline(nested_admin.NestedTabularInline):
    model = OrderItem
    extra = 0

class OrderInline(nested_admin.NestedStackedInline):
    model = Order
    inlines = [OrderItemInline]  # Inline DENTRO de inline
    extra = 0

@admin.register(Collection)
class CollectionAdmin(nested_admin.NestedModelAdmin):
    inlines = [OrderInline]
```

Evaluacion:
- Pro: resuelve limitacion nativa de Django (no nested inlines)
- Contra: complejidad de JS, puede ser lento con muchos niveles
- Ideal para: relaciones jerarquicas (Collection > Order > OrderItem)
- Evitar si: puedes resolver con `autocomplete_fields` o views separadas

## django-admin-interface

Customizacion visual del admin via DB (sin codigo).

```
pip install django-admin-interface
```

Permite desde el admin:
- Cambiar colores, logo, favicon
- Custom CSS via textarea en el admin
- Temas guardados en DB (switchable)
- Responsive sidebar

Evaluacion:
- Pro: no-code customization, ideal para clientes no-tecnicos
- Contra: overhead de queries para cargar tema en cada request
- Ideal para: admin que sera usado por no-tecnicos que quieren branding

## django-jazzmin

Tema Bootstrap 4 para el admin con sidebar moderna.

```
pip install django-jazzmin
```

```python
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    # ...
]

JAZZMIN_SETTINGS = {
    'site_title': 'Rezebra',
    'site_header': 'Rezebra Admin',
    'site_brand': 'Rezebra',
    'welcome_sign': 'Welcome to Rezebra',
    'show_sidebar': True,
    'navigation_expanded': False,
    'icons': {
        'products.Product': 'fas fa-box',
        'orders.Order': 'fas fa-shopping-cart',
    },
}
```

Evaluacion:
- Pro: facil setup, iconos Font Awesome, sidebar moderna
- Contra: Bootstrap 4 (no 5), menos activo que unfold en 2025
- Ideal para: upgrade rapido de look & feel sin mucho effort
- Alternativa moderna: django-unfold (Tailwind, mas activo)

## django-debug-toolbar

No es un tema, pero esencial para development del admin:

```
pip install django-debug-toolbar
```

```python
# settings/local.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']
```

Muestra:
- SQL queries ejecutadas (N+1 detection)
- Template rendering time
- Cache hits/misses
- Request/response headers

## django-extensions

Utilidades para desarrollo:

```
pip install django-extensions
```

Comandos utiles para admin:
- `show_urls` — lista todas las URLs (incluyendo admin custom)
- `graph_models` — genera diagrama ER de los modelos
- `shell_plus` — shell con auto-import de modelos
- `admin_generator` — genera codigo admin basico para todos los modelos

```bash
# Generar admin boilerplate automatico
python manage.py admin_generator products
```

## Comparacion rapida

| Libreria | Proposito | Mantenimiento 2025 | Complejidad |
|----------|-----------|--------------------|-------------|
| django-unfold | UI moderna (Tailwind) | Activo | Baja (drop-in) |
| django-import-export | CSV/Excel import/export | Activo | Media |
| django-admin-sortable2 | Drag-and-drop ordering | Activo | Baja |
| django-nested-admin | Nested inlines | Activo | Alta |
| django-admin-interface | No-code customization | Activo | Baja |
| django-jazzmin | Tema Bootstrap | Moderado | Baja |
| django-debug-toolbar | Debug/profiling | Activo | Baja |
| django-extensions | Dev utilities | Activo | Baja |

## Recomendaciones para rezebra

Para el proyecto rezebra, las librerias mas relevantes serian:

1. **django-import-export** — export de CostRecords, AuditLogs, Orders a CSV para analisis
2. **django-admin-sortable2** — ordering de Categories, items con orden manual
3. **django-debug-toolbar** — detectar N+1 queries en development
4. **django-unfold** — si se necesita admin presentable (evaluar si vale la dependencia)

No recomendadas actualmente:
- django-nested-admin — el proyecto usa admin views custom en vez de nested inlines
- django-jazzmin — django-unfold es la opcion mas moderna
- django-admin-interface — el branding se controla via templates

## Instalar sin romper

Antes de agregar cualquier libreria:

1. Verificar compatibilidad con Django 6 y Python 3.14
2. Agregar a `server/pyproject.toml` (`[project.dependencies]` con version pinned `==X.Y.Z`)
3. Regenerar lockfile: `uv lock --project server`
4. Rebuild container: `python devtools/run.py docker rebuild --service=server`
5. Agregar a `INSTALLED_APPS` en el orden correcto (antes o despues de `django.contrib.admin` segun docs)
6. Ejecutar tests: `python devtools/run.py test_runner --module=server --type=coverage`
7. Verificar que admin existente no se rompe (HTTP 200 en changelist y add views)

[Anterior: 06-widgets-inlines-forms](06-widgets-inlines-forms.md) | [Volver: README](README.md)
