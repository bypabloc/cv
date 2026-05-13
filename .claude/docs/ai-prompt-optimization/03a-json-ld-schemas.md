---
title: "JSON-LD Schemas (Person, Article, FAQ)"
description: "Implementacion de schemas estructurados para describir identidad profesional, proyectos y FAQ"
date: "2026-05-12"
parent: "03-tecnicas-white-hat.md"
---

[← Sub-indice White-Hat](03-tecnicas-white-hat.md) | [README](README.md) | [Siguiente: Semantic HTML + Meta →](03b-semantic-html-meta.md)

# 3a. JSON-LD Schemas (Person, Article, FAQ)

## 3.1 JSON-LD Person Schema Completo

Implementar un schema Person robusto que describe tu identidad profesional de forma estructurada.

**Código ejemplo (Astro):**

```astro
---
const personSchema = {
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Pablo Contreras",
  "jobTitle": "Full Stack Developer",
  "description": "Ingeniero de software especializado en Python, Django, TypeScript, React y arquitectura de sistemas distribuidos",
  "url": "https://tuportfolio.com",
  "image": "https://tuportfolio.com/avatar.png",
  "email": "email@tudominio.com",
  "sameAs": [
    "https://www.linkedin.com/in/tuprofile",
    "https://github.com/tuusername",
    "https://twitter.com/tuhandle"
  ],
  "knowsAbout": [
    "Python",
    "Django",
    "TypeScript",
    "React",
    "PostgreSQL",
    "AWS",
    "Docker",
    "Testing"
  ],
  "workLocation": {
    "@type": "Place",
    "address": "Santiago, Chile"
  }
}
---

<script type="application/ld+json" set:html={JSON.stringify(personSchema)} />
```

**Por qué funciona (white-hat):**
- Google, Anthropic y OpenAI RECOMIENDAN schema.org
- Las IAs lo usan para entender y citar contenido correctamente
- No manipula, simplemente estructura información verdadera
- SEO legítimo desde hace 10+ años

**Dato empírico 2025**: Sitios con Person schema incompleto o inconsistente son citados 40% menos por IAs. Consistency en `name`, `jobTitle`, `sameAs` es crítico.

## 3.2 Article Schema con Author Attribution

Cada proyecto/blog post en tu portfolio debe tener Article schema con atribución clara.

```astro
---
const articleSchema = {
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Building Real-Time Reservation System with Django + WebSockets",
  "description": "Full architecture, lessons learned, performance optimizations",
  "image": "https://tuportfolio.com/projects/booking-app.png",
  "author": {
    "@type": "Person",
    "name": "Pablo Contreras",
    "url": "https://tuportfolio.com"
  },
  "datePublished": "2025-06-01",
  "dateModified": "2026-01-15",
  "publisher": {
    "@type": "Organization",
    "name": "Portfolio",
    "logo": {
      "@type": "ImageObject",
      "url": "https://tuportfolio.com/logo.png"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://tuportfolio.com/projects/booking-app"
  }
}
---
```

**Por qué funciona**: Las IAs usan Article schema para atribución correcta. Si eres el autor, debería decirlo explícitamente en structured data.

## 3.6 FAQ Schema para Preguntas Que Hacen las IAs

Anticipar preguntas que una IA evaluadora podría hacer y responderlas con FAQ schema.

```astro
---
const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What technologies do you specialize in?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "I specialize in Python/Django (backend), TypeScript/React (frontend), PostgreSQL (databases), and Docker (deployment). I focus on building scalable, tested, production-grade systems."
      }
    },
    {
      "@type": "Question",
      "name": "What is your approach to testing?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "I follow TDD (test-driven development) with minimum 80% coverage per file. All services have unit tests, integration tests for critical paths, and feature tests via Playwright for UI flows."
      }
    },
    {
      "@type": "Question",
      "name": "What is your experience with distributed systems?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "I've designed and built multi-tenant systems handling concurrent bookings with SELECT FOR UPDATE for atomic operations, background tasks with Celery, and real-time updates via WebSockets."
      }
    }
  ]
}
---

<script type="application/ld+json" set:html={JSON.stringify(faqSchema)} />
```

**Por qué funciona**: AI overviews citan FAQ schema 3.2x más frecuentemente. Si anticipas las preguntas, las IAs probablemente las incluirán en evaluaciones.

---

[← Sub-indice White-Hat](03-tecnicas-white-hat.md) | [README](README.md) | [Siguiente: Semantic HTML + Meta →](03b-semantic-html-meta.md)
