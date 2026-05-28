# 09. Commits — plan 02

> Rama base: `feature/auth-mfa-N-<x>` desde `dev` (plan 01 ya mergeado).
> Multiples PRs incrementales a `dev`. Conventional Commits espanol.

## Modelo de PRs

**8 PRs en total**. Cada uno deja el repo verde y deployable. Mapeo
1:1 con las fases del README + tareas del 08-descomposicion.

### Ramas

```text
dev (post plan 01 mergeado)
 ├── feature/auth-mfa-1-spec-and-docs              (T1)
 ├── feature/auth-mfa-2-shared-auth-ext-and-kms    (T2 + T3)
 ├── feature/auth-mfa-3-schema-and-repos           (T4)
 ├── feature/auth-mfa-4-infra-and-manifest         (T5 + T6)
 ├── feature/auth-mfa-5-services                   (T7 + T8)
 ├── feature/auth-mfa-6-controllers-mfa-webauthn   (T9 + T10)  PARALELO
 ├── feature/auth-mfa-7-login-extension            (T11)
 └── feature/auth-mfa-8-verificacion-e2e           (T12)
```

## PR 1 — `docs(specs+claude): plan 02-auth-mfa + docs/auth-system MFA + WebAuthn`

#### Commit 1.1 — `docs(specs): plan 02-auth-mfa`

- Agrega `docs/specs/02-auth-mfa/` (12 archivos).
- **Verificacion**: markdownlint OK.

#### Commit 1.2 — `docs(claude): docs/auth-system/04-mfa.md + 05-webauthn.md + rule update + skill keywords`

- Agrega `.claude/docs/auth-system/04-mfa.md`, `05-webauthn.md`.
- Modifica `.claude/rules/auth-system.md` agregando secciones.
- Modifica `.claude/skills/auth-system/SKILL.md` agregando keywords
  (`mfa`, `totp`, `passkey`, `webauthn`, `2fa`, etc.).
- **NO modifica `.claude/rules/lambda-shared-imports.md`** — el
  catalogo se actualiza en Commit 2.3 (PR 2), una vez que el codigo
  publicado de `shared.auth` + `shared.aws.kms` ya existe (evita la
  ventana de incoherencia donde el catalogo cita paquetes que aun
  no estan en `pyproject.toml`).
- **Verificacion**:
  - markdownlint
  - 5 prompts ES via `claude -p` (validacion skill).
- **AC**: ninguna (meta).

> Merge PR 1.

---

## PR 2 — `feat(shared): aws.kms (CMK directa) + auth.totp + auth.webauthn + auth.recovery_codes + catalogo de portadores`

#### Commit 2.1 — `feat(shared/aws): wrappers kms_encrypt + kms_decrypt (CMK directa)`

- Agrega `shared/aws/kms.py` con `kms_encrypt` / `kms_decrypt`
  (Encrypt/Decrypt directos, NO GenerateDataKey).
- Modifica `shared/aws/__init__.py` re-exports.
- Agrega 4 tests con moto en `shared/tests/unit/shared/aws/test_kms_*.py`.
- **Verificacion**: `serverless tests --type=unit --shared`.

#### Commit 2.2 — `feat(shared/auth): totp + webauthn (post-spike) + recovery codes`

- **Pre-commit**: spike de 30 min validando python-fido2 API actual
  (ver decision 4 + nota en 03-shared-auth-extension.md). Ajustar
  el codigo del webauthn.py si la firma difiere.
- Agrega `shared/auth/{totp,webauthn,recovery_codes}.py`. NO
  `encryption.py` (decision 1 — KMS CMK directa hace el cifrado).
- Modifica `shared/auth/__init__.py`, `pyproject.toml` (agregar
  SOLO pyotp + python-fido2, sin cryptography ni segno), `uv.lock`.
- Agrega 13 tests en `shared/tests/unit/shared/auth/`.
- **Verificacion**:
  - `serverless lint-deps --shared`
  - `serverless tests --type=coverage --shared` (>= 80% per-file).

#### Commit 2.3 — `docs(claude): catalogo de portadores con pyotp + python-fido2 + boto3.kms`

- Modifica `.claude/rules/lambda-shared-imports.md` agregando los 3
  paquetes nuevos al catalogo. Hace este commit en PR 2 (NO en PR 1)
  para que el catalogo refleje SIEMPRE el codigo publicado, sin
  ventana de incoherencia.
- **Verificacion**:
  - markdownlint
  - skill validation (`.claude/rules/claude-config-testing.md`)

> Merge PR 2.

---

## PR 3 — `feat(db): schema auth_mfa + auth_webauthn + repositories`

#### Commit 3.1 — `feat(db/models): mfa_method + recovery_code + webauthn_credential`

- Agrega modelos + actualiza `enums.py` con `AuthMfaKind`.
- Modifica `models/auth/__init__.py`.
- **Verificacion**: `python -m compileall -q`.

#### Commit 3.2 — `feat(db/alembic): migration 00000003_auth_mfa`

- Agrega migration.
- **Verificacion** (branch Neon de prueba):
  - upgrade head -> down -1 -> upgrade head idempotente.

#### Commit 3.3 — `feat(db/repositories): auth_mfa helpers + 14 tests unit`

- Agrega `repositories/auth_mfa.py` + tests.
- **Verificacion**: `serverless tests --type=unit --shared`.
- **AC**: AC-23 indirectamente.

#### Commit 3.4 — `chore(db): aplica migration 00000003 en dev`

- Operativo: `serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev`.
- Verificacion: `current.json` muestra revision `00000003`.

> Merge PR 3.

---

## PR 4 — `feat(infra): webauthn-challenges DDB + manifest auth kms + provisioner`

#### Commit 4.1 — `feat(resources/dynamodb): webauthn-challenges`

- Agrega `resources/dynamodb/webauthn-challenges.yaml`.
- **Verificacion**: `serverless validate-catalog`.

#### Commit 4.2 — `feat(provisioner): soporte uses.kms en manifest` (SI APLICA)

- Modifica `devtools/serverless/provisioner.py` si el shape `uses.kms`
  no esta hoy. Agrega tests del provisioner.
- **Verificacion**: tests + smoke `serverless deploy --dry-run`.

#### Commit 4.3 — `feat(services/auth): manifest update con kms + webauthn env vars`

- Modifica `services/auth/manifest.yaml`.
- **Verificacion**: `serverless deploy --lambda=auth --stage=dev --dry-run --aws-profile=tfs-dev`.

#### Commit 4.4 — `chore(infra): provision dev (webauthn-challenges + iam kms)`

- Operativo:
  `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
  `serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev`
- Verificacion: `serverless status --lambda=auth --stage=dev`.

> Merge PR 4.

---

## PR 5 — `feat(auth): services internos + AppConfig + EventModel extension`

#### Commit 5.1 — `feat(auth/config): AppConfig con kms_totp_key_id + webauthn_*`

- Modifica `core/settings/config.py`.
- **Verificacion**: `serverless tests --type=unit --lambda=auth`.

#### Commit 5.2 — `feat(auth/services): mfa_method + totp + webauthn + recovery_codes + challenge + auth helper`

- Agrega 6 services + ~25 tests.
- **Verificacion**: `serverless tests --type=coverage --lambda=auth` (>= 85%).

#### Commit 5.3 — `feat(auth/models): mfa.py + webauthn.py + login.py extension`

- Agrega modelos Pydantic + ~10 tests.
- Modifica `event.py` y `operations.py`.
- **Verificacion**: idem.

> Merge PR 5.

---

## PR 6 — `feat(auth): controllers mfa + webauthn (worktrees paralelos)`

Worktrees T9 + T10. Mergear los 2 en un solo PR para reducir overhead.

#### Commit 6.1 — `feat(auth/mfa): controllers setup-totp/confirm-totp/setup-email-code/set-preferred/disable/list`

- Agrega 6 controllers de mfa basicos + 6 events + ~10 tests.
- **AC**: AC-1..AC-6.
- **Verificacion**: `serverless tests --type=unit --lambda=auth`.

#### Commit 6.2 — `feat(auth/mfa): controllers recovery-codes-generate + recovery-codes-consume`

- Agrega 2 controllers + 2 events + ~5 tests.
- **AC**: AC-7..AC-10.

#### Commit 6.3 — `feat(auth/webauthn): controllers register-options + register-verify`

- Agrega 2 controllers + 2 events + 5 tests + `_fixtures.py`.
- **AC**: AC-11, AC-12.

#### Commit 6.4 — `feat(auth/webauthn): controllers login-options + login-verify`

- Agrega 2 controllers + 2 events + ~5 tests.
- **AC**: AC-13, AC-14, AC-15.

#### Commit 6.5 — `feat(auth/webauthn): list-credentials + delete-credential`

- Agrega 2 controllers + 2 events + 3 tests.
- **AC**: AC-16, AC-17, AC-25.

> Merge PR 6.

---

## PR 7 — `feat(auth): login extension con password + verify-totp`

#### Commit 7.1 — `feat(auth/login): verify-password controller`

- Agrega `controllers/login/verify_password.py` + event + ~3 tests.
- **AC**: AC-18, AC-21.

#### Commit 7.2 — `feat(auth/login): verify-totp controller`

- Agrega `controllers/login/verify_totp.py` + event + ~2 tests.
- **AC**: AC-19.

#### Commit 7.3 — `feat(auth/login): start delta con password opcional + deteccion MFA`

- Modifica `controllers/login/start.py` agregando logica de
  password (si presente -> validar) + listar methods MFA + emitir
  temp JWT step=2 si MFA configurado.
- **Verificacion incremental**:
  - tests unit del controller existente NO regresionan.
  - tests nuevos `test_login_start_with_password_*.py` (~3) verdes.
- **AC**: AC-20.

#### Commit 7.4 — `chore(rate-limit): seed reglas MFA + WebAuthn + login.verify-* en dev/stage/prod`

- Operativo. 8 reglas nuevas listadas en seccion 04.
- Verificacion: `serverless rate-limit list --stage=dev`.

#### Commit 7.5 — `chore(deploy): auth lambda -> dev`

- Operativo.
- Comando: `serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev`.

> Merge PR 7.

---

## PR 8 — `chore(specs): verificacion E2E + cierre del plan 02-auth-mfa`

#### Commit 8.1 — `test(auth): integration tests MFA + WebAuthn + login con password`

- Agrega 7 archivos en `tests/integration/`.
- **Verificacion**:
  `serverless tests --type=integration --lambda=auth`
  (con AWS dev + Neon dev disponibles).

#### Commit 8.2 — `docs(diagrams): actualiza db-er.mmd con cluster auth_mfa_*`

- Modifica `docs/diagrams/db-er.mmd`.

#### Commit 8.3 — `chore(specs): elimina la carpeta efimera del plan 02`

- `git rm -r docs/specs/02-auth-mfa/`.
- **Verificacion**:
  - Bateria completa de [11-verificacion-e2e.md](11-verificacion-e2e.md) verde.

> Merge PR 8 a `dev`. Promociones a `stage` y `main` siguen
> `.claude/rules/git-workflow.md`.

## Resumen de la secuencia

```text
PR 1  spec + docs/claude (sin catalogo aun)    (sin codigo)
PR 2  shared.aws.kms + shared.auth ext + catalogo  transversal
PR 3  schema + repos                           AC-23
PR 4  infra (DDB + manifest + spike provisioner)  AC-12 (IAM)
PR 5  services internos del lambda             transversal
PR 6  controllers mfa + webauthn (paralelos)   AC-1..17, AC-25
PR 7  login ext (pass + TOTP) + rate-limit IP + deploy  AC-18..22
PR 8  E2E + ER + cleanup spec                  AC-23, AC-24, AC-26, AC-27
```

## Body de PR — template

```markdown
## Problema

- (subscope que cubre este PR del plan 02)

## Solucion

- (paralelo a Problema)

## Como probar

```bash
# (bateria especifica del PR)
```

## TODO

- (vacio o follow-ups)
```

NUNCA atribucion de IA.
