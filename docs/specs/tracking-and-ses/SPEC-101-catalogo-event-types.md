# SPEC-101: Catalogo `event_types`

**Estado**: draft
**Fase**: 1
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/migrations/`, `packages/content/`
**Dependencias**: ninguna (SPEC-008 ya provee el schema base de Neon)
**Paralelizable con**: SPEC-100

> Anterior: [SPEC-100](SPEC-100-ses-funcional.md) | Siguiente: [SPEC-102](SPEC-102-trackingpixel-page-load.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases, DoD del backend |
| `serverless/migrations/005_migrations_log.sql` | Ver el patron de las migrations existentes y la tabla `migrations_log` |
| `serverless/migrations/001_init_schema.sql` | Ver como esta definida `tracking_events` (se le agregan columnas) |
| `serverless/scripts/migrate.py` | Runner de migrations: como aplica los pares `NNN_*.sql` |
| `packages/content/src/index.ts` | Barrel del package; se le agrega el re-export |
| `packages/content/src/lib/` (ej. `format-date.ts`) | Patron de un modulo TS de utilidad del package |
| `packages/content/tests/unit/lib/` | Patron de un test Vitest del package |

### Rules del proyecto aplicables

- `.claude/rules/neon-management.md` — runner de migrations, pares
  `.sql`/`.down.sql`, NUNCA editar una migration aplicada, probar en branch Neon
- `.claude/rules/astro-landing.md` — TypeScript strict, Biome, Vitest
- `.claude/rules/python.md` + skill `postgresql-18` — PostgreSQL 18, `uuidv7()`

### Decisiones del interview que aplican

- El catalogo `event_types` es la fuente de verdad; los UUID son fijos y se
  replican como constantes TS (cero requests del cliente).
- Las columnas de `tracking_events` van en migration aparte (007), separadas
  de la creacion del catalogo (006).

### UUID literales del catalogo (FIJOS — usar exactamente estos)

El seed de la migration `006` y el modulo `event-types.ts` DEBEN usar estos
UUIDv7. En Fase 1 solo se siembra `page_load`; el resto los siembra SPEC-200
(estan aqui para que ambos specs compartan la misma fuente).

```text
page_load               019e372b-e0a7-7154-8279-8829bcf6a08c
spa_navigation          019e372b-e0a7-70c6-8e56-2b643ddf1702
cta_click               019e372b-e0a7-793b-84ed-690388a13b15
nav_click               019e372b-e0a7-776d-8598-81772857f6a8
project_link_click      019e372b-e0a7-7c1b-b8e7-3d822a5ce42d
experience_link_click   019e372b-e0a7-7267-8f09-f81f75d90f64
cv_download             019e372b-e0a7-78a3-ad27-15dfd3d266a2
theme_toggle            019e372b-e0a7-767c-bbc4-d359c3522e86
external_link_click     019e372b-e0a7-7987-8699-8e6381865036
contact_view            019e372b-e0a7-7f8f-b568-3fbdb8a91756
contact_form_start      019e372b-e0a7-7467-a074-603b7e294cf8
contact_form_submit     019e372b-e0a7-7a02-b754-606a5fe38afc
contact_form_success    019e372b-e0a7-7d1b-9bd3-3cb2ee92b4d7
contact_form_error      019e372b-e0a7-77f6-897f-17f41a06b2c0
scroll_depth            019e372b-e0a7-7067-a5c5-d0baf8352385
page_exit               019e372b-e0a7-78dd-a3b5-7cf649c4638f
```

## 1. Contexto

El sistema de tracking necesita distinguir tipos de evento (`page_load`,
`cta_click`, `contact_submit`, etc.). Se decidio (interview previo) que exista
una tabla catalogo `event_types` en PostgreSQL con PK UUIDv7, `code_name` y
`description`. El frontend envia el `uuid` del tipo de evento en cada request
a `/track`; el backend lo persiste como FK al catalogo.

### Hallazgos de exploracion

- `serverless/migrations/` usa pares `NNN_*.sql` + `NNN_*.down.sql`. La ultima
  migration aplicada es `005_migrations_log.sql`. Las siguientes libres son
  `006`, `007`.
- `serverless/migrations/001_init_schema.sql` ya crea `tracking_events` y
  `contacts`. PostgreSQL 18 soporta `uuidv7()` nativo.
- El frontend NO debe consultar la DB para conocer los uuid. La decision es
  replicarlos como constantes TS generadas a partir del seed.
- `packages/content/src/lib/` agrupa utilidades TS compartidas por las 6 apps
  (`filter-by-niche.ts`, `format-date.ts`, etc.) y se re-exportan desde
  `packages/content/src/index.ts`. Es el lugar natural para el modulo de
  constantes de eventos.

## 2. Solucion propuesta

Esta spec crea SOLO el catalogo y la infraestructura de constantes. El seed
inicial incluye unicamente `page_load` (Fase 1); SPEC-200 amplia el seed con
el resto de eventos.

1. **Migration `006_event_types.sql`**: crear la tabla `event_types`
   (`id uuid PK default uuidv7()`, `code_name text UNIQUE NOT NULL`,
   `description text NOT NULL`, `created_at timestamptz default now()`) y
   sembrar la fila `page_load` con un UUID fijo conocido.
2. **Migration `007_tracking_event_columns.sql`**: agregar a `tracking_events`
   las columnas `event_id uuid` y `event_type_id uuid`, con FK
   `event_type_id REFERENCES event_types(id)`. Indice por `event_type_id`.
3. **Modulo TS `packages/content/src/lib/event-types.ts`**: exportar el objeto
   `EVENT_TYPES` con los mismos UUID del seed (`PAGE_LOAD: '<uuid>'`) y el tipo
   derivado. Re-exportar desde `packages/content/src/index.ts`.
4. **Test de paridad**: un test Vitest que parsea el `.sql` del seed y verifica
   que cada UUID de `EVENT_TYPES` coincide con el de la tabla — evita drift
   entre la fuente SQL y las constantes TS.

### Decisiones clave

- **Decision 1: catalogo en SQL, constantes en TS** — la tabla `event_types`
  es la fuente de verdad y la documentacion. Los UUID son fijos: se replican
  como constantes TS para que el cliente no haga requests ni consulte la DB.
- **Decision 2: UUID fijos hardcodeados en el seed** — el seed NO usa
  `uuidv7()` para `page_load`; usa un literal. Razon: el cliente necesita
  conocer el valor en build-time; un UUID generado en runtime seria imposible
  de replicar como constante.
- **Decision 3: las columnas de `tracking_events` van en migration aparte
  (007)** — separar "crear catalogo" de "enlazar tracking" mantiene cada
  migration con un cambio logico coherente y permite rollback granular.
- **Decision 4: el modulo vive en `packages/content`** — es el package que
  ya centraliza datos y constantes compartidas; las 6 apps y `packages/ui` lo
  importan sin crear una dependencia nueva.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given la migration `006` aplicada, When se consulta
  `SELECT code_name, description FROM event_types WHERE code_name='page_load'`,
  Then retorna exactamente una fila con una `description` no vacia.
- **AC-2**: Given la migration `006`, When se inspecciona la columna `id` de
  `event_types`, Then es `uuid`, PK, y `code_name` tiene constraint `UNIQUE`.
- **AC-3**: Given la migration `007` aplicada, When se inspecciona
  `tracking_events`, Then existen las columnas `event_id uuid` y
  `event_type_id uuid` con FK a `event_types(id)`.
- **AC-4**: Given las migrations `006` y `007`, When se ejecuta su rollback
  (`006.down`, `007.down`), Then `event_types` se elimina y `tracking_events`
  queda sin las columnas `event_id`/`event_type_id`, sin error.
- **AC-5**: Given el modulo `event-types.ts`, When se importa
  `EVENT_TYPES.PAGE_LOAD`, Then su valor es un string UUID identico al UUID
  del seed de la migration `006`.
- **AC-6**: Given el test de paridad, When el seed SQL y `EVENT_TYPES`
  divergen en cualquier UUID, Then el test falla.
- **AC-7**: Given `packages/content/src/index.ts`, When se importa
  `EVENT_TYPES` desde `@portfolio/content`, Then el simbolo esta exportado y
  tipado.

## 4. Diagrama de Flujo

N/A — el cambio no altera flujos de control. Es schema + constantes.

## 5. Diagrama ER

```text
event_types (NUEVO)                tracking_events (modificado)
┌──────────────────────────┐       ┌──────────────────────────────┐
│ id          uuid PK      │──┐    │ session_id     text          │
│ code_name   text UNIQUE  │  │    │ page_id        uuid          │
│ description text         │  │    │ event_id       uuid    (*)   │
│ created_at  datetime     │  └──< │ event_type_id  uuid FK (*)   │
└──────────────────────────┘       │ ... (resto sin cambios)      │
                                   └──────────────────────────────┘

(*) columnas nuevas. FK event_type_id -> event_types(id)
```

`event_id` no es FK: es el UUID del evento generado por el cliente, sirve para
idempotencia. `event_type_id` SI es FK al catalogo.

## 6. Tests Requeridos

### 6.B. Unit Tests

**Frontend (Vitest, `packages/content/tests/unit/lib/`):**

- `event-types.test.ts`:
  - `EVENT_TYPES.PAGE_LOAD` es un UUID string valido `[AC-5]`
  - Paridad: parsear `serverless/migrations/006_event_types.sql`, extraer los
    pares `(code_name, uuid)` del `INSERT`, y verificar que cada constante de
    `EVENT_TYPES` matchea `[AC-6]`
  - `EVENT_TYPES` exportado desde el barrel `@portfolio/content` `[AC-7]`

**Backend (verificacion de migrations):**

- Las migrations se prueban en un branch Neon (no son tests unitarios):
  `up` + `down` + `up` y consultas de schema `[AC-1..AC-4]`.

### 6.C. Typecheck

- `pnpm --filter @portfolio/content run typecheck`.

## 7. Archivos Afectados

### Crear

- `serverless/migrations/006_event_types.sql` — `CREATE TABLE event_types`
  + `INSERT` del seed `page_load` con UUID literal.
  - Por que: tabla catalogo, fuente de verdad de los tipos de evento.
  - Verificar: branch Neon, `migrate up`, `[AC-1]` y `[AC-2]`.
- `serverless/migrations/006_event_types.down.sql` — `DROP TABLE event_types`.
  - Verificar: `migrate down` sin error `[AC-4]`.
- `serverless/migrations/007_tracking_event_columns.sql` —
  `ALTER TABLE tracking_events ADD COLUMN event_id uuid`,
  `ADD COLUMN event_type_id uuid`, `ADD CONSTRAINT ... FOREIGN KEY
  (event_type_id) REFERENCES event_types(id)`, `CREATE INDEX` por
  `event_type_id`.
  - Por que: enlazar cada evento de tracking con su tipo en el catalogo.
  - Verificar: branch Neon, `[AC-3]`.
- `serverless/migrations/007_tracking_event_columns.down.sql` — `DROP` de las
  dos columnas y el constraint.
  - Verificar: `migrate down` `[AC-4]`.
- `packages/content/src/lib/event-types.ts` — objeto `EVENT_TYPES`
  (`as const`) + tipo `EventTypeCode` derivado. UUID del seed `page_load`.
  - Por que: dar al cliente los uuid del catalogo sin consultar la DB.
  - Verificar: `pnpm --filter @portfolio/content run typecheck`.
- `packages/content/tests/unit/lib/event-types.test.ts` — test de paridad
  SQL <-> TS + validacion de formato UUID.
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`.

### Modificar

- `packages/content/src/index.ts` — agregar
  `export { EVENT_TYPES, type EventTypeCode } from './lib/event-types'`.
  - Por que: que las apps y `packages/ui` importen desde `@portfolio/content`.
  - Verificar: `pnpm --filter @portfolio/content run typecheck`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `006_*.sql` + `007_*.sql` (+ down) | AC-1,2,3,4 | — | T2 |
| T2 | `event-types.ts` + `index.ts` + test | AC-5,6,7 | — | T1 (el UUID se acuerda antes) |

El UUID literal de `page_load` se fija al inicio (lo decide T1 o se acuerda en
el spec) para que T1 y T2 usen el mismo valor.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] UUID literal de `page_load` decidido y anotado
- [ ] Branch Neon de prueba creado (`db-branch create`)
- [ ] Test de paridad escrito y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-7 cubiertos por tests/verificaciones que pasan
- [ ] Migrations `006`/`007` probadas `up` + `down` + `up` en branch Neon
- [ ] `pnpm --filter @portfolio/content run typecheck` sin errores
- [ ] `pnpm --filter @portfolio/content exec vitest run` verde, coverage >= 80%
- [ ] `pnpm exec biome check .` sin errores
- [ ] Branch Neon de prueba eliminado tras validar

> Anterior: [SPEC-100](SPEC-100-ses-funcional.md) | Siguiente: [SPEC-102](SPEC-102-trackingpixel-page-load.md)
