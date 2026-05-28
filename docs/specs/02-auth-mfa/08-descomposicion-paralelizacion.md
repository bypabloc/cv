# 08. Descomposicion para Paralelizacion — plan 02

> Plan **Large** (~147 archivos). 11 tareas atomicas. Las tareas T9,
> T10 (mfa, webauthn) son paralelizables entre si. Login extension
> (T11) viene al final porque toca codigo del plan 01.

## Grafo de dependencias

```text
T1 plan + claude docs                          (raiz)
  |
  +--> T2 shared.auth extension                (raiz tras T1)
  |     (totp, webauthn, recovery, encryption)
  |     |
  |     +--> tests shared.auth                 (parte de T2)
  |
  +--> T3 shared.aws KMS wrappers              (raiz tras T1, indep T2)
  |
  +--> T4 schema Neon + modelos + repository    (raiz tras T1)
  |
  +--> T5 resources (webauthn-challenges DDB)   (raiz tras T1)
  |
  +--> T6 manifest update + provisioner kms     (raiz tras T1; afecta T7+)
  |
  +--> T7 lambda auth: services nuevos         (depende de T2..T6)
  |     (mfa_method, totp, webauthn, recovery, challenge, auth-helper)
  |
  +--> T8 lambda auth: EventModel + operations registry + models Pydantic
  |     (depende de T7)
  |
  +--> T9 controllers/mfa/                     (depende de T8)
  |     |  (paralelo con T10)
  |     +--> 8 controllers + tests
  |
  +--> T10 controllers/webauthn/               (depende de T8)
  |     |  (paralelo con T9)
  |     +--> 6 controllers + tests
  |
  +--> T11 login extension (verify-password, verify-totp + login.start delta)
  |     (depende de T7 + T9; ya que reutiliza TotpService y MfaMethodService)
  |     |
  |     +--> 2 controllers nuevos + 1 modificado (login/start.py)
  |
  +--> T12 verificacion E2E + ER + limpieza spec  (seccion 11)
```

## Tareas

### T1: Plan + claude docs

- **Archivos**:
  - `docs/specs/02-auth-mfa/*.md` (12).
  - `.claude/docs/auth-system/04-mfa.md`
  - `.claude/docs/auth-system/05-webauthn.md`
  - `.claude/rules/auth-system.md` (modificar).
  - `.claude/rules/lambda-shared-imports.md` (modificar — catalogo).
  - `.claude/skills/auth-system/SKILL.md` (modificar — keywords).
- **AC**: ninguna.
- **Depende de**: ninguna.
- **Paralelizable con**: ninguna.
- **Verify**:
  - markdownlint
  - Validacion skill segun `.claude/rules/claude-config-testing.md`.
- **Done**: spec + docs/claude + skill commiteados.

### T2: shared.auth extension

- **Archivos**:
  - `shared/auth/{totp,webauthn,recovery_codes,encryption}.py`
  - `shared/auth/__init__.py` (modificar)
  - `shared/auth/pyproject.toml` (modificar — agregar deps)
  - `shared/auth/uv.lock` (regenerar)
  - `shared/tests/unit/shared/auth/test_*` (17 nuevos)
- **AC**: AC-24 (encryption at rest).
- **Depende de**: T1.
- **Paralelizable con**: T3, T4, T5, T6.
- **Verify**:
  `serverless lint-deps --shared`
  `serverless tests --type=unit --shared`
- **Done**: 17 tests verdes, coverage >= 95% en modulos nuevos.

### T3: shared.aws KMS wrappers

- **Archivos**:
  - `shared/aws/__init__.py` (modificar — re-exports kms_generate_data_key, kms_decrypt)
  - `shared/aws/kms.py` (NUEVO — wrappers boto3)
  - `shared/aws/pyproject.toml` (sin cambios — boto3 ya esta)
  - `shared/tests/unit/shared/aws/test_kms_*.py` (4 tests con moto)
- **AC**: soporta AC-24 indirectamente.
- **Depende de**: T1.
- **Paralelizable con**: T2, T4, T5, T6.
- **Verify**: `serverless tests --type=unit --shared`.
- **Done**: 4 tests verdes; T2 puede importar de aqui (depende de la
  publicacion de shared.aws.kms_* re-exports).

> Nota: T2 (`shared.auth.encryption.py`) importa de `shared.aws.kms_*`.
> Por orden topologico: T3 antes que T2. Si se trabajan en paralelo,
> T2 puede stub `shared.aws.kms_*` con `# type: ignore[attr-defined]`
> hasta que T3 merge. Recomendado: completar T3 antes de T2.

### T4: Schema Neon + repositories

- **Archivos**:
  - `shared/db/alembic/versions/00000003_auth_mfa.py`
  - `shared/db/models/auth/{mfa_method,recovery_code,webauthn_credential}.py`
  - `shared/db/models/auth/enums.py` (modificar — agregar `AuthMfaKind`)
  - `shared/db/models/auth/__init__.py` (modificar)
  - `shared/db/repositories/auth_mfa.py`
  - `shared/tests/unit/shared/db/repositories/test_auth_mfa_*.py` (14)
- **AC**: AC-23.
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T5, T6.
- **Verify**:
  Branch Neon de prueba upgrade + downgrade + upgrade idempotente
  `serverless tests --type=unit --shared`
- **Done**: migration up/down OK, 14 tests verdes.

### T5: Resources

- **Archivos**:
  - `serverless/lambda/resources/dynamodb/webauthn-challenges.yaml`
- **AC**: soporta AC-11..14.
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T4, T6.
- **Verify**:
  `serverless validate-catalog --stage=dev`
  `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
- **Done**: tabla creada en AWS dev.

### T6: Manifest update + provisioner KMS (si aplica)

- **Archivos**:
  - `serverless/lambda/services/auth/manifest.yaml` (modificar)
  - `devtools/serverless/provisioner.py` (modificar SOLO si no soporta
    `uses.kms` declarativo)
  - tests del provisioner si se toca.
- **AC**: soporta AC-1, AC-12 (necesita IAM correcto).
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T4, T5.
- **Verify**: `serverless deploy --lambda=auth --stage=dev --dry-run`.
- **Done**: manifest actualizado + provisioner soporta `uses.kms`.

### T7: Services del lambda auth

- **Archivos**:
  - `services/auth/core/services/{mfa_method,totp,webauthn,recovery_codes,challenge,auth}_service.py`
  - tests unit ~25.
- **AC**: transversal.
- **Depende de**: T2, T3, T4, T5, T6 (cierre transitivo necesario).
- **Paralelizable con**: ninguna en su capa.
- **Verify**: `serverless tests --type=unit --lambda=auth`.
- **Done**: 6 services + 25 tests verdes.

### T8: EventModel + operations + models Pydantic

- **Archivos**:
  - `core/settings/operations.py` (modificar)
  - `core/models/event.py` (modificar)
  - `core/models/mfa.py` (NUEVO)
  - `core/models/webauthn.py` (NUEVO)
  - `core/models/login.py` (modificar — schemas nuevos)
  - tests models ~10.
- **AC**: soporta validacion.
- **Depende de**: T7 (services existen).
- **Paralelizable con**: ninguna en su capa.
- **Verify**: `serverless tests --type=unit --lambda=auth`.
- **Done**: 10 tests models verdes; el lambda compila con
  EVENT_MODEL extendido.

### T9: Controllers mfa/ (paralelo con T10)

- **Archivos**:
  - `core/controllers/mfa/{setup_totp,confirm_totp,setup_email_code,set_preferred,disable,list,recovery_codes_generate,recovery_codes_consume}.py`
  - `events/mfa-*.json` (8)
  - tests controllers/test_mfa_*.py (~15)
- **AC**: AC-1..AC-10.
- **Depende de**: T7, T8.
- **Paralelizable con**: T10.
- **Verify**: `serverless tests --type=unit --lambda=auth`.
- **Done**: 8 controllers + 15 tests verdes.

### T10: Controllers webauthn/ (paralelo con T9)

- **Archivos**:
  - `core/controllers/webauthn/{register_options,register_verify,login_options,login_verify,list_credentials,delete_credential}.py`
  - `events/webauthn-*.json` (6)
  - tests controllers/webauthn/_fixtures.py
  - tests controllers/test_webauthn_*.py (~10)
- **AC**: AC-11..AC-17, AC-25.
- **Depende de**: T7, T8.
- **Paralelizable con**: T9.
- **Verify**: idem.
- **Done**: 6 controllers + 10 tests verdes.

### T11: Login extension (verify-password + verify-totp + login.start delta)

- **Archivos**:
  - `core/controllers/login/{verify_password,verify_totp}.py` (NUEVOS)
  - `core/controllers/login/start.py` (modificar — agregar deteccion
    de password en body + methods MFA en response)
  - tests/unit/controllers/test_login_verify_*.py (~5)
  - tests/unit/controllers/test_login_start_with_password_*.py (~3)
- **AC**: AC-18..AC-22.
- **Depende de**: T7, T9 (necesita TotpService + MfaMethodService).
- **Paralelizable con**: T10.
- **Verify**: idem.
- **Done**: 2 controllers nuevos + 1 modificado + 8 tests verdes.

### T12: Verificacion E2E + ER + limpieza spec (= seccion 11)

- **Archivos**:
  - `services/auth/tests/integration/test_mfa_*.py` y
    `test_webauthn_*.py` (7)
  - `docs/diagrams/db-er.mmd` (modificar)
  - `docs/specs/02-auth-mfa/` (eliminar)
- **AC**: TODOS.
- **Depende de**: T2..T11.
- **Paralelizable con**: ninguna.
- **Verify**: ver [11-verificacion-e2e.md](11-verificacion-e2e.md).
- **Done**: bateria verde.

## Tabla de paralelismo

| Tarea | Depende de | Paralelizable con |
|-------|------------|--------------------|
| T1 plan + docs/claude | — | — |
| T2 shared.auth ext | T1 (T3) | T4, T5, T6 |
| T3 shared.aws KMS | T1 | T2, T4, T5, T6 |
| T4 schema Neon + repos | T1 | T2, T3, T5, T6 |
| T5 resources DDB | T1 | T2, T3, T4, T6 |
| T6 manifest + provisioner | T1 | T2, T3, T4, T5 |
| T7 services auth | T2..T6 | — |
| T8 EventModel + models | T7 | — |
| T9 controllers mfa | T8 | T10 |
| T10 controllers webauthn | T8 | T9 |
| T11 login extension | T7, T9 | T10 |
| T12 E2E + ER + cleanup | T2..T11 | — |

## Maximo paralelismo util

- Tras T1: lanzar **T2 + T3 + T4 + T5 + T6** en 5 worktrees
  concurrentes (raices, archivos disjuntos). Limite practico
  recomendado.
- Tras T7 + T8: lanzar **T9 + T10** en 2 worktrees concurrentes.
- Tras T9: lanzar T11 (depende de T9 por TotpService usage).

3-5 worktrees concurrentes. Dentro del limite.

## Anti-patrones evitados

- T2 (`shared.auth.encryption`) importa de `shared.aws.kms_*` (T3).
  Para evitar circular trabajo, T3 termina antes (es chico: ~80 lineas
  + 4 tests). Si los 2 se hacen en paralelo y T2 stubea, requiere
  rebase antes del merge.
- T6 (manifest + provisioner) toca un archivo central (`provisioner.py`).
  Hacerse antes del PR de T7 evita conflictos.
- T9 y T10 son worktree-safe (carpetas disjuntas `controllers/mfa/` vs
  `controllers/webauthn/`). NO modifican `event.py` (lo hace T8 ya en
  scaffold).
- T11 modifica `login/start.py` (existente desde plan 01). NO se
  puede paralelizar con otro worktree que tambien quiera tocar ese
  archivo. T11 es el unico que lo toca en este plan.
