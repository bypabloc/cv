#!/bin/bash
# SubagentStop hook.
# Cuando un subagente termina su turno, verifica si actualizo su MEMORY.md
# durante la sesion (heuristica: hubo cambios en el archivo en los ultimos
# 30 minutos). Si no, emite recordatorio al stderr.
#
# Aplica solo a agentes con `memory: project` (que tienen MEMORY.md en
# .claude/agent-memory/<agente>/).
#
# NO bloquea (exit 0). Es un nudge, no un gate.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

# Lee el subagente desde stdin (si esta disponible en el payload del hook).
# El payload de SubagentStop contiene { agent_name, ... } segun docs.
AGENT_NAME="$(python3 -c "import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('agent_name', '') or d.get('subagent', '') or d.get('subagent_type', ''))
except Exception:
    pass" 2>/dev/null)"

# Si no podemos identificar el agente, salimos silenciosamente.
[ -z "$AGENT_NAME" ] && exit 0

MEMORY_FILE="$CLAUDE_PROJECT_DIR/.claude/agent-memory/${AGENT_NAME}/MEMORY.md"

# Si el agente no usa memoria persistente, salir.
[ -f "$MEMORY_FILE" ] || exit 0

# Calcular antiguedad del archivo en minutos (cross-platform: GNU stat vs BSD stat).
NOW="$(date +%s)"
MTIME="$(stat -c %Y "$MEMORY_FILE" 2>/dev/null || stat -f %m "$MEMORY_FILE" 2>/dev/null || echo "0")"

if [ "$MTIME" = "0" ]; then
  exit 0
fi

AGE_MIN=$(( (NOW - MTIME) / 60 ))

# Si fue actualizado en los ultimos 30 min, asumimos que el agente lo hizo.
if [ "$AGE_MIN" -lt 30 ]; then
  echo "[agent-memory] OK: $AGENT_NAME actualizo MEMORY.md hace ${AGE_MIN} min." >&2
  exit 0
fi

# Recordatorio.
echo "[agent-memory] WARNING: $AGENT_NAME termino sin actualizar MEMORY.md." >&2
echo "  Archivo: .claude/agent-memory/${AGENT_NAME}/MEMORY.md" >&2
echo "  Si descubriste un patron util esta sesion, anotalo (1 linea) para sesiones futuras." >&2

exit 0
