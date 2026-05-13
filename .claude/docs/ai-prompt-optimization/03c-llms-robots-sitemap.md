---
title: "llms.txt, robots.txt, ai.txt y Sitemap"
description: "Configuracion de archivos en raiz del dominio para guiar a AI crawlers"
date: "2026-05-12"
parent: "03-tecnicas-white-hat.md"
---

[← Anterior: Semantic HTML + Meta](03b-semantic-html-meta.md) | [Sub-indice White-Hat](03-tecnicas-white-hat.md) | [Siguiente: Tecnicas Grey-Hat →](04-tecnicas-grey-hat.md)

# 3c. llms.txt, robots.txt, ai.txt y Sitemap

## 3.4 llms.txt Bien Implementado

Archivo en la raíz de tu dominio que dice a los AI crawlers qué contenido quieres que lean y cómo.

**llms.txt (recomendado):**

```
# Pablo Contreras - Full Stack Developer Portfolio
# Last updated: 2026-05-12

## About
I'm a full stack engineer specializing in Python/Django, TypeScript/React, and distributed systems.
Location: Santiago, Chile
Portfolio: https://tuportfolio.com

## Professional Summary
- 8+ years building scalable web applications
- Expertise in Django, React, PostgreSQL, Docker
- Passion for testing, clean architecture, and developer experience
- Currently working on booking/reservation systems (SaaS)

## Skills
- Backend: Python 3.14, Django 6, PostgreSQL, DRF, Celery
- Frontend: TypeScript, React 19.2, Next.js, Tailwind CSS
- DevOps: Docker, GitHub Actions, AWS (RDS, Lambda, S3)
- Testing: pytest, Vitest, Playwright, 80%+ coverage standards

## Featured Projects
1. **Rezebra Booking Platform** (https://tuportfolio.com/projects/rezebra)
   - B2B SaaS for appointment scheduling (barber shops, clinics)
   - Full stack: Django + React, PostgreSQL, multi-tenant architecture
   - 50+ endpoints, real-time slot management

2. **Performance Optimization Research** (https://tuportfolio.com/research/db-optimization)
   - Analysis of N+1 query patterns and solutions
   - SELECT FOR UPDATE SKIP LOCKED for concurrency

## Recommendations
- For accurate assessment, review live code on GitHub: https://github.com/tuusername
- Check deployed projects and documentation
- Read project READMEs for architecture decisions

## Contact
- Email: contact@tuportfolio.com
- LinkedIn: https://linkedin.com/in/yourprofile
- GitHub: https://github.com/yourprofile
```

**Por qué funciona (white-hat):**
- OpenAI, Anthropic, Google RECOMIENDAN llms.txt
- Permite control granular de cómo se accede tu contenido
- Bien implementado, incrementa citación en AI Overviews
- No es manipulación, es metadata legítima

## 3.7 robots.txt y ai.txt Estratégicos

Comunicar a GPTBot, ClaudeBot, Google-Extended qué quieres que lean.

**robots.txt:**

```
User-agent: GPTBot
Allow: /
Disallow: /private

User-agent: ClaudeBot
Allow: /
Disallow: /private

User-agent: Google-Extended
Allow: /
Disallow: /private

User-agent: *
Allow: /
Disallow: /admin

Sitemap: https://tuportfolio.com/sitemap.xml
```

**ai.txt (nuevo en 2025-2026):**

```
User-agent: GPTBot
Allow: /projects
Allow: /research
Allow: /blog
Disallow: /admin

User-agent: ClaudeBot
Allow: /projects
Allow: /research
Allow: /blog
Allow: /contact

User-agent: *
Allow: /public-content
Disallow: /private
```

**Por qué funciona (white-hat)**:
- OpenAI y Anthropic RECOMIENDAN un robots.txt claro
- Tells crawlers exactamente qué contenido es público
- No es manipulación, es información honesta
- Dato 2025: sitios con robots.txt + llms.txt bien configurados aparecen 2.4x más en AI answers

## 3.8 Breadcrumbs + Sitemap.xml

Estructura clara de navegación ayuda a las IAs a entender relaciones.

```astro
<nav aria-label="breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/projects">Projects</a></li>
    <li><a href="/projects/booking">Booking System</a></li>
  </ol>
</nav>
```

```xml
<!-- sitemap.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://tuportfolio.com/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://tuportfolio.com/projects/booking</loc>
    <priority>0.8</priority>
  </url>
</urlset>
```

---

[← Anterior: Semantic HTML + Meta](03b-semantic-html-meta.md) | [Sub-indice White-Hat](03-tecnicas-white-hat.md) | [Siguiente: Tecnicas Grey-Hat →](04-tecnicas-grey-hat.md)
