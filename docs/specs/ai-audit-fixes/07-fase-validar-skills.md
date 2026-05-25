# Fase 6 - Validar skills con claude -p

[< 06 app-shared JSON-LD](06-fase-app-shared-jsonld.md) | [08 Commits >](08-commits.md)

## Objetivo

Per `.claude/rules/claude-config-testing.md`: TODO cambio en
`.claude/*` debe validarse con `claude -p` antes de cerrar la
tarea. En commit anterior (fix isitagentready + tools nuevas)
modificamos:

- `.claude/rules/ai-audit.md` (3 tools nuevas, 5 descartadas)
- `.claude/skills/ai-audit/SKILL.md` (keywords nuevas)
- `.claude/docs/ai-audit/{README,01,02,03,04}.md` (estructura nueva)

Aplicar la matriz de 5 angulos.

## Cambios

NO modificamos archivos en esta fase. Solo EJECUTAMOS la
verificacion documentada en `claude-config-testing.md` y guardamos
los resultados.

## Matriz de prompts

Per la matriz oficial (5 angulos):

| # | Angulo | Prompt en espanol |
|---|--------|-------------------|
| 1 | General | "que tan preparado esta el portfolio para IA?" |
| 2 | Especifico | "como configuro la PSI_API_KEY para lighthouse_psi en el audit?" |
| 3 | Sintoma/error | "el audit dice SKIPPED en lighthouse_psi, que hago?" |
| 4 | Negativo | "como auditar el contraste de color con axe-core" (NO debe invocar ai-audit) |
| 5 | Trampa | "como uso ahrefs para auditar el portfolio?" (debe explicar que fue descartado) |

## Comando canonico

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "<prompt>" 2>&1 | jq '{num_turns, is_error, result_first_300: (.result[0:300])}'
```

## Criterios de aprobacion por prompt

| # | Esperado |
|---|----------|
| 1 | `num_turns > 1`. Result menciona las 3 tools actuales (isitagentready, validators, lighthouse_psi). |
| 2 | `num_turns > 1`. Result menciona Google Cloud Console + `docker/env/dev-cli/.{env}` + `PSI_API_KEY=`. |
| 3 | `num_turns > 1`. Result diagnostica que falta la PSI_API_KEY y linkea a Google Cloud Console. |
| 4 | `num_turns == 1` (skill NO se invoca). Si invoca, ajustar keywords del frontmatter. |
| 5 | `num_turns > 1`. Result explica que Ahrefs fue descartado en mayo 2026 y la razon ($500+/mes). |

## Salida esperada

Si un prompt falla:

1. Inspeccionar el `result`.
2. Editar `.claude/skills/ai-audit/SKILL.md` (description, keywords)
   o `.claude/rules/ai-audit.md` (contenido).
3. Re-correr el prompt.
4. Documentar en commit que se hizo el round-trip.

## Archivos afectados

NINGUNO en esta fase salvo (si necesario) ajuste de la
description/keywords del SKILL.md tras un fallo de prompt.

### (Posible) Modificar

- `.claude/skills/ai-audit/SKILL.md` (solo si un prompt falla)
- `.claude/rules/ai-audit.md` (solo si un prompt falla)

## Verificacion incremental

```bash
# Correr los 5 prompts en sequencia
for prompt in \
  "que tan preparado esta el portfolio para IA?" \
  "como configuro la PSI_API_KEY para lighthouse_psi en el audit?" \
  "el audit dice SKIPPED en lighthouse_psi, que hago?" \
  "como auditar el contraste de color con axe-core" \
  "como uso ahrefs para auditar el portfolio?"
do
  echo "=== $prompt ==="
  claude --permission-mode bypassPermissions \
    --disallowedTools "WebSearch" "WebFetch" \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    --output-format json \
    -p "$prompt" 2>&1 | jq -r '"num_turns=\(.num_turns) is_error=\(.is_error)"'
done
```

[< 06 app-shared JSON-LD](06-fase-app-shared-jsonld.md) | [08 Commits >](08-commits.md)
