# Fase 7 — Documentación (rules + skill + READMEs)

> Actualiza la documentación que toca el nuevo flujo: rules, skill,
> READMEs internos. Asegura que la fuente de verdad documental refleje el
> catálogo YAML, no los diccionarios hardcodeados.

## `.claude/rules/serverless-secrets.md` (modificar)

Cambios principales:

1. Reemplazar la tabla "SSM Parameter Store — inventario completo" por una
   referencia a `serverless/lambda/resources/secrets/*.yaml`:

   > "El inventario actualizado vive en `serverless/lambda/resources/secrets/`
   > (un archivo YAML por entrada). Esta sección documenta el patrón;
   > los valores específicos viven en el catálogo y en SSM."

2. Agregar sección nueva: **"Cómo agregar un secreto nuevo"** con receta:

   ```text
   1. crear serverless/lambda/resources/secrets/<short-name>.yaml
   2. agregar la KEY a docker/env/server/.example
   3. agregar el valor real a docker/env/server/.{dev,stage,prod}
   4. listar el short-name en uses.secrets del manifest.yaml del Lambda consumer
   5. el codigo del Lambda usa: from shared.aws.ssm import get_secret
   6. en deploy: el sync automatico publica a SSM
   ```

3. Reemplazar la sección "Anti-patrones" agregando:

   | Anti-patrón | Por qué | Corrección |
   |-------------|---------|------------|
   | Editar `_SECRETS` / `_SSM_PARAMETERS` en código | Ya no existen | Editar `resources/secrets/*.yaml` |
   | Pasar el valor del secreto en `--value` de aws-cli | Queda en `ps aux` | Usar `_aws_ssm_put_parameter_secure` (tempfile) |
   | Imprimir `env_values` en logs | Leak | Logger con `%s name`, nunca `f'{name}={value}'` |
   | Duplicar el valor en .env y en SSM manualmente | Drift | `serverless sync-secrets --stage=dev` |
   | Olvidar agregar el secreto al `.example` | El dev nuevo no sabe que existe | El `.example` se regenera con `serverless dump-example` (opcional) |

4. Actualizar la sección "AWS auth (deploy)" para reflejar que el sync
   ahora corre antes del `deploy` (mencionar `--skip-sync`).

## `.claude/rules/env-files.md` (modificar)

Agregar excepción documentada:

```markdown
## Excepción: devtools en flujo de deploy automatizado

`devtools/serverless/secrets_sync.py` lee `docker/env/server/.{stage}`
durante `serverless deploy --stage=<env>`. Es la única excepción a la
regla "NUNCA leer un .env":

- El valor pasa del archivo a un dict Python local a SSM, NUNCA a Claude.
- Tests automáticos (`test_no_leaking.py`) verifican que el valor no
  aparece en stdout/stderr.
- El subprocess `aws ssm put-parameter` recibe el valor via
  tempfile (`--value file://...`), no como argumento (que sería visible
  en `ps aux`).

Claude y los subagentes NO ejecutan `serverless deploy` directamente:
sólo el dev humano lo hace. Si Claude necesita revisar el estado del
sync, usa `serverless secrets-status --stage=<env>` (que muestra
hash truncado, no valor).
```

## `.claude/rules/neon-management.md` (modificar)

Sección "Parametros SSM por stage" → actualizar mención de
`/portfolio/neon-url` (legacy, fallback) → ya está deprecado. El catálogo
no incluye el legacy. Documentar la migración del path `/portfolio/neon-url`
(sin stage) a `/portfolio/${stage}/neon-url`.

## `.claude/rules/lambda-controller.md` (modificar)

Sección "Operacion con devtools": mencionar `serverless sync-secrets` y
`serverless secrets-status` como comandos relevantes.

## Skill `aws-ses` (modificar mínimo)

Si menciona el path `/portfolio/ses-from-address` explícito, actualizar
a `from shared.aws.ssm import get_secret; get_secret('ses-from-address')`.

## README del catálogo

Crear `serverless/lambda/resources/secrets/README.md`:

```markdown
# Catalogo de secretos / parametros SSM

Cada archivo `<short-name>.yaml` declara un parametro de SSM Parameter
Store del backend serverless. devtools usa este catalogo como UNICA
fuente de verdad (los diccionarios hardcodeados de antes ya no existen).

## Schema

Ver `docs/specs/serverless-secrets-catalog/02-schema-y-parser.md`
(deprecated despues del merge: el schema queda en codigo + ejemplos en
este README).

## Como agregar un secreto

1. Crear `<short-name>.yaml` siguiendo el ejemplo de
   `turnstile-secret.yaml`.
2. Agregar la KEY a `docker/env/server/.example` (sin valor).
3. Agregar el valor real a `docker/env/server/.dev` (gitignored).
4. Listar `<short-name>` en `uses.secrets` del `manifest.yaml` del
   Lambda consumer.
5. En el codigo del Lambda: `from shared.aws.ssm import get_secret`
   `value = get_secret('<short-name>')`.
6. Deploy: `serverless deploy --stage=dev --lambda=<X>`. El sync se
   ejecuta automaticamente.

## Como rotar un secreto

`serverless rotate-secret --name=<short-name> --stage=dev
--from-env --confirm` (despues de actualizar el `.dev`).

O manualmente:
1. Generar nuevo valor.
2. Actualizar `docker/env/server/.dev` (gitignored).
3. `serverless sync-secrets --stage=dev`.

## Inventario actual

Ver los archivos en este directorio. Comando rapido:

  python -c "from devtools.serverless.secrets_catalog import Catalog;
             [print(s.name) for s in Catalog.load().by_name.values()]"
```

## `docker/env/server/.example` (modificar)

Regenerar a partir del catálogo. Estructura:

```bash
# Auto-generado desde serverless/lambda/resources/secrets/
# Para regenerar: python devtools/run.py serverless dump-example
#
# Portfolio - Variables de categoria SERVER.
# Config del backend serverless. Solo placeholders.
#
# Los SECRETOS reales NO se commitean. Llenar el archivo
# docker/env/server/.{stage} (gitignored) con el valor real, y correr:
#   python devtools/run.py serverless sync-secrets --stage=<env>
# para publicar a SSM (que es lo que la Lambda lee en runtime).

# --- Catalogo: secrets/turnstile-secret.yaml ---
# Cloudflare Turnstile secret key (siteverify) — Portfolio Backend
# SSM: /portfolio/${stage}/turnstile-secret (SecureString)
TURNSTILE_SECRET_KEY=

# --- Catalogo: secrets/turnstile-bypass-secret.yaml ---
# Token de bypass para Playwright E2E (solo dev)
# SSM: /portfolio/dev/turnstile-bypass-secret (SecureString)
TURNSTILE_BYPASS_SECRET=

# --- Catalogo: secrets/neon-url.yaml ---
# Neon PostgreSQL connection string
# SSM: /portfolio/${stage}/neon-url (SecureString)
DB_URL=

# --- Catalogo: secrets/owner-email.yaml ---
# Email destino del form de contacto
# SSM: /portfolio/owner-email (String)
OWNER_EMAIL=

# --- Catalogo: secrets/ses-from-address.yaml ---
# From address verificada en SES
# SSM: /portfolio/ses-from-address (String)
EMAIL_FROM=

# --- Catalogo: secrets/ses-from-name.yaml ---
# Nombre del remitente en emails de SES
# SSM: /portfolio/ses-from-name (String)
EMAIL_FROM_NAME=

# --- Variables NO catalogadas (inline en manifest.yaml de cada Lambda) ---
# Constantes:
EMAIL_BACKEND=ses
AWS_REGION=us-east-1
AWS_SES_REGION=us-east-1
AWS_S3_REGION_NAME=us-east-1
KMS_KEY_ALIAS=alias/portfolio-lambdas
SSM_PATH_PREFIX=/portfolio

# Solo informativos (DB_URL ya contiene todo):
DB_DB=neondb
DB_USER=neondb_owner
DB_PORT=5432
DB_SSLMODE=require
DB_CHANNEL_BINDING=require
DB_HOST=
DB_PASSWORD=

# Bucket S3 por stage (mover a catalogo si decision = TODAS):
AWS_STORAGE_BUCKET_NAME=
```

Comando opcional: `serverless dump-example` regenera el `.example` desde
el catálogo + lista de variables no-catalogadas.

## Archivos afectados

### Modificar

- `.claude/rules/serverless-secrets.md` — reflejar el catálogo
- `.claude/rules/env-files.md` — agregar excepción devtools
- `.claude/rules/neon-management.md` — actualizar path legacy
- `.claude/rules/lambda-controller.md` — mencionar comandos nuevos
- `.claude/skills/aws-ses/SKILL.md` — si menciona paths SSM
- `docker/env/server/.example` — regenerar

### Crear

- `serverless/lambda/resources/secrets/README.md` — guía del catálogo

## Verify-before-done

```bash
# Lectura visual de rules:
ls .claude/rules/serverless-secrets.md .claude/rules/env-files.md \
   .claude/rules/neon-management.md .claude/rules/lambda-controller.md

# Validación con claude -p (según .claude/rules/claude-config-testing.md)
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como agrego un secreto nuevo al backend serverless del portfolio"
# Esperado: num_turns > 1, response menciona resources/secrets/<name>.yaml
```
