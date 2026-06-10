# Lambda `cv_admin`

> Endpoint HTTP `POST /cv-admin` de la gestion del CV (plan
> c-cv-management): operation `content` (escritura de las entidades
> `cv_*` en Neon) y operation `publish` (dispara/consulta el workflow
> `deploy-apps.yml` via la GitHub API). TODAS las actions son admin-only:
> access JWT + whitelist SSM `admin-emails` (no-admin -> 404
> anti-enumeration). Sin Turnstile (ya autenticado).

## Contrato

Body JSON `{operation, action, data}` + header
`Authorization: Bearer <access JWT>`.

| Operation | Actions |
|-----------|---------|
| `content` | `upsert-profile`, `upsert-experience` / `delete-experience`, `upsert-project` / `delete-project`, `upsert-education` / `delete-education`, `upsert-certificate` / `delete-certificate`, `upsert-award` / `delete-award`, `upsert-language` / `delete-language`, `upsert-endorsement` / `delete-endorsement`, `upsert-publication` / `delete-publication`, `upsert-skill-category` / `delete-skill-category`, `reorder`, `catalogs` |
| `publish` | `dispatch`, `status` |

Errores: `1100 UNKNOWN_NICHE` / `1101 REORDER_SLUGS_MISMATCH` /
`1102 INVALID_FIELD_VALUE` (400), `4404 SLUG_NOT_FOUND` /
`NICHE_NOT_FOUND` (404), `5200 GITHUB_API_ERROR` (502). El contrato
vive en el codigo: payloads en `core/models/` (Pydantic, shape YAML del
seed), mapeo codigo->status en `core/controllers/_base.py` y los E2E de
`tests/api/test_cv_admin_*.py` como especificacion ejecutable.

## Escritura

Los services NO duplican SQL: llaman la capa unica de escritura
`shared.db.repositories.cv_write` / `cv_write_entities` (la misma que el
seed de la Lambda `db`) dentro de UNA transaccion (`db_session()`), y al
commit invalidan el cache DynamoDB por tag `'cv'` (las lecturas del
Lambda `cv` usan `@cached(tags=['cv'])`).

## Seeds de rate-limit (operativo — correr 1 vez por stage)

Las reglas NO viven en el repo: se seedean en la tabla
`rate-limit-rules` con el CLI de devtools (patron de
`.claude/docs/auth-system/03-rate-limit-rules.md`). Reglas de cv_admin:

```bash
# dev (repetir con --stage=prod)
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv-admin#content' --limit=30 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv-admin#publish.dispatch' --limit=3 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv-admin#publish.status' --limit=30 --window=60 --aws-profile=tfs-dev
```

`content` comparte UNA key por operation (todas las actions ~30/min,
mismo criterio que `/users#admin`); `publish.dispatch` tiene su propia
key estricta (cada dispatch es un trigger de CI).

## Secretos (SSM)

| Short name | Uso |
|------------|-----|
| `neon-url` | connection string Neon (escritura `cv_*`) |
| `jwt-secret` | verifica el access JWT (HS256) |
| `admin-emails` | whitelist del scope admin (todas las actions) |
| `github-deploy-token` | PAT fine-grained (Actions RW en `bypabloc/cv`) para el `workflow_dispatch` |

## Operacion

```bash
python devtools/run.py serverless tests --type=unit --lambda=cv_admin
python devtools/run.py serverless tests --type=coverage --lambda=cv_admin
python devtools/run.py serverless lint-deps --lambda=cv_admin
python devtools/run.py serverless deploy --lambda=cv_admin --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=cv_admin \
  --event=events/catalogs.json --aws-profile=tfs-dev
```

Tras el primer deploy: MEDIR la memoria minima real (procedimiento de
`.claude/rules/lambda-config.md`) y actualizar el comentario del
`manifest.yaml`.
