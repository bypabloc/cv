# Sección 10 — Paralelización con git worktrees

> Define la base secuencial (commits que todos los worktrees necesitan)
> y las fases que se pueden ejecutar en paralelo. Límite: 5-7 agentes
> concurrentes (regla de `.claude/rules/plan-format.md`).

## Base secuencial (no paralelizable)

Los commits 1-3 son la BASE. Todo lo demás depende de ellos. Se hacen en
orden, en la rama principal `feature/serverless-secrets-catalog`:

| # | Commit | Por qué bloquea | Archivos clave |
|---|--------|------------------|-----------------|
| 1 | `docs(specs): plan del catalogo` | Define el contrato del plan | `docs/specs/serverless-secrets-catalog/` |
| 2 | `feat(devtools): parser secrets_catalog.py` | Los demás módulos lo importan | `devtools/serverless/secrets_catalog.py`, tests |
| 3 | `feat(serverless): 6 archivos del catalogo` | Datos que consumen los demás commits | `serverless/lambda/resources/secrets/*.yaml` |

A partir del commit 3 se puede paralelizar.

## Fases worktree-safe (paralelizables)

| Worktree | Fase | Commits | Archivos disjuntos |
|----------|------|---------|---------------------|
| WT-A: provisioner | 1 | #4 | `devtools/serverless/provisioner.py`, tests |
| WT-B: sync | 2 | #5, #11 | `devtools/serverless/secrets_sync.py`, hermetismo |
| WT-C: helper-lambda | 3 | #6 | `serverless/lambda/shared/aws/ssm/secret_resolver.py`, tests |
| WT-D: lambdas-refactor | 4 | #7 | `serverless/lambda/services/{contact_form,stream_processor,db}/core/services/` |
| WT-E: local-runtime | 5 | #8 | `devtools/serverless/local_runtime.py`, `local_runtime_secrets.py` |
| WT-F: comandos | 6 | #9 | `devtools/serverless/secrets_commands.py`, `main.py`, `flags.py`, `help.py` |
| WT-G: docs | 7 | #12, #13 | `.claude/rules/*.md`, `docker/env/server/.example` |

### Dependencias entre worktrees

```text
Base (#1, #2, #3) terminada
   |
   ├──> WT-A (#4 provisioner)        [independiente, lee Catalog]
   ├──> WT-B (#5 sync, #11 hermet)   [independiente, lee Catalog + .env]
   ├──> WT-C (#6 helper)             [independiente, lee env vars]
   ├──> WT-E (#8 local-runtime)      [depende de WT-C antes de mergear,
   │                                   pero codifica en paralelo OK]
   ├──> WT-F (#9 comandos)           [depende de WT-B para sync_secrets,
   │                                   pero independiente para status/validate]
   └──> WT-G (#12 docs)              [siempre paralelizable, no toca codigo]

   WT-D (#7 refactor lambdas)        [depende de WT-C MERGEADO]
   ↓
Cierre: #10, #14, #15 secuencial en la rama principal
```

WT-D NO puede empezar hasta que WT-C esté mergeado (necesita el helper
`get_secret` importado). Las demás pueden ir en paralelo desde el inicio.

## Lo que NO se paraleliza

- Commit #1 (plan): crea la carpeta `docs/specs/`. Debe estar antes.
- Commit #2 (parser): lo importan todos los demás módulos.
- Commit #3 (catálogo): datos que los demás consumen.
- Commit #10 (eliminar `_SSM_PARAMETERS` legacy): después de #9.
- Commit #14 (eliminar `_SECRETS` y refs): después de que TODOS los
  worktrees mergearon (es la limpieza final).
- Commit #15 (verificación E2E): siempre en último lugar, en la rama
  principal, sin worktree.

## Cómo lanzar cada worktree

```bash
# Desde la rama principal, despues del commit #3:
git checkout feature/serverless-secrets-catalog

# WT-A: provisioner
git worktree add ../portfolio-wt-provisioner -b wt/provisioner
cd ../portfolio-wt-provisioner
# ... agente trabaja, commitea, hace push
# Volver a la rama principal y mergear con merge commit:
cd ../portfolio
git merge --no-ff wt/provisioner

# WT-B: sync
git worktree add ../portfolio-wt-sync -b wt/sync
# ... etc

# Cleanup al final:
git worktree remove ../portfolio-wt-provisioner
git worktree remove ../portfolio-wt-sync
# ... etc
```

## Reglas de file exclusivity

Cada worktree toca un subset disjunto de archivos. Antes de lanzar un
worktree, verificar:

```bash
# Listar archivos que el worktree va a tocar
# y verificar que NO los toca otro worktree concurrente.
git ls-files | rg '^(devtools/serverless/provisioner|devtools/tests/serverless/test_provisioner)' \
  | sort
```

Conflicto potencial: WT-F (comandos) toca `devtools/serverless/main.py`,
que es CENTRAL. Si otro worktree necesita registrar un comando, esperar
a que WT-F mergee. Mitigación: WT-F va PRIMERO entre los paralelizables
si tiene dependencias.

## Sub-agentes recomendados

Cada worktree es candidato a un sub-agente especializado:

| Worktree | Sub-agente | Razón |
|----------|------------|-------|
| WT-A | `general-purpose` | Refactor con tests existentes |
| WT-B | `general-purpose` | Implementación + tests no-leaking |
| WT-C | `general-purpose` | Helper compartido + tests |
| WT-D | `general-purpose` | Refactor de 3 lambdas (lectura cuidadosa) |
| WT-E | `general-purpose` | Tocar local_runtime con cuidado |
| WT-F | `general-purpose` | Comandos CLI con flags |
| WT-G | `general-purpose` | Edición de markdown + validación claude -p |

Si se prefiere serializar (más simple, menos overhead), hacer todo en la
rama principal sin worktrees. Para 15 commits chicos, la paralelización
ahorra ~30% del tiempo total pero suma overhead de coordinación.

## Recomendación práctica

Para el portfolio (1 dev humano + Claude), serializar todo. La
paralelización es útil si se lanzan 3-4 sub-agentes en paralelo desde un
prompt; sino, es overhead innecesario. Mantener la estructura de
worktrees DOCUMENTADA acá como opción para acelerar si surge.
