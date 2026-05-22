# Plan: Servicio serverless `cv` + handler HTTP generico

> Crea el Lambda `serverless/lambda/services/cv/` (lectura del CV desde Neon
> via API Gateway) y refactoriza el `lambda_kit` de `shared` con un handler
> HTTP generico que resuelve `operation`/`action` del request (query params
> en GET, body en POST) en vez de hardcodearlos por Lambda.

## Indice

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, solucion, criterios de aceptacion (secciones 1-3) |
| [02-fase-http-kit.md](02-fase-http-kit.md) | Fase A — handler HTTP generico en `shared.lambda_kit` |
| [03-fase-migracion-handlers.md](03-fase-migracion-handlers.md) | Fase B — migrar `contact_form` + `tracking_pixel` al kit |
| [04-fase-servicio-cv.md](04-fase-servicio-cv.md) | Fase C — Lambda `cv` (modelos, repository, controllers) |
| [05-fase-consumo-apps.md](05-fase-consumo-apps.md) | Fase D — apps Astro consumen el API en prebuild |
| [06-archivos-afectados.md](06-archivos-afectados.md) | Secciones 7-8 — archivos + descomposicion |
| [07-commits.md](07-commits.md) | Seccion 9 — listado de commits |
| [08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md) | Seccion 10 — git worktrees |
| [09-verificacion-e2e.md](09-verificacion-e2e.md) | Seccion 11 — verificacion E2E iterativa |

## Escala

**Large** (11+ archivos): refactor de `shared.lambda_kit` + nuevo Lambda `cv`
con ~6 actions + migracion del consumo de las 6 apps Astro. Template completo,
descomposicion detallada.

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| Precondicion | DB Neon poblada con datos del CV (seed) | PENDIENTE — verificar antes de empezar |
| A | Handler HTTP generico en `shared.lambda_kit` | pending |
| B | Migrar `contact_form` + `tracking_pixel` al handler generico | pending |
| C | Lambda `cv` (lectura del CV) | pending |
| D | Apps Astro consumen el API en prebuild | pending |
| E | Verificacion E2E iterativa | pending |

## Decisiones (no reabribles)

1. **API por query param, NO por path param.** Un solo endpoint `GET /cv`.
   La entidad va como `?entity=experiences`. devtools hoy solo cablea UN
   segmento de path bajo la raiz (`_wire_http_trigger` en `provisioner.py`):
   evitar `{proxy+}` mantiene el plan sin tocar devtools.
2. **Contrato HTTP uniforme para TODOS los Lambdas HTTP.** `operation` y
   `action` se reciben del cliente: en GET como query params, en POST en el
   body JSON. El resto de argumentos viajan por el mismo canal y los valida
   el modelo Pydantic del controller. Lo implementa un handler generico en
   `shared.lambda_kit` — los handlers de cada Lambda dejan de hardcodear
   `operation`/`action`.
3. **La DB Neon pasa a ser fuente de verdad del CV.** Las apps Astro haran
   `fetch` del API en el `prebuild` en vez de leer `packages/content/src/data`.
   Los YAML quedan deprecados (no se borran en este plan — la limpieza es
   trabajo posterior, ver TODO de la fase D).
4. **El seed esta fuera de scope.** Lo ejecuta otra sesion. Este plan
   VERIFICA que la DB este poblada como precondicion (ver abajo) y NO inventa
   datos.
5. **`cv` es read-only.** Solo `GET`. Sin escritura, sin rate-limit estricto,
   sin Turnstile. Cache via `@cached` (DynamoDB) por el bajo cambio del CV.

## Precondicion bloqueante — verificar ANTES de empezar

El Lambda `cv` lee datos del CV de Neon. Si la DB no esta poblada, el API
devuelve listas vacias y la fase D no se puede verificar. Antes del primer
commit del plan, ejecutar:

```bash
# Tablas + row counts de la DB dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/tables.json --aws-profile=tfs-dev
```

Criterio: las tablas del CV (`profile`, `experiences`, `projects`,
`translations`, `niches`, ...) deben tener `rows > 0`. Si estan vacias, el
seed (otra sesion) aun no corrio — NO empezar la fase C/D hasta que el seed
este aplicado en `dev`. Las fases A y B no dependen del seed y SI pueden
arrancar.

## Reglas criticas

- Rama de trabajo: la sesion ya esta en `feature/cv-data-consistency`. Si al
  ejecutar el plan esa rama ya esta mergeada, crear `feature/cv-data-service`
  desde `dev`. NUNCA trabajar sobre `dev`/`stage`/`main`.
- El refactor del handler NO debe cambiar el comportamiento observable de
  `contact_form` ni `tracking_pixel` (mismos HTTP status, mismo CORS, mismas
  metricas). La fase B es refactor puro.
- `cv` sigue el estandar `lambda-controller` (ver `.claude/rules/lambda-controller.md`):
  `handler.py` dentro de `core/`, controllers descubiertos por convencion,
  logica en `services/`, `manifest.yaml` como fuente de verdad.
- `cv` NO importa `sqlalchemy` en su `core/` — consume `shared.db.repository`.
  Las queries ORM nuevas viven en `shared/db/repository.py` (o un modulo
  hermano `shared/db/cv_repository.py`).
- Verificacion incremental por commit. `git push` + PR SOLO con la bateria de
  la seccion 11 completa en verde.

## Matriz de verificacion

| Fase | Verificacion |
|------|--------------|
| A | `serverless tests --type=unit --shared` verde; tests nuevos del handler HTTP |
| B | `serverless tests --type=unit --lambda=contact_form` y `--lambda=tracking_pixel` verdes; integration E2E sin regresion |
| C | `serverless tests --type=unit --lambda=cv` verde, coverage >= 80%; `serverless run --stage=local --lambda=cv` devuelve el CV |
| D | `pnpm run build` de las 6 apps verde consumiendo el API |
| E | Bateria completa: lint + typecheck + unit + build + E2E Playwright |

## Navegacion

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
