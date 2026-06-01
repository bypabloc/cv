# Plan: reducir el tiempo de respuesta del backend serverless (cold + warm)

> Bajar el tiempo de respuesta de los Lambdas del portfolio atacando las
> dos palancas REALES medidas en CloudWatch: (1) la query de `cv`
> (9 secciones secuenciales a Neon, domina warm/cold/cache-MISS) y
> (2) el INIT crudo de ~14s que se paga cuando SnapStart NO restaura.
> NO se sube memoria ni se sobre-aprovisiona: el foco es estructura,
> queries e imports.

Estado: **propuesta / no implementado**. Rama de trabajo:
`feature/serverless-coldstart-refactor` (ya activa, no protegida).

## Hallazgo que reordena el problema (datos duros)

El número "cold cv.get = 13.9s" del reporte de `api_e2e` **NO es el cold
típico de produccion**. Medido en AWS (cuenta `637423614564`, `us-east-1`,
perfil `tfs-dev`, 2026-05-31):

| Hecho medido | Fuente | Implicacion |
|---|---|---|
| API GW `cv-dev` (`gvz6y2xcsa`) `/cv GET` integra `...:portfolio-cv-dev:live/invocations` | `get-integration` | El trafico real va a `:live` (SnapStart), NO a `$LATEST` |
| stage (`5k8os58pn5`) y prod (`332ivhahf2`) idem `:live` | `get-integration` | prod tambien sirve via SnapStart |
| `SnapStart.OptimizationStatus=On` en `cv:12` dev, cv-stage, cv-prod | `get-function-configuration --qualifier` | El snapshot del INIT ya esta activo |
| `RESTORE_REPORT Restore Duration: 963 ms` / `1262 ms` | CloudWatch | El "cold" real vvia SnapStart es **~1.2s**, no 14s |
| `INIT_REPORT Init Duration: 7s / 8s / 14s / 17s / 20s` (varianza salvaje) | CloudWatch | El INIT CRUDO se paga solo cuando SnapStart NO restaura (ventana post-deploy + escalado; AWS no garantiza restore) |
| `cv.get` warm `7.3s` con `Max Memory Used: 162 MB / 256 MB` | CloudWatch | La QUERY es el costo constante: no es OOM, no es memoria |
| `api_e2e` mide `elapsed` HTTP client-side, NO fuerza cold, NO distingue `:live` vs INIT crudo | `devtools/api_e2e/support.py:27-34`, `reporter.py` | El "cold 13.9s" es un INIT crudo capturado cuando SnapStart no restauro |

**Veredicto:** reestructurar imports/`shared` para "bajar el cold" tiene
**ROI casi nulo** — SnapStart ya absorbe el INIT en el path real. Las dos
palancas reales son:

1. **La query de `cv` (7.3s warm).** Se paga en warm, en cada cache MISS
   y dentro del cold. Es el mayor tiempo real y constante. **Palanca #1.**
2. **El INIT crudo de ~14s.** SnapStart lo absorbe casi siempre, pero la
   ventana donde no restaura (post-deploy, escalado brusco) cae a 14s.
   Bajarlo acota ese peor caso. **Palanca #2.**

El vendoring del zip se auditó y **está correcto** (uv `--python-platform
aarch64-manylinux2014 --only-binary=:all:`, poda boto3/botocore, cierre
transitivo por AST). No hay bug ahí; solo una mejora menor opcional
(strip de `.dist-info`).

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---|---|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto completo, solucion elegida, AC numerados |
| [02-fase-query-cv.md](02-fase-query-cv.md) | Palanca #1: unir las 9 secciones en 1 session + paralelizar/consolidar |
| [03-fase-init-imports.md](03-fase-init-imports.md) | Palanca #2: bajar el INIT crudo (Logger/Metrics lazy, warm_db, .pyc) |
| [04-fase-medicion-api-e2e.md](04-fase-medicion-api-e2e.md) | Hacer que `api_e2e` mida cold REAL (restore) vs INIT crudo, separado |
| [05-fase-vendoring-opcional.md](05-fase-vendoring-opcional.md) | Mejora menor opcional del zip (strip dist-info) |
| [06-commits.md](06-commits.md) | Seccion 9: listado de commits incrementales |
| [07-paralelizacion-worktrees.md](07-paralelizacion-worktrees.md) | Seccion 10: que se paraleliza con worktrees |
| [08-verificacion-e2e.md](08-verificacion-e2e.md) | Seccion 11: bateria final de verificacion (medir antes/despues) |
| [09-baseline-config-costo.md](09-baseline-config-costo.md) | Baseline medida (37/37 PASS), config uniforme 1024/60/snapstart aplicada a los 8, costo sin free tier vs $5/mes |

## Decisiones no reabribles

1. **NO subir memoria ni cambiar arch.** El usuario lo pidió explícito y
   los datos lo respaldan (Max Memory 162/256 MB: no hay presión).
2. **SnapStart se queda.** Ya funciona; el plan no lo toca salvo medir su
   restore. Es la razón por la que el cold real es ~1.2s.
3. **Palanca #1 = query de `cv`.** Es donde está el tiempo real.
4. **Alcance dev EXCLUSIVO.** dev tiene el código actual de la rama
   `feature/serverless-coldstart-refactor` (refactor SQS->invoke + lo de
   este plan). stage/prod corren código VIEJO (pre-refactor) sobre stacks
   CloudFormation SAM legacy: NO son comparables y este plan NO los toca.
   Toda medición, deploy y verificación es sobre dev. El `SnapStart Off`
   y los tiempos raros observados en stage/prod son de ese código viejo —
   esperado, se resuelven cuando la rama se promueva, fuera de scope aquí.

## Reglas críticas (de CLAUDE.md, siempre activas)

- Imports concretos desde `shared.<subpaquete>.<modulo>` (inits vacíos).
- `core/` de un Lambda NO importa paquetes externos directo (via `shared`).
- `serverless lint-deps` debe pasar (dedup D-3 + imports + no-submodule).
- Coverage >= 80% per-file en archivos modificados.
- `git push` + PR SOLO con la sección 11 en verde.
- Medir SIEMPRE antes de declarar listo (`api_e2e` antes/después).
- Conventional Commits en español, sin atribución de IA.

## Matriz de verificación (resumen)

| Que | Comando |
|---|---|
| Tests shared | `python devtools/run.py serverless tests --type=unit --shared` |
| Tests cv | `python devtools/run.py serverless tests --type=coverage --lambda=cv` |
| Lint deps | `python devtools/run.py serverless lint-deps --lambda=cv` |
| Deploy dev | `python devtools/run.py serverless deploy --lambda=cv --stage=dev --aws-profile=tfs-dev` |
| Medición real | `python devtools/run.py api_e2e --env=dev` (antes y después) |

## Objetivo cuantitativo

| Métrica | Hoy (medido) | Objetivo |
|---|---|---|
| `cv.get` warm | 7.3s | < 2.0s (consolidar/paralelizar query) |
| `cv.get` cache HIT | <0.1s | sin cambio (ya óptimo) |
| `cv.get` cold via SnapStart restore | ~1.2s | ~1.2s + query reducida |
| INIT crudo (sin restore) | 7-20s | < 6s (acotar peor caso) |
| Memoria | 256 MB | 256 MB (sin cambio) |
