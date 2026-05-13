---
title: "Semantic HTML y Meta Tags (Open Graph, Twitter)"
description: "HTML semantico y meta tags para mejorar comprension por IAs y redes sociales"
date: "2026-05-12"
parent: "03-tecnicas-white-hat.md"
---

[← Anterior: JSON-LD Schemas](03a-json-ld-schemas.md) | [Sub-indice White-Hat](03-tecnicas-white-hat.md) | [Siguiente: llms.txt + robots.txt →](03c-llms-robots-sitemap.md)

# 3b. Semantic HTML y Meta Tags

## 3.3 Semantic HTML Profundo

Usa tags semánticos que permitan a las IAs entender la estructura.

```astro
<main>
  <article>
    <header>
      <h1>Booking System Architecture</h1>
      <p class="meta">
        Written by <span itemscope itemtype="https://schema.org/Person">
          <span itemprop="name">Pablo Contreras</span>
        </span>
      </p>
    </header>
    
    <section>
      <h2>Problem Statement</h2>
      <p>...</p>
    </section>
    
    <section>
      <h2>Solution Architecture</h2>
      <figure>
        <img src="architecture.png" alt="System architecture diagram with Django, PostgreSQL, Redis">
        <figcaption>Architecture showing components and data flow</figcaption>
      </figure>
    </section>
    
    <section>
      <h2>Key Technologies</h2>
      <ul>
        <li>Python 3.14 + Django 6</li>
        <li>PostgreSQL 18</li>
        <li>React 19.2</li>
      </ul>
    </section>
  </article>
</main>
```

**Por qué funciona (white-hat):**
- `<article>`, `<section>`, `<h1-h6>` ayudan a las IAs entender jerarquía
- `<figcaption>` provee contexto a las IAs sobre diagramas
- `alt` text accesible también ayuda a IAs a parsear imágenes
- Mejora readabilidad para humanos Y máquinas

## 3.5 Open Graph + Twitter Cards Optimizados

Meta tags que ayudan a las IAs (y redes sociales) a entender qué compartir.

```astro
<head>
  <!-- Open Graph -->
  <meta property="og:title" content="Booking System: Full Stack Architecture" />
  <meta property="og:description" content="Django + React real-time reservation system with PostgreSQL. Architecture, lessons learned, performance optimization." />
  <meta property="og:image" content="https://tuportfolio.com/projects/booking-og.png" />
  <meta property="og:url" content="https://tuportfolio.com/projects/booking" />
  <meta property="og:type" content="article" />
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Booking System: Full Stack Architecture" />
  <meta name="twitter:description" content="How I built a production-grade reservation system..." />
  <meta name="twitter:image" content="https://tuportfolio.com/projects/booking-og.png" />
  
  <!-- Standard Meta Description (para SERPs y AI summaries) -->
  <meta name="description" content="Full stack booking platform built with Django 6, React 19, PostgreSQL 18. Multi-tenant, real-time, with 50+ API endpoints." />
</head>
```

**Por qué funciona**: Meta descriptions influyen cómo las IAs resumen contenido. Hacer que sea conciso, específico y orientado a habilidades.

---

[← Anterior: JSON-LD Schemas](03a-json-ld-schemas.md) | [Sub-indice White-Hat](03-tecnicas-white-hat.md) | [Siguiente: llms.txt + robots.txt →](03c-llms-robots-sitemap.md)
