**05**

# Configurar cada agente

[← Índice](README.md)

---

### Resumen

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Evento para reinyectar | `SessionStart` `compact` | `SessionStart` `compact` | `context` (cada llamada) | `PreInvocation` (cada llamada) |
| Dónde vive el hook | Proyecto | **Usuario**, con guarda por repo | Proyecto (plugin) | Proyecto (`.agents/hooks.json`) |
| Entrada | snake_case | snake_case | La arma el plugin | camelCase |
| Salida | `additionalContext` | `additionalContext` (no empezar con `[`) | `system.push` | `injectSteps[].ephemeralMessage` |
| Se reenvía en turnos siguientes | Sí | Sí | **No** | **No** |
| Errores visibles | stderr del hook | `Failed` en `codex exec` | `debug config` | Solo en su log |

### 1. Claude Code: `.claude/settings.json`

```json
{
  "env": { "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "60" },
  "permissions": { "additionalDirectories": ["../<repo>-worktrees"] },
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact|fork",
      "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"", "timeout": 10 }] }],
    "PreCompact": [{ "matcher": "manual|auto", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "PreToolUse": [{ "matcher": "^AskUserQuestion$", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "PostToolUse": [{ "matcher": "^(Edit|Write)$", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }]
  }
}
```

| Hook | Para qué |
| :-- | :-- |
| `SessionStart` | Inyecta el handoff al iniciar, reanudar, tras `/clear`, en un fork y **justo después de compactar** (también si compacta un plugin). **[doc + prueba]** |
| `PreCompact` | Corre antes del resumen: **su stdout son instrucciones para el resumen**; con exit 2 bloquea la compactación. No corre si un plugin responde la compactación. **[doc + prueba]** |
| `Stop` | Bloquea el cierre del turno (`decision: block`) mientras haya trabajo pendiente. **[uso real]** |
| `PreToolUse` de preguntas | Rechaza una pregunta al usuario cuando el agente debería decidir. **[uso real]** |
| `PostToolUse` de `Edit\|Write` | Valida las líneas de estado justo después de escribirlas. **[uso real]** |

- **Entrada:** `session_id`, `cwd`, `source`, `transcript_path` y `hook_event_name`.
- `$CLAUDE_PROJECT_DIR` apunta al proyecto donde se abrió la sesión: el script que corre es **el del checkout principal**.
- `PostCompact` existe pero no inyecta contexto: solo sirve para efectos secundarios.
- La pausa larga no necesita nada: `idleCompaction` viene activada ([cap. 07](07-pausa-larga.md)).
- Recomendado: un `PreToolUse` de `Bash` que rechace `git worktree add` con una ruta dentro del repo ([cap. 11](11-uso-diario.md)).

### 2. Codex: proyecto y usuario

`.codex/config.toml` (proyecto, solo en rutas de confianza):

```toml
model_post_turn_compact_threshold_percent = 65
model_auto_compact_token_limit = 190000
project_doc_max_bytes = 65536
```

Los hooks **no** van en el proyecto. Los de proyecto (`.codex/hooks.json`) corren solo si la ruta es de confianza **y** se aprobaron en `/hooks`. Cada worktree es una ruta distinta: ahí el hook **no corre y Codex no avisa**, ni con `--dangerously-bypass-hook-trust`. **[prueba]**

La solución es un hook **de usuario**, `~/.codex/hooks.json`, con tres eventos:

| Evento | Matcher | Comando | Si no aplica |
| :-- | :-- | :-- | :-- |
| `SessionStart` | `^(startup\|resume\|clear\|compact\|fork)$` | `session_handoff.py` | `\|\| true` |
| `UserPromptSubmit` | — | `session_handoff.py` | `\|\| true` |
| `Stop` | — | `session_handoff.py --touch` | `\|\| echo '{}'` (exige JSON) |

Cada comando lleva una **guarda por repo**, porque un hook de usuario corre en cualquier repo que abra Codex:

```sh
[ "$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" = '<repo>/.git' ] \
  && r=$(git rev-parse --show-toplevel 2>/dev/null) \
  && [ -f "$r/agent-hooks/session_handoff.py" ] && python3 "$r/agent-hooks/session_handoff.py" || true
```

- Sin la guarda, un repo clonado que traiga un `agent-hooks/session_handoff.py` ejecutaría código en cada sesión.
- Los worktrees comparten el `.git` común, así que pasan la guarda.
- No crees además `.codex/hooks.json` en el repo: en el principal se sumaría e inyectaría dos veces.
- La salida en texto plano **sí** se inyecta; si empieza con `[`, Codex la lee como JSON y marca el hook como `Failed`. Emite JSON para no depender de eso. **[prueba]**
- Codex guarda la confianza por hash: cambiar el hook exige volver a aprobarlo en `/hooks` y reiniciar la sesión. **[doc]**
- **Instálalo con un script**, no con `cp`: que fusione la plantilla en `~/.codex/hooks.json` (reemplaza solo los grupos que llaman al script y respalda el archivo), anteponga la guarda con la ruta real del `.git` y tenga un modo `status` que salga con 1 si falta un evento o difiere.

### 3. OpenCode: `opencode.json` y un plugin

```json
{ "compaction": { "buffer": 400000 } }
```

`.opencode/plugins/session-handoff.ts`, lo esencial:

```ts
const { text, cut } = handoffFor(request.sessionID, directory, opening) // opening: id del último mensaje si es del usuario
if (text) request.system.push({ type: "text", text })
if (text) applyCut(request.messages, cut)   // quita lo anterior al corte; el historial guardado no cambia
// http.request: ttl "1h" en cada cache_control de las peticiones a Anthropic (cap. 07)
export default { id: `session-handoff:${PLUGIN_ROOT}`, setup }
```

- Plugins con la API V2: `export default { id, setup(ctx) }`.
- `ctx.session.hook("context", req => …)` corre **antes de cada llamada al modelo**. Lo que agrega a `system` **no se guarda en el historial**: sobrevive a la compactación sin duplicarse. **[prueba]**
- El nombre `context` no está documentado, y un hook con un nombre inexistente no da error: repite la prueba en cada actualización.
- OpenCode busca `opencode.json` y `.opencode/` **hacia arriba**: desde un worktree dentro del repo carga también los del principal. Por eso cada copia del plugin actúa solo si la raíz git de la sesión es la suya, y el `id` lleva la ruta del checkout.
- Tras cambiar el plugin, `opencode service restart`. Para probar, `opencode run --standalone`: el servicio en segundo plano conserva el `setup` viejo.

### 4. Antigravity: `.agents/hooks.json`

```json
{ "session-handoff": {
  "PreInvocation":  [{ "type": "command", "command": "python3 <repo>/agent-hooks/session_handoff.py || echo '{}'", "timeout": 10 }],
  "PostInvocation": [{ "type": "command", "command": "python3 <repo>/agent-hooks/session_handoff.py --touch || echo '{}'", "timeout": 10 }]
} }
```

- Es un **mapa de hooks con nombre**, no el formato de Claude Code. **[doc + prueba]** ([hooks CLI](https://antigravity.google/docs/hooks?tab=cli))
- Entrada en **camelCase**: `conversationId`, `workspacePaths`, `transcriptPath`; `PreInvocation` añade `invocationNum`.
- No hay evento de compactación: inyectar en cada `PreInvocation` deja el handoff siempre presente.
- El `ephemeralMessage` queda guardado en la transcripción (el resumen de `/compact` lo usa), pero **no se reenvía** en los turnos siguientes. **[medido]**
- Un `hooks.json` mal formado no hace fallar la corrida: el error solo aparece en `~/.gemini/antigravity-cli/log/cli-*.log`.
- En headless, una acción que pide aprobación se deniega, la ejecución sigue y sale con 0. **[doc]**

### En mi caso

Los dos errores más caros fueron silenciosos. En Codex, el hook de usuario **nunca se había instalado** en una de mis máquinas: Codex trabajaba sin handoff y nada lo avisaba. De ahí salió el instalador con modo `status`. Y la primera plantilla de ese hook llamaba al script de la raíz git de **cualquier** repo; no lo detectó una prueba, sino una revisión de seguridad automática. La guarda por repo salió de ahí.

En OpenCode, dentro de un worktree, ninguna copia del plugin actuaba: las dos tenían el mismo `id`, se registraba solo la primera que cargaba y esa se descartaba por la raíz. Lo mostró la prueba real, no los tests. En Antigravity medí el costo de inyectar en cada invocación: +1500 tokens el turno que se vincula y ~210 por turno después, porque el mensaje no se acumula.

`claude-code` `codex` `opencode` `antigravity` `hooks`
