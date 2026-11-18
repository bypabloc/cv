**10**

# Probar que el handoff llega

[← Índice](README.md)

---

### El principio: probar con un marcador

Que el archivo exista, o que el hook salga con 0, no prueba que el modelo recibió el handoff. La prueba que distingue:

1. Escribe un **marcador inventado** (`WK-208`, `OT-555`) en el `PROGRESS.md` de un trabajo de prueba.
2. Vincula la sesión a ese trabajo.
3. Pregúntale al agente por el marcador **prohibiéndole leer archivos o ejecutar comandos**.

Si responde el marcador, solo pudo sacarlo de lo inyectado.

- En una sesión **sin vínculo**, la lista de trabajos activos incluye el siguiente paso de cada uno y el marcador puede filtrarse por ahí: vincula la sesión a **otro** trabajo con otro marcador y comprueba que responde ese.
- Al terminar, borra el trabajo, los vínculos y el estado de pausa.

### Claude Code: `claude -p`

```bash
claude --permission-mode bypassPermissions --model haiku \
  --disallowedTools "WebSearch" "WebFetch" "Bash" "Read" "Glob" "Grep" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json -p "¿Cuál es el siguiente paso del trabajo?" </dev/null > tmp/config-tests/marcador.json
jq -r '.is_error, .result' tmp/config-tests/marcador.json
```

- Sin `Bash`, `Read`, `Glob` ni `Grep`, la respuesta solo puede venir del contexto inyectado.
- `/compact` real: crea la sesión con `-p`, vincúlala y ejecuta `--resume <id> -p "/compact"`; la transcripción debe mostrar el handoff después de compactar.
- Plugin de compactación: lo mismo, con `--debug-file`, buscando que el resumidor no corrió ([cap. 09](09-receta-del-plugin.md)).

### Codex: `codex exec`

```bash
codex exec --ephemeral -s read-only -c model_reasoning_effort='"low"' \
  -o tmp/config-tests/marcador.txt '¿Cuál es el siguiente paso del trabajo?' </dev/null
```

- Sin `</dev/null`, `codex exec` se queda esperando stdin.
- La salida muestra `hook: SessionStart Completed` (corrió) o `Failed` (su salida no es válida).
- Un hook en línea, sin escribir archivos: `-c 'hooks.SessionStart=[…]'` con `--dangerously-bypass-hook-trust` (solo en pruebas).
- Configuración: `codex debug prompt-input` (0 si es válida). Confianza y capas cargadas: `codex doctor`.

### Antigravity: `agy -p`

```bash
agy -p 'hola' --output-format json </dev/null                       # devuelve conversation_id
# escribir el nombre del trabajo en tmp/handoff/.sessions/<conversation_id>
agy -p '¿Cuál es el siguiente paso del trabajo?' --conversation <id> --output-format json </dev/null
```

- Si el hook no parece correr, revisa el log más reciente en `~/.gemini/antigravity-cli/log/`.
- `agy -p '/compact' --conversation <id>` crea un `CHECKPOINT` cuyo resumen incluye lo inyectado.
- Para medir si el `ephemeralMessage` se acumula, suma `input_tokens` y `cache_read_tokens` de cada `PLANNER_RESPONSE` en la transcripción.

### OpenCode: `opencode run`

```bash
opencode service restart && opencode debug config        # comprueba compaction.buffer
opencode run --standalone -s ses_prueba01 --format json '¿Cuál es el siguiente paso del trabajo?' </dev/null
```

- `--standalone` evita el servicio en segundo plano, que conserva el `setup` viejo; `--print-logs` muestra `loading plugin`.
- Para confirmar que el plugin ejecuta el script: un envoltorio de `python3` en el `PATH` que registre cada llamada.

### Pausa larga simulada

Escribe `{"last": 0}` en `tmp/handoff/.idle/<id>` y manda el siguiente mensaje:

| Agente | Qué debes ver |
| :-- | :-- |
| OpenCode | Turno 1 «recuerda TULIPAN»; tras la pausa, la sesión no conoce la palabra y copia el `Next step`; el estado guarda el corte |
| Antigravity | Exit 3, `status: ERROR` y el aviso, sin `PLANNER_RESPONSE`. El reenvío responde |
| Codex | `hook: Stop Completed` registra la hora; tras la pausa, `hook: UserPromptSubmit Blocked`; el reenvío responde |

### Tests unitarios del script

| Grupo | Qué cubre |
| :-- | :-- |
| Trabajo actual | Gana el vínculo; dos sesiones en la misma rama no chocan; número de plan de la rama; rechazo de `../` y de vínculos a carpetas que no existen |
| Mensaje | Inyección y truncado; sesión sin vínculo; silencio sin id; texto por estado, fase y evento |
| Checkout principal | **Repo git real con un worktree**: desde el worktree, el principal y una subcarpeta; fuera de git, nada |
| Entrada y salida | snake_case, camelCase, `source` por defecto; el JSON de cada agente |
| Líneas de estado | Viñeta, negrita, claves faltantes, líneas largas |
| Cierre de turno y preguntas | Bloquea; deja parar con terminado, bloqueado válido, espera externa o tope |
| Pausas | Umbrales, estado corrupto, ids inseguros, corte de Antigravity solo con `invocationNum` 0, corte persistente de OpenCode, variable en `0`, un comando largo que no dispara el corte |
| Instalador de Codex | Fusión que conserva hooks ajenos, idempotencia, respaldo y **un repo ajeno con el script que no lo ejecuta** |

### Lo que las pruebas cortas no cubren

| Qué | Por qué | Cómo cerrarlo |
| :-- | :-- | :-- |
| Que la compactación ocurra exactamente en el umbral | Habría que llenar el contexto | Medir en uso real desde los transcripts ([cap. 12](12-problemas-y-soluciones.md)) |
| Codex interactivo con el hook de usuario | Requiere aprobarlo en `/hooks` | Instalar, aprobar y preguntar por el marcador |
| Pausas reales de 10, 30 o 55 min | Se simulan | El aviso dice cuántos minutos pasaron |
| Plugins de OpenCode en el servicio | Las pruebas usan `--standalone` | `opencode service restart` y revisar el uso |

### En mi caso

En OpenCode, tras el corte por pausa, el turno siguiente escribió 145 tokens y leyó ~59k (system y herramientas); el siguiente, 164. Y un error que solo mostró la prueba real, no los tests: dentro de un worktree, ninguna copia del plugin de OpenCode actuaba por el `id` repetido ([cap. 05](05-configurar-cada-agente.md)). Las pruebas cortas tampoco vieron lo que apareció con semanas de uso: corridas autónomas, varias sesiones a la vez y lotes grandes de herramientas en paralelo ([cap. 11](11-uso-diario.md)).

`testing` `headless` `hooks` `verificación`
