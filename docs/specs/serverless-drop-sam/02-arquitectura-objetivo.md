# 02 — Arquitectura objetivo

> [Anterior: 01](01-contexto-y-decision.md) | [README](README.md) | [Siguiente: 03](03-fase-1-capa-base.md)

## 1. Modulos de `devtools/serverless/` despues de la migracion

```text
devtools/serverless/
├── main.py              [MODIFICAR]  registro de comandos
├── flags.py             [MODIFICAR]  quita flags de SAM, agrega destroy/status
├── help.py              [MODIFICAR]  textos de ayuda
├── resolve.py           [igual]      resuelve --lambda / --path
├── shared_resolver.py   [igual]      cierre de subpaquetes shared/ por AST
├── packaging.py         [MODIFICAR]  build/ -> build.zip
├── vendoring.py         [igual]      vendoriza shared/ en core/shared/
├── lambda_controller.py [MODIFICAR]  deploy/run usan provisioner+state, no SAM
├── infra_deploy.py      [RENOMBRAR]  -> infra_provision.py, sin CloudFormation
├── database.py          [igual*]     (*lo toca serverless-restructure, no esta spec)
├── secrets.py           [igual]
├── observability.py     [igual]
├── quality.py           [igual]
├── lifecycle.py         [igual]
├── rate_limit_cmds.py   [igual]
├── testing.py           [igual]
├── aws_cli.py           [CREAR]      wrapper unico sobre `aws ...`
├── state.py             [CREAR]      lee/escribe/diff del .state/
├── provisioner.py       [CREAR]      manifest.yaml -> secuencia de llamadas AWS
├── infra_provision.py   [CREAR]      resources/*.yaml -> llamadas AWS
└── local_runtime.py     [CREAR]      run-local con RIE / ejecucion directa

devtools/serverless/sam_generate.py   [ELIMINAR]
```

## 2. Archivo de estado

devtools mantiene un JSON por `(scope, stage)`:

```text
serverless/lambda/.state/
├── .gitignore           [CREAR]  ignora *.json
├── infra-dev.json
├── infra-stage.json
├── infra-prod.json
├── contact-form-dev.json
├── tracking-pixel-dev.json
├── stream-processor-dev.json
├── db-dev.json
└── ... (un archivo por lambda x stage)
```

### Esquema de un archivo de estado

```jsonc
{
  "scope": "contact-form",        // "infra" | nombre del lambda
  "stage": "dev",                 // dev | stage | prod
  "config_hash": "sha256:...",    // hash de la config renderizada (IAM, env, memory, ...)
  "code_hash": "sha256:...",      // hash del contenido de core/ (solo lambdas)
  "resources": {                  // identificadores de lo creado
    "role_arn": "arn:aws:iam::...:role/portfolio-contact-form-dev",
    "role_name": "portfolio-contact-form-dev",
    "function_arn": "arn:aws:lambda:...:function:portfolio-contact-form-dev",
    "function_name": "portfolio-contact-form-dev",
    "log_group": "/aws/lambda/portfolio-contact-form-dev",
    "api_resource_id": "abc123",
    "api_method": "POST /contact",
    "event_source_uuid": null
  },
  "updated_at": "2026-05-21T10:00:00Z"
}
```

`config_hash` y `code_hash` son la clave del diff: si ambos coinciden con
lo que esta en disco, el `deploy` es no-op. Si solo cambia `code_hash`,
se hace `update-function-code`. Si cambia `config_hash`, se re-aplica
configuracion / IAM.

## 3. Flujo de un `deploy` de Lambda

```text
serverless deploy --lambda=contact-form --stage=dev
   |
   v
[1] resolve_lambda          -> ResolvedLambda (root, manifest.yaml)
[2] provisioner.render      -> RenderedLambda (role policy, function config, wiring)
[3] packaging.package       -> build.zip (uv: deps arm64 + core/ + shared/)
[4] state.load(scope,stage) -> estado previo o None
[5] state.diff              -> accion: create | update-code | update-config | noop
   |
   +-- create:
   |     aws iam create-role
   |     aws iam put-role-policy
   |     aws logs create-log-group  (+ put-retention-policy)
   |     aws s3 cp build.zip s3://<bucket>/
   |     aws lambda create-function
   |     [trigger http]            aws apigateway put-method/put-integration
   |                               aws apigateway create-deployment
   |                               aws lambda add-permission
   |     [trigger on-table-changes] aws lambda create-event-source-mapping
   |
   +-- update-code:    aws lambda update-function-code
   +-- update-config:  aws lambda update-function-configuration
   |                   aws iam put-role-policy   (si cambio el IAM)
   +-- noop:           (nada)
   |
   v
[6] state.save(scope,stage)  -> escribe .state/contact-form-dev.json
```

## 4. Flujo de un `destroy`

```text
serverless destroy --stage=dev --yes
   |
   v
[1] state.load de cada scope (infra + 4 lambdas)
[2] borra en ORDEN INVERSO al de creacion:
       lambdas:
         aws lambda delete-event-source-mapping
         aws lambda remove-permission
         aws apigateway delete-method / delete-resource
         aws lambda delete-function
         aws iam delete-role-policy + delete-role
         aws logs delete-log-group
       infra:
         aws apigateway delete-rest-api
         aws dynamodb delete-table  (x5)
         aws sqs delete-queue
[3] state.clear -> borra los .state/*.json del stage
```

## 5. Esquema de los YAML de infra (`resources/`)

Los fragmentos de `resources/` dejan de ser CloudFormation. Pasan a un
esquema propio de devtools, plano y sin funciones intrinsecas. Ejemplo
`resources/dynamodb/contacts.yaml`:

```yaml
# Esquema devtools — NO CloudFormation. Sin Transform, Fn::Sub, Ref.
kind: dynamodb-table
name: portfolio-contacts-${stage}
billing_mode: PAY_PER_REQUEST
hash_key: { name: id, type: S }
stream: NEW_AND_OLD_IMAGES
point_in_time_recovery: true
encryption: true
publishes_ssm:                    # devtools escribe estos SSM tras crear
  name: /portfolio/${stage}/dynamodb/contacts/name
  arn: /portfolio/${stage}/dynamodb/contacts/arn
  stream_arn: /portfolio/${stage}/dynamodb/contacts/stream-arn
tags: { Project: portfolio, ManagedBy: devtools }
```

`infra_provision.py` lee este esquema y emite las llamadas AWS CLI
(`aws dynamodb create-table`, `aws ssm put-parameter`). El manifiesto de
los Lambdas (`lambda.yaml`, que la Fase 2 renombra a `manifest.yaml`) NO
cambia de estructura — sigue declarando `uses.tables`, `uses.secrets`,
`trigger`. Cambian dos cosas: el nombre del archivo y quien lo consume
(`provisioner.py` en vez de `sam_generate.py`).

## 6. Comandos del CLI tras la migracion

| Comando | Antes | Despues |
|---------|-------|---------|
| `sam-generate` | genera `template.yaml` SAM | ELIMINADO |
| `deploy --lambda` | `sam build` + `sam deploy` | `provisioner` + AWS CLI |
| `deploy-infra` | `aws cloudformation deploy` | RENOMBRADO a `provision-infra`, AWS CLI directo |
| `run --stage=local` | `sam local invoke` | RIE / ejecucion directa |
| `run --stage=dev` | `aws lambda invoke` | igual (ya era AWS CLI) |
| `destroy` | (no existia) | NUEVO: borra lambda(s) + infra de un stage |
| `status` | (no existia) | NUEVO: estado local vs `describe-*` |

## 7. Capas de la migracion (orden de implementacion)

```text
Fase 1  aws_cli.py + state.py        (base, sin dependencias)
   |
Fase 2  provisioner.py               (depende de aws_cli + state)
   |
Fase 3  infra_provision.py           (depende de aws_cli + state)
   |
Fase 4  local_runtime.py             (depende de packaging, NO de provisioner)
   |
Fase 5  main.py + flags.py + help.py + lambda_controller.py  (reconexion CLI)
   |
Fase 6  eliminar sam_generate.py + templates + Transform
   |
Fase 7  docs + rules + skill + CLAUDE.md
```

Fases 2, 3 y 4 son independientes entre si (ver
[11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md)).

---

[Anterior: 01](01-contexto-y-decision.md) | [README](README.md) | [Siguiente: 03](03-fase-1-capa-base.md)
