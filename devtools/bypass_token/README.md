# bypass_token

Keygen + mint del **token de bypass de Turnstile** firmado con Ed25519.
Lado FIRMANTE (devtools) del bypass; el backend
(`shared.crypto.bypass_token`) es el VERIFICADOR.

El bypass permite que los tests E2E (`tests/`, comando `e2e`) y dev local ejerciten los
endpoints protegidos por Turnstile (`contact.create`, `auth.register.start`,
`auth.login.start`) sin un widget real. El firmante tiene la clave PRIVADA
(local-only); el Lambda solo tiene la PUBLICA (SSM) -> un leak del entorno
del Lambda NO permite forjar tokens.

**NUNCA prod**: el bypass solo se acepta en `dev`.

## Comandos

```bash
# Generar un par Ed25519 por env (privada -> dev-cli, publica -> server)
python devtools/run.py bypass_token keygen --envs=dev
python devtools/run.py bypass_token keygen --envs=dev --dry-run

# Firmar un token efimero (TTL 300s) e imprimirlo (para curl)
python devtools/run.py bypass_token mint --env=dev
python devtools/run.py bypass_token mint --env=dev --ttl=120
```

## keygen

Genera un par Ed25519 por env y escribe:

- `TURNSTILE_BYPASS_PRIVATE_KEY` -> `docker/env/dev-cli/.{env}` (LOCAL-ONLY,
  gitignored, NUNCA sincronizada a remoto). La privada NUNCA se imprime.
- `TURNSTILE_BYPASS_PUBLIC_KEY` -> `docker/env/server/.{env}` (se publica a
  SSM con `sync_secrets --category=server` o `serverless setup-ssm`).

Tras `keygen`, publicar la publica a SSM:

```bash
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/dev/turnstile-bypass-public-key --env=dev --aws-profile=tfs-dev
```

## mint

Firma un token efimero y lo imprime (solo el token, para pegar en `curl`):

```bash
TOKEN=$(python devtools/run.py bypass_token mint --env=dev)
curl -X POST https://api.portfolio.dev.the-full-stack.com/contact \
  -H "X-Turnstile-Bypass-Token: $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"contact","action":"create","name":"X","email":"x@example.com","message":"hola hola hola","cf_token":""}'
```

La privada se resuelve de `docker/env/dev-cli/.{env}` (extraida sin volcar
el `.env`, ver `.claude/rules/env-files.md`) o se pasa con `--private-key`.

## Formato del token

`b64url(payload_json).b64url(ed25519_sig)`, payload
`{v:1, iat, exp, jti, stage}`. El verificador del backend valida firma +
expiracion + `stage` que coincide. Es el ESPEJO EXACTO de
`serverless/lambda/shared/crypto/bypass_token.py`; la paridad la ancla el
test `devtools/tests/unit/src/shared/test_bypass_token_matches_backend.py`.
