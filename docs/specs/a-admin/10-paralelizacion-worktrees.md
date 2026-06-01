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
              C.1 (admin-shell) en paralelo con B.1-B.3
              ↓
              C.2 ((admin)/layout)
              ↓
              <<<< CHECKPOINT: aqui empieza la paralelizacion >>>>
```

Hasta C.2 todo SECUENCIAL (mismo working tree, commit a `feature/admin-frontend`).
Razon: tocan archivos centrales (package.json, configs, globals.css) o
dependencias duras (auth store que TODAS las features consumen, `AuthGuard`
y el barrel `features/auth/index.ts` que consumen el layout y las features
de gestion).

> El plan a-admin es SOLO el frontend del admin: scaffold + auth + app shell
> + features de GESTION (settings, sessions-mgmt, users-admin, placeholder
> CV). Las pantallas de METRICAS (analytics, sessions de tracking, events,
> visits, geo, devices, funnel, contacts) NO viven aqui: las implementa el
> plan `b-analytics-api`, montadas dentro de este mismo app shell. Por eso
> los worktrees de abajo NO incluyen features de metricas.

## Fases paralelizables (worktree-safe)

Una vez completado el checkpoint (A.8 + B.3 + C.2), las fases B.4 + D.1 - D.4
+ E.1 - E.3 son worktree-safe (file exclusivity garantizada por carpeta de
feature). Consolidamos en 4 worktrees concurrentes para mantener el conteo
bajo el limite 5-7 de `.claude/rules/plan-format.md` capitulo 1.

| Worktree | Fases | Archivos exclusivos | Verifica antes de push |
|----------|-------|---------------------|------------------------|
| `wt-auth-pages` | B.4 (auth pages) | `admin/src/app/(auth)/{login,register,verify,callback,set-password}/page.tsx` + tests mirror | `pnpm --filter @portfolio/admin build && curl localhost:3000/login` |
| `wt-settings` | D.1 (settings) | `admin/src/features/settings/**` + `admin/src/app/(admin)/settings/{page,security/page}.tsx` + tests | `pnpm test:coverage tests/unit/features/settings` |
| `wt-sessions-mgmt-users` | D.2 + D.3 (sessions-mgmt + users-admin) | `admin/src/features/{sessions-mgmt,users-admin}/**` + `admin/src/app/(admin)/{settings/sessions,users}/page.tsx` + tests | `pnpm test:coverage tests/unit/features/{sessions-mgmt,users-admin}` |
| `wt-cv-devtools` | D.4 (placeholder CV) + E.1 + E.2 + E.3 | `admin/src/app/(admin)/cv/page.tsx` + `devtools/cloudflare_setup/config.py` + `devtools/sync_secrets/catalog.py` + `docker/env/client/.example` + `.github/workflows/{deploy-apps,ci}.yml` + `.claude/docs/subdomain-standard/02-naming-rules.md` + tests | `pnpm test:coverage tests/unit/app/cv` + `python devtools/run.py {cloudflare_setup,sync_secrets} ... --dry-run` |

Total: **4 worktrees** (dentro del limite 5-7 recomendado por
`.claude/rules/plan-format.md` capitulo 1). Si tenes 8GB RAM o menos,
limitar a 3 concurrentes. D.2 + D.3 comparten patrones de DataTable/Drawer
(gestion de cuentas) y van juntas; D.4 (page placeholder pequena) viaja con
las tareas de devtools (Python/YAML, no TS) para repartir carga.

> E.3 (workflows) depende de E.1 + E.2 ya commiteadas: dentro de
> `wt-cv-devtools` se hace en orden E.1 -> E.2 -> E.3 (todas en la misma
> worktree, sin colision externa). Si preferis paralelizar mas, separar E.3
> a su propia worktree DESPUES de pushar E.1 + E.2.

## Lo que NO se paraleliza

- A.* (base secuencial) — tocan workspace root.
- B.1, B.2, B.3 (auth) — encadenadas.
- C.1, C.2 (shell) — C.2 depende de B.3 (`AuthGuard`) + C.1 (Sidebar/Header).
- F.1 (E2E) — necesita TODAS las B.* + C.* + D.* mergeadas a la branch.
- F.2 (verificacion + cleanup) — la ultima.

## Como lanzar un worktree

```bash
# Asumiendo cwd = portfolio repo, branch actual = feature/admin-frontend
git status                              # working tree clean
git pull origin feature/admin-frontend  # sync

# Crear worktree con SU PROPIA branch (clave: el flag -b crea una branch
# nueva partiendo de feature/admin-frontend). NUNCA reutilizar
# feature/admin-frontend como branch del worktree secundario — esa
# branch ya esta checked out en el worktree principal y git lo rechaza
# con "fatal: 'feature/admin-frontend' is already checked out"
git worktree add -b feature/admin-wt-settings \
  ../portfolio-wt-settings feature/admin-frontend
cd ../portfolio-wt-settings

# Setup en el worktree (cada worktree tiene su node_modules; pnpm store
# global ya reduce el duplicado via hardlinks)
pnpm install

# Trabajar D.1 (settings):
# ... crear archivos, commits, tests ...

# Antes de commit/push: verify del scope
pnpm --filter @portfolio/admin test:coverage tests/unit/features/settings
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin lint

# Commit en la branch del worktree
git add admin/src/features/settings 'admin/src/app/(admin)/settings' admin/tests/unit/features/settings
git commit -m "feat(admin,settings): perfil + seguridad MFA/WebAuthn + recovery codes ..."

# Push de la branch del worktree
git push -u origin feature/admin-wt-settings

# Integrar a feature/admin-frontend desde el worktree principal:
cd ../portfolio
git checkout feature/admin-frontend
git merge --no-ff feature/admin-wt-settings  # merge commit, sin rebase
git push origin feature/admin-frontend

# Limpiar al terminar
git worktree remove ../portfolio-wt-settings
git branch -d feature/admin-wt-settings       # ya mergeada
git push origin --delete feature/admin-wt-settings
```

## Coordinacion entre worktrees

### Conflictos potenciales (deberian ser CERO si file exclusivity OK)

| Archivo | Worktrees que podrian tocar | Resolucion |
|---------|------------------------------|-----------|
| `admin/package.json` | Cualquiera que agregue dep | NO debe pasar: deps ya estan en A.2-A.4. Si una D.* necesita una dep nueva, primero rebase a feature/admin-frontend, agregar en el worktree principal, push, despues worktrees pull |
| `admin/src/components/ui/index.ts` | Cualquiera que cree un primitivo nuevo | NO debe pasar: D.* NO crea primitivos nuevos. Si si: pedir promote en PR comment, NO hacer en worktree de feature |
| `admin/tests/mocks/handlers/*.ts` | Cada feature actualiza su handler | Si los handlers de `settings.ts` y `users-admin.ts` estan en archivos separados (lo recomendado), no hay conflicto |
| `pnpm-lock.yaml` | Cualquiera que `pnpm install` | Si se agrega dep: cada worktree corre `pnpm install` despues de pull → el lockfile diff puede generar conflicto. Mitigar: NO agregar deps en worktrees |

### Estrategia de push y pull

1. Cada worktree pull de `feature/admin-frontend` al empezar el dia.
2. Cada worktree push despues de verificar su scope verde.
3. Antes de push: `git pull --rebase origin feature/admin-frontend`
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
(ver `.claude/rules/harness-protocol.md`). Cap de concurrencia: max 4
agentes simultaneos (ver `.claude/rules/orchestration.md`); con 4
worktrees, una sola ola cubre todo el bloque paralelo.

## Cuando NO usar worktrees

- Cambio chico (< 5 archivos). Overhead > beneficio.
- Trabajo serial mental (vos solo, sin paralelizar). El worktree no
  acelera nada.
- Si la maquina tiene < 8GB RAM. Cada worktree carga su node_modules.

## Cuando SI usar worktrees

- Trabajo paralelo con subagentes.
- Vos + un colaborador trabajando en features distintas.
- Necesitas tener 2 estados del codigo a la vez (ej. comparar
  features/admin-frontend con dev).

## Espacio en disco

Cada worktree = ~500MB-1GB (node_modules + .next). 4 worktrees = ~4GB.
Tener en cuenta si tu disco es chico.

Tip: usar pnpm store global (ya configurado en el repo) reduce el
duplicado. `pnpm install` en cada worktree usa hardlinks al store.

## Cleanup al final

```bash
# Lista los worktrees activos
git worktree list

# Limpiar cada uno
git worktree remove ../portfolio-wt-auth-pages
git worktree remove ../portfolio-wt-settings
git worktree remove ../portfolio-wt-sessions-mgmt-users
git worktree remove ../portfolio-wt-cv-devtools

# Verificar que el principal sigue OK
cd ~/projects/bypabloc/portfolio
git status
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Crear worktree antes de A.* completo | Cada worktree falla al instalar | Esperar checkpoint post-C.2 |
| Editar el mismo archivo en 2 worktrees | Conflict al push | File exclusivity por feature folder |
| Crear una worktree para una feature de metricas | El scope de metricas es del plan b-analytics-api | En a-admin solo el link en el sidebar (C.1) |
| Agregar deps en una D.* worktree | Lockfile conflict | Primero pull al main, agregar, push, worktrees pull |
| Olvidar `pnpm install` en un worktree nuevo | Lint/typecheck rotos | `pnpm install` al cd al worktree |
| Push sin verify del scope | Romper la branch para otros worktrees | Verify primero |
| Tener 10+ worktrees | OOM + cognitive overhead | Max 5-7 |
| `worktree remove` sin commit + push primero | Perdes trabajo | Commit + push siempre antes |

[< 09-commits](09-commits.md) | [Siguiente: 11-verificacion-e2e >](11-verificacion-e2e.md)
