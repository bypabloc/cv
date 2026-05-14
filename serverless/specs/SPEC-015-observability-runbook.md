# SPEC-015: RUNBOOK + DEPLOYMENT + smoke tests + AWS Billing Alarm

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/DEPLOYMENT.md`, `serverless/RUNBOOK.md`,
`serverless/scripts/smoke_test.sh`, AWS Billing
**Dependencias**: TODAS las anteriores (es el cierre del proyecto)
**Paralelizable con**: SPEC-014

## 1. Contexto

Documentacion operacional final + AWS Billing Alarm como UNICA alarma
del proyecto (gratis). Sin esto, el proyecto queda sin runbook para
incidentes y sin script para verificar despues de cada deploy.

### Hallazgos de exploracion

- `serverless/README.md` ya existe
- `serverless/ARCHITECTURE.md` y `serverless/INTEGRATION.md` cubren
  arquitectura y diseno
- Falta `DEPLOYMENT.md` (pasos primer deploy) y `RUNBOOK.md` (operacion)

## 2. Solucion propuesta

Crear 3 documentos + 1 script + AWS Billing Alarm configurada:

### `serverless/DEPLOYMENT.md`

Guia paso a paso del primer deploy:

1. Pre-requisitos (AWS CLI, SAM, uv, Cloudflare account)
2. Setup inicial (SPEC-000 + SPEC-011 ejecutados)
3. Deploy stages:
   - `serverless validate`
   - `serverless build`
   - `serverless deploy --stage=dev --guided`
   - `serverless db-migrate --stage=dev`
   - `serverless rate-limit set ...` (3 reglas iniciales)
   - `serverless smoke --stage=dev`
4. Configurar Turnstile widget hostnames
5. Verificar Email del owner llega
6. Deploy a prod (despues de testing en dev)

### `serverless/RUNBOOK.md`

Operaciones comunes + troubleshooting:

- Como rotar secrets (Turnstile, Neon URL, password dashboard)
- Como ver logs (`serverless logs -n <function> --tail`)
- Como ver metrics (`serverless metrics --since=24h`)
- Como manejar DLQ messages (StreamProcessorDLQ)
- Como agregar/quitar reglas rate-limit
- Como aplicar migrations PG sin downtime
- Como invalidar cache (tag global)
- Como rotar password del dashboard
- Como responder a un ataque DDoS sostenido (escalar reserved
  concurrency, considerar volver a WAF)
- Como verificar que cron aggregator corrio (mirar daily_metrics)
- Cuando llamar a Cloudflare support (DDoS L7 que no mate)

### `serverless/scripts/smoke_test.sh`

Bash script que ejecuta:
- curl OPTIONS preflight contra /contact (espera 200 + CORS)
- curl POST /contact con MOCK Turnstile token (mode dev) (espera 200)
- curl POST /track con session_id valido (espera 204)
- aws dynamodb scan contacts (espera al menos 1 row del test)
- psql contra Neon (espera row replicada del test)
- aws sesv2 describe email identity (espera "Verified")

### AWS Billing Alarm

Ya documentada en SPEC-000 AC-5. Validar que existe.

### Decisiones clave

- **Decision 1: Sin runbook PagerDuty/Opsgenie** — portfolio personal,
  no hay on-call rotation. Solo email a owner desde AWS Billing.
- **Decision 2: Smoke test ejecutable en CI futura** — script
  preparado para correrlo desde GitHub Actions cuando se agregue
  workflow deploy.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given `serverless/DEPLOYMENT.md` creado, When un desarrollador
  nuevo lo lee + ejecuta paso a paso, Then llega a un stack funcional
  en dev sin asistencia
- **AC-2**: Given `serverless/RUNBOOK.md` creado, When ocurre un
  incidente real (rate-limit triggered, DLQ message, alarma billing),
  Then el RUNBOOK tiene el procedimiento documentado
- **AC-3**: Given `smoke_test.sh` ejecutado contra stage dev, When
  pasa, Then exit code 0 + log JSON con verificaciones
- **AC-4**: Given billing alarm creada, When subo threshold a 0.01
  USD temporalmente, Then llega email en <6h
- **AC-5**: Given decision "no AWS::CloudWatch::Alarm", When inspecciono
  el stack final, Then `aws cloudwatch describe-alarms
  --alarm-name-prefix portfolio-` retorna 0 alarmas
  (excepto la billing global en us-east-1)

## 4. Diagrama de Flujo

N/A — documentacion + bash script.

## 5. Diagrama ER

N/A.

## 6. Tests Requeridos

### 6.E. Manual verification

- Ejecutar `smoke_test.sh` contra dev + prod
- Followup del DEPLOYMENT.md desde una VM limpia (o WSL nueva)
- Probar billing alarm con threshold $0.01

## 7. Archivos Afectados

### Crear

- `serverless/DEPLOYMENT.md` — guia primer deploy + screenshots
- `serverless/RUNBOOK.md` — operaciones + troubleshooting
- `serverless/scripts/smoke_test.sh` — smoke test bash
- `serverless/scripts/seed_test_contact.py` — helper para crear
  contacto de prueba en Dynamo (ya existe placeholder, completar)

### Modificar

- `serverless/README.md` — agregar links a DEPLOYMENT.md + RUNBOOK.md
  (ya existen como references en el indice actual)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | DEPLOYMENT.md | TODAS las specs | T2, T3 |
| T2 | RUNBOOK.md | TODAS las specs | T1, T3 |
| T3 | smoke_test.sh + seed_test_contact.py | TODAS | T1, T2 |
| T4 | Validacion manual de los 3 docs + script | T1, T2, T3 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] TODAS las specs anteriores done

### Definition of Done

- [ ] AC-1 a AC-5 cumplidos
- [ ] Smoke test pasa en dev y prod
- [ ] DEPLOYMENT.md validado siguiendolo desde scratch (puede ser
      por otro desarrollador o re-deploy completo en otra cuenta)
- [ ] RUNBOOK.md cubre los 10 escenarios mas frecuentes (rotar
      secrets, ver logs, manejar DLQ, etc.)
- [ ] AWS Billing Alarm responde a test
- [ ] `aws cloudwatch describe-alarms --alarm-name-prefix portfolio-`
      retorna 0 alarmas operacionales (solo billing global)
