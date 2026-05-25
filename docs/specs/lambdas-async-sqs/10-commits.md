# 10 — Lista de Commits (seccion 9)

> Secuencia explicita de commits incrementales que implementan el plan.
> Cada commit deja el repo verde, cubre AC especificos y tiene su
> verificacion incremental.

[< 09](09-idempotencia-orm.md) | [Siguiente: 11 — Worktrees >](11-paralelizacion-worktrees.md)

---

## Rama base

`feature/lambdas-async-sqs` desde `dev`. Antes del primer commit verificar:

```bash
branch=$(git branch --show-current)
case "$branch" in
  dev|stage|main|master)
    git checkout -b feature/lambdas-async-sqs   # parte de dev
    ;;
esac
```

## Secuencia de commits

### Commit 1 — `docs(specs): plan lambdas-async-sqs`

- Agrega `docs/specs/lambdas-async-sqs/` (esta carpeta — 12 archivos `.md`).
- Sin cambios de codigo.
- **Verificacion**: `python -m json.tool` sobre archivos JSON; `markdownlint`
  si esta configurado (skip si no).
- **AC**: ninguno (preparatorio).

---

### Commit 2 — `feat(serverless): catalogo YAML SQS + CloudWatch alarms`

- Crea `serverless/lambda/resources/sqs/` con 4 YAMLs:
  - `contact-form-dlq.yaml`, `contact-form-queue.yaml`
  - `tracking-events-dlq.yaml`, `tracking-events-queue.yaml`
  - `README.md`
- Crea `serverless/lambda/resources/cloudwatch_alarms/` con 2 YAMLs:
  - `contact-form-dlq-alarm.yaml`, `tracking-events-dlq-alarm.yaml`
  - `README.md`
- Sin cambios en devtools (los YAMLs todavia no se provisionan).
- **Verificacion**: `python -c "import yaml; [yaml.safe_load(...) for ...]"`
  sobre los 6 YAMLs (parsean OK).
- **AC**: AC-16 (declarado), AC-17 (declarado).

---

### Commit 3 — `feat(devtools): soporte redrive_policy + visibility_timeout en sqs-queue`

- Extiende `devtools/serverless/infra_provision.py::_provision_sqs_queue`:
  - Aplica `VisibilityTimeout` (set-queue-attributes).
  - Aplica `RedrivePolicy` con resolucion del ARN de la DLQ.
- Cambia `_PROVISION_ORDER` para sub-ordenar DLQs antes que principales.
- + Tests `test_sqs_queue_with_redrive_provisions_dlq_first`.
- **Verificacion**: `pytest devtools/tests/serverless/test_infra_provision.py -v`
- **AC**: AC-16.

---

### Commit 4 — `feat(devtools): soporte kind=cloudwatch-alarm en provisioner`

- Agrega `_provision_cloudwatch_alarm` a `infra_provision.py`.
- Agrega `'cloudwatch_alarms'` a `_RESOURCE_TYPES` y
  `'cloudwatch-alarm'` a `_PROVISION_ORDER` y `_PROVISIONERS`.
- + Tests `test_cloudwatch_alarm_idempotent`.
- **Verificacion**: `pytest devtools/tests/serverless/test_infra_provision.py
  -v -k cloudwatch`
- **AC**: AC-17 (provisioner ready; verde real en E2E).

---

### Commit 5 — `feat(serverless): provisionar SQS + alarmas en dev`

- **Commit operativo (no codigo)**: ejecuta
  `python devtools/run.py serverless provision-infra --stage=dev
  --aws-profile=tfs-dev`.
- Crea en AWS: 4 colas SQS, 2 alarmas CloudWatch, 6 parametros SSM nuevos.
- + Captura del output en el body del commit message.
- **Verificacion**: `aws sqs list-queues --profile tfs-dev | jq` muestra las
  4 colas; `aws cloudwatch describe-alarms --profile tfs-dev | jq` muestra
  las 2 alarmas.
- **AC**: AC-16 (verde), AC-17 (verde — la alarma esta en OK).

---

### Commit 6 — `feat(devtools): soporte trigger.type=sqs en manifest.yaml`

- Extiende `devtools/serverless/provisioner.py`:
  - `_VALID_TRIGGERS = ('direct', 'http', 'sqs')`.
  - `_build_trigger`: nuevo branch `sqs` con `queue`, `batch_size`,
    `function_response_types`.
  - `_wire_sqs_trigger`: crea/actualiza Event Source Mapping.
- + `uses.queues` con `access: producer | consumer`:
  - `_SQS_ACTIONS` mapping.
  - `_sqs_statements` para IAM.
  - Env vars `SSM_<UPPER>_QUEUE_URL_PATH` inyectadas en `_build_env_vars`
    cuando hay `uses.queues`.
- + Tests `test_trigger_sqs_creates_event_source_mapping`,
  `test_uses_queues_consumer_generates_iam_statement`,
  `test_uses_queues_producer_inyecta_env_var_ssm_url_path`.
- **Verificacion**: `pytest devtools/tests/serverless/test_provisioner.py -v`
- **AC**: AC-15.

---

### Commit 7 — `feat(shared): nuevo subpaquete shared.queue (publisher SQS)`

- Crea `serverless/lambda/shared/queue/`:
  - `pyproject.toml` con `internal-deps: [shared.observability, shared.aws]`.
  - `__init__.py`, `client.py`, `publisher.py`.
  - `tests/conftest.py` + 4 tests unit (moto SQS).
- + `shared_resolver.py` reconoce el nuevo subpaquete (probable: ya
  detecta por convention, verificar).
- **Verificacion**: `cd serverless/lambda/shared/queue && .venv/bin/pytest
  tests/ -v`.
- **AC**: indirectos (AC-1 y AC-6 lo usan).

---

### Commit 8 — `feat(shared/db): helpers idempotentes insert_*_idempotent`

- Agrega a `serverless/lambda/shared/db/repository.py`:
  - `insert_contact_idempotent(session, payload) -> bool`.
  - `insert_tracking_idempotent(session, payload) -> bool`.
- Mantiene los viejos `insert_contact` y `insert_tracking`.
- + Tests `test_repository_idempotent.py` (4 tests usando Neon de test).
- **Verificacion**: `serverless tests --type=unit --shared=db` (los tests
  de integracion requieren Neon).
- **AC**: AC-10, AC-14.

---

### Commit 9 — `feat(contact_worker): nuevo Lambda worker para SQS contact-form`

- Crea `serverless/lambda/services/contact_worker/` con:
  - `manifest.yaml` con `trigger.type: sqs`, `uses.queues: consumer`.
  - `core/` (handler, controller, service, models, settings, templates).
  - `tests/unit/` (6 tests) + `tests/integration/` (3 tests).
  - `pyproject.toml`, `uv.lock`, `.gitignore`.
- Templates `owner_email.{html,txt}` copiados de `contact_form/core/templates/`.
- **Verificacion**: `serverless tests --type=unit --lambda=contact_worker`;
  `serverless tests --type=integration --lambda=contact_worker` (requiere
  Neon de test + moto SES).
- **AC**: AC-9, AC-10, AC-11.

---

### Commit 10 — `feat(tracking_worker): nuevo Lambda worker para SQS tracking-events`

- Crea `serverless/lambda/services/tracking_worker/` con:
  - `manifest.yaml` con `batch_size: 10`, `ReportBatchItemFailures`.
  - `core/` (handler, controller process_batch, service, models, settings).
  - `tests/unit/` (8 tests) + `tests/integration/` (3 tests).
  - `pyproject.toml`, `uv.lock`, `.gitignore`.
- **Verificacion**: `serverless tests --type=unit --lambda=tracking_worker`;
  `serverless tests --type=integration --lambda=tracking_worker`.
- **AC**: AC-12, AC-13, AC-14.

---

### Commit 11 — `feat(contact_form): refactor a encoder + feature flag ASYNC_MODE`

- Modifica `services/contact_form/core/controllers/contact/create.py`:
  branch async/sync segun `AppConfig.async_mode`.
- Agrega `services/contact_form/core/models/contact.py::ContactAcceptedOutput`.
- Agrega `services/contact_form/core/services/contact_service.py::enqueue_contact_message`.
- Agrega `services/contact_form/core/settings/config.py::AppConfig.async_mode`.
- Modifica `services/contact_form/core/handler.py`: `success_status=202`
  cuando `async_mode`.
- Modifica `services/contact_form/manifest.yaml`: + `uses.queues`,
  + `ASYNC_MODE: 'true'`, bajar memory a 256, timeout a 10.
- Modifica `services/contact_form/pyproject.toml`: + `shared.queue` en
  `internal-deps`.
- + Tests unit nuevos (8 tests del encoder + parametrize de los E2E
  existentes con ASYNC_MODE).
- **Verificacion**: `serverless tests --type=unit --lambda=contact_form`
  con ASYNC_MODE=true Y ASYNC_MODE=false.
- **AC**: AC-1, AC-2, AC-3, AC-4, AC-5.

---

### Commit 12 — `feat(tracking_pixel): refactor a encoder + feature flag ASYNC_MODE`

- Mismo patron que commit 11 aplicado a `tracking_pixel`.
- Modifica `controllers/tracking/track.py`: branch async/sync.
- Modifica `manifest.yaml`: + `uses.queues`, + `ASYNC_MODE`, memory 128,
  timeout 5.
- + `enqueue_tracking_message` en `services/tracking_service.py`.
- + Tests del encoder (7 tests).
- **Verificacion**: `serverless tests --type=unit --lambda=tracking_pixel`
  con ASYNC_MODE=true Y ASYNC_MODE=false.
- **AC**: AC-6, AC-7, AC-8.

---

### Commit 13 — `chore(serverless): deploy contact_worker + tracking_worker en dev`

- **Commit operativo**: `serverless deploy --lambda=contact_worker
  --stage=dev --aws-profile=tfs-dev` y `serverless deploy
  --lambda=tracking_worker --stage=dev --aws-profile=tfs-dev`.
- Verifica que el Event Source Mapping se creo OK:
  `aws lambda list-event-source-mappings --function-name
  portfolio-contact-worker-dev --profile tfs-dev`.
- **Verificacion**: comandos `serverless status --lambda=contact_worker
  --stage=dev` y `serverless status --lambda=tracking_worker --stage=dev`.
- **AC**: AC-15 (verde).

---

### Commit 14 — `chore(serverless): redeploy contact_form + tracking_pixel en dev`

- **Commit operativo**: `serverless deploy --lambda=contact_form
  --stage=dev --aws-profile=tfs-dev` y `serverless deploy
  --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev` para
  inyectar las nuevas env vars (`SSM_CONTACT_FORM_QUEUE_URL_PATH`, etc.)
  y el `ASYNC_MODE`.
- **Verificacion**: `aws lambda get-function-configuration --function-name
  portfolio-contact-form-dev --profile tfs-dev | jq .Environment.Variables`
  muestra `ASYNC_MODE=true` y las SSM_*_URL_PATH.
- **AC**: AC-18.

---

### Commit 15 — `test(specs): smoke test E2E dev — /track + /contact async + verificacion E2E iterativa`

- **Ultimo commit** del plan (seccion 11).
- Bate la suite completa:
  - `pnpm exec biome check .`
  - `serverless tests --type=unit --lambda=contact_worker`
  - `serverless tests --type=unit --lambda=tracking_worker`
  - `serverless tests --type=unit --lambda=contact_form`
  - `serverless tests --type=unit --lambda=tracking_pixel`
  - `serverless tests --type=integration --lambda=contact_worker`
  - `serverless tests --type=integration --lambda=tracking_worker`
  - Smoke test contra `https://api.portfolio.dev.the-full-stack.com`:
    - `curl -X POST .../track` con evento valido -> esperar 202 + verificar
      tracking_event en Neon dev en <30s.
    - `curl -X POST .../contact` con form valido -> esperar 202 + contact_id
      + verificar contact en Neon dev y email recibido en <30s.
- Documenta el bucle de correccion en el body del commit.
- **Elimina la carpeta del plan**: `git rm -r docs/specs/lambdas-async-sqs/`.
- **AC**: TODOS los AC (verificacion E2E).

---

## Resumen de secuencia

```text
1  docs spec                                   (sin codigo)
2  YAMLs SQS + CloudWatch alarms               AC-16, AC-17 (decl)
3  devtools: redrive_policy + visibility_to    AC-16 (provisioner)
4  devtools: kind=cloudwatch-alarm             AC-17 (provisioner)
5  provision-infra dev (operativo)             AC-16, AC-17 (verde)
6  devtools: trigger.type=sqs + uses.queues    AC-15
7  shared/queue (publisher)                    indirecto
8  shared/db: insert_*_idempotent              AC-10, AC-14
                                              ─── desde aqui: paralelizable ───
9  contact_worker (nuevo Lambda)               AC-9, AC-10, AC-11
10 tracking_worker (nuevo Lambda)              AC-12, AC-13, AC-14
11 contact_form refactor encoder + flag        AC-1..AC-5
12 tracking_pixel refactor encoder + flag      AC-6, AC-7, AC-8
                                              ─── reintegracion ───
13 deploy workers dev (operativo)              AC-15 verde
14 redeploy encoders dev (operativo)           AC-18
15 verificacion E2E + smoke + cleanup spec     TODOS los AC
```

## PR

Un solo PR `feature/lambdas-async-sqs -> dev`. Body siguiendo
`.claude/rules/git-workflow.md` (Problema / Solucion / Como probar / TODO).
La seccion "Como probar" reusa la bateria del commit 15.

El PR NO se mergea hasta que toda la bateria del commit 15 pasa en verde
contra dev. Una vez mergeado a dev, deploy automatico vía CI/CD a stage y
prod sigue el flujo habitual `dev -> stage -> main`.

## Rollback

Si despues del deploy en prod algo va mal:

1. **Plan A (rapido)**: cambiar `ASYNC_MODE=false` en el `manifest.yaml`
   del encoder afectado, hacer `serverless deploy --lambda=<X>
   --stage=prod`. <2 min. Vuelve al flujo sync legacy.
2. **Plan B (drastico)**: `git revert <commit-merge>` sobre `main`, push.
   Restaura todo. Los workers nuevos quedan provisionados pero sin
   trafico (las colas estaran vacias).
3. **Plan C (manual)**: si solo el worker falla pero el encolado funciona,
   los mensajes se acumulan en la cola hasta que el bug se fixea + redeploy
   del worker (SQS retiene 4 dias).

## Reglas duras

- **SIEMPRE** cada commit deja el repo verde. Los commits operativos
  (provision-infra, deploy) son los unicos que requieren AWS.
- **SIEMPRE** los AC referenciados en cada commit son verificables; el
  commit no se considera completo si no se ejecuta la verificacion.
- **SIEMPRE** el commit 15 ELIMINA `docs/specs/lambdas-async-sqs/` (la
  spec es efimera).
- **NUNCA** atribucion de IA en los mensajes.
- **NUNCA** se hace `git push` ni se abre PR antes del commit 15 con la
  bateria verde.
- **NUNCA** `--no-verify` para saltar hooks.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Commit que incluye codigo de varios lambdas | Imposible revertir uno solo | 1 commit = 1 cambio coherente |
| `serverless deploy` antes de tests unit verdes | Deploy roto en AWS | Tests primero |
| `--no-verify` en push | Bypassea hooks (lint/types/tests) | Fix el problema, no bypass |
| Smoke test solo "el server responde 202" | No verifica end-to-end | Verifica row en Neon Y email recibido |

---

[< 09](09-idempotencia-orm.md) | [Siguiente: 11 — Worktrees >](11-paralelizacion-worktrees.md)
