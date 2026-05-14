# SPEC-006: Lambda `tracking_pixel`

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/src/tracking_pixel/`, `serverless/template.yaml`
**Dependencias**: SPEC-002, SPEC-003, SPEC-004
**Paralelizable con**: SPEC-005, SPEC-007

## 1. Contexto

Lambda menos critica: recibe POST /track desde el tracking pixel
(componente Astro client:idle), enriquece con CF headers + UA parsing,
aplica rate-limit (mas permisivo: 30 req/5min/IP) y persiste en
DynamoDB `tracking` con TTL +60d.

### Hallazgos de exploracion

- Flujo en `serverless/ARCHITECTURE.md` seccion 4 (POST /track)
- UA parsing puede ser costoso (regex grandes); cachear con @cached(24h)
- Country viene de CF-IPCountry header (gratis, sin lookup adicional)

## 2. Solucion propuesta

Crear `serverless/src/tracking_pixel/` con 6 archivos:

```text
tracking_pixel/
├── __init__.py
├── handler.py             # entry point
├── service.py             # enrichment + persist
├── enrichment.py          # CF headers + UA parsing (cached)
├── persistence.py         # save_tracking_event con TTL +60d
├── schemas.py             # Pydantic models input
└── requirements.txt
```

### Decisiones clave

- **Decision 1: Sin Turnstile validation** — el tracking pixel acepta
  invisible Turnstile token opt-in pero no requiere. Razon: tracking es
  best-effort, no critico, perder algunos eventos por usuarios con JS
  bloqueado es aceptable.
- **Decision 2: 204 No Content como response** — sin body. Mejor UX
  (cliente no necesita parse), menor latencia network.
- **Decision 3: UA parsing en Lambda warm via cached @decorator** —
  user-agents.io library en Python; cachear el resultado por UA hash
  (TTL 24h) reduce CPU.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given POST /track con payload valido (session_id, url,
  signals), When invoco, Then retorna 204 No Content con CORS headers
- **AC-2**: Given mismo IP haciendo 31 requests en 5min, When 31ra
  invocacion, Then retorna 429 con `Retry-After` header
- **AC-3**: Given POST /track valido, When inspecciono DynamoDB tabla
  `tracking`, Then existe item con `session_id`, `page_id` (UUIDv7),
  `url`, `path`, `referrer`, `utm_*`, `screen_res`, `viewport`,
  `device_type` (parsed from UA), `browser`, `os`, `lang`, `timezone`,
  `ip_address`, `country`, `expires_at = now + 60d`
- **AC-4**: Given header `CF-IPCountry: CL`, When invoco, Then row en
  DynamoDB tiene `country = "CL"`
- **AC-5**: Given mismo `User-Agent` consultado 2 veces, When invoco
  warm, Then segunda invocacion lee UA parsing de cache (no re-parse)

## 4. Diagrama de Flujo

Documentado en `serverless/ARCHITECTURE.md` seccion 4. Resumen del
handler:

```text
event POST /track
    |
    v
JSON Schema validator (max payload size, session_id format)
    |
    v
1. extract_ip(event)
2. check_or_raise(ip, '/track', country, turnstile_validated=False)
3. enrich(event)  -> CF headers + UA parsed (cached 24h)
4. save_tracking_event(enriched_payload, expires_at)
    |
    v
return 204 No Content + CORS
```

## 5. Diagrama ER

Tabla `tracking` documentada en `serverless/ARCHITECTURE.md` seccion 6.
Sin cambios.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN payload valido THEN 204 + row persistida [AC-1, AC-3]
- WHEN 31 requests THEN 31ra = 429 [AC-2]
- WHEN CF-IPCountry=CL THEN row.country = "CL" [AC-4]
- WHEN mismo UA 2 veces THEN segunda lee de cache [AC-5]

### 6.B. Unit Tests

Path mirror `tests/unit/tracking_pixel/test_<X>.py`:

- `test_handler.py` — handler con moto DynamoDB
- `test_service.py` — orquestacion
- `test_enrichment.py` — UA parsing + CF headers extraction
- `test_persistence.py` — put_item con TTL
- `test_schemas.py` — validacion de signals

Coverage minimo: 80% per-file (Lambda menos critica que contact_form).

## 7. Archivos Afectados

### Crear

- `serverless/src/tracking_pixel/handler.py`
- `serverless/src/tracking_pixel/service.py`
- `serverless/src/tracking_pixel/enrichment.py`
- `serverless/src/tracking_pixel/persistence.py`
- `serverless/src/tracking_pixel/schemas.py`
- `serverless/src/tracking_pixel/requirements.txt` — `user-agents>=2.2`
- `serverless/events/tracking_pixel_valid.json`
- `serverless/events/tracking_pixel_with_utm.json`
- `serverless/events/tracking_pixel_no_session.json`

### Modificar

- `serverless/template.yaml` — agregar `TrackingPixelFunction`:
  - Policies: DynamoDBWritePolicy tracking + rate-limit tables + cache
  - ReservedConcurrentExecutions: 20
  - MemorySize: 256, Timeout: 10
  - Events: TrackPost API
- `serverless/src/layers/common_python/requirements.txt` — agregar
  `user-agents>=2.2` para UA parsing

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | schemas.py + enrichment.py | — | T2 |
| T2 | persistence.py | — | T1 |
| T3 | service.py + handler.py | T1, T2 | — |
| T4 | template.yaml + deploy | T3 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-002, SPEC-003, SPEC-004 done

### Definition of Done

- [ ] AC-1 a AC-5 cumplidos
- [ ] Coverage >= 80% per-file
- [ ] sam local invoke con 3 events JSON pasa
- [ ] Smoke test: curl POST /track desde local contra dev stage
- [ ] Latencia cold start < 1s, warm < 200ms
- [ ] CloudWatch Logs sin errores
