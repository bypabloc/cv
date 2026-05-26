# Commits

> 10 commits incrementales. Cada uno deja el repo verde (lint + typecheck +
> tests del scope) y trae verificacion explicita. El primer commit es la
> carpeta del plan; el ultimo es la verificacion E2E e incluye el `git rm
> -r docs/specs/contact-form-latency-optim/`.

Rama de trabajo: `feature/contact-form-latency-optim` (desde `dev`).

## Secuencia

### Commit 1 — `docs(specs): plan contact-form-latency-optim`

- Crea `docs/specs/contact-form-latency-optim/` con los 7 archivos del plan.
- Verifica: `ls docs/specs/contact-form-latency-optim/ | wc -l == 7`.
- No toca codigo. Permite que el plan quede commiteado antes de empezar.

### Commit 2 — `test(shared/lambda_kit): tests TDD snap_start_warmup (Red)`

- Crea `serverless/lambda/shared/tests/unit/shared/lambda_kit/test_snap_start_warmup.py`
  con los 4 tests del plan (Red phase: fallan porque el modulo aun no existe).
- Verifica: `serverless tests --type=unit --shared` muestra los 4 tests
  failing con `ModuleNotFoundError: shared.lambda_kit.snap_start_warmup`.

### Commit 3 — `feat(shared/lambda_kit): snap_start_warmup hook generico (Green)`

- Crea `serverless/lambda/shared/lambda_kit/snap_start_warmup.py` con la
  implementacion completa del modulo.
- Actualiza `serverless/lambda/shared/lambda_kit/__init__.py` si re-export
  hace falta.
- Verifica: `serverless tests --type=unit --shared` pasa los 4 tests del
  modulo + cero regresion del resto.

### Commit 4 — `test(shared/rate_limit): tests TDD check paralelo (Red)`

- Crea `serverless/lambda/shared/tests/unit/shared/rate_limit/test_check_parallel.py`
  con los 4 tests (Red phase: 3 pasan con el codigo secuencial actual, 1
  falla porque mide max(N) en vez de sum(N)).
- Verifica: el test de paralelizacion (`test_check_or_raise_parallel_total_under_max_when_all_slow`)
  FALLA con un valor cercano a 400ms (sum de 4×100ms con overhead).

### Commit 5 — `refactor(shared/rate_limit): paraleliza check_or_raise con ThreadPoolExecutor (Green)`

- Refactor de `serverless/lambda/shared/rate_limit/check.py` a la version
  paralela del plan.
- Verifica:
  - `serverless tests --type=unit --shared` pasa los 4 tests nuevos +
    cero regresion en los tests existentes de rate_limit.
  - `serverless tests --type=coverage --shared` -> check.py >= 80%.

### Commit 6 — `test(contact_form): test wired warmup hook (Red)`

- Crea `serverless/lambda/services/contact_form/tests/unit/test_handler_warmup_wired.py`
  con el test del plan (Red: falla porque el handler aun no llama register_warmup).
- Verifica: `serverless tests --type=unit --lambda=contact_form` muestra
  el test failing con `mock_warmup.assert_called_once_with(...)`.

### Commit 7 — `feat(contact_form): wire snap_start_warmup hook (Green)`

- Modifica `serverless/lambda/services/contact_form/core/handler.py` —
  agrega el import y el `register_warmup(...)` module-scope.
- Modifica `serverless/lambda/services/contact_form/manifest.yaml` —
  documenta `snap_start_warmup: [sqs, dynamodb, ssm]`.
- Verifica:
  - `serverless tests --type=unit --lambda=contact_form` pasa el test
    nuevo + cero regresion.
  - `serverless lint-deps --lambda=contact_form` verde.

### Commit 8 — `chore(serverless): coverage + integration tests verdes`

- Confirma con la suite completa:
  - `serverless tests --type=unit --shared` verde.
  - `serverless tests --type=coverage --shared` >= 80% en
    `shared/rate_limit/check.py` y `shared/lambda_kit/snap_start_warmup.py`.
  - `serverless tests --type=unit --lambda=contact_form` verde.
  - `serverless tests --type=coverage --lambda=contact_form` >= 80% en
    el handler modificado.
- Sin cambios en codigo. Solo el ejecuta-suite + commit cosmetico de
  cierre del refactor.

### Commit 9 — `chore(serverless): tabla metricas baseline pre-deploy`

- Crea `docs/specs/contact-form-latency-optim/baseline-metrics.md` con
  10 mediciones de cold + 10 de warm del estado **actual** de los 3 envs
  (dev/stage/prod), antes del deploy de las optimizaciones.
- Verifica: tabla con valores reales de CloudWatch + percentiles p50/p95.

### Commit 10 — `chore(specs): cierra plan contact-form-latency-optim`

- ULTIMO commit: borra `docs/specs/contact-form-latency-optim/` con
  `git rm -r`.
- Antes de borrar, verificar la bateria de [07-verificacion-e2e.md]
  completa en VERDE en los 3 envs (smoke + tabla metricas post-deploy
  con speedup >= 20% cold y >= 30% warm vs baseline).
- Verifica: `git status` muestra solo la carpeta del plan eliminada.

## PR

UN SOLO PR atomico: `feature/contact-form-latency-optim -> dev`.

Tras merge a dev y deploy verde + smoke con tabla metricas verde, se
promueve `dev -> stage` y `stage -> main` siguiendo el flujo enforced del
proyecto.
