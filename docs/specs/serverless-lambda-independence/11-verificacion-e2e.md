# 11 — Verificacion E2E iterativa (fase final)

[< 10 Worktrees](10-paralelizacion-worktrees.md) | [README >](README.md)

Fase de cierre. SIEMPRE la ultima fase y el ultimo commit (C-15). Es el
gate del PR. Consolida — no sustituye — la verificacion incremental de
cada fase.

## Parte A — Refactor de tests

Garantizar que ningun test viejo referencia codigo eliminado o movido:

1. **Barrido de imports a codigo eliminado**:

   ```bash
   # Ningun test debe importar los utils viejos por-lambda:
   rg -l 'from utils\.(base_controller|base_settings|import_controller)' \
     serverless/lambda/services/*/tests/
   # Esperado: cero resultados (ahora es shared.lambda_kit.*)

   # Ningun test debe importar alembic/sqlalchemy desde el core de db/stream:
   rg -l 'import (alembic|sqlalchemy)' \
     serverless/lambda/services/db/tests/ \
     serverless/lambda/services/stream_processor/tests/
   # Esperado: cero (la logica esta en shared/db, sus tests viven alla)
   ```

2. **Tests nuevos en ruta correcta**: los tests de la logica movida
   viven en `shared/db/tests/` y `shared/lambda_kit/tests/`, NO en los
   `tests/` de los Lambdas.

3. **Tests de orquestacion adaptados**: los tests de `db_service` /
   `stream_service` que cubrian la logica movida ahora prueban que el
   `core/services/` ORQUESTA (mockean `shared.db`).

4. **Sin referencia al venv compartido**:

   ```bash
   rg -l 'serverless/\.venv|_PORTFOLIO_SERVERLESS_VENV' \
     devtools/serverless/ devtools/tests/
   # Esperado: cero (todo usa el venv aislado del lambda)
   ```

5. **Sin referencia al workspace uv**:

   ```bash
   rg -l 'tool\.uv\.workspace|tool\.uv\.sources' serverless/
   # Esperado: cero
   ```

## Parte B — Bateria de comandos reales

Ejecutar de punta a punta con el codigo final. Bucle "no parar hasta
que funcione": ejecutar -> si falla, diagnosticar -> corregir ->
re-ejecutar la suite completa -> repetir. NO se marca completa con un
comando fallando, un test rojo o coverage < 80%.

### B.1 — Estructura

```bash
# Workspace uv eliminado (AC-1)
test ! -f serverless/uv.lock && echo "OK: sin uv.lock raiz"
rg 'tool.uv.workspace' serverless/pyproject.toml 2>/dev/null \
  && echo "FAIL" || echo "OK: sin workspace"

# Cada lambda con su uv.lock + .venv ignorado
for l in contact_form db stream_processor tracking_pixel; do
  test -f serverless/lambda/services/$l/uv.lock && echo "OK: $l uv.lock"
done

# Sin core/utils duplicados (AC-3 estructura)
rg -l 'core/utils/base_controller.py' --files \
  serverless/lambda/services/ 2>/dev/null \
  && echo "FAIL" || echo "OK: utils unificados"
```

### B.2 — Dedup (AC-3..AC-8)

```bash
# Los pyproject de db/stream sin libs de shared
rg 'sqlalchemy|alembic|psycopg' \
  serverless/lambda/services/db/pyproject.toml \
  && echo "FAIL: db duplica" || echo "OK: db sin duplicacion"
rg 'sqlalchemy|psycopg' \
  serverless/lambda/services/stream_processor/pyproject.toml \
  && echo "FAIL" || echo "OK: stream sin duplicacion"

# El core/ sin imports de libs de dominio (AC-5, AC-6)
rg 'import (alembic|sqlalchemy)' \
  serverless/lambda/services/db/core/ \
  && echo "FAIL" || echo "OK: db/core limpio"
rg 'from sqlalchemy' \
  serverless/lambda/services/stream_processor/core/ \
  && echo "FAIL" || echo "OK: stream/core limpio"

# El validador automatico pasa para los 4 lambdas (AC-8)
python devtools/run.py serverless lint-deps
```

### B.3 — Tests (AC-2, AC-11, AC-12)

```bash
# Suite completa: 4 lambdas + shared, con coverage
python devtools/run.py serverless tests --type=coverage
# Esperado: todo verde, coverage per-file >= 80%

# Cada lambda usa SU venv (AC-2) — verificar en el output del comando
# que el python invocado es <lambda>/.venv/bin/python
python devtools/run.py serverless tests --type=unit --lambda=db --verbose
```

### B.4 — Run local sin cambio de comportamiento (AC-13)

```bash
# El lambda db responde igual que antes del refactor
python devtools/run.py serverless run --stage=local --lambda=db \
  --runtime-mode=direct --event=events/current.json
# El lambda stream_processor con un event de Stream
python devtools/run.py serverless run --stage=local \
  --lambda=stream_processor --runtime-mode=direct \
  --event=events/<un-event-de-stream>.json
```

### B.5 — Peso del artefacto (AC-9, AC-10)

```bash
# Build de cada lambda: imprime ambas cifras (zip + descomprimido)
for l in contact_form db stream_processor tracking_pixel; do
  python devtools/run.py serverless deploy --lambda=$l --stage=dev \
    --dry-run --aws-profile=tfs-dev
done
# Esperado: ambas cifras impresas, ningun warning (los 4 estan
# muy por debajo de los limites)
```

### B.6 — Quality gates

```bash
python devtools/run.py serverless lint
python devtools/run.py serverless typecheck
# devtools tambien:
python devtools/run.py serverless tests --type=unit --module=devtools
```

### B.7 — CI

```bash
# El workflow CI sigue verde tras descentralizar el tooling
# (validar con act o esperar el run real del PR)
```

## Regla de cierre

El plan NO se declara completo hasta que:

- [ ] Parte A: los 5 barridos `rg` dan cero resultados.
- [ ] B.1: estructura verificada.
- [ ] B.2: `lint-deps` pasa, sin duplicacion en ningun `pyproject.toml`.
- [ ] B.3: `serverless tests --type=coverage` verde, coverage >= 80%
      per-file en TODO.
- [ ] B.4: `run --stage=local` de `db` y `stream_processor` responde
      igual que antes (comparar con la salida pre-refactor).
- [ ] B.5: build imprime ambas cifras, sin warning.
- [ ] B.6: `lint` + `typecheck` + tests de devtools verdes.
- [ ] B.7: CI verde.

El "Como probar" del PR reutiliza esta bateria.

[< 10 Worktrees](10-paralelizacion-worktrees.md) | [README >](README.md)
