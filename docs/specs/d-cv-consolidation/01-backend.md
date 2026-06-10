# 01 — Backend: Authorize en lambda_kit + fusion cv_admin -> cv

> [README](README.md) | [02-frontend](02-frontend.md) | [03-commits](03-commits-verificacion.md)

## Fase Authorize (shared/lambda_kit)

- `base_controller.py`: atributo de clase `required_permission: str | None
  = None`; setter module-global `set_permission_checker(fn)` (espejo de
  `set_app_config` — el kit NUNCA importa shared.auth/shared.db). En
  `run()`, ANTES de Preload: si `required_permission` es None -> no-op; si
  no hay checker -> `{is_valid: False, code: CONFIGURATION_MISSING}`; si
  hay -> `checker(permission, meta, action=<ClassName>)` que RAISEA
  `ApplicationError` (401/403/404) — propaga limpio por `run_controller`
  hasta el `except ApplicationError` de `http_handler` (metrica rejected).
  El subject retornado queda en `self.permission_subject` (AuthUser).
- `_meta` se lee de `self.event.get('_meta')` (dict CRUDO — validate aun
  no corrio).
- `http_dispatch.py`: `cors_origin` acepta ademas `dict[str, str]` keyed
  por operation (`{'cv': 'public', 'content': 'echo', 'publish': 'echo'}`).
- Tests espejo en `shared/tests/unit/shared/lambda_kit/`: no-op con None,
  CONFIGURATION_MISSING sin checker, corta antes de preload al rechazar,
  subject disponible, cors dict por operation.

## Fusion cv_admin -> cv

Mover TAL CUAL (ajustando imports `cv_admin` -> `cv` y endpoints
`'/cv-admin#...'` -> `'/cv#...'`):

- `controllers/content/` (21) + `controllers/publish/` (2) + su `_base.py`
  (pierde los pasos auth+admin de `execute()`: los reemplaza
  `required_permission = 'admin'`; el rate-limit QUEDA en execute — un 401
  no consume slot y el orden se preserva porque Authorize corre antes).
- `services/`: jwt_service, admin_guard, rate_limit_service,
  content_service, catalog_service, reorder_service, publish_service,
  `_errors.py` (coexiste con el ServiceError de cv_service: modulos
  distintos, sin cross-import).
- `models/`: `_common.py`, content.py, content_simple.py, publish.py; el
  `event.py` fusiona OPERATIONS={cv, content, publish} y fuerza la carga
  de los modelos In.
- `settings/config.py` del cv gana: jwt_secret/issuer/audience,
  jwt_blacklist_table_name, rate_limit_*, ErrorCode y LogMetricType del
  dominio admin.
- `handler.py` del cv: imports de modelos FK-target (incl.
  `shared.db.models.auth.user`), `set_permission_checker(...)` en cold
  start, cors dict por operation, POST aceptado.
- `manifest.yaml` del cv: `trigger.methods: [GET, POST]`; tables + cache
  rw, jwt-blacklist read, rate-limit-rules read, rate-limit-buckets rw;
  secrets + jwt-secret, admin-emails, github-deploy-token; env JWT_ISSUER/
  JWT_AUDIENCE; CORS_ALLOWED_ORIGINS + origin del admin; timeout 60,
  memory 1024 (piso).
- Tests de cv_admin (~70) migran a `services/cv/tests/` (imports +
  conftest fusionado); pyproject dev-group del cv gana freezegun y
  moto[dynamodb,ssm].
- El permission checker del cv: `core/services/permission_checker.py` que
  compone `require_active_user` + `require_admin_user` y se registra en el
  handler.

## get-all + sesion compartida (shared/db/cv_repository.py)

- Funciones de seccion ganan parametro `session: Session | None = None`
  (None -> abren la suya: back-compat con el seed y tests).
- `get_full_cv` abre UNA sesion y la comparte (AC-3, respuesta identica).
- Nueva `list_publications(...)` (la escritura ya existe; falta lectura) y
  `get_full_cv_admin(...)`: 10 secciones + publications en 1 sesion,
  shape = el de las lecturas publicas por seccion.
- `cv/services/cv_service.py`: `get_all_admin()` con
  `@cached(ttl=900, tags=['cv'])` (todo write invalida tag 'cv' ->
  coherente) + registro de la action `get-all` en controllers/content/.

## Devtools / referencias

- `rate_limit_cmds.py` `_VALID_ENDPOINTS`: `'/cv#content'`,
  `'/cv#publish.dispatch'`, `'/cv#publish.status'`.
- `e2e/flags.py` VALID_LAMBDAS sin `cv_admin`; tests devtools
  (`resolve.py` lista de lambdas, `test_describe.py`) actualizados.
- `resources/secrets/github-deploy-token.yaml`: consumed_by/tags -> cv.
- Docstrings que citan cv_admin (cv_write*, seed_service, github.py).

## Secuencia de cierre (no negociable)

1. Merge PR -> deploy-backend redeploya `cv` (POST + deployment nuevo del
   stage) y deploy-apps publica el admin con `/cv`.
2. Seed rate-limit `'/cv#...'` en dev (y prod, inerte hasta promocion).
3. E2E api + admin verdes contra dev.
4. `serverless destroy --lambda=cv_admin --stage=dev` (carpeta AUN viva) +
   `aws apigateway create-deployment` (deprovision no re-deploya el stage)
   + verificar `/cv-admin` muerto (AC-4).
5. Commit de seguimiento: `git rm -r serverless/lambda/services/cv_admin/`
   + limpiar state S3/local huerfano + rows rate-limit viejas.
