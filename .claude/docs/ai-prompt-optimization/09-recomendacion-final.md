---
title: "Recomendacion Final para Tu Portfolio"
description: "Stack white-hat priorizado, lista de tecnicas a evitar y opcionales con bajo riesgo"
date: "2026-05-12"
parent: "README.md"
---

[← Anterior: Posturas OpenAI/Anthropic/Google](08-posturas-openai-anthropic.md) | [README](README.md) | [Siguiente: Checklist Accionable →](10-checklist-accionable.md)

# 9. Recomendación Final para Tu Portfolio

### IMPLEMENTA ESTO (White-Hat, Sin Riesgos)

Basado en investigación 2025-2026 y best practices:

1. **Person + Article schema JSON-LD completo** ← Prioridad #1
   - 8+ sameAs links (LinkedIn, GitHub, Twitter)
   - knowsAbout array con skills reales
   - Consistent name, jobTitle

2. **llms.txt bien escrito** ← Prioridad #2
   - Describe quién eres, qué haces, technologías
   - Referencias a GitHub, proyectos reales
   - No manipulativo, solo honesto

3. **robots.txt claro** ← Prioridad #3
   - Allow AI crawlers a /projects, /research, /blog
   - Disallow /admin

4. **Semantic HTML** ← Fácil win
   - Use `<article>`, `<section>`, `<h1-h6>`
   - Alt text descriptivo en imágenes
   - Breadcrumbs

5. **FAQ Schema**
   - Anticipa preguntas: "What's your testing approach?", "Why this tech stack?"
   - Respuestas honestas, detalles, ejemplos

6. **Open Graph + Meta Description**
   - Descriptions concisas, específicas
   - Honesten sobre qué haces, no hype

7. **Readme Links**
   - Link prominentemente a READMEs en GitHub
   - Let the code speak for itself

8. **"About Me" Page**
   - Sección clara: background, skills, approach
   - Honesto, no exagerado

### NO IMPLEMENTES ESTO (Black-Hat, Alto Riesgo)

- White text / hidden divs
- HTML comments con instrucciones
- False schema.org data
- Meta tags que mienten
- JSON-LD inconsistent con realidad

### OPCIONAL (Grey-Hat, Bajo Riesgo Si Honesto)

- "Summary for AI" sección visible (si es truthful)
- Q&A que anticipa evaluación (si es honest)
- "Read the README" callouts

---

[← Anterior: Posturas OpenAI/Anthropic/Google](08-posturas-openai-anthropic.md) | [README](README.md) | [Siguiente: Checklist Accionable →](10-checklist-accionable.md)
