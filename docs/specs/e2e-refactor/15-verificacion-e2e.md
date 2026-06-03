# 15 — Seccion 11: Verificacion E2E iterativa (fase final)

[<- 14 worktrees](14-paralelizacion-worktrees.md) | [Siguiente: 16 DoD ->](16-definition-of-done.md)

> Fase de cierre. SIEMPRE la ultima fase y el ultimo commit. Tres partes.
> Bucle "no parar hasta que funcione": ejecutar -> si falla, diagnosticar ->
> corregir -> re-ejecutar -> repetir.

## Parte A — Refactor de tests (consistencia)

Verificar que no quedo nada apuntando a lo viejo:

```bash
cd /home/bypabloc/projects/bypabloc/portfolio

# 1. Sin specs TS de Playwright vivos
rg -l "@playwright/test|\.spec\.ts" tests/ 2>/dev/null && echo "FAIL: spec TS vivo" || echo "ok"

# 2. Sin imports de api_e2e en codigo funcional
rg -l "import api_e2e|from api_e2e" --glob '!docs/specs/**' --glob '!**/__pycache__/**' \
  && echo "FAIL" || echo "ok"

# 3. Sin referencias vivas a tests/feature / module=feature
rg -l "tests/feature|module=feature|--type=feature|run_feature" \
  --glob '!docs/specs/**' --glob '!**/__pycache__/**' && echo "revisar" || echo "ok"

# 4. Los nuevos tests existen y se descubren
devtools/.venv/bin/python -m pytest tests/ --collect-only -q | tail -5
```

Resultado esperado: cero specs TS, cero imports vivos de api_e2e, las
referencias a `feature` solo en el codigo que da el mensaje de migracion
(test_runner/flags) o en planes archivados.

## Parte B — Bateria de comandos reales (codigo final)

Bucle hasta verde. NO marcar completa con un comando fallando.

```bash
# --- Estatico (sin SSO) ---
# Lint Python (ruff via devtools)
python devtools/run.py docker lint --module=devtools --env=local   # o ruff directo
# Sintaxis (interprete correcto 3.14)
devtools/.venv/bin/python -m compileall -q devtools/e2e tests/
# Unit del comando + shared
python devtools/run.py test_runner --module=devtools --type=unit   # coverage >=80%
# Collect-only de los 3 modulos
devtools/.venv/bin/python -m pytest tests/api tests/admin tests/app --collect-only -q

# --- Frontend intacto (el refactor no debe romper apps) ---
pnpm run lint
pnpm run typecheck
pnpm run build

# --- E2E reales (requiere SSO + clave bypass) ---
aws sso login --profile tfs-dev
python devtools/run.py e2e --module=api   --env=dev --aws-profile=tfs-dev   # AC-1
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev   # AC-2
python devtools/run.py e2e --module=app   --env=dev --aws-profile=tfs-dev   # AC-3
python devtools/run.py e2e               --env=dev --aws-profile=tfs-dev    # los 3, AC-4
```

Criterio: los 3 modulos exit 0; el resumen de tiempos presente; datos
sinteticos limpiados (Neon + blacklist). Si algun caso FAIL -> diagnosticar,
corregir, re-ejecutar la suite del modulo, repetir.

## Parte C — Verificacion de despliegue REAL

`N/A — este plan NO despliega ni provisiona infra`. El refactor toca tooling
de testing, no el backend ni las apps. Los E2E CORREN contra el despliegue
existente (no lo modifican). La verificacion de que "el sitio sirve" la hace
implicitamente la Parte B (los modulos `admin`/`app` hacen GET 200 reales a
las URLs desplegadas como parte de los tests; `api` hace requests reales al
API Gateway).

> Si en la fase B (container) se cambiara algo del compose que afecte un
> despliegue, reactivar la Parte C. Por defecto: N/A.

## Bucle de correccion

```text
ejecutar bateria (Parte A + B)
  |
  v
todo verde? --no--> diagnosticar el comando rojo
  | si                 |  (sin SSO -> activar; sin clave -> generar;
  v                    |   test flaky -> estabilizar; import roto -> fix)
declarar listo         v
                    corregir -> re-ejecutar la suite -> repetir
```

## Gate de cierre

- `git push` + PR SOLO cuando Parte A + Parte B (estatico + frontend + los 3
  modulos E2E) esten verdes.
- El ultimo commit (commit 10) incluye `git rm -r docs/specs/e2e-refactor/`.
- NUNCA declarar el plan "listo" con un comando fallando, un test rojo o
  coverage < 80% en el codigo nuevo.

[<- 14 worktrees](14-paralelizacion-worktrees.md) | [Siguiente: 16 DoD ->](16-definition-of-done.md)
