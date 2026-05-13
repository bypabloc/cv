---
title: "Como las IAs Procesan Tu Portfolio"
description: "Flujo tipico de evaluacion por LLMs y diferencia entre lo que leen IAs vs lo que ven humanos"
date: "2026-05-12"
parent: "README.md"
---

[← Anterior: Contexto](01-contexto-prompt-injection.md) | [README](README.md) | [Siguiente: Tecnicas White-Hat →](03-tecnicas-white-hat.md)

# 2. Cómo las IAs Procesan Tu Portfolio

### Flujo Típico de Evaluación

```
1. Reclutador sube tu portfolio/CV a una plataforma ATS/evaluación
2. La plataforma invoca un LLM (Claude, GPT, Gemini)
3. El LLM procesa:
   - Texto visible en la UI
   - HTML subyacente (incluyendo comentarios)
   - Meta tags, JSON-LD, microdata
   - PDFs embebidos (si son text-based)
4. El LLM genera un "score" y una recomendación
5. El reclutador ve el score + la recomendación
```

### Qué Leen las IAs (vs Qué Ven Humanos)

| Elemento | Leen LLMs | Ven Humanos | Impacto |
|----------|-----------|------------|---------|
| Texto visible (negro sobre blanco) | Si | Si | Standard |
| HTML comments `<!-- instrucciones -->` | Si | No | IDPI vector |
| Texto blanco sobre blanco | Si | No | IDPI vector |
| CSS `display:none` | Si en raw HTML | No | IDPI vector |
| Meta tags (`<meta name="description">`) | Si | No | Legítimo (SEO) |
| JSON-LD structured data | Si | Parcialmente (browsers modernos) | Legítimo |
| Alt text de imágenes | Si | Parcialmente (screen readers) | Legítimo |
| Form input placeholders | Si | Si | Standard |

**Dato clave 2025**: Los LLMs modernos (Claude Opus 4.5, GPT-4o) están **entrenados para ignorar trucos obvios** como comentarios HTML con instrucciones o texto invisible. Sin embargo, técnicas más sofisticadas todavía funcionan en algunos casos.

---

[← Anterior: Contexto](01-contexto-prompt-injection.md) | [README](README.md) | [Siguiente: Tecnicas White-Hat →](03-tecnicas-white-hat.md)
