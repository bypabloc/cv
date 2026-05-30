# 11 — Verificación E2E iterativa + medición de cold start (gate del PR)

[← 10 worktrees](10-paralelizacion-worktrees.md) · [README](README.md)

> Última fase y último commit. Bucle "no parar hasta que funcione". El `git
> push` + PR ocurren SÓLO con esta batería completa en verde. NO se fan-outea
> (Bash o 1-2 agentes secuenciales). **NO hay `db_writer`.**

## Parte A — Refactor de tests (barrido global)

Confirmar con `rg -l` (0 resultados, fuera de `_archive/` y de la carpeta del
plan mientras exista):

```bash
rg -l "shared.queue|send_to_queue|QueuePublishError"     serverless/lambda
rg -l "ASYNC_MODE|async_mode"                            serverless/lambda
rg -l "auth_email_worker|contact_worker|tracking_worker" serverless devtools
rg -l "uses.queues|trigger.*sqs|_provision_sqs"          devtools serverless
rg -l "db_writer|db-writer"                              serverless devtools
rg -l "stream_processor|stream-processor" --glob '!**/_archive/**'
```

- Ningún test referencia los 3 workers, `shared.queue`, `ASYNC_MODE` ni
  `db_writer`.
- Los modelos de mensaje SQS (`ContactQueueMessage`/`TrackingQueueMessage`/
  `AuthEmailMessage`) se eliminaron (su lógica de persistencia vive ahora
  inline en los encoders).
- Tests nuevos en ruta/convención correcta (mirror + BDD-style, asserts
  exactos).

## Parte B — Batería de comandos (orden, todo verde)

```bash
python -m compileall -q serverless/lambda                          # 1. sintaxis
python devtools/run.py serverless lint-deps                        # 2. imports + dedup
for L in send_email auth users contact_form tracking_pixel; do     # 3. unit+cov ≥80%
  python devtools/run.py serverless tests --type=coverage --lambda=$L
done
python devtools/run.py serverless tests --type=unit --shared       # 4. portadores nuevos
python devtools/run.py test_runner --module=devtools --type=unit   # 5. devtools
python devtools/run.py serverless tests --type=unit                # 6. suite backend completa
```

## Parte C — Deploy a dev + seed + smoke (`--aws-profile=tfs-dev`)

```bash
# Infra: tabla email-config + bucket S3 (idempotente). NO crea colas SQS.
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev

# Deploy de send_email + seed de templates/config
python devtools/run.py serverless deploy --lambda=send_email --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless seed-email-config --stage=dev --aws-profile=tfs-dev

# Redeploy de los callers migrados
for L in auth users contact_form tracking_pixel; do
  python devtools/run.py serverless deploy --lambda=$L --stage=dev --aws-profile=tfs-dev
done

# Destruir los 3 workers (ya sin código)
for W in auth_email_worker contact_worker tracking_worker; do
  python devtools/run.py serverless destroy --lambda=$W --stage=dev --yes --aws-profile=tfs-dev 2>/dev/null || true
done
```

### Smoke E2E (HTTP real contra dev) — reusar patrón de `api_e2e`

- `POST /contact` válido → **201** con el contacto persistido; verificar en
  Neon que se escribió (AC-1) y que llegó el email al owner (SES /
  `simulator.amazonses.com`) (AC-12).
- `POST /track` válido → **202**; verificar el tracking_event en Neon (AC-2).
- `auth register.start` → llegan magic-link + code (send_email) (AC-10).
- `send_email` con `kind` inexistente (invoke directo) → error sin SES (AC-4).

## Parte D — Medición de cold start (el punto de honestidad del plan)

Con el procedimiento de `.claude/rules/lambda-config.md` (memorias
decrecientes sobre `$LATEST`, sin SnapStart restore = peor caso), medir y
documentar en el comentario de cada manifest:

```bash
# Por cada lambda nuevo/cambiado: send_email, contact_form, tracking_pixel
for mem in 512 256 128; do
  aws lambda update-function-configuration --function-name <fn> \
    --memory-size $mem --region us-east-1 --profile tfs-dev >/dev/null
  aws lambda wait function-updated --function-name <fn> --region us-east-1 --profile tfs-dev
  aws lambda invoke --function-name <fn> --payload fileb://<event>.json \
    --log-type Tail --region us-east-1 --profile tfs-dev ./tmp/out.json \
    --query 'LogResult' --output text | base64 -d \
    | rg 'Init Duration|^REPORT.*Duration|Max Memory'
done
```

- **send_email**: medir el mínimo (Jinja2 + boto3 dynamodb/s3/ses, sin Neon).
  Estimado 256; bajar a 128 sólo si la medición lo permite.
- **tracking_pixel**: CONFIRMAR el bump a 256 (footprint Neon a 128 = OOM).
  Documentar Init/handler/Max Memory reales.
- **contact_form**: confirmar que sigue en 256 sin regresión.
- **Comparar** con las métricas previas (encoder SQS): registrar en el body
  del PR que el cold start es ~neutro (SnapStart) y que `tracking_pixel`
  subió a 256 MB (tradeoff aceptado). Si la medición muestra que el restore
  de `tracking_pixel` se degradó por sqlalchemy y es inaceptable para `/track`:
  evaluar el write path raw psycopg3 (mitigación de [05](05-encoders-refactor.md)).

## Parte E — Cierre

```bash
git rm -r docs/specs/serverless-sqs-to-async-invoke/
```

Definition of Done:
- [ ] AC-1..AC-16 cubiertos por test/smoke que pasa.
- [ ] Coverage ≥80% per-file en archivos nuevos/modificados.
- [ ] `compileall` + `lint-deps` + `test_runner devtools` + suite backend verdes.
- [ ] Deploy dev + seed + smoke OK.
- [ ] memory/timeout MEDIDOS y justificados (incl. tracking_pixel 256).
- [ ] `rg` de SQS/ASYNC_MODE/stream_processor/db_writer → 0 (fuera de `_archive/`).
- [ ] rules/CLAUDE.md actualizadas y validadas con `claude -p`.
- [ ] Sin atribución de IA.

## Gate del PR

`git push` + `gh pr create --base dev` SÓLO con TODA esta batería en verde. Si
algo falla: diagnosticar → corregir → re-ejecutar → repetir. NUNCA push/PR con
un comando fallando, un test rojo o coverage < 80%.

[← 10 worktrees](10-paralelizacion-worktrees.md) · [README](README.md)
