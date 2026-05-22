# Plan: Servicio serverless `cv` + handler HTTP generico + seed migrado

> Migra el seeder del CV legacy (`db/cv/`) al Lambda `db`, crea el Lambda
> `services/cv/` (lectura del CV desde Neon via API Gateway) y refactoriza el
> `lambda_kit` de `shared` con un handler HTTP generico que resuelve
> `operation`/`action` del request (query params en GET, body en POST).

## Indice

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, solucion, criterios de aceptacion (secciones 1-3) |
| [00-fase-seed-migration.md](00-fase-seed-migration.md) | Fase 0 — migrar `db/cv/` al Lambda `db` + seeds en su arbol |
| [02-fase-http-kit.md](02-fase-http-kit.md) | Fase A — handler HTTP generico en `shared.lambda_kit` |
| [03-fase-migracion-handlers.md](03-fase-migracion-handlers.md) | Fase B — migrar `contact_form` + `tracking_pixel` al kit |
| [04-fase-servicio-cv.md](04-fase-servicio-cv.md) | Fase C — Lambda `cv` (modelos, repository, controllers) |
| [05-fase-consumo-apps.md](05-fase-consumo-apps.md) | Fase D — apps Astro consumen el API en prebuild |
| [06-archivos-afectados.md](06-archivos-afectados.md) | Secciones 7-8 — archivos + descomposicion |
| [07-commits.md](07-commits.md) | Seccion 9 — listado de commits |
| [08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md) | Seccion 10 — git worktrees |
| [09-verificacion-e2e.md](09-verificacion-e2e.md) | Seccion 11 — verificacion E2E iterativa |

## Escala

**Large** (11+ archivos): migracion del seeder legacy + refactor de
`shared.lambda_kit` + nuevo Lambda `cv` con ~6 actions + migracion del consumo
de las 6 apps Astro. Template completo, descomposicion detallada.

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Migrar `db/cv/` al Lambda `db`; YAML del CV como seeds en su arbol | pending |
| A | Handler HTTP generico en `shared.lambda_kit` | pending |
| B | Migrar `contact_form` + `tracking_pixel` al handler generico | pending |
| C | Lambda `cv` (lectura del CV) | pending |
| D | Apps Astro consumen el API en prebuild | pending |
| E | Verificacion E2E iterativa | pending |

## Decisiones (no reabribles)

1. **API por query param, NO por path param.** Un solo endpoint `GET /cv`.
   La entidad va como `?action=experiences`. devtools hoy solo cablea UN
   segmento de path bajo la raiz (`_wire_http_trigger` en `provisioner.py`):
   evitar `{proxy+}` mantiene el plan sin tocar devtools.
2. **Contrato HTTP uniforme para TODOS los Lambdas HTTP.** `operation` y
   `action` se reciben del cliente: en GET como query params, en POST en el
   body JSON. El resto de argumentos viajan por el mismo canal y los valida
   el modelo Pydantic del controller. Lo implementa un handler generico en
   `shared.lambda_kit`.
3. **La DB Neon pasa a ser fuente de verdad del CV.** Las apps Astro haran
   `fetch` del API en el `prebuild` en vez de leer `packages/content/src/data`.
4. **El Lambda `db` es el UNICO con acceso a los seeds y a los modelos.**
   El seeder legacy `db/cv/seed/seed_from_yaml.py` se migra a
   `services/db/core/`. Los 71 YAML del CV + `profile.ts` se copian a
   `services/db/seeds/` (dentro del arbol del Lambda) para que `db` sea
   autocontenido y se vendoricen al zip de deploy. El arbol legacy `db/cv/`
   se elimina al cerrar el plan.
5. **`cv` es read-only.** Solo `GET`. Sin escritura, sin rate-limit estricto,
   sin Turnstile. Cache via `@cached` (DynamoDB).

## Precondicion — verificar ANTES de empezar la Fase C

La Fase 0 puebla la DB. La Fase C (`cv`) la lee. Tras la Fase 0, verificar:

```bash
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/tables.json --aws-profile=tfs-dev
```

Las tablas del CV (`profile`, `experiences`, `projects`, ...) deben tener
`rows > 0`. Las fases 0, A y B no dependen de ese estado y pueden arrancar de
inmediato.

## Reglas criticas

- Rama de trabajo: `feature/cv-data-service` desde `dev`. NUNCA `dev`/`stage`/
  `main`.
- El refactor del handler NO cambia el comportamiento observable de
  `contact_form` ni `tracking_pixel`.
- `cv` y `db` siguen el estandar `lambda-controller`.
- `cv` NO importa `sqlalchemy` en su `core/` — consume `shared.db`.
- El Lambda `db` queda autocontenido: modelos via `shared.db`, seeds en su
  propio arbol, sin depender de `db/cv/`.
- Verificacion incremental por commit. `git push` + PR SOLO con la bateria de
  la seccion 11 completa en verde.

## Matriz de verificacion

| Fase | Verificacion |
|------|--------------|
| 0 | `serverless tests --type=unit --lambda=db` verde; `serverless run --stage=dev --lambda=db --event=events/seed.json` puebla la DB |
| A | `serverless tests --type=unit --shared` verde |
| B | `serverless tests --type=unit --lambda=contact_form` y `--lambda=tracking_pixel` verdes |
| C | `serverless tests --type=unit --lambda=cv` verde, coverage >= 80% |
| D | `pnpm run build` de las 6 apps verde consumiendo el API |
| E | Bateria completa: lint + typecheck + unit + build + E2E Playwright |

## Navegacion

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
