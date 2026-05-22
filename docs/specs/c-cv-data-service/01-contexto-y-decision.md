# 01 — Contexto, solucion y criterios de aceptacion

[<- README](README.md) | [Siguiente: Fase A ->](02-fase-http-kit.md)

## 1. Contexto / Problema

Las 6 apps Astro del portfolio (`generic`, `hub`, `fintech`, `architect`,
`leader`, `vibe`) consumen la data del CV desde `packages/content/src/data/*`
(YAML cargados con `vite-plugin-yaml` + Zod). El schema relacional de esa data
ya existe: 35 tablas SQLAlchemy en `serverless/lambda/shared/db/models/`,
gestionadas por un solo Alembic, persistidas en Neon PostgreSQL.

Hoy NO existe forma de leer ese CV desde la DB: el unico Lambda que toca el
schema del CV es `db` (migraciones) y `stream_processor` (escribe datos del
visitante). Falta el camino de lectura.

Ademas, los handlers HTTP del backend (`contact_form`, `tracking_pixel`)
**hardcodean** `operation` y `action` (`'contact'/'create'`,
`'tracking'/'track'`) y los sintetizan a mano dentro de cada `handler.py`. No
hay un contrato uniforme: cada Lambda HTTP nuevo reescribe el mismo parsing.

### Hallazgos de exploracion

- `shared.lambda_kit` ya tiene `run_controller` que valida el evento
  `{operation, action, data}`, resuelve el controller y ejecuta su ciclo.
  Lo que falta es el ADAPTADOR HTTP: extraer `operation`/`action`/`data` del
  evento crudo de API Gateway. Hoy ese adaptador esta duplicado y hardcodeado
  en cada `handler.py`.
- `devtools` (`provisioner.py:_wire_http_trigger`) cablea el `trigger.path`
  del manifiesto como UN solo `--path-part` bajo la raiz de la API. No
  soporta paths multi-segmento ni `{proxy+}`. Por eso el API de `cv` usa un
  solo path (`/cv`) y la entidad va por query param.
- El schema del CV son 36 tablas con un patron claro: entidades con `slug`
  UNIQUE, textos bilingues en la tabla polimorfica `translations`
  (`entity_type`, `entity_id`, `field`, `locale`), niches en uniones
  `<entidad>_niches`, priority por niche en `niche_priorities`.
- `shared.db.repository` ya concentra el acceso ORM (`list_tables`,
  `insert_contact`, ...). El Lambda `cv` agregara aqui sus queries de lectura
  — su `core/` NO importa `sqlalchemy`.

## 2. Solucion Propuesta

Cuatro fases:

**Fase A — handler HTTP generico en `shared.lambda_kit`.** Nuevo modulo
`shared/lambda_kit/http_dispatch.py` con:
- `extract_request(event)` — funcion pura que, dado un evento API Gateway REST
  proxy, devuelve `(operation, action, data)`:
  - **GET**: `operation` y `action` de `queryStringParameters`; el resto de
    query params forman `data`.
  - **POST/PUT**: `operation`, `action` y el resto de campos del body JSON.
- `http_handler(event, *, event_model, ...)` — envuelve el ciclo completo:
  `extract_request` -> sintetiza `{operation, action, data + _meta}` ->
  `run_controller` -> traduce `DispatchResult` a respuesta HTTP. Devuelve la
  respuesta de API Gateway. Recibe hooks opcionales para metricas y CORS.

El `_meta` (IP, country, user-agent, bypass-secret) lo inyecta `http_handler`
desde los headers/requestContext — sigue viajando dentro de `data` para que
el modelo Pydantic lo valide.

**Fase B — migrar `contact_form` + `tracking_pixel`.** Sus `handler.py` pasan
a delegar en `http_handler`. Dejan de hardcodear `operation`/`action`: ahora
el cliente los manda (el frontend del form/tracking se actualiza para enviar
`operation`/`action` en el body). Refactor sin cambio de comportamiento
observable salvo el contrato de entrada (documentado en AC-7).

**Fase C — Lambda `cv`.** Nuevo `serverless/lambda/services/cv/` siguiendo el
estandar `lambda-controller`. Una operation `cv` con actions:
- `get` — el CV completo (profile + stats + todas las colecciones), filtrado
  por niche y locale.
- `profile`, `experiences`, `projects`, `certificates`, `awards`, `education`,
  `languages`, `references`, `skills` — cada coleccion por separado.

El handler delega en `http_handler`; la entidad pedida se resuelve por el
query param `action` (`GET /cv?operation=cv&action=experiences`). Las queries
ORM viven en `shared/db/cv_repository.py`. Cada respuesta se cachea con
`@cached` (el CV cambia raramente).

**Fase D — apps Astro consumen el API.** El `prebuild` de cada app
(`scripts/build-public-assets.mjs`) hace `fetch` del API `cv` en lugar de
importar `@portfolio/content`. Se agrega un cliente TS compartido en
`packages/content` (`src/lib/cv-api-client.ts`) que pega al API y valida la
respuesta con los Zod schemas existentes — asi el shape no cambia para los
componentes Astro.

### Decisiones clave

- **Decision 1: contrato uniforme via `http_handler`** — un solo punto que
  resuelve `operation`/`action` para todos los Lambdas HTTP. Elimina la
  duplicacion y hace trivial agregar Lambdas HTTP nuevos.
- **Decision 2: query param, no path param** — evita tocar `devtools`
  (`_wire_http_trigger` solo soporta un segmento). `GET /cv?operation=cv&action=get`.
- **Decision 3: `cv_repository.py` en `shared/db/`** — el `core/` del Lambda
  `cv` no importa `sqlalchemy`; consume funciones de `shared.db`, igual que
  `db` y `stream_processor`.
- **Decision 4: el cliente TS valida con los Zod schemas existentes** — el
  shape que reciben los componentes Astro no cambia; solo cambia el ORIGEN
  (API en vez de YAML). Riesgo de migracion acotado.
- **Decision 5: cache `@cached`** — el CV es casi inmutable; cachear la
  respuesta del API en DynamoDB evita golpear Neon en cada build.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un evento API Gateway GET con
  `queryStringParameters={operation, action, ...}`, When `extract_request` lo
  procesa, Then devuelve `(operation, action, data)` con `data` conteniendo el
  resto de los query params.
- **AC-2**: Given un evento API Gateway POST con body JSON
  `{operation, action, ...campos}`, When `extract_request` lo procesa, Then
  devuelve `(operation, action, data)` con `data` conteniendo los campos
  restantes del body.
- **AC-3**: Given un request HTTP sin `operation` o sin `action`, When
  `http_handler` lo procesa, Then responde HTTP 400 con codigo
  `INVALID_REQUEST` sin invocar ningun controller.
- **AC-4**: Given `GET /cv?operation=cv&action=get&niche=fintech&locale=es`,
  When el Lambda `cv` lo atiende, Then responde HTTP 200 con el CV completo
  (profile, stats, experiences[], projects[], certificates[], awards[],
  education[], languages[], references[], skillCategories[]) filtrado por
  niche `fintech` y locale `es`.
- **AC-5**: Given `GET /cv?operation=cv&action=experiences&niche=fintech`,
  When el Lambda `cv` lo atiende, Then responde HTTP 200 con solo el array de
  experiencias del niche `fintech`.
- **AC-6**: Given un `action` que no existe (ej. `action=foobar`), When el
  Lambda `cv` lo atiende, Then responde HTTP 400 con codigo `INVALID_REQUEST`.
- **AC-7**: Given el frontend del form de contacto, When envia el POST a
  `/contact`, Then el body incluye `operation: 'contact'` y `action: 'create'`
  y el Lambda `contact_form` responde HTTP 201 igual que antes del refactor.
- **AC-8**: Given el `prebuild` de una app Astro, When corre con el API `cv`
  disponible, Then genera la misma data que generaba leyendo los YAML (mismo
  shape validado por los Zod schemas) y `pnpm run build` de la app pasa.
- **AC-9**: Given un niche sin entradas para una coleccion, When el Lambda
  `cv` la consulta, Then responde HTTP 200 con un array vacio para esa
  coleccion (NO error).
- **AC-10**: Given la DB Neon vacia (sin seed), When se consulta el API `cv`,
  Then responde HTTP 200 con colecciones vacias y el plan documenta esto como
  precondicion no cumplida (no es un bug del Lambda).

## 4. Diagrama de Flujo

### Antes

```text
cliente HTTP --> API Gateway --> handler.py de cada Lambda
                                   |
                                   +-- parsea body/query A MANO
                                   +-- hardcodea operation='contact'
                                   +-- hardcodea action='create'
                                   +-- sintetiza {operation, action, data}
                                   +-- run_controller(...)
```

### Despues

```text
cliente HTTP --> API Gateway --> handler.py (delgado)
                                   |
                                   +-- http_handler(event, event_model=...)
                                         |
                                         +-- extract_request(event)
                                         |     GET  -> query params
                                         |     POST -> body JSON
                                         +-- (operation, action, data)
                                         +-- inyecta data._meta (IP, ...)
                                         +-- run_controller({op, action, data})
                                         +-- DispatchResult -> respuesta HTTP
```

## 5. Diagrama ER

`N/A — no hay cambios en el schema de la DB`. El plan LEE las 36 tablas
existentes; no agrega ni modifica modelos ni migraciones. El seed que las
puebla es trabajo de otra sesion.

## 6. Tests Requeridos

### 6.A. TDD Flows (logica nueva en `shared/lambda_kit/` y `shared/db/`)

- `WHEN extract_request recibe GET con queryStringParameters {operation:cv,
  action:get, niche:fintech} THEN devuelve ('cv', 'get', {niche:'fintech'})
  [AC-1]`
- `WHEN extract_request recibe POST con body {operation:contact,
  action:create, name:X} THEN devuelve ('contact','create',{name:'X'}) [AC-2]`
- `WHEN extract_request recibe GET sin operation THEN levanta ValidationError
  code=INVALID_REQUEST [AC-3]`
- `WHEN cv_repository.get_full_cv(niche='fintech', locale='es') THEN devuelve
  un dict con todas las colecciones filtradas por niche [AC-4]`
- `WHEN cv_repository.list_experiences(niche='fintech') THEN devuelve solo las
  experiencias del niche [AC-5]`

### 6.B. Unit Tests (pytest)

- `shared`: `tests/unit/lambda_kit/test_http_dispatch_*.py` — un archivo por
  escenario de `extract_request` + `http_handler` (estandar de testing
  lambda-controller: un archivo = un escenario).
- `shared`: `tests/unit/db/test_cv_repository_*.py` — queries del CV con una
  DB de prueba (branch Neon o fixture).
- `cv`: `tests/unit/` — modelo Pydantic + service + controller + handler por
  cada action (estandar de testing).
- `contact_form` / `tracking_pixel`: ajustar los tests existentes al nuevo
  contrato (el handler ahora delega en `http_handler`).
- Coverage v8/pytest >= 80% per-file en archivos modificados.

### 6.C. Typecheck

- Python: `python -m compileall -q core` por Lambda + `serverless lint-deps`.
- TS (fase D): `pnpm exec tsc --noEmit` + `pnpm exec astro check` en cada app.

### 6.D. E2E Tests

- `cv`: `tests/integration/test_*_e2e.py` — `serverless tests
  --type=integration --lambda=cv` contra un branch Neon de prueba poblado.
- Playwright: la suite `tests/feature/` debe seguir verde tras la fase D (las
  apps renderizan el CV consumido del API). Ver fase E.

Continua en [02-fase-http-kit.md](02-fase-http-kit.md).
