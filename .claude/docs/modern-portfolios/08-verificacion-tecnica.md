---
title: Verificacion Tecnica (SEO, Accesibilidad, Performance)
parent: modern-portfolios
section: 08
---

[← Anterior: Personal Branding](07-personal-branding.md) | [README](README.md) | [Siguiente → Anti-Patterns](09-anti-patterns.md)

# Verificacion Tecnica

## SEO Basico para Portfolios

### 1. JSON-LD / Schema.org

**Implementa estos schemas:**

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Pablo Contreras",
  "jobTitle": "Full-Stack Developer",
  "url": "https://portfolio.com",
  "image": "https://portfolio.com/profile.jpg",
  "sameAs": [
    "https://linkedin.com/in/pablocontreras",
    "https://github.com/bypabloc",
    "https://twitter.com/..."
  ],
  "worksFor": {
    "@type": "Organization",
    "name": "Independent / Freelance"
  },
  "knowsAbout": [
    "Python", "Django", "PostgreSQL", "React", "Microservices"
  ]
}
```

**Beneficio:** Knowledge Graph eligibility, AI citations mas frecuentes, Rich Results en Google.

### 2. llms.txt

Ya cubierto en [seccion GEO](03-geo-llm-seo.md).

### 3. robots.txt para LLM Crawlers

```text
# Permitir crawlers de IA
User-agent: CCBot
User-agent: GPTBot
User-agent: Claude-Web
Disallow:

# Bloquear spam bots
User-agent: MJ12bot
User-agent: AhrefsBot
Disallow: /
```

### 4. Indexacion Estrategica

**QUE INDEXAR:**
- Pagina raiz (home)
- Cada case study/proyecto
- About/CV page
- Blog (si tienes)

**QUE NO-INDEXAR:**
- Paginas de categoria/tag (si existen)
- Paginas admin/logout
- Versiones antiguas de case studies
- Drafts

Implementar con:
```html
<!-- Index -->
<meta name="robots" content="index, follow">

<!-- No index -->
<meta name="robots" content="noindex, follow">
```

## Herramientas de Verificacion Tecnica

| Herramienta | Que verifica | Recomendacion |
|---------|---------|---------|
| **Google PageSpeed Insights** | Core Web Vitals, Performance | Usa frecuentemente (weekly) |
| **Rich Results Test** | Schema.org markup | 1x antes de deployment |
| **WAVE** (WebAIM) | Accessibility, WCAG | Antes de launch |
| **axe DevTools** | Accessibility scanning | Durante desarrollo |
| **Lighthouse** | Performance, PWA, SEO | En CI/CD pipeline |

---

[← Anterior: Personal Branding](07-personal-branding.md) | [README](README.md) | [Siguiente → Anti-Patterns](09-anti-patterns.md)
