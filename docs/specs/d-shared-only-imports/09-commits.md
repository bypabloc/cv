# Seccion 9 — Commits

> Listado de commits incrementales en `feature/shared-only-imports` (desde
> `dev`). Cada commit deja el repo verde (lint + typecheck + tests del scope).
> Conventional Commits en espanol. Un solo PR final `feature/shared-only-imports`
> -> `dev`.

## Rama de trabajo

Antes del primer commit verificar la rama:

```bash
branch=$(git branch --show-current)
case "$branch" in
  dev|stage|main|master)
    git checkout dev && git pull --rebase origin dev
    git checkout -b feature/shared-only-imports
    ;;
  feature/shared-only-imports) ;;  # continuar
  *) echo "rama inesperada: $branch"; exit 1 ;;
esac
```

## Secuencia de commits

| # | Commit | Fase | Verificacion incremental |
|---|--------|------|--------------------------|
| 1 | `docs(specs): plan d-shared-only-imports` | Plan | sintaxis MD ok |
| 2 | `feat(shared/core): re-exporta pydantic con extra email-validator` | A | `lint-deps`, `compileall shared/core` |
| 3 | `feat(shared/db): re-exporta subset de SQLAlchemy via __init__` | B | `compileall shared/db`, `tests --shared` |
| 4 | `feat(shared/aws): agrega send_email helper y re-exporta TypeDeserializer` | C | `tests --shared` (incluye los 4 tests nuevos de Fase C) |
| 5 | `feat(shared/observability): re-exporta MetricUnit de Powertools` | D | `compileall shared/observability` |
| 6 | `refactor(cv): usa shared.core y shared.observability en lugar de imports directos` | E.1 | `tests --lambda=cv`, `lint-deps --lambda=cv` |
| 7 | `refactor(db): seed_service usa shared.db; handler/models usan shared.core + shared.observability` | E.2 | `tests --lambda=db`, `lint-deps --lambda=db` |
| 8 | `refactor(contact_form): usa shared.core (EmailStr), shared.aws.send_email y shared.observability` | E.3 | `tests --lambda=contact_form`, `lint-deps --lambda=contact_form` |
| 9 | `refactor(tracking_pixel): usa shared.core y shared.observability` | E.4 | `tests --lambda=tracking_pixel` |
| 10 | `refactor(stream_processor): usa shared.core, shared.aws.TypeDeserializer y shared.observability` | E.5 | `tests --lambda=stream_processor` |
| 11 | `feat(devtools/serverless): lint-deps escanea imports prohibidos en core/` | F | `test_runner --module=devtools`, `lint-deps` |
| 12 | `docs(claude): rule + skill + docs para shared-only imports en lambdas` | G | validacion `claude -p` con 5 prompts |
| 13 | `test(serverless): verificacion E2E del refactor shared-only imports` | Verif | bateria completa B.1-B.10 |

Total: **13 commits**.

## Regla por commit

- Cada commit corresponde a una sola fase del plan (o sub-fase de E).
- Cada commit deja:
  - `python -m compileall` verde para el scope tocado.
  - Tests del scope verdes (no necesariamente la suite completa hasta la
    verificacion E2E final).
  - `serverless lint-deps` verde despues de las fases relevantes (D-3 ya
    pasa; el check de imports recien empieza a aplicar desde commit 11).
- Cada commit es atomico y revisable: un cambio, un proposito.
- Mensajes en Conventional Commits espanol, sin atribucion de IA, sin
  emojis, subject <=70 caracteres.

## PR

Un solo PR `feature/shared-only-imports` -> `dev`. Title del PR:

```text
refactor(serverless): los services usan solo shared/ para deps externas
```

Body del PR:

```markdown
## Problema

Los `serverless/lambda/services/*/core/**/*.py` importaban directamente paquetes
externos (pydantic, sqlalchemy, boto3, aws-lambda-powertools): 14 ocurrencias.
El cierre transitivo de `shared/` los aporta, pero el contrato "todo via shared"
era solo documental — CI no detectaba la regresion.

## Solucion

Refactor en 7 fases (12 commits + verificacion E2E):

1. shared.core re-exporta pydantic (con extra email-validator).
2. shared.db re-exporta SQLAlchemy (select, func, pg_insert, Session).
3. shared.aws.ses agrega send_email helper; shared.aws.dynamodb_types nuevo
   con TypeDeserializer.
4. shared.observability re-exporta MetricUnit.
5. Migrar los 5 services (1 commit por service): cero imports directos en core/.
6. Extender serverless lint-deps con check de imports prohibidos en
   services/*/core/**/*.py.
7. .claude/rules/lambda-shared-imports.md + skill + docs como contrato
   permanente para Lambdas nuevos/existentes.

## Como probar

```bash
git fetch origin && git checkout feature/shared-only-imports
python devtools/run.py serverless lint-deps
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit  # los 5 lambdas
python devtools/run.py serverless deploy --lambda=db --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db --event=events/seed.json --aws-profile=tfs-dev
# counts esperados: 1 profile, 9 experiences, 6 projects, 11 certificates,
# 10 references, 2 awards, 3 education, 2 languages, 354 translations,
# 99 skills, 26 tech_tags, 36 niche_priorities

# validar la rule/skill nuevas
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "donde vive pydantic en el backend serverless del portfolio"
```

## TODO

(vacio — el plan se elimina en el ultimo commit; rule + skill + docs son
los artefactos permanentes)
```
