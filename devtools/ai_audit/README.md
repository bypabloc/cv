# ai_audit

Scraper Python (Playwright) que audita la preparacion del portfolio
para crawlers/agentes de IA y motores de busqueda generativa.

## Comandos

```bash
# Audit default: 6 homes de prod, las 4 tools
python devtools/run.py ai_audit

# Subset de niches / tools / paths
python devtools/run.py ai_audit --niches=hub,fintech
python devtools/run.py ai_audit --tools=isitagentready,aibotchecker
python devtools/run.py ai_audit --targets=architect:/projects,leader:/about

# Setup auth (1 vez por tool, abre browser interactivo)
python devtools/run.py ai_audit setup --tool=ahrefs
python devtools/run.py ai_audit setup --tool=semrush
python devtools/run.py ai_audit setup --tool=ahrefs --check-only

# Re-render del Markdown desde un snapshot
python devtools/run.py ai_audit report \
  --snapshot=tmp/ai-audit/2026-05-25T10-30-00/snapshot.json
```

## Estructura

| Modulo | Responsabilidad |
|--------|----------------|
| `flags.py` | Parsing + validacion (3 subcomandos: audit/setup/report) |
| `catalog.py` | Resolver `(env, niche, path)` -> URL absoluta |
| `auth.py` | Load/save Playwright storageState (dev-cli, local-only) |
| `scraper.py` | Orquestador async con retry/backoff |
| `tools/base.py` | Tipos `Status`, `Severity`, `Fix`, `ToolResult`, `Tool` |
| `tools/<X>.py` | Scraper concreto por tool (4 archivos) |
| `report.py` | JSON snapshot + Markdown renderer |
| `main.py` | Router de subcomandos |

## Output

```
tmp/ai-audit/<ISO-timestamp>/
├── snapshot.json     # crudo (por target,tool -> score+categorias+fixes)
├── report.md         # legible (tabla comparativa + top 5 fixes)
└── runs/<target>_<tool>.{log,error.png}
```

## Auth storage (local-only)

```
docker/env/dev-cli/ai-audit/
├── ahrefs.json       # Playwright storageState (cookies + localStorage)
└── semrush.json
```

NUNCA commitear (gitignored). Categoria `dev-cli`: ver
`.claude/rules/secrets-strategy.md`.

## Documentacion

- Rule: `.claude/rules/ai-audit.md`
- Skill invocable: `.claude/skills/ai-audit/SKILL.md` (`/ai-audit`)
- Knowledge tree: `.claude/docs/ai-audit/`
- Plan de implementacion (efimero hasta mergear): `docs/specs/ai-audit-tool/`
