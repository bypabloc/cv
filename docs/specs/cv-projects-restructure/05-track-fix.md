# Fase 8: Fix del /track 403 en dev

## Diagnostico esperado

Causas posibles (en orden de probabilidad):

1. **IP del usuario en blacklist** (DynamoDB table
   `portfolio-rate-limit-rules-dev`, rule_key=`ip#<ip>`,
   kind=`ip_blacklist`).
2. **Country rule** con `action=block` para el pais del usuario.
3. **Frontend envia body invalido** (faltan campos requeridos como
   `session_id`, `event_id`); en realidad seria 400 pero el navegador
   puede mostrarlo como bloqueo.
4. **CORS pre-flight** mal configurado, pero el cors del tracking
   pixel ya es `*` (`cors_origin='public'` en handler.py).

## Pasos de diagnostico

```bash
# A) Identificar IP usada (con curl desde la maquina del dev)
curl -s https://api.dev.the-full-stack.com/track -X OPTIONS -v \
  | head -30

# B) Tail logs del lambda en dev
aws logs tail /aws/lambda/portfolio-tracking-pixel-dev \
  --since 30m --follow --region us-east-1 \
  --profile tfs-dev

# C) Reproducir un POST a /track con los headers tipicos del navegador
curl -X POST https://api.dev.the-full-stack.com/track \
  -H "Content-Type: application/json" \
  -H "Origin: https://generic.portfolio.dev.the-full-stack.com" \
  -d '{
    "operation": "tracking",
    "action": "track",
    "data": {
      "session_id": "00000000-0000-0000-0000-000000000000",
      "event_id": "11111111-1111-1111-1111-111111111111",
      "event_type_id": "22222222-2222-2222-2222-222222222222",
      "page_url": "https://generic.portfolio.dev.the-full-stack.com/",
      "event_props": {}
    }
  }' \
  -i

# Si responde 403: leer el body, debe traer code de la ApplicationError
# (IPBlacklistedError o CountryBlockedError)

# D) Si es blacklist: ver el rule en DynamoDB
aws dynamodb scan \
  --table-name portfolio-rate-limit-rules-dev \
  --filter-expression "kind = :k" \
  --expression-attribute-values '{":k":{"S":"ip_blacklist"}}' \
  --region us-east-1 \
  --profile tfs-dev
```

## Fix dependiente del diagnostico

### Caso 1 (probable): IP blacklisteada por testing previo

Si durante el desarrollo se envio 3+ veces el form /contact en 60s desde
la misma IP, el sistema de bot-detection auto-blacklisteo la IP por 24h
y ahora TODOS los endpoints (incluyendo /track) devuelven 403.

Comando de limpieza rapida (agregado en este plan):

```bash
# Listar todas las IPs blacklisted en dev
python devtools/run.py serverless rate-limit list --stage=dev \
  --aws-profile=tfs-dev

# Limpiar TODAS las blacklisted de una sola vez (DEV ONLY)
python devtools/run.py serverless rate-limit unblock-all --stage=dev \
  --confirm --aws-profile=tfs-dev

# O remover una IP especifica
python devtools/run.py serverless rate-limit unblock --ip=<MI_IP> \
  --stage=dev --aws-profile=tfs-dev

# Tambien limpiar los buckets (counters de sliding window) si la IP
# acumulo throttling y aun esta cerca del limite
python devtools/run.py serverless rate-limit clear-buckets --stage=dev \
  --confirm --aws-profile=tfs-dev
```

### Caso 2: Country block

Probablemente intencional. Verificar la tabla; si es por testing,
borrar el item del pais.

### Caso 3: Frontend body invalido

Mirar `packages/ui/src/components/TrackingPixel.astro` y
`packages/ui/src/lib/click-tracking.ts`. Verificar que TODOS los
eventos envien session_id, event_id, event_type_id con el formato
correcto (UUID v4 36-char).

### Caso 4: CORS pre-flight

Verificar `serverless/lambda/services/tracking_pixel/core/handler.py`
linea ~65 (`cors_origin='public'`). Si esta correcto, NO es CORS.

## Verificacion

```bash
# 1. POST a /track desde curl devuelve 204
curl -X POST https://api.dev.the-full-stack.com/track \
  -H "Content-Type: application/json" \
  -d '<body valido>' -i 2>&1 | head -20

# 2. En el navegador, abrir devtools network tab y verificar que las
#    requests del TrackingPixel devuelven 204
pnpm --filter @portfolio/generic run dev
# Navegar a http://localhost:9970 y verificar Network -> Filter "track"
```

## Si la causa es algo mas (escalar a investigacion)

Si despues de los pasos A-D no se identifica la causa, abrir un mini-doc
de investigacion en `docs/specs/track-403-debug.md` con los detalles y
seguir. NO declarar la fase como completa hasta que el endpoint
responda 204 a un POST valido.
