# 01 — Contexto, solucion y criterios de aceptacion

[← README](README.md) | [Siguiente: Diagrama ER →](02-diagrama-er.md)

## 1. Contexto / Problema

Hoy en Neon hay 2 tablas de "datos de negocio":

- **`tracking_events`** (replica analitica del journey): cada page_load /
  click / scroll del visitante. Tiene `session_id`, `ip`, `country`,
  `user_agent`, `browser`, `browser_version`, `os`, `device_type`,
  `utm_source/medium/campaign/content/term`, `niche`, etc.
- **`contacts`** (envios del form de contacto): tiene `session_id`
  (nullable, NO FK), `ip`, `country`, `user_agent`, `niche`. Resto es
  data de negocio (`name`, `email`, `message`, etc.).

El visitante se identifica con `session_id` (texto generado por el
cliente en `localStorage` al primer page_load). El mismo `session_id`
puede aparecer en `tracking_events` muchas veces (1 row por evento) y
en `contacts` cuando completa el form.

### Duplicaciones identificadas

| Campo | tracking_events | contacts |
|---|---|---|
| `session_id` | si (NOT NULL) | si (NULL, sin FK) |
| `ip` | si | si |
| `country` | si | si |
| `user_agent` | si | si |
| `niche` | si | si |
| `browser`/`browser_version`/`os`/`device_type` | si | no |
| `viewport_width/height` | si | no |
| `utm_*` | si | no |

El usuario detecto que esto es **redundancia**: la identidad y los
datos de navegacion del visitante deberian vivir en una tabla aparte;
`tracking_events` y `contacts` deberian solo referenciarla.

### Caso edge identificado por el usuario

> "¿Que pasa si entra varias veces desde diferentes redes? ¿O desde
> diferentes fuentes y se marca diferentes utms? ¿Solo se conserva el
> primero y el ultimo?"

Un visitante con el mismo `session_id` (porque su `localStorage` persiste)
puede:
- Dia 1: entrar desde Twitter (utm_source=twitter), IP=1.1.1.1 (casa)
- Dia 2: entrar desde LinkedIn (utm_source=linkedin), IP=2.2.2.2 (oficina)
- Dia 3: entrar directo desde bookmark, IP=3.3.3.3 (mobile, 4G)

Con un "snapshot inmutable" solo conservamos el primer touch (Twitter).
Con "first + last" perdemos LinkedIn. Con "todas las visitas en
`tracking_events`" tenemos granularidad pero tracking_events vuelve a
tener `utm_*`/`ip`/`country` por evento (regreso al estado actual).

La decision tomada (decision 8) es separar `session_visits`: una row por
cada visita "distinta" del visitante, identificada por el cambio en
`(ip, utm_source, utm_medium, utm_campaign)`.

## 2. Solucion Propuesta

3 tablas relacionadas:

```
sessions (identidad estable)
  ── 1:N ── session_visits (cada cambio de network/utm)
                                  ── 1:N ── tracking_events (cada evento web)
                                  ── 1:N ── contacts (form submits — opcional via visit, obligatorio via session)
```

### `sessions` — identidad estable del visitante (decision 10)

PK = `session_id` (texto, viene del cliente). Datos del visitante que
varian poco dentro del mismo `session_id`:

- `first_seen_at`, `last_seen_at` (timestamps)
- `user_agent`, `browser`, `browser_version`, `os`, `device_type`

`last_seen_at` se UPDATEa en cada UPSERT. Los demas campos son
**snapshot inmutable del primer evento** — si Chrome se actualiza y el
UA cambia, NO se sobrescribe (decision 1).

### `session_visits` — cada combinacion (ip, utm_*) distinta (decision 8)

PK = `visit_id` (UUIDv7 server-side, `uuidv7()` PG18). Una row por
"visita logica":

- `session_id` (FK a `sessions`)
- `started_at`, `ended_at` (timestamps; `ended_at` se UPDATEa al
  ultimo evento de la visit)
- `ip`, `country` (snapshot al inicio de la visit)
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`
- `referrer` (referer original del landing de la visit)
- `landing_page_path` (page_path del primer evento de la visit)
- `niche` (niche del landing — decision 11: no cambia dentro de la
  visit aunque el visitante navegue a otro niche)

### `tracking_events` — modificada

Mantiene su rol de "1 row por evento" pero PIERDE las columnas que se
movieron a `sessions`/`session_visits`. Agrega 2 FKs:

- `session_id` NOT NULL → `sessions(session_id)`
- `visit_id` NOT NULL → `session_visits(visit_id)`

**Columnas que pierde**: `ip`, `country`, `user_agent`, `browser`,
`browser_version`, `os`, `device_type`, `utm_source`, `utm_medium`,
`utm_campaign`, `utm_content`, `utm_term`.

**Columnas que conserva**: `page_id`, `created_at`, `received_at`,
`page_path`, `event_id`, `event_type_id`, `event_props`,
`viewport_width`, `viewport_height`, `niche` (del evento — puede
diferir del niche de la visit; ver decision 11).

### `contacts` — modificada

Mantiene su rol de "1 row por envio del form". Cambia `session_id` de
nullable sin FK a **NOT NULL + FK**:

- `session_id` NOT NULL → `sessions(session_id)`
- **Columnas que pierde**: `ip`, `country`, `user_agent`.

Si `/contact` llega sin un `/track` previo (decision 2 — adblock, JS
bloqueado, primer click directo al form), el Lambda crea la session
on-the-fly. Para inferir `niche` cuando no hay visit previa, se usa el
header `Origin` (decision 6): `fintech.portfolio.dev.the-full-stack.com`
-> `niche='fintech'`.

### Logica del backend: `ensure_session_and_visit(...)`

Helper en `shared/db/repository.py` que ambos Lambdas
(`tracking_pixel` y `contact_form`) invocan dentro de la misma
transaccion del INSERT del event/contact:

```python
def ensure_session_and_visit(
    session: Session,
    *,
    session_id: str,
    ip: str | None,
    country: str | None,
    user_agent: str | None,
    browser: str | None,
    browser_version: str | None,
    os_name: str | None,
    device_type: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    utm_content: str | None,
    utm_term: str | None,
    referrer: str | None,
    landing_page_path: str | None,
    niche: str | None,
) -> tuple[str, str]:
    """Devuelve (session_id, visit_id). Idempotente.

    Pasos:
    1. UPSERT en `sessions`: si no existe, crea. Si existe, SET
       last_seen_at=now() (snapshot resto inmutable).
    2. SELECT ultimo visit del session ORDER BY started_at DESC LIMIT 1.
    3. Si no existe O (ip, utm_source, utm_medium, utm_campaign) cambio
       respecto al ultimo visit -> INSERT nuevo visit.
       Si igual -> UPDATE ended_at=now() en el visit existente, reusa.
    """
```

Concurrencia: `SELECT ... FOR UPDATE` en el paso 2 para evitar 2 events
concurrentes del mismo `session_id` creando 2 visits redundantes.

## 3. Criterios de Aceptacion (AC)

Formato BDD. Fuente de verdad referenciada por tests + tareas.

- **AC-1**: Given un evento `/track` con `session_id=X` que no existe
  en la DB, When el Lambda procesa, Then se crea una row en `sessions`
  (con `first_seen_at = last_seen_at = now()`) y una row en
  `session_visits` (con `started_at = ended_at = now()`).
- **AC-2**: Given un evento `/track` con `session_id=X` ya existente y
  `(ip, utm_*)` IGUAL al ultimo visit, When el Lambda procesa, Then NO
  se crea nuevo visit y `session_visits.ended_at` del visit actual se
  UPDATEa a `now()`. `sessions.last_seen_at` tambien se UPDATEa.
- **AC-3**: Given un evento `/track` con `session_id=X` ya existente y
  `ip` distinta al ultimo visit, When el Lambda procesa, Then se crea
  un NUEVO `session_visits` row con el nuevo `(ip, utm_*)` y se enlaza
  `tracking_events.visit_id` al nuevo visit_id.
- **AC-4**: Given un evento `/track` con `session_id=X` ya existente y
  cualquier `utm_source/medium/campaign` distinto al ultimo visit,
  When el Lambda procesa, Then se crea NUEVO visit (igual que AC-3).
- **AC-5**: Given un evento `/track` con `session_id=X`, Then la row
  resultante en `tracking_events` tiene `session_id=X` y `visit_id` =
  el id del visit donde cae el evento (el reusado en AC-2, el nuevo
  en AC-3/AC-4).
- **AC-6**: Given un POST `/contact` con `session_id=Y` que NO existe
  en `sessions`, When el Lambda procesa, Then crea la session
  on-the-fly con ip/ua/country del request y un primer visit con
  `niche = niche-derivado-del-Origin-header`, `landing_page_path=NULL`,
  `utm_*=NULL`. El contact se inserta con `session_id=Y` y la FK pasa.
- **AC-7**: Given un POST `/contact` con `session_id=Y` que SI existe
  (porque hubo `/track` previo), When el Lambda procesa, Then ejecuta
  el mismo `ensure_session_and_visit` (puede crear o reusar visit) y
  el contact se inserta. `contacts.session_id` matchea.
- **AC-8**: Given el schema final, Then `tracking_events` NO tiene las
  columnas `ip`, `country`, `user_agent`, `browser`, `browser_version`,
  `os`, `device_type`, `utm_source`, `utm_medium`, `utm_campaign`,
  `utm_content`, `utm_term`. `contacts` NO tiene `ip`, `country`,
  `user_agent`.
- **AC-9**: Given el schema final, Then `tracking_events.session_id` y
  `tracking_events.visit_id` son `NOT NULL` con FKs a `sessions` y
  `session_visits`. `contacts.session_id` es `NOT NULL` con FK a
  `sessions`.
- **AC-10**: Given la migracion ejecutada en dev, Then las 3 tablas
  (`sessions`, `session_visits`, `tracking_events`, `contacts`) tienen
  0 rows post-TRUNCATE (decision 3).
- **AC-11**: Given un `DELETE FROM sessions WHERE session_id=X` con
  tracking_events o contacts existentes, Then el DELETE falla con
  `ForeignKeyViolation` (decision 7 — sin cascade).
- **AC-12**: Given la transaccion del Lambda falla en el INSERT final
  de `tracking_events` (ej. FK violation a `event_types`), Then NADA
  se persiste: la session, el visit y el event quedan revertidos en
  el rollback (atomicidad).

[← README](README.md) | [Siguiente: Diagrama ER →](02-diagrama-er.md)
