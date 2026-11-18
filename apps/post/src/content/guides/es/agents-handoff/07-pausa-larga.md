**07**

# Retomar tras una pausa larga

[← Índice](README.md)

---

### La pregunta

¿Se puede evitar reenviar toda la conversación después de una pausa larga y seguir solo con el handoff?

- **Interceptar cuando la caché ya venció no sirve por sí solo.** Ningún agente tiene un evento "la caché expiró", y la primera petición tras la pausa ya paga la reescritura completa, salvo que se recorte lo que se envía.
- El ahorro viene de dos caminos:
  1. **Antes de que venza:** compactar con la caché caliente. Claude Code lo hace de forma nativa.
  2. **Al volver:** no enviar el historial. Una sesión nueva donde el hook de inicio inyecta el handoff (Codex y Antigravity), o recortar lo enviado en la misma sesión (OpenCode).
- Condición para los dos: el handoff tiene que estar en disco **al cerrar cada turno**, no recién al volver.
- Solo en sesiones **con trabajo vinculado**: sin handoff, una sesión nueva no tiene con qué seguir.

### Qué hace cada agente

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Mecanismo | Nativo: `idleCompaction` al ~90 % del TTL | `Stop` registra la hora; `UserPromptSubmit` bloquea una vez | Plugin: corte en el mensaje que abre el turno | `PostInvocation` registra; `PreInvocation` (`invocationNum` 0) termina el turno |
| Umbral | ~54 min (con ≥ 200k tokens) | 30 min | 55 min con caché de 1 h (5 min si la caché es de 5) | 10 min |
| Qué ves | "Compacted while idle…" | `hook: UserPromptSubmit Blocked` y el aviso | Nada: sigue en la misma sesión | Error con el aviso; exit 3 en `-p` |
| Cómo sigues | Igual que siempre | Sesión nueva (no `resume`) + «retoma el trabajo X», o reenviar | Igual que siempre | Conversación nueva + «retoma el trabajo X», o reenviar |
| Qué conserva | El resumen (o la cola) y el handoff | Solo el handoff y el repo | El handoff y lo posterior al corte | Solo el handoff |
| Evidencia | **[bin]** y compactaciones reales | **[prueba]** `codex exec` | **[prueba]** 3 turnos y tokens medidos | **[prueba]** transcripción sin llamada al modelo |

### Claude Code: ya resuelto

`idleCompaction` programa un temporizador en `lastActivityAt + 0,9 × (expiresAt − lastActivityAt)`: unos 54 min con TTL de 1 h. Compacta **leyendo de caché**, lo mejor posible. **[bin]**

- Condiciones: sesión interactiva, TTL de 1 h, prefijo sin cambios y al menos `max(100k, CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS)` tokens (200 000 por defecto).
- Se apaga con `"idleCompaction": false`.
- Tras cada una, `SessionStart` `compact` reinyecta el handoff. **[prueba]**

### Codex: bloquear una vez y pedir sesión nueva

Ningún hook de Codex puede recortar lo que se envía: `UserPromptSubmit` solo agrega contexto o bloquea. **[doc]**

1. `Stop` (con `--touch`) registra la hora en `tmp/handoff/.idle/<session_id>` e imprime `{}`.
2. En el siguiente mensaje, si pasaron más de 30 min, `UserPromptSubmit` devuelve `{"decision":"block","reason":"…"}` con los minutos, el trabajo y su carpeta.
3. Abres una sesión nueva y escribes «retoma el trabajo `042-login-form`». **No uses `resume`**: carga la conversación completa.
4. El bloqueo es de una sola vez: si reenvías el mensaje, sigue en la misma sesión, por si el contexto completo vale más que el ahorro.

### Antigravity: terminar el turno antes de llamar al modelo

- `PostInvocation` registra la hora; `PreInvocation` evalúa **solo con `invocationNum` 0** (la primera llamada del turno).
- Tras 10 min, devuelve `terminationBehavior: "terminate"` con un `errorMessage`: corta **antes** de llamar al modelo. **[doc + prueba]**
- Trampas: con `terminate`, `agy -p` sale con 3, y el `usage` del JSON es **acumulado** aunque no se llamó al modelo.

### OpenCode: recortar en la misma sesión

- El hook `context` recibe `messages` y se puede reemplazar: quitar los viejos solo cambia lo que se envía, no el historial guardado. **[prueba]**
- Tras la pausa, el plugin fija un corte en el mensaje del usuario que abre el turno y envía solo lo posterior, con el handoff en `system`. Corta en un límite de turno para no romper pares `tool_use`/`tool_result`.
- El corte se guarda: las llamadas siguientes envían el mismo prefijo, que vuelve a quedar en caché.
- Un comando largo **no** dispara el corte: dentro de un turno, la llamada siguiente la abre un resultado de herramienta, no el usuario.

### Pedir 1 h de caché en OpenCode

Con la API de Anthropic, OpenCode usa caché de 5 min y no deja configurarla: un comando de más de 5 min hacía que la llamada siguiente reescribiera todo el prefijo (×1,25) en vez de leerlo (×0,1).

- El plugin atiende `http.request`, reescribe cada petición al proveedor y pone `ttl: "1h"` en **todos** los `cache_control` (Anthropic exige que las marcas de 1 h precedan a las de 5 min).
- La escritura de 1 h cuesta ×2. Con eso, el corte por pausa pasa de 5 a 55 min.
- Si el cuerpo no es JSON, la petición sigue igual. Se verifica en `cache_creation.ephemeral_1h_input_tokens` del `message_start`.

### Los umbrales

- Salen del TTL medido de cada agente ([cap. 06](06-cache-de-prompt.md)).
- Una variable de entorno los cambia todos y `0` los apaga. En OpenCode la lee el servicio en segundo plano.
- Estado por sesión en `tmp/handoff/.idle/<session_id>` (`last` y, en OpenCode, `cut`). Escribir `{"last": 0}` simula una pausa ([cap. 10](10-probar-el-handoff.md)).

### En mi caso

| Caso | Sin esto | Con esto | Base |
| :-- | :-- | :-- | :-- |
| OpenCode tras la pausa | El siguiente mensaje reescribe todo el historial | Solo lo no cacheado: 145 y 164 tokens tras el corte | **[medido]** |
| Codex, 150k de contexto | ~USD 0,75 en frío por mensaje | Sesión nueva con un handoff de 8k: ~USD 0,04 | **[cálculo]** |
| Antigravity | Todo el historial con ~11 % de aciertos tras 7 min | La conversación nueva arranca con el handoff | **[medido]** aciertos |
| Claude Code, 200k, TTL de 1 h | ~400k unidades de reescritura (escritura ×2) | ~40k: compacta antes de que venza | **[cálculo]** |

Busqué antes qué existía en la comunidad: plugins de auto-handoff y de compactación a los 55 min para Claude Code (se solapan con el nativo), kits de handoff manuales para Codex y un `/handoff` manual para OpenCode. Ninguno detectaba la pausa y seguía con un handoff en disco de forma automática en Codex, OpenCode o Antigravity.

`prompt-caching` `inactividad` `costos` `handoff`
