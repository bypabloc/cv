# Fase 3 — Lambda nlweb (Python)

> Objetivo: nueva Lambda `nlweb` que recibe POST con `{query, niche?}`,
> hace retrieval estructurado contra Neon, y retorna schema.org JSON-LD
> con experiencias/proyectos/skills matchados. Cubre AC-8, AC-9, AC-10.

## 1. Decisiones puntuales (cerradas en el README, recordadas aqui)

- **Lambda nueva separada** en `serverless/lambda/services/nlweb/`,
  hermana de `cv`. Sigue el patron `lambda-controller` (manifest,
  pyproject, core/{handler,controllers,services,models,settings}).
- **Sin LLM** — retrieval estructurado por keywords con `ILIKE` +
  ranking por overlap de tokens. La IA cliente razona sobre la
  respuesta JSON-LD.
- **Cache via `@cached(ttl=300)`** del paquete `shared.cache` — si la
  misma query llega 2x en 5min, el segundo es HIT.
- **Trigger HTTP POST /nlweb/ask** — API Gateway REST API. Reusa el
  REST API ya provisionado (mismo `ApiId` en SSM).

## 2. Estructura del paquete

```text
serverless/lambda/services/nlweb/
├── manifest.yaml                # config del Lambda (devtools la lee)
├── pyproject.toml               # deps Python (PEP 621, uv)
├── uv.lock
├── .gitignore                   # build/, build.zip, __pycache__
├── core/
│   ├── __init__.py
│   ├── handler.py               # entrypoint AWS
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── nlweb/
│   │       ├── __init__.py
│   │       └── ask.py           # Ask(BaseController)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── retrieval_service.py # busqueda Neon (experiences, projects, skills)
│   │   └── schema_org_service.py# convierte resultados a JSON-LD ItemList
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ask.py               # AskPayload Pydantic (query, niche)
│   │   └── schema_org.py        # SchemaOrgItemList, Person, Organization, etc.
│   └── settings/
│       ├── __init__.py
│       ├── config.py            # AppConfig (NEON_URL_PATH, CACHE_TTL, etc.)
│       └── operations.py        # OPERATIONS = {'nlweb': {controller: 'nlweb'}}
├── events/
│   ├── ask.json                 # payload de prueba para serverless run
│   └── ask_empty.json           # query sin matches (verifica AC-9)
└── tests/
    ├── conftest.py              # mocks unit, env vars, sys.path
    ├── _helpers.py              # builders compartidos
    ├── unit/
    │   ├── test_retrieval_service_filters_by_niche.py
    │   ├── test_retrieval_service_ranks_by_token_overlap.py
    │   ├── test_retrieval_service_returns_empty_when_no_match.py
    │   ├── test_schema_org_service_wraps_in_itemlist.py
    │   ├── test_schema_org_service_emits_person_context.py
    │   ├── test_ask_controller_preload_resolves_neon_url.py
    │   ├── test_ask_controller_validate_rejects_empty_query.py
    │   ├── test_ask_controller_execute_returns_schema_org.py
    │   ├── test_handler_ask_action_returns_200_with_jsonld.py
    │   ├── test_handler_missing_query_returns_400.py
    │   └── test_handler_cache_hit_emits_x_cache_header.py
    └── integration/
        ├── conftest.py          # SIN mocks; fixtures Neon real
        ├── _fixtures/
        │   └── seeded_cv.py     # asegura datos en Neon antes del test
        └── test_ask_e2e_fintech_query_returns_real_data.py
```

## 3. `manifest.yaml`

```yaml
# Manifiesto del Lambda `nlweb` — NLWeb endpoint sobre el CV (Neon).
# devtools traduce este manifiesto a llamadas AWS CLI directas:
#   python devtools/run.py serverless deploy --lambda=nlweb

name: nlweb
description: NLWeb endpoint — natural-language query sobre el CV, retorna schema.org JSON-LD.

runtime: python3.13
handler: core.handler.lambda_handler
memory: 512
timeout: 30

trigger:
  type: http
  method: POST
  path: /nlweb/ask

uses:
  tables:
    cache: read-write
  secrets:
    - neon-url
  sends-email: false

env:
  default:
    LOG_LEVEL: INFO
    CACHE_TTL: '300'
    NLWEB_RESULT_LIMIT: '20'
  dev:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.dev.the-full-stack.com,https://hub.portfolio.dev.the-full-stack.com,https://fintech.portfolio.dev.the-full-stack.com,https://architect.portfolio.dev.the-full-stack.com,https://leader.portfolio.dev.the-full-stack.com,https://vibe.portfolio.dev.the-full-stack.com'
  stage:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.stage.the-full-stack.com,https://hub.portfolio.stage.the-full-stack.com,https://fintech.portfolio.stage.the-full-stack.com,https://architect.portfolio.stage.the-full-stack.com,https://leader.portfolio.stage.the-full-stack.com,https://vibe.portfolio.stage.the-full-stack.com'
  prod:
    LOG_LEVEL: WARNING
    CORS_ALLOWED_ORIGINS: 'https://the-full-stack.com,https://hub.portfolio.the-full-stack.com,https://fintech.portfolio.the-full-stack.com,https://architect.portfolio.the-full-stack.com,https://leader.portfolio.the-full-stack.com,https://vibe.portfolio.the-full-stack.com'
```

## 4. `pyproject.toml`

Deps minimas — la libreria comun aporta SQLAlchemy, psycopg, pydantic
y boto3 via vendoring selectivo. La regla de dedup
(`serverless lint-deps`) rechaza declarar deps que ya estan en
`shared.db`/`shared.cache`/`shared.observability`.

```toml
[project]
name = "nlweb-lambda"
version = "0.1.0"
description = "NLWeb endpoint Lambda — schema.org JSON-LD over CV"
requires-python = ">=3.13,<3.14"
dependencies = [
    # SQLAlchemy y psycopg vienen via shared.db (no declarar aqui)
    # pydantic y boto3 via shared.lambda_kit y shared.aws
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
    "pytest-cov>=5.0",
]

[tool.shared]
internal-deps = [
    "core",
    "db",
    "cache",
    "lambda_kit",
    "http",
    "observability",
]
```

## 5. Modelos Pydantic

### `core/models/ask.py`

```python
"""Payload del POST /nlweb/ask."""
from typing import Literal
from pydantic import BaseModel, Field

Niche = Literal['generic', 'hub', 'fintech', 'architect', 'leader', 'vibe']


class AskPayload(BaseModel):
    """Body del request a /nlweb/ask.

    Given un POST con {query, niche?}, valida estructura y normaliza.
    """
    query: str = Field(min_length=1, max_length=500)
    niche: Niche | None = None
    limit: int = Field(default=20, ge=1, le=50)
```

### `core/models/schema_org.py`

```python
"""Modelos del response schema.org JSON-LD."""
from typing import Any
from pydantic import BaseModel, Field


class SchemaOrgPerson(BaseModel):
    type_: str = Field(alias='@type', default='Person')
    name: str
    url: str | None = None


class SchemaOrgListItem(BaseModel):
    type_: str = Field(alias='@type', default='ListItem')
    position: int
    item: dict[str, Any]


class SchemaOrgItemList(BaseModel):
    context: str = Field(alias='@context', default='https://schema.org')
    type_: str = Field(alias='@type', default='ItemList')
    name: str
    description: str
    numberOfItems: int
    itemListElement: list[SchemaOrgListItem]
    about: SchemaOrgPerson | None = None
```

## 6. Service: retrieval estructurado

### `core/services/retrieval_service.py`

```python
"""Retrieval estructurado sobre Neon — sin LLM.

Estrategia:
1. Tokenizar la query (lowercase, split, dropping stopwords)
2. Buscar entries de cv_experiences, cv_projects, cv_skills donde
   alguna columna textual matchea ILIKE %token% para algun token
3. Rankear por overlap de tokens
4. Filtrar por niche si se proveyo (usando tabla puente cv_<X>_niches)
5. Retornar hasta 'limit' entries con score
"""
from dataclasses import dataclass
from typing import Any

from shared.db.engine import get_engine
from sqlalchemy import text

STOPWORDS = {'a', 'an', 'and', 'or', 'the', 'in', 'on', 'at', 'with',
             'el', 'la', 'los', 'las', 'de', 'del', 'y', 'o', 'en'}


@dataclass(frozen=True)
class RetrievalResult:
    kind: str  # 'experience' | 'project' | 'skill'
    slug: str
    title: str
    description: str
    score: float
    metadata: dict[str, Any]


def tokenize(query: str) -> list[str]:
    tokens = [t.strip().lower() for t in query.replace(',', ' ').split()]
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]


def retrieve(*, query: str, niche: str | None, limit: int) -> list[RetrievalResult]:
    tokens = tokenize(query)
    if not tokens:
        return []
    engine = get_engine()
    results: list[RetrievalResult] = []
    with engine.connect() as conn:
        results.extend(_query_experiences(conn, tokens=tokens, niche=niche))
        results.extend(_query_projects(conn, tokens=tokens, niche=niche))
        results.extend(_query_skills(conn, tokens=tokens))
    # Rank por score desc, luego truncar
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


def _query_experiences(conn, *, tokens, niche):
    # Construye OR de ILIKE por token sobre role, company, summary
    or_clauses = ' OR '.join(
        f"(role_es ILIKE :tok{i} OR role_en ILIKE :tok{i} "
        f"OR company ILIKE :tok{i} OR summary_es ILIKE :tok{i})"
        for i in range(len(tokens))
    )
    niche_join = ''
    niche_where = ''
    params = {f'tok{i}': f'%{tok}%' for i, tok in enumerate(tokens)}
    if niche:
        niche_join = ' JOIN cv_experience_niches en ON en.experience_id = e.id'
        niche_where = ' AND en.niche = :niche'
        params['niche'] = niche
    sql = text(f"""
        SELECT e.slug, e.role_en, e.company, e.summary_es
        FROM cv_experiences e
        {niche_join}
        WHERE ({or_clauses}) {niche_where}
        LIMIT 50
    """)
    rows = conn.execute(sql, params).fetchall()
    return [
        RetrievalResult(
            kind='experience',
            slug=r.slug,
            title=f'{r.role_en} @ {r.company}',
            description=r.summary_es or '',
            score=_score(tokens, f'{r.role_en} {r.company} {r.summary_es}'),
            metadata={'company': r.company, 'role': r.role_en},
        )
        for r in rows
    ]


# _query_projects, _query_skills siguen mismo patron


def _score(tokens: list[str], text_blob: str) -> float:
    blob_lower = text_blob.lower()
    hits = sum(1 for t in tokens if t in blob_lower)
    return hits / len(tokens) if tokens else 0.0
```

### `core/services/schema_org_service.py`

```python
"""Convierte RetrievalResult[] a schema.org ItemList JSON-LD."""
from typing import Any

from .retrieval_service import RetrievalResult

PERSON = {
    '@type': 'Person',
    'name': 'Pablo Contreras',
    'url': 'https://the-full-stack.com',
    'jobTitle': 'Senior Full Stack Engineer',
}


def to_schema_org(*, query: str, niche: str | None, results: list[RetrievalResult]) -> dict[str, Any]:
    return {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'name': f'Query: {query}',
        'description': f'Results matching "{query}"' + (f' (niche: {niche})' if niche else ''),
        'numberOfItems': len(results),
        'about': PERSON,
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': i + 1,
                'item': _to_schema_item(r),
            }
            for i, r in enumerate(results)
        ],
    }


def _to_schema_item(r: RetrievalResult) -> dict[str, Any]:
    if r.kind == 'experience':
        return {
            '@type': 'WorkExperience',
            'name': r.title,
            'description': r.description,
            'worksFor': {
                '@type': 'Organization',
                'name': r.metadata['company'],
            },
            'jobTitle': r.metadata['role'],
            'url': f'https://the-full-stack.com/experience/{r.slug}',
        }
    if r.kind == 'project':
        return {
            '@type': 'CreativeWork',
            'name': r.title,
            'description': r.description,
            'url': f'https://the-full-stack.com/projects/{r.slug}',
        }
    if r.kind == 'skill':
        return {
            '@type': 'DefinedTerm',
            'name': r.title,
            'description': r.description,
        }
    raise ValueError(f'Unknown kind: {r.kind}')
```

## 7. Controller: Ask

### `core/controllers/nlweb/ask.py`

```python
"""Controller del action 'ask' de la operation 'nlweb'."""
from typing import Any

from shared.cache import cached
from shared.lambda_kit import BaseController

from core.models.ask import AskPayload
from core.services.retrieval_service import retrieve
from core.services.schema_org_service import to_schema_org


class Ask(BaseController):
    """Procesa POST /nlweb/ask.

    Lifecycle:
    - preload: nada que resolver (Neon URL viene de env var inyectada por devtools)
    - validate: parse del body con AskPayload (Pydantic)
    - execute: retrieve + to_schema_org, con @cached
    """
    event_model = AskPayload

    def preload(self) -> dict[str, Any]:
        return {'is_valid': True, 'data': {}, 'code': 0}

    def execute(self) -> dict[str, Any]:
        payload: AskPayload = self.validated_data
        result = self._cached_search(
            query=payload.query,
            niche=payload.niche,
            limit=payload.limit,
        )
        return {
            'is_valid': True,
            'data': result,
            'code': 0,
            'content_type': 'application/ld+json',
        }

    @cached(ttl=300, key_prefix='nlweb:ask')
    def _cached_search(self, *, query: str, niche: str | None, limit: int) -> dict[str, Any]:
        results = retrieve(query=query, niche=niche, limit=limit)
        return to_schema_org(query=query, niche=niche, results=results)
```

## 8. Handler y settings

### `core/settings/operations.py`

```python
OPERATIONS = {
    'nlweb': {
        'controller': 'nlweb',
        'arn_key': '',
    },
}
```

### `core/handler.py`

Reusa `shared.lambda_kit.http_dispatch` (definida en el plan
`c-cv-data-service` ya mergeado — confirmar en `shared/lambda_kit/__init__.py`).

```python
"""Entrypoint AWS — POST /nlweb/ask."""
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger

from core.settings.operations import OPERATIONS


def lambda_handler(event, context):
    """Recibe POST API Gateway, devuelve response con CORS + JSON-LD."""
    return http_handler(
        event=event,
        context=context,
        operations=OPERATIONS,
        default_operation='nlweb',
        default_action='ask',
        logger=logger,
    )
```

> Si `http_dispatch.http_handler` aun no soporta POST con body (solo GET
> con query params), agregarle el path POST en la misma fase (se hace
> en `shared/lambda_kit/http_dispatch.py`). Es un cambio chico — el
> handler ya distingue method. Verificar en el codigo actual.

## 9. Events de prueba (`events/`)

### `events/ask.json`

```json
{
  "version": "2.0",
  "routeKey": "POST /nlweb/ask",
  "rawPath": "/nlweb/ask",
  "requestContext": {
    "http": { "method": "POST", "path": "/nlweb/ask" }
  },
  "headers": { "content-type": "application/json" },
  "body": "{\"query\": \"fintech experience with Vue and Django\", \"niche\": \"fintech\"}",
  "isBase64Encoded": false
}
```

### `events/ask_empty.json`

```json
{
  "version": "2.0",
  "routeKey": "POST /nlweb/ask",
  "rawPath": "/nlweb/ask",
  "requestContext": { "http": { "method": "POST", "path": "/nlweb/ask" } },
  "headers": { "content-type": "application/json" },
  "body": "{\"query\": \"zzzzzzzzzzzz\"}",
  "isBase64Encoded": false
}
```

## 10. Tests — un archivo por escenario

### Unit (ejemplos clave)

```python
# tests/unit/test_retrieval_service_filters_by_niche.py
"""Given query con niche, When retrieve, Then solo entries del niche."""
from unittest.mock import MagicMock
from core.services.retrieval_service import retrieve, RetrievalResult

def test_retrieve_filters_by_niche(mocker):
    # Arrange
    mock_engine = mocker.patch('core.services.retrieval_service.get_engine')
    mock_conn = mock_engine.return_value.connect.return_value.__enter__.return_value
    mock_conn.execute.return_value.fetchall.return_value = []
    # Act
    retrieve(query='fintech', niche='fintech', limit=20)
    # Assert
    sql_call = mock_conn.execute.call_args_list[0]
    params = sql_call[0][1]
    assert params['niche'] == 'fintech'
```

```python
# tests/unit/test_schema_org_service_wraps_in_itemlist.py
"""Given results, When to_schema_org, Then @type=ItemList con @context."""
from core.services.retrieval_service import RetrievalResult
from core.services.schema_org_service import to_schema_org

def test_to_schema_org_wraps_in_itemlist():
    # Arrange
    results = [RetrievalResult(kind='experience', slug='x', title='Senior @ Acme',
                                description='desc', score=1.0,
                                metadata={'company': 'Acme', 'role': 'Senior'})]
    # Act
    result = to_schema_org(query='senior', niche=None, results=results)
    # Assert
    assert result['@type'] == 'ItemList'
    assert result['@context'] == 'https://schema.org'
    assert result['numberOfItems'] == 1
```

```python
# tests/unit/test_handler_ask_action_returns_200_with_jsonld.py
"""Given POST /nlweb/ask con body valido, When handler, Then 200 + content-type ld+json."""
from core.handler import lambda_handler
import json

def test_handler_returns_200_with_jsonld(mocker):
    # Arrange
    mocker.patch('core.controllers.nlweb.ask.retrieve', return_value=[])
    event = json.load(open('events/ask.json'))
    # Act
    result = lambda_handler(event, None)
    # Assert
    assert result['statusCode'] == 200
    assert result['headers']['Content-Type'] == 'application/ld+json'
    body = json.loads(result['body'])
    assert body['@context'] == 'https://schema.org'
    assert body['numberOfItems'] == 0
```

```python
# tests/unit/test_handler_cache_hit_emits_x_cache_header.py
"""Given misma query 2x, When handler, Then segunda con X-Cache: HIT [AC-10]."""

def test_cache_hit_on_second_call(mocker):
    # Arrange
    mock_retrieve = mocker.patch('core.controllers.nlweb.ask.retrieve', return_value=[])
    event = json.load(open('events/ask.json'))
    # Act
    first = lambda_handler(event, None)
    second = lambda_handler(event, None)
    # Assert
    assert mock_retrieve.call_count == 1   # cache evito segunda llamada
    assert first['headers'].get('X-Cache') == 'MISS'
    assert second['headers'].get('X-Cache') == 'HIT'
```

### Integration

```python
# tests/integration/test_ask_e2e_fintech_query_returns_real_data.py
"""Given Neon con CV seedeado, When POST con query fintech, Then resultados reales."""
# SIN mocks — necesita conexion a Neon dev y fixtures _fixtures/seeded_cv.py
```

## 11. Wiring con devtools

```bash
# Local
python devtools/run.py serverless run \
  --stage=local --lambda=nlweb --event=events/ask.json

# Tests unit
python devtools/run.py serverless tests --type=unit --lambda=nlweb

# Coverage
python devtools/run.py serverless tests --type=coverage --lambda=nlweb

# Deploy a dev
python devtools/run.py serverless deploy \
  --lambda=nlweb --stage=dev --aws-profile=tfs-dev

# Verificar
python devtools/run.py serverless status \
  --lambda=nlweb --stage=dev --aws-profile=tfs-dev

# Probar contra dev
curl -X POST 'https://api.portfolio.dev.the-full-stack.com/nlweb/ask' \
  -H 'Content-Type: application/json' \
  -d '{"query": "fintech", "niche": "fintech"}' | jq .
```

## 12. Verificacion incremental

Cada commit de la fase debe pasar:

```bash
# Sintaxis Python OK
cd serverless/lambda/services/nlweb && uv run python -m compileall -q core

# Lint deps (la regla de dedup contra shared)
python devtools/run.py serverless lint-deps --lambda=nlweb

# Unit tests verdes
python devtools/run.py serverless tests --type=unit --lambda=nlweb

# Coverage >= 80% (regla pre-push)
python devtools/run.py serverless tests --type=coverage --lambda=nlweb
```

## 13. Riesgos / mitigaciones

| Riesgo | Mitigacion |
|--------|-----------|
| Retrieval con `ILIKE` es lento en tabla grande | El CV de Pablo tiene <50 experiencias, <30 proyectos. No es problema. Si llega a serlo, agregar GIN index en pg_trgm |
| Query injection via tokens | Pydantic limita query a 500 chars; usamos parametros SQL `:tok0` (psycopg escapa). Verificado |
| Cache stampede en cold start | `shared.cache` ya implementa lock distribuido. Heredado |
| CORS no permite request desde el subdominio nuevo | El manifest declara los 6 origins por stage. Confirmar que el resolver de CORS los honra |
| Cliente nuevo (Cursor) ignora `Content-Type: application/ld+json` | Es compliant con MCP spec; los clientes que no lo entiendan pueden parsearlo como `application/json` (es valido JSON). Verificable en el AC-8 |

## 14. Notas

- NO se modifica la Lambda `cv` ni `contact_form`. Aisladamente.
- El seed del CV ya ocurre en la Lambda `db` (action `seed`). Si la
  data de dev/prod no esta seedeada al momento de testear, correr:
  ```bash
  python devtools/run.py serverless run --stage=dev --lambda=db \
    --event=events/seed.json --aws-profile=tfs-dev
  ```
- El AC-13 (score 70+) depende de TODAS las fases. Esta sola no lo
  alcanza — debe estar acoplada a fases 1, 2, 4.
