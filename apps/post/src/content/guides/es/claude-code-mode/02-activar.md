**02**

# Activarlo y comprobar que está encendido

[← Índice](README.md)

---

### Requisitos

| Requisito | Detalle **[doc]** |
| :-- | :-- |
| Versión | Claude Code 2.1.323 o posterior (mejor la última: hubo muchos arreglos) |
| Instalación | Nativa |
| Cuenta | Suscripción de Claude o cuenta de Console. No funciona con Bedrock, Vertex, Foundry, un gateway ni un `ANTHROPIC_BASE_URL` propio |
| Organización | Sin HIPAA ni retención cero de datos |
| Modelo | Opus 5.5, Sonnet 5.5, Haiku 5.5 o Fable 5.2 |
| Dónde | Solo la sesión **interactiva** de `claude` en la terminal. No en `claude -p`, el Agent SDK, el panel de VS Code, Desktop ni sesiones en la nube |
| Windows | Git for Windows (los comandos de shell de los scripts corren en Git Bash) |

### Activarlo para una sesión

```bash
CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 claude
```

En PowerShell:

```powershell
$env:CLAUDE_CODE_EXPERIMENTAL_CODE_MODE = "1"
claude
```

La primera vez aparece un diálogo de confirmación; aceptarlo reinicia la sesión con el modo encendido. Al arrancar, la sesión muestra `Code Mode (experimental) is on · this session can be resumed only with Code Mode on`.

### Dejarlo fijo

En el bloque `env` de `~/.claude/settings.json`:

```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_CODE_MODE": "1" } }
```

El valor **se ignora en los settings de un proyecto**: un repo clonado no puede encenderlo por su cuenta. Para apagarlo, quita la variable o ponla en `0`; un `0` en cualquier lugar gana sobre un `1`. Una organización puede bloquearlo con `0` en managed settings, pero no forzarlo a encendido **[doc]**.

### Comprobar que está activo

| Dónde | Qué ver |
| :-- | :-- |
| `/status` | `Code Mode: on (experimental)` y su origen, o el motivo por el que no está disponible |
| `/context` | Las "System tools" bajan de unos 25k a unos 11k tokens |
| `Ctrl+O` | El transcript: cada script aparece como una fila **Code** que se puede expandir para leer el JavaScript |
| La conversación | Un resumen del bloque ("Read 8 files, ran 16 shell commands") y los diffs |

### Cuando dice "isn't available"

`/status` muestra el motivo. Los más comunes: proveedor o gateway no admitido, autenticación con `apiKeyHelper` o `ANTHROPIC_AUTH_TOKEN`, modelo no admitido, `--remote-control`, tracing de OpenTelemetry, un plugin o mod incompatible, `REPL` ausente de `--tools` o en `deny`, y `~/.claude.json` sin permiso de escritura **[doc]**. También falla si lanzas `claude` desde dentro de otra sesión de Claude Code (hereda sus variables): usa una terminal limpia.

### En mi caso

No lo dejé fijo: lo enciendo por sesión con una función en mi `.zshrc`, `claude-cm() { CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 command claude "$@"; }`. Así `claude` sigue siendo el modo normal y `claude-cm` abre una sesión con Code Mode, que es justo lo que necesito para comparar. Una sesión iniciada con el modo solo se reanuda con el modo encendido: para comparar, abro sesiones nuevas en vez de usar `--resume`.

`activación` `requisitos` `status`
