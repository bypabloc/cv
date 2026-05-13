[Anterior: 05-performance-security](05-performance-security.md) | [Siguiente: 07-third-party-libraries](07-third-party-libraries.md)

# 06. Widgets, Inlines y Forms Avanzados

> Custom widgets con thumbnails, inline avanzados, formsets, sortable inlines, nested inlines, y forms custom para el admin.

## Custom Widget con thumbnails

Patron real del proyecto — checkbox con preview de imagenes:

```python
# server/apps/products/admin/widgets.py

class ImageCheckboxSelect(forms.CheckboxSelectMultiple):
    """Checkbox widget con thumbnail previews y data attributes."""

    def __init__(self, image_data=None, max_images=2, **kwargs):
        super().__init__(**kwargs)
        # image_data: list of (image_id, label, category_id, url)
        self._image_data = {
            row[0]: (row[2], row[3]) for row in (image_data or [])
        }
        self._max_images = max_images

    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(
            name, value, label, selected, index, **kwargs,
        )

        image_id = str(value) if value else ''
        data = self._image_data.get(image_id)
        if data:
            category_id, url = data
            # Inyectar data attributes para JS
            option['attrs']['data-category-id'] = category_id
            if url:
                thumb = format_html(
                    '<img src="{}" style="width:80px;height:120px;'
                    'object-fit:cover;border-radius:4px;'
                    'margin-left:8px;vertical-align:middle" />',
                    url,
                )
                option['label'] = mark_safe(f'{label}{thumb}')

        return option

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['data-max-images'] = str(self._max_images)
        return attrs

    class Media:
        js = ('products/js/image_selector.js',)
```

## JSON Editor Widget (OBLIGATORIO para JSONField)

SIEMPRE usar `JSONEditorWidget` de `django-json-widget` para campos `JSONField` en admin. NUNCA usar `forms.Textarea` plano.

Libreria: `django-json-widget>=2.1.1` (declarada en `server/pyproject.toml`, registrada en `INSTALLED_APPS` como `'django_json_widget'`).

Ofrece: syntax highlighting, validacion JSON en tiempo real, modos `code` (editor) y `tree` (visual), dark mode nativo.

```python
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {
            'widget': JSONEditorWidget(
                options={
                    'mode': 'code',
                    'modes': ['code', 'tree'],
                },
            ),
        },
    }
```

Para customizar altura por campo especifico (override individual en el form):

```python
class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = '__all__'
        widgets = {
            'config': JSONEditorWidget(
                options={'mode': 'tree', 'modes': ['tree', 'code']},
                attrs={'style': 'height:300px;width:90%'},
            ),
        }
```

## Custom Widget: Color Picker

```python
class ColorWidget(forms.TextInput):
    input_type = 'color'
    template_name = 'admin/widgets/color_input.html'

    def __init__(self, attrs=None):
        defaults = {'style': 'width:60px;height:32px;padding:2px;cursor:pointer'}
        if attrs:
            defaults.update(attrs)
        super().__init__(attrs=defaults)
```

## Custom ModelForm para admin

Patron real del proyecto — form con campos inline para schedule:

```python
class ScheduledApiCallForm(forms.ModelForm):
    """Form con campos adicionales no-modelo."""

    # Campos que NO existen en el modelo
    credentials_plain = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Bearer token o API key. Dejar vacio para mantener actual.',
        label='Credentials',
    )

    interval_every = forms.IntegerField(
        required=False, min_value=1, initial=5, label='Every',
    )
    interval_period = forms.ChoiceField(
        required=False,
        choices=[('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        label='Period',
    )

    class Meta:
        model = ScheduledApiCall
        fields = ('name', 'url', 'http_method', 'schedule_type', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_from_instance()

    def _populate_from_instance(self):
        """Llenar campos inline desde FK existentes."""
        obj = self.instance
        if not obj or not obj.pk:
            return
        if obj.interval:
            self.fields['interval_every'].initial = obj.interval.every
            self.fields['interval_period'].initial = obj.interval.period

    def clean(self):
        cleaned = super().clean()
        schedule_type = cleaned.get('schedule_type')
        if schedule_type == 'interval':
            if not cleaned.get('interval_every'):
                self.add_error('interval_every', 'Required for interval schedule.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Encriptar credentials si se proporcionaron
        plain = self.cleaned_data.get('credentials_plain', '')
        if plain:
            instance.set_credentials(plain)

        # Crear/actualizar schedule FK
        if self.cleaned_data['schedule_type'] == 'interval':
            from django_tasks_database.models import IntervalSchedule
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=self.cleaned_data['interval_every'],
                period=self.cleaned_data['interval_period'],
            )
            instance.interval = schedule

        if commit:
            instance.save()
        return instance
```

Registrar:

```python
@admin.register(ScheduledApiCall)
class ScheduledApiCallAdmin(admin.ModelAdmin):
    form = ScheduledApiCallForm
```

## TabularInline vs StackedInline

| Feature | TabularInline | StackedInline |
|---------|--------------|---------------|
| Layout | Tabla (compacta) | Formulario vertical (amplia) |
| Mejor para | Pocos campos, muchos items | Muchos campos, pocos items |
| Espacio | Ahorra espacio vertical | Consume mas espacio |

```python
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    autocomplete_fields = ('user',)
    fields = ('user', 'permission')

class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 0
    fields = (
        'platform', 'username', 'encrypted_password',
        'auth_token', 'is_active',
    )
```

## Inline avanzado: Read-only con link al objeto

```python
class RecentExecutionsInline(admin.TabularInline):
    model = ApiCallExecution
    extra = 0
    max_num = 10
    fields = ('status', 'response_status', 'latency_ms', 'executed_at')
    readonly_fields = fields
    ordering = ['-executed_at']
    can_delete = False
    show_change_link = True  # Link al change view del objeto inline

    def has_add_permission(self, request, obj=None):
        return False
```

## Dynamic `get_extra()` en inlines

```python
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant

    def get_extra(self, request, obj=None, **kwargs):
        """No extra forms si ya hay shares, 1 si no hay."""
        if obj and obj.shares.exists():
            return 0
        return 1
```

## Inline con form custom

```python
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('user', 'permission')
        widgets = {
            'permission': forms.RadioSelect,
        }

    def clean_user(self):
        user = self.cleaned_data['user']
        product = self.instance.product if self.instance.pk else None
        if product and product.created_by == user:
            raise forms.ValidationError("Can't share with the owner.")
        return user

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    form = ProductVariantForm
```

## Sortable Inlines (drag-and-drop)

Sin libreria — patron basico con campo `order`:

```python
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('order', 'name', 'description')
    ordering = ['order']

    class Media:
        js = ('admin/js/sortable_inline.js',)
```

```javascript
// sortable_inline.js — usando Sortable.js
(function () {
  'use strict'

  function init() {
    var tbody = document.querySelector('.inline-group tbody')
    if (!tbody) return

    // Requiere Sortable.js cargado
    if (typeof Sortable === 'undefined') return

    Sortable.create(tbody, {
      handle: '.drag-handle',
      animation: 150,
      onEnd: function () {
        // Actualizar campo order en cada row
        var rows = tbody.querySelectorAll('tr.dynamic-orderitem_set')
        rows.forEach(function (row, index) {
          var orderInput = row.querySelector('input[name$="-order"]')
          if (orderInput) orderInput.value = index
        })
      },
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
```

Con django-admin-sortable2 (recomendado):

```python
# pip install django-admin-sortable2
from adminsortable2.admin import SortableInlineAdminMixin

class OrderItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = OrderItem
    extra = 0
    # El campo de orden se detecta automaticamente (position_field)
```

## Formset customization

```python
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    min_num = 0
    max_num = 10
    validate_min = False
    validate_max = True

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Customizar el formset class
        formset.validate_min = self.validate_min
        formset.validate_max = self.validate_max
        return formset
```

## Inline condicional en fieldsets

Mostrar inlines solo en ciertas condiciones:

```python
def get_inline_instances(self, request, obj=None):
    """Solo mostrar inlines en change view."""
    if obj is None:
        return []

    inlines = []
    for inline_class in self.get_inlines(request, obj):
        inline = inline_class(self.model, self.admin_site)
        if self._should_show_inline(inline, obj):
            inlines.append(inline)
    return inlines

def _should_show_inline(self, inline, obj):
    """Logica para decidir si mostrar un inline."""
    if isinstance(inline, ProductImageInline):
        return obj.status == 'active'
    return True
```

## Custom formfield overrides

Cambiar widgets globalmente por tipo de campo:

```python
from django_json_widget.widgets import JSONEditorWidget

@admin.register(ScheduledApiCall)
class ScheduledApiCallAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {
            'widget': JSONEditorWidget(
                options={'mode': 'code', 'modes': ['code', 'tree']},
            ),
        },
        models.TextField: {
            'widget': forms.Textarea(attrs={
                'rows': 4,
                'style': 'width:100%',
            }),
        },
        models.URLField: {
            'widget': forms.URLInput(attrs={
                'style': 'width:100%',
                'placeholder': 'https://',
            }),
        },
    }
```

**REGLA**: Todo `formfield_overrides` que incluya `models.JSONField` DEBE usar `JSONEditorWidget`. Usar `forms.Textarea` para JSONField esta prohibido.

## Prepopulated fields

```python
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'codename': ('name',),  # Auto-genera slug desde name
    }
```

Para logica mas compleja, usar JS via Media:

```javascript
// codename_autofill.js
(function () {
  'use strict'

  function init() {
    var nameField = document.getElementById('id_name')
    var codenameField = document.getElementById('id_codename')
    if (!nameField || !codenameField) return
    if (codenameField.value) return // No sobreescribir si ya tiene valor

    nameField.addEventListener('input', function () {
      codenameField.value = nameField.value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '')
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
```

## Fieldset classes

Django admin soporta CSS classes en fieldsets:

```python
fieldsets = (
    ('Basic', {
        'fields': ('name', 'codename'),
    }),
    ('Advanced', {
        'fields': ('preferred_provider', 'visibility'),
        'classes': ('collapse',),  # Colapsado por defecto
    }),
    ('Debug', {
        'fields': ('created_at', 'updated_at'),
        'classes': ('collapse', 'wide'),
        'description': 'Timestamps automaticos del modelo.',
    }),
)
```

Classes disponibles:
- `collapse` — fieldset colapsado, toggle con click
- `wide` — inputs mas anchos
- Custom classes via CSS en `Media.css`

## Patron: Fields dinamicos con HTMX

```html
<!-- change_form.html override -->
{% block after_field_sets %}
{{ block.super }}

<fieldset class="module" id="dynamic-preview">
  <h2>Live Preview</h2>
  <div hx-get="{% url 'admin:products_product_preview' object_id %}"
       hx-trigger="change from:#id_name, change from:#id_codename delay:500ms"
       hx-swap="innerHTML"
       hx-include="#product_form">
    {% include "admin/products/product/_preview.html" %}
  </div>
</fieldset>
{% endblock %}
```

## Mejores practicas

1. **Widgets via `formfield_overrides`** para cambios globales por tipo de campo
2. **`create_option()` override** para inyectar `data-` attributes y thumbnails
3. **`Media` class** en widgets para JS/CSS autoincluidos
4. **`extra = 0`** en inlines de solo lectura — no mostrar forms vacios
5. **`show_change_link = True`** en inlines readonly — permite navegar al objeto
6. **`autocomplete_fields`** sobre dropdowns para FK con >50 opciones
7. **`max_num` en inlines** — previene abuse y mejora UX
8. **Formset validation** via `clean()` en form custom del inline
9. **JS en archivos separados** via `Media` — nunca inline en Python
10. **JSONField SIEMPRE con `JSONEditorWidget`** de `django-json-widget` — NUNCA `forms.Textarea` plano

[Anterior: 05-performance-security](05-performance-security.md) | [Siguiente: 07-third-party-libraries](07-third-party-libraries.md)
