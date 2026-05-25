# 06 - Fase CLI (orquestador + wire en devtools)

> Implementacion del `scraper.py` (orquestador con retry/backoff) +
> wire del comando default en `main.py`. Reune scaffold + auth +
> tools + report en un flujo end-to-end.

[< 05 Report](05-fase-report.md) | [07 Docs permanentes >](07-fase-docs-permanentes.md)

## Alcance

- `devtools/ai_audit/scraper.py` con orquestador async + retry +
  sleeps entre tools/targets.
- `auto_install_chromium()` invocado en el primer run.
- Comando default `python devtools/run.py ai_audit ...` produce
  snapshot + report y exit code apropiado.
- Verificacion smoke E2E real contra isitagentready.

## AC referenciados

- AC-2 (1 audit OK < 90s)
- AC-3 (stdout summary + path)
- AC-4 (retry [5, 15, 45]s + BLOCKED tras 3 fallos)
- AC-8 (auto-install chromium primer run)

## Tareas atomicas

### T-6.1 scraper.py — orquestador

```python
TARGET_SLEEP = 2
TOOL_SLEEP = 5
RETRY_WAITS = (5, 15, 45)

async def run_audit(
    *, targets: list[str], tool_names: list[str], headless: bool = True
) -> list[ToolResult]:
    results: list[ToolResult] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        try:
            for target in targets:
                for tool_name in tool_names:
                    result = await _scrape_with_retry(
                        browser=browser, tool_name=tool_name, target=target,
                    )
                    results.append(result)
                    await asyncio.sleep(TOOL_SLEEP)
                await asyncio.sleep(TARGET_SLEEP)
        finally:
            await browser.close()
    return results
```

`_scrape_with_retry`:

```python
async def _scrape_with_retry(
    *, browser: Browser, tool_name: str, target: str,
) -> ToolResult:
    tool = REGISTRY[tool_name]
    auth_state = auth.check(tool_name) if tool.REQUIRES_AUTH else AuthState.VALID
    if auth_state != AuthState.VALID:
        return _skipped_result(tool, target, reason=f'storageState {auth_state.value}')
    context = await browser.new_context(
        storage_state=auth.load(tool_name) if tool.REQUIRES_AUTH else None,
    )
    page = await context.new_page()
    for attempt, wait in enumerate([0, *RETRY_WAITS]):
        if wait:
            await asyncio.sleep(wait)
        try:
            return await tool.scrape(page, target)
        except BlockedError:
            continue
    return _blocked_result(tool, target)
```

### T-6.2 auto-install chromium

```python
def auto_install_chromium() -> None:
    """Idempotente: instala chromium si no esta."""
    try:
        async_playwright()  # smoke
    except Exception:
        subprocess.run(['playwright', 'install', 'chromium'], check=True)
```

Invocar en `main()` antes del `asyncio.run(run_audit(...))`.

### T-6.3 main() default

```python
def main(flags: dict) -> int:
    if flags['subcommand'] == 'setup':
        return _run_setup(flags)
    if flags['subcommand'] == 'report':
        return _run_report(flags)
    return _run_default(flags)

def _run_default(flags: dict) -> int:
    auto_install_chromium()
    targets = catalog.resolve_targets(
        env=flags['env'],
        niches=flags['niches'],
        targets_override=flags.get('targets'),
    )
    tool_names = flags['tools']
    if not targets or not tool_names:
        print('ERROR: no targets or tools resolved', file=sys.stderr)
        return 2
    ran_at = datetime.now(UTC)
    run_dir = Path('tmp/ai-audit') / ran_at.strftime('%Y-%m-%dT%H-%M-%S')
    run_dir.mkdir(parents=True, exist_ok=True)
    results = asyncio.run(scraper.run_audit(
        targets=targets, tool_names=tool_names,
    ))
    report.write_snapshot(
        results=results, env=flags['env'], ran_at=ran_at,
        path=run_dir / 'snapshot.json',
    )
    report.render_markdown(
        snapshot_path=run_dir / 'snapshot.json',
        path=run_dir / 'report.md',
    )
    _print_summary(results, run_dir / 'report.md')
    return _resolve_exit_code(results)
```

### T-6.4 Exit code resolver

```python
def _resolve_exit_code(results: list[ToolResult]) -> int:
    bad = sum(1 for r in results if r.status in (Status.BLOCKED, Status.ERROR))
    if bad >= len(results) / 2:
        return 1
    return 0
```

### T-6.5 Print summary

Tabla minimal en stdout:

```text
[ai_audit] env=prod, 6 targets x 4 tools = 24 audits
[ai_audit] OK: 20  PARTIAL: 2  BLOCKED: 1  ERROR: 0  SKIPPED: 1
[ai_audit] report: tmp/ai-audit/2026-05-25T10-30-00/report.md
```

### T-6.6 Tests scraper

`test_scraper.py`:

- Given 3x BlockedError seguidos, When `_scrape_with_retry`, Then retorna ToolResult(status=BLOCKED) tras esperar [5, 15, 45]s [AC-4]
- Given 1 success en intento 2, When `_scrape_with_retry`, Then retorna OK con duration_ms reflejando los 5s del primer wait [AC-4]
- Given auth.check -> MISSING para Ahrefs, When `_scrape_with_retry('ahrefs', ...)`, Then retorna SKIPPED sin abrir context [AC-6]
- Given 2 targets x 1 tool con sleep mockeado, When `run_audit`, Then `asyncio.sleep` se llama con TOOL_SLEEP y TARGET_SLEEP en orden [AC-4]

Mockear `async_playwright` + `Tool.scrape`.

### T-6.7 Smoke E2E real

NO automatizado en CI. El dev lo corre antes del push:

```bash
python devtools/run.py ai_audit \
  --tools=isitagentready --niches=generic
# Esperado:
# - tmp/ai-audit/<ts>/snapshot.json existe
# - 1 result con status=OK, score numerico
# - report.md generado
# - exit code 0
```

Si el smoke pasa, el contrato basico funciona end-to-end.

## Done

- [ ] T-6.1 scraper.py: orquestador + retry implementado
- [ ] T-6.2 auto-install chromium idempotente
- [ ] T-6.3 main() default wireado
- [ ] T-6.4 + T-6.5: exit code + summary
- [ ] T-6.6 tests scraper: 4 tests pasan, coverage >= 80%
- [ ] T-6.7 smoke real OK (manual, antes del PR)
- [ ] Commit: `feat(devtools): ai_audit orquestador + comando default end-to-end`

[< 05 Report](05-fase-report.md) | [07 Docs permanentes >](07-fase-docs-permanentes.md)
