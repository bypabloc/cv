# 10 — Sección 11: verificación E2E iterativa (gate del PR)

[← 09 worktrees](09-worktrees.md) · [README](README.md)

> Última fase y último commit. Gate del PR. Bucle "no parar hasta que
> funcione".

## Parte A — refactor de tests

```bash
rg -l "bypass_secret|X-Turnstile-Bypass-Secret|TURNSTILE_BYPASS_SECRET|turnstile-bypass-secret" \
  serverless/ devtools/ docker/ .github/ .claude/
# esperado: vacío (AC-11)
```

Tests nuevos en ruta correcta: `shared/tests/unit/shared/crypto/**`;
`contact_form`/`auth` con `test_bypass_rejected_in_prod` [AC-1] +
`test_bypass_accepts_valid_token_in_dev` [AC-2]; `tracking_pixel`/`cv` sin
`bypass_*` [AC-10].

## Parte B — batería de comandos reales

```bash
# 1. Unit + coverage (shared + 4 Lambdas)
python devtools/run.py serverless tests --type=unit --shared
for L in contact_form auth tracking_pixel cv; do
  python devtools/run.py serverless tests --type=unit --lambda=$L
done
python devtools/run.py serverless tests --type=coverage --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=auth

# 2. Deps aisladas (AC-12)
python devtools/run.py serverless lint-deps
python devtools/run.py serverless lint-deps --lambda=tracking_pixel
python devtools/run.py serverless lint-deps --lambda=cv

# 3. Deploy a dev + publicar pública a SSM
python devtools/run.py rotate_secrets turnstile-bypass-key --envs=dev,stage
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/dev/turnstile-bypass-public-key --env=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev

# 4. E2E real contra dev (token firmado local)
python devtools/run.py api_e2e --env=dev
```

## Regla de cierre

- Todos los AC con test verde. Coverage >=80% per-file.
- `lint-deps` verde; `tracking_pixel`/`cv` sin `cryptography`.
- `rg` de referencias viejas: vacío.
- E2E real dev: `flow_auth` + `flow_readonly` verde.
- Recién entonces: `git push` + PR. Último commit incluye
  `git rm -r docs/specs/turnstile-signed-bypass/`.

[← 09 worktrees](09-worktrees.md) · [README](README.md)
