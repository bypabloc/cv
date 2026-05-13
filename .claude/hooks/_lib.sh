#!/bin/bash
# Helpers compartidos para hooks de Claude Code.
# Proyecto: portfolio (Astro 6 + TypeScript + Biome + Vitest + Playwright).
#
# Uso:
#   source "$(dirname "$0")/_lib.sh"

set -u

CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_PREFIX="[claude-hook]"
PROJECT_NAME="portfolio"

# Lee stdin JSON y extrae tool_input.file_path (vacio si no existe).
# IMPORTANTE: consume stdin completamente. Llamar SOLO UNA VEZ por ejecucion.
read_file_path_from_stdin() {
  python3 -c "import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass" 2>/dev/null
}

# Lee stdin JSON y extrae tool_input.command (Bash tool). Vacio si no existe.
read_command_from_stdin() {
  python3 -c "import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass" 2>/dev/null
}

# Retorna el nombre de la rama actual de git.
current_branch() {
  cd "$CLAUDE_PROJECT_DIR" && git symbolic-ref --short HEAD 2>/dev/null
}

# True si la rama actual es protegida (master/main/dev/release).
on_protected_branch() {
  local b
  b="$(current_branch)"
  case "$b" in
    master|main|dev|release) return 0 ;;
    *) return 1 ;;
  esac
}

# True si el comando `pnpm` esta disponible en PATH.
have_pnpm() {
  command -v pnpm >/dev/null 2>&1
}

# Helper de log al stderr (no se mezcla con stdout JSON de respuesta de hook).
hook_log() {
  echo "$LOG_PREFIX $*" >&2
}
