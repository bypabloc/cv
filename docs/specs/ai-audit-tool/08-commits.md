# 08 - Commits (secuencia commiteable)

> Listado de commits incrementales en `feature/ai-audit-devtools`.
> Cada commit deja el repo verde (lint + typecheck + tests del
> scope) y ejecuta su verificacion incremental ANTES de commitear.
> Un solo PR a `dev` al final.

[< 07 Docs](07-fase-docs-permanentes.md) | [09 Paralelizacion >](09-paralelizacion-worktrees.md)

## Secuencia

### C1 — Plan + docs permanentes (entregado ya por esta sesion)

```text
docs(specs): plan ai-audit-tool + rule + skill + docs de claude
```

**Contenido**:

- `docs/specs/ai-audit-tool/` completo (11 archivos)
- `.claude/rules/ai-audit.md`
- `.claude/skills/ai-audit/SKILL.md`
- `.claude/docs/ai-audit/` (README + 4 capitulos)

**Verificacion**:

- `python3 -m json.tool` no aplica (no hay JSON cambiado).
- Validacion `claude -p` con prompt en espanol — tras push:
  ```bash
  claude --permission-mode bypassPermissions \
    --disallowedTools "WebSearch" "WebFetch" \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    --output-format json \
    -p "como audito la preparacion del portfolio para IA"
  ```
  Esperado: `num_turns > 1`, respuesta cita el script y las 4 tools.

**AC cubiertos**: AC-10 (skill responde sobre el contrato).

### C2 — Scaffold (fase 02)

```text
feat(devtools): scaffold devtools/ai_audit (flags + catalog + skeleton)
```

**Contenido**:

- Skeleton del paquete (`__init__.py`, `main.py` minimal,
  `flags.py`, `catalog.py`, `tools/__init__.py`, `tools/base.py` con
  protocols).
- `devtools/pyproject.toml` con `playwright` en `[project.dependencies]`.
- `devtools/uv.lock` regenerado.
- `.gitignore` con `tmp/ai-audit/` + `docker/env/dev-cli/ai-audit/`.
- `devtools/tests/unit/src/ai_audit/test_flags.py` (8 tests).
- `devtools/tests/unit/src/ai_audit/test_catalog.py` (4 tests).

**Verificacion**:

```bash
python -m compileall -q devtools/ai_audit
cd devtools && uv run ruff check ai_audit tests/unit/src/ai_audit
cd devtools && uv run pytest tests/unit/src/ai_audit/ -v
git check-ignore tmp/ai-audit/x docker/env/dev-cli/ai-audit/x.json
```

**AC**: AC-7 (flags invalidos), AC-2 parcial (resolver).

### C3 — Auth + setup (fase 03)

```text
feat(devtools): ai_audit auth + subcomando setup con storageState
```

**Contenido**:

- `devtools/ai_audit/auth.py` (load, save, check, setup_interactive).
- Wire en `main.py` del subcomando `setup`.
- `test_auth.py` (6 tests, Playwright mockeado).

**Verificacion**:

```bash
cd devtools && uv run pytest tests/unit/src/ai_audit/test_auth.py -v
python devtools/run.py ai_audit setup --tool=ahrefs --check-only
# esperado: imprime MISSING, exit 1
```

**AC**: AC-1, AC-6.

### C4-C7 — Tools (paralelizables, fase 04)

4 commits, uno por tool. Pueden hacerse en cualquier orden, o en
paralelo via git worktrees (ver fase 09).

```text
feat(devtools): ai_audit tool isitagentready (parser + fixture + tests)
feat(devtools): ai_audit tool aibotchecker (parser + fixture + tests)
feat(devtools): ai_audit tool ahrefs (auth-gated parser + fixture + tests)
feat(devtools): ai_audit tool semrush (auth-gated parser + fixture + tests)
```

**Contenido por commit**:

- `devtools/ai_audit/tools/<tool>.py`
- `devtools/tests/unit/src/ai_audit/fixtures/<tool>/sample.html`
- `devtools/tests/unit/src/ai_audit/fixtures/<tool>/challenge.html`
- `devtools/tests/unit/src/ai_audit/tools/test_<tool>.py` (5 tests)

**Verificacion por commit**:

```bash
cd devtools && uv run pytest tests/unit/src/ai_audit/tools/test_<tool>.py -v
cd devtools && uv run pytest tests/unit/src/ai_audit/tools/test_<tool>.py \
  --cov=ai_audit/tools/<tool>.py --cov-report=term-missing
# coverage >= 80%
```

El ultimo de los 4 commits ademas actualiza `tools/__init__.py` con
el `REGISTRY` final.

**AC**: AC-2, AC-4 parcial, AC-6, AC-9.

### C8 — Report (fase 05)

```text
feat(devtools): ai_audit report (JSON snapshot + Markdown + re-render)
```

**Contenido**:

- `devtools/ai_audit/report.py`.
- Wire del subcomando `report`.
- `test_report.py` (6 tests).

**Verificacion**:

```bash
cd devtools && uv run pytest tests/unit/src/ai_audit/test_report.py -v
# Smoke (sin red):
python devtools/run.py ai_audit report \
  --snapshot=devtools/tests/unit/src/ai_audit/fixtures/snapshot.json
# Esperado: rendered: <path>; exit 0
```

**AC**: AC-3, AC-5.

### C9 — CLI orquestador (fase 06)

```text
feat(devtools): ai_audit orquestador + comando default end-to-end
```

**Contenido**:

- `devtools/ai_audit/scraper.py`.
- `main.py` completo.
- `test_scraper.py` (4 tests).
- `devtools/ai_audit/README.md` con uso operativo.

**Verificacion**:

```bash
cd devtools && uv run pytest tests/unit/src/ai_audit/ -v
cd devtools && uv run pytest tests/unit/src/ai_audit/ --cov=ai_audit --cov-report=term-missing
# coverage per-file >= 80%

# Smoke E2E real (1 audit real contra isitagentready):
python devtools/run.py ai_audit --tools=isitagentready --niches=generic
# Esperado: < 90s, snapshot.json + report.md, exit 0
```

**AC**: AC-2, AC-3, AC-4, AC-8, AC-9.

### C10 — Verificacion E2E + cleanup (fase 10)

```text
chore(specs): cierra plan ai-audit-tool, elimina docs/specs/
```

**Contenido**:

- `git rm -r docs/specs/ai-audit-tool/` (carpeta efimera).
- Si quedara aprendizaje permanente que no este ya en
  `.claude/docs/ai-audit/`, promoverlo a las rules/docs primero.

**Verificacion** (bateria completa, ver
[10-verificacion-e2e.md](10-verificacion-e2e.md)).

## Resumen secuencia

```text
C1 (este sesion)
  -> C2 (scaffold)
  -> C3 (auth)
  -> C4 || C5 || C6 || C7 (4 tools paralelizables)
  -> C8 (report) || C9 puede empezar (scraper.py es independiente del report.py)
  -> C9 (orquestador) — solo despues de tools + auth
  -> C10 (verificacion E2E + cleanup)
```

Un solo PR `feature/ai-audit-devtools -> dev` al final.

[< 07 Docs](07-fase-docs-permanentes.md) | [09 Paralelizacion >](09-paralelizacion-worktrees.md)
