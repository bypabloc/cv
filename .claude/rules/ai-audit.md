# AI readiness audit (devtools `ai_audit`)

> Como auditar que tan preparado esta el portfolio para crawlers/agentes
> de IA (ClaudeBot, GPTBot, PerplexityBot) y motores de busqueda
> generativa (ChatGPT Search, Perplexity, Google AI Overviews) usando
> el script `devtools/ai_audit`. Combina 4 herramientas externas via
> scraping headless (Playwright Python) y produce un snapshot JSON +
> reporte Markdown comparativo.

## Activacion

Aplica SIEMPRE que se trabaje con:

- El script `python devtools/run.py ai_audit [...]`
- Cualquier archivo bajo `devtools/ai_audit/`
- StorageState de Playwright en `docker/env/dev-cli/ai-audit/<tool>.json`
- Reportes generados en `tmp/ai-audit/<timestamp>/`
- Decisiones de "que mejorar primero para GEO/AI SEO" basadas en estos
  scores

NO aplica al SEO tradicional (Google Search Console, Lighthouse SEO,
Core Web Vitals) — esas pertenecen al skill `astro-portfolio` y a
otros flujos.

> **Estado**: rule + skill + docs estan escritos; la implementacion
> del script (`devtools/ai_audit/`) se entrega en el plan
> [docs/specs/ai-audit-tool/](../../docs/specs/ai-audit-tool/). Hasta
> mergear ese plan, los comandos `python devtools/run.py ai_audit ...`
> NO existen — leer este archivo como referencia del contrato a
> implementar.

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** correr el audit contra **prod** como fuente de verdad.
  dev/stage tienen `noindex` + robots bloqueando AI crawlers por
  diseno; auditarlos da scores falsos negativos. El flag `--env=stage`
  existe solo para validar regresiones de config (ej. confirmar que
  stage SI bloquea bots).
- **SIEMPRE** el `storageState` de auth (Ahrefs, Semrush) vive en
  `docker/env/dev-cli/ai-audit/<tool>.json` — categoria `dev-cli`,
  LOCAL-ONLY, gitignored. NUNCA en `client/` ni `server/` ni en SSM.
- **SIEMPRE** los reportes van a `tmp/ai-audit/<timestamp>/` — NUNCA
  a `docs/` ni a la raiz del repo. `tmp/` esta gitignored.
- **SIEMPRE** el orden de prioridad de fixes es: severity DESC, luego
  reach DESC (cuantos crawlers se ven afectados). El reporte lo
  ordena solo.
- **SIEMPRE** los 4 scrapers son INDEPENDIENTES — un fallo en uno
  NUNCA aborta el run; se reporta como `BLOCKED` o `ERROR` y se
  continua.
- **SIEMPRE** retry con backoff exponencial (5s, 15s, 45s) ante 4xx,
  5xx, timeout y challenge de Cloudflare. Tras 3 intentos: skip.
- **NUNCA** scrapear paginas que requieran login que no sea el
  storageState configurado del propio usuario (no extraer datos
  de cuentas ajenas).
- **NUNCA** correr el audit en serie contra los 4 tools sin pausa —
  los servidores aplican rate-limit. Sleep entre tools >= 5s aun en
  caso exitoso.
- **NUNCA** commitear `docker/env/dev-cli/ai-audit/*.json` (cookies
  de auth = credenciales personales).
- **NUNCA** correr el audit en CI/CD automatico — es scraping de
  servicios de terceros y puede romper sus ToS si se hace a alta
  frecuencia. Solo manual on-demand.

## Comando canonico

```bash
# Default: 6 homes de prod, las 4 tools, output a tmp/ai-audit/<ts>/
python devtools/run.py ai_audit

# Subset de niches (solo homes)
python devtools/run.py ai_audit --niches=hub,fintech

# Custom targets (niche + path)
python devtools/run.py ai_audit \
  --targets=architect:/projects,leader:/about

# Subset de tools (skip las que requieren login)
python devtools/run.py ai_audit \
  --tools=isitagentready,aibotchecker

# Otro env (raro — dev/stage estan disenados para bloquear crawlers)
python devtools/run.py ai_audit --env=stage

# Setup de auth (1 vez por tool, abre browser interactivo)
python devtools/run.py ai_audit setup --tool=ahrefs
python devtools/run.py ai_audit setup --tool=semrush

# Re-render del Markdown desde un snapshot JSON existente
python devtools/run.py ai_audit report \
  --snapshot=tmp/ai-audit/2026-05-25T10-30-00/snapshot.json
```

Acciones reportadas por target/tool: `OK` (score capturado) /
`PARTIAL` (capturado parcial, ej. sin login) / `BLOCKED` (Cloudflare
challenge tras 3 retries) / `ERROR` (DOM cambio, parser roto) /
`SKIPPED` (tool deshabilitado por flag).

## Flujo en orden

1. **Antes de correr el audit**: confirmar que prod esta deployado y
   accesible publicamente. Si las apps estan caidas, el score es
   irrelevante.
2. **Primera vez**: correr `ai_audit setup --tool=ahrefs` y
   `--tool=semrush` para guardar storageState. Las otras 2 son
   anonimas.
3. **Run**: el comando ejecuta hasta 24 audits (6 URLs x 4 tools por
   env) con retry + backoff. Tarda ~10-20 min para un env completo.
4. **Lectura del reporte**: abrir `report.md` del run. La tabla top
   compara los 6 niches; la seccion "Top 5 fixes priorizados" lista
   las acciones concretas con el path del archivo a tocar.
5. **Iteracion**: aplicar los fixes, redeployar prod, re-correr el
   audit. Comparar contra el snapshot anterior con
   `ai_audit report --diff=<snapshot1> --vs=<snapshot2>` (fase
   opcional, no incluida en MVP).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Correr el audit cada commit en CI | Scraping a alta frecuencia rompe ToS de las tools | Manual on-demand, max 1-2 por semana |
| Auditar dev/stage como gate de PR | Esos envs bloquean AI crawlers por diseno; score bajo es esperado | Solo prod como gate |
| Commitear `tmp/ai-audit/` al repo | Es scratch; pollute history y leak de URLs custom | Esta en `.gitignore` del proyecto |
| Commitear `docker/env/dev-cli/ai-audit/*.json` | Son cookies de auth = credenciales personales | Categoria `dev-cli`, LOCAL-ONLY, gitignored |
| Confiar solo en isitagentready (la de Cloudflare) | Mide standards emergentes; ignora brand mentions y crawl accesibility low-level | Combinar las 4 tools, ponderar por categoria |
| Bloquear el run global si un tool falla | Las 4 son ortogonales; perder 1 no invalida los otros 3 | Retry + skip + reportar como BLOCKED/ERROR |
| Implementar tracker de score historico en JSONL | Scope creep — el MVP es snapshot puntual | Diferir a fase posterior si hay demanda |
| Scrapear paths internos sin override explicito | Los tools cobran/limitan por URL; gastar limites en /404 es desperdicio | Default = home; paths internos via `--targets=` |

## Referencias cruzadas

- Skill: [`/ai-audit`](../skills/ai-audit/SKILL.md) — invocacion
  manual con keywords ES/EN
- Docs (knowledge tree): [.claude/docs/ai-audit/](../docs/ai-audit/)
  — tools evaluadas, auth setup, arquitectura, troubleshooting
- Plan de implementacion: [docs/specs/ai-audit-tool/](../../docs/specs/ai-audit-tool/)
  — efimero, se elimina al mergear el plan
- Skill relacionada: [`/modern-portfolios`](../skills/modern-portfolios/SKILL.md)
  — GEO + ATS + estrategia general; el audit es la medicion de eso
- Skill relacionada: [`/ai-prompt-optimization`](../skills/ai-prompt-optimization/SKILL.md)
  — white-hat AI SEO (JSON-LD, llms.txt, robots.txt) que el audit valida
- Rule relacionada: [secrets-strategy.md](secrets-strategy.md) —
  donde vive el storageState (categoria `dev-cli`)
- Rule relacionada: [devtools.md](devtools.md) — convenciones de
  scripts en `devtools/`
- Rule relacionada: [python.md](python.md) — Python 3.14, ruff,
  testing
