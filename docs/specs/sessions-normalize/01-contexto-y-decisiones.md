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
| --- | --- | --- |
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
`(ip, utm_source, utm_medium, utm_campaign, utm_content, utm_term)`
(decision 9 — los 6 campos al completo, incluye `utm_content` y
`utm_term`).

### Hallazgo del audit: niches duplicados en backend + frontend

Antes de implementar este plan, busqueda exhaustiva en el repo encontro
que `_VALID_NICHES` se define en al menos 2 lugares con scopes
diferentes:

- `serverless/lambda/services/cv/core/models/cv.py:18` — `frozenset({'fintech', 'architect', 'leader', 'vibe', 'generic'})` (5 niches, sin `hub`). Usado para filtrar contenido del CV.
- `packages/content/src/lib/cv-api-client.ts:26` — `type CvNiche = 'fintech' | 'architect' | 'leader' | 'vibe' | 'generic'`.

El portfolio tiene 6 sitios (los 5 del CV mas `hub` — el selector
multi-niche). `hub` NO existe en `_VALID_NICHES` porque el CV no tiene
contenido especifico para hub, pero SI debe poder persistirse en
`tracking_events.niche` y `session_visits.niche` cuando el visitante
esta en `hub.portfolio.*`. Decision 13 introduce un modulo central con
ambos conceptos.

## 2. Solucion Propuesta

3 tablas relacionadas + un modulo central de niches:

```text
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
- `event_count` (INTEGER, default 0 — cache denormalizado; cada
  `tracking_events` INSERT incrementa via UPDATE en la misma tx;
  decision 12)
- `ip`, `country` (snapshot al inicio de la visit)
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`
  (los 6 campos disparan nuevo visit ante cambio)
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
-> `niche='fintech'`. La logica vive en
`shared/core/niches.niche_from_origin` (decision 13).

### Modulo central de niches: `shared/core/niches.py` (decision 13)

Una sola fuente de verdad. Reemplaza el `_VALID_NICHES` local del
Lambda `cv`. Expone:

```python
# serverless/lambda/shared/core/niches.py

ALL_NICHES: frozenset[str] = frozenset({
    'hub', 'fintech', 'architect', 'leader', 'vibe', 'generic',
})
"""Los 6 niches/subdominios reales del portfolio. Usar para tracking,
session_visits.niche, y validacion de entrada cuando aplique."""

CV_NICHES: frozenset[str] = ALL_NICHES - {'hub'}
"""Los 5 niches con contenido en el CV. `hub` es solo selector,
no tiene CV propio. Usar SOLO en el Lambda `cv` para filtrado."""


def niche_from_origin(origin: str | None) -> str | None:
    """Infiere el niche del Origin header del request HTTP.

    Parsea el primer label del hostname y matchea contra ALL_NICHES.
    Retorna None si origin es None, no es una URL valida, o el primer
    label no esta en ALL_NICHES.

    Ejemplos:
        'https://fintech.portfolio.dev.the-full-stack.com' -> 'fintech'
        'https://the-full-stack.com'                       -> None
        None                                                -> None
    """
```

Cambios en consumidores:

- `services/cv/core/models/cv.py` importa `CV_NICHES` desde
  `shared.core.niches` y elimina su `_VALID_NICHES` local.
- `services/contact_form/core/controllers/contact/create.py` importa
  `niche_from_origin` y lo usa cuando el form no envia `niche`.
- `services/tracking_pixel/core/services/tracking_service.py` puede
  importar `ALL_NICHES` si se decide validar el `niche` recibido del
  cliente (defensa antes de persistirlo).

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
    2. SELECT ultimo visit del session ORDER BY started_at DESC LIMIT 1
       FOR UPDATE (evita race entre 2 events concurrentes).
    3. Si no existe O cualquiera de (ip, utm_source, utm_medium,
       utm_campaign, utm_content, utm_term) cambio respecto al ultimo
       visit -> INSERT nuevo visit (event_count = 1 al crearse junto
       con su primer tracking_event).
       Si igual -> UPDATE ended_at=now(), event_count = event_count + 1
       en el visit existente, reusa.
    """
```

NOTA sobre el `event_count`: el helper NO incrementa por si solo —
incrementar es responsabilidad del INSERT del `tracking_event`/`contact`
que viene a continuacion. En la **misma transaccion** del Lambda, tras
recibir `visit_id` del helper, el caller hace:

```sql
UPDATE session_visits
   SET ended_at = now(),
       event_count = event_count + 1
 WHERE visit_id = :visit_id;
INSERT INTO tracking_events (..., session_id, visit_id) VALUES (...);
COMMIT;
```

Para evitar duplicar este UPDATE en ambos services, el helper expone
una variante `ensure_session_and_visit_and_bump_count(...)` o
incorpora el bump dentro del propio helper como parametro
`bump_event_count: bool = True`. Decision interna: incorporarlo
con el parametro flag para simplicidad.

Concurrencia: `SELECT ... FOR UPDATE` en el paso 2 para evitar 2
events concurrentes del mismo `session_id` creando 2 visits
redundantes. El UPDATE de `event_count` queda lockado en la misma row.

## 3. Criterios de Aceptacion (AC)

Formato BDD. Fuente de verdad referenciada por tests + tareas.

- **AC-1**: Given un evento `/track` con `session_id=X` que no existe
  en la DB, When el Lambda procesa, Then se crea una row en `sessions`
  (con `first_seen_at = last_seen_at = now()`) y una row en
  `session_visits` (con `started_at = ended_at = now()` y
  `event_count = 1`).
- **AC-2**: Given un evento `/track` con `session_id=X` ya existente y
  los 6 campos `(ip, utm_source, utm_medium, utm_campaign, utm_content,
  utm_term)` IGUALES al ultimo visit, When el Lambda procesa, Then NO
  se crea nuevo visit y `session_visits.ended_at` del visit actual se
  UPDATEa a `now()`. `session_visits.event_count` se incrementa en 1.
  `sessions.last_seen_at` tambien se UPDATEa.
- **AC-3**: Given un evento `/track` con `session_id=X` ya existente y
  `ip` distinta al ultimo visit, When el Lambda procesa, Then se crea
  un NUEVO `session_visits` row con `event_count = 1` y se enlaza
  `tracking_events.visit_id` al nuevo visit_id.
- **AC-4**: Given un evento `/track` con `session_id=X` ya existente y
  cualquiera de `utm_source/medium/campaign/content/term` distinto al
  ultimo visit, When el Lambda procesa, Then se crea NUEVO visit
  (igual que AC-3). Esto cubre los 5 campos UTM.
- **AC-5**: Given un evento `/track` con `session_id=X`, Then la row
  resultante en `tracking_events` tiene `session_id=X` y `visit_id` =
  el id del visit donde cae el evento (el reusado en AC-2, el nuevo
  en AC-3/AC-4).
- **AC-6**: Given un POST `/contact` con `session_id=Y` que NO existe
  en `sessions`, When el Lambda procesa, Then crea la session
  on-the-fly con ip/ua/country del request y un primer visit con
  `niche = niche-derivado-del-Origin-header`, `landing_page_path=NULL`,
  `utm_*=NULL`, `event_count=1`. El contact se inserta con
  `session_id=Y` y la FK pasa.
- **AC-7**: Given un POST `/contact` con `session_id=Y` que SI existe
  (porque hubo `/track` previo), When el Lambda procesa, Then ejecuta
  el mismo `ensure_session_and_visit` (puede crear o reusar visit) y
  el contact se inserta. `contacts.session_id` matchea. El
  `event_count` del visit usado se incrementa.
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
- **AC-13**: Given el modulo `shared/core/niches.py` existe, Then:
  (a) `ALL_NICHES == {'hub', 'fintech', 'architect', 'leader', 'vibe',
  'generic'}` (6 niches);
  (b) `CV_NICHES == ALL_NICHES - {'hub'}` (5 niches);
  (c) `niche_from_origin('https://fintech.portfolio.dev.the-full-stack.com')
  == 'fintech'`;
  (d) `niche_from_origin('https://the-full-stack.com') is None`;
  (e) `niche_from_origin(None) is None`.
- **AC-14**: Given el refactor de centralizacion, Then
  `services/cv/core/models/cv.py` YA NO define `_VALID_NICHES` y en
  su lugar importa `CV_NICHES` desde `shared.core.niches`. Los tests
  existentes del Lambda `cv` (filtrado por niche) siguen verdes.
- **AC-15**: Given un INSERT de tracking_event sobre un visit
  existente, Then el `event_count` del visit se incrementa en
  exactamente 1 en la misma transaccion (NO en una tx aparte). Si el
  INSERT del tracking_event falla, el incremento se revierte.
- **AC-16**: Given una serie de N eventos en una misma visit, Then
  `session_visits.event_count == COUNT(*) FROM tracking_events WHERE
  visit_id = X`. Esta invariante se verifica con un query SQL
  post-pruebas E2E (parte del gate de cierre).

[← README](README.md) | [Siguiente: Diagrama ER →](02-diagrama-er.md)
