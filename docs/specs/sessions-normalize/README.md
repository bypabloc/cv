# Spec: sessions-normalize

> Normalizar el schema de Neon: extraer `sessions` (identidad estable del
> visitante) y `session_visits` (visitas multi-touch) como tablas
> dedicadas. `tracking_events` y `contacts` se referencian via FK a ambas.
> Elimina la duplicacion actual de `session_id`/`ip`/`country`/
> `user_agent`/`utm_*`/`browser`/`os`/`device_type` entre las dos tablas
> de "datos de negocio".

## Cuando leer

| Tema | Archivo | Cuando |
|---|---|---|
| Contexto + decisiones (no reabribles) | [01-contexto-y-decisiones.md](01-contexto-y-decisiones.md) | Antes de tocar nada del plan |
| Diagrama ER + schema SQL | [02-diagrama-er.md](02-diagrama-er.md) | Antes de escribir el modelo ORM / migration |
| Archivos afectados + comandos de verificacion | [03-archivos-afectados.md](03-archivos-afectados.md) | Antes de cada commit |
| Descomposicion en tareas atomicas | [04-descomposicion.md](04-descomposicion.md) | Antes de paralelizar o asignar |
| Secuencia de commits (Conventional Commits) | [05-commits.md](05-commits.md) | Mientras se implementa, en orden |
| Paralelizacion con git worktrees | [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) | Solo si se decide paralelizar |
| Verificacion E2E iterativa (gate de cierre) | [07-verificacion-e2e.md](07-verificacion-e2e.md) | Como ultima fase, antes del PR |

## Decisiones no reabribles (locked-in)

Las tomo el usuario en la conversacion previa al plan. NO se cambian sin
re-iniciar la spec:

1. **Update strategy de `sessions`**: snapshot inmutable + `last_seen_at`
   se UPDATE en cada evento. Cambios de IP/UA/utm dentro del mismo
   `session_id` NO sobrescriben el primer snapshot — generan una nueva
   `session_visit` (decision 8).
2. **`/contact` sin session previa**: el Lambda crea la session
   on-the-fly con los datos del request. `contacts.session_id` es
   `NOT NULL` + FK obligatoria.
3. **Migracion de datos existentes**: TRUNCATE en TODOS los stages
   (dev/stage/prod). No se consolida la data historica de
   `tracking_events` ni `contacts`. La spec elimina el riesgo a costa
   de perder los pocos registros de smoke testing en dev/prod.
4. **Scope de columnas**: maximo (identidad + adquisicion + niche).
5. **Modo de ejecucion**: plan formal primero (este documento) y luego
   implementacion.
6. **`niche` cuando `/contact` llega sin `/track` previo**: se infiere
   del header `Origin` del POST (ej. `fintech.portfolio.dev.the-full-stack.com`
   -> `niche='fintech'`).
7. **Cascade en FKs**: SIN cascade. `DELETE FROM sessions` falla si tiene
   `tracking_events` o `contacts`. GDPR / right-to-erasure se hace
   manual con orden inverso.
8. **Modelo multi-touch**: tabla `session_visits` separada. Cada
   combinacion distinta de `(ip, utm_source, utm_medium, utm_campaign)`
   genera un nuevo `visit_id` (UUIDv7).
9. **Visit trigger**: backend compara el ultimo visit del session (por
   `started_at DESC LIMIT 1`) contra el nuevo evento. Si
   `(ip, utm_source, utm_medium, utm_campaign)` cambio -> nuevo visit.
   Si igual -> reutiliza el visit_id existente y actualiza `ended_at`.
10. **Columnas de `sessions`**: `session_id`, `first_seen_at`,
    `last_seen_at`, `user_agent`, `browser`, `browser_version`, `os`,
    `device_type` (identidad estable). Todo lo demas
    (ip/country/utm/referrer/landing/niche) va en `session_visits`.
11. **Cambio de niche dentro de la misma visit**: NO dispara nuevo
    visit. `session_visits.niche` queda con el niche del landing_page
    de esa visit. `tracking_events.niche` guarda el niche del momento
    del evento (puede diferir).

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** las 3 escrituras (`session UPSERT`, `visit
  INSERT/UPDATE`, `tracking_event/contact INSERT`) van en **una sola
  transaccion**. Si el INSERT final falla, todo rollback.
- **SIEMPRE** el `visit_id` es server-side (`uuidv7()` en PG18), NUNCA
  generado por el cliente. El cliente no conoce este concepto.
- **SIEMPRE** el helper de UPSERT esta en `shared/db/repository.py`
  (`ensure_session_and_visit`) y se importa desde los 2 services
  (`tracking_pixel`, `contact_form`). NUNCA duplicar la logica.
- **SIEMPRE** las FK son `NOT NULL` (`session_id` y `visit_id` en
  tracking_events y contacts).
- **NUNCA** atribucion de IA en codigo, commits, ni el body del PR.
- **NUNCA** consolidar la data vieja (decision 3 — TRUNCATE en todos
  los stages).
- **NUNCA** dejar el plan a medias y declarar listo sin la verificacion
  E2E completa de [07-verificacion-e2e.md](07-verificacion-e2e.md).

## Estado por fase

| # | Fase | Archivo | Estado |
|---|---|---|---|
| 0 | Spec escrita | (este README + 01-07) | pending review |
| 1 | Migration Alembic + modelos ORM | [03-archivos-afectados.md](03-archivos-afectados.md#fase-1) | pending |
| 2 | Repository helper `ensure_session_and_visit` | [03-archivos-afectados.md](03-archivos-afectados.md#fase-2) | pending |
| 3 | `tracking_pixel`: integrar el helper | [03-archivos-afectados.md](03-archivos-afectados.md#fase-3) | pending |
| 4 | `contact_form`: integrar el helper + niche fallback Origin | [03-archivos-afectados.md](03-archivos-afectados.md#fase-4) | pending |
| 5 | Verificacion E2E (deploy dev + curls + CloudWatch checks) | [07-verificacion-e2e.md](07-verificacion-e2e.md) | pending |

## Matriz de verificacion

| Gate | Comando | Cuando |
|---|---|---|
| Unit tests pasan | `serverless tests --type=unit --lambda=tracking_pixel` y `--lambda=contact_form` | Cada fase |
| Lint | `pnpm exec biome check .` + Ruff (devtools) | Cada commit |
| Typecheck Python | `python -m compileall -q serverless/lambda/services/` | Cada commit |
| Integration tests | `serverless tests --type=integration --lambda=tracking_pixel` y `--lambda=contact_form` | Fase 5 |
| Migration up/down | `serverless run --stage=dev --lambda=db --event=events/migrate.json` y events/downgrade.json en un branch Neon de prueba | Fase 1 |
| /track devuelve 204 en dev con payload realista | `curl -X POST .../track` | Fase 5 |
| /contact devuelve 200 desde el browser real con form valido | manual | Fase 5 |
| `session_id` aparece en `sessions` post-tracking | `psql ... SELECT * FROM sessions WHERE session_id=...` | Fase 5 |
| 2 visits distintos por cambio de utm | `psql ... SELECT visit_id FROM session_visits WHERE session_id=...` | Fase 5 |

## Tamano

**Medium** (~8-10 archivos de codigo + 1 migration + tests). 5 fases con
~2-3 commits cada una.
