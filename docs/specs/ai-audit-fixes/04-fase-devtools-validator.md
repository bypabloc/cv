# Fase 3 - devtools: validator robots + sitemap fallback

[< 03 packages/ui](03-fase-packages-ui-tokens.md) | [05 prebuild scripts >](05-fase-prebuild-scripts.md)

## Objetivo

Subir `validators` tool de 50/100 a 100/100 arreglando los 2 falsos
fails:

1. **robots.txt FAIL**: prod sirve managed-content de Cloudflare con
   AI bots bloqueados. Es intencional. Validator debe tratar como
   `neutral`.
2. **sitemap.xml FAIL**: prod sirve `/sitemap-index.xml`, no
   `/sitemap.xml`. Validator debe fallback al index.

## Cambios

### A. Validator robots: detectar Cloudflare-managed

`devtools/ai_audit/validators.py`:

```python
_CF_MANAGED_SIGNATURE = '# BEGIN Cloudflare Managed content'
# Alternativa: 'As a condition of accessing this website, you agree to abide'


def validate_robots_ai_bots(content: str | None) -> dict[str, Any]:
    """..."""
    if not content:
        return {'status': 'fail', 'message': 'robots.txt ausente', 'details': {}}

    blocked = _collect_blocked_ai_bots(content)
    if not blocked:
        return {
            'status': 'pass',
            'message': 'ningun AI bot conocido esta bloqueado por robots.txt',
            'details': {'blocked': []},
        }

    # NEW: si el bloqueo viene de Cloudflare Managed Content Signals,
    # es intencional -> neutral, no fail.
    if _is_cloudflare_managed(content):
        return {
            'status': 'neutral',
            'message': (
                'AI bots bloqueados por Cloudflare Content Signals '
                '(decision intencional del owner)'
            ),
            'details': {'managed': True, 'blocked': sorted(set(blocked))},
        }

    return {
        'status': 'fail',
        'message': f'AI bots bloqueados: {", ".join(sorted(set(blocked)))}',
        'details': {'managed': False, 'blocked': sorted(set(blocked))},
    }


def _is_cloudflare_managed(content: str) -> bool:
    """True si el robots.txt es generado por la feature managed CF."""
    return _CF_MANAGED_SIGNATURE in content
```

### B. Validator sitemap: fallback a sitemap-index.xml

`devtools/ai_audit/tools/validators.py._fetch_all`:

```python
async def _fetch_all(self, target: str) -> dict[str, str | None]:
    """Fetcha llms.txt, robots.txt, sitemap.xml (con fallback) y home."""
    async with httpx.AsyncClient(...) as client:
        paths = ['/llms.txt', '/robots.txt', '/sitemap.xml', '']
        urls = [validators.normalize_url(target, p) if p else target for p in paths]
        responses = await asyncio.gather(*[client.get(u) for u in urls], return_exceptions=True)

    out: dict[str, str | None] = {}
    for path, response in zip(paths, responses, strict=True):
        key = path.lstrip('/') or 'home'
        out[key] = _ok_text(response)

    # NEW: si sitemap.xml no es XML, probar sitemap-index.xml
    if out.get('sitemap.xml') is None or '<urlset' not in (out.get('sitemap.xml') or ''):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                r = await client.get(validators.normalize_url(target, '/sitemap-index.xml'))
                if r.status_code == 200:
                    out['sitemap.xml'] = r.text
        except httpx.HTTPError:
            pass

    return out


def _ok_text(response):
    if isinstance(response, Exception) or response.status_code != 200:
        return None
    return response.text
```

### C. Scoring: `neutral` cuenta como 0.5 (no como pass ni como fail)

`devtools/ai_audit/tools/validators.py._run_validators`:

```python
def _run_validators(self, target, fetched):
    per_check = {...}  # igual que ahora

    # NEW: score con neutral=0.5
    scores = []
    for v in per_check.values():
        status = v['status']
        if status == 'pass':
            scores.append(1.0)
        elif status == 'neutral':
            scores.append(0.5)
        # fail -> 0
    score = round(sum(scores) / len(per_check) * 100) if per_check else 0

    # categories: 100 pass / 50 neutral / 0 fail
    categories = {
        name: {'pass': 100, 'neutral': 50, 'fail': 0}[v['status']]
        for name, v in per_check.items()
    }

    fixes = tuple(
        Fix(...) for name, v in per_check.items() if v['status'] == 'fail'
    )  # neutral NO genera Fix
```

## Tests

`devtools/tests/unit/src/ai_audit/validators.py`:

- `test_robots_managed_cloudflare_returns_neutral_with_managed_true`
- `test_robots_blocked_without_managed_signature_returns_fail`

`devtools/tests/unit/src/ai_audit/tools/validators.py`:

- `test_fetch_all_falls_back_to_sitemap_index_when_sitemap_xml_not_xml`
- `test_run_validators_neutral_counts_half_for_score`

## Archivos afectados

### Modificar

- `devtools/ai_audit/validators.py`
- `devtools/ai_audit/tools/validators.py`
- `devtools/tests/unit/src/ai_audit/validators.py`
- `devtools/tests/unit/src/ai_audit/tools/validators.py`
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`
  - Coverage >= 80% per-file en archivos modificados

## Verificacion incremental

```bash
python devtools/run.py test_runner --module=devtools --type=unit
# 789+ tests (los 785 actuales + ~4 nuevos)

# Smoke local del fix robots (usar el robots.txt real de prod como fixture)
curl -sS https://the-full-stack.com/robots.txt > /tmp/managed-robots.txt
devtools/.venv/bin/python -c "
from ai_audit.validators import validate_robots_ai_bots
print(validate_robots_ai_bots(open('/tmp/managed-robots.txt').read()))
"
# Esperado: {'status': 'neutral', 'details': {'managed': True, ...}}
```

[< 03 packages/ui](03-fase-packages-ui-tokens.md) | [05 prebuild scripts >](05-fase-prebuild-scripts.md)
