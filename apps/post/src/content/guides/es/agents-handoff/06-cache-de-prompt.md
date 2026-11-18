**06**

# Saber cuándo venció la caché

[← Índice](README.md)

---

### La regla común

Ningún agente avisa en pantalla cuando la caché de prompt expira (salvo la statusline de Claude Code). La señal sale del **uso de tokens de cada llamada**:

> **Fallo de caché** = la parte leída de caché cae a ~0 (o a un piso fijo, como las instrucciones del sistema) y vuelve a escribirse o cobrarse casi todo el prompt.
>
> - **Tras una pausa mayor que el TTL:** la caché expiró.
> - **Sin pausa:** algo cambió el prefijo (modelo, herramientas o MCP, system prompt, compactación, effort).

### Por agente

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Caché | Anthropic, `cache_control` | OpenAI, automática por prefijo | La del proveedor (Anthropic en estas pruebas) | Gemini implícita |
| TTL | **1 h** en la conversación principal con suscripción; 5 min con API key, créditos o subagentes **[doc]** | Sin TTL fijo: `in_memory` de 5–10 min (hasta 1 h) o `24h`, según modelo y ZDR **[doc]** | 5 min con Anthropic; 1 h si un plugin lo pide | Probabilístico, sin TTL publicado **[doc]** |
| Dónde verlo | Statusline (`prompt_cache`), `/usage`, JSONL de la transcripción, OTel | `codex exec --json` (`turn.completed.usage`), rollouts en `~/.codex/sessions/` | Tabla `message` de `~/.local/share/opencode/opencode.db`, `opencode export` | `agy -p --output-format json`, `stream-json`, transcripción |
| Campos | `cache_read_input_tokens`, `cache_creation_input_tokens` (`ephemeral_5m`, `ephemeral_1h`) | `input_tokens` (**incluye** lo cacheado) y `cached_input_tokens` | `tokens.cache.read`, `tokens.cache.write` | JSON: `input_tokens` **incluye** `cache_read_tokens`; transcripción: solo lo no cacheado |
| Proporción de aciertos | `read / (read + creation + input)` | `cached / input` | `read / (input + read + write)` | JSON `cache_read / input`; transcripción `cache_read / (input + cache_read)` |
| Aviso sin consultas | **Sí:** la statusline se vuelve a ejecutar al llegar `expires_at` (`warm`, `last_miss_cause`, `recache_tokens_if_cold`) | No | No | No |

### Qué invalida la caché sin pausa

- **Todos:** cambiar de modelo, herramientas o MCP, system prompt, effort o razonamiento; compactar.
- **Claude Code** **[doc]**: invalidan `/model`, effort, fast mode, conectar o quitar un MCP sin tool search, `/compact` y una actualización. **No** invalidan editar archivos, editar CLAUDE.md, cambiar permisos, `/rewind` ni los subagentes.
- **OpenAI** **[doc]**: más de 15 peticiones por minuto pueden caer en otra máquina sin la caché.

### Cómo vigilarla

1. **Claude Code:** una statusline con `prompt_cache.warm`, `expires_at` y `last_miss_cause`; para algo puntual, `/usage`.
2. **Codex:** `codex exec --json` y `cached_input_tokens / input_tokens` por turno; en interactivo, los rollouts.
3. **OpenCode:** la tabla `message` (en solo lectura) o herramientas de terceros.
4. **Antigravity:** `stream-json` y `cache_read_tokens` de cada paso.

No hagas "pings" para mantener la caché viva: cuestan tokens. En Claude Code, la opción oficial es `promptCacheTtl: "1h"` (o `CLAUDE_CODE_PROMPT_CACHE_TTL=1h`).

### Efecto del handoff en la caché

- **Claude Code y Codex:** el handoff se inyecta solo al iniciar, reanudar, compactar, `/clear` o fork: no afecta la caché entre turnos. **[doc]**
- **OpenCode:** va en `system` en cada llamada. Mientras `PROGRESS.md` no cambie, el prefijo es idéntico; **al editarlo, se reescribe la caché completa** en la llamada siguiente. Es razonable si se edita pocas veces. **[criterio]**
- **Antigravity:** el `ephemeralMessage` no se acumula; los turnos siguientes leyeron de caché con normalidad. **[medido]**

### En mi caso

Medí los registros locales de los cuatro agentes en sesiones reales. Estas cifras fijan los umbrales del [capítulo 07](07-pausa-larga.md):

| Agente | Lo medido |
| :-- | :-- |
| Claude Code | Pausas de 5 a 18 min: siguió leyendo de caché (205K–499K) y reescribió casi nada. Una pausa de 590 min leyó 28K y reescribió ~130K: TTL de 1 h vencido |
| Codex | Pausas de 42 a 54 min: a veces 0,98–1,00 de aciertos y otras un piso de ~11K (instrucciones compartidas) o 0. Desde 66 min, siempre falla |
| Antigravity | <1 min 99 %, 1–3 min 95 %, 3–5 min 88 %, 5–7 min 68 %, 7–10 min 11 %, 15–30 min 9 %, >30 min 0 %. La primera llamada de una conversación nueva no lee caché |
| OpenCode | Con 5 min de fábrica: 100 % con pausas < 5 min y 0 % con > 30 (2145 mensajes). Con 1 h pedida por el plugin: tras 6 min 40 s leyó 59 505 y escribió 20; 2 de 7 pausas reescribieron sin causa encontrada |

Circulan blogs que afirman que el TTL de Claude Code bajó a 5 min. La documentación y mis mediciones muestran 1 h con suscripción.

Fuentes: [prompt caching de Claude Code](https://code.claude.com/docs/en/prompt-caching.md), [statusline](https://code.claude.com/docs/en/statusline.md), [prompt caching de Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [prompt caching de OpenAI](https://developers.openai.com/api/docs/guides/prompt-caching), [headless de Antigravity](https://antigravity.google/docs/cli/headless), [caching de Gemini](https://aistudio.google.com/docs/caching).

`prompt-caching` `ttl` `tokens` `costos`
