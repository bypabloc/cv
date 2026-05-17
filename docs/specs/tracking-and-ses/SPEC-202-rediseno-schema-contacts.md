# SPEC-202: Rediseno schema `contacts` con `session_id`

**Estado**: draft
**Fase**: 2
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/migrations/`, `serverless/src/contact_form/`,
`serverless/src/stream_processor/`, `packages/ui/`
**Dependencias**: SPEC-102 (el pixel ya genera `session_id` en
`localStorage.cf_session`)
**Paralelizable con**: SPEC-200, SPEC-201

> Anterior: [SPEC-201](SPEC-201-cookiebanner-gdpr.md) | Siguiente: [SPEC-203](SPEC-203-runbook-observability.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de SPEC-102 (el pixel ya genera `cf_session`).

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases |
| `serverless/src/contact_form/persistence.py` | Escritura actual del item `contacts` (se le quita ip/country/UA, se agrega session_id) |
| `serverless/src/contact_form/schemas.py` | `ContactFormInput` a extender con `session_id` |
| `serverless/src/contact_form/service.py` | Deja de inyectar ip/country/UA al payload de DynamoDB |
| `serverless/migrations/001_init_schema.sql` | Definicion SQL de `contacts` (referencia; NO se edita) |
| `serverless/src/stream_processor/pg_writer.py` | `INSERT` a `contacts` (Neon): agregar `session_id` |
| `packages/ui/src/components/ContactFormReact.tsx` | Lee `localStorage.cf_session` y lo envia en el body |
| `packages/ui/src/lib/contact-form-schema.ts` | Schema Zod espejo del Pydantic |
| `.claude/docs/postgresql-18-analytics/README.md` | Doc a actualizar con la query de correlacion |

### Rules del proyecto aplicables

- `.claude/rules/neon-management.md` — migration `010`, NUNCA editar migrations
  aplicadas, branch Neon, NUNCA `DROP COLUMN` sin migration separada
- `.claude/rules/python.md` — backend `contact_form`/`stream_processor`
- `.claude/rules/astro-landing.md` — `ContactFormReact.tsx`, TS strict
- `.claude/rules/markdown-docs.md` — al editar el doc de analytics

### Decisiones del interview que aplican

- `contacts` deja de duplicar `ip`/`country`/`user_agent`; gana `session_id`.
- El origen del contacto se consulta con `JOIN` a `tracking_events` por
  `session_id`.
- Las columnas legacy `ip`/`country`/`user_agent` NO se borran (datos
  historicos); solo se dejan de poblar.
- La IP sigue llegando al Lambda (la usa el rate-limit), solo no se persiste.
- `session_id` es opcional: un visitante sin `cf_session` se guarda igual.

## 1. Contexto

Hoy la tabla `contacts` (DynamoDB y PostgreSQL) guarda `ip`, `country` y
`user_agent` del momento del submit. Esa misma informacion — y mucha mas sobre
el journey del visitante — ya esta o estara en `tracking_events`. Duplicarla en
`contacts` es redundante.

El feedback del owner: `contacts` no deberia cargar los datos de "donde se
contactan"; eso pertenece a las tablas de tracking. La solucion no es borrar
todo de `contacts`, sino **enlazar**: que el form envie el `session_id` y se
guarde como clave de correlacion. Asi `contacts` queda con lo minimo (quien +
que dijo + `session_id`) y todo el "de donde viene / que vio" se consulta en
`tracking_events` con un `JOIN` por `session_id`.

### Hallazgos de exploracion

- `contact_form/persistence.py` escribe en el item de `contacts`: `id`,
  `created_at`, `name`, `email`, `message`, opcionales (`company`, `role`,
  `service_type`, `budget`, `timeline`, `niche`) y metadata (`ip`, `country`,
  `user_agent`).
- `contact_form/schemas.py` (`ContactFormInput`) NO acepta `session_id`.
- `serverless/migrations/001_init_schema.sql` define `contacts` con columnas
  `ip INET`, `country CHAR(2)`, `user_agent TEXT`. NO tiene `session_id`.
- `tracking_events` SI tiene `session_id` como parte de su PK.
- `ContactFormReact.tsx` NO lee `localStorage.cf_session` ni lo envia.
- `service.py` arma el payload de DynamoDB agregando `ip`/`country`/
  `user_agent` desde los headers; eso alimenta lo que `persistence.py` escribe.

## 2. Solucion propuesta

1. **Frontend**: `ContactFormReact.tsx` lee `localStorage.cf_session` (la misma
   key que usa el `TrackingPixel`) y lo incluye en el body del `POST /contact`.
   Si no existe sesion (usuario que nunca acepto tracking), se envia vacio /
   ausente — `session_id` es opcional en `contacts`.
2. **Backend schema**: `ContactFormInput` acepta `session_id` opcional
   (validado con el mismo formato que en tracking: 20-64 chars).
3. **Backend persistence**: `persistence.py` deja de escribir `ip`, `country`,
   `user_agent` en el item de `contacts`, y escribe `session_id`. `service.py`
   deja de inyectar esos tres campos al payload de DynamoDB.
4. **Migration `010_contacts_session_id.sql`**: `ALTER TABLE contacts ADD
   COLUMN session_id TEXT`, indice por `session_id`. Las columnas
   `ip`/`country`/`user_agent` se mantienen en SQL (datos historicos ya
   capturados) pero el `stream_processor` deja de poblarlas para contactos
   nuevos — quedan `NULL` de aqui en adelante.
5. **`stream_processor/pg_writer.py`**: el `INSERT` de `contacts` incluye
   `session_id` y omite `ip`/`country`/`user_agent` (o los deja `NULL`).
6. **Documentacion**: registrar el patron de correlacion (consulta de ejemplo
   `JOIN` por `session_id`) en `.claude/docs/postgresql-18-analytics/`.

> Nota sobre las columnas legacy: NO se hace `DROP COLUMN ip/country/user_agent`
> de `contacts`. Razon: hay filas historicas que ya las tienen pobladas; un
> `DROP` destruiria ese dato. Se dejan de escribir y se documentan como legacy.
> Si en el futuro se quiere limpiar, sera una migration aparte y explicita.

### Decisiones clave

- **Decision 1: enlazar, no duplicar** — `contacts` guarda `session_id`; el
  origen del contacto (IP, pais, navegador, journey) se consulta en
  `tracking_events`. Una sola fuente de verdad para los datos de navegacion.
- **Decision 2: `session_id` opcional en `contacts`** — un visitante que
  rechazo el tracking no tiene `cf_session`; su contacto se guarda igual sin
  correlacion. El form nunca debe fallar por falta de `session_id`.
- **Decision 3: no se borran las columnas legacy** — `ip`/`country`/
  `user_agent` se conservan en SQL por los datos historicos; solo se dejan de
  poblar. Evita perdida de datos.
- **Decision 4: la IP sigue llegando al Lambda** — `extract_ip` se mantiene:
  la IP se usa para rate-limit y anti-abuso (necesario), simplemente ya no se
  persiste en `contacts`. El valor anti-abuso es del momento, no del registro.
- **Decision 5: misma key `cf_session`** — el form reutiliza la sesion que ya
  genera el `TrackingPixel`; no se crea un identificador nuevo.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un visitante con `localStorage.cf_session` seteado, When
  envia el form de contacto, Then el body del `POST /contact` incluye
  `session_id` con ese valor.
- **AC-2**: Given un visitante sin `cf_session` (rechazo tracking o primera
  visita sin consentimiento), When envia el form, Then el `POST /contact` se
  procesa con exito sin `session_id` y el contacto se guarda igual.
- **AC-3**: Given un `POST /contact` con `session_id` valido, When se persiste
  en DynamoDB `ContactsTable`, Then el item incluye `session_id` y NO incluye
  `ip`, `country` ni `user_agent`.
- **AC-4**: Given un `session_id` con formato invalido (fuera de 20-64 chars),
  When valida el backend, Then responde `400 INVALID_INPUT`.
- **AC-5**: Given la migration `010` aplicada, When se inspecciona `contacts`
  en PostgreSQL, Then existe la columna `session_id TEXT` con su indice.
- **AC-6**: Given un contacto nuevo fluye por el Stream, When `stream_processor`
  lo replica, Then el `INSERT` en `contacts` (Neon) puebla `session_id` y deja
  `ip`/`country`/`user_agent` en `NULL`.
- **AC-7**: Given un contacto con `session_id` y eventos de tracking con el
  mismo `session_id`, When se ejecuta el `JOIN` documentado, Then se obtiene el
  journey de navegacion asociado a ese contacto.
- **AC-8**: Given filas historicas de `contacts` que ya tenian `ip`/`country`/
  `user_agent`, When se aplica la migration `010`, Then esas columnas y sus
  datos se conservan intactos (la migration NO las elimina).

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
POST /contact
  service.py: payload += ip, country, user_agent  (de los headers)
  persistence.py: item de contacts incluye ip/country/user_agent
  -> dato de navegacion DUPLICADO entre contacts y tracking_events
```

### Despues

```text
ContactFormReact lee localStorage.cf_session
POST /contact { ..., session_id }
  service.py: NO inyecta ip/country/user_agent al payload de DynamoDB
              (la IP se sigue usando para rate-limit, no se persiste)
  persistence.py: item de contacts incluye session_id, sin ip/country/UA
  stream_processor: INSERT contacts (session_id, ip=NULL, country=NULL, UA=NULL)

consulta del origen de un contacto:
  SELECT t.* FROM tracking_events t
    WHERE t.session_id = (SELECT session_id FROM contacts WHERE id = :id)
```

## 5. Diagrama ER

```text
contacts (modificado)              tracking_events
┌──────────────────────────┐       ┌──────────────────────────────┐
│ id          uuid PK      │       │ session_id   text       >────┤
│ session_id  text   (*)   │───────┤ page_id      uuid            │
│ created_at  datetime     │  corr. │ ip           inet            │
│ name, email, message     │  por   │ country      char(2)         │
│ company, role, ...       │ session│ user_agent   text            │
│ ip         inet  (legacy)│  _id   │ browser, os, device_type     │
│ country    char (legacy) │       │ event_id, event_type_id      │
│ user_agent text  (legacy)│       └──────────────────────────────┘
│ status, notes            │
└──────────────────────────┘

(*) columna nueva. ip/country/user_agent: legacy, ya no se pueblan
para contactos nuevos, no se eliminan. Correlacion logica via session_id
(sin FK formal: tracking_events tiene TTL y puede no existir la fila).
```

> No se declara FK `contacts.session_id -> tracking_events.session_id`:
> `tracking_events` tiene TTL de 60 dias y un contacto puede sobrevivir a sus
> eventos. La correlacion es logica, por `JOIN`, no por constraint.

## 6. Tests Requeridos

### 6.B. Unit Tests

**Backend (pytest, `serverless/tests/contact_form/`):**

- `test_schemas.py`: `session_id` opcional aceptado; formato invalido ->
  `ValidationError` `[AC-1][AC-4]`.
- `test_persistence.py`: el item de `contacts` incluye `session_id` y NO
  incluye `ip`/`country`/`user_agent` `[AC-3]`.
- `test_service.py`: `service.py` ya no inyecta `ip`/`country`/`user_agent` al
  payload de DynamoDB `[AC-3]`.
- `stream_processor`: el `INSERT` de `contacts` puebla `session_id` y deja las
  columnas legacy en `NULL` `[AC-6]`.

**Frontend (Vitest, `packages/ui/tests/unit/`):**

- Logica de `ContactFormReact`: lee `cf_session` de `localStorage` y lo agrega
  al payload; ausencia de sesion -> payload sin `session_id` `[AC-1][AC-2]`.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit`; `serverless typecheck`.

### 6.D. E2E Tests (Playwright)

`tests/feature/contact/contact-session-link.spec.ts`:

- WHEN acepto tracking, navego, y envio el form THEN el `POST /contact` lleva
  el mismo `session_id` que los eventos de `/track` `[AC-1][AC-7]`.
- WHEN rechazo tracking y envio el form THEN el contacto se guarda sin
  `session_id` `[AC-2]`.

## 7. Archivos Afectados

### Crear

- `serverless/migrations/010_contacts_session_id.sql` + `.down.sql` —
  `ALTER TABLE contacts ADD COLUMN session_id TEXT` + indice. El `.down`
  elimina solo la columna nueva (NO toca las legacy).
  - Por que: persistir la clave de correlacion en PostgreSQL.
  - Verificar: branch Neon, `migrate up`/`down`, `[AC-5][AC-8]`.
- `tests/feature/contact/contact-session-link.spec.ts` — E2E de la correlacion.
  - Verificar: `test_runner --module=feature --type=feature --env=local`.

### Modificar

- `serverless/src/contact_form/schemas.py` — agregar `session_id: str | None`
  a `ContactFormInput`, validado (20-64 chars cuando esta presente).
  - Por que: el backend debe aceptar y validar el `session_id` del form.
  - Verificar: `test_schemas.py` `[AC-1][AC-4]`.
- `serverless/src/contact_form/persistence.py` — escribir `session_id` en el
  item de `contacts`; quitar la escritura de `ip`/`country`/`user_agent`.
  - Por que: `contacts` deja de duplicar datos de navegacion.
  - Verificar: `test_persistence.py` `[AC-3]`.
- `serverless/src/contact_form/service.py` — dejar de inyectar `ip`,
  `country`, `user_agent` al payload de DynamoDB. `extract_ip` se mantiene
  porque la IP sigue usandose para el rate-limit.
  - Por que: la metadata de origen ya no va a `contacts`.
  - Verificar: `test_service.py` `[AC-3]`.
- `serverless/src/stream_processor/pg_writer.py` — el `INSERT` de `contacts`
  incluye `session_id`; `ip`/`country`/`user_agent` se pasan como `NULL`.
  - Por que: replicar el nuevo schema a Neon sin romper el `INSERT`.
  - Verificar: test de `pg_writer` `[AC-6]`.
- `packages/ui/src/components/ContactFormReact.tsx` — leer
  `localStorage.cf_session` y agregar `session_id` al body del `POST /contact`
  (ausente si no hay sesion).
  - Por que: el form debe enviar la clave de correlacion.
  - Verificar: unit test del form; `contact-session-link.spec.ts` `[AC-1][AC-2]`.
- `packages/ui/src/lib/contact-form-schema.ts` — agregar `session_id` opcional
  al schema Zod (espejo del Pydantic).
  - Por que: mantener la paridad de validacion cliente/servidor.
  - Verificar: `pnpm exec tsc --noEmit`.
- `.claude/docs/postgresql-18-analytics/README.md` — documentar el patron de
  correlacion `contacts` <-> `tracking_events` por `session_id` con una query
  `JOIN` de ejemplo.
  - Por que: dejar registrado como obtener el journey de un contacto.
  - Verificar: revision del doc; `[AC-7]`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `010_*.sql` (+ down) | AC-5,8 | — | T2, T3 |
| T2 | `schemas.py`, `persistence.py`, `service.py`, `pg_writer.py` + tests | AC-1,3,4,6 | — | T1, T3 |
| T3 | `ContactFormReact.tsx`, `contact-form-schema.ts` + unit | AC-1,2 | — | T1, T2 |
| T4 | doc analytics + `contact-session-link.spec.ts` | AC-7 | T1,T2,T3 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Fase 1 en `main` (el pixel ya genera `cf_session`)
- [ ] Branch Neon de prueba creado
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-8 cubiertos por tests que pasan
- [ ] Coverage >= 80% per-file en archivos modificados
- [ ] Migration `010` probada `up`/`down` en branch Neon, datos legacy intactos
- [ ] `pnpm exec tsc --noEmit` + `pnpm exec astro check` sin errores
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` de las 6 apps exitoso
- [ ] `serverless` lint/format/typecheck/validate pasan
- [ ] E2E `contact-session-link.spec.ts` verde
- [ ] Query de correlacion `JOIN` verificada en dev con datos reales
- [ ] Doc de analytics actualizada

> Anterior: [SPEC-201](SPEC-201-cookiebanner-gdpr.md) | Siguiente: [SPEC-203](SPEC-203-runbook-observability.md)
