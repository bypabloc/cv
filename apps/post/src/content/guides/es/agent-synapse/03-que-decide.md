**03**

# Qué bloquea, qué pregunta y qué deja pasar

[← Índice](README.md)

---

### Las cuatro decisiones

| Decisión | Qué significa | Ejemplo |
| :-- | :-- | :-- |
| `allow` | Se ejecuta sin preguntar | Borrar algo en `./tmp/` o en `dist/` |
| `ask` | Se pide confirmación al usuario | Un `git reset --hard` |
| `block` | No se ejecuta; el agente recibe el motivo | `rm -rf /`, un `cat .env` |
| `pass` | Synapse no opina; rigen los permisos normales del agente | Lecturas, `git status`, `pnpm test` |

`pass` es la decisión más frecuente y la que más importa: lo rutinario no debe costar ni un milisegundo de atención.

### Los cuatro hooks

Todos corren en `PreToolUse`, antes de que la herramienta se ejecute:

| Hook | Herramientas | Qué decide |
| :-- | :-- | :-- |
| `block_dangerous` | Bash (y el shell de cada agente) | Comandos destructivos, escrituras fuera del proyecto, exfiltración, escritura de archivos desde Bash |
| `block_env_read` | Read, Bash | Lectura de archivos `.env` |
| `detect_secrets` | Edit, Write | Credenciales en el contenido que se va a escribir |
| `protect_files` | Edit, Write | `.git/`, `.venv/`, lockfiles y configuración de agentes |

### block_dangerous en detalle

| Decisión | Casos |
| :-- | :-- |
| **block** | `rm -rf /` o `~`, fork bombs, escribir en `/dev/sd*`, `chmod 777 /`, `curl … \| sh`, reverse shells, `kill -1`, exfiltración de credenciales, escrituras fuera del proyecto (con variables resueltas: `p=/home/x; rm -rf "$p"`), escribir archivos desde Bash (`echo >`, `cat <<EOF >`, `sed -i`) |
| **ask** | Force push, `reset --hard`, `DROP DATABASE`, `filter-branch`, modificar `.git/`, salida dirigida a `/tmp` del sistema, borrar código versionado con cambios, docker privilegiado, lanzar otro agente en modo no interactivo (`codex exec`, `claude -p`) |
| **allow** | Operaciones en `./tmp/`, el scratchpad del agente y artefactos de build (`dist/`, `build/`, `.turbo/`, `target/`, `.cache/`, `node_modules/`); borrar contenido versionado y limpio ([cap. 04](04-alcance-del-proyecto.md)) |
| **pass** | Lecturas, `git`/`gh` rutinarios, `bun\|npm\|pnpm run\|test`, `uv run <herramienta>`, `python -m pytest`, scripts versionados del proyecto y los prefijos que declares ([cap. 06](06-configurar-por-proyecto.md)) |

### Por qué se bloquea escribir desde Bash

Los hooks de `detect_secrets` y `protect_files` revisan Edit y Write. Si el agente escribe un archivo con `cat <<EOF > config.ts`, esos controles no lo ven. Por eso Synapse bloquea la escritura de archivos desde Bash y le pide al agente usar la herramienta de edición. La salida de herramientas (`pytest > log`, `cmd | tee log`) y los mensajes de commit con heredoc siguen permitidos.

### protect_files

- **block:** modificar a mano `.git/`, `.venv/` o lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `bun.lock`, `uv.lock`, `poetry.lock`, `Cargo.lock`).
- **ask:** la configuración de los agentes (`.claude/settings.json`, `.codex/config.toml`, hooks) y la de Synapse.
- **pass:** las instrucciones en Markdown (`AGENTS.md`, `CLAUDE.md`, `.agents/rules/*.md`): no son permisos, y protegerlas genera esperas sin aumentar la seguridad ([cap. 10](10-codex-y-windows.md)).

### Qué ve el agente

Un bloqueo nombra el hook, el motor y la regla, y explica el motivo:

```text
🚫 BLOCKED · Synapse · block_dangerous (python) · regla structure.outside_project
Prohibido modificar rutas fuera del proyecto (~/code/mi-app): 'rm' sobre ~/otro.
```

Con ese texto, el agente casi siempre corrige solo: cambia la ruta, usa la herramienta de edición o anota que necesita tu aprobación y sigue con lo demás.

### En mi caso

La regla que más cambió mi día a día fue la de escribir desde Bash. Antes de tenerla, el agente esquivaba sin querer los controles de secretos con heredocs; después, cada archivo pasa por la herramienta de edición y queda revisado. El costo fue una tanda de falsos positivos al principio (un `rg "a|b"` que parecía una tubería, un `sed` con `;` entre comillas) que se arreglaron haciendo que la tokenización respete las comillas.

`decisiones` `block_dangerous` `protect_files`
