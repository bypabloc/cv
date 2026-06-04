# 04 — Backend: analytics con timestamps + bucket minute/hour

[← users](03-backend-users.md) · [Siguiente: settings tabs →](05-admin-settings-tabs.md)

> Cubre AC-3, AC-4. Lambda `analytics`. Sin migration (solo modelos +
> services). RETROCOMPATIBLE: el cliente que sigue mandando `date` (sin hora)
> funciona idéntico.

## Estado actual

- `DateRange` (`models/_common.py`): `date_from`/`date_to` son `date`,
  defaults 30d, max 90d, `date_to_exclusive() = date_to + 1 día`.
- `TimeseriesInput` (`models/analytics.py`): `bucket: str =
  Field(default='day', pattern='^(day|hour|week)$')`.
- `analytics_service.timeseries`: `func.date_trunc(bucket,
  TrackingEvent.created_at)`.
- Los services bindean el rango con `date_from` y `date_to_exclusive()`.

## Solución (retrocompatible)

### AC-3 — `from`/`to` aceptan datetime con hora

`DateRange` pasa a aceptar **`datetime | date`** en `from`/`to`. Pydantic
parsea tanto `2026-06-03` (date → medianoche) como `2026-06-03T18:00:00Z`
(datetime). Internamente se normaliza a `datetime` aware (UTC). El límite
superior exclusivo cambia:

- Si el cliente mandó una **fecha** (sin hora): mantener la convención
  half-open actual (`date_to` + 1 día) → el día `to` queda incluido.
- Si mandó un **datetime** (con hora): el `to` es exclusivo directo (no se
  suma 1 día), porque la hora ya es precisa.

```python
# models/_common.py — DateRange (reescrito, retrocompatible)
from datetime import date, datetime, time, timedelta, UTC

class DateRange(BaseModel):
    date_from: datetime | None = Field(default=None, alias='from')
    date_to: datetime | None = Field(default=None, alias='to')
    # Pydantic coacciona "2026-06-03" (date) a datetime medianoche y
    # "2026-06-03T18:00:00Z" a datetime aware. Guardamos un flag interno
    # para saber si el `to` venía sin hora (para la convención half-open).
    ...
    # _to_has_time: bool  # True si el input traía hora
```

El span (max 90d) se valida con `timedelta` (`(to - from) <= 90 días`),
cubriendo tanto fechas como datetimes. `date_to_exclusive()` devuelve el
`datetime` exclusivo: `date_to + 1 día` si vino sin hora, o `date_to` tal
cual si vino con hora.

> Implementación cuidadosa: Pydantic v2 coacciona `"2026-06-03"` a
> `datetime(2026,6,3,0,0)` y `"...T18:00:00Z"` a aware. Para distinguir "vino
> sin hora", se puede usar un `field_validator(mode='before')` que detecte si
> el string original es solo-fecha (len 10, sin `T`) y setear el flag. Cubrir
> con tests ambos formatos.

### AC-4 — `bucket=minute`

`TimeseriesInput.bucket` pasa el pattern a
`^(minute|hour|day|week)$`. El service ya hace `func.date_trunc(bucket, ...)`
— `date_trunc('minute', ...)` es válido en PostgreSQL, así que NO requiere
cambio en el service salvo verificar que el `bucket` llega tal cual.

> Guard de cardinalidad: un rango de 90 días con `bucket=minute` daría
> ~130k puntos. Agregar validación: si `bucket=minute`, el rango no puede
> exceder ~24h (o el límite que tenga sentido); si `bucket=hour`, max ~14d.
> Documentar los límites por bucket en `TimeseriesInput` (validator que
> combina bucket + span). Esto protege la query y el payload.

## 7. Archivos afectados (fase 4)

### Modificar
- `serverless/lambda/services/analytics/core/models/_common.py` — `DateRange`
  acepta `datetime | date`, normaliza a aware UTC, `date_to_exclusive`
  condicional, span por timedelta. Retrocompatible con date-only.
  - Verificar: `serverless tests --type=unit --lambda=analytics`.
- `serverless/lambda/services/analytics/core/models/analytics.py` —
  `TimeseriesInput.bucket` pattern `^(minute|hour|day|week)$` + validator de
  cardinalidad (bucket vs span).
  - Verificar: idem.
- (revisar) `analytics_service.py` — confirmar que todos los services que
  usan `date_to_exclusive()` siguen correctos con datetime (probablemente sí,
  porque comparan `created_at < date_to_exclusive`). Ajustar binds si algún
  service asumía `date` puro.
  - Verificar: `serverless tests --type=unit --lambda=analytics`.

### Crear
- `serverless/lambda/services/analytics/tests/unit/models/test_daterange_datetime.py`
  — from/to con hora respetada; date-only retrocompatible; span por
  timedelta. [AC-3]
- `serverless/lambda/services/analytics/tests/unit/models/test_timeseries_bucket_minute.py`
  — bucket=minute aceptado; cardinalidad guard. [AC-4]

### NO se toca
- El schema / migration (ninguno: `date_trunc` opera sobre `created_at`).
- Los demás endpoints (overview, top-pages, etc.) heredan el `DateRange`
  extendido sin cambio funcional (retrocompatible).

## Verificación (fase 4)

```bash
python devtools/run.py serverless lint-deps --lambda=analytics
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=coverage --lambda=analytics  # >=80%
```

Parte C (dev real): tras redeploy de `analytics`, invoke `timeseries` con
`from`/`to` datetime + `bucket=minute` → puntos por minuto. [AC-3, AC-4]

[← users](03-backend-users.md) · [Siguiente: settings tabs →](05-admin-settings-tabs.md)
