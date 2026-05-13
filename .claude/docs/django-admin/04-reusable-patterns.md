[Anterior: 03-custom-views-templates](03-custom-views-templates.md) | [Siguiente: 05-performance-security](05-performance-security.md)

# 04. Reusable Patterns y Mixins

> Mixins reutilizables, base classes, patrones de composicion, AdminSite custom, y estrategias para admin escalables y consistentes.

## Base ModelAdmin del proyecto

Patron para establecer defaults de proyecto:

```python
# server/common/admin/base.py
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin con defaults del proyecto rezebra."""

    # Prevenir N+1 en list view
    show_full_result_count = False  # Evita COUNT(*) en tablas grandes

    # Timestamps siempre readonly
    readonly_fields = ('created_at', 'updated_at')

    # Paginacion por defecto
    list_per_page = 25
    list_max_show_all = 200

    def get_queryset(self, request):
        """Override para que subclases puedan agregar select_related."""
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        """Hook para auto-assign de created_by si existe."""
        if not change and hasattr(obj, 'created_by') and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
```

Uso:

```python
from common.admin.base import BaseModelAdmin

@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    list_display = ('title', 'status', 'category')
    # Hereda show_full_result_count=False, readonly timestamps, etc.
```

## Mixin: Export CSV

```python
# server/common/admin/mixins/export_csv.py
import csv
from django.http import HttpResponse


class ExportCSVMixin:
    """Agrega action para exportar a CSV."""

    def get_csv_fields(self):
        """Override para definir campos a exportar."""
        return [f.name for f in self.model._meta.get_fields()
                if hasattr(f, 'column')]

    def get_csv_filename(self):
        return f'{self.model._meta.model_name}_export.csv'

    @admin.action(description='Export selected to CSV')
    def export_as_csv(self, request, queryset):
        fields = self.get_csv_fields()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="{self.get_csv_filename()}"'
        )

        writer = csv.writer(response)
        writer.writerow(fields)

        for obj in queryset.only(*fields):
            row = []
            for field in fields:
                value = getattr(obj, field, '')
                if callable(value):
                    value = value()
                row.append(str(value))
            writer.writerow(row)

        return response
```

Uso:

```python
@admin.register(CostRecord)
class CostRecordAdmin(ExportCSVMixin, BaseModelAdmin):
    actions = ['export_as_csv']

    def get_csv_fields(self):
        return ['user', 'provider', 'amount', 'currency', 'billed_date']
```

## Mixin: Audit Log

```python
# server/common/admin/mixins/audit_log.py
import logging

logger = logging.getLogger('admin.audit')


class AuditLogMixin:
    """Logea cambios en admin para auditoria."""

    def save_model(self, request, obj, form, change):
        action = 'changed' if change else 'added'
        logger.info(
            'Admin %s %s %s (pk=%s)',
            request.user.username,
            action,
            obj._meta.model_name,
            obj.pk,
            extra={
                'user_id': str(request.user.pk),
                'model': f'{obj._meta.app_label}.{obj._meta.model_name}',
                'object_id': str(obj.pk),
                'action': action,
                'changed_fields': list(form.changed_data) if change else [],
            },
        )
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        logger.info(
            'Admin %s deleted %s (pk=%s)',
            request.user.username,
            obj._meta.model_name,
            obj.pk,
            extra={
                'user_id': str(request.user.pk),
                'model': f'{obj._meta.app_label}.{obj._meta.model_name}',
                'object_id': str(obj.pk),
                'action': 'deleted',
            },
        )
        super().delete_model(request, obj)
```

## Mixin: Read-Only Admin

```python
# server/common/admin/mixins/readonly.py

class ReadOnlyAdminMixin:
    """Admin completamente read-only (para logs, audit trail, etc.)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions
```

Uso:

```python
@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    list_display = ('user', 'action', 'target_type', 'created_at')
    list_filter = ('action', 'target_type')
    date_hierarchy = 'created_at'
```

## Mixin: Soft Delete

```python
# server/common/admin/mixins/soft_delete.py

class SoftDeleteAdminMixin:
    """Admin para modelos con soft delete (is_active flag)."""

    def get_queryset(self, request):
        """Mostrar todos, incluidos soft-deleted."""
        return self.model._default_manager.all()

    def delete_model(self, request, obj):
        """Soft delete en vez de hard delete."""
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])

    def delete_queryset(self, request, queryset):
        """Bulk soft delete."""
        queryset.update(is_active=False)

    @admin.action(description='Restore selected (undelete)')
    def action_restore(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} item(s) restored.')
```

## Mixin: Status Badge Display

```python
# server/common/admin/mixins/status_badge.py
from django.utils.html import format_html


class StatusBadgeMixin:
    """Mixin para mostrar status con badge coloreado."""

    # Override en subclase
    STATUS_COLORS: dict[str, tuple[str, str]] = {
        # 'status_value': ('background', 'foreground')
    }

    def status_badge_html(self, status: str, label: str = '') -> str:
        bg, fg = self.STATUS_COLORS.get(status, ('#6c757d', '#fff'))
        return format_html(
            '<span style="'
            'background:{};color:{};padding:2px 8px;'
            'border-radius:4px;font-size:11px;'
            'font-weight:600;text-transform:uppercase;'
            'letter-spacing:.5px'
            '">{}</span>',
            bg, fg, label or status,
        )
```

Uso:

```python
@admin.register(Order)
class OrderAdmin(StatusBadgeMixin, BaseModelAdmin):
    STATUS_COLORS = {
        'queued': ('#6c757d', '#fff'),
        'processing': ('#0d6efd', '#fff'),
        'completed': ('#198754', '#fff'),
        'failed': ('#dc3545', '#fff'),
    }

    @admin.display(description='Status', ordering='status')
    def status_display(self, obj):
        return self.status_badge_html(obj.status, obj.get_status_display())
```

## Mixin: Thumbnail Display

```python
# server/common/admin/mixins/thumbnail.py
from django.utils.html import format_html


class ThumbnailMixin:
    """Mixin para mostrar thumbnails de imagenes en list_display."""

    THUMBNAIL_SIZE = (48, 48)

    def thumbnail_html(
        self,
        url: str | None,
        alt: str = '',
        size: tuple[int, int] | None = None,
    ) -> str:
        if not url:
            return format_html(
                '<span style="color:#999">{}</span>', '\u2014',
            )

        w, h = size or self.THUMBNAIL_SIZE
        return format_html(
            '<img src="{}" alt="{}" width="{}" height="{}"'
            ' style="object-fit:cover;border-radius:4px;'
            'border:1px solid #ddd;vertical-align:middle">',
            url, alt, w, h,
        )
```

## Mixin: Background Task Trigger

```python
# server/common/admin/mixins/task_trigger.py

class TaskTriggerMixin:
    """Mixin para encolar background tasks desde admin actions."""

    def enqueue_task(self, request, queryset, task_func, description):
        """Helper generico para encolar tasks por cada objeto."""
        count = 0
        for obj in queryset:
            task_func.delay(str(obj.pk))
            count += 1

        self.message_user(
            request,
            f'{count} task(s) enqueued: {description}',
        )
```

Uso:

```python
@admin.register(ScheduledApiCall)
class ScheduledApiCallAdmin(TaskTriggerMixin, BaseModelAdmin):
    @admin.action(description='Execute now (immediate)')
    def execute_now(self, request, queryset):
        from apps.scheduler.tasks import execute_scheduled_api_call
        self.enqueue_task(
            request,
            queryset.filter(is_active=True),
            execute_scheduled_api_call,
            'scheduled API call execution',
        )
```

## Composicion de mixins

Orden de herencia (MRO): mixins ANTES de la base class.

```python
@admin.register(Product)
class ProductAdmin(
    AuditLogMixin,
    StatusBadgeMixin,
    ThumbnailMixin,
    ExportCSVMixin,
    BaseModelAdmin,
):
    actions = ['export_as_csv', 'action_process']
    # ...
```

## Custom AdminSite

Para branding y personalizacion del sitio admin completo:

```python
# server/config/admin_site.py
from django.contrib.admin import AdminSite


class RezebraAdminSite(AdminSite):
    site_header = 'Rezebra Administration'
    site_title = 'Rezebra'
    index_title = 'Dashboard'

    def get_app_list(self, request, app_label=None):
        """Reorder apps in sidebar."""
        app_list = super().get_app_list(request, app_label)
        # Custom ordering
        priority = {
            'products': 0,
            'orders': 1,
            'categories': 2,
            'accounts': 3,
            'scheduler': 4,
        }
        app_list.sort(key=lambda x: priority.get(x['app_label'], 99))
        return app_list
```

Registrar:

```python
# server/config/urls.py
from config.admin_site import RezebraAdminSite

admin_site = RezebraAdminSite(name='admin')

# Registrar todos los modelos en admin_site en vez de admin.site
# O usar: admin.site = admin_site (reemplazo global)
```

## Custom filters reutilizables

```python
# server/common/admin/filters.py
from django.contrib.admin import SimpleListFilter
from django.utils import timezone


class CreatedRecentlyFilter(SimpleListFilter):
    """Filtrar por items creados recientemente."""
    title = 'Created'
    parameter_name = 'created_recently'

    def lookups(self, request, model_admin):
        return [
            ('today', 'Today'),
            ('week', 'Last 7 days'),
            ('month', 'Last 30 days'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        match self.value():
            case 'today':
                return queryset.filter(created_at__date=now.date())
            case 'week':
                return queryset.filter(
                    created_at__gte=now - timezone.timedelta(days=7),
                )
            case 'month':
                return queryset.filter(
                    created_at__gte=now - timezone.timedelta(days=30),
                )
        return queryset


class IsActiveFilter(SimpleListFilter):
    """Filtro booleano mejorado con labels descriptivos."""
    title = 'Active'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return [('1', 'Active'), ('0', 'Inactive')]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(is_active=True)
        if self.value() == '0':
            return queryset.filter(is_active=False)
        return queryset


class HasRelatedFilter(SimpleListFilter):
    """Filtro generico para "tiene relacion" / "no tiene relacion"."""
    title = ''  # Override
    parameter_name = ''  # Override
    related_field = ''  # Override: nombre del campo FK/M2M

    def lookups(self, request, model_admin):
        return [('yes', 'Has'), ('no', 'Missing')]

    def queryset(self, request, queryset):
        lookup = f'{self.related_field}__isnull'
        if self.value() == 'yes':
            return queryset.filter(**{lookup: False})
        if self.value() == 'no':
            return queryset.filter(**{lookup: True})
        return queryset
```

Uso:

```python
class HasImageFilter(HasRelatedFilter):
    title = 'Image'
    parameter_name = 'has_image'
    related_field = 'image_url'

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(image_url='')
        if self.value() == 'no':
            return queryset.filter(image_url='')
        return queryset
```

## `@admin.display` decorator (Django 5+)

Reemplazo limpio de los atributos `short_description`, `admin_order_field`, `boolean`:

```python
# ANTES (legacy)
def status_badge(self, obj):
    return format_html('...')
status_badge.short_description = 'Status'
status_badge.admin_order_field = 'status'

# AHORA (Django 5+/6)
@admin.display(description='Status', ordering='status')
def status_badge(self, obj):
    return format_html('...')

# Para booleanos
@admin.display(description='Active', boolean=True)
def is_active_display(self, obj):
    return obj.is_active

# Con empty_value para None
@admin.display(description='Last run', empty_value='-', ordering='last_executed_at')
def last_run_display(self, obj):
    return obj.last_executed_at
```

## Patron: Admin modular con archivos separados

Para admin complejos, dividir en archivos:

```
server/apps/products/admin/
├── __init__.py              # Re-exports
├── product.py               # ProductAdmin principal
├── product_variant.py       # ProductVariantInline
├── product_image.py         # ProductImageInline
├── forms.py                 # ProductAdminForm
└── category_views.py        # Vistas standalone de categories
```

`__init__.py`:

```python
from apps.products.admin.product import ProductAdmin
from apps.products.admin.product_variant import ProductVariantAdmin

__all__ = ['ProductAdmin', 'ProductVariantAdmin']
```

## Mejores practicas

1. **Mixins para comportamiento transversal** — no duplicar logica entre admins
2. **Base class para defaults de proyecto** — `show_full_result_count`, readonly timestamps, etc.
3. **Un archivo por admin class** cuando supera ~100 lineas
4. **Filters reutilizables** en `common/admin/filters.py`
5. **`@admin.display`** siempre sobre atributos legacy
6. **Composicion sobre herencia profunda** — max 3-4 niveles de herencia
7. **AdminSite custom** para branding, ordering de apps, dashboard

[Anterior: 03-custom-views-templates](03-custom-views-templates.md) | [Siguiente: 05-performance-security](05-performance-security.md)
