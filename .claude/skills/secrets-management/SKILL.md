---
name: secrets-management
description: >
  Unified secrets management reference for this portfolio. Covers the 3
  categories: client (docker/env/client -> GitHub Environment Variables,
  public PUBLIC_* + URL builders), server (docker/env/server -> AWS SSM
  Parameter Store us-east-1 with SecureString + KMS alias/portfolio-lambdas,
  real secrets like Turnstile secret key, Neon URL, owner email), and
  dev-cli (docker/env/dev-cli -> LOCAL-ONLY, personal IAM keys + API
  tokens that devtools uses to deploy from the developer laptop, NOT
  synced anywhere because CI uses OIDC). The unified command is
  `python devtools/run.py sync_secrets --env=<dev|prod>
  [--category=all|client|server|dev-cli] [--dry-run] [--keys=A,B]
  [--create-env] [--aws-profile=tfs-dev]`. Hermetic: NO value of any
  secret appears in stdout, stderr, or error messages — only SHA256
  truncated hashes (8 chars) for diagnostic. Actions: SKIP (match),
  PUSH (update), CREATE (new), MISSING (empty in local), LOCAL-ONLY
  (dev-cli only), ERROR. ALWAYS invoke this skill BEFORE answering ANY
  question about: rotating secrets, syncing env vars, adding a new
  environment variable, where a secret lives (GitHub Variables vs AWS
  SSM vs local), what dev-cli is and why it's not synced, PUBLIC_* vs
  Secret distinction, the Turnstile sitekey/secret rotation flow, AWS
  SSM Parameter Store paths in /portfolio/*, KMS encryption of secrets,
  GitHub Environment Variables vs Secrets for this project, the
  sync_secrets command, devtools/sync_secrets/ module, IAM keys for
  the dev IAM user vs OIDC for CI, secrets_sync_to_ssm function from
  serverless module. NEVER answer secrets management questions from
  training data alone — this portfolio has a consolidated 2026
  strategy with 3 distinct categories that override generic advice.
  Use when the user says "secrets", "secretos", "rotar secret", "rotar
  turnstile", "sincronizar secretos", "sync secrets", "sync_secrets",
  "github_sync", "client env", "server env", "dev-cli env", "donde va
  este secret", "where does this secret go", "agregar variable nueva",
  "add env var", "github environment variables", "gh variables", "gh
  secrets", "aws ssm", "ssm parameter store", "kms alias/portfolio-lambdas",
  "iam dev user", "aws sso login", "tfs-dev profile", "docker/env/",
  "rotar credenciales", "rotate credentials", "rotar api token",
  "secretos del client", "secretos del server", "credenciales del
  dev-cli", "validar configuracion local", "audit secrets", "drift
  detection secrets", "oidc github actions aws", "neon api key", "cloudflare
  api token devtools", "iam access key local".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "categoria (opcional): client | server | dev-cli | all"
---

# Secrets Management

Esta skill carga la rule umbrella y rutea a las hijas segun la pregunta.

## Cargar siempre

Leer estos 4 archivos al activar la skill (en orden):

1. `.claude/rules/secrets-strategy.md` — umbrella (las 3 categorias + comando unificado)
2. `.claude/rules/env-files.md` — politica de NO leer `.env`
3. `devtools/sync_secrets/README.md` — referencia tecnica del comando

## Cargar segun la pregunta

Si la pregunta es sobre:

- **client / GH Variables / PUBLIC_* / Turnstile sitekey publica / URL builders / dropdown / build env vars de Astro** → leer `.claude/rules/client-env-sync.md`
- **server / SSM / KMS / Turnstile secret / Neon URL / owner-email / SES / contact_form lambda secrets** → leer `.claude/rules/serverless-secrets.md`
- **dev-cli / IAM keys / aws sso / CF API token / Neon API key / `tfs-dev` profile / OIDC en CI** → la info esta en `secrets-strategy.md` (no hay rule hija dedicada, dev-cli es local-only)

## Comando canonico

```bash
# Sincronizar todas las categorias
python devtools/run.py sync_secrets --env=dev --aws-profile=tfs-dev

# Categoria especifica
python devtools/run.py sync_secrets --env=dev --category=client
python devtools/run.py sync_secrets --env=dev --category=server --aws-profile=tfs-dev
python devtools/run.py sync_secrets --env=dev --category=dev-cli

# Dry-run + rotacion puntual
python devtools/run.py sync_secrets --env=prod --keys=PUBLIC_TURNSTILE_SITEKEY \
  --category=client --dry-run
```

## Decision rapida: ¿donde va una key nueva?

| ¿La consume? | ¿Es publica? | Categoria | Destino |
|---|---|---|---|
| Browser (bundle Astro) | si (PUBLIC_*) | client | GH Variables |
| Lambda runtime | NO | server | SSM SecureString + KMS |
| Lambda runtime | si | server | SSM String |
| devtools local | NO (personal) | dev-cli | local-only |

## Output esperado

Acciones que reporta el comando: `SKIP / PUSH / CREATE / MISSING /
LOCAL-ONLY / ERROR`. NUNCA el valor del secreto en stdout — solo hashes
SHA256 truncados a 8 chars para diagnostico.

## NUNCA hacer

- `gh variable set` o `aws ssm put-parameter` a mano (usar `sync_secrets`)
- Marcar PUBLIC_* como GH Secret (van como Variables)
- Sincronizar dev-cli a remoto (CI usa OIDC, son creds del dev)
- Leer el `.env` completo con Read tool, `cat`, o `source` (ver
  `.claude/rules/env-files.md` — extraer con `grep -m1 ^KEY=` puntual)
- Hardcodear sitekey/endpoint en workflows o codigo de apps
