# 06 — Encoders refactor (contact_form inline; tracking async-via-invoke)

[← 05 send_email](05-send-email-lambda.md) · [siguiente: 07 cv cache →](07-cv-cache.md)

> Fase 4. Quita `ASYNC_MODE` de los dos encoders y elimina el path SQS. **Las
> dos lambdas NO se tratan igual** (decisión basada en el diagnóstico de cold):
> `contact_form` → escritura **inline síncrona** (el usuario espera la respuesta
> del form igual); `tracking_pixel` → **async vía invoke Lambda** a un writer,
> SIN SQS, para **preservar su cold de 3.7s** (no toca Neon en el request).

## 6.1 `contact_form` — escritura inline + invoke send_email

### Estado actual
- `core/handler.py`: `success_status=202 if AppConfig.async_mode else 201`.
- `core/services/contact_service.py`: importa `shared.db.repository` (top) +
  `send_to_queue`. Path async (SQS) + path sync (Neon).
- `core/controllers/contact/create.py`: ramifica por `async_mode`.

### Cambios
- Eliminar el branch `async_mode`: queda SOLO el path sync (escribir Neon +
  invoke send_email). El handler responde **201** siempre.
- `contact_service.py`: quitar el import `send_to_queue`; agregar
  `from shared.aws.lambda_invoke import invoke_async`.
- Tras escribir el contacto, invocar `send_email` async (kind=contact).

### Por qué inline (y no async como tracking)
El form es de **baja frecuencia** y el usuario **espera la respuesta** (ve el
"gracias"). El INSERT pooled caliente es ~10-25ms; el cold paga el wake de Neon
(~1-5s) pero eso ocurre raras veces y el usuario tolera el envío de un form.
Mantener inline simplifica (sin segundo Lambda para contact).

### Flujo nuevo
```
POST /contact ─► contact_form
  1. rate-limit + Turnstile (igual que hoy)
  2. ensure_session_and_visit + insert_contact_idempotent  (Neon, sync)
  3. invoke_async(send_email, {kind=contact, to=owners, reply_to=visitor, data})
  4. 201 Created
```

## 6.2 `tracking_pixel` — async vía invoke (preserva el cold de 3.7s)

> **Decisión del usuario (no inline).** El diagnóstico probó que
> `tracking_pixel` es el más rápido (cold 3.7s) PRECISAMENTE porque NO toca Neon
> en el request. Pasarlo a inline heredaría el wake de Neon (~9s cold). Como es
> el Lambda de **mayor volumen** y es **fire-and-forget** (sendBeacon: el
> browser no espera), se mantiene async — pero SIN SQS.

### Estado actual
- `core/handler.py`: `success_status=202 if AppConfig.async_mode else 204`.
- `core/services/tracking_service.py`: deps Neon LAZY (`_ensure_db_deps`),
  path async → SQS, path sync → Neon.

### Cambios
- Eliminar el branch `async_mode` + el path SQS.
- El request path: rate-limit → `invoke_async(tracking_writer, evento)` → **202**.
  NO toca Neon, NO importa `shared.db` en el request → **el cold se mantiene en
  ~3.7s** (sólo boto3 + rate-limit, ya warmeado en INIT).
- `tracking_service.py`: quitar `send_to_queue`; reemplazar por
  `from shared.aws.lambda_invoke import invoke_async`. La escritura a Neon se
  MUEVE al nuevo `tracking_writer` (ver 6.3). Conservar el warmup boto3 +
  read-path del rate-limit en INIT (ya existe, es lo que da el 3.7s).
- Memoria: **se queda en 128 MB** (no carga `shared.db`). Sin regresión.

## 6.3 `tracking_writer` — el writer async (reconvertido del worker SQS)

`tracking_worker` (hoy consumer de SQS) se **reconvierte** a un Lambda
`trigger.type=direct` invocado por `invoke_async`. Su lógica de persistencia ya
existe (`tracking_worker/core/services/persistence.py:process_tracking_message`)
— sólo cambia el disparador (de SQS event a invoke payload directo).

### Cambios
- `manifest.yaml`: `trigger.type: direct` (quitar el trigger sqs + `uses.queues`).
- `handler.py`: recibir el payload directo `{operation, action, data}` (el mismo
  evento que tracking_pixel arma), en vez del `Records[]` de SQS.
- Conserva `shared.db` + warm_db en INIT (es el que toca Neon ahora; su cold no
  importa — es async, nadie espera).
- IAM: tracking_pixel gana `uses.invokes: [tracking_writer]`.

> Esto es el patrón "async sin SQS": el bus (SQS) se reemplaza por
> `InvocationType='Event'`. Pierde el retry/DLQ automático de SQS — aceptado
> (tracking es best-effort; un evento perdido no es crítico). Documentar el
> tradeoff en el manifest.

## 6.4 Reglas

- **SIEMPRE** la escritura inline (contact_form) y la del writer
  (tracking_writer) usan el endpoint pooled de Neon + `warm_db()` en INIT.
- **SIEMPRE** el invoke async (send_email, tracking_writer) es best-effort: si
  falla, log + métrica, NO rompe el 201/202.
- **SIEMPRE** `tracking_pixel` NO importa `shared.db` (queda en 128 MB).
- **NUNCA** reintroducir `ASYNC_MODE` ni SQS. **NUNCA** subir memoria de
  tracking_pixel (el writer carga Neon, no el pixel).

## Archivos afectados (fase 4)

### Crear
- tests del path inline único de contact_form + del invoke de tracking_pixel +
  del `tracking_writer` como invoke-target.

### Modificar
- `contact_form/core/{handler,services/contact_service,controllers/contact/create}.py`
  - Verificar: `serverless tests --type=unit --lambda=contact_form`
- `tracking_pixel/core/{handler,services/tracking_service}.py`
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel` (cold no
    peor que baseline; sigue 128 MB)
- `tracking_worker/` → `tracking_writer/` (manifest direct + handler payload)
  - Verificar: `serverless tests --type=unit --lambda=tracking_writer`

[← 05 send_email](05-send-email-lambda.md) · [siguiente: 07 cv cache →](07-cv-cache.md)
