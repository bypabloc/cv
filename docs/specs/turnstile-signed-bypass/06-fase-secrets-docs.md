# 06 — Fase 5: secrets (SSM) + docs + borrado del secreto viejo

[← 05 devtools](05-fase-devtools.md) · [Siguiente: Sección 8 →](07-descomposicion.md)

> Publica la clave pública a SSM, elimina el secreto fijo viejo (catálogo +
> SSM + código), actualiza las rules.

## A — catálogo / SSM

- Reemplazar `resources/secrets/turnstile-bypass-secret.yaml` por
  `turnstile-bypass-public-key.yaml`:
  - Tipo `String` (NO `SecureString` — sin KMS).
  - Paths: `/portfolio/dev/turnstile-bypass-public-key`,
    `/portfolio/stage/turnstile-bypass-public-key`. NO prod.
  - `local_env: TURNSTILE_BYPASS_PUBLIC_KEY`.
- `resources/secrets/README.md`: actualizar la entrada.
- `shared/core/config.py`: `turnstile_bypass_secret` →
  `turnstile_bypass_public_key` (o eliminar si solo se lee vía
  `get_parameter` en el orquestador).

### Publicar + borrar el viejo

```bash
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/dev/turnstile-bypass-public-key --env=dev --aws-profile=tfs-dev
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/stage/turnstile-bypass-public-key --env=stage --aws-profile=tfs-dev
aws ssm delete-parameter --name /portfolio/dev/turnstile-bypass-secret \
  --region us-east-1 --profile tfs-dev
aws ssm delete-parameter --name /portfolio/stage/turnstile-bypass-secret \
  --region us-east-1 --profile tfs-dev
```

## B — borrado en código/env

- Quitar `TURNSTILE_BYPASS_SECRET` de `docker/env/server/.{dev,stage,prod}` y
  `.example`. Agregar `TURNSTILE_BYPASS_PUBLIC_KEY` al `.example`.
- Confirmar (AC-11):

```bash
rg -n "turnstile-bypass-secret|TURNSTILE_BYPASS_SECRET|bypass_secret|X-Turnstile-Bypass-Secret" \
  serverless/ devtools/ docker/env/ .github/ .claude/
# esperado: vacío
```

## C — docs / rules

- `.claude/rules/serverless-secrets.md`: entrada `turnstile-bypass-secret` →
  `turnstile-bypass-public-key` (String, no KMS, dev/stage). Documentar que la
  PRIVADA vive en `dev-cli` local-only.
- `.claude/rules/lambda-shared-imports.md`: fila `cryptography → shared.crypto`.
- `.claude/rules/auth-system.md`: si menciona el bypass, actualizar.
- `.claude/rules/secrets-strategy.md`: nota privada de bypass = `dev-cli`.
- Validar `.claude/*` con `claude -p` (claude-config-testing.md).

## Verificación de la fase

```bash
rg -n "TURNSTILE_BYPASS_SECRET|turnstile-bypass-secret" serverless/ devtools/ docker/ .claude/
python devtools/run.py serverless lint-deps
```

[← 05 devtools](05-fase-devtools.md) · [Siguiente: Sección 8 →](07-descomposicion.md)
