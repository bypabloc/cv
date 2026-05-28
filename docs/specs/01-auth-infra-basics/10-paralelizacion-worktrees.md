# 10. Paralelizacion con git worktrees

> Plan Large con dependencias estrictas + 4 operaciones (register,
> login, verify, session) que son worktree-safe entre si tras T7+T8.

## Base secuencial (no se paraleliza)

```text
PR 1   T1 + T13                         <-- BASE 1: spec + docs/claude
PR 2   T2                               <-- BASE 2: shared.auth (todos importan de aqui)
PR 3   T3 + T4                          <-- BASE 3: schema Neon + repositories
PR 4   T5                               <-- BASE 4: resources AWS (DDB + SQS + SSM)
PR 6.1+6.2  T7 + T8 (scaffold+services) <-- BASE 5: handlers/services del lambda auth

       hasta aqui TODO secuencial
```

PR 1 -> PR 4 son secuenciales por dependencia logica: cada uno apoya
al siguiente. PR 5 (`auth_email_worker`) puede correr paralelo a PR 6
porque toca un Lambda distinto, pero por simplicidad de revision se
hacen secuenciales tambien.

## Fase paralela: worktrees lanzables tras PR 6 mergeado

Tras PR 6 mergeado en `dev`, el repo tiene `services/auth/` con
`handler.py` + 8 services + EventModel registrando 4 operations. Los
controllers no existen aun. Aqui se abre la ventana de paralelizacion:

| Worktree | Tarea | Archivos nuevos | Archivos modificados | Colision? |
|----------|-------|-----------------|----------------------|-----------|
| WT-A | T9 register | `controllers/register/*` + `models/register.py` + `tests/unit/controllers/test_register_*.py` + `events/register-*.json` | ninguno | no |
| WT-B | T10 login | `controllers/login/*` + `models/login.py` + `tests/unit/controllers/test_login_*.py` + `events/login-*.json` | ninguno | no |
| WT-C | T11 verify | `controllers/verify/*` + `models/verify.py` + `tests/unit/controllers/test_verify_*.py` + `events/verify-*.json` | ninguno | no |
| WT-D | T12 session | `controllers/session/*` + `models/session.py` + `tests/unit/controllers/test_session_*.py` + `events/session-*.json` | ninguno | no |

**Por que NO hay colision**:

- Cada worktree crea SU PROPIA subcarpeta en `controllers/` y SU
  archivo en `models/`.
- `core/models/event.py` (potencial choke point) NO se modifica en
  estos worktrees: T7 (en el scaffold) ya registro las 4 operations
  con sus 10 actions en el `build_event_model({...})`. Cada operation
  tiene sus Pydantic schemas declaradas en el `models/<op>.py` que
  cada worktree crea. **NO hay edicion concurrente del event.py**.
- Los services (T8) ya existen y son interfaces estables (Interface
  Stability check OK).
- `controllers/__init__.py` por operation existe (lo crea el worktree
  responsable). NO hay un `controllers/__init__.py` raiz que requiera
  edicion concurrente (la descubrimiento es dinamico via
  `import_controller`).

Limite practico: **4 worktrees** (uno por operation). Cumple las
recomendaciones del estandar (5-7 max).

## Fase secuencial final tras worktrees

Tras integrar WT-A..WT-D en `dev` (uno por PR: PR 7 con WT-A+WT-B y
PR 8 con WT-C+WT-D — decision combinada para reducir overhead de
review):

```text
PR 8.3  rate-limit seed                       (operativo, toca AWS dev)
PR 8.4  deploy auth -> dev                    (operativo)
PR 9    integration tests + ER + limpieza     (verificacion E2E)
```

Todo secuencial.

## Como lanzar un worktree

Tras PR 6 mergeado:

```bash
# 1. Actualizar la rama base
git checkout dev
git pull origin dev

# 2. Crear el worktree (por ejemplo para WT-A register)
git worktree add ../portfolio-wt-register feature/auth-infra-basics-7-register
cd ../portfolio-wt-register
git checkout -b feature/auth-infra-basics-7-register

# 3. Instalar deps si hace falta (pnpm + uv sync para el lambda)
pnpm install
cd serverless/lambda/services/auth && uv sync

# 4. Implementar la tarea (T9 en este caso)
#    - Crear controllers/register/{start,verify_magic_link,verify_code}.py
#    - Crear models/register.py
#    - Crear tests + events

# 5. Verificar
serverless tests --type=unit --lambda=auth
serverless run --stage=local --lambda=auth --event=events/register-start.json

# 6. Commitear y push (cuando la fase este verde)
git add -A
git commit -m "feat(auth/register): controllers start + verify-magic-link + verify-code"
git push -u origin feature/auth-infra-basics-7-register
gh pr create --base dev --title "..." --body "..."
```

### Con subagentes en paralelo

Para lanzar las 4 ramas en paralelo a partir del mismo punto base
(post PR 6), usar 4 instancias de `Agent` con `isolation: "worktree"`
y prompts que apunten cada uno a su .md de fase:

```text
Agent A: prompt = "Implementar T9 segun docs/specs/01-auth-infra-basics/05-...md seccion register + 08-...md tarea T9"
Agent B: prompt = "Implementar T10 segun ... operation login"
Agent C: prompt = "Implementar T11 segun ... operation verify"
Agent D: prompt = "Implementar T12 segun ... operation session"
```

Cada uno crea su rama, implementa, verifica, hace push y abre su PR
independiente (o uno por par segun el agrupamiento PR 7 / PR 8).

## Que NO se paraleliza

- T1, T2, T3, T4, T5, T6, T7, T8: dependencias estrictas, secuenciales.
- T13: docs/claude — paralelizable con T2-T12 pero por simplicidad va
  en PR 1 (junto con T1).
- T14 (seccion 11): es el cierre, toca archivos transversales
  (`docs/diagrams/db-er.mmd`) y consolida E2E. SIEMPRE secuencial al
  final.
- `core/models/event.py`: editado SOLO una vez en T7. Cada worktree
  asume ese archivo ya tiene las 4 operations registradas.
- `manifest.yaml`, `pyproject.toml`, `uv.lock` del lambda auth:
  editados SOLO en T7 (scaffold). Si una operation nueva requiere una
  dep nueva (no esperado: todas las deps ya estan en `shared.auth` o
  `shared.lambda_kit`), se hace en un commit secuencial al final.

## Anti-patrones evitados

| Anti-patron | Como lo evitamos |
|-------------|------------------|
| Lanzar worktrees antes de la base | PR 1..PR 6 secuenciales, mergeados antes de empezar PR 7 |
| Dos worktrees editan `models/event.py` | T7 lo deja completo desde el scaffold; los worktrees NO lo tocan |
| Conflicto en `controllers/__init__.py` raiz | NO existe — descubrimiento dinamico por `import_controller` |
| Conflicto en `pyproject.toml` del lambda | NO se edita en los worktrees (todas las deps via shared) |
| Worktree D depende de C | Cada operation es 100% independiente (services ya implementados en T8) |
| Mas de 7 worktrees concurrentes | Maximo 4 |

## Resumen visual

```text
PR 1 spec+claude  ─────────────┐
PR 2 shared.auth  ─────────────┤  (BASE secuencial)
PR 3 schema Neon  ─────────────┤
PR 4 resources    ─────────────┤
PR 5 email worker ─────────────┤
PR 6 auth scaffold+services ───┘
                               │
       ┌───────────┬───────────┼───────────┬───────────┐
       │           │           │           │           │
     WT-A        WT-B        WT-C        WT-D       (T13 ya hecho en PR 1)
   register    login       verify      session
       │           │           │           │
       └───────────┴───────────┴───────────┘
                               │
                  PR 7 (WT-A + WT-B mergeados)
                  PR 8 (WT-C + WT-D mergeados + rate-limit + deploy)
                               │
                               v
                  PR 9 verificacion E2E + limpieza (SEC. 11)
```

Maximo paralelismo util: **4 worktrees concurrentes** durante la fase
de operations. El resto secuencial.
