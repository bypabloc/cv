# Verificacion E2E iterativa + tabla metricas

> Fase final del plan. SIEMPRE es la ultima fase y el ultimo commit
> (commit 10). El commit 10 incluye `git rm -r docs/specs/contact-form-latency-optim/`
> SOLO si la bateria de abajo pasa completa en VERDE en los 3 envs.

## Parte A — Refactor de tests (barrido global)

Confirmar que ningun test viejo referencia codigo eliminado y que los
tests nuevos viven en la ruta correcta.

```bash
# 1. Cero referencias a get_ip_rule/get_country_rule/get_endpoint_rule
#    SECUENCIALES en codigo viejo (todas deben pasar por check_or_raise).
rg -l 'get_ip_rule|get_country_rule|get_endpoint_rule' serverless/lambda/services/
# Esperado: VACIO. Si aparece, es codigo que no pasa por check_or_raise
# y hay que migrarlo o documentar excepcion.

# 2. Confirmar que los tests nuevos existen en la ruta correcta
test -f serverless/lambda/shared/tests/unit/shared/lambda_kit/test_snap_start_warmup.py
test -f serverless/lambda/shared/tests/unit/shared/rate_limit/test_check_parallel.py
test -f serverless/lambda/services/contact_form/tests/unit/test_handler_warmup_wired.py

# 3. Confirmar que NO hay residuos de la version secuencial vieja en check.py
rg 'ip_rule = get_ip_rule|country_rule = get_country_rule|endpoint_rule = get_endpoint_rule' \
  serverless/lambda/shared/rate_limit/check.py
# Esperado: VACIO si quedaron como futures.
```

## Parte B — Bateria de comandos reales

Bucle "no parar hasta que funcione": ejecutar → si falla, diagnosticar →
corregir → re-ejecutar. NO se marca completa con un comando fallando, un
test rojo o coverage < 80%.

### B.1 — Unit tests + coverage

```bash
# Shared kit (incluye los 8 tests nuevos)
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=coverage --shared

# Lambda contact_form (incluye el test wired)
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=contact_form

# Suite global (los 4 lambdas + shared completo)
python devtools/run.py serverless tests --type=unit
```

**GATE**: TODOS verdes. Coverage >= 80% en cada archivo modificado o nuevo.

### B.2 — Lint + lint-deps

```bash
python devtools/run.py serverless lint-deps --lambda=contact_form
# Esperado: zero issues — no agregamos deps nuevas en pyproject.toml.

# Ruff sobre lo modificado
ruff check serverless/lambda/shared/lambda_kit/snap_start_warmup.py
ruff check serverless/lambda/shared/rate_limit/check.py
ruff check serverless/lambda/services/contact_form/core/handler.py
```

**GATE**: cero issues.

### B.3 — Deploy a dev + smoke

```bash
# Deploy
python devtools/run.py serverless deploy --lambda=contact_form \
  --stage=dev --aws-profile=tfs-dev

# Smoke con bypass Turnstile (dev tiene SSM_TURNSTILE_BYPASS_SECRET_PATH)
BYPASS=$(aws ssm get-parameter --name /portfolio/dev/turnstile-bypass-secret \
  --with-decryption --profile tfs-dev --query 'Parameter.Value' --output text)

curl -sS -o /tmp/resp.json -w 'HTTP %{http_code} | time %{time_total}s\n' \
  -X POST 'https://api.portfolio.dev.the-full-stack.com/contact' \
  -H 'Content-Type: application/json' \
  -H "X-Turnstile-Bypass-Secret: $BYPASS" \
  -H 'Origin: https://portfolio.dev.the-full-stack.com' \
  -d '{"operation":"contact","action":"create","name":"Latency Optim Smoke","email":"smoke@example.com","message":"smoke del plan contact-form-latency-optim"}'

unset BYPASS

# Esperado: HTTP 202 + body {contact_id, created_at, accepted: true}
```

**Verificar logs**: en CloudWatch del cold start del primer smoke debe
aparecer:

```
[snap_start_warmup] sqs: ok (XXXms)
[snap_start_warmup] dynamodb: ok (XXXms)
[snap_start_warmup] ssm: ok (XXXms)
```

Si NO aparecen, el hook no se llamo (validar import en handler.py).
Si aparecen WARNINGS, validar los permisos IAM del rol del lambda.

### B.4 — Captura de metricas post-deploy

Tras smoke OK en dev, capturar 10 mediciones (5 cold + 5 warm) en
CloudWatch para popularse en la tabla metrics (ver mas abajo).

```bash
# Ejecutar 10 smokes espaciados 30 seg para garantizar mix cold + warm
for i in $(seq 1 10); do
  BYPASS=$(aws ssm get-parameter --name /portfolio/dev/turnstile-bypass-secret \
    --with-decryption --profile tfs-dev --query 'Parameter.Value' --output text)
  curl -sS -w '%{http_code}|%{time_total}s\n' \
    -X POST 'https://api.portfolio.dev.the-full-stack.com/contact' \
    -H 'Content-Type: application/json' \
    -H "X-Turnstile-Bypass-Secret: $BYPASS" \
    -H 'Origin: https://portfolio.dev.the-full-stack.com' \
    -d "{\"operation\":\"contact\",\"action\":\"create\",\"name\":\"Smoke $i\",\"email\":\"smoke$i@example.com\",\"message\":\"medicion $i del plan latency-optim\"}" \
    -o /dev/null
  unset BYPASS
  sleep 30
done

# Despues, capturar Restore Duration + Duration + Init Duration via:
aws logs filter-log-events \
  --log-group-name /aws/lambda/portfolio-contact-form-dev \
  --start-time $(($(date +%s) * 1000 - 600000)) \
  --filter-pattern 'REPORT' \
  --profile tfs-dev \
  --query 'events[*].message' --output text \
  | grep -oE 'Duration: [0-9.]+|Restore Duration: [0-9.]+|Billed Duration: [0-9]+'
```

### B.5 — Promocion a stage y prod

Una vez verde en dev:

```bash
# PR dev -> stage (sigue el flujo enforced)
gh pr create --base stage --head dev --title 'promote: dev -> stage (contact-form-latency-optim)' --body '...'
gh pr merge <PR_ID> --merge

# Esperar deploy backend stage verde
gh run watch <RUN_ID>

# Repetir smoke + captura metrics en stage (sin bypass — verificar HTTP 403 CAPTCHA_INVALID con timing)

# PR stage -> main
gh pr create --base main --head stage --title 'promote: stage -> main (contact-form-latency-optim)' --body '...'
gh pr merge <PR_ID> --merge

# Esperar deploy backend prod verde
gh run watch <RUN_ID>

# Smoke + captura metrics en prod
```

## Tabla metricas — GATE OBLIGATORIO

El commit 10 (cierre del plan) requiere esta tabla completa con datos
reales. Sin ella, el plan NO se considera completo y la carpeta del plan
NO se borra.

### Baseline (commit 9, pre-deploy)

```markdown
## Baseline (pre-deploy plan latency-optim)

Capturado: YYYY-MM-DD HH:MM UTC

### Cold start (10 mediciones por env)

| Env   | p50 Restore | p50 Duration | p50 Total (R+D) | p95 Total |
|-------|-------------|--------------|-----------------|-----------|
| dev   | XXX ms      | XXXX ms      | XXXX ms         | XXXX ms   |
| stage | XXX ms      | XXXX ms      | XXXX ms         | XXXX ms   |
| prod  | XXX ms      | XXXX ms      | XXXX ms         | XXXX ms   |

### Warm path (10 mediciones, segunda invocacion del mismo microVM)

| Env   | p50 Duration | p95 Duration |
|-------|--------------|--------------|
| dev   | XXX ms       | XXXX ms      |
| stage | XXX ms       | XXXX ms      |
| prod  | XXX ms       | XXXX ms      |
```

### Post-deploy (commit 10, tras los 3 deploys)

```markdown
## Post-deploy plan latency-optim

Capturado: YYYY-MM-DD HH:MM UTC

### Cold start

| Env   | p50 Restore | p50 Duration | p50 Total | speedup vs baseline |
|-------|-------------|--------------|-----------|---------------------|
| dev   | XXX ms      | XXXX ms      | XXXX ms   | -XX% (target: -20%) |
| stage | XXX ms      | XXXX ms      | XXXX ms   | -XX% (target: -20%) |
| prod  | XXX ms      | XXXX ms      | XXXX ms   | -XX% (target: -20%) |

### Warm path

| Env   | p50 Duration | speedup vs baseline |
|-------|--------------|---------------------|
| dev   | XXX ms       | -XX% (target: -30%) |
| stage | XXX ms       | -XX% (target: -30%) |
| prod  | XXX ms       | -XX% (target: -30%) |

### Verificacion de los hooks

| Env   | [snap_start_warmup] sqs | [snap_start_warmup] dynamodb | [snap_start_warmup] ssm |
|-------|--------------------------|------------------------------|--------------------------|
| dev   | ok (XX ms) | ok (XX ms) | ok (XX ms) |
| stage | ok (XX ms) | ok (XX ms) | ok (XX ms) |
| prod  | ok (XX ms) | ok (XX ms) | ok (XX ms) |
```

## Gate de cierre (commit 10)

El commit 10 SOLO se hace si:

- [ ] Bateria B.1 verde (todos los tests + coverage >= 80%).
- [ ] Bateria B.2 verde (lint + lint-deps).
- [ ] Bateria B.3 verde en los 3 envs (HTTP 202 + warmup logs).
- [ ] Tabla post-deploy completa con valores reales.
- [ ] Cold speedup >= 20% en al menos 2 de los 3 envs (acceptable: prod
  puede tener variabilidad por low traffic).
- [ ] Warm speedup >= 30% en al menos 2 de los 3 envs.
- [ ] Cero WARNINGS de `[snap_start_warmup]` en los logs (todos los
  hooks completan OK).

Si CUALQUIERA falla: NO commitear el 10. Diagnosticar + corregir +
re-ejecutar.
