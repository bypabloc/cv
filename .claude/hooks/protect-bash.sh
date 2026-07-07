#!/bin/bash
# PreToolUse hook (matcher: Bash).
# Bloquea comandos destructivos o riesgosos en Bash que la deny list no
# alcanza a cubrir por su naturaleza (redirects a .env, escrituras a
# .git-hooks/, pipes a shell remoto, etc).
#
# Si detecta un patron peligroso: exit 2 + mensaje al stderr -> el harness
# rechaza la operacion y le dice a Claude el motivo.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

CMD="$(read_command_from_stdin)"
[ -z "$CMD" ] && exit 0

# Helper: bloquea con mensaje y exit 2.
deny() {
  echo "Bloqueado por protect-bash: $1" >&2
  echo "Comando rechazado: $CMD" >&2
  exit 2
}

LOWER_CMD="$(echo "$CMD" | tr '[:upper:]' '[:lower:]')"

# 1. Escritura a archivos sensibles via redirect.
if echo "$CMD" | grep -Eq '>[[:space:]]*\.env($|[[:space:]])'; then
  deny "redirect a .env detectado. Editar manualmente fuera de Claude."
fi

if echo "$CMD" | grep -Eq '>[[:space:]]*\.env\.[a-z]+'; then
  deny "redirect a .env.<algo> detectado. Editar manualmente."
fi

if echo "$CMD" | grep -Eq '>[[:space:]]*\.git-hooks/'; then
  deny "modificacion de .git-hooks/ via redirect. Usa Edit tool con review."
fi

if echo "$CMD" | grep -Eq '>[[:space:]]*\.git/config'; then
  deny "redirect a .git/config detectado. NUNCA modificar config de git desde un hook."
fi

# 2. Pipes peligrosos a shell remoto (curl|bash, wget|sh).
if echo "$LOWER_CMD" | grep -Eq '(curl|wget)[[:space:]].*[[:space:]]\|[[:space:]]*(bash|sh|zsh)([[:space:]]|$)'; then
  deny "pipe a shell de descarga remota detectado. Riesgo de ejecucion de codigo no auditado."
fi

# 3. rm con destino = la raiz literal (/ o /*) o el home a secas (~, $HOME).
#    Solo bloquea cuando el destino ES root/home, no cuando es un archivo o
#    carpeta concreta bajo un path absoluto (ese caso lo evalua
#    block-dangerous.py con su regla tmp/gitignore -> allow o ask).
if echo "$CMD" | grep -Eq 'rm[[:space:]]+-[a-zA-Z]*[[:space:]]+(/|/\*|~|\$HOME|\$\{HOME\})([[:space:]]|$)'; then
  deny "rm con destino la raiz (/) o el home (~). Usa un path concreto del proyecto."
fi

# 4. Modificacion de hooks de git via edicion directa de .git/hooks/.
if echo "$CMD" | grep -Eq '\.git/hooks/'; then
  deny "manipulacion de .git/hooks/ detectada. Los hooks viven en .git-hooks/ versionados."
fi

# 5. Bypass explicito de hooks (--no-verify) — politica del proyecto.
if echo "$CMD" | grep -Eq -- '--no-verify'; then
  deny "--no-verify detectado. Politica del proyecto: NUNCA bypassear hooks. Si fallan, usar fix-hooks skill."
fi

# 6. chmod 777 (apertura total de permisos).
if echo "$CMD" | grep -Eq 'chmod[[:space:]]+777'; then
  deny "chmod 777 detectado. Usa permisos minimos necesarios (755 ejecutables, 644 archivos)."
fi

# 7. Edicion de pnpm-lock.yaml via sed/awk in-place (corrupcion de lockfiles).
if echo "$CMD" | grep -Eq 'sed[[:space:]]+.*-i.*(pnpm-lock\.yaml|package-lock\.json|yarn\.lock)'; then
  deny "modificacion in-place de lockfile via sed. Regenerar con pnpm install."
fi

exit 0
