# 10 - Verificacion E2E iterativa (fase final)

> Bateria de cierre del plan. Es la ultima fase y el ultimo commit
> del PR. SOLO cuando esta bateria pasa COMPLETA en verde se hace
> `git push` + se crea el PR.

[< 09 Paralelizacion](09-paralelizacion-worktrees.md) | [README >](README.md)

## Parte A — Refactor de tests + barrido

Ningun test viejo debe referenciar codigo eliminado, ningun test
nuevo debe quedar fuera de la convencion.

### Checklist A

- [ ] `rg -l 'ai_audit' devtools/tests/ | sort -u` — todos los hits
  estan en `devtools/tests/unit/src/ai_audit/`.
- [ ] `rg -l 'isitagentready|aibotchecker|ahrefs|semrush' devtools/
  | sort -u` — todos los hits estan en `devtools/ai_audit/` o en
  `devtools/tests/unit/src/ai_audit/`.
- [ ] `rg -l 'docker/env/dev-cli/ai-audit' .` — todos los hits
  estan en `.claude/`, `docs/specs/`, `devtools/ai_audit/auth.py` o
  `.gitignore`. NUNCA en codigo de apps.
- [ ] `rg 'placeholder|TODO\|FIXME' devtools/ai_audit/` — vacio.

## Parte B — Bateria de comandos reales

Ejecutar en orden. NO declarar el plan completo hasta que TODO esta
verde. Si algo falla: diagnosticar, corregir, re-ejecutar la suite
desde el principio.

### B.1 — Sintaxis + lint

```bash
python -m compileall -q devtools/ai_audit
cd devtools && uv run ruff check ai_audit tests/unit/src/ai_audit
cd devtools && uv run ruff format --check ai_audit tests/unit/src/ai_audit
```

Exit 0 esperado en los 3.

### B.2 — Tests unitarios + coverage per-file

```bash
cd devtools && uv run pytest tests/unit/src/ai_audit/ -v
cd devtools && uv run pytest tests/unit/src/ai_audit/ \
  --cov=ai_audit --cov-report=term-missing --cov-fail-under=80
```

Esperado: todos verdes, coverage TOTAL >= 80%, ningun archivo de
`ai_audit/` con coverage < 80%.

### B.3 — Validacion `.claude/*` (skill responde)

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como audito si the-full-stack.com esta preparada para crawlers de IA" \
  2>&1 | tail -80
```

Esperado: `num_turns > 1` (skill invocada), respuesta menciona
`devtools/ai_audit`, las 4 tools, `tmp/ai-audit/`, retry policy.

### B.4 — Smoke E2E real (1 tool, 1 niche)

```bash
python devtools/run.py ai_audit \
  --tools=isitagentready --niches=generic
```

Esperado:

- < 90s wall time.
- `tmp/ai-audit/<ts>/snapshot.json` existe con 1 resultado.
- `tmp/ai-audit/<ts>/report.md` existe.
- Exit code 0.
- Snapshot contiene `status=OK`, score numerico, categorias dict, 0+
  fixes.

### B.5 — Smoke subcomandos

```bash
# Setup en modo check-only (sin storageState)
python devtools/run.py ai_audit setup --tool=ahrefs --check-only
# Esperado: imprime MISSING o EXPIRED, exit 1

# Re-render desde el snapshot generado en B.4
SNAP=$(ls -t tmp/ai-audit/*/snapshot.json | head -1)
python devtools/run.py ai_audit report --snapshot="$SNAP"
# Esperado: rendered: <path>; exit 0; < 5s wall time
```

### B.6 — Cleanup de la carpeta del plan

```bash
git rm -r docs/specs/ai-audit-tool/
git status
```

Esperado: `docs/specs/ai-audit-tool/` no figura mas. La trazabilidad
del plan vive en `git log` y en el PR.

Si quedara aprendizaje permanente no contemplado en
`.claude/docs/ai-audit/`, promoverlo ANTES de borrar la carpeta.

### B.7 — Commit final del cleanup

```text
chore(specs): cierra plan ai-audit-tool, elimina docs/specs/
```

### B.8 — Bateria del repo (gates del proyecto)

```bash
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec astro check
```

Esperado: todo verde. Si alguno falla por algo NO relacionado con el
plan, abrir investigacion aparte; el plan no debe romper estos
gates.

## Gate del PR: push + PR SOLO con todo verde

Tras B.1-B.8 verdes:

```bash
git push origin feature/ai-audit-devtools
gh pr create --base dev --head feature/ai-audit-devtools \
  --title "feat(devtools): ai_audit - scraper de AI readiness multi-tool" \
  --body "$(cat <<'EOF'
## Problema
1. No hay forma sistematica de medir AI readiness de los 6 sitios del portfolio.
2. Las 4 tools externas (isitagentready, aibotchecker, Ahrefs, Semrush) no tienen API publica.
3. Iterar mejoras de GEO sin medir = ciego.

## Solucion
1. Nuevo script `python devtools/run.py ai_audit` que scrapea las 4 tools via Playwright Python.
2. Snapshot JSON + reporte Markdown con top 5 fixes priorizados, en `tmp/ai-audit/<ts>/`.
3. StorageState de auth (Ahrefs/Semrush) en `docker/env/dev-cli/ai-audit/` (LOCAL-ONLY).

## Como probar

Ver bateria completa en el commit del plan (`docs/specs/ai-audit-tool/10-verificacion-e2e.md`
antes del cleanup). Resumen:

\`\`\`bash
# Sintaxis + tests
cd devtools && uv run pytest tests/unit/src/ai_audit/ -v --cov=ai_audit --cov-fail-under=80

# Smoke real (1 audit)
python devtools/run.py ai_audit --tools=isitagentready --niches=generic
# Esperado: < 90s, snapshot.json + report.md, exit 0

# Subcomandos
python devtools/run.py ai_audit setup --tool=ahrefs --check-only  # MISSING, exit 1
python devtools/run.py ai_audit report --snapshot=tmp/ai-audit/<ts>/snapshot.json
\`\`\`

## TODO (fuera de scope, posibles fases futuras)
- Time-series JSONL para tracking historico.
- Subcomando `diff` para comparar 2 snapshots.
- 5ta tool si surge una buena alternativa estable.
EOF
)"
```

## Reglas de cierre

- NUNCA `git push` con un test rojo o coverage < 80%.
- NUNCA crear el PR con la bateria B.1-B.8 parcial.
- NUNCA mergear sin pasar el CI (que reproduce B.1, B.2, B.8).
- El plan se considera completo CUANDO el PR se mergea a `dev` y la
  carpeta `docs/specs/ai-audit-tool/` desaparece del HEAD de `dev`.

[< 09 Paralelizacion](09-paralelizacion-worktrees.md) | [README >](README.md)
