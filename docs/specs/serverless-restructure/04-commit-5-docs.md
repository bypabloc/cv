# Commit 5 — Docs, rules, skill, CLAUDE.md

> [Anterior: 03](03-commit-4-drop-db.md) | [README](README.md) |
> [Siguiente: 05](05-paralelizacion-worktrees.md)

## Objetivo

Actualizar toda la documentacion para reflejar la estructura
`serverless/lambda/`, el CLI unificado (`tests`/`run`) y la eliminacion
de los `db-*`.

## Archivos afectados

### Rules
- `.claude/rules/lambda-controller.md`
  - Estructura obligatoria: `serverless/lambda/services/<lambda>/`,
    `serverless/lambda/shared/`.
  - Seccion "Operacion con devtools": `tests --type` y `run --stage`
    en vez de `test-unit`/`run-local`/`invoke-remote`.
  - Tabla de anti-patrones: revisar referencias a `src/`.
- `.claude/rules/neon-management.md`
  - Toda la operacion `db-*` pasa a `run --lambda=db --event=...`.
  - Paths `serverless/shared/db/` -> `serverless/lambda/shared/db/`.
- `.claude/rules/python.md`
  - Referencias a `serverless/` y la estructura de paquetes.
- `.claude/rules/serverless-secrets.md`
  - Si se implemento el commit 3: documentar los SSM params nuevos
    (`/portfolio/{stage}/dynamodb/...`).

### Docs
- `.claude/docs/lambda-controller/` (6 capitulos) — estructura, comandos.
  Especialmente `06-devtools-operations.md` (todo el inventario de
  comandos).
- `.claude/docs/serverless-backend/` — modelo de stacks, paths.
  `04-deploy-operacion.md` cambia con el nuevo `deploy-resource`.

### Skill
- `.claude/skills/lambda-controller/SKILL.md`
  - Estructura, comandos, ejemplos.
  - VALIDAR tras el cambio con `claude -p` (regla
    `.claude/rules/claude-config-testing.md`): 5 angulos, prompts en
    espanol, web deshabilitada.

### CLAUDE.md (raiz del proyecto)
- Tabla "Arbol de conocimiento": entradas de serverless.
- Seccion de comandos devtools serverless: `tests`/`run`, sin `db-*`.
- Estructura del repo: `serverless/lambda/`.

## Verificacion

```bash
# Validar la skill (obligatorio, regla claude-config-testing.md)
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como ejecuto los tests unit de un lambda" 2>&1 | tail -40
# repetir con 5 angulos: tests, run local, deploy, drop db-*, estructura

# Markdown lint si aplica
pnpm exec biome check .claude/ docs/ 2>/dev/null || true
```

## Definition of Done

- [ ] `lambda-controller.md` + `neon-management.md` reflejan la
      estructura y el CLI nuevos.
- [ ] Los 6 capitulos de `.claude/docs/lambda-controller/` actualizados.
- [ ] `SKILL.md` actualizado y validado con `claude -p` (5/5 angulos).
- [ ] `CLAUDE.md` actualizado.
- [ ] Sin referencias a `serverless/src/`, `serverless/shared/`,
      `test-unit`, `run-local`, `db-migrate` en docs (salvo notas
      historicas explicitas).

---

[Anterior: 03](03-commit-4-drop-db.md) | [README](README.md) |
[Siguiente: 05](05-paralelizacion-worktrees.md)
