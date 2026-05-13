[Anterior: 04-reusable-patterns](04-reusable-patterns.md) | [Siguiente: 06-widgets-inlines-forms](06-widgets-inlines-forms.md)

# 05. Performance y Security

> Optimizacion de queries, prevencion de N+1, permisos granulares, field-level permissions, y seguridad en Django admin.

## Prevencion de N+1 en list view

### `list_select_related`

```python
@admin.register(CostRecord)
class CostRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'amount', 'billed_date')

    # Opcion 1: boolean — Django auto-detecta FK en list_display
    list_select_related = True

    # Opcion 2: tuple explicita — mas eficiente, solo lo necesario
    list_select_related = ('user', 'provider', 'job')
```

### `get_queryset()` con prefetch

```python
def get_queryset(self, request):
    return (
        super()
        .get_queryset(request)
        .select_related('created_by', 'preferred_provider')
        .prefetch_related('images', 'shares__user')
    )
```

### `.only()` para modelos con muchos campos

```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    if self.model._meta.model_name == 'order':
        # Solo cargar campos usados en list_display
        qs = qs.only(
            'id', 'title', 'status', 'platform_id',
            'scheduled_at', 'created_at',
        )
    return qs
```

## `show_full_result_count`

```python
class BaseModelAdmin(admin.ModelAdmin):
    show_full_result_count = False  # Evita COUNT(*) en tablas con >10K rows
```

Sin esto, Django ejecuta `SELECT COUNT(*) FROM tabla` en cada page load del changelist.

## `autocomplete_fields` vs `raw_id_fields`

| Feature | `autocomplete_fields` | `raw_id_fields` |
|---------|----------------------|-----------------|
| UI | Dropdown con search (Select2) | Input texto + icono lookup |
| Query | AJAX search on type | Solo al abrir popup |
| Requisito | `search_fields` en el admin del FK target | Ninguno |
| UX | Mejor para usuarios finales | OK para admins tecnicos |

```python
@admin.register(CostRecord)
class CostRecordAdmin(admin.ModelAdmin):
    # Requiere que UserAdmin tenga search_fields definido
    autocomplete_fields = ('user', 'provider', 'job')

    # Alternativa sin requisito de search_fields
    # raw_id_fields = ('user', 'provider', 'job')
```

Requisito del modelo target:

```python
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email', 'first_name')  # REQUERIDO para autocomplete
```

## Paginacion eficiente

```python
class BaseModelAdmin(admin.ModelAdmin):
    list_per_page = 25           # Items por pagina (default: 100 es mucho)
    list_max_show_all = 200      # Max items en "Show all"

    # Para tablas enormes (>100K rows)
    show_full_result_count = False
```

## `search_fields` eficientes

```python
# MAL: search con __icontains en campos no indexados
search_fields = ('description__icontains', 'body__icontains')

# BIEN: search en campos indexados
search_fields = ('name', 'codename', 'created_by__username')
# Django aplica __icontains automaticamente

# Para busqueda exacta (mas rapida):
search_fields = ('=email', '=username')  # = prefix = exact match

# Para busqueda por prefijo (usa index B-tree):
search_fields = ('^name', '^codename')  # ^ prefix = startswith
```

## `date_hierarchy` eficiente

```python
@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'  # Requiere index en created_at
    # TimestampedModel ya incluye index en created_at
```

Para tablas grandes, `date_hierarchy` puede ser lento. Alternativa con filtro:

```python
list_filter = (
    ('created_at', admin.DateFieldListFilter),
)
```

## Permisos: hooks del ModelAdmin

### Permisos por accion

```python
def has_add_permission(self, request):
    """Controla quien puede agregar objetos."""
    return request.user.has_perm('myapp.add_model')

def has_change_permission(self, request, obj=None):
    """Controla quien puede editar. obj=None para changelist."""
    if obj and hasattr(obj, 'created_by'):
        # Solo el creador o superuser puede editar
        return obj.created_by == request.user or request.user.is_superuser
    return super().has_change_permission(request, obj)

def has_delete_permission(self, request, obj=None):
    """Controla quien puede borrar."""
    if obj and obj.status == 'published':
        return False  # No borrar publicados
    return super().has_delete_permission(request, obj)

def has_view_permission(self, request, obj=None):
    """Controla quien puede ver (read-only access)."""
    return True  # Todos pueden ver

def has_module_permission(self, request):
    """Controla si la app aparece en el index del admin."""
    return request.user.is_staff
```

### Read-only para ciertos usuarios

```python
def get_readonly_fields(self, request, obj=None):
    readonly = list(super().get_readonly_fields(request, obj))
    if not request.user.is_superuser:
        # Usuarios normales no pueden cambiar status ni provider
        readonly.extend(['status', 'preferred_provider'])
    return tuple(readonly)
```

### Filtrar queryset por usuario

```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    if not request.user.is_superuser:
        # Usuarios normales solo ven sus propios objetos
        qs = qs.filter(created_by=request.user)
    return qs
```

## Field-level permissions

Patron para controlar visibilidad de campos por grupo/permiso:

```python
# Campos sensibles que requieren permiso especial
_SENSITIVE_FIELDS = ('api_key', 'credentials', 'internal_notes')
_SENSITIVE_PERMISSION = 'billing.view_sensitive_data'

def get_fieldsets(self, request, obj=None):
    fieldsets = list(super().get_fieldsets(request, obj))
    if not request.user.has_perm(self._SENSITIVE_PERMISSION):
        # Remover campos sensibles de todos los fieldsets
        fieldsets = [
            (name, {
                **options,
                'fields': [
                    f for f in options['fields']
                    if f not in self._SENSITIVE_FIELDS
                ],
            })
            for name, options in fieldsets
        ]
    return fieldsets

def get_list_display(self, request):
    cols = list(super().get_list_display(request))
    if not request.user.has_perm(self._SENSITIVE_PERMISSION):
        cols = [c for c in cols if c not in self._SENSITIVE_FIELDS]
    return cols
```

## Inline permissions

```python
class RecentExecutionsInline(admin.TabularInline):
    model = ApiCallExecution
    extra = 0
    max_num = 10
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # Solo lectura

    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
```

## `format_html` seguro vs `mark_safe` inseguro

```python
# SEGURO: format_html escapa automaticamente los argumentos
@admin.display(description='Status')
def status_badge(self, obj):
    return format_html(
        '<span style="color:{}">{}</span>',
        self.STATUS_COLORS.get(obj.status, '#666'),
        obj.get_status_display(),  # Escapado automaticamente
    )

# INSEGURO: mark_safe NO escapa nada
from django.utils.safestring import mark_safe
def bad_status(self, obj):
    return mark_safe(f'<span>{obj.user_input}</span>')  # XSS vulnerability!

# Si NECESITAS mark_safe (HTML construido en loop), escapar manualmente:
from django.utils.html import escape, format_html
cards = ''
for item in items:
    cards += format_html('<div>{}</div>', item.name)
return mark_safe(cards)  # noqa: S308 — cada parte ya esta escapada via format_html
```

## Prevencion de CSRF en vistas custom

```python
def generate_enqueue_view(self, request):
    """Custom POST view — CSRF protegido automaticamente por admin_view()."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    # self.admin_site.admin_view() ya aplica CSRF + auth check
    # Solo necesitas CSRF token en el request
    # ...
```

En JavaScript:

```javascript
// Incluir CSRF token en cada POST
fetch(url, {
  method: 'POST',
  headers: {
    'X-CSRFToken': document.querySelector(
      'input[name="csrfmiddlewaretoken"]',
    ).value,
  },
  credentials: 'same-origin',
})
```

## Rate limiting en admin actions

```python
from django.core.cache import cache

@admin.action(description='Generate images (rate limited)')
def action_generate(self, request, queryset):
    cache_key = f'admin_generate_{request.user.pk}'
    last_run = cache.get(cache_key)

    if last_run:
        self.message_user(
            request,
            'Please wait 60 seconds between operations.',
            messages.WARNING,
        )
        return

    cache.set(cache_key, True, timeout=60)
    # ... enqueue tasks
```

## Admin LogEntry (audit trail built-in)

Django ya registra cambios en `LogEntry`. Acceder:

```python
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION

# Ver historial de un objeto
entries = LogEntry.objects.filter(
    content_type__app_label='products',
    content_type__model='product',
    object_id=str(product.pk),
).select_related('user', 'content_type')

for entry in entries:
    print(f'{entry.action_time}: {entry.user} {entry.get_action_flag_display()}')
    if entry.change_message:
        print(f'  Changes: {entry.get_change_message()}')
```

## Checklist de performance

| Check | Accion |
|-------|--------|
| N+1 en list view | `list_select_related` o `get_queryset()` con `select_related` |
| COUNT(*) lento | `show_full_result_count = False` |
| Search lento | Usar `^` (startswith) o `=` (exact) en `search_fields` |
| FK con muchas opciones | `autocomplete_fields` (no dropdown completo) |
| Tabla >100K rows | `list_per_page = 25`, no `date_hierarchy` |
| Inline con muchos items | `max_num` + `extra = 0` + `readonly_fields` |
| Campos no usados cargados | `.only()` o `.defer()` en `get_queryset()` |

## Checklist de seguridad

| Check | Accion |
|-------|--------|
| Custom views sin auth | SIEMPRE `admin_site.admin_view()` wrapper |
| HTML con datos de usuario | SIEMPRE `format_html()`, NUNCA `mark_safe(f-string)` |
| CSRF en POST custom | Header `X-CSRFToken` en Fetch, `credentials: 'same-origin'` |
| Datos sensibles en list | `get_list_display()` condicional por permiso |
| Objetos de otros usuarios | `get_queryset()` filtrado por `created_by=request.user` |
| Actions destructivas | `has_delete_permission()` + confirmacion intermedia |
| Credentials en forms | `PasswordInput(render_value=False)` + encriptar en `save()` |

[Anterior: 04-reusable-patterns](04-reusable-patterns.md) | [Siguiente: 06-widgets-inlines-forms](06-widgets-inlines-forms.md)
