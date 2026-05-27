# Sección 11 — Verificación E2E iterativa (fase final)

> Gate de cierre del plan. Es el ÚLTIMO commit. Solo se hace `git push` +
> abrir PR cuando esta batería pasa completa en verde.

## Parte A — Refactor de tests

Antes de la batería, verificar que la migración dejó la suite consistente.

```bash
# 1. Ningun test importa _SECRETS o _SSM_PARAMETERS (ya no existen)
rg -l '_SECRETS|_SSM_PARAMETERS' devtools/ serverless/
# Esperado: cero resultados (excepto los que migraron a Catalog)

# 2. Todos los tests del catalogo y sync existen
ls devtools/tests/serverless/test_secrets_catalog.py \
   devtools/tests/serverless/test_secrets_sync.py \
   devtools/tests/serverless/test_secrets_commands.py \
   devtools/tests/serverless/test_no_leaking.py

# 3. Ningun test viejo referencia provisioner._SECRETS
rg 'provisioner\._SECRETS|provisioner._SECRETS' devtools/tests/
# Esperado: cero
```

## Parte B — Batería de comandos reales

Bucle "no parar hasta que funcione": ejecutar → si falla, diagnosticar →
corregir → re-ejecutar → repetir.

### B.1. Conformance + tests unit

```bash
# Lint Python
ruff check devtools/serverless/ devtools/tests/serverless/

# Tests unit del parser
pytest devtools/tests/serverless/test_secrets_catalog.py -v

# Tests unit del sync (incluye no-leaking)
pytest devtools/tests/serverless/test_secrets_sync.py -v
pytest devtools/tests/serverless/test_no_leaking.py -v

# Tests unit de los comandos
pytest devtools/tests/serverless/test_secrets_commands.py -v

# Tests unit del helper compartido
pytest serverless/lambda/shared/tests/unit/aws/test_secret_resolver.py -v

# Tests unit de los lambdas refactorizados
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=stream_processor
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel

# Coverage >= 80% en archivos modificados
pytest devtools/tests/serverless/ \
  --cov=devtools/serverless/secrets_catalog \
  --cov=devtools/serverless/secrets_sync \
  --cov=devtools/serverless/secrets_commands \
  --cov-fail-under=80
```

### B.2. Validación del catálogo cargado

```bash
python -c "
from devtools.serverless.secrets_catalog import Catalog
c = Catalog.load()
assert len(c.by_name) == 6, f'expected 6 secrets, got {len(c.by_name)}'
expected = {'turnstile-secret', 'turnstile-bypass-secret', 'neon-url',
            'owner-email', 'ses-from-address', 'ses-from-name'}
assert set(c.by_name) == expected, f'mismatch: {set(c.by_name)} vs {expected}'
# turnstile-bypass-secret solo en dev
assert c.get('turnstile-bypass-secret').stages == frozenset({'dev'})
# neon-url en los 3 stages
assert c.get('neon-url').stages == frozenset({'dev', 'stage', 'prod'})
# owner-email es String, sin \${stage}
oe = c.get('owner-email')
assert oe.ssm_type == 'String'
assert '\${stage}' not in oe.path_template
print('OK catalogo coherente')
"
```

### B.3. Dry-run del sync

```bash
python devtools/run.py serverless sync-secrets --stage=dev --dry-run \
  --aws-profile=tfs-dev
# Esperado:
#   - Lista los 6 secretos
#   - Cada uno con estado [SKIP|PUSH|MISSING]
#   - Sin un solo valor en stdout
#   - Exit code 0 si todos los required estan en .env, 1 si falta alguno
```

### B.4. Sync real contra AWS dev (idempotente)

```bash
# Primera ejecución (puede tener PUSH si algo cambió)
python devtools/run.py serverless sync-secrets --stage=dev \
  --aws-profile=tfs-dev

# Segunda ejecución INMEDIATA (debe ser todo SKIP)
python devtools/run.py serverless sync-secrets --stage=dev \
  --aws-profile=tfs-dev | grep PUSH
# Esperado: cero PUSH (idempotencia)
```

### B.5. Status

```bash
python devtools/run.py serverless secrets-status --stage=dev \
  --aws-profile=tfs-dev
# Esperado: tabla con 6 filas, todas con Match=yes (despues del sync)
```

### B.6. Deploy de un lambda completo a dev

```bash
python devtools/run.py serverless deploy --stage=dev \
  --lambda=contact_form --aws-profile=tfs-dev

# Verificar que la Lambda funciona
python devtools/run.py serverless run --stage=dev --lambda=contact_form \
  --event=events/sample-valid.json --aws-profile=tfs-dev
# Esperado: 200 OK, email enviado (verificar en SES + bandeja)
```

### B.7. Local mode (sin AWS)

```bash
# Desconectar credenciales para garantizar que no toca AWS
AWS_ACCESS_KEY_ID="" AWS_SECRET_ACCESS_KEY="" AWS_PROFILE="" \
python devtools/run.py serverless run --stage=local \
  --lambda=contact_form --event=events/sample-valid.json

# Esperado:
#   - La lambda corre
#   - Lee TURNSTILE_SECRET_KEY de docker/env/server/.local
#   - No hace ninguna llamada a boto3.ssm
#   - Si tiene Turnstile bypass token, el form valida
#   - 200 OK
```

### B.8. Hermetismo en deploy real

```bash
# Setear un valor canary en .dev temporal
CANARY="CANARY_PROD_e2e_$(date +%s)"
echo "EMAIL_FROM_NAME=$CANARY" >> docker/env/server/.dev

# Correr el sync y capturar TODO el output
python devtools/run.py serverless sync-secrets --stage=dev \
  --aws-profile=tfs-dev 2>&1 | tee /tmp/sync-output.log

# Verificar que el canary NO aparece
if grep -q "$CANARY" /tmp/sync-output.log; then
  echo "FAIL: canary leaked to stdout/stderr"
  exit 1
fi

# Verificar ps aux durante el sync
# (correr en otra terminal mientras se ejecuta):
ps auxww | grep "$CANARY" | grep -v grep
# Esperado: cero resultados

# Limpieza: restaurar .dev original
git checkout -- docker/env/server/.dev
```

### B.9. setup-ssm con nombre corto

```bash
echo "test-value-$(date +%s)" | python devtools/run.py serverless setup-ssm \
  --name=turnstile-secret --stage=dev --aws-profile=tfs-dev
# Esperado:
#   - Expande automaticamente a /portfolio/dev/turnstile-secret
#   - Lee el valor de stdin (no del .env)
#   - Publica con SecureString + KMS
#   - Exit 0
```

### B.10. validate-catalog

```bash
python devtools/run.py serverless validate-catalog
# Esperado: "OK 6 secretos validos"

# Test negativo: romper un YAML temporal y verificar fail
cp serverless/lambda/resources/secrets/turnstile-secret.yaml /tmp/backup.yaml
echo "INVALID YAML CONTENT" > serverless/lambda/resources/secrets/turnstile-secret.yaml
python devtools/run.py serverless validate-catalog || echo "OK fallo esperado"
# Restaurar
cp /tmp/backup.yaml serverless/lambda/resources/secrets/turnstile-secret.yaml
```

### B.11. Branch flow (rule)

Antes de push:

```bash
# Verificar rama actual
git branch --show-current
# Esperado: feature/serverless-secrets-catalog (no dev/stage/main)

# Conformance global
ruff check devtools/
pnpm exec biome check .

# Build estatico del frontend (no se rompió nada)
pnpm run build

# Eliminacion de docs/specs/
git rm -r docs/specs/serverless-secrets-catalog/
git add -A
git commit -m "test(serverless): verificacion E2E iterativa del catalogo de secretos

- Bateria completa de comandos pasa en verde (sync, status, deploy, run)
- Tests no-leaking verifican que ningun valor del .env aparece en stdout/stderr/ps
- Catalogo de 6 secretos validado, parser idempotente, deploy idempotente
- Local mode funciona sin AWS
- Elimina docs/specs/serverless-secrets-catalog/ (artefacto efimero del plan)
"
```

## Bucle de corrección

Si CUALQUIER comando falla, NO avanzar. Diagnosticar la causa:

1. Lint rojo → corregir el archivo, re-correr `ruff check`.
2. Test rojo → debug, fix, re-correr la suite.
3. Sync falla con "DB_URL ausente" → verificar `.dev`, no avanzar hasta
   que `secrets-status` muestre todo OK.
4. Deploy falla → revisar `serverless/lambda/.state/<scope>-dev.json`,
   limpiar si está corrupto.
5. `ps aux` muestra el canary → grave: refactorizar el subprocess para
   usar tempfile, agregar test de regression, re-correr B.8.

Volver a ejecutar la batería desde B.1 después de cualquier fix. NO se
saltea ningún paso. NO se reporta "listo" sin que TODOS los comandos
hayan pasado en una sola corrida desde B.1 hasta B.11.

## Cierre

Cuando la batería completa pasa:

1. `git push origin feature/serverless-secrets-catalog`
2. `gh pr create --base dev --head feature/serverless-secrets-catalog --title "..." --body "..."` con el template de la sección 9.
3. Esperar CI verde.
4. `gh pr merge --merge --delete-branch`.
5. La carpeta `docs/specs/serverless-secrets-catalog/` ya fue eliminada
   en el commit #15 — confirmar que no quedó residuo:
   `git log dev -- docs/specs/serverless-secrets-catalog/ | head`.

Si la PR está mergeada y `docs/specs/serverless-secrets-catalog/` ya no
existe en `dev`, el plan está cerrado.
