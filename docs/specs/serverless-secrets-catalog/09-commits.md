# Sección 9 — Commits

> Lista de commits incrementales del plan. Cada uno deja el repo verde
> (lint + typecheck + tests del scope) y cubre un objetivo coherente.
> Idioma: español, Conventional Commits. Sin atribución a IA.

## Orden y secuencia

| # | Tipo y mensaje | Cubre AC | Verificación incremental |
|---|----------------|----------|--------------------------|
| 1 | `docs(specs): plan del catalogo de secretos serverless` | — | `ls docs/specs/serverless-secrets-catalog/README.md` |
| 2 | `feat(devtools): agrega parser del catalogo en secrets_catalog.py` | AC-1, AC-2 | `pytest devtools/tests/serverless/test_secrets_catalog.py` |
| 3 | `feat(serverless): catalogo inicial de 6 secretos en resources/secrets/` | — | `python -c "from devtools.serverless.secrets_catalog import Catalog; Catalog.load()"` |
| 4 | `refactor(devtools): provisioner.py lee del catalogo y elimina _SECRETS` | AC-3, AC-11 | `pytest devtools/tests/serverless/test_provisioner.py` |
| 5 | `feat(devtools): sync automatico .env -> SSM en serverless deploy` | AC-4, AC-5, AC-6 | `pytest devtools/tests/serverless/test_secrets_sync.py` |
| 6 | `feat(serverless): helper get_secret en shared/aws/ssm/secret_resolver.py` | AC-7 | `pytest serverless/lambda/shared/tests/unit/aws/test_secret_resolver.py` |
| 7 | `refactor(lambdas): consumir get_secret en contact_form, stream_processor, db` | AC-7 | `serverless tests --type=unit --lambda=contact_form` (+ otros) |
| 8 | `feat(devtools): modo local sin SSM en local_runtime` | AC-7 | `serverless run --stage=local --lambda=contact_form --event=...` |
| 9 | `feat(devtools): comandos secrets-status, sync-secrets, validate-catalog` | AC-8, AC-9 | `pytest devtools/tests/serverless/test_secrets_commands.py` |
| 10 | `refactor(devtools): secrets.py setup-ssm consume catalogo, elimina _SSM_PARAMETERS` | AC-9, AC-11 | `serverless setup-ssm --name=turnstile-secret --stage=dev --help` |
| 11 | `feat(devtools): hermetismo en sync (tempfile + tests no-leaking)` | AC-10 | `pytest devtools/tests/serverless/test_no_leaking.py` |
| 12 | `docs(rules): actualiza serverless-secrets, env-files, neon-management con catalogo` | — | validacion claude -p |
| 13 | `docs(server): regenera docker/env/server/.example desde catalogo` | — | diff visual |
| 14 | `chore(serverless): elimina diccionarios _SECRETS y _SSM_PARAMETERS legacy` | AC-11 | grep no encuentra ocurrencias |
| 15 | `test(serverless): verificacion E2E iterativa + eliminacion de docs/specs/` | — | bateria E2E completa verde |

## Regla por commit

- Cada commit deja el repo verde (`pnpm exec biome check .` +
  `python devtools/run.py serverless tests --type=unit --lambda=devtools` o
  el subset correspondiente).
- Cada commit cubre al menos un AC y registra la verificación incremental
  en su body.
- El commit #1 crea la carpeta del plan; el #15 la elimina y consolida.

## PR único

Un solo PR `feature/serverless-secrets-catalog -> dev` con los 15 commits.

Título: `feat(serverless): catalogo YAML de secretos SSM en resources/secrets/`

Body siguiendo el template de `.claude/rules/git-workflow.md`:

```markdown
## Problema
1. Inventario de secretos SSM duplicado y hardcodeado en
   devtools/serverless/{provisioner.py, secrets.py}. Mantenimiento manual
   propenso a drift.
2. No hay nexo declarativo entre docker/env/server/.{env} y SSM. El dev
   tiene que ingresar el valor por stdin cuando ya esta en el .env.

## Solucion
1. Catalogo YAML en serverless/lambda/resources/secrets/<name>.yaml siguiendo
   el patron de dynamodb/, sqs/, api_gateway/. Una fuente de verdad para el
   inventario + el mapeo .env <-> SSM <-> Lambda.
2. serverless deploy sincroniza automaticamente desde el .env del stage a
   SSM (idempotente, hash-based). Comando standalone serverless sync-secrets.
   Hermetismo estricto: el valor nunca aparece en stdout, stderr o ps aux.
   Modo --stage=local sin SSM (env vars directas al runtime).

## Como probar
1. Catalogo: `python -c "from devtools.serverless.secrets_catalog import Catalog; print(sorted(Catalog.load().by_name))"` -> lista los 6 secretos.
2. Status: `python devtools/run.py serverless secrets-status --stage=dev --aws-profile=tfs-dev` -> tabla con .env / SSM / match.
3. Sync dry-run: `python devtools/run.py serverless sync-secrets --stage=dev --dry-run` -> lista PUSH/SKIP/MISSING.
4. Deploy: `python devtools/run.py serverless deploy --stage=dev --lambda=contact_form --aws-profile=tfs-dev` -> sync + deploy.
5. Local: `python devtools/run.py serverless run --stage=local --lambda=contact_form --event=events/sample.json` -> corre sin AWS.
6. Tests: `pytest devtools/tests/serverless/ -v` -> todos verdes (incluye test_no_leaking).

## TODO
- Decidir si AWS_STORAGE_BUCKET_NAME pasa al catalogo o queda inline.
- Decidir si las constantes (AWS_REGION, KMS_KEY_ALIAS, etc.) tambien
  pasan al catalogo (decision pendiente de tanda con usuario).
```

## Convenciones de los mensajes

- subject < 70 chars, imperativo, minusculas, sin punto
- body: bullets `-` con cambios concretos
- scope frecuente: `devtools`, `serverless`, `lambdas`, `rules`, `specs`
- Sin atribución IA en ningún commit ni en el PR body
