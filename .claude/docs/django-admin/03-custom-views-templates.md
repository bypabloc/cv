[Anterior: 02-typescript-moderno](02-typescript-moderno.md) | [Siguiente: 04-reusable-patterns](04-reusable-patterns.md)

# 03. Custom Views y Templates

> Como agregar vistas custom al admin (dashboards, wizards, progress pages), override de templates, y el sistema de bloques de Django admin.

## `get_urls()` para registrar vistas custom

Patron fundamental para agregar endpoints al admin:

```python
from django.urls import path

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def get_urls(self):
        custom = [
            path(
                'process-progress/',
                self.admin_site.admin_view(self.process_progress_view),
                name='products_product_process_progress',
            ),
            path(
                'process-enqueue/',
                self.admin_site.admin_view(self.process_enqueue_view),
                name='products_product_process_enqueue',
            ),
            path(
                '<uuid:pk>/dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='products_product_dashboard',
            ),
        ]
        # CRITICO: custom ANTES de super() — evita que Django capture la URL
        return custom + super().get_urls()
```

Reglas:
- SIEMPRE wrappear con `self.admin_site.admin_view()` — asegura autenticacion + permisos
- URLs custom VAN ANTES de `super().get_urls()` — Django matchea `<path>` antes
- Naming convention: `<app>_<model>_<action>` para consistencia con admin URL names

## Vista HTML (TemplateResponse)

```python
from django.template.response import TemplateResponse

def process_progress_view(self, request):
    raw_ids = request.GET.get('ids', '')
    id_list = [i.strip() for i in raw_ids.split(',') if i.strip()]
    products = Product.objects.filter(pk__in=id_list).select_related(
        'preferred_provider',
    )

    context = {
        **self.admin_site.each_context(request),  # Sidebar, site_header, etc.
        'title': 'Generating base images',
        'products': products,
        'opts': self.model._meta,  # Para breadcrumbs
        'changelist_url': reverse('admin:products_product_changelist'),
    }
    return TemplateResponse(
        request,
        'admin/products/product/process_progress.html',
        context,
    )
```

`self.admin_site.each_context(request)` inyecta:
- `site_header`, `site_title`, `site_url`
- `has_permission` (boolean)
- `available_apps` (para el sidebar)
- `is_popup`, `is_nav_sidebar_enabled`

## Vista JSON (API endpoints)

```python
from django.http import JsonResponse

def process_enqueue_view(self, request):
    """POST endpoint para encolar generacion."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    raw_ids = request.GET.get('ids', '')
    id_list = [i.strip() for i in raw_ids.split(',') if i.strip()]

    jobs = []
    for product in Product.objects.filter(pk__in=id_list):
        job = create_generation_job(product=product)
        process_task.delay(str(job.pk))
        jobs.append({
            'job_id': str(job.pk),
            'product_name': product.name,
        })

    return JsonResponse({'jobs': jobs})
```

## Vistas standalone (fuera del ModelAdmin)

Para vistas que no pertenecen a un modelo especifico:

```python
# server/apps/products/admin/category_views.py

from django.template.response import TemplateResponse

def category_picker_view(request, admin_site, opts):
    """Vista standalone registrada en ProductAdmin.get_urls()."""
    raw_ids = request.GET.get('ids', '')
    # ...
    context = {
        **admin_site.each_context(request),
        'title': 'Select categories',
        'opts': opts,
        'products': products,
        'categories': categories,
    }
    return TemplateResponse(
        request,
        'admin/products/product/category_picker.html',
        context,
    )
```

Registrar en `get_urls()`:

```python
def get_urls(self):
    from apps.products.admin.category_views import category_picker_view

    custom = [
        path(
            'category-picker/',
            self.admin_site.admin_view(
                lambda r: category_picker_view(
                    r, self.admin_site, self.model._meta,
                ),
            ),
            name='products_product_category_picker',
        ),
    ]
    return custom + super().get_urls()
```

## Admin actions con paginas intermedias

Patron: action redirige a vista custom en vez de ejecutar directamente.

```python
@admin.action(description='Process selected')
def action_process(self, request, queryset):
    """Redirige a pagina de progreso."""
    ids = ','.join(str(pk) for pk in queryset.values_list('pk', flat=True))
    url = reverse('admin:products_product_process_progress') + f'?ids={ids}'
    return HttpResponseRedirect(url)
```

Para confirmacion:

```python
@admin.action(description='Delete with confirmation')
def action_delete_with_confirm(self, request, queryset):
    if request.POST.get('confirmed'):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} objects deleted.')
        return None

    context = {
        **self.admin_site.each_context(request),
        'title': 'Confirm deletion',
        'queryset': queryset,
        'opts': self.model._meta,
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return TemplateResponse(
        request,
        'admin/myapp/confirm_action.html',
        context,
    )
```

Template de confirmacion:

```html
{% extends "admin/base_site.html" %}
{% block content %}
<form method="post">
  {% csrf_token %}
  <p>Are you sure you want to delete {{ queryset.count }} items?</p>
  <ul>
    {% for obj in queryset %}
    <li>{{ obj }}
      <input type="hidden" name="{{ action_checkbox_name }}" value="{{ obj.pk }}">
    </li>
    {% endfor %}
  </ul>
  <input type="hidden" name="action" value="action_delete_with_confirm">
  <input type="hidden" name="confirmed" value="1">
  <input type="submit" value="Confirm Delete" class="default">
  <a href="{% url opts|admin_urlname:'changelist' %}">Cancel</a>
</form>
{% endblock %}
```

## Sistema de templates del admin

### Jerarquia de busqueda de templates

Django admin busca templates en este orden:
1. `templates/admin/<app>/<model>/<template>.html` — mas especifico
2. `templates/admin/<app>/<template>.html` — nivel app
3. `templates/admin/<template>.html` — global admin
4. Django built-in `django/contrib/admin/templates/admin/<template>.html`

### Templates principales que se pueden overridear

| Template | Uso |
|----------|-----|
| `change_form.html` | Formulario de add/change individual |
| `change_list.html` | Lista de objetos |
| `delete_confirmation.html` | Confirmacion de borrado |
| `object_history.html` | Historial de cambios |
| `base_site.html` | Base del sitio admin (branding) |
| `index.html` | Dashboard principal del admin |
| `app_index.html` | Indice de una app |
| `login.html` | Pagina de login |

### Bloques de `change_form.html`

```html
{% extends "admin/change_form.html" %}
{% load static %}

{% block extrahead %}
  {{ block.super }}
  {# CSS y JS adicional #}
{% endblock %}

{% block extrastyle %}
  {{ block.super }}
  <style>/* CSS inline */</style>
{% endblock %}

{% block content_title %}
  {# Titulo customizado #}
  <h1>{{ title }} - Custom</h1>
{% endblock %}

{% block content %}
  {{ block.super }}
  {# Contenido adicional DESPUES del form #}
{% endblock %}

{% block after_field_sets %}
  {# Insertar contenido entre fieldsets y botones #}
  <div class="custom-section">
    {% include "admin/myapp/_preview_panel.html" %}
  </div>
{% endblock %}

{% block after_related_objects %}
  {# Insertar despues de inlines #}
{% endblock %}

{% block submit_buttons_bottom %}
  {{ block.super }}
  {# Botones adicionales junto a Save #}
  <input type="submit" name="_process" value="Save & Process">
{% endblock %}
```

### Bloques de `change_list.html`

```html
{% extends "admin/change_list.html" %}

{% block content_title %}
  {{ block.super }}
  <a href="{% url 'admin:myapp_model_export' %}" class="button">
    Export CSV
  </a>
{% endblock %}

{% block result_list %}
  {{ block.super }}
  {# Contenido adicional debajo de la tabla #}
{% endblock %}

{% block pagination %}
  {{ block.super }}
{% endblock %}
```

## Patron: `change_form_template` para override por modelo

```python
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_form_template = 'admin/products/product/change_form.html'
```

Template location: `server/apps/products/templates/admin/products/product/change_form.html`

Ejemplo real del proyecto — inyectar seccion de related items:

```html
{% extends "admin/change_form.html" %}
{% load i18n static %}

{% block after_field_sets %}
  {{ block.super }}

  {% if related_groups %}
  <fieldset class="module">
    <h2>{% trans "Related Items" %}</h2>
    <div style="padding:16px">
      {% for group in related_groups %}
      <div style="margin-bottom:24px">
        <h3>{{ group.name }}
          <small style="color:#666">({{ group.provider }})</small>
        </h3>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          {% for img in group.images %}
          <div style="text-align:center">
            <img src="{{ img.url }}"
                 style="max-width:180px;max-height:250px;
                        object-fit:contain;border-radius:4px;
                        border:1px solid #ddd">
            <div style="font-size:12px;color:#666;margin-top:4px">
              Item {{ img.index }}
            </div>
          </div>
          {% endfor %}
        </div>
        <div style="font-size:12px;color:#888;margin-top:8px">
          {{ group.success_count }} OK / {{ group.fail_count }} Failed
        </div>
      </div>
      {% endfor %}
    </div>
  </fieldset>
  {% endif %}
{% endblock %}
```

## Dashboard custom en admin

```python
# admin.py o admin_site.py
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = 'Rezebra Admin'
    site_title = 'Rezebra'
    index_title = 'Dashboard'
    index_template = 'admin/custom_index.html'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'total_products': Product.objects.count(),
            'pending_orders': Order.objects.filter(
                status='pending',
            ).count(),
            'recent_orders': Order.objects.order_by(
                '-created_at',
            )[:5],
        })
        return super().index(request, extra_context)

admin_site = CustomAdminSite(name='custom_admin')
```

Template `admin/custom_index.html`:

```html
{% extends "admin/index.html" %}

{% block content %}
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;
            margin-bottom:24px">
  <div class="module" style="padding:16px;text-align:center">
    <h3>{{ total_products }}</h3>
    <p>Total Products</p>
  </div>
  <div class="module" style="padding:16px;text-align:center">
    <h3>{{ pending_orders }}</h3>
    <p>Pending Orders</p>
  </div>
</div>

{{ block.super }}
{% endblock %}
```

## Wizard multi-step en admin

```python
def get_urls(self):
    return [
        path('wizard/step1/', self.admin_site.admin_view(self.wizard_step1),
             name='myapp_model_wizard_step1'),
        path('wizard/step2/', self.admin_site.admin_view(self.wizard_step2),
             name='myapp_model_wizard_step2'),
        path('wizard/step3/', self.admin_site.admin_view(self.wizard_step3),
             name='myapp_model_wizard_step3'),
    ] + super().get_urls()

def wizard_step1(self, request):
    if request.method == 'POST':
        form = Step1Form(request.POST)
        if form.is_valid():
            request.session['wizard_step1'] = form.cleaned_data
            return HttpResponseRedirect(
                reverse('admin:myapp_model_wizard_step2'),
            )
    else:
        form = Step1Form()

    context = {
        **self.admin_site.each_context(request),
        'title': 'Step 1: Select Options',
        'form': form,
        'opts': self.model._meta,
        'current_step': 1,
        'total_steps': 3,
    }
    return TemplateResponse(
        request,
        'admin/myapp/model/wizard_step.html',
        context,
    )
```

## Partial templates (reutilizables)

Convencion de naming: prefijo `_` para partials.

```
templates/admin/products/product/
├── change_form.html        # Override principal
├── process_progress.html  # Vista custom full-page
├── category_picker.html    # Vista custom full-page
├── _status_badge.html      # Partial: badge de status
├── _image_grid.html        # Partial: grid de imagenes
└── _progress_bar.html      # Partial: barra de progreso
```

```html
{# _image_grid.html #}
<div class="image-grid" style="display:flex;gap:12px;flex-wrap:wrap">
  {% for img in images %}
  <div class="image-card" style="text-align:center;max-width:200px">
    <img src="{{ img.url }}"
         style="max-width:200px;max-height:280px;object-fit:contain;
                border:1px solid #ddd;border-radius:4px">
    <span style="font-size:.8rem;color:#555">{{ img.label }}</span>
  </div>
  {% empty %}
  <em style="color:#999">No items yet</em>
  {% endfor %}
</div>
```

Incluir: `{% include "admin/products/product/_image_grid.html" with images=base_images %}`

## Mejores practicas

1. **`each_context(request)`** obligatorio en vistas custom — asegura sidebar y branding
2. **`opts` en context** — necesario para breadcrumbs y URL generation en templates
3. **`TemplateResponse`** sobre `render()` — permite middleware de template alterar la respuesta
4. **Partials con prefijo `_`** — distinguir de templates full-page
5. **NUNCA lanzar 500** en vistas custom — catch exceptions y mostrar mensajes amigables
6. **`admin_view()` wrapper** — SIEMPRE para autenticacion y permisos
7. **URLs custom ANTES de `super().get_urls()`** — Django matchea en orden

[Anterior: 02-typescript-moderno](02-typescript-moderno.md) | [Siguiente: 04-reusable-patterns](04-reusable-patterns.md)
