# 10 — Paralelizacion con git worktrees

[< 09-commits](09-commits.md) | [Siguiente: 11-verificacion-e2e >](11-verificacion-e2e.md)

> Como ejecutar las fases paralelizables (P-1..P-7) en git worktrees
> independientes para que multiples agentes/devs avancen en paralelo
> sin pisarse. Reglas, base secuencial obligatoria, y fases NO
> paralelizables.

## Punto de partida (la base secuencial)

NO se lanza ningun worktree hasta tener mergeados los commits 1-7 en
`feature/analytics-dashboard-api`. Esos commits dejan listos:

- Carpeta del plan
- Indices Neon (si aplica)
- Scaffold completo del Lambda
- `OPERATIONS` con TODAS las entradas (controllers aun vacios)
- Handler + utils + `_common.py` + rate_limit_guard
- Test infrastructure (conftests + helpers)
- Command `seed-rate-limit-rule` en Lambda `db`

Con esa base, cualquier worktree puede importar:

- `core.settings.operations` -> sus entradas ya estan listas
- `core.models._common` -> DateRange + Pagination estables
- `core.handler` -> stub funcional, no se modifica desde worktrees
- `shared.*` -> congelado por la base

## Fases worktree-safe

Las **7 fases paralelizables** (P-1..P-7) tocan archivos DISJUNTOS por
operation/dominio. La matriz de file exclusivity esta en
[08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md).

| Worktree | Branch | Operation(s) | Archivos disjuntos | Commit final |
|----------|--------|--------------|---------------------|--------------|
| `wt-p1-analytics` | `feature/analytics-op-analytics` | `analytics` (7 actions) | `core/models/analytics.py`, `core/services/analytics_service.py`, `core/controllers/analytics/**`, `tests/unit/{models,services,controllers}/analytics/**`, `events/{overview,timeseries,top_pages,top_referrers,top_niches,active_now,retention}.json` | Commit 8 |
| `wt-p2-events` | `feature/analytics-op-events` | `events` (3 actions) | `core/models/events.py`, `core/services/events_service.py`, `core/controllers/events/**`, tests | Commit 9 |
| `wt-p3-sessions` | `feature/analytics-op-sessions` | `sessions` (2 actions) | `core/models/sessions.py`, `core/services/sessions_service.py`, `core/controllers/sessions/**`, tests | Commit 10 |
| `wt-p4-visits` | `feature/analytics-op-visits` | `visits` (2 actions) | `core/models/visits.py`, `core/services/visits_service.py`, `core/controllers/visits/**`, tests | Commit 11 |
| `wt-p5-geo-devices` | `feature/analytics-op-geo-devices` | `geo` + `devices` (2 actions total) | `core/models/{geo,devices}.py`, `core/services/{geo,devices}_service.py`, `core/controllers/{geo,devices}/**`, tests | Commit 12 |
| `wt-p6-funnel` | `feature/analytics-op-funnel` | `funnel` (1 action) | `core/models/funnel.py`, `core/services/funnel_service.py`, `core/controllers/funnel/**`, tests | Commit 13 |
| `wt-p7-contacts` | `feature/analytics-op-contacts` | `contacts` (2 actions) | `core/models/contacts.py`, `core/services/contacts_service.py`, `core/controllers/contacts/**`, tests | Commit 14 |

## Como lanzar cada worktree

Desde el repo raiz (asumiendo que `feature/analytics-dashboard-api` ya
tiene commits 1-7):

```bash
# Worktree raiz (ya estas ahi):
cd /home/bypabloc/projects/bypabloc/portfolio
git checkout feature/analytics-dashboard-api

# Lanzar worktree P-1 (analytics op)
git worktree add ../portfolio-wt-p1-analytics \
  -b feature/analytics-op-analytics

# Lanzar worktree P-2 (events op) en paralelo
git worktree add ../portfolio-wt-p2-events \
  -b feature/analytics-op-events

# ... idem P-3 a P-7
```

Cada worktree es una **copia independiente del working tree** del repo,
con su propio `.git` apuntando al mismo objeto-store. Cambios en uno NO
afectan a los otros HASTA que se mergea.

Al terminar el trabajo en un worktree:

```bash
cd ../portfolio-wt-p1-analytics
# ... implementar, testear ...
python devtools/run.py serverless tests --type=unit --lambda=analytics
# tests verdes -> commit (segun seccion 09)
git add core/ tests/ events/
git commit -m "feat(analytics): operation analytics con 7 actions y queries SQL"
git push -u origin feature/analytics-op-analytics

# Volver al worktree principal y mergear
cd /home/bypabloc/projects/bypabloc/portfolio
git checkout feature/analytics-dashboard-api
git merge --no-ff feature/analytics-op-analytics

# Cleanup del worktree
git worktree remove ../portfolio-wt-p1-analytics
git branch -d feature/analytics-op-analytics
```

## Lo que NO se paraleliza

Estas tareas son secuenciales por dependencia o por riesgo:

| # | Tarea | Razon de no-paralelizar |
|---|-------|------------------------|
| Commits 1-7 (base) | Plan + indices + scaffold + settings + handler + test infra + db seeder | Establecen contratos que todas las fases consumen. Paralelizar generaria conflictos en `OPERATIONS`, `_common`, `handler`. |
| Commit 15 (integration tests) | Tests E2E contra dev DB | Necesita TODAS las operations mergeadas + Lambda deployado. Tocar `tests/integration/` desde un worktree paralelo genera conflictos en `conftest.py`. |
| Commit 16 (SnapStart) | `runtime_hooks.py` | Es 1 archivo + deploy + observacion CloudWatch. Tarea atomica, no se beneficia de paralelismo. |
| Commit 17 (cleanup) | Eliminar spec efimera + actualizar knowledge tree + bateria E2E | Ultima fase, secuencial obligatorio. |
| Seed de rate-limit rule en DDB | `serverless run --lambda=db --event=seed_rate_limit_analytics.json` | Comando manual + idempotente. Se corre 3 veces (dev/stage/prod) cuando cada env esta listo. NO se paraleliza con CI. |
| Promocion `dev -> stage -> main` | PRs encadenados | Politica del repo, ver `git-workflow.md`. |

## Reglas de oro para worktrees

- **NUNCA** desde un worktree paralelo editar archivos de la base
  (`OPERATIONS`, `handler.py`, `_common.py`, `rate_limit_guard.py`,
  `config.py`, `shared/**`).
- **SIEMPRE** correr `serverless lint-deps --lambda=analytics` antes del
  commit (cada worktree tiene la misma copia de `shared/`).
- **NUNCA** intentar arreglar un bug detectado en la base desde un
  worktree paralelo — abrir un commit dedicado en el worktree raiz,
  rebasar los demas worktrees sobre el commit nuevo.
- **SIEMPRE** los worktrees comparten `.git/objects` — los `git
  fetch`/`push` son seguros, NO se crean blobs duplicados.
- **NUNCA** hacer `git worktree remove` con cambios sin commitear (la
  data se pierde silenciosamente).
- **SIEMPRE** correr `git worktree list` antes de empezar a editar para
  saber donde estoy y que branches estan vivos.

## Estrategia de merge

Cuando los 7 worktrees terminan:

```bash
cd /home/bypabloc/projects/bypabloc/portfolio
git checkout feature/analytics-dashboard-api

# Mergear en orden alfabetico (no importa el orden por file exclusivity,
# pero consistencia ayuda al review):
for branch in \
  feature/analytics-op-analytics \
  feature/analytics-op-contacts \
  feature/analytics-op-events \
  feature/analytics-op-funnel \
  feature/analytics-op-geo-devices \
  feature/analytics-op-sessions \
  feature/analytics-op-visits ; do
    git merge --no-ff "$branch" -m "chore(analytics): merge $branch"
done

# Verificar nada se rompio
python devtools/run.py serverless lint-deps --lambda=analytics
python devtools/run.py serverless tests --type=unit --lambda=analytics

# Cleanup worktrees
for wt in ../portfolio-wt-p*; do git worktree remove "$wt"; done
for branch in feature/analytics-op-*; do git branch -d "$branch"; done
```

## Conflictos esperados (cero)

Por la matriz de file exclusivity, los merges deberian aplicarse
**linealmente sin conflictos**. Los unicos riesgos:

1. **`events/`** — si en la base no creamos los 19 JSON vacios y cada
   worktree los suma, no hay conflicto (archivos disjuntos). Si dos
   worktrees crearan el mismo `events/X.json` -> conflicto. Por eso la
   tabla de file exclusivity asigna los JSON por dominio.
2. **`__init__.py`** vacios de `controllers/<dominio>/` — un worktree
   por dominio, sin colision.
3. **Tests fixtures compartidos** — `tests/unit/_helpers.py` lo
   commiteamos en la base (commit 6). Si una fase necesita un helper
   nuevo, lo agrega en su propio archivo `tests/unit/<dominio>/_helpers.py`
   para no tocar el compartido.

## Si decides NO paralelizar

Esta seccion describe el camino paralelizable. **Si lo haces secuencial**
(1 dev, sin worktrees), simplemente corres los commits 8-14 uno tras
otro en `feature/analytics-dashboard-api` directamente. Misma cantidad
de codigo, mismo PR final. El plan funciona en ambas modalidades.

Tiempo estimado:

- Secuencial (1 dev): ~5-7 dias de trabajo activo.
- Paralelizado (3-7 worktrees con devs/agentes distintos): ~2-3 dias.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Lanzar worktrees ANTES de commitear la base | Cada worktree no ve `OPERATIONS`, falla en runtime | Esperar commit 7 mergeado |
| Editar `OPERATIONS` desde un worktree para "agregar mi action" | Las entradas ya estan en commit 4 | Si necesitas una action nueva, va en un commit aparte en feature/X |
| Worktrees en branches sin sufijo `op-<X>` | Confusion en `git worktree list` | Convencion: `feature/analytics-op-<dominio>` |
| Olvidar `git worktree remove` despues del merge | Worktrees viejos quedan vivos, ocupan disco | Cleanup post-merge |
| Hacer `git stash` y cambiar worktree | El stash es global; podes desestabilizar otro | Cada worktree resuelve sus cambios sin stash |
| Confiar en CI para detectar conflictos | Tarde y caro | Validar file exclusivity en este doc ANTES de lanzar |

[< 09-commits](09-commits.md) | [Siguiente: 11-verificacion-e2e >](11-verificacion-e2e.md)
