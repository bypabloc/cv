# AI readiness audit — knowledge tree

> Documentacion de referencia del script `devtools/ai_audit`. El stack
> actual son 3 tools complementarias 100% gratis tras descartar las 3
> comerciales originales (Ahrefs/Semrush/aibotchecker) por costo
> prohibitivo + falta de API publica.

## Cuando leer

| Documento | Cuando leer |
|-----------|-------------|
| [01-tools-evaluadas.md](01-tools-evaluadas.md) | Antes de proponer una tool nueva. Cubre las 3 activas (isitagentready / validators / lighthouse_psi) + las 5 descartadas (aibotchecker, Ahrefs, Semrush, Cloro, HubSpot AEO) con razones documentadas. |
| [02-auth-setup.md](02-auth-setup.md) | Si `lighthouse_psi` reporta SKIPPED. Como obtener API key gratis de Google y pegarla en `docker/env/dev-cli/.{env}`. |
| [03-arquitectura.md](03-arquitectura.md) | Antes de cambiar la estructura interna del paquete: flow del orquestador, contratos entre `scraper -> tools -> report`, decisiones de diseno. |
| [04-troubleshooting.md](04-troubleshooting.md) | Cuando un run reporta BLOCKED / ERROR. Sintomas comunes, como diagnosticar. |

## Reglas criticas (resumen — autoritativa en [rules/ai-audit.md](../../rules/ai-audit.md))

- SIEMPRE auditar prod como fuente de verdad. dev = falsos negativos.
- SIEMPRE `PSI_API_KEY` en `docker/env/dev-cli/.{env}` (LOCAL-ONLY, gitignored).
- SIEMPRE reportes a `tmp/ai-audit/` (no a `docs/`).
- NUNCA correr en CI/CD (consumo de APIs externas + ToS).
- NUNCA commitear el `.env` con la key ni los reportes.

## Las 3 tools activas

| Tool             | URL                                              | Auth           | Mide                                                                                              |
| ---------------- | ------------------------------------------------ | -------------- | ------------------------------------------------------------------------------------------------- |
| `isitagentready` | API JSON `https://isitagentready.com/api/scan`   | Anonima        | 5 categorias agent-readiness, MCP, robots.txt Content Signals, llms.txt (level 0-5)               |
| `validators`     | (codigo OSS propio)                              | Anonima        | 4 checks: llms.txt spec, robots.txt AI bots blocked, sitemap.xml, JSON-LD Person/Organization     |
| `lighthouse_psi` | Google PageSpeed Insights v5 API                 | API key gratis | 4 categorias Lighthouse: Performance, SEO, Accessibility, BestPractices                           |

Detalle: [01-tools-evaluadas.md](01-tools-evaluadas.md).

## Comandos canonicos (resumen)

```bash
# Audit default (6 homes de prod, las 3 tools)
python devtools/run.py ai_audit

# Subset
python devtools/run.py ai_audit --niches=hub,fintech
python devtools/run.py ai_audit --tools=isitagentready,validators
python devtools/run.py ai_audit --targets=architect:/projects

# Re-render report desde snapshot existente
python devtools/run.py ai_audit report --snapshot=<path>
```

## Output

Cada run produce una carpeta en `tmp/ai-audit/<ISO-timestamp>/`:

- `snapshot.json` — datos crudos serializables por (target, tool).
- `report.md` — tabla comparativa por niche + top 5 fixes priorizados
  (severity DESC, reach DESC).

## Navegacion

- [Rule autoritativa](../../rules/ai-audit.md)
- [Skill invocable `/ai-audit`](../../skills/ai-audit/SKILL.md)
- [Rule env-files](../../rules/env-files.md) — politica de NO leer `.env` completos
