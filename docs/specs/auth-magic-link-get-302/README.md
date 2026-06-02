# Magic link GET → 302 al admin (soporte multi-método en `/auth`)

> Plan efímero. Se elimina al mergear a `dev` (último commit). Trazabilidad
> queda en `git log` + el PR.

## Problema

El magic link del email apunta a un **GET** a
`api.portfolio.{env}.the-full-stack.com/auth?operation=...&action=verify-magic-link&token=XXX`,
pero el API Gateway de `/auth` solo tiene **POST** (+ OPTIONS) → el click
devuelve `403 {"message":"Missing Authentication Token"}` (error genérico de
API GW para método inexistente). El POST funciona (el admin lo usa por fetch).

## Solución (3 capas)

1. **devtools/provisioner**: soportar `trigger.methods: [GET, POST]` (lista),
   backward-compat con `trigger.method: POST` (string, otros 7 Lambdas).
2. **shared**: `redirect_response` 302; `http_handler` emite 302 cuando es
   éxito + método GET + `data.redirect_url`. POST sigue JSON.
3. **manifest del auth**: `methods: [GET, POST]`.

El `/callback` del admin (ya existente) lee el fragment hash y hace login.

## Decisión clave / riesgo

El statement de permiso del Lambda usa el mismo Sid (`apigw-{stage}[-live]`)
con SourceArn distinto (`POST/auth` viejo → `*/auth` nuevo).
`_cleanup_legacy_permissions` lo salta (mismo Sid) y `add-permission`
(`check=False`) no actualiza un Sid existente → el GET quedaría sin permiso.
**Fix**: `remove-permission --statement-id {sid}` (idempotente) ANTES del
`add-permission`.

## Commits

1. `feat(shared): agrega redirect_response 302 en http responses`
2. `feat(shared): http_handler emite 302 en GET con redirect_url`
3. `feat(devtools): soporta multiples metodos HTTP por trigger en el provisioner`
4. `feat(auth): habilita GET en el trigger /auth para el magic link`
5. verificación E2E + `git rm -r docs/specs/auth-magic-link-get-302/`

## AC

Ver el plan completo. Resumen: render multi-método (AC-1..4), wiring GET+POST
+ remove-permission (AC-5), 302 en GET (AC-6), POST JSON (AC-7), GET sin
redirect → JSON (AC-8), redirect_response shape (AC-9), E2E 302 real (AC-10).

## Verificación

```
ruff check devtools/serverless serverless/lambda/shared
python devtools/run.py test_runner --module=devtools --type=unit
python devtools/run.py serverless tests --type=coverage --shared
python devtools/run.py serverless lint-deps --shared
```

Parte C (post-merge): `serverless deploy --lambda=auth --stage=dev
--aws-profile=tfs-dev`; `aws apigateway get-resources` muestra GET; `curl` GET
al magic link real → 302 + Location admin/callback.
