#!/bin/bash
# PreToolUse hook (matcher: Bash).
# Bloquea git commit y git push directos cuando HEAD esta en una rama
# protegida (master/main/dev/release).
#
# Politica: trabajo siempre en feature/fix/chore branches, merge via PR.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

CMD="$(read_command_from_stdin)"
[ -z "$CMD" ] && exit 0

# Solo nos interesan comandos git commit / git push / git merge.
case "$CMD" in
  *"git commit"*|*"git push"*|*"git merge"*) ;;
  *) exit 0 ;;
esac

BRANCH="$(current_branch)"

# Si no estamos en repo git o no podemos detectar rama, no bloquear (el comando fallara solo).
[ -z "$BRANCH" ] && exit 0

# Lista de ramas protegidas.
case "$BRANCH" in
  master|main|dev|release) ;;
  *) exit 0 ;;
esac

# Detectar el tipo de operacion para mensaje preciso.
OP=""
case "$CMD" in
  *"git commit"*) OP="commit" ;;
  *"git push"*) OP="push" ;;
  *"git merge"*) OP="merge" ;;
esac

# Excepcion: git push origin master/main/dev/release ya esta en deny list de Bash.
# Pero git push (sin args) en rama protegida tambien debe bloquearse.

echo "Bloqueado por protect-branch: estas en rama protegida '$BRANCH'." >&2
echo "Operacion rechazada: $OP" >&2
echo "Politica del proyecto (.claude/rules/git-workflow.md):" >&2
echo "  - NUNCA $OP directo en master/main/dev/release." >&2
echo "  - Crea feature/fix/chore branch primero:" >&2
echo "      git checkout -b feature/<nombre>" >&2
echo "  - Despues abre PR con /pr-create o gh pr create." >&2
echo "" >&2
echo "Comando: $CMD" >&2
exit 2
