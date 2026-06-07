# CI/CD pipeline del portfolio

> Workflows GitHub Actions del backend serverless y las apps Astro.
> Auth via AWS OIDC (cero secrets de larga vida), deploy automatizado
> en merge a `dev`/`stage`/`main`, migraciones de DB previas a
> redeploy de Lambdas, queue por env, estado de devtools en S3.

## Activacion

Aplica SIEMPRE al editar:

- Cualquier `.github/workflows/*.yml`.
- `devtools/serverless/state.py`, `change_detector.py`, comandos CLI
  asociados.
- Cualquier IAM role / S3 bucket / OIDC provider usado por el deploy.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** `migrate-db` ANTES de `deploy-lambdas`. Si migrate falla,
  abortar. Los Lambdas viejos crashearian referenciando columnas que
  todavia no existen.
- **SIEMPRE** `deploy-lambdas` ANTES de `deploy-apps` cuando el contrato
  del API cambia. (Hoy ambos workflows corren en paralelo en push, pero
  los apps fallan graceful si el API esta caido — el browser reintenta.)
- **SIEMPRE** `concurrency.group=deploy-<area>-${branch}` +
  `cancel-in-progress: false`. Dos pushes seguidos al mismo env se
  encolan; nunca se cancelan.
- **SIEMPRE** AWS auth via OIDC con `aws-actions/configure-aws-credentials@v4`
  + `role-to-assume`. NUNCA IAM access keys en GitHub Secrets.
- **SIEMPRE** los IAM roles del CI son scoped por branch
  (`StringLike: sub: repo:bypabloc/cv:ref:refs/heads/<branch>`).
  Defensa en profundidad contra deploy accidental a prod desde dev.
- **NUNCA** editar manualmente el JSON de state en S3 (rompe la
  idempotencia del provisioner).
- **NUNCA** correr `serverless downgrade` desde el workflow CI. Las
  migrations son forward-only en CI. Para revertir, aplicar una
  migracion nueva que revierta (forward fix).
- **NUNCA** usar `cancel-in-progress: true` en workflows que tocan AWS
  (cancelar mid-deploy deja AWS en estado parcial).
- **SIEMPRE** tras un merge que dispara un workflow de deploy, ESPERAR y
  REVISAR su resultado real antes de declarar el deploy hecho: el
  `conclusion` global Y el de CADA job (`gh run view <id> --json jobs`).
  Un job en `failure` (ej. `Verify <app> dist matches env`) significa que
  el deploy NO esta sano, aunque "se haya disparado". Diagnosticar ESE job.
- **SIEMPRE** despues de un deploy de apps, hacer `curl` a la URL canonica
  real de cada env tocado (no al `.pages.dev`): debe dar 200 + el marcador
  esperado. "El workflow corrio" / "CI verde" NO es evidencia de que el
  site sirve — la evidencia es el HTTP de la URL final (ver
  [verify-before-done.md](verify-before-done.md), "Verificacion de
  despliegue REAL").
- **SIEMPRE** que se provisione un app/subdominio NUEVO, correr
  `cloudflare_setup all --env=<X>` (NO solo `projects`): `domains` attacha
  el custom domain y `dns` crea el registro CNAME. Sin el CNAME el custom
  domain queda en `pending`, el cert ACM no se emite y la URL canonica da
  `Could not resolve host` aunque el `.pages.dev` sirva.
- **NUNCA** atribuir a IA en codigo, commits ni mensajes del workflow.

## Workflows

| Workflow | Trigger | Que hace | Duracion |
|----------|---------|----------|----------|
| `ci.yml` | PRs + push dev/stage/main | Biome check + build apps (artifact dist-all-apps-<sha>) | ~45s |
| `branch-flow-guard.yml` | PRs a main/stage | Valida cadena dev->stage->main | <10s |
| `clean-pr-attribution.yml` | PRs | Limpia atribucion IA | <10s |
| `deploy-backend.yml` | Push dev/stage/main | migrate-db -> detect-changes -> deploy-lambdas (matrix) | 2-5 min |
| `deploy-apps.yml` | Push dev/stage/main + manual | build-apps -> deploy-pages (matrix 6 niches) | 1-3 min |

## Mapeo branch -> env -> recursos

| Branch | Stage | IAM role | Cloudflare Pages projects | URL pattern |
|--------|-------|----------|---------------------------|-------------|
| `dev` | `dev` | `portfolio-deploy-dev` | `portfolio-{niche}-dev` | `{niche}.portfolio.dev.the-full-stack.com` |
| `stage` | `stage` | `portfolio-deploy-stage` | `portfolio-{niche}-stage` | `{niche}.portfolio.stage.the-full-stack.com` |
| `main` | `prod` | `portfolio-deploy-prod` | `portfolio-{niche}` | `{niche}.portfolio.the-full-stack.com` (apex para `generic`) |

## Estado de devtools en S3

- Bucket: `portfolio-devtools-state` (us-east-1, KMS encrypted, versioned).
- Layout: `s3://portfolio-devtools-state/state/<scope>-<stage>.json`.
- Activacion: env vars `DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=portfolio-devtools-state` (declaradas en los
  workflows de deploy).
- Default sin env vars: backend local en `serverless/lambda/.state/`
  (lo usa el laptop del dev).
- Lifecycle: versions noncurrent (>30 dias) se borran automaticamente.

## Detect-changes (deploy-backend)

`devtools/serverless/change_detector.py` decide que lambdas redeployar:

1. `services/<X>/**` cambia -> redeploy `X` (excepto `tests/`, `events/`,
   `build/`, `core/seeds/data/`).
2. `shared/<Y>/**` cambia -> redeploy TODOS los consumers (cierre
   transitivo via `shared_resolver.resolve_lambda_shared`).
3. `shared/tests/**` no dispara redeploy.
4. `db` se excluye del matrix porque ya fue redeployado en `migrate-db`.

Comando CLI: `serverless detect-changes --base=<sha> --head=<sha>`
imprime JSON `{"affected": [...]}`.

## Build env vars del deploy de apps

`deploy-apps.yml -> build-apps` declara `environment: <stage>` para leer
GH Variables del environment activo. Sin eso, las vars caen al default
prod (bug que motivo el plan build-env-vars-per-env).

| Var | dev | stage | prod |
|---|---|---|---|
| `BASE_DOMAIN` | `portfolio.dev.the-full-stack.com` | `portfolio.stage.the-full-stack.com` | `portfolio.the-full-stack.com` |
| `APEX_DOMAIN` | (vacio) | (vacio) | `the-full-stack.com` |
| `BASE_SCHEME` | `https` | `https` | `https` |
| `PUBLIC_API_ENDPOINT` | `https://api.portfolio.dev...` | `...stage...` | `...prod...` |
| `PUBLIC_TURNSTILE_SITEKEY` | sitekey dev | sitekey stage | sitekey prod |

**SIEMPRE** el build de `deploy-apps.yml` declara `environment: <stage>`
para leer `vars.*` correctas. Sin eso, las vars son `''` y los guards
de `TrackingPixel.astro` fallan el build (defensa en profundidad).

Las vars se publican con
`python devtools/run.py sync_secrets --env=<X> --category=client`
desde `docker/env/client/.{env}`. Ver
[secrets-strategy.md](secrets-strategy.md) (umbrella) o
[client-env-sync.md](client-env-sync.md) (detalle por categoria).

## Quitar redundancias con pre-push

El pre-push hook local (`.git-hooks/pre-push`) corre la bateria
completa: lint + typecheck + unit + coverage + build + E2E. CI es la
red de seguridad para casos donde el hook se bypassea o un colaborador
no lo tiene setup.

`ci.yml` SOLO corre lint + build (subset que detecta deploys rotos).
No corre typecheck/unit/coverage — ya pasaron en local. astro check
no corre porque duplica el parsing del grafo con `astro build`.

## Adopcion idempotente de recursos (provision-infra)

`serverless provision-infra --stage=<X>` es **idempotente y ADOPTA**
recursos preexistentes: para cada tabla DynamoDB / bucket S3 / REST API
consulta `describe-*`/`get-*` por **nombre fisico** y si ya existe NO la
recrea (solo lee sus ARNs). Esto permite migrar un backend gestionado por
otra herramienta (un stack CloudFormation legacy) a devtools sin perder
datos ni cambiar el endpoint:

- **SIEMPRE** la REST API se matchea por `Name` (`portfolio-api-${stage}`),
  no por logical-id de CloudFormation. Si el `Name` coincide, devtools
  reutiliza el **mismo `restApiId`** -> el custom domain NO se re-apunta,
  el endpoint productivo NO cambia.
- **SIEMPRE** tras `provision-infra` de un env productivo, verificar que el
  `restApiId` NO cambio (gate duro):

  ```bash
  aws ssm get-parameter --name /portfolio/${stage}/api_gateway/portfolio-api/id \
    --region us-east-1 --query 'Parameter.Value' --output text
  aws apigateway get-base-path-mappings \
    --domain-name api.portfolio.${stage}.the-full-stack.com --region us-east-1 \
    --query 'items[0].restApiId' --output text
  # Ambos deben coincidir con el ID previo. Si difieren -> ROLLBACK.
  ```

- **SIEMPRE** al adoptar un env cuya Lambda `db` es vieja (conoce menos
  migraciones que el repo), re-deployar `db` ANTES de `migrate` (la version
  vendorizada de Alembic viaja en el zip del Lambda).
- **NUNCA** `aws cloudformation delete-stack` sobre un stack legacy cuyos
  recursos tienen `DeletionPolicy: Delete` (default SAM) y son compartidos
  (REST API, tablas con datos): destruiria la API/tablas que devtools ya
  adopto. Si no se puede editar el template para poner `Retain` (no esta en
  el repo), dejar el stack **INERTE** (vivo, sin gestion; sus Lambdas ya
  reemplazadas in-place; costo idle ~$0). Borrar a mano solo los huerfanos
  SIN datos (colas SQS vacias, layers, roles de funciones eliminadas).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| IAM access keys en GitHub Secrets | Larga vida, no rotables, leak risk | OIDC con roles federados |
| `delete-stack` de un stack legacy con `DeletionPolicy: Delete` sobre recursos compartidos | Destruye la REST API / tablas que devtools adopto -> outage + perdida de datos | Stack inerte; borrar a mano solo huerfanos sin datos |
| Migrar la DB con la Lambda `db` vieja en el env | Su Alembic vendorizado no conoce las migraciones nuevas | Re-deploy `db` ANTES de `migrate` |
| `cancel-in-progress: true` en deploy | Cancela mid-deploy, AWS queda parcial | `cancel-in-progress: false` |
| Editar el state JSON a mano (local o S3) | Rompe idempotencia del provisioner | Recrear el recurso (provisioner detecta drift) |
| `migrate-db` en paralelo con `deploy-lambdas` | Lambdas pueden referenciar columnas inexistentes | Sequencial obligatorio |
| Apps deploy SIN backend deploy en el mismo PR | Frontend roto si el API cambio shape | Mergear primero el backend, luego el frontend |
| Path-detection para apps | Apps son baratas, consistencia importa | Apps SIEMPRE rebuild + deploy |
| Usar el rol `portfolio-deploy-prod` desde una rama que no sea `main` | El sub del OIDC no matchea, falla con AccessDenied | Lanzar el workflow desde la rama correcta |
| Repetir las credenciales AWS en cada job | Multiplica el tiempo de assumeRole | Reutilizar el step `configure-aws-credentials` por job |
| Declarar el deploy "listo" tras `gh pr merge` sin mirar el workflow | El workflow puede fallar (un job `Verify * dist` rojo) y el site no servir | Revisar `conclusion` global + de cada job; curl a la URL real |
| Provisionar un app nuevo con `cloudflare_setup projects` solamente | Sin `domains`+`dns` el custom domain queda `pending` y no resuelve | `cloudflare_setup all --env=<X>` (projects -> domains -> dns -> status) |
| Asumir el `.pages.dev` con prefijo `portfolio-` | El naming real del project/subdomain es `<niche>-<env>` (ej. `admin-dev`, subdomain `admin-dev-exl.pages.dev`) | Consultar el project real en la API antes de curl |

## Referencias cruzadas

- `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md` — runbook completo
  del setup AWS (OIDC provider + 3 IAM roles + S3 bucket).
- `.claude/docs/ci-cd-pipeline/troubleshooting.md` — errores comunes.
- Skill `ci-cd-pipeline` — guia rapida invocable.
- `devtools/serverless/state.py` — backend de estado.
- `devtools/serverless/change_detector.py` — detector de lambdas.
- `.claude/rules/git-workflow.md` — flujo `dev -> stage -> main`.
- `.claude/rules/neon-management.md` — migrations Alembic via la
  Lambda `db`.
