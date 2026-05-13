[Anterior: API Reference](01-api-reference.md) | [Volver al indice](README.md)

# Django 6 - Background Tasks Framework

> Sistema built-in para ejecutar codigo fuera del ciclo request-response con `@task` decorator y `.enqueue()`.

## Concepto

Django 6 incluye un framework nativo de tareas en background. Permite mover operaciones costosas (envio de emails, procesamiento de imagenes, llamadas a APIs) fuera del request-response sin necesidad de Celery o Redis para casos simples.

**Flujo basico**:

1. Decorar funcion con `@task`
2. Llamar `.enqueue()` en el request
3. Django ejecuta la tarea en background segun el backend configurado

## Configuracion

```python
# settings.py

# Backend para desarrollo (ejecuta inmediatamente, sincrono)
TASKS_BACKEND = "django.tasks.backends.ImmediateBackend"

# Backend dummy (no ejecuta, util para tests)
# TASKS_BACKEND = "django.tasks.backends.DummyBackend"

# Backend de produccion (requiere paquete de terceros)
# TASKS_BACKEND = "django_tasks_database.DatabaseBackend"
```

### Backends de produccion (terceros)

Django solo incluye backends de desarrollo. Para produccion:

| Backend | Paquete | Broker |
|---------|---------|--------|
| Database | `django-tasks-database` | PostgreSQL/MySQL |
| Redis | `django-tasks-redis` | Redis |

```bash
# Instalar backend de base de datos
uv add django-tasks-database
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_tasks_database",
]
TASKS_BACKEND = "django_tasks_database.DatabaseBackend"
```

```bash
# Crear tabla de tareas
python manage.py migrate

# Ejecutar worker de tareas
python manage.py run_tasks
```

## @task decorator

```python
from django.tasks import task

@task()
def send_welcome_email(user_id: int) -> None:
    """Envia email de bienvenida al usuario."""
    user = User.objects.get(id=user_id)
    user.email_user(
        subject="Bienvenido",
        message=f"Hola {user.first_name}",
    )

@task(priority=10)
def process_payment(payment_id: int) -> dict:
    """Procesa un pago con prioridad alta."""
    payment = Payment.objects.get(id=payment_id)
    result = gateway.charge(payment)
    return {"status": result.status, "transaction_id": result.id}
```

### Parametros del decorator

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `priority` | int | 0 | Prioridad (mayor = primero) |
| `queue` | str | "default" | Cola de ejecucion |
| `unique` | bool | False | Evitar duplicados |

## Enqueue

```python
# En una vista
from myapp.tasks import send_welcome_email, process_payment

def register_user(request):
    user = User.objects.create_user(...)

    # Encolar tarea - NO ejecuta inmediatamente
    result = send_welcome_email.enqueue(user.id)

    # result es un TaskResult con metodos utiles
    print(result.id)        # UUID de la tarea
    print(result.status)    # "pending", "running", "completed", "failed"

    return redirect("dashboard")
```

### Encolar con opciones

```python
from datetime import timedelta

# Ejecutar con delay
send_welcome_email.enqueue(user.id, run_after=timedelta(minutes=5))

# Ejecutar en cola especifica
process_payment.enqueue(payment.id, queue="high_priority")
```

## Retry y error handling

```python
from django.tasks import task
import logging

logger = logging.getLogger(__name__)

@task()
def call_external_api(endpoint: str, payload: dict) -> dict:
    """Llama a API externa con manejo de errores."""
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API call failed: {e}")
        raise  # Re-raise para que el backend maneje el retry
```

El mecanismo de retry depende del backend:

```python
# django-tasks-database soporta retry nativo
TASKS_BACKEND = "django_tasks_database.DatabaseBackend"
TASKS_DATABASE_BACKEND = {
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 60,  # segundos
}
```

## Integracion con rezebra

Ejemplo de uso para procesamiento en lote:

```python
from django.tasks import task
from myapp.services import process_item, upload_to_s3

@task(queue="processing")
def process_and_upload(item_id: int, s3_key: str) -> str:
    """Procesa un item y sube resultado a S3."""
    result_bytes = process_item(item_id)
    url = upload_to_s3(result_bytes, s3_key)
    return url

# En la vista o script
for i, item_id in enumerate(item_ids):
    process_and_upload.enqueue(
        item_id=item_id,
        s3_key=f"results/batch_{batch_id}/{i}.pdf",
    )
```

## Celery vs Background Tasks

| Aspecto | Django Background Tasks | Celery |
|---------|------------------------|--------|
| Setup | Minimo (built-in) | Requiere broker (Redis/RabbitMQ) |
| Dependencias | Solo Django | celery + broker + result backend |
| Tareas periodicas | No soportado (usar django-tasks-scheduler) | Beat scheduler built-in |
| Workflows | No soportado | Chains, groups, chords |
| Monitoring | Basico (admin) | Flower, eventos, metricas |
| Distribuido | Limitado | Multi-worker, multi-nodo |
| Retry | Via backend de terceros | Built-in con backoff |
| Caso de uso | Tareas simples, emails, webhooks | Workflows complejos, distribuido |
| Performance | Adecuado para volumen bajo-medio | Alto volumen, baja latencia |

### Cuando usar Background Tasks

- Envio de emails/notificaciones
- Llamadas a APIs externas (webhooks, procesamiento)
- Procesamiento de archivos pequenos
- Proyectos que no justifican un broker dedicado

### Cuando usar Celery

- Tareas periodicas (cron-like)
- Workflows complejos (chains, groups)
- Alto volumen de tareas (>1000/min)
- Arquitectura distribuida multi-nodo
- Requiere monitoring avanzado

## Limitaciones

1. **Sin tareas periodicas** nativas (necesita `django-tasks-scheduler` u otro)
2. **Sin workflows** (chains, groups, chords como Celery)
3. **Backends de produccion son terceros** (Django solo incluye desarrollo)
4. **Sin dashboard de monitoring** built-in (depende del backend)
5. **Retry limitado** al backend elegido
6. **Sin soporte multi-nodo** real (limitado a un worker por defecto)

---

[Anterior: API Reference](01-api-reference.md) | [Volver al indice](README.md)
