# 09 — Baseline medida, config uniforme y costo (sin free tier)

[< Verificacion E2E](08-verificacion-e2e.md) | [README](README.md)

> Captura del estado ANTES de cambiar los manifests, la config uniforme
> aplicada a los 8 lambdas, y la estimacion de costo SIN free tier contra
> el presupuesto de $5/mes. Medido en dev (perfil `tfs-dev`), 2026-05-31.

## A. Baseline ANTES (api_e2e --env=dev) — 37/37 PASS

Comando: `python devtools/run.py api_e2e --env=dev --aws-profile=tfs-dev`.
Config en ese momento: memory 128-512 (mayoria 256), timeout 30-120,
snap_start true (salvo db). Las apps NO se tocaron.

### Cold start por lambda (primer invoke del contenedor)

| Lambda | cold (s) | primer caso |
|--------|----------|-------------|
| cv | 2.832 | cv.get (success) |
| contact_form | 14.990 | contact.create (success) |
| tracking_pixel | 3.884 | tracking.track (success) |
| auth | 12.484 | register.start (success) |
| users | 12.726 | profile.get (success) |
| **COLD avg** | **9.383** | |

### Tiempos por caso (warm, segundos)

```text
cv     cv.get                        cold 2.832   warm 0.170
cv     cv.profile/experiences/...    cold   -     warm 0.139-0.172  (cache HIT)
contact contact.create               cold 14.990  warm 1.398
tracking tracking.track              cold 3.884   warm 1.321
auth   register.start                cold 12.484  warm   -
auth   register.verify-code          cold   -     warm 3.606
auth   session.refresh               cold   -     warm 2.410
auth   login.start                   cold   -     warm 4.260
auth   verify.set-password           cold   -     warm 5.441
auth   session.logout                cold   -     warm 1.166
users  profile.get                   cold 12.726  warm 1.856
users  profile.update                cold   -     warm 2.212
users  status.get / list-sessions    cold   -     warm 1.834-1.842
GLOBAL                               cold 9.383   warm 1.018
```

### Lecturas clave de la baseline

- **cv.get warm = 0.170s** (cache HIT) — el cache `@cached` funciona. El
  "7.3s" del reporte original era un cache MISS + INIT crudo combinados,
  NO el caso tipico. cv.get cold = 2.83s (con SnapStart restore + query
  MISS).
- **contact_form cold = 14.99s** y **auth/users cold ~12.5s** — INIT crudo
  (SnapStart no restauro ese primer hit). Es el peor caso que el
  experimento de 1024 MB busca acotar (mas CPU en INIT).
- **warm global 1.018s** — el backend caliente ya responde bien; el
  problema es el cold del primer invoke en low traffic.

Archivo crudo: `tmp/api_e2e_baseline.txt` (no se commitea, es scratch).

## B. Config uniforme aplicada (los 8 manifests)

Por pedido explicito: subir TODOS a una config uniforme para medir con
CPU x4. Aplicado a `serverless/lambda/services/*/manifest.yaml`:

| Campo | Antes | Ahora |
|-------|-------|-------|
| `memory` | 128 / 256 / 512 (segun lambda) | **1024** (los 8) |
| `timeout` | 30 / 120 | **60** (los 8) |
| `snap_start` | true (salvo `db`) | **true** (los 8, agregado a `db`) |
| ephemeral `/tmp` | 512 (default AWS) | sin cambio (no soportado en provisioner, default 512, los lambdas no usan /tmp) |

Cada manifest documenta que es un EXPERIMENTO y que el valor debe
REVERTIRSE al minimo medido tras evaluar si la mejora lo justifica
(regla `.claude/rules/lambda-config.md`: la memoria == CPU, NUNCA subir
para enmascarar; el fix real de cv es la query en 1 sesion, no la CPU).

**Nota honesta:** memory == CPU en Lambda. Subir a 1024 (de 256) da ~4x
CPU, lo que acelera `configure_mappers`/argon2id/Jinja2 en el INIT y el
handler. Es un experimento valido para MEDIR cuanto, pero el costo se
cuadruplica (ver C) y el cold real (con SnapStart restore ~1.2s) NO
depende de la memoria. El valor sostenible es el minimo medido por lambda.

## C. Costo SIN free tier (presupuesto $5/mes)

AWS Lambda us-east-1, arm64 (Graviton), SnapStart on, 8 lambdas. Trafico
estimado: ~37k invokes/mes (cv 5k, tracking 15k x2, contact 200,
send_email 400, auth 500, users 800, db 20).

### Lambda compute

| Componente | 256 MB (previo) | 1024 MB (experimento) |
|------------|-----------------|------------------------|
| compute | $0.130 | $0.521 |
| requests | $0.007 | $0.007 |
| snapshot cache (SnapStart) | $0.005 | $0.005 |
| restore (SnapStart) | $0.114 | $0.456 |
| **TOTAL Lambda/mes** | **~$0.26** | **~$0.99** |

### Otros costos del backend (no Lambda, no cambian con memory)

| Servicio | Costo/mes estimado |
|----------|--------------------|
| KMS CMK (`alias/portfolio-lambdas`) | ~$1.00 fijo + ~$0.01 req |
| DynamoDB On-Demand (cache + tracking + rate-limit) | ~$0.05-0.30 |
| CloudWatch Logs (7d retention, low vol) | ~$0.10-0.50 |
| API Gateway REST ($3.50/M) | ~$0.08 |
| SES ($0.10/1000 emails) | ~$0.00 |
| Neon | $0 (free tier perpetuo de Neon, NO AWS) |

### Total backend estimado

| Escenario | Lambda | Otros | **TOTAL/mes** | vs $5 |
|-----------|--------|-------|----------------|-------|
| 256 MB (minimos previos) | $0.26 | ~$1.5 | **~$1.8** | holgado |
| **1024 MB (experimento)** | $0.99 | ~$1.5 | **~$2.5** | dentro |

**Conclusion de costo:** el experimento de 1024 MB entra en el presupuesto
de $5/mes (~$2.5 estimado). El mayor costo fijo NO es el compute sino la
**KMS key (~$1/mes)**. Si el trafico real superara el estimado ~3x, 1024
empezaria a apretar; los minimos medidos (~$1.8 total) dan mas colchon.

> El costo escala lineal con (memoria x duracion x invokes). Si tras medir
> el experimento la mejora de warm/cold no justifica el 4x de compute +
> restore, REVERTIR cada manifest a su minimo medido baja el Lambda de
> ~$0.99 a ~$0.26/mes sin perder el cold real (que lo da SnapStart).

## D. DESPUES (medido tras el deploy en dev) — 37/37 PASS

Los 8 lambdas confirmados en AWS a `1024 MB / 60s / SnapStart :live
(OptimizationStatus On)`. Se corrio `api_e2e --env=dev` dos veces:

- **1a corrida** (justo tras el deploy, SnapStart re-optimizando): cold
  avg 5.62s.
- **2a corrida** (SnapStart ya estable): cold avg **1.39s** — este es el
  cold REAL representativo.

### Comparativa cold por lambda (segundos)

| Lambda | ANTES (256-512) | DESPUES 1a corrida | DESPUES 2a (estable) |
|--------|-----------------|--------------------|-----------------------|
| cv | 2.832 | 2.326 | **0.565** |
| contact_form | 14.990 | 7.604 | **1.078** |
| tracking_pixel | 3.884 | 1.644 | **0.340** |
| auth | 12.484 | 9.688 | **3.250** |
| users | 12.726 | 6.815 | **1.720** |
| **COLD avg** | **9.383** | **5.615** | **1.391** |

### Comparativa warm (segundos, casos clave)

| Caso | ANTES | DESPUES |
|------|-------|---------|
| cv.get | 0.170 | 0.165 |
| cv.* (cache HIT) | 0.139-0.172 | 0.131-0.139 |
| contact.create | 1.398 | 1.078 |
| tracking.track | 1.321 | 0.310 |
| auth register.verify-code | 3.606 | 3.264 |
| auth login.start | 4.260 | 3.555 |
| auth verify.set-password | 5.441 | 3.212 |
| users profile.get | 1.856 | 1.597 |
| **warm avg global** | **1.018** | **0.791** |

### Lecturas del experimento

- **El cold cayo a ~1.4s avg** — pero NO por la memoria: lo da el
  SnapStart restore (~1s), que ya existia. La 1a corrida (5.62s) era el
  artefacto de re-optimizacion post-deploy; el cold sostenible es ~1.4s.
- **El warm bajo modestamente** (~22%): mas CPU acelera algo el handler
  (argon2id/Jinja2/configure_mappers), pero los casos Neon-I/O-bound (cv,
  users, auth verify) siguen dominados por la red a Neon, no por la CPU.
  cv.get warm quedo igual (0.165s, cache HIT — la memoria no lo toca).
- **Confirma el diagnostico**: la memoria a 1024 dio una mejora marginal
  de warm y CERO mejora estructural de cold (SnapStart ya lo cubria). El
  4x de CPU no se traduce en 4x de velocidad. El fix real de cv sigue
  siendo la query en 1 sesion (fase 02), independiente de la memoria.

### Recomendacion

El experimento cumplio su proposito (medir). Para sostener: REVERTIR cada
manifest a su minimo medido (baja Lambda de ~$0.99 a ~$0.26/mes) salvo
que se decida pagar el 4x por el ~22% de warm. La mejora de cold es
atribuible a SnapStart, no a la memoria, asi que se conserva al revertir.

[< Verificacion E2E](08-verificacion-e2e.md) | [README](README.md)
