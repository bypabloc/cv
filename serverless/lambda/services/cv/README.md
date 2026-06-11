# Lambda `cv`

> TODA la logica del CV en un solo Lambda (plan d-cv-consolidation):
> `GET /cv` operation `cv` (lectura publica cacheada desde Neon),
> `POST /cv` operation `content` (escritura admin de las entidades
> `cv_*` + `reorder` + `catalogs` + `get-all`) y operation `publish`
> (dispara/consulta el workflow `deploy-apps.yml` via la GitHub API).
> Las operations admin exigen access JWT + whitelist SSM `admin-emails`
> (no-admin -> 404 anti-enumeration) via `required_permission='admin'`
> resuelto por la fase Authorize del lambda_kit. Sin Turnstile.

## Contrato

- `GET /cv?operation=cv&action=<get|profile|experiences|projects|certificates|awards|education|languages|references|skills>[&niche=][&locale=]`
  — publico, CORS `*`, cacheado (`@cached` tags `['cv']`).
- `POST /cv` body JSON `{operation, action, data}` + header
  `Authorization: Bearer <access JWT>` — admin-only, CORS echo (origin
  del admin).

| Operation | Actions |
|-----------|---------|
| `content` | `get-all` (CV completo en shape de edicion, 10 secciones incl. publications, 1 sesion Neon), `upsert-profile`, `upsert-<entidad>` / `delete-<entidad>` (experience, project, education, certificate, award, language, endorsement, publication, skill-category), `reorder`, `catalogs` |
| `publish` | `dispatch`, `status` |

Errores admin: `1100 UNKNOWN_NICHE` / `1101 REORDER_SLUGS_MISMATCH` /
`1102 INVALID_FIELD_VALUE` (400), `4404 SLUG_NOT_FOUND` /
`NICHE_NOT_FOUND` (404), `5200 GITHUB_API_ERROR` (502). El contrato
vive en el codigo: payloads en `core/models/` (Pydantic, shape YAML del
seed), mapeo codigo->status en `core/controllers/_base.py` y los E2E de
`tests/api/test_cv_admin_*.py` como especificacion ejecutable.

## Escritura

Los services NO duplican SQL: llaman la capa unica de escritura
`shared.db.repositories.cv_write` / `cv_write_entities` (la misma que el
seed de la Lambda `db`) dentro de UNA transaccion (`db_session()`), y al
commit invalidan el cache DynamoDB por tag `'cv'` (las lecturas usan
`@cached(tags=['cv'])` — el editor nunca ve datos stale tras editar).

## Seeds de rate-limit (operativo — correr 1 vez por stage)

Las reglas NO viven en el repo: se seedean en la tabla
`rate-limit-rules` con el CLI de devtools (patron de
`.claude/docs/auth-system/03-rate-limit-rules.md`):

```bash
# dev (repetir con --stage=prod)
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv#content' --limit=30 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv#publish.dispatch' --limit=3 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='/cv#publish.status' --limit=30 --window=60 --aws-profile=tfs-dev
```

`content` comparte UNA key por operation (todas las actions ~30/min,
mismo criterio que `/users#admin`); `publish.dispatch` tiene su propia
key estricta (cada dispatch es un trigger de CI). La operation publica
`cv` NO tiene regla (cacheada + publica). Las rows viejas `'/cv-admin#*'`
del ex Lambda cv_admin quedan huerfanas (sin CLI delete) — limpiarlas
con `aws dynamodb delete-item` manual.

## Secretos (SSM)

| Short name | Uso |
|------------|-----|
| `neon-url` | connection string Neon (lectura + escritura `cv_*`) |
| `jwt-secret` | verifica el access JWT (HS256) de content/publish |
| `admin-emails` | whitelist del scope admin |
| `github-deploy-token` | PAT fine-grained (Actions RW en `bypabloc/cv`) para el `workflow_dispatch` |

## Operacion

```bash
python devtools/run.py serverless tests --type=unit --lambda=cv
python devtools/run.py serverless tests --type=coverage --lambda=cv
python devtools/run.py serverless lint-deps --lambda=cv
python devtools/run.py serverless deploy --lambda=cv --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=cv \
  --event=events/get.json --aws-profile=tfs-dev
```
