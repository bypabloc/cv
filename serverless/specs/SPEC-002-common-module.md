# SPEC-002: Modulo `src/common/` compartido

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/common/`
**Dependencias**: SPEC-001
**Paralelizable con**: SPEC-008

## 1. Contexto

Las 5 Lambdas del proyecto comparten infrastructure code: boto3 clients
inicializados en module scope, Powertools logger/tracer/metrics
configurados, helpers de respuestas HTTP, validators, type definitions.
Sin un modulo `common/`, este codigo se duplicaria en cada handler con
drift inevitable.

### Hallazgos de exploracion

- Patron documentado en `serverless/ARCHITECTURE.md` seccion 1 (estructura)
- Decision en `.claude/docs/aws-lambda/04-cold-start-optimization.md`:
  boto3 clients en module scope, NO en handler
- Type hints obligatorios por `.claude/rules/python.md`

## 2. Solucion propuesta

Crear `serverless/src/common/` con 14 archivos:

```text
common/
├── __init__.py
├── config.py              # Settings desde env vars + SSM (Pydantic)
├── logger.py              # Powertools Logger configurado
├── tracer.py              # Powertools Tracer (X-Ray)
├── metrics.py             # Powertools Metrics (CloudWatch EMF)
├── responses.py           # JSON response helpers (200/400/429/500 + CORS)
├── cors.py                # Whitelist + Gateway Response helper
├── exceptions.py          # ApplicationError + ValidationError jerarquia
├── dynamodb_client.py     # boto3.resource('dynamodb') module scope
├── ses_client.py          # boto3.client('sesv2') module scope
├── ssm_client.py          # Powertools parameters + KMS decrypt
├── ip_extractor.py        # CF-Connecting-IP > X-Forwarded-For priority
├── ulid.py                # UUIDv7 generator (sorted by time)
├── validators.py          # Email regex + sanitizers
└── types.py               # TypedDicts compartidos
```

### Decisiones clave

- **Decision 1: Pydantic v2 para Settings** — vs python-decouple. Razon:
  validacion estructural + auto-cast tipos + integracion natural con
  Powertools `@validator`.
- **Decision 2: Powertools Logger con `inject_lambda_context`** — vs
  logging stdlib. Razon: correlation IDs automaticos, JSON structured
  por default, retencion natural con LOG_LEVEL env var.
- **Decision 3: Module-scope clients** — boto3 client/resource inicializa
  ~30-100ms (HTTPS connection pool + STS roles). Reusar entre invocaciones
  warm baja cold-start de ~250ms a ~100ms.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given handler de prueba importa `from common.logger import
  logger`, When invoco handler con event vacio, Then logs en CloudWatch
  contienen `service`, `correlation_id`, `cold_start` (formato JSON
  Powertools)
- **AC-2**: Given `common/ip_extractor.py`, When llamo
  `extract_ip(event)` con headers `{"CF-Connecting-IP": "1.2.3.4",
  "X-Forwarded-For": "5.6.7.8, 9.10.11.12"}`, Then retorna `"1.2.3.4"`
  (CF tiene prioridad)
- **AC-3**: Given `common/ulid.py`, When llamo `new_uuidv7()` 1000 veces
  en orden, Then los strings resultantes son lexicograficamente ordenados
  (UUIDv7 incluye timestamp en bits altos)
- **AC-4**: Given `common/validators.py`, When llamo
  `is_valid_email("user@example.com")`, Then retorna `True`; When llamo
  `is_valid_email("not-an-email")`, Then retorna `False`
- **AC-5**: Given `common/responses.py`, When llamo
  `json_response(200, {"ok": True}, origin="https://the-full-stack.com")`,
  Then retorna dict con `statusCode: 200`, `body: '{"ok":true}'`, y
  `headers["Access-Control-Allow-Origin"] = "https://the-full-stack.com"`
- **AC-6**: Given `common/ssm_client.py`, When llamo
  `get_secret("/portfolio/turnstile-secret")` warm Lambda, Then la
  segunda invocacion lee de cache Powertools (no llama SSM API)

## 4. Diagrama de Flujo

N/A — modulo helper sin flujo logico de negocio.

## 5. Diagrama ER

N/A — sin entidades nuevas.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN extract_ip recibe CF-Connecting-IP=1.2.3.4 THEN retorna "1.2.3.4" [AC-2]
- WHEN extract_ip recibe solo X-Forwarded-For="a, b, c" THEN retorna "a" [AC-2]
- WHEN new_uuidv7 se llama 2 veces seguidas THEN segundo > primero (string compare) [AC-3]
- WHEN is_valid_email("user@example.com") THEN True [AC-4]
- WHEN is_valid_email("@example.com") THEN False [AC-4]
- WHEN is_valid_email("user@") THEN False [AC-4]
- WHEN json_response(200, body, origin) THEN headers tienen CORS correcto [AC-5]

### 6.B. Unit Tests (pytest + moto)

Path mirroring `tests/unit/common/test_<X>.py`:

- `test_config.py` — settings carga desde env vars con tipos correctos
- `test_logger.py` — logger emite JSON con structure de Powertools
- `test_ip_extractor.py` — prioridades CF > XFF > requestContext
- `test_ulid.py` — orden temporal + uniqueness
- `test_validators.py` — email regex + sanitizers
- `test_responses.py` — shape API Gateway responses + CORS
- `test_ssm_client.py` — uso de moto para mock SSM + cache hit/miss

Coverage minimo: 90% per-file (modulo critico, todas las Lambdas dependen).

### 6.C. Typecheck

- `serverless typecheck --module-path=src/common` pasa con mypy --strict

## 7. Archivos Afectados

### Crear

- `serverless/src/common/__init__.py` — re-exports publicos
  - Verificar: `python -c "from common import logger, tracer, metrics"` no falla
- `serverless/src/common/config.py` — `Settings(BaseSettings)` Pydantic
  - Verificar: tests unitarios pasan, settings carga env vars correctamente
- `serverless/src/common/logger.py` — `logger = Logger(service=...)`
  - Verificar: AC-1
- `serverless/src/common/tracer.py` — `tracer = Tracer(service=...)`
  - Verificar: handler tagged con `@tracer.capture_lambda_handler` aparece en X-Ray
- `serverless/src/common/metrics.py` — `metrics = Metrics(namespace='portfolio')`
  - Verificar: invocacion emite EMF JSON parseable en logs
- `serverless/src/common/responses.py` — `json_response`, `text_response`, `error_response`
  - Verificar: AC-5 + tests unitarios
- `serverless/src/common/cors.py` — `WHITELIST_ORIGINS = [...6 subdomains...]`,
  `resolve_origin(event)`, `cors_headers(origin)`
  - Verificar: tests unitarios cubren los 6 subdominios + origenes invalidos
- `serverless/src/common/exceptions.py` — `ApplicationError`, `ValidationError`,
  `TurnstileError`, `RateLimitExceededError`, `IPBlacklistedError`
  - Verificar: `pytest tests/unit/common/test_exceptions.py` pasa
- `serverless/src/common/dynamodb_client.py` — `dynamodb = boto3.resource('dynamodb')` module scope
  - Verificar: import time < 50ms
- `serverless/src/common/ses_client.py` — `ses = boto3.client('sesv2')` module scope
- `serverless/src/common/ssm_client.py` — `get_secret(name)` con Powertools parameters cache
  - Verificar: AC-6 (cache hit en 2da llamada)
- `serverless/src/common/ip_extractor.py` — `extract_ip(event) -> str`
  - Verificar: AC-2 + tests unitarios cubren 5 escenarios (CF, XFF, fallback, malformado, IPv6)
- `serverless/src/common/ulid.py` — `new_uuidv7() -> str`
  - Verificar: AC-3
- `serverless/src/common/validators.py` — `is_valid_email`, `sanitize_text`, `is_valid_country`
  - Verificar: AC-4
- `serverless/src/common/types.py` — `LambdaEvent`, `LambdaContext`, `JsonResponse` TypedDicts

### Modificar

- `serverless/src/layers/common_python/requirements.txt` — agregar
  `aws-lambda-powertools[all]>=3.0`, `httpx>=0.27`, `pydantic>=2.5`

## 8. Descomposicion para Paralelizacion

Aplicable porque son 14 archivos. Paralelizable en 4 grupos:

| Task | Archivos | Paralelizable con |
|------|----------|-------------------|
| T1 | logger.py + tracer.py + metrics.py | T2, T3, T4 |
| T2 | responses.py + cors.py + types.py | T1, T3, T4 |
| T3 | dynamodb_client.py + ses_client.py + ssm_client.py | T1, T2, T4 |
| T4 | ip_extractor.py + ulid.py + validators.py + exceptions.py + config.py | T1, T2, T3 |

Cada task: tests unitarios + typecheck independiente.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-001 done (template SAM existe + Layer Powertools deployado)
- [ ] tests/unit/common/ scaffold creado con conftest.py + pytest.ini

### Definition of Done

- [ ] AC-1 a AC-6 cumplidos
- [ ] Coverage >= 90% per-file en `src/common/`
- [ ] mypy --strict pasa
- [ ] `ruff check` sin warnings
- [ ] Cada archivo < 200 lineas
- [ ] Docstrings BDD-style en funciones publicas
- [ ] Import time del modulo `common` < 100ms (medir con `python -X importtime`)
