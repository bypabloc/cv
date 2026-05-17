# SPEC-100: SES funcional + multi-destinatario

**Estado**: draft
**Fase**: 1
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/src/contact_form/`, `serverless/template.yaml`
**Dependencias**: ninguna
**Paralelizable con**: SPEC-101

> Anterior: [README](README.md) | Siguiente: [SPEC-101](SPEC-101-catalogo-event-types.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases, DoD del backend |
| `serverless/src/contact_form/notification.py` | Codigo actual del envio SES: `From`, `ToAddresses`, lectura de SSM |
| `serverless/src/contact_form/service.py` | El `try/except` que silencia el fallo de email (a corregir) |
| `serverless/src/contact_form/handler.py` | Como se usan `metrics` y `MetricUnit` (patron a replicar) |
| `serverless/template.yaml` | Bloque `ContactFormFunction` (se le agrega `AWS_SES_REGION`) |
| `serverless/tests/contact_form/` | Patron de tests pytest del backend; mock de SES con `moto` |

### Rules del proyecto aplicables

- `.claude/rules/python.md` + skill `python-devtools` — Python 3.13/3.14,
  interprete correcto, estilo, logging sin f-strings
- `.claude/rules/env-files.md` — NUNCA leer `.env`; extraer keys puntuales
- `.claude/rules/verify-before-done.md` — verificar antes de declarar listo
- skill `aws-ses` — SES v2, DKIM/SPF/DMARC, deliverability

### Decisiones del interview que aplican

- `owner-email` en SSM como lista CSV con los 2 correos del owner
  (`pacg1991@gmail.com`, `bypabloc@gmail.com`).
- El email es no-bloqueante pero VISIBLE: un fallo emite la metrica
  `OwnerEmailFailed`, el contacto se guarda igual, no se devuelve error al
  usuario.

## 1. Contexto

El form de contacto guarda el contacto en DynamoDB pero el email al owner no
llega. El dominio `the-full-stack.com` ya esta verificado en SES y fuera de
sandbox: la verificacion NO es la causa.

### Hallazgos de exploracion

- `serverless/src/contact_form/service.py` envuelve `send_owner_email()` en
  `try/except Exception` que solo hace `logger.exception()` y NO re-raise.
  Cualquier fallo de SES o de SSM queda invisible: no hay metrica, el usuario
  recibe `201` igual.
- `serverless/src/contact_form/notification.py` lee dos parametros SSM
  (`/portfolio/ses-from-address` y `/portfolio/owner-email`) via
  `get_parameter()`. Si no existen, lanza `ParameterNotFound` — atrapado y
  silenciado por el except de `service.py`. **Esta es la causa #1 sospechada.**
- `notification.py` envia a UN solo destinatario:
  `Destination={'ToAddresses': [owner_email]}`.
- `template.yaml` NO setea `AWS_SES_REGION`; `notification.py` defaultea a
  `us-east-1` (correcto, pero implicito y fragil).
- El `From` se arma como `"The Full Stack <{from_address}>"`. Si `from_address`
  no pertenece al dominio verificado, SES rechaza.

## 2. Solucion propuesta

Cuatro cambios acotados, todos en `contact_form/` + `template.yaml`:

1. **SSM params**: crear/corregir `/portfolio/ses-from-address` y
   `/portfolio/owner-email`. Este ultimo pasa a contener los dos correos
   personales del owner separados por coma.
2. **`notification.py`**: parsear `owner-email` como lista CSV — `split(',')`,
   `strip()` de cada item, descartar vacios — y pasar la lista completa a
   `Destination.ToAddresses`.
3. **`service.py`**: mantener el email no-bloqueante (el contacto se guarda
   aunque el email falle, no se pierde el lead) pero hacer el fallo VISIBLE:
   emitir la metrica CloudWatch `OwnerEmailFailed` ademas del `logger.exception`.
4. **`template.yaml`**: agregar `AWS_SES_REGION: us-east-1` explicito en el
   bloque `Environment.Variables` de `ContactFormFunction`.

### Decisiones clave

- **Decision 1: `owner-email` como lista en SSM** — cambiar destinatarios a
  futuro = editar el parametro SSM, sin redeploy del Lambda.
- **Decision 2: email visible pero no bloqueante** — el contacto se persiste
  siempre (no perder el lead aunque SES falle); el fallo se hace detectable
  con la metrica `OwnerEmailFailed`. Es el balance correcto para un email
  transaccional. NO se devuelve error al usuario por un fallo de email.
- **Decision 3: `AWS_SES_REGION` explicito** — elimina la dependencia del
  default de boto3, que podria leer otra region del entorno.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given los parametros SSM `/portfolio/ses-from-address` y
  `/portfolio/owner-email` creados, When se invoca `POST /contact` con datos
  validos, Then se envia un email via SES cuyo `Destination.ToAddresses`
  contiene `pacg1991@gmail.com` y `bypabloc@gmail.com`.
- **AC-2**: Given `owner-email = " a@x.com , b@y.com "`, When `notification.py`
  parsea el valor, Then `ToAddresses == ["a@x.com", "b@y.com"]` (trim de
  espacios aplicado).
- **AC-3**: Given `owner-email = "a@x.com,,b@y.com,"`, When se parsea, Then
  `ToAddresses == ["a@x.com", "b@y.com"]` (entradas vacias descartadas).
- **AC-4**: Given `send_owner_email()` lanza una excepcion, When se procesa el
  contacto, Then el contacto queda persistido en DynamoDB, se emite la metrica
  `OwnerEmailFailed` con value 1, se registra un `logger.exception`, y la
  respuesta HTTP al usuario sigue siendo `201`.
- **AC-5**: Given `send_owner_email()` tiene exito, When se procesa el
  contacto, Then NO se emite la metrica `OwnerEmailFailed`.
- **AC-6**: Given el `template.yaml` desplegado, When se inspecciona la config
  de `ContactFormFunction`, Then la variable de entorno `AWS_SES_REGION` tiene
  valor `us-east-1`.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
POST /contact -> contact_form
  save_contact -> DynamoDB  OK
  try: send_owner_email()        # 1 destinatario
  except Exception:
    logger.exception(...)        # fallo invisible: sin metrica
  return 201
```

### Despues

```text
POST /contact -> contact_form
  save_contact -> DynamoDB  OK
  try:
    send_owner_email()           # N destinatarios (CSV de SSM)
  except Exception:
    logger.exception(...)
    metrics.add_metric('OwnerEmailFailed', 1)   # fallo VISIBLE
  return 201                     # nunca bloquea por el email
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos.

## 6. Tests Requeridos

### 6.B. Unit Tests (pytest)

Path mirror en `serverless/tests/contact_form/`:

- `test_notification.py`:
  - `owner-email` con dos correos -> `ToAddresses` con dos entradas `[AC-1]`
  - valor con espacios -> trim aplicado `[AC-2]`
  - valor con entradas vacias -> descartadas `[AC-3]`
  - Mock de SES con `moto`; `create_email_identity` para `the-full-stack.com`.
- `test_service.py`:
  - `send_owner_email` mockeado para lanzar excepcion -> contacto persistido,
    metrica `OwnerEmailFailed=1`, sin re-raise, resultado normal `[AC-4]`
  - `send_owner_email` exitoso -> sin metrica `OwnerEmailFailed` `[AC-5]`
  - Verificar metrica con el capture de Powertools (`metrics` en test mode).

### 6.C. Typecheck

- Toolchain de `serverless/`: `serverless typecheck` sin errores.

## 7. Archivos Afectados

### Modificar

- `serverless/src/contact_form/notification.py` — funcion que resuelve
  destinatarios: leer `owner-email` de SSM, hacer `split(',')`, `strip()`,
  filtrar vacios; pasar la lista a `Destination.ToAddresses`. El `From`,
  templates y `ReplyToAddresses` quedan igual.
  - Por que: enviar a los dos correos del owner sin redeploy futuro.
  - Verificar: `serverless` test runner de `test_notification.py` verde.
- `serverless/src/contact_form/service.py` — en el `except Exception` que
  rodea `send_owner_email()`, agregar `metrics.add_metric(name='OwnerEmailFailed',
  unit=Count, value=1)`. Mantener el `logger.exception` y el NO re-raise.
  Importar `metrics` y `MetricUnit` (ya usados en `handler.py`).
  - Por que: un fallo de email hoy es invisible; con la metrica es detectable
    en CloudWatch sin romper la respuesta al usuario.
  - Verificar: `test_service.py` verde; `[AC-4]` y `[AC-5]` cubiertos.
- `serverless/template.yaml` — en `ContactFormFunction.Properties.Environment.
  Variables`, agregar `AWS_SES_REGION: us-east-1`.
  - Por que: hacer la region de SES explicita, no depender del default boto3.
  - Verificar: `serverless validate` (sam validate) sin errores.

### Acciones manuales (documentar en el PR, no son archivos)

- Verificar estado previo:
  - `aws ssm get-parameter --name /portfolio/owner-email --region us-east-1`
  - `aws ssm get-parameter --name /portfolio/ses-from-address --region us-east-1`
  - `aws sesv2 get-account --region us-east-1 --query 'ProductionAccessEnabled'`
  - `aws sesv2 list-email-identities --region us-east-1`
- Crear/actualizar los parametros:
  - `aws ssm put-parameter --name /portfolio/ses-from-address
    --value "no-reply@the-full-stack.com" --type String --overwrite
    --region us-east-1`
  - `aws ssm put-parameter --name /portfolio/owner-email
    --value "pacg1991@gmail.com,bypabloc@gmail.com" --type String --overwrite
    --region us-east-1`
- El `from-address` debe pertenecer a una identidad verificada en SES. Si
  `no-reply@the-full-stack.com` no esta como email identity y solo lo esta el
  dominio, el envio desde cualquier `@the-full-stack.com` funciona igual (la
  domain identity cubre todos los buzones).

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `notification.py` + `test_notification.py` | AC-1,2,3 | — | T2, T3 |
| T2 | `service.py` + `test_service.py` | AC-4,5 | — | T1, T3 |
| T3 | `template.yaml` | AC-6 | — | T1, T2 |
| T4 | SSM params (manual) | AC-1 | — | todas |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Confirmado que SES esta fuera de sandbox (`ProductionAccessEnabled=true`)
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-6 cubiertos por tests que pasan
- [ ] Coverage >= 80% per-file en `notification.py` y `service.py`
- [ ] `serverless lint`, `serverless format`, `serverless typecheck` pasan
- [ ] `serverless validate` pasa
- [ ] SSM params creados y verificados
- [ ] `serverless deploy --stage=dev` exitoso
- [ ] Smoke: `POST /contact` real en dev -> email llega a ambos correos
- [ ] CloudWatch Logs sin `ERROR` en las primeras invocaciones

> Anterior: [README](README.md) | Siguiente: [SPEC-101](SPEC-101-catalogo-event-types.md)
