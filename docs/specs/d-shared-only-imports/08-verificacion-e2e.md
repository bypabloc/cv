# Fase Verificacion — E2E iterativa + eliminacion del plan

> Ultima fase y ultimo commit. Dos partes: refactor de tests + bateria
> completa de comandos reales con el codigo final. Bucle "no parar hasta
> que funcione". El commit incluye `git rm -r docs/specs/d-shared-only-imports/`.

## Parte A — refactor de tests

Tras Fase E + Fase F, revisar:

1. **Mocks en tests de contact_form**: hoy parchean `contact_service._ses_client`.
   Tras la migracion, deben parchear `shared.aws.ses._client` (o `shared.aws.send_email`
   si se mockea al nivel del helper). Buscar:

   ```bash
   rg -l "_ses_client" serverless/lambda/services/contact_form/tests/
   rg -l "shared.aws.send_email" serverless/lambda/services/contact_form/tests/
   ```

   Cada test que mockee SES debe documentar el nuevo punto de mock.

2. **Tests de stream_processor**: si algun test parchea
   `boto3.dynamodb.types.TypeDeserializer`, ajustar a
   `shared.aws.TypeDeserializer`. Mismo principio.

3. **Tests del seeder (db)**: si testean los upserts, los imports de
   sqlalchemy en el test pueden seguir siendo directos (tests/ esta exento
   del check). Documentar la decision en el docstring.

4. **Tests del re-export shared**: confirmar que los tests nuevos de Fase A,
   B, C y D existen y pasan. Mapeo:

   - `shared/tests/unit/shared/core/test_pydantic_reexport.py` (Fase A)
   - `shared/tests/unit/shared/db/test_sqlalchemy_reexport.py` (Fase B)
   - `shared/tests/unit/shared/aws/test_send_email_*` (Fase C, 3 tests)
   - `shared/tests/unit/shared/aws/test_dynamodb_types_reexport.py` (Fase C)
   - `shared/tests/unit/shared/observability/test_metric_unit_reexport.py` (Fase D)

5. **Barrido global** — cero referencias a paths viejos:

   ```bash
   rg -l "from pydantic" serverless/lambda/services/*/core/
   rg -l "from sqlalchemy" serverless/lambda/services/*/core/
   rg -l "import boto3" serverless/lambda/services/*/core/
   rg -l "from boto3" serverless/lambda/services/*/core/
   rg -l "from aws_lambda_powertools" serverless/lambda/services/*/core/
   ```

   Esperado: cero hits en cualquiera. Si hay un hit, corregir y re-correr.

## Parte B — bateria de comandos reales

Ejecutar en orden. Si cualquier paso falla: diagnosticar, corregir,
re-correr la suite desde el principio. NO se marca completa con un
comando fallando.

### B.1 — Sintaxis + compileall

```bash
python -m compileall -q serverless/lambda/shared
python -m compileall -q serverless/lambda/services
python -m compileall -q devtools/serverless
```

### B.2 — Lint-deps global (los 2 checks)

```bash
python devtools/run.py serverless lint-deps
```

Esperado: exit 0. Cero duplicacion D-3. Cero imports prohibidos en `core/`.

### B.3 — Tests unit por lambda

```bash
for lam in cv db contact_form tracking_pixel stream_processor; do
  python devtools/run.py serverless tests --type=unit --lambda=$lam
done
```

Esperado: todas las suites verdes, sin regresiones.

### B.4 — Tests unit del shared

```bash
python devtools/run.py serverless tests --type=unit --shared
```

Esperado: incluye los re-exports nuevos (Fase A, B, C, D).

### B.5 — Tests unit de devtools (lint-deps escaner)

```bash
python devtools/run.py test_runner --module=devtools --type=unit
```

Esperado: los 8 tests del `import_validator` verdes.

### B.6 — Coverage threshold

```bash
python devtools/run.py serverless tests --type=coverage --shared
```

Esperado: coverage per-file >= 80% en archivos modificados (en especial
`shared/aws/ses.py` con la funcion `send_email` nueva, y
`shared/aws/dynamodb_types.py`).

### B.7 — Deploy + run E2E del lambda `db` en dev

```bash
python devtools/run.py serverless deploy --lambda=db --stage=dev \
  --aws-profile=tfs-dev

python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed.json --aws-profile=tfs-dev
```

Esperado: counts identicos al run pre-refactor (1 profile, 9 experiences,
6 projects, 11 certificates, 10 references, 2 awards, 3 education, 2
languages, 354 translations, 99 skills, 26 tech_tags, 36 niche_priorities).
Confirma que `shared.db` re-export funciona en runtime real.

### B.8 — Deploy + run E2E del lambda `cv` en dev (smoke)

```bash
python devtools/run.py serverless deploy --lambda=cv --stage=dev \
  --aws-profile=tfs-dev

python devtools/run.py serverless run --stage=dev --lambda=cv \
  --event=events/get-profile.json --aws-profile=tfs-dev
```

Esperado: respuesta HTTP 200 con `data.profile.<campos>`. Confirma que
los re-exports de Fase A funcionan en runtime.

### B.9 — Validacion de la rule/skill nuevas (Fase G)

```bash
# 5 prompts en espanol, formato del comando en .claude/rules/claude-config-testing.md
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "donde vive pydantic en el backend serverless del portfolio" \
  2>&1 | tail -40
# repetir con los 4 prompts restantes (ver Fase G)
```

Esperado: `num_turns > 1` en los 4 prompts positivos; el negativo no
dispara la rule/skill.

### B.10 — Diff total + working tree limpio

```bash
git status
git diff --stat dev..HEAD
```

Esperado: working tree limpio. `docs/specs/d-shared-only-imports/` ELIMINADA
en este commit. Diff razonable (no deberian aparecer cambios fuera de
`serverless/lambda/`, `devtools/serverless/`, `.claude/`, `CLAUDE.md`).

## Criterios de aceptacion

- **AC-V1**: Given todos los pasos B.1-B.10 ejecutados, When inspecciono
  exit codes, Then todos son 0 (no hay rojo).
- **AC-V2**: Given el grep de imports prohibidos en `core/`, Then la
  salida es vacia.
- **AC-V3**: Given los 5 lambdas, When ejecuto `serverless lint-deps`,
  Then exit 0.
- **AC-V4**: Given el lambda db con seeder migrado a `shared.db`, When
  ejecuto el evento `seed.json` en dev, Then los counts son identicos a
  los del run previo (verificado byte a byte si es necesario).
- **AC-V5**: Given el commit final, When inspecciono `git show --stat`,
  Then contiene `git rm -r docs/specs/d-shared-only-imports/...`.

## Bucle de correccion

Si cualquiera de los 10 pasos falla:

1. Leer el output completo del comando fallido.
2. Identificar la causa (import roto, test que parchea path viejo,
   regresion en seeder, etc.).
3. Corregir el archivo afectado.
4. Re-correr la suite DESDE B.1.
5. NO mergear con un solo paso rojo.

## Commit final (con eliminacion del plan)

```text
test(serverless): verificacion E2E del refactor shared-only imports

- Refactor de tests: mocks de SES apuntan a shared.aws._client (antes
  contact_service._ses_client); mocks de stream apuntan a
  shared.aws.TypeDeserializer
- Barrido global: cero from pydantic / from sqlalchemy / import boto3 /
  from aws_lambda_powertools en services/*/core/
- serverless lint-deps verde (dedup D-3 + imports prohibidos)
- 5 suites unit por lambda verdes; shared verde; devtools verde
- Deploy + seed del lambda db en dev: counts identicos al run previo
- Deploy + cv-get en dev: HTTP 200 con perfil esperado
- 5 prompts de validacion claude -p OK (4 positivos invocan la rule;
  1 negativo no dispara)
- Elimina docs/specs/d-shared-only-imports/ (plan efimero; rule + skill
  + docs en .claude/ son los artefactos permanentes)
```
