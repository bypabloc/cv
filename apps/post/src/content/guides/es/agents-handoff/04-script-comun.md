**04**

# El script común de los hooks

[← Índice](README.md)

---

### Un script, cuatro agentes

`agent-hooks/session_handoff.py` (Python sin dependencias, versionado en el repo) responde a todos los eventos de los cuatro agentes y devuelve la salida en el formato de cada uno. Mantener **una sola** lógica evita que los agentes reciban mensajes distintos para el mismo estado.

### Entradas que atiende

| Entrada (stdin JSON) | Origen | Respuesta |
| :-- | :-- | :-- |
| `{"session_id","cwd","source"}` | `SessionStart` de Claude Code y Codex | El handoff en `additionalContext`. Sin `source`, asume `compact` |
| `{"hook_event_name":"PreCompact", …}` | Claude Code | Texto plano: qué debe conservar el resumen (trabajo, ruta, siguiente paso) |
| `{"hook_event_name":"Stop", …}` | Claude Code | `decision: block` mientras haya `Next step` sin estado terminal; tope de 3 bloqueos sin cambios |
| `PreToolUse` de la herramienta de preguntas | Claude Code | Rechaza la pregunta con un plan en ejecución, salvo un `blocked` de categoría válida |
| `PostToolUse` de `Write`/`Edit` | Claude Code | Si se editó un `PROGRESS.md` del handoff, nombra las líneas de estado de más de 120 caracteres |
| `{"hook_event_name":"UserPromptSubmit", …}` | Codex | Nada; tras una pausa larga, `{"decision":"block","reason":…}` una sola vez |
| `Stop` con `--touch` | Codex | Registra la actividad e imprime `{}` |
| `{"conversationId","workspacePaths","invocationNum"}` | `PreInvocation` de Antigravity | `injectSteps[].ephemeralMessage`; tras una pausa con `invocationNum` 0, `errorMessage` y `terminationBehavior: terminate` |
| Lo mismo con `--touch` | `PostInvocation` de Antigravity | Registra la actividad e imprime `{}` |
| `{"session_id","cwd","source":"context","agent":"opencode","message_id"}` | Plugin de OpenCode | El handoff, más el id del mensaje de corte tras una pausa |
| `--status` | Indicador en pantalla ([cap. 08](08-compactar-sin-resumen.md)) | Las líneas de estado en JSON |
| `--log` | Plugin de compactación | Registra su decisión en la bitácora |

### Piezas

| Pieza | Qué hace |
| :-- | :-- |
| `main_checkout(cwd)` | Padre de `git rev-parse --path-format=absolute --git-common-dir`: el principal, también desde un worktree |
| `current_work(store, session_id, branch)` | El vínculo `.sessions/<id>` y, si falta, la carpeta con el número de plan de la rama. Rechaza nombres inseguros (`../`) |
| `active_works(store)` | Trabajos con su `Next step` |
| `progress_fields(text)` | Lee las líneas de estado (tolera viñeta y negrita, no claves traducidas) |
| `build_message(...)` | Arma el texto según estado, fase y evento; trunca cada archivo a ~6000 caracteres |
| `render(message, output)` | Lo convierte al JSON de cada agente |
| Módulo de textos | Todos los mensajes en un solo lugar: seguir, decidir, bloqueado, terminado, por fase, por evento, cierre de turno, línea larga |
| Módulo de pausas | Umbral por agente (Codex 30, Antigravity 10, OpenCode 55 min; una variable de entorno los cambia y `0` los apaga), última actividad en `tmp/handoff/.idle/<id>` y el corte de OpenCode |
| Bitácora | `tmp/handoff/.log/events.jsonl`: `inject`, `precompact`, `compact.kept`/`compact.fallback`, `stop.block`/`stop.release`, `idle.block`, con snapshots por hash |

### Esqueleto mínimo para empezar

Este esqueleto cubre lo esencial: encuentra el checkout principal, lee el vínculo de la sesión, arma el mensaje y responde en el formato de Claude Code y Codex o de Antigravity. Sobre él agregas, de a una, las piezas de la tabla anterior.

```python
#!/usr/bin/env python3
"""Inyecta el handoff de la sesion vinculada (esqueleto minimo)."""

import json
import re
import subprocess
import sys
from pathlib import Path

MAX_CHARS = 6000
FILES = ('PROGRESS.md', 'DECISIONS.md', 'NOTES.md')
SAFE = re.compile(r'^[\w.-]+$')


def main_checkout(cwd: str) -> Path | None:
    """Raiz del checkout principal, tambien desde un worktree."""
    run = subprocess.run(
        ['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    if run.returncode != 0:
        return None
    return Path(run.stdout.strip()).parent


def current_work(store: Path, session_id: str) -> str | None:
    """Nombre del trabajo vinculado a la sesion, validado contra ../."""
    if not SAFE.match(session_id):
        return None
    link = store / '.sessions' / session_id
    work = link.read_text().strip() if link.is_file() else ''
    ok = SAFE.match(work) and not work.startswith('.')
    return work if ok and (store / work).is_dir() else None


def build_message(store: Path, work: str, source: str) -> str:
    parts = [
        f'# Handoff: {work} ({source})',
        f'Folder: {store / work}',
        'These files win over any summary; check them against git status '
        'and git log. Continue with the Next step: budget warnings are '
        'not a limit.',
    ]
    for name in FILES:
        path = store / work / name
        if path.is_file():
            text = path.read_text()
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + '\n[truncated]'
            parts.append(f'## {name}\n{text}')
    return '\n\n'.join(parts)


def render(message: str, data: dict) -> dict:
    if 'conversationId' in data:  # Antigravity PreInvocation
        return {'injectSteps': [{'ephemeralMessage': message}]}
    return {
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': message,
        },
    }


def main() -> int:
    data = json.load(sys.stdin)
    session_id = data.get('session_id') or data.get('conversationId') or ''
    cwd = data.get('cwd') or (data.get('workspacePaths') or ['.'])[0]
    root = main_checkout(cwd)
    work = root and current_work(root / 'tmp' / 'handoff', session_id)
    if not work:
        print('{}')
        return 0
    store = root / 'tmp' / 'handoff'
    message = build_message(store, work, data.get('source', 'compact'))
    print(json.dumps(render(message, data)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Pruébalo a mano antes de conectarlo a un agente:

```bash
mkdir -p tmp/handoff/.sessions tmp/handoff/042-login-form
printf 'Status: in-progress\nNext step: WK-208\n' > tmp/handoff/042-login-form/PROGRESS.md
echo 042-login-form > tmp/handoff/.sessions/prueba
echo '{"session_id":"prueba","cwd":"."}' | python3 agent-hooks/session_handoff.py | jq -r .hookSpecificOutput.additionalContext
```

Debe imprimir el mensaje con `WK-208`. Repite el último comando desde un worktree: la ruta del handoff debe ser la del principal. Con `"session_id":"../x"` o fuera de git, debe imprimir `{}`.

Los textos del mensaje van en inglés, igual que las líneas de estado: el agente los lee igual de bien y así no dependes del idioma de cada sesión.

### Las instrucciones que lo acompañan

- Una regla corta, siempre cargada, que diga dónde está el handoff, qué archivos lleva, cuándo escribirlo, las líneas de estado y las categorías de `blocked`. El detalle va a un documento de referencia, para no gastar contexto en cada sesión.
- La tabla de umbrales de compactación por agente ([cap. 02](02-compactar-antes.md)).
- La regla de worktrees: fuera del repo y, al cerrar, borrar el handoff ([cap. 11](11-uso-diario.md)).
- Si un agente lee reglas con frontmatter (Antigravity), cada regla con su `trigger`.

### Aplicarlo en otro repo

1. Copia el script, sus módulos (textos, pausas, bitácora) y sus tests. Ajusta cómo se reconoce el plan de una rama.
2. Asegura que `tmp/` esté en `.gitignore`.
3. Configura cada agente ([cap. 05](05-configurar-cada-agente.md)).
4. Escribe la regla y su referencia.
5. Prueba con el marcador ([cap. 10](10-probar-el-handoff.md)) y abre las sesiones desde el checkout principal.

### En mi caso

Al contrastar el sistema ya implementado, la versión nueva del script no estaba activa aunque ya estaba fusionada en la rama de integración. Claude Code ejecuta `$CLAUDE_PROJECT_DIR/agent-hooks/...`, y `$CLAUDE_PROJECT_DIR` es el checkout **principal**, que estaba atrasado. Un cambio al script llega a los agentes solo después de actualizar el principal.

`hooks` `python` `script` `implementación`
