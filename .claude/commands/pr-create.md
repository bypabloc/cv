---
description: >
  Crea un Pull Request en GitHub para la rama actual contra base (default
  dev), generando titulo y body automatico desde commits.
argument-hint: "[base=dev] [draft]"
---

# /pr-create — crea el PR via agente pr-creator

Argumento ($ARGUMENTS): opciones para el agente.

- Sin args: base = dev, no draft.
- `dev` o `master`: especifica base.
- `draft`: crear como draft.

Ejemplos:

```
/pr-create
/pr-create master
/pr-create dev draft
```

## Workflow

Invoca el agente `pr-creator` (ver `.claude/agents/pr-creator.md`).
El agente se encarga de:

1. Verificar pre-condiciones (rama no protegida, tree limpio, branch pusheada).
2. Reunir commits + diff vs base.
3. Generar titulo (Conventional Commits espanol) y body (Resumen / Cambios / Testing / Notas).
4. Ejecutar `gh pr create` o usar `mcp__github__create_pull_request`.
5. Si ya existe PR para la rama, actualiza el body en vez de duplicar.
6. Devuelve URL del PR + breakdown.

## Reglas

- NUNCA crear PR desde rama protegida.
- NUNCA atribucion IA en titulo o body.
- NUNCA mergear automaticamente — el merge es decision separada.
- Si el agente no tiene `gh` disponible y MCP github falla, reportar y
  sugerir crear PR manual con la plantilla generada.
