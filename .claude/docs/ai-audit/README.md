# AI readiness audit — knowledge tree

> Documentacion de referencia del script `devtools/ai_audit`: las 4
> tools externas auditadas, como configurar auth, arquitectura
> interna del scraper, y troubleshooting.

## Estado

Rule + skill + estos docs estan escritos. La implementacion del
script vive en [docs/specs/ai-audit-tool/](../../../docs/specs/ai-audit-tool/)
(plan efimero, rama `feature/ai-audit-devtools`).

## Cuando leer

| Documento | Cuando leer |
|-----------|-------------|
| [01-tools-evaluadas.md](01-tools-evaluadas.md) | Antes de agregar/modificar un scraper en `devtools/ai_audit/tools/`. Detalle por tool: URL, auth, score que devuelve, gotchas del DOM, frecuencia de breakage. |
| [02-auth-setup.md](02-auth-setup.md) | Antes de correr el audit por primera vez. Como crear cuentas free de Ahrefs y Semrush, como guardar storageState, donde vive, cuando expira. |
| [03-arquitectura.md](03-arquitectura.md) | Antes de cambiar la estructura interna del paquete: flow del orquestador, contratos entre `scraper -> tools -> report`, decisiones de diseno. |
| [04-troubleshooting.md](04-troubleshooting.md) | Cuando un run reporta BLOCKED / ERROR / PARTIAL en mas del 50% de los targets. Sintomas comunes, como diagnosticar, cuando rebuildear el storageState. |

## Reglas criticas (resumen — autoritativa en [rules/ai-audit.md](../../rules/ai-audit.md))

- SIEMPRE auditar prod como fuente de verdad. dev/stage = falsos negativos.
- SIEMPRE storageState en `docker/env/dev-cli/ai-audit/` (LOCAL-ONLY, gitignored).
- SIEMPRE reportes a `tmp/ai-audit/` (no a `docs/`).
- NUNCA correr en CI/CD (rompe ToS de las tools por frecuencia).
- NUNCA commitear cookies de auth ni reportes.

## Las 4 tools (resumen)

| Tool | URL | Auth | Mide |
|------|-----|------|------|
| Is Your Site Agent-Ready? | isitagentready.com | Anonima | 5 categorias agent-readiness, standards emergentes (MCP, robots.txt Content Signals) |
| AI Visibility Checker | aibotchecker.online | Anonima | 60+ checks per-bot (GPTBot, ClaudeBot, etc.) |
| Ahrefs AI Visibility | ahrefs.com/ai-visibility-checker | Cuenta gratis | Brand mentions en respuestas de ChatGPT, Gemini, Perplexity, Copilot |
| Semrush AI Visibility | semrush.com/ai-visibility-audit | Cuenta gratis | AI readiness score + trafico real desde plataformas IA |

Detalle: [01-tools-evaluadas.md](01-tools-evaluadas.md).

## Comandos canonicos (resumen)

```bash
# Audit default (6 homes de prod, las 4 tools)
python devtools/run.py ai_audit

# Subset
python devtools/run.py ai_audit --niches=hub,fintech
python devtools/run.py ai_audit --tools=isitagentready,aibotchecker
python devtools/run.py ai_audit --targets=architect:/projects

# Setup auth (1 vez por tool)
python devtools/run.py ai_audit setup --tool=ahrefs

# Re-render report desde snapshot existente
python devtools/run.py ai_audit report --snapshot=<path>
```

## Output

Cada run produce una carpeta en `tmp/ai-audit/<ISO-timestamp>/`:

- `snapshot.json` — datos crudos serializables por (target, tool).
- `report.md` — tabla comparativa por niche + top 5 fixes priorizados
  (severity DESC, reach DESC).
- `runs/<target>_<tool>.log` — log del scraper.
- `runs/<target>_<tool>_error.png` — screenshot Playwright si el
  scraper fallo (debug).

## Navegacion

- [Rule autoritativa](../../rules/ai-audit.md)
- [Skill invocable `/ai-audit`](../../skills/ai-audit/SKILL.md)
- [Plan de implementacion (efimero)](../../../docs/specs/ai-audit-tool/)
