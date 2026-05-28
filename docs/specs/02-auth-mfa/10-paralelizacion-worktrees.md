# 10. Paralelizacion con git worktrees — plan 02

## Base secuencial

```text
PR 1  T1 plan + docs/claude            <-- BASE 1
PR 2  T2 shared.auth + T3 shared.aws   <-- BASE 2 (transversal)
PR 3  T4 schema + repos                <-- BASE 3
PR 4  T5 infra + T6 manifest+provis    <-- BASE 4
PR 5  T7 services + T8 EventModel      <-- BASE 5
```

BASE 1..5 secuencial. Cada PR mergeado antes de empezar el siguiente.

## Fase paralela: worktrees tras PR 5 mergeado

Tras PR 5 mergeado en `dev`, el repo tiene services + EventModel
listos. Los controllers no existen aun. Se abre ventana de
paralelizacion:

| Worktree | Tarea | Archivos nuevos | Modificados | Colision? |
|----------|-------|-----------------|-------------|-----------|
| WT-A | T9 controllers mfa | `controllers/mfa/*` + tests + events | ninguno | no |
| WT-B | T10 controllers webauthn | `controllers/webauthn/*` + tests + events | ninguno | no |
| WT-C | T11 login extension | `controllers/login/{verify_password,verify_totp}.py` + tests | `controllers/login/start.py` | si — con T9 si T9 toca login/start (no lo toca, OK) |

WT-A y WT-B son 100% disjuntos. WT-C modifica `login/start.py` que
es un archivo del plan 01. NO se solapa con WT-A ni WT-B porque T9
solo toca `controllers/mfa/` y T10 solo `controllers/webauthn/`.

### Tabla de colisiones

| Archivo | T9 | T10 | T11 | Status |
|---------|-----|------|------|--------|
| `controllers/mfa/*` | WRITE | — | — | exclusivo T9 |
| `controllers/webauthn/*` | — | WRITE | — | exclusivo T10 |
| `controllers/login/verify_password.py` | — | — | WRITE | exclusivo T11 |
| `controllers/login/verify_totp.py` | — | — | WRITE | exclusivo T11 |
| `controllers/login/start.py` | — | — | WRITE | exclusivo T11 |
| `events/mfa-*.json` | WRITE | — | — | exclusivo T9 |
| `events/webauthn-*.json` | — | WRITE | — | exclusivo T10 |
| `events/login-verify-*.json` | — | — | WRITE | exclusivo T11 |
| `tests/unit/controllers/test_mfa_*.py` | WRITE | — | — | exclusivo T9 |
| `tests/unit/controllers/test_webauthn_*.py` | — | WRITE | — | exclusivo T10 |
| `tests/unit/controllers/test_login_*.py` | — | — | WRITE (nuevos) | exclusivo T11 |
| `tests/unit/controllers/webauthn/_fixtures.py` | — | WRITE | — | exclusivo T10 |
| `core/models/event.py` | — | — | — | sin cambios (ya hecho en T8/PR 5) |
| `core/models/{mfa,webauthn,login}.py` | — | — | — | sin cambios (ya hecho en T8/PR 5) |

Sin colisiones. 3 worktrees concurrentes.

## Fase secuencial final

```text
T11 paralelizado con T9 + T10 (PR 6 + PR 7 puede mergearse en orden).

Tras los 3 worktrees mergeados:
- PR 7.4  rate-limit seed                 (operativo)
- PR 7.5  deploy auth -> dev              (operativo)
- PR 8    integration tests + ER + cleanup (verificacion E2E)
```

## Como lanzar un worktree

Mismo patron que plan 01. Ejemplo para WT-B (webauthn):

```bash
# Asumiendo dev al dia con PR 5 mergeado
git checkout dev
git pull origin dev

git worktree add ../portfolio-wt-webauthn-controllers feature/auth-mfa-6-webauthn
cd ../portfolio-wt-webauthn-controllers
git checkout -b feature/auth-mfa-6-webauthn

# Instalar deps
pnpm install
cd serverless/lambda/services/auth && uv sync

# Implementar T10
#  - controllers/webauthn/register_options.py
#  - controllers/webauthn/register_verify.py
#  - controllers/webauthn/login_options.py
#  - controllers/webauthn/login_verify.py
#  - controllers/webauthn/list_credentials.py
#  - controllers/webauthn/delete_credential.py
#  - tests/unit/controllers/webauthn/_fixtures.py
#  - tests/unit/controllers/test_webauthn_*.py
#  - events/webauthn-*.json

# Verificar
serverless tests --type=unit --lambda=auth
serverless run --stage=local --lambda=auth --event=events/webauthn-register-options.json

# Commit + push
git add -A
git commit -m "feat(auth/webauthn): controllers register-options + register-verify + login-options + login-verify + list + delete"
git push -u origin feature/auth-mfa-6-webauthn
gh pr create --base dev --title "feat(auth): webauthn controllers" --body "..."
```

### Con subagentes en paralelo

3 instancias de `Agent` con `isolation: "worktree"`. Cada una con
prompt apuntando al archivo de la tarea correspondiente:

```text
Agent A (T9 mfa): "Implementar segun docs/specs/02-auth-mfa/05-...md
  controller mfa.* + docs/specs/02-auth-mfa/08-...md tarea T9"
Agent B (T10 webauthn): "... seccion webauthn + tarea T10"
Agent C (T11 login extension): "... login + tarea T11"
```

## Que NO se paraleliza

- T1, T2, T3, T4, T5, T6, T7, T8: dependencias estrictas.
- `event.py`, `operations.py`: editados SOLO en T8 (PR 5). Cada
  worktree asume el EventModel ya extendido.
- T6 (`provisioner.py`): central; se hace antes de T7.
- T12 (seccion 11): cierre.

## Anti-patrones evitados

| Anti-patron | Como lo evitamos |
|-------------|------------------|
| WT-C y WT-A editan login/start.py | WT-A no toca login/* — solo controllers/mfa/* |
| WT-B y WT-A editan event.py | event.py se cierra en T8/PR 5, NO en los worktrees |
| WT-B y WT-C editan models/login.py | models/login.py se cierra en T8/PR 5 |
| Mas de 5 worktrees | Maximo 3 (T9, T10, T11) |

## Resumen visual

```text
PR 1 spec+docs/claude            ─┐
PR 2 shared.auth + aws.kms       ─┤
PR 3 schema + repos              ─┤   BASE secuencial
PR 4 infra + manifest            ─┤
PR 5 services + EventModel       ─┘
                                  │
       ┌──────────────┬───────────┼───────────┐
       │              │           │           │
     WT-A           WT-B        WT-C
   mfa            webauthn    login-ext
   controllers   controllers
       │              │           │
       └──────────────┼───────────┘
                      │
              PR 6 (T9 mfa + T10 webauthn)
              PR 7 (T11 login + rate-limit + deploy)
                      │
                      v
              PR 8 verificacion E2E + cleanup (SEC. 11)
```

Maximo paralelismo util: **3 worktrees concurrentes** (T9, T10, T11)
durante la fase de controllers. Resto secuencial.
