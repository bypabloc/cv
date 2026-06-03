# 03 — Bug 2: CORS falta `Authorization` (backend + reprovision)

[<- 02](02-bug-sesion-bootstrap.md) | [Bug 3 ->](04-bug-email-unificado.md)

Backend + infra. Redeploy Lambda + REPROVISION del API Gateway.

## Causa raiz (DOS lugares independientes)

1. **Respuestas del Lambda**: `serverless/lambda/shared/http/cors.py:165-167`
   — `Access-Control-Allow-Headers` sin `Authorization`.
2. **MOCK del OPTIONS (preflight)**: `devtools/serverless/provisioner.py:999`
   hardcodea `allowed_headers = 'Content-Type,X-Turnstile-Token,X-Turnstile-Bypass-Token'`.
   El OPTIONS es MOCK integration -> NO ejecuta el Lambda -> `cors.py` no
   aplica al preflight. Por eso cambiar solo `cors.py` NO arregla el preflight.

El admin manda `Authorization: Bearer <JWT>` a `/users` (todas las operations)
-> el browser bloquea el preflight. `/users` falla siempre; `/auth` falla en
sus endpoints autenticados.

## Diseno

Agregar `Authorization` en AMBOS strings (identicos):
- `cors.py:165-167`: `'Content-Type,Authorization,X-Turnstile-Token,X-Turnstile-Bypass-Token'`.
- `provisioner.py:999`: el mismo string.

`_wire_cors_options` es generico (una pasada cubre `/users`, `/auth`,
`/contact`, `/track`). Los `put-*` son idempotentes.

## Reprovision requerida

Redeploy del Lambda propaga el cambio de `cors.py` a las RESPUESTAS reales,
pero el PREFLIGHT lo sirve el MOCK -> hay que correr el provisioner (regenera
el integration-response del OPTIONS) + `create-deployment` del stage para que
tome efecto. Verificar con curl OPTIONS por env.

## Tests

- Doctest/test de `cors_headers` -> incluye `Authorization` [AC-5].
- Test del provisioner (`devtools/tests/unit/src/serverless/provisioner.py`)
  -> asserta `allowed_headers` con `Authorization` [AC-5].
- Verificacion manual post-deploy: `curl -X OPTIONS` /users y /auth en dev
  (ver fase 07, Parte C) [AC-6].

## Nota observada (no es scope, solo registro)

El OPTIONS devuelve `Access-Control-Allow-Origin: *` (no echo del origin). Es
seguro para requests sin credentials, pero contradice el comentario de
`cors.py` (que documenta echo + whitelist). El fix minimo de este bug es SOLO
agregar `Authorization`; no se cambia el `*`.
