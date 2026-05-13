---
description: "Protocolo OBLIGATORIO de testing cuando se agrega/modifica/elimina cualquier archivo en .claude/* (skills, rules, agents, commands, hooks, settings). Bloquea WebSearch/WebFetch + MCP de internet en validacion para forzar que el conocimiento venga del archivo bajo test."
globs: ".claude/**/*"
---

# Testing de cambios en `.claude/*` (OBLIGATORIO)

> Cualquier modificacion en `.claude/skills/`, `.claude/rules/`, `.claude/agents/`,
> `.claude/commands/`, `.claude/hooks/` o `.claude/settings.json` DEBE validarse
> con `claude --permission-mode bypassPermissions -p "<prompt>"` antes de cerrar
> la tarea. No basta con leer el archivo — hay que demostrar que se invoca y
> responde correctamente.

## Comando canonico

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "<prompt en espanol>"
```

### Por que cada flag

| Flag | Razon |
|------|-------|
| `--permission-mode bypassPermissions` | Evita prompts interactivos durante la validacion |
| `--disallowedTools "WebSearch" "WebFetch"` | El conocimiento debe venir de la skill/rule/agent, no de la web. Si la skill responde sin estos tools, el archivo es la fuente de verdad |
| `--strict-mcp-config --mcp-config '{"mcpServers":{}}'` | Apaga TODOS los MCP servers de `.mcp.json` (playwright, github, db-readonly, shadcn, next-devtools). Aunque ninguno hace busquedas web hoy, varios usan `npx -y` y resuelven paquetes online — bloquearlos garantiza ausencia total de red |
| `--output-format json` | Permite parsear `num_turns` (>1 = skill invocada) y verificar el comportamiento programaticamente |
| `-p "<prompt>"` | Modo headless, una sola query |

### Prompts: SIEMPRE en espanol

Todos los prompts de validacion deben estar en espanol. Razon: este portfolio
es proyecto hispanohablante, las keywords espanolas del frontmatter son
criticas para el matching real, y validar solo en ingles deja huecos donde
un usuario nativo no dispara la skill (ver caso real abajo).

## Excepcion: skills que SI necesitan web

Skills de busqueda dejan los tools habilitados:

```bash
# OK para .claude/skills/research/SKILL.md (necesita WebSearch + WebFetch)
claude --permission-mode bypassPermissions \
  --output-format json \
  -p "investiga las novedades de pnpm 11.0.9"
```

Lista de skills con web habilitada:

| Skill | Tools requeridos |
|-------|------------------|
| `.claude/skills/research/SKILL.md` | `WebSearch`, `WebFetch` |
| (futuras) skills cuyo `allowed-tools` incluya `WebSearch`/`WebFetch` | mismos |

Para todo el resto: bloquear web es obligatorio.

## Estrategia de validacion (5 angulos minimo)

Cubrir estos 5 angulos en cada cambio de skill/rule:

| # | Angulo | Ejemplo de prompt |
|---|--------|-------------------|
| 1 | Pregunta general en espanol | "que cambio en pnpm 11" |
| 2 | Pregunta tecnica especifica en espanol | "como apruebo build scripts de sharp en pnpm" |
| 3 | Codigo de error o sintoma | "como soluciono ERR_PNPM_IGNORED_BUILDS" o "container pnpm en restart loop" |
| 4 | Negativo (NO debe disparar) | Pregunta generica adyacente que NO debe activar la skill |
| 5 | Terminologia legacy/trampa | Termino viejo (v10) o sinonimo poco obvio para validar que la skill cubre el caso |

### Lectura del JSON

```jsonc
{
  "num_turns": 4,        // > 1 = la skill se invoco (Read del archivo)
  "is_error": false,     // sin error de ejecucion
  "result": "...",       // respuesta. Inspeccionar contenido vs el archivo bajo test
  "duration_ms": 49910
}
```

Reglas:

- `num_turns == 1` + se esperaba invocacion = FAIL (la skill no se activo)
- `num_turns > 1` + se esperaba skip = FAIL (se invoco innecesariamente)
- `result` debe contener informacion del archivo, no solo training data del modelo

## Caso real: por que esta regla existe

Durante la creacion de `pnpm-workflow` (commit `2641d09`), el test inicial con
prompt "como apruebo build scripts de sharp y esbuild en pnpm? hablame de
onlyBuiltDependencies" devolvio `num_turns=1` (skill NO invocada) e
informacion INVERTIDA (decia que `allowBuilds` estaba deprecado, cuando es al
reves: `onlyBuiltDependencies` fue REMOVIDO en v11 y `allowBuilds` lo
reemplaza).

Causa raiz: la `description` del frontmatter no incluia keywords legacy de v10
ni una directiva ALWAYS suficientemente fuerte. Sin la skill, Claude respondio
desde training data (que tenia info v10 mezclada con v11).

Fix aplicado (SKILL.md v1.1):

- Agregada directiva "ALWAYS invoke this skill BEFORE answering ANY pnpm question"
- Agregada directiva "NEVER answer pnpm questions from training data alone"
- Agregadas keywords legacy v10: `neverBuiltDependencies`, `ignoreDepScripts`,
  `verifyDepsBeforeRun`, `optimisticRepeatInstall`, `minimumReleaseAge`,
  `pmOnFail`, `packageManagerStrict`
- Agregadas keywords espanol: "aprobar build scripts", "aprobar builds",
  "gestor de paquetes node", "paquete manager"

Re-test post-v1.1: `num_turns=4`, respuesta correcta diciendo
`onlyBuiltDependencies` REMOVIDO + reemplazo `allowBuilds`.

Sin esta validacion sistematica, la skill habria quedado muerta para los
casos donde mas se necesita: usuarios pidiendo ayuda con terminologia vieja.

## Workflow para agregar/modificar skill, rule, agent

```text
1. Crear/editar archivo en .claude/<tipo>/<nombre>.md
2. Identificar 5 angulos de prompts (ver tabla arriba)
3. Para cada prompt, ejecutar:
   claude --permission-mode bypassPermissions \
     --disallowedTools "WebSearch" "WebFetch" \
     --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
     --output-format json \
     -p "<prompt en espanol>" 2>&1 | tail -80
4. Verificar num_turns y contenido del result vs lo esperado
5. Si algun angulo falla:
   - Inspeccionar SKILL.md o rule
   - Ajustar description, keywords, directivas ALWAYS/NEVER
   - Volver a paso 3
6. Documentar resultados en commit body (5/5 PASS o detalles del fix)
7. Commit + push
```

## Anti-patterns

- ❌ Editar `.claude/<tipo>/<nombre>.md` sin correr ningun prompt de validacion
- ❌ Validar solo con prompts en ingles (deja huecos en hispanohablantes)
- ❌ Validar con `WebSearch`/`WebFetch` habilitados — la respuesta puede venir
  de la web y no del archivo bajo test (falso positivo)
- ❌ Dejar MCP servers activos durante validacion sin necesidad explicita
- ❌ Aceptar `num_turns == 1` cuando se esperaba invocacion
- ❌ Confiar en que "el archivo se ve bien" sin demostrar invocacion real
- ❌ Borrar/modificar una skill sin validar que quien dependia de ella sigue
  funcionando (rules que apuntan a la skill, comandos que la invocan)

## Referencia rapida

```bash
# Comando completo para copy-paste
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "PROMPT_EN_ESPANOL_AQUI" 2>&1 | tail -80
```

## Convenciones relacionadas

- `.claude/rules/skills.md` — frontmatter de skills, keywords bilingues
- `.claude/rules/verify-before-done.md` — verify-before-done general (NO declarar
  listo sin verificar)
- `.claude/rules/harness-protocol.md` — auto-mejora cuando un patron de error
  se detecta (esta regla nace de ese principio)
