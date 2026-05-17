# Tracking de eventos + SES funcional

> Plan en dos fases para activar el envio de email del form de contacto y
> construir el sistema de tracking de eventos del portfolio (que ve el
> usuario, donde hace click, si llega a contacto). Consolida y reemplaza los
> specs del antiguo `serverless/specs/`.

## Contexto

El backend serverless tiene dos piezas a medio terminar:

1. **El email de `/contact` no llega.** El dominio `the-full-stack.com` ya
   esta verificado en SES y fuera de sandbox, asi que la causa NO es la
   verificacion. El bug real: `serverless/src/contact_form/service.py`
   envuelve `send_owner_email()` en un `try/except Exception` que silencia
   cualquier fallo. El contacto se guarda en DynamoDB (parece exito) pero el
   email falla sin dejar rastro. Causa mas probable dentro de ese except:
   los parametros SSM `/portfolio/ses-from-address` y `/portfolio/owner-email`
   no existen o estan mal seteados.

2. **`POST /track` nunca se invoca desde el frontend.** Los componentes
   `TrackingPixel.astro` y `CookieBanner.astro` existen en `packages/ui`
   pero estan huerfanos: no se exportan en el barrel ni se montan en ningun
   layout. El backend `tracking_pixel` esta deployado y operativo, pero
   nadie lo llama.

## Decisiones tomadas (interview previo)

| Tema | Decision |
| ------ | ---------- |
| Datos de origen en `contacts` | Quitar `ip`/`country`/`user_agent` de `contacts`; enlazar con `tracking_events` via `session_id` (sin duplicacion) |
| Identificador de evento | `event_id` lo genera el cliente (UUIDv4 por evento) -> idempotencia en reintentos de `sendBeacon` |
| Catalogo de tipos de evento | Tabla SQL `event_types` (PK UUIDv7, `code_name`, `description`). El frontend envia el `uuid` del tipo; el backend lo persiste como FK |
| UUIDs al cliente | Constantes fijas: seed en migration + modulo TS compartido. Cero requests extra |
| Eventos a mapear | page_load + navegacion, clicks, embudo de contacto, engagement |
| GDPR | `CookieBanner` incluido, tracking gated por consentimiento |
| Manejo de error de email | Visible pero no bloqueante: el contacto se guarda igual, un fallo emite metrica `OwnerEmailFailed` |
| Alcance | Por fases: Fase 1 entrega SES + page_load; Fase 2 el resto |

## Las dos fases

### Fase 1 — SES funcional + tracking page_load

Objetivo: el form de contacto envia email a los 2 correos personales del
owner, y cada carga de pagina de las 6 apps emite un evento `page_load`
identificado por `event_id`.

| Spec | Titulo | Objetivo |
| ------ | -------- | ---------- |
| [SPEC-100](SPEC-100-ses-funcional.md) | SES funcional + multi-destinatario | Arreglar el email de `/contact`: SSM params, lista de destinatarios, error visible |
| [SPEC-101](SPEC-101-catalogo-event-types.md) | Catalogo `event_types` | Tabla SQL catalogo + modulo TS de constantes (fuente unica de los tipos de evento) |
| [SPEC-102](SPEC-102-trackingpixel-page-load.md) | TrackingPixel `page_load` en 6 apps | Montar el pixel, enviar `event_id`+`event_type_id`, persistir en backend |

### Fase 2 — Mapa de eventos + GDPR + rediseno + hardening

Objetivo: mapear todos los eventos relevantes, el banner de consentimiento
real, desacoplar el schema de `contacts`, cerrar la documentacion operacional
y la deuda de tests del backend.

| Spec | Titulo | Objetivo |
| ------ | -------- | ---------- |
| [SPEC-200](SPEC-200-mapa-de-eventos.md) | Mapa de eventos: clicks, embudo, engagement | Seed del catalogo completo + emision de los eventos desde el frontend |
| [SPEC-201](SPEC-201-cookiebanner-gdpr.md) | CookieBanner + consentimiento GDPR | Montar el banner, gating real del tracking, cumplimiento EU |
| [SPEC-202](SPEC-202-rediseno-schema-contacts.md) | Rediseno schema `contacts` con `session_id` | Quitar datos de origen duplicados, enlazar con tracking por `session_id` |
| [SPEC-203](SPEC-203-runbook-observability.md) | RUNBOOK + observability + smoke test | Documentacion operacional del backend + smoke test post-deploy |
| [SPEC-204](SPEC-204-hardening-backend.md) | Hardening del backend | Deuda real verificada: tests faltantes + cache UA + limpieza `005` |

## Orden de ejecucion y dependencias

```text
Fase 1
  SPEC-100  ─────────────────────────┐  (independiente)
  SPEC-101  ──┬──────────────────────┤
              └──> SPEC-102          │
                                     v
                            merge dev -> stage -> main
                            (el usuario prueba el email)
Fase 2
  SPEC-200  (depende de SPEC-101 y SPEC-102)
  SPEC-201  (depende de SPEC-102)
  SPEC-202  (depende de SPEC-102; usa session_id ya emitido por el pixel)
  SPEC-203  (depende de Fase 1 desplegada y estable)
  SPEC-204  (depende de Fase 1; SPEC-102 toca los mismos archivos)
```

Fase 2 NO empieza hasta que Fase 1 este en `main` y el usuario confirme la
recepcion del email.

## Historial: migracion desde `serverless/specs/`

Este directorio reemplaza al antiguo `serverless/specs/`, que fue eliminado.
Aquel README marcaba todas las specs como `done`, pero el frontmatter de los
archivos individuales decia `draft` y la verificacion del codigo encontro que
varias estaban incompletas. Resultado de la verificacion:

| Spec antiguo | Tema | Estado real verificado | Destino |
| -------------- | ------ | ------------------------ | --------- |
| SPEC-000 | Setup inicial (AWS, SSM, Turnstile) | implementado | cerrado (done) |
| SPEC-001 | SAM template base + 3 tablas | implementado | cerrado (done) |
| SPEC-002 | Modulo `common/` | implementado | cerrado (done) |
| SPEC-003 | Cache module | implementado | cerrado (done) |
| SPEC-004 | Rate-limit module | implementado | cerrado (done) |
| SPEC-005 | Lambda `contact_form` | implementado | cerrado (done); el email lo arregla SPEC-100 |
| SPEC-006 | Lambda `tracking_pixel` | parcial: faltan tests + cache UA | deuda -> SPEC-204; extension -> SPEC-102 |
| SPEC-008 | Neon + migrations | parcial: migrations 003/004 nunca se hicieron | OBSOLETO (dashboard descartado): no se reimplementa |
| SPEC-009 | Lambda `stream_processor` | funciona; faltan tests | deuda de tests -> SPEC-204 |
| SPEC-011 | SES DNS production | la verificacion DNS ya ocurrio | cerrado (done) |
| SPEC-012 | Frontend contact form | implementado (`ContactFormReact.tsx`) | cerrado (done) |
| SPEC-013 | TrackingPixel + CookieBanner | componentes existen, no integrados | reemplazado por SPEC-102 + SPEC-201 |
| SPEC-015 | RUNBOOK + observability | nunca se hizo | -> SPEC-203 |

Specs ya descartadas en su momento (no existian archivos): SPEC-007
(`turnstile_validator` — la validacion vive en `common/turnstile.py`),
SPEC-010 (`aggregator` cron — alimentaba el dashboard), SPEC-014
(`dashboard_api` — el dashboard se descarto). Las migrations 003/004 de
SPEC-008 servian a SPEC-010/014; al estar descartadas, son obsoletas.

## Definition of Done — backend serverless (transversal)

Toda spec que toque codigo de `serverless/` debe cumplir, ademas de su DoD
propia:

- Tests pytest con coverage >= 80 % per-file
- `serverless lint` + `serverless format` + `serverless typecheck` pasan
- `serverless validate` (sam validate) pasa
- `serverless invoke` con event JSON ejemplar pasa local
- `serverless deploy --stage=dev` exitoso
- `serverless smoke --stage=dev` pasa
- CloudWatch Logs limpios en las primeras 10 invocaciones (sin `ERROR`)
- Documentacion actualizada (`ARCHITECTURE.md`, `RUNBOOK.md` si aplica)
- Conventional commits en espanol, sin atribucion de IA

Convenciones criticas del backend: Python 3.13 + arm64 (Graviton2), AWS
Powertools v3 (`@logger @tracer @metrics`), boto3 clients en module scope,
secrets via SSM Parameter Store (NUNCA env vars), IAM least privilege, tests
path mirror `src/X -> tests/unit/X`, BDD-style en docstring + AAA en cuerpo +
asserts EXACTOS.

## Convenciones (todas las specs)

- AC numerados en formato BDD `Given/When/Then` — fuente de verdad de tests
- Tests referencian AC entre corchetes `[AC-N]`
- Frontend Astro 6 + TS strict, Biome, Vitest, tokens del DS
- Migrations SQL: par `NNN_*.sql` + `NNN_*.down.sql`, probadas en branch Neon

## Navegacion

- [SPEC-100 — SES funcional](SPEC-100-ses-funcional.md)
- [SPEC-101 — Catalogo event_types](SPEC-101-catalogo-event-types.md)
- [SPEC-102 — TrackingPixel page_load](SPEC-102-trackingpixel-page-load.md)
- [SPEC-200 — Mapa de eventos](SPEC-200-mapa-de-eventos.md)
- [SPEC-201 — CookieBanner GDPR](SPEC-201-cookiebanner-gdpr.md)
- [SPEC-202 — Rediseno schema contacts](SPEC-202-rediseno-schema-contacts.md)
- [SPEC-203 — RUNBOOK observability](SPEC-203-runbook-observability.md)
- [SPEC-204 — Hardening backend](SPEC-204-hardening-backend.md)
