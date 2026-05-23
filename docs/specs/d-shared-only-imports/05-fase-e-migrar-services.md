# Fase E — Migrar imports en los 5 services

> Reemplaza todos los `from pydantic`, `from sqlalchemy`, `import boto3`,
> `from aws_lambda_powertools` en `services/*/core/**/*.py` por imports
> desde `shared.*`. Cinco commits independientes (uno por service).

## Contexto / Problema

Estado actual (auditoria):

| Service | Archivos con import prohibido |
|---------|--------------------------------|
| cv | `core/models/cv.py` (pydantic), `core/handler.py` (MetricUnit) |
| db | `core/models/db.py` (pydantic), `core/handler.py` (MetricUnit), `core/services/seed_service.py` (sqlalchemy) |
| contact_form | `core/models/contact.py` (pydantic + EmailStr), `core/services/contact_service.py` (boto3 + MetricUnit) |
| tracking_pixel | `core/models/tracking.py` (pydantic), `core/handler.py` (MetricUnit) |
| stream_processor | `core/models/stream.py` (pydantic), `core/handler.py` (MetricUnit), `core/services/stream_service.py` (boto3.dynamodb.types) |

Cada service se migra en un commit aparte. Los services NO declaran los
paquetes en su `pyproject.toml` — el cierre transitivo de `shared/` ya los
aporta. `contact_form` ademas RETIRA `pydantic[email]` (ahora en shared.core).

## Solucion

### E.1 — cv (commit 1)

**Archivos**:
- `serverless/lambda/services/cv/core/models/cv.py`
- `serverless/lambda/services/cv/core/handler.py`

**Cambios**:
```diff
- from pydantic import BaseModel, Field
+ from shared.core import BaseModel, Field
```
```diff
- from aws_lambda_powertools.metrics import MetricUnit
+ from shared.observability import MetricUnit
```

**Verificacion**: `serverless tests --type=unit --lambda=cv` + `serverless
lint-deps --lambda=cv`.

### E.2 — db (commit 2)

**Archivos**:
- `serverless/lambda/services/db/core/models/db.py`
- `serverless/lambda/services/db/core/handler.py`
- `serverless/lambda/services/db/core/services/seed_service.py`

**Cambios en seed_service.py**:
```diff
- from sqlalchemy import select, func
- from sqlalchemy.dialects.postgresql import insert
- from sqlalchemy.orm import Session
+ from shared.db import Session, func, pg_insert as insert, select
```
(El alias `pg_insert as insert` preserva el nombre `insert` ya usado en el
cuerpo del modulo, minimiza el diff.)

**Cambios en handler.py + models/db.py**: identicos al patron de E.1.

**Verificacion**: `serverless tests --type=unit --lambda=db` + `serverless
lint-deps --lambda=db`. Validacion runtime opcional: `serverless deploy
--lambda=db --stage=dev` + `serverless run --stage=dev --lambda=db
--event=events/seed.json` (los counts deben coincidir con el run previo).

### E.3 — contact_form (commit 3)

**Archivos**:
- `serverless/lambda/services/contact_form/pyproject.toml`
- `serverless/lambda/services/contact_form/core/models/contact.py`
- `serverless/lambda/services/contact_form/core/services/contact_service.py`

**Cambios en pyproject.toml**:
```diff
- "pydantic[email]>=2.5,<3.0",   # EXCEPTION D-3: lo usa EmailStr, shared/ no lo aporta
+ # pydantic[email] viene transitivo de shared/core/pyproject.toml
```
Tras el cambio el dedup pasa: shared.core declara `pydantic[email]` y
contact_form no lo declara.

**Cambios en contact.py**:
```diff
- from pydantic import BaseModel, EmailStr, Field, field_validator
+ from shared.core import BaseModel, EmailStr, Field, field_validator
```

**Cambios en contact_service.py**:
```diff
- import boto3
- from aws_lambda_powertools.metrics import MetricUnit
+ from shared.aws import send_email
+ from shared.observability import MetricUnit
```

Reemplazar la funcion `_ses_client()` y la llamada manual a `send_email` de
boto3 por la invocacion al helper:

```python
# antes: _ses_client().send_email(FromEmailAddress=..., Destination=..., Content=...)
# despues:
response = send_email(
    from_address=settings.ses_from_address,
    to_addresses=destination_addresses,
    subject=subject,
    text_body=text_body,
    html_body=html_body,
    reply_to=[contact.email] if contact.email else None,
)
```

**Tests del contact_form**: actualizar mocks. Los tests que parchen
`contact_service._ses_client` deben ahora parchear `shared.aws.ses._client`
(o `shared.aws.send_email` segun nivel). Documentar el nuevo punto de mock
en el docstring del test.

**Verificacion**: `serverless tests --type=unit --lambda=contact_form` +
`serverless lint-deps --lambda=contact_form`.

### E.4 — tracking_pixel (commit 4)

**Archivos**:
- `serverless/lambda/services/tracking_pixel/core/models/tracking.py`
- `serverless/lambda/services/tracking_pixel/core/handler.py`

**Cambios**: identicos al patron de E.1 (pydantic + MetricUnit).

**Verificacion**: `serverless tests --type=unit --lambda=tracking_pixel`.

### E.5 — stream_processor (commit 5)

**Archivos**:
- `serverless/lambda/services/stream_processor/core/models/stream.py`
- `serverless/lambda/services/stream_processor/core/handler.py`
- `serverless/lambda/services/stream_processor/core/services/stream_service.py`

**Cambios en stream_service.py**:
```diff
- from boto3.dynamodb.types import TypeDeserializer
+ from shared.aws import TypeDeserializer
```

**Cambios en handler.py + models/stream.py**: identicos al patron de E.1.

**Verificacion**: `serverless tests --type=unit --lambda=stream_processor`.

## Criterios de aceptacion globales (Fase E)

- **AC-E1**: Given los 5 services migrados, When ejecuto `grep -rE
  "^from pydantic|^import pydantic|^from sqlalchemy|^import boto3|^from
  boto3|^from aws_lambda_powertools|^import aws_lambda_powertools"
  serverless/lambda/services/*/core/`, Then la salida es vacia.
- **AC-E2**: Given `serverless lint-deps`, When se ejecuta sin target, Then
  exit 0 para los 5 lambdas (no hay duplicacion).
- **AC-E3**: Given `serverless tests --type=unit --lambda=<X>` para cada
  uno de los 5 lambdas, Then las suites pasan (cero regresiones).
- **AC-E4**: Given `serverless deploy --lambda=db --stage=dev` post-migracion
  y luego `serverless run --stage=dev --lambda=db --event=events/seed.json`,
  Then los counts del seed son identicos al run previo (1 profile, 9
  experiences, 6 projects, 11 certificates, 10 references, 2 awards, 3
  education, 2 languages, 354 translations, 99 skills, 26 tech_tags, 36
  niche_priorities).

## Verificacion por service (resumen)

```bash
# Por cada service migrado
python devtools/run.py serverless tests --type=unit --lambda=<X>
python devtools/run.py serverless lint-deps --lambda=<X>

# Tras los 5
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless lint-deps
```

## Commits

1. `refactor(cv): usa shared.core y shared.observability en lugar de pydantic y powertools directo`
2. `refactor(db): seed_service usa shared.db; handler y models usan shared.core + shared.observability`
3. `refactor(contact_form): usa shared.core (EmailStr), shared.aws.send_email y shared.observability`
4. `refactor(tracking_pixel): usa shared.core y shared.observability`
5. `refactor(stream_processor): usa shared.core, shared.aws.TypeDeserializer y shared.observability`
