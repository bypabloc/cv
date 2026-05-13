---
title: "Posturas de OpenAI, Anthropic, Google"
description: "Politica oficial 2025 de los principales proveedores de LLMs frente a prompt injection"
date: "2026-05-12"
parent: "README.md"
---

[← Anterior: Deteccion y Riesgos](07-deteccion-riesgos.md) | [README](README.md) | [Siguiente: Recomendacion Final →](09-recomendacion-final.md)

# 8. Posturas de OpenAI, Anthropic, Google

### 8.1 OpenAI

**Postura 2025**:
- Acknowledges prompt injection is a real threat, pero "unlikely to ever be fully solved"
- Has trained a "hacker bot" that probes for weaknesses
- Recommends: input sanitization, data tagging, detection classifiers
- NO recomienda confiar en que prompt injection never happens

**Para portfolios**: Si un ATS usa GPT-4, es relativamente robusto a tricks simples, pero no garantizado.

### 8.2 Anthropic

**Postura 2025**:
- Claude Opus 4.5 fue explícitamente entrenado contra prompt injections
- Published [Mitigating the risk of prompt injections in browser use](https://www.anthropic.com/research/prompt-injection-defenses)
- Reducciones en attack success rate: de ~5-10% a ~1% en browser operations
- Transparencia: publica rates de success de ataques (algo que OpenAI no hace públicamente)

**Implicación**: Si tu portfolio será evaluado por Claude, es más difícil inyectar prompts.

### 8.3 Google

**Postura 2025**:
- Enfoque arquitectónico: restrict agentic systems capabilities
- SpamBrain y otros algoritmos detectan hidden content explícitamente
- robots.txt + llms.txt bien implementados = mejor visibility sin necesidad de tricks

**Para portfolios**: Si Google indexa tu portfolio, técnicas white-hat (robots.txt, llms.txt, schema) son la mejor estrategia.

---

[← Anterior: Deteccion y Riesgos](07-deteccion-riesgos.md) | [README](README.md) | [Siguiente: Recomendacion Final →](09-recomendacion-final.md)
