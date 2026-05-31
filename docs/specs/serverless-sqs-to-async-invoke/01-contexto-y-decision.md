# 01 — Contexto, diagnóstico y criterios de aceptación

[← README](README.md) · [siguiente: 02 fase 0 →](02-fase-0-medicion-coldstart.md)

## 1. Contexto / Problema

Dos problemas se atacan juntos porque tocan el mismo código:

### 1.A Latencia (la motivación real del usuario)

El reporte `api_e2e` mostró colds de 9-14s (cv 13.9s, auth 11.3s, contact_form
9.8s, users 8.5s, tracking_pixel 3.7s). El usuario pidió reducirlos con lazy
imports, **sin subir memoria**.

### 1.B Complejidad de infra (SQS encoder+worker)

| Cola | Productor | Worker | Trabajo |
|------|-----------|--------|---------|
| `portfolio-auth-email-${stage}` | `auth` + `users` | `auth_email_worker` | render template + SES + audit |
| `portfolio-contact-form-${stage}` | `contact_form` | `contact_worker` | persistir contacto (Neon) + email owner |
| `portfolio-tracking-events-${stage}` | `tracking_pixel` | `tracking_worker` | persistir tracking event (Neon) |

Más: el feature flag `ASYNC_MODE` (mantiene vivo un path sync legacy
duplicado), templates de email hardcodeados en cada worker (mustache-lite
casero), y el Lambda `stream_processor` (consume DynamoDB Streams en stage/prod
— ver §1.D).

### 1.C Diagnóstico de latencia con DATOS DUROS (CloudWatch en vivo, dev)

Medido directo (no estimado) — corrige la hipótesis de "lazy imports":

| Lambda | Restore (Init+imports) | Handler COLD | Handler WARM | Lectura |
|--------|----------------------:|-------------:|-------------:|---------|
| cv | **1.24-1.38s** | 10.1s | **7.3s** | el warm 7.3s = query fan-out 11 secciones |
| auth | **1.20s** | 6.9s | 4.2s | Neon + argon2id en login-con-password |
| users | **0.90s** | 7.4s | 0.19s | cold = Neon wake; warm trivial |
| contact_form | (snapshot) | — | 0.5s | warm 0.5s → casi todo el cold es Neon wake |
| tracking_pixel | 3.0s init (sin Neon) | — | 0.3s | el mejor; no toca Neon en el request |

Fuentes: `RESTORE_REPORT`/`REPORT` de CloudWatch + `get-function-configuration
--qualifier live` (todos `OptimizationStatus: On`). Detalle:
`tmp/cold-start-analysis/08-diagnostico-final-datos-duros.md`.

**Conclusiones (HECHO, no estimación):**

- **SnapStart YA restaura** → los imports están en el snapshot (Restore
  ~1s). El Init NO es el cuello.
- **Lazy imports: ROI ~nulo, riesgo de empeorar.** Sacar un import
  incondicional del module-scope lo saca del snapshot → se paga en el handler
  (CPU-starved). El lazy correcto (fido2/argon2 por acción via
  `import_controller`, `__init__` vacíos) ya está aplicado.
- **El cold de 2 dígitos = query lenta (cv) + wake de Neon scale-to-zero
  (~1-5s) + red del harness (~2.6s, no cuenta para el usuario real que entra
  por Cloudflare).**
- **NUNCA subir memoria**: el cuello es I/O (Neon), no CPU.

→ El foco se reorienta a: **(1) verificar SnapStart**, **(2) cache de cv para
no tocar Neon**, **(3) sacar el toque a Neon del path de tracking**, y de paso
los objetivos de simplicidad (−SQS, send_email, −ASYNC_MODE, −stream_processor).

### 1.D `stream_processor` SÍ existe (corrección al plan v1)

`aws lambda list-functions` confirma `portfolio-stream-processor-stage` y
`-prod` (no en dev), con Event Source Mappings a los DynamoDB Streams de
`portfolio-contacts-*` y `portfolio-tracking-*`. El plan v1 decía "nunca
existió" — FALSO. Eliminarlo es un `serverless destroy` real por stage + borrar
el ESM + las refs de código (ver [09](09-cleanup-stream-processor.md)).

### Hallazgos de investigación (2025-2026)

- **En Lambda NO hay async fire-and-forget en proceso**: el container se
  congela al `return`. Diferir trabajo exige un 2º invoke (otro Lambda) — sin
  bus si se usa `InvocationType='Event'`.
- INSERT a Neon pooled caliente ~10-25ms (imperceptible). El async NO se
  justifica por la escritura: se justifica (sólo en tracking) por **no pagar el
  wake de Neon en el request del usuario**.
- SnapStart es la palanca de imports y ya está activo; las conexiones TCP NO
  sobreviven el snapshot → reconectar post-restore (NullPool ya lo cubre +
  `after_restore` hook, ver [02](02-fase-0-medicion-coldstart.md)).

## 2. Solución propuesta

```
ANTES                                  DESPUÉS
─────                                  ───────
contact_form ─SQS→ contact_worker      contact_form: escribe Neon inline (sync)
                                                     + invoke(Event) send_email [owner]
tracking_pixel ─SQS→ tracking_worker   tracking_pixel ─invoke(Event)→ tracking_writer
                                                     (preserva su cold; no toca Neon)
auth/users ─SQS→ auth_email_worker     auth/users ─invoke(Event)→ send_email
cv → Neon (query 11 secciones)         cv → @cached DynamoDB (hit: no toca Neon)
stream_processor (DDB Streams)         ELIMINADO (destroy stage+prod)
```

### Decisiones clave

- **D1 — Fase 0 bloqueante**: medir SnapStart + descomponer el cold antes de
  refactorizar (no optimizar a ciegas).
- **D2 — cv `@cached` DynamoDB**: el read-only/estático no toca Neon en cache
  hit. Mayor impacto absoluto.
- **D3 — contact_form inline síncrono** + invoca `send_email` async siempre.
- **D4 — tracking_pixel async-via-invoke** a `tracking_writer` (reconvertido del
  worker SQS): preserva su cold de 3.7s, sin Neon en el request.
- **D5 — send_email puro**: DynamoDB (config) + S3 (template) + Jinja2 + SES.
- **D6 — eliminar ASYNC_MODE + SQS + stream_processor**.
- **D7 — provider-swappable**: `shared.aws.lambda_invoke` + `shared.templating`
  nuevos; `shared.aws.s3`/`ses`/`db`/`cache` reusados.
- **D8 — NUNCA subir memoria**; lazy imports NO es el foco.

### Inventario de kinds (10) → templates → callers

| kind | caller | recipient | template vars |
|------|--------|-----------|---------------|
| `register-magic-link` | auth | user | `verify_url`, `expires_in_min` |
| `login-magic-link` | auth | user | `verify_url`, `expires_in_min` |
| `password-reset` | auth | user | `verify_url`, `expires_in_min` |
| `email-change-verify` | users | user (nuevo) | `verify_url`, `expires_in_min` |
| `register-code` | auth | user | `code`, `expires_in_min` |
| `login-code` | auth | user | `code`, `expires_in_min` |
| `email-changed` | users | user (viejo) | `new_email` |
| `account-disabled` | users | user | `reason` |
| `account-deleted` | users | user | — |
| `contact` | contact_form | owner | `name`, `email`, `message`, `company`, `role`, `service_type`, `budget`, `timeline`, `niche` |

## 3. Criterios de aceptación (BDD)

### Cold start (NUEVOS — el foco)

- **AC-1**: Given el alias `:live` de los 5 Lambdas, When se consulta
  `get-function-configuration --qualifier live`, Then `SnapStart.ApplyOn ==
  PublishedVersions` y `OptimizationStatus == On`; y un cold real muestra
  `Restore Duration` (no `Init Duration`) en la REPORT line.
- **AC-2**: Given la Fase 0, When se descompone el cold de cada Lambda, Then
  queda documentado por Lambda el reparto Restore / Neon-wake / query con
  números de CloudWatch (no del roundtrip httpx).
- **AC-3**: Given `cv.get` con cache poblada, When se invoca, Then responde
  desde DynamoDB `@cached` SIN tocar Neon (Handler Duration warm < 0.5s,
  medido en CloudWatch) y el cold no paga wake de Neon en cache hit.
- **AC-4**: Given `cv.get` con cache miss, When se invoca, Then refresca de
  Neon (SWR) y repuebla la cache; el siguiente hit no toca Neon.
- **AC-5**: Given el refactor completo, When se re-mide en CloudWatch, Then
  NINGÚN manifest subió de memoria respecto al baseline de Fase 0.

### Arquitectura (objetivos previos)

- **AC-6**: Given un POST `/contact` válido, Then escribe el contacto a Neon
  síncrono, invoca `send_email` (`kind=contact`) async, responde 201.
- **AC-7**: Given un POST `/track` válido, Then `tracking_pixel` invoca async
  (`InvocationType='Event'`) a `tracking_writer` y responde 202 SIN tocar Neon
  en el request (preserva su cold ~3.7s).
- **AC-8**: Given `tracking_writer` recibe el evento async, Then escribe el
  tracking_event a Neon (UPSERT session+visit + INSERT idempotente + parse UA).
- **AC-9**: Given `send_email` recibe `{kind, to, data}`, Then lee
  `email-config[kind]`, descarga template html+txt de S3, renderiza Jinja2,
  envía SES.
- **AC-10**: Given un `kind` inexistente, Then `send_email` retorna error
  validación (1xxx) sin llamar SES.
- **AC-11**: Given un `core/**/*.py`, When `serverless lint-deps`, Then 0
  imports directos de `boto3`/`jinja2`/`sqlalchemy` — exit 0.
- **AC-12**: Given `uses.invokes: [send_email]`, Then IAM `lambda:InvokeFunction`
  scoped al ARN + env var `LAMBDA_SEND_EMAIL_FUNCTION_NAME`.
- **AC-13**: Given `uses.buckets: [{name, access:read}]`, Then IAM `s3:GetObject`
  scoped + env var `S3_<NAME>_BUCKET`.
- **AC-14**: Given el repo tras el refactor, When se busca `stream_processor`
  (fuera de `_archive/`), Then 0 referencias **y** el Lambda fue destruido en
  stage y prod (`list-functions` no lo lista).
- **AC-15**: Given el repo tras el refactor, When se busca SQS (`shared.queue`,
  `resources/sqs/`, `uses.queues`, `trigger.type==sqs`, `ASYNC_MODE`), Then 0
  referencias.
- **AC-16**: Given `auth`/`users` disparan email, Then invocan `send_email`
  async (NO SQS).
- **AC-17**: Given `auth` crea user / guarda code/magic-link, Then SIGUE
  escribiendo a Neon síncrono (sin cambios).
- **AC-18**: Given `infra_provision`, Then crea tabla `email-config` + bucket
  `portfolio-email-templates-${stage}`, publica ids a SSM, NO crea colas SQS.
- **AC-19**: Given el seed, Then los 20 templates + 10 filas `email-config`
  cargados.
- **AC-20**: Given `serverless tests --type=unit` (Lambdas + shared), Then
  verdes, coverage ≥80% per-file en archivos modificados; y el cierre shared de
  `send_email` NO incluye `shared.db`/sqlalchemy (es puro).

## 4. Diagrama de flujo

### Antes

```
POST /contact ─► contact_form (ASYNC_MODE?) ─► SQS ─► contact_worker ─► Neon+SES
POST /track   ─► tracking_pixel (ASYNC_MODE?) ─► SQS ─► tracking_worker ─► Neon
GET  /cv      ─► cv ─► Neon (11 queries)
DDB Streams   ─► stream_processor ─► Neon (analítica)
```

### Después

```
POST /contact ─► contact_form: rate-limit+Turnstile → Neon inline (sync)
                 → invoke(Event) send_email[contact] → 201
POST /track   ─► tracking_pixel: rate-limit → invoke(Event) tracking_writer → 202
                 (NO toca Neon en el request → cold ~3.7s preservado)
                 tracking_writer (async): Neon inline (UPSERT + INSERT + UA)
GET  /cv      ─► cv: @cached DynamoDB (hit: ~GetItem, NO Neon)
                 (miss: Neon + repuebla; SWR refresca en background)
auth/users    ─► Neon sync → invoke(Event) send_email[kind] → S3+SES
(stream_processor ELIMINADO)
```

## 5. Diagrama ER (DynamoDB `email-config` — NUEVO)

```
email-config (DynamoDB, PK=kind)
  kind          string  (PK)   -- 'contact', 'register-code', ...
  bucket        string         -- portfolio-email-templates-${stage}
  html_path     string         -- 'contact.html'
  txt_path      string         -- 'contact.txt'
  subject       string         -- Jinja2 ('Nuevo contacto de {{ name }}')
```

La cache de cv reutiliza la tabla `cache` existente (`shared/cache/`, ya
provisionada). Sin cambios en el schema Neon.

[← README](README.md) · [siguiente: 02 fase 0 →](02-fase-0-medicion-coldstart.md)
