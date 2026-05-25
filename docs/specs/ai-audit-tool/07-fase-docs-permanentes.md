# 07 - Fase docs permanentes (entregada en commit 1)

> Esta fase YA esta entregada como parte del commit inicial de este
> plan. Documenta lo que el commit 1 incluye, para trazabilidad.

[< 06 CLI](06-fase-cli.md) | [08 Commits >](08-commits.md)

## Estado: COMPLETA (commit 1 del plan)

El commit 1 (`docs(specs): plan ai-audit-tool + rule + skill + docs`)
entrega los archivos `.claude/` permanentes que documentan el
contrato del script `devtools/ai_audit` ANTES de implementarlo.

## Archivos entregados

| Archivo | Proposito | Estado |
|---------|-----------|--------|
| `.claude/rules/ai-audit.md` | Rule activa: cuando/como usar el script, anti-patterns | entregado |
| `.claude/skills/ai-audit/SKILL.md` | Skill invocable `/ai-audit` con keywords ES/EN | entregado |
| `.claude/docs/ai-audit/README.md` | Indice navegable del knowledge tree | entregado |
| `.claude/docs/ai-audit/01-tools-evaluadas.md` | Detalle por tool: URL, auth, score, gotchas | entregado |
| `.claude/docs/ai-audit/02-auth-setup.md` | Como crear cuentas + Playwright storageState | entregado |
| `.claude/docs/ai-audit/03-arquitectura.md` | Estructura interna del paquete | entregado |
| `.claude/docs/ai-audit/04-troubleshooting.md` | Sintomas comunes + diagnostico | entregado |
| `docs/specs/ai-audit-tool/*` | El plan en si (efimero) | entregado |

## Por que el commit 1 trae rule + skill + docs

Decision explicita del usuario (decision 10 del plan, no-reabrible).
Razon: el contrato del script debe ser legible desde el momento que
empieza la implementacion para que cada fase produzca codigo que
cumpla el contrato documentado.

Riesgo: durante el periodo entre commit 1 y la implementacion
completa, un usuario podria leer la skill `/ai-audit` y tratar de
correr `python devtools/run.py ai_audit ...` que aun no existe.

Mitigacion: cada archivo `.claude/` tiene una seccion "Estado" al
tope apuntando al plan y aclarando que los comandos NO existen
todavia.

## Validacion del commit 1

Tras pushear el commit 1, validar:

```bash
# La skill se invoca y responde sobre el diseño
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como audito si the-full-stack.com esta preparado para crawlers de IA"
# Esperado: num_turns > 1 (skill invocada), respuesta describe
#           devtools/ai_audit + las 4 tools + storageState
```

Esto sigue la rule `.claude/rules/claude-config-testing.md` que
exige validar cada cambio de `.claude/*` con `claude -p`.

## Que NO esta en commit 1

- Codigo Python del paquete `devtools/ai_audit/*` — viene en commits
  2-N (fases 02-06).
- Dependencia `playwright` en `devtools/pyproject.toml` — viene en
  commit 2 (fase scaffold).
- Tests + fixtures HTML — viene en commits 2-N.
- Entradas en `.gitignore` para `tmp/ai-audit/` y
  `docker/env/dev-cli/ai-audit/` — viene en commit 2 (fase scaffold).

## Done

- [x] `.claude/rules/ai-audit.md` escrito y commiteado
- [x] `.claude/skills/ai-audit/SKILL.md` escrito y commiteado
- [x] `.claude/docs/ai-audit/*` 5 archivos escritos y commiteados
- [x] `docs/specs/ai-audit-tool/*` plan completo escrito y commiteado
- [ ] Validacion `claude -p` ejecutada tras push (responsabilidad del
      dev que ejecute el plan)

[< 06 CLI](06-fase-cli.md) | [08 Commits >](08-commits.md)
