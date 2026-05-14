# SPEC-007: Lambda `turnstile_validator`

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/turnstile_validator/`,
`serverless/template.yaml`
**Dependencias**: SPEC-002, SPEC-003
**Paralelizable con**: SPEC-005, SPEC-006

## 1. Contexto

Endpoint interno POST /validate-turnstile que valida un token contra
Cloudflare siteverify de forma centralizada. Util para futuro
(ej. webhook handlers que no tienen contact_form como host pero
necesitan validar Turnstile).

En MVP, contact_form valida internamente (sin invocar este endpoint).
Este endpoint queda disponible para extension futura.

### Hallazgos de exploracion

- Codigo de Turnstile siteverify ya documentado en
  `.claude/docs/cloudflare-turnstile/04-backend-validation-python.md`
- Reusa logica de `contact_form/turnstile.py` (SPEC-005) — extraer a
  common si la duplicacion es excesiva

## 2. Solucion propuesta

Crear `serverless/src/turnstile_validator/` con 4 archivos. Logica simple:
recibe token + opcional remote_ip, valida con Cloudflare, retorna JSON
con `success: bool` + metadata. Rate-limit aplicado: 5 req/min/IP
(mas restrictivo que /contact porque es endpoint interno).

```text
turnstile_validator/
├── __init__.py
├── handler.py
├── service.py          # POST a siteverify (reusa logica de contact_form/turnstile.py)
├── schemas.py
└── requirements.txt
```

### Decisiones clave

- **Decision 1: Endpoint publico pero rate-limited** — para no exponer
  a abuso. Considerar autenticacion en SPEC futura (API key o IAM auth).
- **Decision 2: Refactor turnstile validation a `common/turnstile/`** —
  si la duplicacion entre `contact_form/turnstile.py` y este es alta,
  extraer a `common/turnstile.py`. Decision concreta durante
  implementacion.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given POST /validate-turnstile con `cf_token` valido + opcional
  `remote_ip`, When invoco, Then retorna 200 con
  `{"valid": true, "hostname": "<domain>", "challenge_ts": "<iso>"}`
- **AC-2**: Given token invalido, When invoco, Then retorna 200 con
  `{"valid": false, "error_codes": ["..."]}` (NO 4XX porque no es
  error del cliente, es info de la validacion)
- **AC-3**: Given IP haciendo 6 invocaciones en 60s, When 6ta, Then
  retorna 429
- **AC-4**: Given body invalido (falta `cf_token`), When invoco, Then
  retorna 400 desde API GW request validator
- **AC-5**: Given Cloudflare API caida (timeout 10s), When invoco, Then
  retorna 503 con `{"error": "upstream_unavailable"}`

## 4. Diagrama de Flujo

```text
POST /validate-turnstile
    |
    v
JSON Schema validator (body shape)
    |
    v
1. extract_ip(event)
2. check_or_raise(ip, '/validate-turnstile', country)
3. validate_turnstile(token, remote_ip)
    |
    +-- success: true -> 200 {valid, hostname, challenge_ts}
    +-- success: false -> 200 {valid: false, error_codes}
    +-- timeout -> 503
    +-- network error -> 503
```

## 5. Diagrama ER

N/A — sin persistencia, solo HTTP.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN token valido THEN 200 + valid=true [AC-1]
- WHEN token invalido THEN 200 + valid=false [AC-2]
- WHEN 6 invocaciones THEN 6ta = 429 [AC-3]
- WHEN body sin cf_token THEN 400 desde API GW [AC-4]
- WHEN Cloudflare timeout THEN 503 [AC-5]

### 6.B. Unit Tests

Path mirror `tests/unit/turnstile_validator/test_<X>.py`:

- `test_handler.py` — handler con responses (httpx mock)
- `test_service.py` — siteverify call + error mapping

Coverage minimo: 85% per-file.

## 7. Archivos Afectados

### Crear

- `serverless/src/turnstile_validator/handler.py`
- `serverless/src/turnstile_validator/service.py`
- `serverless/src/turnstile_validator/schemas.py`
- `serverless/src/turnstile_validator/requirements.txt`
- `serverless/events/turnstile_validator_internal.json`

### Modificar

- `serverless/template.yaml` — agregar `TurnstileValidatorFunction`:
  - Policies: rate-limit tables + cache + ssm:GetParameter (turnstile-secret)
  - ReservedConcurrentExecutions: 10
  - Events: ValidateTurnstilePost API
- Posible refactor: `common/turnstile.py` si SPEC-005 + SPEC-007
  duplican significativamente

## 8. Descomposicion para Paralelizacion

Small spec, no requiere descomposicion.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-002, SPEC-003 done

### Definition of Done

- [ ] AC-1 a AC-5 cumplidos
- [ ] Coverage >= 85% per-file
- [ ] sam local invoke con event JSON pasa
- [ ] Latencia cold start < 1.5s, warm < 400ms (Turnstile siteverify
      domina la latencia)
