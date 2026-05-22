# Commit 3 — Recursos como stacks independientes + SSM

> [Anterior: 01](01-commit-2-cli-tests-run.md) | [README](README.md) |
> [Siguiente: 03](03-commit-4-drop-db.md)

## Objetivo

Que cada recurso compartido (cada tabla DynamoDB, la API Gateway, la
DLQ) sea un **stack CloudFormation independiente**, desplegable y
destruible por separado, sin acoplar a los stacks de los Lambdas.

Este es el commit mas grande del refactor. Requiere deploy real a AWS
para validarse — la verificacion en codigo es solo sintactica.

## El problema que resuelve

Hoy `infra.yaml` (un stack unico) publica `Outputs` con `Export` y los
Lambdas los consumen con `Fn::ImportValue`. **CloudFormation prohibe
borrar o recrear un stack cuyo Export esta en uso.** Eso impide
gestionar cada recurso de forma independiente.

## Diseno: stack-por-recurso + SSM

### Cada fragmento es un stack autonomo

`serverless/lambda/resources/<tipo>/<nombre>.yaml` deja de ser un
fragmento parcial y pasa a ser un **template CloudFormation completo**:
con su `AWSTemplateFormatVersion`, `Parameters` (el `Stage`),
`Resources` y `Outputs`.

Estado actual (a corregir): el commit 1 dejo los fragmentos como YAML
parciales (solo `Resources:` + `Outputs:` con `Export`), pensados para
ensamblarse en UN stack. El commit 3 los convierte en stacks autonomos.

### SSM en vez de Export

Cada stack de recurso, en vez de `Outputs` con `Export`, declara
recursos `AWS::SSM::Parameter` que publican sus identificadores:

```yaml
ContactsTableArnParam:
  Type: AWS::SSM::Parameter
  Properties:
    Name: !Sub /portfolio/${Stage}/dynamodb/contacts/arn
    Type: String
    Value: !GetAtt ContactsTable.Arn
```

Convencion de nombres SSM:
`/portfolio/{stage}/{tipo}/{nombre}/{atributo}` — ej.
`/portfolio/dev/dynamodb/contacts/arn`,
`/portfolio/dev/dynamodb/contacts/name`,
`/portfolio/dev/dynamodb/contacts/stream-arn`,
`/portfolio/dev/api_gateway/portfolio-api/id`.

Los Lambdas leen estos parametros en el **cold start** (modulo scope,
no dentro del handler) via boto3, igual que ya hacen con
`turnstile-secret` y `neon-url`. Esto desacopla: un stack de recurso se
puede redeployar sin tocar ni bloquear los stacks de los Lambdas.

### lambda.yaml declara los recursos que consume

```yaml
# lambda.yaml de contact_form
resources:
  dynamodb: [contacts, cache, rate-limit-rules, rate-limit-buckets]
  api_gateway: [portfolio-api]
```

devtools resuelve esos nombres contra `lambda/resources/<tipo>/`:

- `sam-generate` / `deploy` del Lambda: inyecta en el template las env
  vars con los **paths SSM** de los recursos declarados (no los ARNs —
  los ARNs se resuelven en runtime) y el IAM `ssm:GetParameter` scoped
  a esos paths.
- `deploy` del Lambda puede verificar que los stacks de recursos esten
  deployados antes (opcional: warning si falta uno).

## Comandos nuevos / cambiados

| Comando | Que hace |
|---------|----------|
| `deploy-resource --name=dynamodb/contacts --stage=dev` | Deploya UN stack de recurso (`portfolio-dynamodb-contacts-dev`). |
| `destroy-resource --name=... --stage=... --confirm` | Borra un stack de recurso (destructivo). |
| `deploy-infra` | Cambia semantica: deploya TODOS los stacks de recurso de `resources/` en orden. Ya no ensambla un stack unico. |
| `list-resources` | Lista los recursos declarados en `resources/` y su estado por stage (opcional). |

Nombre de stack por recurso: `portfolio-<tipo>-<nombre>-<stage>`
(ej. `portfolio-dynamodb-contacts-dev`, `portfolio-apigw-dev`).

## Archivos afectados

### Reescribir (los 8 fragmentos a stacks autonomos)
- `serverless/lambda/resources/dynamodb/{contacts,tracking,cache,rate-limit-rules,rate-limit-buckets}.yaml`
- `serverless/lambda/resources/api_gateway/portfolio-api.yaml`
- `serverless/lambda/resources/sqs/stream-processor-dlq.yaml`
  - Cada uno: agregar `AWSTemplateFormatVersion`, `Parameters`,
    convertir `Outputs+Export` en recursos `AWS::SSM::Parameter`.
    Mantener `Outputs` sin `Export` (referencia post-deploy).
- `serverless/lambda/resources/_header.yaml`
  - Ya no se usa para ensamblar; eliminarlo o reconvertirlo en
    documentacion del patron.

### Modificar (devtools)
- `devtools/serverless/infra_deploy.py`
  - Reescribir: `cmd_deploy_infra` itera los stacks de recurso.
  - Agregar `cmd_deploy_resource` / `cmd_destroy_resource`.
  - Quitar `_assemble_template` (el ensamblado de stack unico que dejo
    el commit 1).
- `devtools/serverless/resolve.py`
  - `lambda.yaml`: validar la seccion `resources:` nueva.
- `devtools/serverless/sam_generate.py`
  - Inyectar env vars con los paths SSM de los recursos declarados +
    el IAM `ssm:GetParameter` scoped.
- `devtools/serverless/flags.py`, `main.py`, `help.py`
  - Comandos `deploy-resource`, `destroy-resource`; flag `--name`.

### Modificar (codigo de los Lambdas)
- Cada Lambda que hoy lee `CONTACTS_TABLE_NAME` etc. de env var directa
  pasa a leer el path SSM y resolver el valor en cold start. Revisar
  `lambda/shared/aws/` y los `settings/config.py` de cada Lambda.
  ESTE es el punto que exige deploy real para verificar.

## Criterios de aceptacion

- AC-10: `lambda.yaml` con `resources: {dynamodb: [contacts]}` ->
  `sam-generate` produce un template con la env var del path SSM y el
  IAM scoped.
- AC-11: `deploy-resource --name=dynamodb/contacts --stage=dev` crea el
  stack `portfolio-dynamodb-contacts-dev` y publica los 3 SSM params.
- AC-12: redeployar `dynamodb/contacts` NO requiere bajar
  `contact_form` ni `stream_processor` (no hay Export en uso).
- AC-13: `deploy-infra` deploya todos los stacks de recurso.

## Verificacion

Sin AWS (lo que se puede en sesion):
```bash
for f in serverless/lambda/resources/*/*.yaml; do
  sam validate --template-file "$f" --lint || cfn-lint "$f"
done
devtools/.venv/bin/python -m compileall -q devtools/serverless
```

Con AWS (lo hace el usuario):
```bash
python devtools/run.py serverless deploy-resource --name=dynamodb/contacts --stage=dev
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev
# invocar y verificar que resuelve la tabla via SSM
```

## Definition of Done

- [ ] Los 8 recursos son stacks autonomos validos (`cfn-lint`).
- [ ] `deploy-resource` / `destroy-resource` / `deploy-infra` funcionan.
- [ ] `lambda.yaml` soporta `resources:` y devtools lo resuelve.
- [ ] Los Lambdas leen los recursos via SSM en cold start.
- [ ] Deploy a `dev` verificado por el usuario antes de promover.

## Riesgo

Alto. Toca infra de produccion y el codigo de runtime de los 4 Lambdas.
Considerar partir este commit en dos: (3a) los stacks de recurso + SSM
+ `deploy-resource`; (3b) migrar el codigo de los Lambdas a leer de SSM.

---

[Anterior: 01](01-commit-2-cli-tests-run.md) | [README](README.md) |
[Siguiente: 03](03-commit-4-drop-db.md)
