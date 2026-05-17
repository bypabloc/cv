---
description: >
  Push de la rama actual, crea PR con gh, espera GitHub Actions, mergea
  con merge commit a la base (default dev) y deja al usuario en dev con el
  pull aplicado. Flujo end-to-end de cierre de feature.
argument-hint: "[base=dev] [--draft]"
---

# /push-pr-merge — push + PR + CI + merge + sync local

Argumento (`$ARGUMENTS`):

- Sin args: base = `dev`, no draft.
- `dev` o `master` o `release`: especifica base.
- `--draft`: crear como draft (NO se mergea automaticamente — se reporta y termina).

Ejemplos:

```text
/push-pr-merge
/push-pr-merge master
/push-pr-merge dev --draft
```

## Workflow

Sigue estos pasos en orden, sin pedir intervencion al usuario excepto si
hay un blocker insalvable.

### 1. Pre-checks

Verifica que las pre-condiciones se cumplen:

```bash
# Rama actual no es protegida
BRANCH=$(git symbolic-ref --short HEAD)
case "$BRANCH" in
  master|main|dev|release) echo "BLOCKER: estas en rama protegida $BRANCH"; exit 1 ;;
esac

# Working tree limpio (todos los commits aplicados antes de invocar el command)
test -z "$(git status --porcelain)" || { echo "BLOCKER: hay cambios sin commitear"; exit 1; }

# Hay commits que pushear (al menos uno por encima de la base)
BASE="${1:-dev}"
git fetch origin "$BASE" 2>&1
COMMITS=$(git log --oneline "origin/$BASE..HEAD" | wc -l)
test "$COMMITS" -gt 0 || { echo "BLOCKER: no hay commits nuevos vs origin/$BASE"; exit 1; }

# gh CLI disponible y autenticado
gh auth status >/dev/null 2>&1 || { echo "BLOCKER: gh CLI no autenticado. Corre 'gh auth login'"; exit 1; }
```

Si algun pre-check falla, detente y reporta. NO intentes auto-fix.

### 2. Push de la rama

```bash
git push -u origin "$BRANCH" 2>&1 | tail -30
```

El pre-push hook corre quality gates (Ruff, Biome, coverage, integration
tests). Si falla:

- Lee el output, identifica que paso fallo.
- Sugiere el comando para reproducir local (`SKIP_STEPS=... .git-hooks/pre-push`).
- Detente. NO uses `--no-verify`.

Si push pasa, anota el output `BRANCH -> BRANCH` confirmando el upstream.

### 3. Crear o actualizar PR

```bash
# Si ya existe PR para esta rama, no duplicar
EXISTING=$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number' 2>/dev/null)

if [ -n "$EXISTING" ]; then
  echo "PR #$EXISTING ya existe. Skip create."
  PR_NUMBER="$EXISTING"
else
  # Generar titulo desde el ultimo commit del branch
  TITLE=$(git log -1 --pretty=%s)

  # Body: enumerar commits + Como probar generico
  # Si la rama tiene multiples commits, listar todos en "Cambios"
  # Si los commits siguen Conventional Commits, parsear el scope para "Como probar"
  # IMPORTANTE: NUNCA incluir atribucion de IA (Co-Authored-By Claude, Generated with...)

  gh pr create --base "$BASE" --head "$BRANCH" \
    --title "$TITLE" \
    --body "<body generado, ver formato abajo>" \
    [--draft si aplica]
fi
```

Formato del body (4 secciones obligatorias del template del proyecto, ver
`.github/pull_request_template.md` y `.claude/rules/git-workflow.md`):

```markdown
## Problema

<descripcion del problema, enumerada si son varios>

## Solucion

<que se hizo, paralelo a Problema>

## Como probar

<pasos reproducibles, NO 'lo probe local'>

## TODO

<deuda pendiente fuera de scope, vacio si no aplica>
```

Si el cuerpo es complejo y los commits del branch tienen suficiente
contexto (mensajes Conventional Commits con bullets), parsearlos y armar
el body. Si la rama tiene >5 commits o son muy diversos, pedir al usuario
contexto adicional ANTES de crear el PR.

Reporta la URL del PR (`https://github.com/<owner>/<repo>/pull/N`).

### 4. Esperar GitHub Actions

```bash
# Espera unos segundos a que CI arranque
sleep 8

# Lista runs activos del branch
gh run list --branch "$BRANCH" --limit 5

# Watch el run de quality-gates (el principal del proyecto)
RUN_ID=$(gh run list --branch "$BRANCH" --workflow CI --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN_ID" --exit-status 2>&1 | tail -40
```

Si CI falla:

- `gh run view <run_id> --log-failed | tail -80` para ver el log del paso fallido.
- Identifica la causa (test fallido, lint, coverage). Sugiere fix concreto.
- NO mergees si CI falla. Detente y reporta.

Si CI pasa: continuar.

### 5. Verificar checks completos antes de merge

```bash
gh pr checks "$PR_NUMBER" 2>&1
```

Todos los checks deben estar `pass`. Si alguno esta `pending`, esperar.
Si alguno esta `fail`, detenerse.

### 6. Merge a la base

Si el PR es draft, NO mergees — reporta que esta listo para revision y termina.

Si NO es draft:

```bash
# Feature -> dev: merge commit + borrar la feature branch (es efimera).
# Promocion dev -> stage / stage -> main: merge commit SIN --delete-branch
# (las ramas de entorno son permanentes).
if [ "$BASE" = "stage" ] || [ "$BASE" = "main" ] || [ "$BASE" = "master" ]; then
  gh pr merge "$PR_NUMBER" --merge 2>&1 | tail -10
else
  gh pr merge "$PR_NUMBER" --merge --delete-branch 2>&1 | tail -10
fi
```

`--merge` (merge commit) preserva los SHAs y evita la divergencia entre
`dev`/`stage`/`main` — regla del proyecto en `.claude/rules/git-workflow.md`.
El proyecto es **merge-commit-only**: `--rebase` y `--squash` estan
deshabilitados en GitHub.

### 7. Switch a base + pull

```bash
git checkout "$BASE" 2>&1
git pull --rebase origin "$BASE" 2>&1 | tail -5

# Confirma que llegaron los commits
git log --oneline -5
git status
```

La branch local ya se elimino automaticamente con `--delete-branch` en
el merge. Si quedo colgante:

```bash
git branch -d "$BRANCH" 2>&1 || true
```

### 8. Reporte final

```markdown
## Push + PR + Merge completado

### PR
- Numero: #<N>
- URL: <url>
- Base: <base>
- Commits: <N>
- Estado final: MERGED / DRAFT / FAIL

### CI
- quality-gates: <status> (<duration>)
- clean: <status> (<duration>)

### Local
- Rama actual: <base>
- Sincronizado con origin/<base>: si/no
- Working tree: limpio/sucio

### Siguiente paso sugerido
- Si todo OK: "Listo para nueva feature."
- Si CI fallo: "Inspecciona <comando concreto>"
- Si draft: "Revisa el PR y mergea manualmente cuando este listo."
```

## Reglas

- NUNCA `git push --no-verify` (rompe quality gates del proyecto).
- NUNCA mergear sin CI verde. Si fuerza el merge, reportar que el usuario
  debe usar `gh pr merge --admin` manualmente.
- SIEMPRE mergear con `--merge` (merge commit). NUNCA `--rebase` ni
  `--squash`: el proyecto es merge-commit-only — el merge commit preserva
  los SHAs y evita la divergencia entre `dev`/`stage`/`main`
  (`.claude/rules/git-workflow.md`).
- NUNCA atribucion de IA en titulo, body, ni comentarios del PR (politica
  global, hook `prepare-commit-msg` la elimina si se cuela).
- NUNCA mergear si el PR es draft — solo reportar.
- Si gh CLI falla con MCP github disponible (`mcp__github__*`), usar
  fallback MCP. Si ambos fallan, detente y sugiere creacion manual.
- Time-box: maximo 10 minutos para CI watch. Si CI tarda mas, reportar
  timeout y dejar al usuario decidir.
- Idioma del reporte final: espanol, terminos tecnicos en ingles.

## Anti-patterns

- ❌ Crear PR antes de pushear (gh fallaria con upstream missing).
- ❌ Mergear sin esperar CI (puede romper la base).
- ❌ Hacer `--no-verify` en push para "saltarse" hooks lentos.
- ❌ Quedarse en la rama de feature tras el merge (debe terminar en `dev`).
- ❌ Inventar contenido para el body del PR sin leer los commits reales.
- ❌ Usar `gh pr merge --auto` (espera condiciones que pueden tardar
  horas; este command es sincrono).

## Cuando NO usar este command

- La rama no esta lista (faltan tests, hay TODO criticos pendientes).
  Usa `/ship` primero para cerrar la implementacion.
- Hay PR existente con conflictos vs base — resolver manualmente con rebase
  antes de invocar este command.
- La rama tiene cambios destructivos que requieren review humano explicito.
  Crear PR como draft (`/push-pr-merge dev --draft`) y dejar el merge para
  decision manual.
