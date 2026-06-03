# 10 — Seccion 6: Tests requeridos

[<- 09 rule/skill](09-fase-rule-skill.md) | [Siguiente: 11 archivos afectados ->](11-archivos-afectados.md)

> El plan tiene DOS niveles de "test": (a) los E2E que se construyen (son el
> producto del plan) y (b) los unit tests del comando `e2e` + el shared
> portado (que validan la maquinaria). Cada test referencia un AC.

## 6.A — Unit tests Python del comando + shared (devtools/.venv, pytest)

Mirror en `devtools/tests/unit/src/`:

- `devtools/tests/unit/src/e2e/test_flags.py` [AC-5, AC-6]
  - WHEN `--module=foo` THEN ValueError con lista de validos.
  - WHEN `--env=prod` THEN ValueError (prod prohibido).
  - WHEN `--module` ausente THEN default = los 3 modulos.
  - WHEN `--samples` no-int THEN coerce o ValueError.
- `devtools/tests/unit/src/e2e/test_describe.py`
  - WHEN `describe()` THEN dict con name='e2e', flags module/env/samples.
- `devtools/tests/unit/src/e2e_shared/test_config.py` [AC-3]
  - WHEN `subdomain('fintech', 'dev')` THEN
    `https://fintech.portfolio.dev.the-full-stack.com`.
  - WHEN `synthetic_email(run, slot)` THEN matchea
    `success+api-e2e-...@simulator.amazonses.com`.
- `devtools/tests/unit/src/e2e_shared/test_reporter.py`
  - (migrado de `api_e2e/test_reporter.py`) tabla de tiempos correcta.
- `devtools/tests/unit/src/e2e_shared/test_runner.py`
  - (migrado de `api_e2e/test_runner.py`) clasificacion PASS/FAIL exacta.
- `devtools/tests/unit/src/e2e_shared/test_totp.py`
  - WHEN code generado THEN == pyotp para el mismo secret/tiempo.
- `devtools/tests/unit/src/e2e_shared/test_secrets_hermetic.py` [AC-9]
  - WHEN se resuelve un secreto THEN su valor NO aparece en stdout/stderr
    (canary string, como el patron de `test_secrets_sync.py`).

Los tests viejos de `api_e2e` (`test_flags`, `test_config`, `test_reporter`,
`test_runner`) se MIGRAN (no se borran sin reemplazo): su logica vale, solo
cambia el import path.

## 6.B — Typecheck / lint Python

- `ruff` sobre `devtools/e2e/` + `tests/` (config de `devtools/ruff.toml`
  para devtools; `tests/` usa la config del arbol). Sin errores.
- `python -m compileall -q devtools/e2e tests/` sin SyntaxError (usar
  `devtools/.venv/bin/python`, NO el `python3` del shell — ver `python.md`).

## 6.C — Tests E2E (el producto del plan)

Son los tests de `tests/{api,admin,app}/`. NO se "mockean": corren contra
desplegado dev. Su verificacion es la bateria de la seccion 11.

- `tests/api/` [AC-1, AC-10, AC-11]: 5 Lambdas, exito + errores.
- `tests/admin/` [AC-2]: flujos browser reales (login/logout/forms/MFA).
- `tests/app/` [AC-3]: 6 apps (smoke/navbar/contact/tracking/screenshots).

Cada test pytest:
- nombre `test_<unidad>_<escenario>`.
- docstring BDD (Given/When/Then) que referencia su AC.
- cuerpo AAA, asserts EXACTOS (status codes, textos, payloads exactos).

## 6.D — Coverage

Los E2E NO tienen threshold de coverage per-file (son tests de integracion
contra un sistema desplegado, no unit). El coverage >=80% per-file aplica al
codigo NUEVO de `devtools/e2e/` y a `tests/shared/` (la maquinaria), medido
por sus unit tests de 6.A. Verificar con:

```bash
python devtools/run.py test_runner --module=devtools --type=unit
# (cubre devtools/e2e + el shared portado via los mirrors de arriba)
```

[<- 09 rule/skill](09-fase-rule-skill.md) | [Siguiente: 11 archivos afectados ->](11-archivos-afectados.md)
