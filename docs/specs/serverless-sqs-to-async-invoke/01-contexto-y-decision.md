# 01 — Contexto, solución y criterios de aceptación

[← README](README.md) · [siguiente: 02 shared foundations →](02-shared-foundations.md)

## 1. Contexto / Problema

El backend usa un patrón **encoder + worker** con 3 colas SQS:

| Cola | Productor | Worker | Trabajo |
|------|-----------|--------|---------|
| `portfolio-auth-email-${stage}` | `auth` + `users` | `auth_email_worker` | render template + SES + audit |
| `portfolio-contact-form-${stage}` | `contact_form` | `contact_worker` | persistir contacto (Neon) + email owner |
| `portfolio-tracking-events-${stage}` | `tracking_pixel` | `tracking_worker` | persistir tracking event (Neon) |

Problemas:

1. **Complejidad de infra**: 3 colas + 3 DLQ + 3 workers + Event Source
   Mappings + el feature flag `ASYNC_MODE` (que mantiene VIVO un path sync
   legacy duplicado en `contact_form` y `tracking_pixel`).
2. **Referencias muertas**: `stream_processor` se documenta en CLAUDE.md,
   devtools, docs y comentarios pero **NO existe** como Lambda.
3. **Email rígido**: templates hardcodeados en el `core/` de cada worker con
   un render mustache-lite casero. Sin config central de qué email se manda
   ni desde dónde; cambiar copy = redeploy del worker.

### Hallazgos de la investigación (2025-2026) sobre el cold start

Una investigación (4 fuentes 2025-2026) sobre "async en Lambda" concluyó:

- **En Lambda NO hay "async fire-and-forget en proceso"**: el container se
  congela al `return` del handler (doc oficial AWS). Diferir trabajo exige un
  segundo invoke (otro Lambda / self-invoke) o una Extension — no hay tercera
  vía sin un bus.
- **El delay real NO es la query**: un INSERT a Neon con conexión pooled
  caliente es **~10-25ms** (imperceptible). El cold start lo domina el
  **import** (sqlalchemy/psycopg) — y con **SnapStart** (ya activo) ese import
  está en el snapshot, así que el cold es el *restore* (~1s), constante.
- **Python 3.14 es irrelevante**: Lambda sólo ofrece runtime 3.13; forzar
  3.14 vía container **pierde SnapStart**. El no-GIL de 3.14 es CPU-bound, no
  I/O.
- **Driver**: psycopg3 (no asyncpg, no ORM en el write path). `gather` sólo
  ayuda con 2+ queries independientes (no aplica a estos encoders).
- **`tracking_pixel` usa `sendBeacon`**: el browser no espera la respuesta →
  la latencia server-side de escribir Neon **el usuario nunca la percibe**.

**Conclusión: NO desacoplar.** Escribir síncrono rápido. Esto elimina SQS
**y** evita crear `db_writer`. El cold start ya lo cubre SnapStart; este
refactor NO lo mejora (su valor es simplicidad + email flexible).

## 2. Solución propuesta

```
ANTES                                  DESPUÉS
─────                                  ───────
contact_form ─SQS→ contact_worker      contact_form: escribe Neon inline (sync)
                                                     + invoke(Event) send_email [owner]
tracking_pixel ─SQS→ tracking_worker   tracking_pixel: escribe Neon inline (sync)
auth/users ─SQS→ auth_email_worker     auth/users ─invoke(Event)→ send_email
```

### Decisiones clave

- **Decisión 1: persistencia inline síncrona** en `contact_form` y
  `tracking_pixel` (psycopg3 vía `shared.db`, endpoint pooled, `warm_db()` en
  INIT para SnapStart). NO se crea `db_writer`. NO async driver.
- **Decisión 2: email vía `send_email`** (Lambda `direct` invocado con
  `InvocationType='Event'`). Cero SQS.
- **Decisión 3: `send_email` puro** — DynamoDB (config) + S3 (template) +
  Jinja2 + SES. Config en `email-config` (PK=`kind`), una plantilla por kind.
- **Decisión 4: owner-email = `contact_form` invoca `send_email` siempre**
  (tras escribir el contacto). No idempotente.
- **Decisión 5: eliminar `ASYNC_MODE`** — un único path.
- **Decisión 6: provider-swappable** — `shared.aws.lambda_invoke` (nuevo),
  `shared.templating` (nuevo), `shared.aws.s3`/`ses`/`db` (existen).

### Inventario de kinds (10) → templates (10) → callers

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

- **AC-1**: Given un POST `/contact` válido, When el handler procesa, Then
  escribe el contacto a Neon **síncrono** (`ensure_session_and_visit` + INSERT
  idempotente), invoca `send_email` (`kind=contact`) async, y responde HTTP
  201 con el contacto persistido.
- **AC-2**: Given un POST `/track` válido, When el handler procesa, Then
  escribe el tracking_event a Neon **síncrono** (UPSERT session+visit + INSERT
  idempotente, con parse de user-agent) y responde HTTP 202.
- **AC-3**: Given `send_email` recibe `{kind, to, data}`, When ejecuta, Then
  lee `email-config[kind]`, descarga el template html+txt de S3, renderiza con
  Jinja2 y envía vía SES.
- **AC-4**: Given un `kind` que NO existe en `email-config`, When `send_email`
  ejecuta, Then retorna error de validación (code 1xxx) sin llamar SES.
- **AC-5**: Given un `core/**/*.py`, When `serverless lint-deps` corre, Then
  no hay imports directos de `boto3`/`jinja2`/`sqlalchemy` (sólo vía
  `shared.*`) — exit 0.
- **AC-6**: Given el manifest declara `uses.invokes: [send_email]`, When
  devtools provisiona, Then el rol IAM tiene `lambda:InvokeFunction` scoped al
  ARN de `portfolio-send-email-${stage}` + env var
  `LAMBDA_SEND_EMAIL_FUNCTION_NAME`.
- **AC-7**: Given el manifest declara `uses.buckets: [{name, access:read}]`,
  When devtools provisiona, Then el rol IAM tiene `s3:GetObject` scoped al ARN
  del bucket + env var `S3_<NAME>_BUCKET`.
- **AC-8**: Given el repo tras el refactor, When se busca `stream_processor`
  (fuera de `_archive/`), Then 0 referencias.
- **AC-9**: Given el repo tras el refactor, When se busca SQS (`shared.queue`,
  `resources/sqs/`, `*_worker`, `uses.queues`, `trigger.type==sqs`,
  `ASYNC_MODE`), Then 0 referencias.
- **AC-10**: Given `auth`/`users` disparan un email, When ejecutan, Then
  invocan `send_email` async (NO publican a SQS) y NO escriben audit
  email-level.
- **AC-11**: Given `auth` crea un user / guarda code/magic-link, When ejecuta,
  Then SIGUE escribiendo a Neon síncrono (sin cambios).
- **AC-12**: Given `send_email` para `kind=contact`, When ejecuta, Then `to`
  son los owner emails y `reply_to` el email del visitante.
- **AC-13**: Given `infra_provision`, When provisiona, Then crea la tabla
  `email-config` + el bucket `portfolio-email-templates-${stage}`, publica sus
  ids a SSM, y NO crea ninguna cola SQS.
- **AC-14**: Given el bucket recién creado, When se corre el seed, Then los 20
  templates + las 10 filas de `email-config` están cargados.
- **AC-15**: Given `serverless tests --type=unit` para los Lambdas + shared,
  Then todos verdes con coverage ≥80% per-file en archivos modificados.
- **AC-16**: Given el deploy de `send_email`, When devtools empaqueta, Then su
  cierre shared NO incluye `shared.db`/sqlalchemy (es puro, sin Neon).

## 4. Diagrama de flujo

### Antes

```
POST /contact ─► contact_form (ASYNC_MODE?)
                   ├─ true  ─► SQS ─► contact_worker ─► Neon + SES
                   └─ false ─► Neon + SES (sync legacy)
```

### Después

```
POST /contact ─► contact_form
                   ├─ rate-limit + Turnstile (igual)
                   ├─ escribe contacto a Neon (sync, ~10-25ms)
                   ├─ invoke(Event) send_email [kind=contact, owner]
                   └─ 201 con el contacto persistido

POST /track   ─► tracking_pixel
                   ├─ rate-limit (igual)
                   ├─ escribe tracking_event a Neon (sync; parse UA)
                   └─ 202 (sendBeacon ni espera)

auth/users    ─► (Neon sync) ─► invoke(Event) send_email [kind=...] ─► S3+SES
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

Sin cambios en el schema Neon (se reutilizan los repositories existentes).

[← README](README.md) · [siguiente: 02 shared foundations →](02-shared-foundations.md)
