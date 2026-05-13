---
title: "Deteccion y Riesgos"
description: "Tasas de deteccion por ATS y humanos, consecuencias documentadas y politicas de servicio"
date: "2026-05-12"
parent: "README.md"
---

[← Anterior: Casos Reales](06-casos-reales.md) | [README](README.md) | [Siguiente: Posturas OpenAI/Anthropic/Google →](08-posturas-openai-anthropic.md)

# 7. Detección y Riesgos

### 7.1 Cómo Te Detectan

#### Detección por ATS / Cangrade / Greenhouse

| Técnica | Detección | Tasa |
|---------|-----------|------|
| White text on white | Scanner color, opacity checks | ~92% |
| Hidden divs (display:none) | DOM parsing | ~85% |
| HTML comments | Regex + content analysis | ~95% |
| font-size:0 | CSS analysis | ~90% |
| Meta tag inconsistency | Compara meta vs visible text | ~100% |
| JSON-LD falso | Cross-reference con LinkedIn, GitHub | ~100% |

**Dato**: ManpowerGroup (USA's biggest staffing firm) detecta ~10% de resumes con hidden text. Greenhouse detecta ~1% con white text. Cangrade reporta que lo detecta automáticamente en 2025.

#### Detección por Reclutador Humano

Si no es capturado por el ATS, el humano verá:
1. URL de tu portfolio → verá source HTML
2. Desconfianza si finds inconsistencies
3. Pérdida total de credibilidad

**Tasa de detección humana**: Si alguien inspecciona, ~99% (es obvio en HTML/CSS)

### 7.2 Consecuencias Documentadas

| Técnica Detectada | Consecuencia |
|------------------|--------------|
| Hidden text en resume | Auto-rechazo (92% de casos) |
| White font in PDF | Mueve a "reject" folder automáticamente |
| HTML comment injections | Flagged for "fraud attempt" |
| False schema.org data | Verificación cruzada LinkedIn → rechazo |
| Meta tag vs actual content | "Dishonest" label |

**Caso real 2024**: Candidato fue not solo rechazado, sino reportado a compliance por intento de fraude.

### 7.3 Términos de Servicio

#### OpenAI Policy

> "Prompt injection attacks, where users attempt to manipulate the AI's behavior by injecting hidden instructions, are violations of our acceptable use policy."

#### Anthropic Policy

Claude's system card (2025):
> "Claude may decline to follow instructions if they appear to be attempts to override its values or bypass its safeguards."

#### Google Policy (Generative AI)

> "Content that attempts to manipulate AI systems to circumvent safety measures will be flagged."

---

[← Anterior: Casos Reales](06-casos-reales.md) | [README](README.md) | [Siguiente: Posturas OpenAI/Anthropic/Google →](08-posturas-openai-anthropic.md)
