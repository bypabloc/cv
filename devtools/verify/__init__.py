"""verify: dada una lista de archivos modificados/staged, retorna las
verificaciones que deberian correrse antes de declarar la feature como
"lista" (según .claude/rules/verify-before-done.md).

Permite invocar con --execute para correr cada comando y reportar exit
codes en JSON.
"""
