---
title: "Checklist Accionable"
description: "Plan semanal de implementacion white-hat en 4 semanas + mantenimiento mensual"
date: "2026-05-12"
parent: "README.md"
---

[← Anterior: Recomendacion Final](09-recomendacion-final.md) | [README](README.md) | [Siguiente: Tabla Comparativa →](11-tabla-comparativa.md)

# 10. Checklist Accionable

### Semana 1: Foundation (White-Hat Core)

- [ ] Escribir Person schema JSON-LD con 8+ sameAs links
- [ ] Validar con Google Rich Results Test y Anthropic's schema validator
- [ ] Agregar Article schema a cada proyecto/blog post
- [ ] Escribir llms.txt honesto

### Semana 2: Enhancement (White-Hat+)

- [ ] Refactor HTML con semantic tags (<article>, <section>, <nav>)
- [ ] Agregar alt text descriptivo a todas las imágenes
- [ ] Crear FAQ schema para 5-10 preguntas comunes
- [ ] Update Open Graph + meta descriptions

### Semana 3: Optimization (White-Hat++)

- [ ] Validar robots.txt y ai.txt
- [ ] Crear sitemap.xml
- [ ] Test con múltiples AI systems (Claude, ChatGPT, Perplexity)
- [ ] Link README prominently

### Semana 4: Verification

- [ ] Inspecciona tu portfolio HTML (F12) → verifica schema está correcto
- [ ] Prueba con `curl https://tuportfolio.com | grep "ld+json"` → debe encontrar schemas
- [ ] Pide a un reclutador que evalúe cómo se ve
- [ ] No escondas nada, todo debe ser visible y honesto

### Monthly: Maintenance

- [ ] Keep sameAs links updated
- [ ] Update projects/blog content
- [ ] Verify schema still valid
- [ ] Monitor para cualquier vulnerabilidad de prompt injection en tu dominio

---

[← Anterior: Recomendacion Final](09-recomendacion-final.md) | [README](README.md) | [Siguiente: Tabla Comparativa →](11-tabla-comparativa.md)
