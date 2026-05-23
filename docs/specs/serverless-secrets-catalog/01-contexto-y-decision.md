# 1. Contexto / Problema / Solución / AC

## 1. Contexto

El backend serverless del portfolio gestiona 6 secretos/parámetros que viven
en AWS SSM Parameter Store: `turnstile-secret`, `turnstile-bypass-secret`,
`neon-url` (3 stages), `owner-email`, `ses-from-address`. Hoy el catálogo
de esos parámetros está **hardcodeado** en dos lugares de devtools:

- `devtools/serverless/provisioner.py` líneas 84-105 — diccionario `_SECRETS`
  que mapea nombre corto -> path SSM + env var del Lambda. Lo usa el
  provisioner para generar la IAM policy y las env vars del Lambda.
- `devtools/serverless/secrets.py` líneas 29-54 — diccionario `_SSM_PARAMETERS`
  que documenta el inventario y se usa en `serverless setup-ssm` para validar
  nombres conocidos.

Los dos diccionarios pueden desincronizarse. La regla
`.claude/rules/serverless-secrets.md` exige mantener `_SSM_PARAMETERS`
sincronizado a mano — fricción y fuente de bugs.

Por otro lado, los valores reales viven en `docker/env/server/.{stage}`
(gitignored). Hoy no hay un nexo declarativo entre la KEY del `.env`
(ej. `TURNSTILE_SECRET_KEY`) y el path SSM (ej.
`/portfolio/${stage}/turnstile-secret`). El dev tiene que hacer
`serverless setup-ssm --name=/portfolio/dev/turnstile-secret` ingresando el
valor por stdin, cuando el valor ya está en `.dev`. Friccionante y propenso
a desincronización entre `.env` y SSM.

### Hallazgos de exploración

- Ya existe el patrón `resources/<tipo>/<name>.yaml` para dynamodb (5
  tablas), sqs (1 cola), api_gateway (1 REST API). Los YAML usan esquema
  plano custom de devtools (no CloudFormation) y `publishes_ssm:` para
  declarar qué identificadores publica el recurso a SSM.
- El `manifest.yaml` de cada Lambda declara `secrets: [<short-name>, ...]`.
  El `provisioner.py` lo lee y resuelve cada nombre corto contra `_SECRETS`.
- `docker/env/server/.local`, `.dev`, `.prod` contienen valores reales:
  `DB_PASSWORD=npg_znkc8sIQfbP0`, `DB_URL=postgresql://neondb_owner:npg_...`.
  Están gitignored y el usuario confirma que no fueron filtrados a git
  history.
- La rule `.claude/rules/env-files.md` prohíbe a Claude/subagentes leer
  archivos `.env`. devtools (proceso automatizado de deploy) sí puede
  leerlos siempre que el valor no llegue al contexto de Claude.

## 2. Solución Propuesta

Crear `serverless/lambda/resources/secrets/<short-name>.yaml`, un archivo
YAML por secreto/parámetro siguiendo el patrón de `dynamodb/*.yaml`. Cada
archivo declara:

- `kind: ssm-parameter` (discriminador del tipo de recurso)
- `name: <short-name>` (lo que el `manifest.yaml` de cada Lambda usa)
- `path: /portfolio/${stage}/<short-name>` (interpolado por stage)
- `ssm_type: SecureString | String`
- `source_env_var: <KEY_EN_EL_.ENV>` (KEY que devtools busca en
  `docker/env/server/.{stage}`)
- `target_env_var: <KEY_EN_EL_LAMBDA>` (el env var que la Lambda lee con
  `os.environ`; suele ser `SSM_<X>_PATH`)
- `stages: [dev, stage, prod]` (stages donde existe el parámetro)
- `required: true | false`
- `description: <una línea>`
- Bloques opcionales: `rotation`, `owners`, `consumed_by`, `tags`.

`devtools/serverless/secrets_catalog.py` (módulo nuevo) carga el directorio,
valida el schema y expone `Catalog.get(short_name) -> SecretSpec`. Reemplaza
los dos diccionarios hardcodeados.

`serverless deploy --stage=<env>` (cuando `env != local`):

1. Carga `docker/env/server/.{stage}` solo en memoria (NO imprime valores).
2. Para cada YAML del catálogo, verifica que `source_env_var` exista y no
   esté vacío en el `.env`. Si falta, falla con mensaje claro (sin valor).
3. Publica a SSM con `aws ssm put-parameter`, pasando el valor por
   `--value file://<tmp>` (tempfile con `0600` perms, borrado al finalizar)
   o vía stdin del subprocess — NUNCA como argumento visible en `ps`.
4. Compara hash SHA256 del valor con el de SSM (si existe): si coincide,
   skip; si difiere, `put-parameter`. Idempotente.
5. Continúa con el deploy normal del Lambda.

`serverless deploy --stage=local`:

- No publica a SSM.
- Inyecta directamente las env vars del `.local` al proceso/RIE del Lambda
  (`Variables` del `lambda-runtime` o env del proceso direct).
- El código del Lambda decide: si `SSM_<X>_PATH` está seteado, lee SSM;
  sino, lee la env var con el nombre del `target_env_var` directo.
  Coexisten ambos modos sin acoplar el código al modo de ejecución.

### Decisiones clave

- **Decisión 1**: Un archivo YAML por secreto (NO un YAML que liste todos).
  Razón: alineación con `dynamodb/*.yaml`, permite PR atómicos por secreto,
  permite agregar bloques específicos (`rotation`) sin tocar otros.
- **Decisión 2**: El `.env` queda como fuente del valor. Razón: el usuario
  necesita que los .env queden commiteados (aunque .env reales sigan
  gitignored), el `.example` se regenera desde el catálogo. Migrar a SSM
  como fuente única perdería offline-dev y consolidaría riesgo en AWS.
- **Decisión 3**: Local NO usa SSM. Razón: dev sin AWS, tests sin AWS,
  cero costo CLI, cero latencia.
- **Decisión 4**: deploy sincroniza por defecto. Razón: el flujo común es
  "edito .env, deploy" — un comando manual extra es trampa de uso. Flag
  `--skip-sync` para casos excepcionales.
- **Decisión 5**: Hermetismo estricto, verificado por test. Razón: una
  filtración accidental del valor en logs hace que SSM/KMS sean teatro.
  Tests automáticos en CI lo previenen.

## 3. Criterios de Aceptación (AC)

- **AC-1**: Given un YAML `resources/secrets/turnstile-secret.yaml` válido,
  When `devtools/serverless/secrets_catalog.py:Catalog.load()` se ejecuta,
  Then devuelve un `SecretSpec` con los campos del YAML normalizados.
- **AC-2**: Given un YAML con campos faltantes (`name`, `path`,
  `source_env_var`), When `Catalog.load()` se ejecuta, Then lanza
  `CatalogError` con mensaje que indica qué campo falta y en qué archivo.
- **AC-3**: Given un Lambda con `secrets: [turnstile-secret]` en su
  manifest.yaml, When `provisioner._resolve_secrets()` corre, Then devuelve
  la misma estructura `{path, env, region, arn}` que el `_SECRETS`
  hardcodeado actual (compatibilidad binaria).
- **AC-4**: Given `docker/env/server/.dev` con `TURNSTILE_SECRET_KEY=abc123`
  y un catálogo con `source_env_var: TURNSTILE_SECRET_KEY`, When
  `serverless deploy --stage=dev --lambda=contact_form` corre, Then el
  valor `abc123` queda publicado en `/portfolio/dev/turnstile-secret` y
  el proceso NO imprime `abc123` en stdout, stderr ni logs.
- **AC-5**: Given el mismo escenario donde SSM ya tiene `abc123`, When el
  deploy corre nuevamente, Then NO hace un `put-parameter` redundante (skip
  por hash match).
- **AC-6**: Given un `docker/env/server/.dev` SIN la KEY `DB_URL`, When
  `serverless deploy --stage=dev` corre y el catálogo marca `neon-url`
  como `required: true` con `source_env_var: DB_URL`, Then falla con
  exit code 1 y mensaje "DB_URL ausente en docker/env/server/.dev"
  (sin imprimir ningún valor).
- **AC-7**: Given `serverless deploy --stage=local --lambda=contact_form`,
  When corre, Then NO se hace ninguna llamada a `aws ssm put-parameter` ni
  `aws ssm get-parameter`, y las env vars del Lambda local incluyen
  `TURNSTILE_SECRET_KEY` (target_env_var modo local) leído del `.local`.
- **AC-8**: Given el comando `serverless secrets-status --stage=dev`,
  When corre, Then imprime una tabla con cada entrada del catálogo: nombre,
  estado en `.env` (presente/ausente), estado en SSM (presente/ausente),
  match (yes/no por hash SHA256 truncado a 4 chars), pero NUNCA el valor.
- **AC-9**: Given el comando `serverless setup-ssm --name=turnstile-secret
  --stage=dev`, When corre y el catálogo tiene esa entrada, Then expande
  el nombre corto a `/portfolio/dev/turnstile-secret` automáticamente.
- **AC-10**: Given un test que inyecta `TURNSTILE_SECRET_KEY=NEVER_LOG_ME`
  en `.local` y corre `serverless deploy --stage=dev` (o un sync
  controlado), When termina, Then ningún stdout/stderr/log capturado
  contiene la string `NEVER_LOG_ME`.
- **AC-11**: Given los diccionarios `_SECRETS` y `_SSM_PARAMETERS` antes
  del plan, When el plan completa la migración, Then ambos están eliminados
  del código y todos los consumidores leen del catálogo YAML.
