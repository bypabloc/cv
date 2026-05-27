# Catálogo de secretos serverless (resources/secrets/)

> Plan para mover el catálogo hardcodeado de SSM Parameters
> (`devtools/serverless/{provisioner.py,secrets.py}`) a archivos YAML
> bajo `serverless/lambda/resources/secrets/`, alineados con el patrón
> existente (`dynamodb/`, `sqs/`, `api_gateway/`). `docker/env/server/.{stage}`
> sigue siendo la fuente de verdad del VALOR; el catálogo declara el MAPEO
> a SSM. `serverless deploy` publica del `.env` al SSM automáticamente.
> Hermetismo estricto: devtools nunca imprime ningún valor cargado.

## Estado

| Fase | Archivo | Estado |
|------|---------|--------|
| 1. Schema del YAML + parser | [02-schema-y-parser.md](02-schema-y-parser.md) | Pendiente |
| 2. Catálogo migrado (6 archivos) | [03-catalogo.md](03-catalogo.md) | Pendiente |
| 3. Sync `.env` -> SSM en `deploy` | [04-sync-deploy.md](04-sync-deploy.md) | Pendiente |
| 4. Modo `--stage=local` (fallback env vars) | [05-stage-local.md](05-stage-local.md) | Pendiente |
| 5. Comandos `secrets-status`, `setup-ssm`, `sync-secrets` | [06-comandos.md](06-comandos.md) | Pendiente |
| 6. No-leaking + hermetismo | [07-no-leaking.md](07-no-leaking.md) | Pendiente |
| 7. Documentación (rules + skill) | [08-docs.md](08-docs.md) | Pendiente |
| 8. Commits | [09-commits.md](09-commits.md) | Pendiente |
| 9. Paralelización con worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) | Pendiente |
| 10. Verificación E2E | [11-verificacion-e2e.md](11-verificacion-e2e.md) | Pendiente |

Detalle del contexto y la solución: [01-contexto-y-decision.md](01-contexto-y-decision.md).

## Decisiones no reabribles

1. **Todo a SSM** (no híbrido): toda variable declarada en
   `resources/secrets/<name>.yaml` se publica a SSM (no se inyecta como env
   var plana del Lambda). La Lambda lee SSM en runtime via `ssm:GetParameter`.
2. **`docker/env/server/.{stage}` es la fuente de verdad del VALOR**.
   El catálogo YAML es el MAPEO (key del .env -> path SSM -> env var del
   Lambda). devtools lee el `.env` LOCALMENTE durante `deploy` y publica los
   valores a SSM. Las Lambdas leen SSM en runtime.
3. **Solo `server/`** (no `client/`, no `dev-cli/`): el catálogo es
   exclusivo del backend serverless. `client/.{env}` sigue siendo build-time
   del frontend Astro (PUBLIC_*). `dev-cli/.{env}` queda local del CLI.
4. **Stages SSM: dev, stage, prod**. `local` NO publica a SSM y NO lee SSM:
   el Lambda en modo local (RIE o direct) recibe las env vars directo desde
   `docker/env/server/.local`.
5. **Archivos commiteados**: cada secreto en `resources/secrets/<name>.yaml`
   queda versionado (no contiene valores, solo el mapeo). Los `.env` con
   valores quedan gitignored (ya lo están). El `.example` se regenera
   desde el catálogo.
6. **Eliminar `_SECRETS` y `_SSM_PARAMETERS` hardcodeados**. Una sola fuente
   de verdad: los YAML.
7. **deploy hace sync automático**. `serverless deploy --stage=dev` publica
   a SSM como paso previo a actualizar la Lambda. Con `--skip-sync` para
   casos excepcionales.
8. **No-leaking estricto**: devtools NUNCA imprime el valor del secreto
   ni en stdout, stderr, logs, exception traceback, ni como argumento a
   subprocess (usar `--value file://...` o pasar via stdin). Tests
   automatizados verifican el invariante.
9. **NO rotar Neon** como parte del plan: el usuario confirma que la password
   no fue filtrada.
10. **Nombres cortos por compatibilidad**: el `manifest.yaml` de cada Lambda
    sigue declarando `secrets: [turnstile-secret, neon-url]`. Cero cambios
    en los manifest existentes.

## Reglas críticas (recordatorios)

- **SIEMPRE** `docker/env/server/.{stage}` queda como fuente del valor real.
- **SIEMPRE** el archivo YAML del catálogo se versiona; el .env no.
- **SIEMPRE** devtools imprime nombre + path + estado, NUNCA el valor.
- **NUNCA** pasar el valor del secreto como argumento de CLI visible en `ps`.
- **NUNCA** Claude/subagentes leen el `.env` directo (la excepción es
  devtools en ejecución automática, sin que el valor entre al contexto
  de Claude).
- **NUNCA** publicar a `/portfolio/local/*` (local NO usa SSM).

## Verify-before-done (matriz rápida)

| Cambio | Verificación |
|--------|---------------|
| Nuevo YAML en `resources/secrets/` | parser pasa, sync no falla con `.dev` |
| Cambio en parser | `pytest devtools/tests/serverless/test_secrets_catalog.py` |
| Cambio en `provisioner.py` (consume catálogo) | `serverless deploy --stage=dev --dry-run` |
| Cambio en hermetismo | test no-leaking en CI |

Cierre del plan: ver [11-verificacion-e2e.md](11-verificacion-e2e.md).

## Ciclo de vida

Esta carpeta es **efímera**. El último commit del PR la elimina con
`git rm -r docs/specs/serverless-secrets-catalog/`. Lo que sobrevive:

- `serverless/lambda/resources/secrets/*.yaml` (catálogo)
- `devtools/serverless/secrets_catalog.py` (parser)
- Cambios en `provisioner.py`, `lifecycle.py`, `secrets.py`
- Tests en `devtools/tests/serverless/`
- `.claude/rules/serverless-secrets.md` actualizada
- `.claude/rules/env-files.md` con la excepción documentada
