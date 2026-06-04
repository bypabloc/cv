# Sesiones de Claude Code en paralelo (sin colisionar)

> Como trabajar VARIAS sesiones de Claude Code a la vez sobre el MISMO
> repo sin que se pisen: el modelo de las 3 capas de paralelismo (ventanas
> VS Code / worktrees / subagentes), el aislamiento de archivos via git
> worktrees, el aislamiento de recursos en este monorepo pnpm + Docker
> (node_modules, puertos, `.worktreeinclude`) y el aislamiento de cuota /
> rate-limit (que NO se puede aislar, se gestiona). Verificado contra el
> changelog y docs oficiales de Claude Code (abril-junio 2026).

## Activacion

Aplica SIEMPRE que se trabaje con:

- Abrir/coordinar MAS de una sesion de Claude Code a la vez en el mismo
  repo (varias ventanas/tabs de la extension VS Code, o `claude agents`).
- El flag `--worktree`/`-w`, las tools `EnterWorktree`/`ExitWorktree`, o
  los settings `worktree.baseRef` / `worktree.bgIsolation`.
- El archivo `.worktreeinclude` (copia de archivos gitignored a worktrees).
- Aislar node_modules, puertos de dev server, containers Docker o caches
  de build entre dos checkouts del mismo repo.
- El error "Server is temporarily limiting requests (not your usage
  limit)" al correr varias sesiones a la vez.

Complementa [orchestration.md](orchestration.md): esa rule gobierna los
SUBAGENTES y WORKFLOWS dentro de UNA sesion (caps de concurrencia,
modelos). ESTA rule gobierna las SESIONES en paralelo (ventanas + worktrees
+ aislamiento de recursos del monorepo). Las dos comparten el mismo techo
de cuota/rate-limit.

## Las 3 capas de paralelismo (modelo mental)

| Capa | Que es | Aislamiento que da | Cuando |
|------|--------|--------------------|--------|
| **(a) Ventanas/tabs VS Code** | Tu abres N sesiones independientes (`Open in New Tab` / `Open in New Window`) | **NINGUNO por defecto** — comparten working tree, node_modules, puertos, Docker | Tareas en paralelo que TU supervisas |
| **(b) Worktrees** (`--worktree` o `git worktree add`) | Checkout git separado por sesion (HEAD/index/branch propios) | **Archivos (git)**: editar en uno nunca toca el otro | Cada sesion en una feature distinta que mutaria los mismos archivos |
| **(c) Subagentes** (Agent/Workflow, `isolation: worktree`) | Fan-out DENTRO de una sesion | Opcional via worktree temporal | Lo gobierna [orchestration.md](orchestration.md) |

**Combinacion correcta para este repo**: capa (a) + capa (b) =
**UNA ventana VS Code por worktree**. Las ventanas dan sesiones
independientes; los worktrees evitan que se pisen los archivos. Multi-tab
SOLO NO aisla nada a nivel git.

## Reglas duras (SIEMPRE / NUNCA)

### Aislamiento de archivos (git)

- **SIEMPRE** dos sesiones que vayan a MUTAR archivos del mismo repo a la
  vez van en **worktrees separados**. NUNCA dos sesiones editando el mismo
  checkout en paralelo (corrompen el working tree, el index y los caches).
- **SIEMPRE** crear el worktree con `claude --worktree <nombre>` (lo pone
  en `.claude/worktrees/<nombre>/`, rama `worktree-<nombre>`) o con
  `git worktree add <ruta> -b <branch>` para control total de ruta/branch.
- **SIEMPRE** `.claude/worktrees/` esta gitignored (ya lo esta en este
  repo, `.gitignore` linea 7) para que los worktrees no aparezcan como
  untracked en el checkout principal.
- **NUNCA** crear ni borrar el branch base (`dev`/`stage`/`main`) como
  worktree: son ramas de entorno. Un worktree es SIEMPRE una rama de
  trabajo (`feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`).
- **NUNCA** confiar en multi-tab de VS Code para aislar archivos: las tabs
  comparten el mismo working tree. Solo los worktrees aislan a nivel git.

### Aislamiento de recursos (monorepo pnpm + Docker)

- **SIEMPRE** cada worktree corre su PROPIO `pnpm install`: es un checkout
  fresco SIN `node_modules` (hoisted al root del workspace). El **store
  global de pnpm se comparte** entre worktrees, asi que el install es
  rapido (solo crea los symlinks). NUNCA correr dos `pnpm install` sobre el
  MISMO checkout en paralelo (race en `node_modules/`).
- **SIEMPRE** que un worktree necesite levantar el stack Docker local,
  aislarlo: o un **env distinto por worktree** (local 9970 / dev 9971 /
  test 9972 — ya tienen puertos y `container_name` distintos), o
  `COMPOSE_PROJECT_NAME` distinto + puerto parametrizado. NUNCA dos
  `docker:up --env=local` a la vez (chocan en `portfolio-<servicio>-local`
  y en el puerto 9970).
- **SIEMPRE** declarar en `.worktreeinclude` los archivos gitignored que un
  worktree fresco necesita (env files, secrets locales): Claude los **copia**
  (no lee su contenido) a cada worktree nuevo. Esto es compatible con
  [env-files.md](env-files.md) (es una copia file-a-file, NO una lectura del
  `.env` al contexto). Ver "Setup del repo" abajo.
- **SIEMPRE** recordar que los caches de build (`.astro/`, `.vite/`,
  `dist/`, `coverage/`) viven DENTRO del worktree -> ya estan aislados, no
  colisionan entre worktrees.
- **NUNCA** asumir que Claude prepara el entorno del worktree: la doc
  oficial es explicita en que cada worktree requiere su propio
  `pnpm install` + setup. Claude crea el checkout, no el entorno.

### Aislamiento de cuota / rate-limit (NO se aisla — se gestiona)

- **SIEMPRE** asumir que la cuota es **de la cuenta**, compartida entre
  Claude web + TODAS las sesiones de Claude Code abiertas (rolling 5h + cap
  semanal). Abrir N ventanas NO multiplica la cuota: drena el MISMO pool
  mas rapido.
- **SIEMPRE** limitar a **2-3 sesiones ACTIVAS a la vez** (generando tokens
  simultaneamente). Mas que eso dispara el throttle per-minuto del servidor
  ("Server is temporarily limiting requests (not your usage limit)"), que es
  un limite de RAFAGA distinto del cap de cuota. Mismo principio que el cap
  de [orchestration.md](orchestration.md) (<=4 subagentes, 1 workflow).
- **SIEMPRE** recordar que el throttle se SUMA: si una sesion ya corre un
  workflow (hasta 4 subagentes), una segunda ventana activa empuja el total
  por encima del techo seguro. NO correr un workflow Y abrir varias ventanas
  activas a la vez.
- **NUNCA** abrir 5+ sesiones activas "para ir mas rapido": por encima del
  techo el 429 mata el trabajo (medido: 4 agentes + web -> 429 con 0 tokens
  utiles).

## Setup del repo (una sola vez)

`.claude/worktrees/` ya esta gitignored. Falta declarar que archivos
gitignored copiar a cada worktree nuevo. Crear `.worktreeinclude` en la
raiz (sintaxis `.gitignore`); solo copia lo que matchea Y es gitignored:

```text
# .worktreeinclude — archivos gitignored que un worktree fresco necesita.
# Claude los COPIA file-a-file (no lee su contenido al contexto).
docker/env/
.env
.env.local
```

> Ajustar los paths a lo que cada worktree necesite para arrancar (env
> files de las 3 categorias client/server/dev-cli viven en `docker/env/`).
> Los `.example` son tracked, no se copian (ni hace falta).

## Workflow operativo (paso a paso)

```bash
# 1. Crear el worktree + arrancar Claude ahi (una ventana por feature)
claude --worktree feature-a        # -> .claude/worktrees/feature-a, rama worktree-feature-a
#   o, para una rama de trabajo con nombre del proyecto:
git worktree add .claude/worktrees/feature-a -b feature/<nombre>
code .claude/worktrees/feature-a   # abrir VS Code en el worktree, abrir Claude ahi

# 2. Dentro del worktree: aislar recursos
pnpm install                       # node_modules propio (store compartido = rapido)
#   si necesita Docker, aislar el proyecto:
COMPOSE_PROJECT_NAME=portfolio-wt-a python devtools/run.py docker up --env=local
#   (o usar un env distinto por worktree: --env=dev en uno, --env=test en otro)

# 3. Trabajar la feature en su ventana/sesion dedicada.
#    Cada worktree tiene su HEAD/index/branch -> cero colision de archivos.
#    Cada sesion tiene su propio docs/progress/current.md (path relativo).

# 4. Mergear en ORDEN (base secuencial primero). Si dos worktrees tocan
#    archivos transversales, mergear uno, rebasar el otro sobre dev, y
#    recien ahi mergear. Ver plan-format.md seccion 10.

# 5. Limpiar el worktree al terminar (los de --worktree NO se barren solos)
git worktree remove .claude/worktrees/feature-a
git worktree prune                 # limpia referencias colgadas
```

### Settings de worktree relevantes (en `.claude/settings.json`)

| Setting | Valores | Que hace |
|---------|---------|----------|
| `worktree.baseRef` | `"fresh"` (default) / `"head"` | `fresh`: el worktree nace de `origin/<default>` (arbol limpio). `head`: nace de tu `HEAD` local (conserva commits sin pushear). Usar `"head"` si el worktree debe partir de trabajo en curso. |
| `worktree.bgIsolation` | (default isolation) / `"none"` | `"none"` deja a las background sessions editar el working copy directo sin `EnterWorktree`. Solo para repos donde los worktrees son impracticables. |

> Cambiar settings de `.claude/*` exige validacion con `claude -p` (ver
> [claude-config-testing.md](claude-config-testing.md)).

### Cambiar de worktree mid-session

Dentro de una sesion, Claude puede crear un worktree (`EnterWorktree`) o
saltar a otro existente bajo `.claude/worktrees/` pasando su `path` a
`EnterWorktree` (el worktree previo queda intacto en disco). `ExitWorktree`
vuelve al checkout principal.

### Gestion multi-sesion: `claude agents` (Agent View)

`claude agents` (Research Preview, disponible en VS Code, CLI, desktop,
web) abre una lista UNICA de todas las sesiones (running / blocked-on-you /
done): despachar, responder, parar, limpiar desde un solo lugar. Es la
forma de NO perder de vista las 2-3 sesiones en paralelo.

> "FleetView" NO existe como feature oficial — es confusion con el tercero
> *Agent Fleet*. La feature de Anthropic se llama **Agent View**.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Dos sesiones editando el MISMO checkout en paralelo | Corrompen working tree / index / caches de build | Un worktree por sesion (`--worktree`) |
| Confiar en multi-tab VS Code para aislar archivos | Las tabs comparten el working tree | Solo los worktrees aislan a nivel git |
| Dos `pnpm install` sobre el mismo `node_modules` | Race en el node_modules hoisted | `pnpm install` propio por worktree (store compartido) |
| Dos `docker:up --env=local` a la vez | Choque de `portfolio-<svc>-local` + puerto 9970 | Env distinto por worktree, o `COMPOSE_PROJECT_NAME` distinto |
| Worktree fresco sin sus `.env` | Es un checkout limpio sin archivos gitignored | `.worktreeinclude` (copia, no lectura) |
| Esperar que Claude prepare el entorno del worktree | Claude crea el checkout, no instala deps | `pnpm install` + setup manual en cada worktree |
| Abrir 5+ ventanas activas para ir mas rapido | La cuota es de cuenta + throttle de rafaga -> 429 | 2-3 sesiones activas a la vez; combinar capas, no multiplicarlas |
| Correr un workflow Y abrir varias ventanas activas | El throttle se suma -> pega el techo | Una cosa a la vez: o el workflow, o las ventanas |
| Dejar worktrees de `--worktree` sin borrar | NO se barren solos (solo los de subagentes/background) | `git worktree remove` + `prune` al terminar |
| Crear `dev`/`stage`/`main` como worktree | Son ramas de entorno protegidas | Worktree = rama de trabajo (`feature/`, `fix/`, ...) |
| Decir / buscar "FleetView" | No es feature oficial | Es **Agent View** (`claude agents`) |

## Referencias cruzadas

- [orchestration.md](orchestration.md) — subagentes/workflows DENTRO de una
  sesion: caps de concurrencia (<=4 agentes, 1 workflow), politica de
  modelos. Comparte el techo de cuota/rate-limit con esta rule.
- [plan-format.md](plan-format.md) — seccion 10 (paralelizacion con git
  worktrees) y seccion 8 (descomposicion): el ORDEN de merge entre
  worktrees y que tareas son worktree-safe.
- [git-workflow.md](git-workflow.md) — ramas de trabajo vs entorno, flujo
  `dev -> stage -> main`, merge en orden.
- [env-files.md](env-files.md) — NUNCA leer `.env` al contexto;
  `.worktreeinclude` COPIA file-a-file, no lee (compatible).
- [harness-protocol.md](harness-protocol.md) — `docs/progress/current.md`
  por sesion; cada worktree tiene el suyo (path relativo).
- Skill [`/orchestration`](../skills/orchestration/SKILL.md).
- Docs oficiales: code.claude.com/docs/en/{worktrees,vs-code,changelog}.
