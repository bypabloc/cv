# Loop fix - portfolio

> Activado con `/loop-fix <interval>` (por ejemplo `/loop-fix 30m`). Variante
> de `/loop` que aplica fixes triviales automaticamente. NO commitea, NO
> pushea, NO toca configuraciones criticas.

## Diferencia con `/loop`

`/loop.md` es solo lectura: observa, reporta, sugiere. `/loop-fix.md`
**aplica fixes triviales** (auto-fix de Biome) y deja un log de cada
accion tomada para que el usuario revise.

NO usar en sesiones cortas — el overhead no compensa. Recomendado para
sesiones largas (4+ horas) donde quieres que el codigo se mantenga
formateado mientras trabajas.

## Pasos en cada tick

### 1. Toolchain

Si `pnpm` no esta o falta `node_modules`, abortar tick y reportar.

```bash
pnpm --version >/dev/null 2>&1 || { echo "[loop-fix] pnpm DOWN — skip"; exit 0; }
test -d node_modules || { echo "[loop-fix] node_modules falta — skip"; exit 0; }
```

### 2. Auto-fix Biome

Si hay archivos modificados:

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx|astro|js|jsx|mjs|cjs|json|jsonc|css)$' | head -1 && \
  pnpm exec biome check --write . 2>&1 | tail -5
```

Reporta que archivos se modificaron por el auto-fix (si los hay).

### 3. Reporte

Una linea por tick:

```text
[loop-fix tick=N] Aplicados: biome(2 archivos) | 0 archivos sin cambio | branch=feature/x
```

Si no hubo nada que fixear:

```text
[loop-fix tick=N] Sin fixes pendientes | branch=feature/x
```

## Reglas estrictas

- **NUNCA** commit ni push automatico.
- **NUNCA** modificar `astro.config.ts`, `biome.json`, `tsconfig.json`
  via auto-fix (deberian ser ediciones intencionales).
- **NUNCA** modificar archivos sensibles (`.env*`, `.git-hooks/`).
- **NUNCA** ejecutar `--unsafe-fixes` (solo fixes seguros).
- **SIEMPRE** dejar log al stderr de cada accion para que el usuario revise.
- Si tras 3 ticks consecutivos no hay nada que fixear, sugerir aumentar el intervalo (`/loop-fix 1h`).

## Cuando no usar

- Si tu rama no tiene cambios sin commitear (loop-fix no tiene sobre que actuar).
- Si estas en medio de un refactor grande — el auto-fix puede confundir el diff.

## Tradeoffs

- **Pro**: codigo siempre formateado, sin acumular issues de lint.
- **Pro**: las modificaciones del auto-fix quedan en working tree, NO commit.
- **Con**: cada tick consume ~2-5s de CPU mientras corre `biome check --write`.
- **Con**: si trabajas en el mismo archivo que el auto-fix toca, puede haber conflicto trivial al guardar (resuelto re-haciendo el cambio).
