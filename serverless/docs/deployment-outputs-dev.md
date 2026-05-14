# Deployment outputs - dev

> Outputs del stack `portfolio-backend-dev` en region `us-east-1`,
> account `637423614564`. ARNs y nombres de recursos referenciables.
>
> Generado automaticamente por `sam deploy --config-env dev`.
> Re-generar este archivo despues de cada deploy con
> `python devtools/run.py serverless outputs --stage=dev`.
>
> Este archivo NO es gitignored (es publico: solo ARNs, sin secretos).

## Stack info

| Atributo | Valor |
|----------|-------|
| StackName | `portfolio-backend-dev` |
| Region | `us-east-1` |
| Account | `637423614564` |
| Status | `CREATE_COMPLETE` |

## Recursos creados (SPEC-001)

| Logical ID | Tipo | Physical ID |
|------------|------|-------------|
| CommonLayer | Lambda Layer | `arn:aws:lambda:us-east-1:637423614564:layer:portfolio-common-dev:2` |
| ContactsTable | DynamoDB Table | `portfolio-contacts-dev` |
| TrackingTable | DynamoDB Table | `portfolio-tracking-dev` |
| CacheTable | DynamoDB Table | `portfolio-cache-dev` |

## Outputs exportados (CloudFormation Exports)

Reusables desde otros stacks con `!ImportValue portfolio-backend-dev-<Output>`:

| Export | Valor |
|--------|-------|
| `portfolio-backend-dev-ContactsTable` | `portfolio-contacts-dev` |
| `portfolio-backend-dev-ContactsTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-contacts-dev` |
| `portfolio-backend-dev-ContactsStreamArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-contacts-dev/stream/2026-05-14T16:07:59.535` |
| `portfolio-backend-dev-TrackingTable` | `portfolio-tracking-dev` |
| `portfolio-backend-dev-TrackingTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-tracking-dev` |
| `portfolio-backend-dev-TrackingStreamArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-tracking-dev/stream/2026-05-14T16:07:59.227` |
| `portfolio-backend-dev-CacheTable` | `portfolio-cache-dev` |
| `portfolio-backend-dev-CacheTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-cache-dev` |
| `portfolio-backend-dev-CommonLayerArn` | `arn:aws:lambda:us-east-1:637423614564:layer:portfolio-common-dev:2` |

## Pending exports (SPEC-005+)

- `portfolio-backend-dev-ApiEndpoint`
- `portfolio-backend-dev-ApiId`

## Verificacion manual

```bash
# Listar stacks portfolio-*
aws cloudformation describe-stacks --region us-east-1 \
  --query 'Stacks[?starts_with(StackName, `portfolio-backend-`)].[StackName,StackStatus]'

# Verificar streams en ContactsTable
aws dynamodb describe-table --table-name portfolio-contacts-dev --region us-east-1 \
  --query 'Table.StreamSpecification'

# Verificar TTL en TrackingTable
aws dynamodb describe-time-to-live --table-name portfolio-tracking-dev --region us-east-1
```
