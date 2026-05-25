# 05 - Fase report (JSON + Markdown)

> Implementacion de `report.py`: serializa snapshot JSON y renderiza
> Markdown con tabla comparativa + top 5 fixes priorizados. Tambien
> el subcomando `report` para re-render.

[< 04 Tools](04-fase-tools.md) | [06 CLI >](06-fase-cli.md)

## Alcance

- `devtools/ai_audit/report.py` con:
  - `write_snapshot(results, path)` — JSON inmutable
  - `render_markdown(snapshot, path)` — Markdown legible
  - `prioritize_fixes(results)` — ordena por severity DESC, reach DESC
- Wire del subcomando `report --snapshot=<path>`.

## AC referenciados

- AC-3 (stdout summary + path al report)
- AC-5 (re-render desde snapshot existente, idempotente, < 5s)

## Tareas atomicas

### T-5.1 Snapshot writer

```python
def write_snapshot(
    *, results: list[ToolResult], env: str, ran_at: datetime, path: Path
) -> None:
    """Escribe snapshot.json. Sobrescribe si existe."""
    payload = {
        'ranAt': ran_at.isoformat() + 'Z',
        'env': env,
        'targets': sorted({r.target for r in results}),
        'tools': sorted({r.tool for r in results}),
        'results': [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
```

- Soporta interrupcion: si el caller pasa `interrupted=True`, agrega
  marca en metadata.
- Reemplaza Paths con strings (JSON-safe).

### T-5.2 Markdown renderer

Estructura del `report.md`:

```markdown
# AI readiness audit — <env> — <ran_at>

## Resumen por niche

| Niche | URL | isitagentready | aibotchecker | Ahrefs | Semrush | Avg |
|-------|-----|----------------|---------------|--------|---------|-----|
| generic | the-full-stack.com | 78 | 92 | 3/5 | 65 | 73 |
| ...

## Top 5 fixes priorizados

### #1 [HIGH] robots.txt missing GPTBot allow rule
- **Tool**: isitagentready (Bot Access Control)
- **Reach**: 8 crawlers afectados
- **Fix**: Add `User-agent: GPTBot\nAllow: /` to robots.txt
- **Archivo sugerido**: apps/generic/public/robots.txt

### #2 ...

## Audits BLOCKED / ERROR

| Niche | Tool | Status | Razon |
|-------|------|--------|-------|
| hub | ahrefs | SKIPPED | storageState missing |
```

Reglas:

- Avg = promedio normalizado 0-100 (Ahrefs 3/5 -> 60).
- Top 5 fixes: severity DESC, luego reach DESC. Ties por nombre del
  niche.
- Si todos OK: omitir seccion "BLOCKED / ERROR".

### T-5.3 prioritize_fixes

```python
SEVERITY_WEIGHT = {Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}

def prioritize_fixes(results: list[ToolResult], top: int = 5) -> list[Fix]:
    all_fixes = [(r, f) for r in results for f in r.fixes]
    return [
        f for _, f in sorted(
            all_fixes,
            key=lambda rf: (SEVERITY_WEIGHT[rf[1].severity], rf[1].reach),
            reverse=True,
        )
    ][:top]
```

### T-5.4 Subcomando report

```python
def _run_report(flags: dict) -> int:
    snapshot_path = Path(flags['snapshot'])
    snapshot = json.loads(snapshot_path.read_text())
    results = [ToolResult(**r) for r in snapshot['results']]
    report_path = snapshot_path.parent / 'report.md'
    render_markdown(
        snapshot=snapshot, results=results, path=report_path,
    )
    print(f'rendered: {report_path}')
    return 0
```

### T-5.5 Tests

`test_report.py`:

- Given 1 result OK, When write_snapshot, Then el JSON contiene `'results': [{...}]` con todos los campos del dataclass [AC-3]
- Given 6 results con scores variados, When render_markdown, Then la tabla resumen tiene 6 filas ordenadas alfabeticamente por niche [AC-3]
- Given results con 0 fixes, When render, Then seccion "Top 5 fixes" dice "no fixes pendientes" sin crashear [AC-5]
- Given 10 fixes con severities mezcladas, When prioritize_fixes(top=5), Then retorna 5 ordenados HIGH primero, luego por reach DESC [AC-3]
- Given snapshot path inexistente, When _run_report, Then exit 2 con mensaje claro [AC-5]
- Given snapshot valido, When _run_report 2 veces seguidas, Then ambos exit 0 y mismo report.md (idempotente) [AC-5]

## Done

- [ ] T-5.1 write_snapshot: 1 test pasa
- [ ] T-5.2 render_markdown: 2 tests pasan
- [ ] T-5.3 prioritize_fixes: 1 test exacto
- [ ] T-5.4 subcomando report wireado
- [ ] T-5.5 tests todos verdes, coverage report.py >= 80%
- [ ] Commit: `feat(devtools): ai_audit report (JSON + Markdown + re-render)`

[< 04 Tools](04-fase-tools.md) | [06 CLI >](06-fase-cli.md)
