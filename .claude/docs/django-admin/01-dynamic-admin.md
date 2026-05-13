[Anterior: README](README.md) | [Siguiente: 02-typescript-moderno](02-typescript-moderno.md)

# 01. Dynamic Admin Configuration

> Configuracion dinamica de ModelAdmin: fieldsets, list_display, readonly_fields, inlines y actions que cambian segun el contexto (usuario, permisos, estado del objeto).

## Metodos `get_*` del ModelAdmin

Django 6 ModelAdmin expone metodos `get_*()` que permiten retornar valores diferentes segun request/obj:

```python
class MyAdmin(admin.ModelAdmin):
    # Metodos dinamicos principales:
    # get_list_display(request) -> list[str]
    # get_list_filter(request) -> list
    # get_search_fields(request) -> list[str]
    # get_fieldsets(request, obj=None) -> list[tuple]
    # get_readonly_fields(request, obj=None) -> tuple[str, ...]
    # get_inline_instances(request, obj=None) -> list[InlineModelAdmin]
    # get_form(request, obj=None, **kwargs) -> type[ModelForm]
    # get_queryset(request) -> QuerySet
    # get_changeform_initial_data(request) -> dict
    # get_actions(request) -> dict
    # get_list_display_links(request, list_display) -> list | None
    # get_exclude(request, obj=None) -> list[str] | None
    # get_ordering(request) -> list[str]
    # get_paginator(request, queryset, per_page, ...) -> Paginator
    pass
```

## Dynamic `list_display` por permisos

```python
@admin.register(CostRecord)
class CostRecordAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        base = ['user', 'provider', 'amount', 'currency', 'billed_date']
        if request.user.has_perm('billing.view_cost_details'):
            base.insert(3, 'cost_tier')
            base.append('internal_notes')
        return base
```

## Conditional fieldsets por estado del objeto

Patron: mostrar fieldsets diferentes en add vs change, o segun el status del objeto.

```python
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        # Add view: solo campos basicos
        if obj is None:
            return [
                ('Product', {'fields': ['name', 'slug', 'visibility']}),
                ('Details', {'fields': self._detail_fields()}),
                ('Pricing', {'fields': ['price', 'currency']}),
            ]

        # Change view: campos completos + estado
        fieldsets = [
            ('Product', {
                'fields': ['created_by_display', 'name', 'slug',
                           'status', 'visibility'],
            }),
            ('Details', {'fields': self._detail_fields()}),
            ('Pricing', {'fields': ['price', 'currency']}),
        ]

        # Agregar seccion de imagenes solo si tiene imagen
        if obj.image_url:
            fieldsets.append(
                ('Images', {
                    'fields': ['image_preview', 'description_preview'],
                }),
            )

        return fieldsets
```

## Dynamic `readonly_fields`

Patron: campos editables en add, readonly en change (o segun status).

```python
_EDITABLE_ON_CHANGE = frozenset({'name', 'slug', 'visibility'})

_READONLY_ADD = ('created_by_display', 'image_preview')
_READONLY_CHANGE = (
    'created_by_display', 'status', 'sku',
    'image_preview',
)

def get_readonly_fields(self, request, obj=None):
    if obj is None:
        return self._READONLY_ADD
    return self._READONLY_CHANGE
```

Patron avanzado — readonly por status:

```python
def get_readonly_fields(self, request, obj=None):
    readonly = list(self._READONLY_BASE)
    if obj and obj.status in ('completed', 'archived'):
        # Bloquear TODOS los campos si esta completado/archivado
        readonly.extend(
            f.name for f in obj._meta.get_fields()
            if hasattr(f, 'name') and f.name not in readonly
        )
    return tuple(readonly)
```

## Conditional inlines

```python
def get_inline_instances(self, request, obj=None):
    """Solo mostrar inlines en change view, no en add."""
    if obj is None:
        return []
    return super().get_inline_instances(request, obj)
```

Patron avanzado — inlines por tipo de objeto:

```python
def get_inlines(self, request, obj=None):
    """Diferentes inlines segun schedule_type."""
    inlines = [RecentExecutionsInline]
    if obj and obj.schedule_type == 'crontab':
        inlines.append(CrontabDetailInline)
    elif obj and obj.schedule_type == 'interval':
        inlines.append(IntervalDetailInline)
    return inlines
```

## Dynamic actions

```python
def get_actions(self, request):
    actions = super().get_actions(request)
    # Remover delete para usuarios sin permiso especial
    if not request.user.has_perm('products.bulk_delete_product'):
        actions.pop('delete_selected', None)
    # Agregar acciones segun grupo
    if request.user.groups.filter(name='Content Managers').exists():
        actions['action_bulk_activate'] = (
            self.action_bulk_activate,
            'action_bulk_activate',
            'Activate selected',
        )
    return actions
```

## Dynamic `list_filter`

```python
def get_list_filter(self, request):
    filters = ['status', 'visibility']
    if request.user.is_superuser:
        filters.extend(['created_by', 'preferred_provider'])
    return filters
```

## `get_changeform_initial_data` para defaults inteligentes

```python
def get_changeform_initial_data(self, request):
    """Pre-fill con defaults del usuario o sistema."""
    initial = super().get_changeform_initial_data(request)
    if 'category' not in initial:
        from apps.catalog.models.category import Category
        default = Category.get_default()
        if default:
            initial['category'] = default.pk
    # Pre-fill created_by con usuario actual
    initial.setdefault('created_by', request.user.pk)
    return initial
```

## Dynamic `get_form` con inyeccion de request

Patron para pasar el request al form:

```python
def get_form(self, request, obj=None, **kwargs):
    form_class = super().get_form(request, obj, **kwargs)

    class FormWithRequest(form_class):
        def __init__(self_form, *args, **kw):
            super().__init__(*args, **kw)
            self_form.request = request

    return FormWithRequest
```

## `save_model` con auto-assign de usuario

```python
def save_model(self, request, obj, form, change):
    if not change:
        obj.created_by = request.user
    super().save_model(request, obj, form, change)
```

## `response_add` / `response_change` para custom redirects

```python
from django.http import HttpResponseRedirect
from django.urls import reverse

def response_add(self, request, obj, post_url_continue=None):
    """Redirect a pagina de procesamiento despues de crear producto."""
    if '_process' in request.POST:
        url = reverse('admin:products_product_process_progress')
        return HttpResponseRedirect(f'{url}?ids={obj.pk}')
    return super().response_add(request, obj, post_url_continue)
```

## `changeform_view` para inyectar extra context

```python
def changeform_view(self, request, object_id=None,
                    form_url='', extra_context=None):
    extra_context = extra_context or {}
    if object_id:
        extra_context['related_groups'] = self._get_related_groups(object_id)
        extra_context['can_process'] = request.user.has_perm(
            'products.process_product',
        )
    return super().changeform_view(
        request, object_id, form_url, extra_context,
    )
```

## Patron completo: Admin con multiples niveles de dinamismo

```python
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        cols = ['title', 'status_badge', 'category', 'scheduled_at']
        if request.user.is_superuser:
            cols.insert(1, 'author')
        return cols

    def get_fieldsets(self, request, obj=None):
        base = [('Content', {'fields': ['title', 'body', 'product']})]
        if obj is None:
            base.append(('Category', {'fields': ['category']}))
        else:
            base.append(('Category', {
                'fields': ['category', 'status', 'completed_at'],
            }))
            if obj.status == 'draft':
                base.append(('Schedule', {
                    'fields': ['scheduled_at'],
                    'classes': ('collapse',),
                }))
        return base

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        readonly = ['status', 'completed_at']
        if obj.status != 'draft':
            readonly.extend(['title', 'body', 'category'])
        return tuple(readonly)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('product', 'category', 'product__created_by')
        if not request.user.is_superuser:
            qs = qs.filter(product__created_by=request.user)
        return qs
```

## Breaking change Django 6: `lookup_allowed`

Django 6 agrego el parametro `request` a `lookup_allowed()`. Si override este metodo, actualizar la firma:

```python
# Django 5 (legacy)
def lookup_allowed(self, lookup, value):
    return super().lookup_allowed(lookup, value)

# Django 6 (obligatorio)
def lookup_allowed(self, lookup, value, request):
    if lookup in ('created_by__email',):
        return True
    return super().lookup_allowed(lookup, value, request)
```

## Mejores practicas

1. **Centralizar constantes de readonly** como `ClassVar` o `frozenset` (no recalcular en cada request)
2. **Separar logica compleja** en metodos privados `_get_scenario_groups()`, no inline en `get_fieldsets()`
3. **Type hints** en todos los metodos override: `def get_fieldsets(self, request: HttpRequest, obj: Product | None = None) -> list[...]`
4. **Usar `@admin.display`** decorator en vez de asignar atributos: `short_description`, `ordering`, `boolean`
5. **NUNCA** acceder a `request.user` para logica de negocio — solo para presentacion/permisos
6. **Testar admins** verificando que la pagina carga (HTTP 200) y los campos esperados aparecen

## Anti-patrones

```python
# MAL: logica de negocio en save_model
def save_model(self, request, obj, form, change):
    obj.calculate_price()        # Esto va en un service
    obj.notify_subscribers()     # Esto va en un service
    obj.update_inventory()       # Esto va en un service
    super().save_model(request, obj, form, change)

# BIEN: delegar a service
def save_model(self, request, obj, form, change):
    if not change:
        obj.created_by = request.user
    super().save_model(request, obj, form, change)
    if not change:
        from apps.orders.services.creation import on_order_created
        on_order_created(order=obj)
```

[Anterior: README](README.md) | [Siguiente: 02-typescript-moderno](02-typescript-moderno.md)
