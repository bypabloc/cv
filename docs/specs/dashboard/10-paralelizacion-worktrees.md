# 10 — Paralelizacion con git worktrees

[< 09-commits](09-commits.md) | [Siguiente: 11-verificacion-e2e >](11-verificacion-e2e.md)

## Base secuencial obligatoria

Antes de paralelizar, completar y commitear estas tareas (ver
seccion 08):

```text
A.1 (plan) -> A.2 (scaffold) -> A.3 (theme) -> A.4 (shadcn) -> A.5 (custom UI) -> A.6 (lib) -> A.7 (providers) -> A.8 (MSW)
              ↓
              B.1 (auth store/lib/api)
              ↓
              B.2 (auth hooks)
              ↓
              B.3 (auth components)
              ↓
              C.1 (dashboard-shell) + B.4 (auth pages) en paralelo
              ↓
              C.2 ((dashboard)/layout)
              ↓
              <<<< CHECKPOINT: aqui empieza la paralelizacion >>>>
```

Hasta C.2 todo SECUENCIAL (mismo working tree, commit a `feature/dashboard-frontend`).
Razon: tocan archivos centrales (package.json, configs, globals.css) o
dependencias duras (auth store que TODAS las features consumen).

## Fases paralelizables (worktree-safe)

Una vez completado el checkpoint, las fases D.1 - D.7 + E.1 + E.2 son
worktree-safe (file exclusivity garantizada).

| Worktree | Fase | Archivos exclusivos | Verifica antes de push |
|----------|------|---------------------|------------------------|
| `wt-analytics` | D.1 (analytics) | `dashboard/src/features/analytics/**` + `dashboard/src/app/(dashboard)/{page,analytics/page}.tsx` + tests mirror | `pnpm test:coverage tests/unit/features/analytics` |
| `wt-sessions-events` | D.2 + D.3 (sessions + events) | `dashboard/src/features/{sessions,events}/**` + `dashboard/src/app/(dashboard)/{sessions,events}/**` + tests | `pnpm test:coverage tests/unit/features/{sessions,events}` |
| `wt-visits-geo` | D.4 (visits + geo) | `dashboard/src/features/{visits,geo}/**` + `dashboard/src/app/(dashboard)/{visits,geo}/page.tsx` + tests | `pnpm test:coverage tests/unit/features/{visits,geo}` |
| `wt-devices-funnel` | D.5 (devices + funnel) | `dashboard/src/features/{devices,funnel}/**` + `dashboard/src/app/(dashboard)/{devices,funnel}/page.tsx` + tests | `pnpm test:coverage tests/unit/features/{devices,funnel}` |
| `wt-contacts-settings` | D.6 + D.7 (contacts + settings) | `dashboard/src/features/{contacts,settings}/**` + `dashboard/src/app/(dashboard)/{contacts,settings}/**` + tests | `pnpm test:coverage tests/unit/features/{contacts,settings}` |
| `wt-devtools` | E.1 + E.2 | `devtools/cloudflare_setup/config.py` + `devtools/sync_secrets/catalog.py` + `docker/env/client/.example` | `python devtools/run.py {cloudflare_setup,sync_secrets} ... --dry-run` |

Total: **6 worktrees** (dentro del limite 5-7 recomendado por
`.claude/rules/plan-format.md` capitulo 1). Si tenes 8GB RAM o menos,
limitar a 3-4 concurrentes. Cada worktree consolida features
cercanas para mantener el conteo bajo el limite (D.2 + D.3 comparten
patrones de Table/Drawer; D.6 + D.7 son ambas settings/admin).

## Lo que NO se paraleliza

- A.* (base secuencial) — tocan workspace root.
- B.1, B.2, B.3, B.4 (auth) — encadenadas.
- C.1, C.2 (shell) — C.2 depende de B.3.
- E.3 (workflows) — depende de E.1 + E.2 ya pushados.
- F.1 (E2E) — necesita TODAS las D.* + B.* + C.* mergeadas a la branch.
- F.2 (verificacion + cleanup) — la ultima.

## Como lanzar un worktree

```bash
# Asumiendo cwd = portfolio repo, branch actual = feature/dashboard-frontend
git status                              # working tree clean
git pull origin feature/dashboard-frontend  # sync

# Crear worktree con SU PROPIA branch (clave: el flag -b crea una branch
# nueva partiendo de feature/dashboard-frontend). NUNCA reutilizar
# feature/dashboard-frontend como branch del worktree secundario — esa
# branch ya esta checked out en el worktree principal y git lo rechaza
# con "fatal: 'feature/dashboard-frontend' is already checked out"
git worktree add -b feature/dashboard-wt-analytics \
  ../portfolio-wt-analytics feature/dashboard-frontend
cd ../portfolio-wt-analytics

# Setup en el worktree (cada worktree tiene su node_modules; pnpm store
# global ya reduce el duplicado via hardlinks)
pnpm install

# Trabajar D.1 (analytics):
# ... crear archivos, commits, tests ...

# Antes de commit/push: verify del scope
pnpm --filter @portfolio/dashboard test:coverage tests/unit/features/analytics
pnpm --filter @portfolio/dashboard typecheck
pnpm --filter @portfolio/dashboard lint

# Commit en la branch del worktree
git add dashboard/src/features/analytics dashboard/src/app/\(dashboard\)/page.tsx dashboard/src/app/\(dashboard\)/analytics dashboard/tests/unit/features/analytics
git commit -m "feat(dashboard,analytics): 7 hooks + 8 componentes ..."

# Push de la branch del worktree
git push -u origin feature/dashboard-wt-analytics

# Integrar a feature/dashboard-frontend desde el worktree principal:
cd ../portfolio
git checkout feature/dashboard-frontend
git merge --no-ff feature/dashboard-wt-analytics  # merge commit, sin rebase
git push origin feature/dashboard-frontend

# Limpiar al terminar
git worktree remove ../portfolio-wt-analytics
git branch -d feature/dashboard-wt-analytics       # ya mergeada
git push origin --delete feature/dashboard-wt-analytics
```

## Coordinacion entre worktrees

### Conflictos potenciales (deberian ser CERO si file exclusivity OK)

| Archivo | Worktrees que podrian tocar | Resolucion |
|---------|------------------------------|-----------|
| `dashboard/package.json` | Cualquiera que agregue dep | NO debe pasar: deps ya estan en A.2-A.4. Si una D.* necesita una dep nueva, primero rebase a feature/dashboard-frontend, agregar en el worktree principal, push, despues worktrees pull |
| `dashboard/src/components/ui/index.ts` | Cualquiera que cree un primitivo nuevo | NO debe pasar: D.* NO crea primitivos nuevos. Si si: pedir promote en PR comment, NO hacer en worktree de feature |
| `dashboard/tests/mocks/handlers/*.ts` | Cada feature actualiza su handler | Si los handlers de `analytics.ts` y `sessions.ts` estan en archivos separados (lo recomendado), no hay conflicto |
| `pnpm-lock.yaml` | Cualquiera que `pnpm install` | Si se agrega dep: cada worktree corre `pnpm install` despues de pull → el lockfile diff puede generar conflicto. Mitigar: NO agregar deps en worktrees |

### Estrategia de push y pull

1. Cada worktree pull de `feature/dashboard-frontend` al empezar el dia.
2. Cada worktree push despues de verificar su scope verde.
3. Antes de push: `git pull --rebase origin feature/dashboard-frontend`
   para integrar commits de otros worktrees.
4. Si hay conflicto: resolver localmente (deberia ser raro por file
   exclusivity), `git rebase --continue`, push.
5. NO usar `--force` (excepto si vos sos el unico en el worktree y
   sabes que es seguro).

### Comunicacion entre dev humano y agentes (si usas subagentes)

Si vos sos solo (no subagentes), los worktrees son herramienta de
organizacion mental. Trabajar 1 worktree a la vez es valido — los
worktrees solo aceleran si vos paralelizas mentalmente (raro).

Si lanzas subagentes (`/spec-workflow` o agents custom), cada uno
trabaja en SU worktree, output-en-disco en `docs/progress/<rol>_<scope>.md`
(ver `.claude/rules/harness-protocol.md`).

## Cuando NO usar worktrees

- Cambio chico (< 5 archivos). Overhead > beneficio.
- Trabajo serial mental (vos solo, sin paralelizar). El worktree no
  acelera nada.
- Si la maquina tiene < 8GB RAM. Cada worktree carga su node_modules.

## Cuando SI usar worktrees

- Trabajo paralelo con subagentes.
- Vos + un colaborador trabajando en features distintas.
- Necesitas tener 2 estados del codigo a la vez (ej. comparar
  features/dashboard-frontend con dev).

## Espacio en disco

Cada worktree = ~500MB-1GB (node_modules + .next). 5 worktrees = ~5GB.
Tener en cuenta si tu disco es chico.

Tip: usar pnpm store global (ya configurado en el repo) reduce el
duplicado. `pnpm install` en cada worktree usa hardlinks al store.

## Cleanup al final

```bash
# Lista los worktrees activos
git worktree list

# Limpiar cada uno
git worktree remove ../portfolio-wt-analytics
git worktree remove ../portfolio-wt-sessions
# ...

# Verificar que el principal sigue OK
cd ~/projects/bypabloc/portfolio
git status
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Crear worktree antes de A.* completo | Cada worktree falla al instalar | Esperar checkpoint post-C.2 |
| Editar el mismo archivo en 2 worktrees | Conflict al push | File exclusivity por feature folder |
| Agregar deps en una D.* worktree | Lockfile conflict | Primero pull al main, agregar, push, worktrees pull |
| Olvidar `pnpm install` en un worktree nuevo | Lint/typecheck rotos | `pnpm install` al cd al worktree |
| Push sin verify del scope | Romper la branch para otros worktrees | Verify primero |
| Tener 10+ worktrees | OOM + cognitive overhead | Max 5-7 |
| `worktree remove` sin commit + push primero | Perdes trabajo | Commit + push siempre antes |

[< 09-commits](09-commits.md) | [Siguiente: 11-verificacion-e2e >](11-verificacion-e2e.md)
