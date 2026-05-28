# 10. Paralelizacion con git worktrees — plan 03

## Base secuencial

```text
PR 1  T1 plan + docs/claude         <-- BASE 1
PR 2  T2 shared.auth.admin          <-- BASE 2 (require_admin)
PR 3  T3 schema + repos             <-- BASE 3 (modelos + auth_user_sessions table)
PR 4  T4 SSM admin-emails           <-- BASE 4
PR 5  T5 email-worker plantillas    <-- BASE 5 (independiente; mergeable en paralelo a 2-4)
PR 6  T6 users scaffold + services  <-- BASE 6 (depende de 2+3+4)
```

BASE 1..6 secuencial. PR 5 puede mergearse paralelo a PR 2-4 si el
equipo coordina, pero recomendado en orden para review claridad.

## Fase paralela: worktrees tras PR 6 mergeado

| Worktree | Tarea | Archivos | Colision? |
|----------|-------|----------|-----------|
| WT-A | T7 controllers profile | `controllers/profile/*` + events + tests | no |
| WT-B | T8 controllers status | `controllers/status/*` + events + tests | no |
| WT-C | T9 controllers admin | `controllers/admin/*` + events + tests | no |
| WT-D | T10 sessions tracking en auth | `services/auth/core/services/session_tracking_service.py` + 8 controllers MODIFICADOS de auth | si — con planes 01/02 si alguien mas toca esos 8 archivos (no aplica) |

WT-A, WT-B, WT-C son disjuntos entre si (subcarpetas distintas en
`services/users/`). WT-D vive en `services/auth/` (lambda distinto). 4
worktrees concurrentes seguros.

### Tabla de colisiones

| Archivo | T7 | T8 | T9 | T10 |
|---------|-----|------|------|------|
| `services/users/controllers/profile/*` | WRITE | — | — | — |
| `services/users/controllers/status/*` | — | WRITE | — | — |
| `services/users/controllers/admin/*` | — | — | WRITE | — |
| `services/users/events/*` | WRITE (4) | WRITE (3) | WRITE (7) | — |
| `services/users/tests/unit/controllers/*` | WRITE | WRITE | WRITE | — |
| `services/users/core/models/event.py` | — | — | — | — (cerrado en T6) |
| `services/users/core/models/{profile,status,admin}.py` | — | — | — | — (cerrados en T6) |
| `services/auth/core/services/session_tracking_service.py` | — | — | — | WRITE (nuevo) |
| `services/auth/core/controllers/{register,login,session,webauthn,mfa}/*.py` (8 archivos) | — | — | — | WRITE (inyeccion minima de 2-3 lineas) |
| `services/auth/tests/integration/test_session_tracking_*.py` | — | — | — | WRITE (4 nuevos) |

`services/users/events/` es la unica zona compartida en cuanto a
carpeta. Pero los archivos son disjuntos (`profile-*.json` vs
`status-*.json` vs `admin-*.json`) — File Exclusivity OK.

## Fase secuencial final

Tras T7+T8+T9+T10 mergeados:

- PR 9 T11 (rate-limit seed + deploy users) — operativo
- PR 9 T12 (integration tests + ER + cleanup) — seccion 11

## Como lanzar worktree

Mismo patron de planes 01 y 02. Ejemplo WT-D (sessions tracking):

```bash
git checkout dev
git pull origin dev

git worktree add ../portfolio-wt-sessions-tracking feature/auth-users-mgmt-8-sessions
cd ../portfolio-wt-sessions-tracking
git checkout -b feature/auth-users-mgmt-8-sessions

pnpm install
cd serverless/lambda/services/auth && uv sync

# Implementar T10:
# 1. core/services/session_tracking_service.py
# 2. Modificar 8 controllers para inyectar:
#    - controllers/register/verify_magic_link.py: tras issue_access+refresh,
#      llamar session_tracking_service.on_session_created(...)
#    - controllers/register/verify_code.py: idem
#    - controllers/login/{verify_magic_link, verify_code, verify_password, verify_totp}.py: idem
#    - controllers/webauthn/login_verify.py: idem
#    - controllers/mfa/recovery_codes_consume.py: idem
#    - controllers/session/refresh.py: on_session_rotated(...) en rotation
#    - controllers/session/logout.py: on_session_revoked(...) tras blacklist
# 3. Agregar 4 tests integration

# Verificar
serverless tests --type=unit --lambda=auth      # no regresiones plan 01/02
serverless tests --type=integration --lambda=auth  # 4 tests nuevos verdes

# Commit + push + PR
```

### Con subagentes en paralelo

4 instancias de `Agent` con `isolation: "worktree"`:

```text
Agent A (T7 profile): "Implementar segun docs/specs/03-.../05-...md
  controller profile.* + docs/specs/03-.../08-...md tarea T7"
Agent B (T8 status): "... seccion status + tarea T8"
Agent C (T9 admin): "... seccion admin + tarea T9"
Agent D (T10 sessions tracking): "... seccion 'Cambios al Lambda auth'
  + tarea T10. Notas: NO modificar los servicios existentes, solo
  inyectar la llamada en 8 controllers."
```

## Que NO se paraleliza

- T1..T6: secuenciales.
- T11 (rate-limit + deploys): operativo final.
- T12 (verificacion E2E): cierre.

## Anti-patrones evitados

- T7, T8, T9 no editan `event.py`, `operations.py`, `models/{profile,status,admin}.py`
  (todos cerrados en T6 con los 14 actions registrados desde el inicio).
- WT-A, WT-B, WT-C son completamente disjuntos.
- T10 toca un lambda DIFERENTE (auth) — NO colisiona con T7/T8/T9.
- Inyeccion del session tracking en los 8 controllers del lambda auth
  es minima (2-3 lineas en `execute()` tras emitir tokens). No
  refactoriza la logica, solo agrega una llamada al helper.

## Resumen visual

```text
PR 1 spec+docs/claude          ─┐
PR 2 shared.auth.admin         ─┤
PR 3 schema + repos            ─┤   BASE secuencial
PR 4 SSM admin-emails          ─┤
PR 5 email-worker ext          ─┤
PR 6 users scaffold + services ─┘
                                │
       ┌───────────┬────────────┼────────────┬───────────┐
       │           │            │            │           │
     WT-A        WT-B         WT-C         WT-D
   profile     status       admin       sessions
   controllers controllers  controllers  tracking
       │           │            │            │ (en lambda auth)
       └───────────┴────────────┴────────────┘
                                │
                       PR 7 (T7+T8+T9 mergeados)
                       PR 8 (T10 mergeado)
                                │
                                v
                       PR 9 verificacion E2E + cleanup (SEC. 11)
```

Maximo paralelismo util: **4 worktrees concurrentes**.
