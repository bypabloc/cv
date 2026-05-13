---
description: "Estandares de base de datos PostgreSQL 18 con Django 6: modelos, constraints, indexes, migrations, QuerySets y prevencion de N+1"
globs: "server/apps/*/models/**/*.py,server/apps/*/migrations/*.py"
---

# Database Standards - Rezebra

> Reglas para PostgreSQL 18 con Django 6 ORM.

## Modelos base

- SIEMPRE heredar de `TimestampedModel` (UUIDv7 PK + created_at + updated_at)
- PK via `db_default=Func(function='uuidv7')` (PostgreSQL 18 nativo)
- NUNCA usar UUID4 manual ni IDs secuenciales
- ForeignKey a User: usar `settings.AUTH_USER_MODEL`
- `db_default` para defaults a nivel de base de datos (mejor integridad)

## Constraints (CRITICO)

- Django 6: `CheckConstraint` usa `condition=` (NO `check=`)
- UniqueConstraint con `name` descriptivo: `uq_<modelo>_<campos>`
- CheckConstraint con `name`: `ck_<modelo>_<logica>`
- Preferir constraints a nivel de DB sobre validacion solo en Python

```python
# Ejemplo: Appointment sin solapamiento para mismo staff
constraints = [
    models.UniqueConstraint(
        fields=['business', 'staff', 'start'],
        name='uq_appointment_business_staff_start',
    ),
    models.CheckConstraint(
        condition=Q(price_amount_cents__gte=0),
        name='ck_appointment_non_negative_price',
    ),
]
```

## Indexes

- Index en campos usados frecuentemente en WHERE/ORDER BY
- Partial indexes con `condition=` para filtros comunes
- GIN indexes para JSONField y full-text search
- Index en `created_at` viene automatico de TimestampedModel

```python
indexes = [
    # Citas activas por negocio + fecha: patron de consulta mas frecuente
    models.Index(fields=['business', 'start', 'status']),
    models.Index(
        fields=['business', 'staff', 'start'],
        condition=Q(status__in=['CONFIRMED', 'PENDING']),
        name='ix_appointment_active_by_staff',
    ),
]
```

## QuerySets custom

- Definir QuerySet custom para filtros reutilizables
- Usar `as_manager()` para registrar como manager

```python
class AppointmentQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(status=AppointmentStatus.CANCELLED)

    def for_business(self, business):
        return self.filter(business=business)

class Appointment(TimestampedModel):
    objects = AppointmentQuerySet.as_manager()
```

## SELECT FOR UPDATE SKIP LOCKED (reserva atomica de slots)

Para crear citas sin race conditions, usar `select_for_update(skip_locked=True)`
dentro de `@transaction.atomic`:

```python
@transaction.atomic
def reserve_slot(*, business, staff, start, end):
    conflict = (
        Appointment.objects
        .select_for_update(skip_locked=True)
        .filter(
            business=business,
            staff=staff,
            status__in=['CONFIRMED', 'PENDING'],
            start__lt=end,
            end__gt=start,
        )
        .exists()
    )
    if conflict:
        raise SlotTakenError("El slot ya fue reservado", extra={'start': str(start)})
```

## Prevencion de N+1 (CRITICO)

- `select_related()` para FK y OneToOne (JOIN en SQL)
- `prefetch_related()` para M2M y reverse FK (query separada)
- Aplicar en selectors, NUNCA en views
- `.exists()` en vez de `.count() > 0`
- `.only()`/`.defer()` para modelos con muchos campos
- `F()` expressions para updates atomicos
- `bulk_create()`/`bulk_update()` con `batch_size` para operaciones masivas

## Natural keys (fixtures)

- Implementar `natural_key()` en modelos que se cargan via fixtures
- Retornar tupla con campo(s) unico(s): `return (self.name,)`
- Fixture resolution: FK fields resueltos por nombre natural

## Migrations

- Auto-generadas via `makemigrations` — NUNCA editar SQL manualmente
- Seeds via `RunPython` en migrations numeradas (0002_seed_*)
- Seeds SIEMPRE reversibles (reverse function que borra lo insertado)
- Usar `apps.get_model()` en migrations, no imports directos
- Despues de crear/modificar: `python devtools/run.py docker migrate`

## GeneratedField (PG18)

- `GeneratedField(db_persist=False)` para columnas virtuales
- Ideal para campos derivados que no necesitan almacenamiento
- Evita inconsistencias entre campo calculado y datos base
