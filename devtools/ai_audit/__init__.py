"""ai_audit script: scraper de 4 herramientas de AI readiness.

Audita la preparacion del portfolio para crawlers/agentes de IA
(GPTBot, ClaudeBot, PerplexityBot, etc.) y motores de busqueda
generativa (ChatGPT Search, Perplexity, Google AI Overviews).

Comando: python devtools/run.py ai_audit [...]

Tools auditadas (ver devtools/ai_audit/tools/):
- isitagentready (Cloudflare, anonimo)
- aibotchecker (independiente, anonimo)
- ahrefs (cuenta gratis, storageState)
- semrush (cuenta gratis, storageState)

Output: tmp/ai-audit/<timestamp>/{snapshot.json,report.md}
Auth storage: docker/env/dev-cli/ai-audit/<tool>.json (LOCAL-ONLY).

Ver:
- .claude/rules/ai-audit.md
- .claude/skills/ai-audit/SKILL.md
- .claude/docs/ai-audit/
"""
