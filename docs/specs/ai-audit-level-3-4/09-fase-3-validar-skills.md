# 09 — Fase 3: Validar skills + rules con `claude -p`

> **Anterior**: [08-fase-2c-mcp-server-card.md](08-fase-2c-mcp-server-card.md) · **Siguiente**: [10-commits.md](10-commits.md)
>
> **Objetivo**: actualizar la rule `.claude/rules/ai-audit.md` con la
> decision de NO implementar OAuth checks, documentar el flujo del MCP
> server, y validar con `claude -p` que las skills/rules siguen
> respondiendo correctamente.

## Estrategia

Tres pasos:

1. Actualizar `.claude/rules/ai-audit.md`: agregar seccion "Decisiones
   de scope" que documenta que OAuth checks NO se implementan + el
   ceiling intencional del score.
2. Crear/actualizar skill `mcp-server` (o agregar al `ai-audit` existente)
   con info del endpoint MCP del portfolio + tools disponibles.
3. Validar con `claude -p` siguiendo `.claude/rules/claude-config-testing.md`
   (matriz 5 prompts en espanol, sin web).

## Tarea 3.1 — Actualizar `.claude/rules/ai-audit.md`

Agregar nueva seccion al final:

```markdown
## Ceiling intencional del score isitagentready

El portfolio NO implementa estos checks por decision arquitectonica:

- `/.well-known/openid-configuration` — el portfolio NO tiene auth real.
  Publicar un stub OAuth es anti-pattern y confunde a los agentes.
  Joost.blog (83/100 = Level 5) deliberadamente rechaza este check por la
  misma razon. Aceptar la penalizacion intencional es correcto.
- `/.well-known/oauth-protected-resource` — idem. Turnstile CAPTCHA del
  Lambda de contacto no es OAuth standard.

**Ceiling esperado**: isitagentready 3-4/5 (no 5/5). El plan
`docs/specs/ai-audit-level-3-4/` documenta como llegamos hasta ahi.

## MCP server endpoint

El portfolio expone un MCP server en cada niche (`/mcp` via Cloudflare
Pages Function). Tools disponibles:

- `get_cv_section(section)` — devuelve seccion del CV en Markdown
- `list_projects(tech_stack?)` — lista proyectos filtrados
- `search_experience(keyword)` — busca en experiencias

Server card publico: `/.well-known/mcp/server-card.json`.

**SIEMPRE** ANTES de extender el MCP server, leer la decision de scope:
3 tools fijas, sin auth, JSON-RPC sobre HTTP transport. Cualquier tool
nueva requiere justificacion + actualizar el server card builder en
`packages/seo/src/lib/build-mcp-server-card.ts`.
```

## Tarea 3.2 — Crear skill `mcp-server` (opcional, ver decision)

Decision: NO crear una skill separada. La rule `ai-audit.md` ya cubre
el MCP server. Si en el futuro se extiende a >5 tools o se agregan
resources/prompts, separar entonces.

## Tarea 3.3 — Validacion con `claude -p` (matriz 5 prompts)

Segun `.claude/rules/claude-config-testing.md`, todo cambio en
`.claude/*` requiere validacion con `claude --permission-mode bypassPermissions`
y la matriz de 5 angulos.

Prompts a usar (en espanol, sin web):

```bash
# Angulo 1: pregunta general
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "cuanto deberia esperar de score en isitagentready para este portfolio" 2>&1 | tail -10

# ESPERADO: num_turns > 1, respuesta menciona "3-4/5" o "ceiling intencional"
```

```bash
# Angulo 2: tecnica especifica
claude ... -p "deberia agregar /.well-known/openid-configuration al portfolio"
# ESPERADO: num_turns > 1, respuesta NO recomienda implementarlo
```

```bash
# Angulo 3: sintoma / codigo de error
claude ... -p "el audit reporta API Catalog is not valid JSON, que hago"
# ESPERADO: num_turns > 1, respuesta indica que es bug SPA fallback de
# Cloudflare y debe renombrarse a .json
```

```bash
# Angulo 4: negativo (NO debe disparar la skill ai-audit)
claude ... -p "como configuro Astro 6 con Tailwind"
# ESPERADO: num_turns == 1 o respuesta NO menciona ai_audit
```

```bash
# Angulo 5: terminologia trampa (level 5, agent-native, MCP)
claude ... -p "como hago el portfolio agent-native (level 5 en isitagentready)"
# ESPERADO: num_turns > 1, respuesta explica que el ceiling intencional
# es 3-4/5 y por que NO se sube a level 5
```

## Tarea 3.4 — Actualizar `.claude/skills/ai-audit/SKILL.md`

Agregar a la description los keywords nuevos:

```yaml
description: >
  AI readiness audit for the portfolio. ...
  Use when the user says "ai audit", ..., "mcp server portfolio",
  "mcp endpoint /mcp", "agent-native", "level 5 isitagentready",
  "oauth para portfolio", "openid-configuration portfolio",
  "ceiling ai audit", "que tan agent-ready se puede llegar".
```

Y agregar la nueva seccion al body del SKILL.md.

## Verificacion incremental

```bash
# Lint markdown
pnpm exec biome check .claude/rules/ai-audit.md .claude/skills/ai-audit/SKILL.md

# Matriz claude -p (5 prompts)
# Ejecutar manualmente y registrar num_turns + extracto del result en
# el body del commit
```

## Archivos afectados

### Modificar

- `.claude/rules/ai-audit.md` — nuevas secciones
- `.claude/skills/ai-audit/SKILL.md` — actualizar description + body
- `.claude/docs/ai-audit/04-troubleshooting.md` — agregar la entrada
  del bug SPA fallback (referenciar Fase 1A del plan)

### Manual

- Ejecutar `claude -p` con los 5 prompts y registrar resultados (incluir
  num_turns en el body del commit de Fase 3)

## Done

- [ ] `.claude/rules/ai-audit.md` actualizado con secciones nuevas
- [ ] `.claude/skills/ai-audit/SKILL.md` actualizado
- [ ] 5/5 prompts pasan la matriz (num_turns correcto + contenido del
  response correcto)
- [ ] Commit `docs(rules,skills): documenta ceiling intencional + MCP server endpoint`
