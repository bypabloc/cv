# Deployment outputs - prod

> Outputs del stack `portfolio-backend-prod` en region `us-east-1`,
> account `637423614564`.
>
> Re-generar con `python devtools/run.py serverless outputs --stage=prod`.

## Stack info

| Atributo | Valor |
|----------|-------|
| StackName | `portfolio-backend-prod` |
| Region | `us-east-1` |
| Account | `637423614564` |
| Status | `CREATE_COMPLETE` |

## Recursos creados (SPEC-001)

| Logical ID | Tipo | Physical ID |
|------------|------|-------------|
| CommonLayer | Lambda Layer | `arn:aws:lambda:us-east-1:637423614564:layer:portfolio-common-prod:1` |
| ContactsTable | DynamoDB Table | `portfolio-contacts-prod` |
| TrackingTable | DynamoDB Table | `portfolio-tracking-prod` |
| CacheTable | DynamoDB Table | `portfolio-cache-prod` |

## Outputs exportados (CloudFormation Exports)

| Export | Valor |
|--------|-------|
| `portfolio-backend-prod-ContactsTable` | `portfolio-contacts-prod` |
| `portfolio-backend-prod-ContactsTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-contacts-prod` |
| `portfolio-backend-prod-ContactsStreamArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-contacts-prod/stream/2026-05-14T16:08:52.372` |
| `portfolio-backend-prod-TrackingTable` | `portfolio-tracking-prod` |
| `portfolio-backend-prod-TrackingTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-tracking-prod` |
| `portfolio-backend-prod-TrackingStreamArn` | (ver `sam list outputs --stack-name portfolio-backend-prod`) |
| `portfolio-backend-prod-CacheTable` | `portfolio-cache-prod` |
| `portfolio-backend-prod-CacheTableArn` | `arn:aws:dynamodb:us-east-1:637423614564:table/portfolio-cache-prod` |
| `portfolio-backend-prod-CommonLayerArn` | `arn:aws:lambda:us-east-1:637423614564:layer:portfolio-common-prod:1` |

## Pending exports (SPEC-005+)

- `portfolio-backend-prod-ApiEndpoint`
- `portfolio-backend-prod-ApiId`
