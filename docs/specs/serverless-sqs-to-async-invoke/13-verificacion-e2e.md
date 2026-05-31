# 13 — Verificación E2E iterativa + gate de cold (fase final)

[← 12 worktrees](12-paralelizacion-worktrees.md) · [README](README.md)

> Última fase y último commit. Tres partes: (A) refactor de tests, (B) batería
> de comandos reales, (C) **gate de cold medido en CloudWatch**. Bucle "no
> parar hasta verde". Es el gate del PR.

## Parte A — Refactor de tests

- Ningún test referencia código eliminado (`shared.queue`, `send_to_queue`,
  `ASYNC_MODE`, `stream_processor`, `auth_email_worker`, `contact_worker`).
- Tests nuevos en ruta y convención correctas (incluye cv cache, tracking_writer,
  after_restore hook).
- Barrido global:
  ```bash
  rg -l "shared.queue|send_to_queue|ASYNC_MODE|async_mode|stream_processor" \
    serverless/lambda/ devtools/ --glob '!**/_archive/**'   # esperado: 0
  ```

## Parte B — Batería de comandos reales

```bash
# 1. lint-deps (shared-only imports + dedup)
python devtools/run.py serverless lint-deps

# 2. Unit de cada Lambda tocado + shared
python devtools/run.py serverless tests --type=unit --shared
for L in send_email contact_form tracking_pixel tracking_writer cv auth users db; do
  python devtools/run.py serverless tests --type=unit --lambda=$L
done

# 3. Coverage >=80% per-file (los nuevos/modificados)
python devtools/run.py serverless tests --type=coverage --lambda=send_email
python devtools/run.py serverless tests --type=coverage --lambda=cv

# 4. Deploy a dev
for L in send_email tracking_writer contact_form tracking_pixel cv auth users; do
  python devtools/run.py serverless deploy --lambda=$L --stage=dev --aws-profile=tfs-dev
done

# 5. Destruir lo eliminado (dev): colas SQS, workers borrados, stream_processor
python devtools/run.py serverless destroy --lambda=auth_email_worker --stage=dev --yes --aws-profile=tfs-dev
python devtools/run.py serverless destroy --lambda=contact_worker --stage=dev --yes --aws-profile=tfs-dev
# stream_processor: stage + prod (no existe en dev)

# 6. Seed email-config + templates + invalidar cache cv
python devtools/run.py serverless seed-email-config --stage=dev --aws-profile=tfs-dev

# 7. Smoke funcional: contacto real + email + tracking + auth flows + cv
python devtools/run.py api_e2e --env=dev --aws-profile=tfs-dev
```

## Parte C — Gate de cold (el foco del plan, medido en CloudWatch)

> NO usar el roundtrip httpx de `api_e2e` como número de cold (incluye red
> WSL2→us-east-1). Medir con la REPORT line de CloudWatch.

```bash
# Por Lambda: Restore Duration (SnapStart) + Duration (handler) cold y warm
for fn in cv auth users contact-form tracking-pixel; do
  LG="/aws/lambda/portfolio-$fn-dev"; START=$(( ($(date +%s)-3600)*1000 ))
  aws logs filter-log-events --log-group-name "$LG" --start-time "$START" \
    --filter-pattern 'REPORT' --region us-east-1 --profile tfs-dev \
    --query 'events[].message' --output text \
    | rg -o 'Restore Duration: [0-9.]+ ms|Duration: [0-9.]+ ms|Max Memory Used: [0-9]+ MB'
done
```

Gate (comparar contra el baseline de Fase 0):
- [ ] **cv**: warm < 0.5s (cache hit, antes 7.3s); cold cache-hit ≈ Restore
  (~1.2s) sin wake de Neon.
- [ ] **tracking_pixel**: cold ≈ 3.7s (NO peor; sigue 128 MB, no toca Neon).
- [ ] **contact_form / auth / users**: sin regresión de cold; mejora donde el
  cache/keep-alive aplique.
- [ ] `Restore Duration` presente en los colds de los 5 (SnapStart aplica).
- [ ] **NINGÚN manifest subió de memoria** vs baseline (AC-5).
- [ ] cleanup de versiones SnapStart viejas (opcional) ejecutado.

Si una métrica no cumple: diagnosticar con CloudWatch, corregir, re-medir.
NUNCA cerrar con un cold peor que el baseline o con memoria subida.

## Cierre

- `git rm -r docs/specs/serverless-sqs-to-async-invoke/`
- Commit final (fase 8 del plan = sección 11).
- PR `feature/serverless-sqs-to-async-invoke → dev`. Body: Problema / Solución /
  Cómo probar (reusa esta batería + el gate de cold) / TODO (cleanup versiones
  SnapStart, keep-alive Neon si se decide). Sin atribución de IA.

[← 12 worktrees](12-paralelizacion-worktrees.md) · [README](README.md)
