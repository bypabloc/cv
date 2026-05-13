---
title: GEO - Generative Engine Optimization
parent: research-modern-portfolios-2026
section: 03
---

[← Anterior: ATS](02-optimizacion-ats.md) | [README](README.md) | [Siguiente → Estructura](04-estructura-contenido.md)

# GEO - Generative Engine Optimization

## Que es GEO?

**Generative Engine Optimization (GEO)** es la optimizacion de contenido para que sistemas de IA lo encuentren, comprendan y **citen** en sus respuestas.

**Diferencia critica vs SEO tradicional:**

| SEO Tradicional (Google, Bing) | GEO (ChatGPT, Claude, Perplexity) |
|--------|--------|
| Objetivo: aparecer en top 10 | Objetivo: ser citado en respuesta sintetizada |
| Metrica: posicion de ranking | Metrica: frecuencia de menciones (mencion rate) |
| Traffic: click en enlace | Traffic: click en fuente citada dentro de respuesta |
| Tiempo horizon: meses | Tiempo horizon: semanas (mas dinamico) |
| Indexacion: GoogleBot en robots.txt | Indexacion: Multiples crawlers (CCBot, GPTBot, etc) |

## Impacto Esperado

- **SEO tradicional declinara 25% by 2026, 50% by 2028** segun forecasts citados
- **Early adopters de GEO** ya reportan visibilidad en AI Overviews y respuestas de Claude/ChatGPT
- Los **profesionales que documentan GEO hoy** tendran ventaja en descubrimiento via AI

## Implementar llms.txt para Portfolios

**llms.txt es un archivo** ubicado en `https://yourdomain.com/llms.txt` que proporciona a las IA una **descripcion curada de tu sitio** en Markdown.

### Que va en llms.txt

```markdown
# [Tu Nombre] - Developer Portfolio

## About
Full-stack developer specializing in Python/Django and React.
7+ years building scalable systems for 100K+ users.

## Featured Work
- [Appointment Booking Platform](https://portfolio.com/projects/booking) — Microservices, PostgreSQL, real-time conflict resolution
- [Data Pipeline Optimization](https://portfolio.com/projects/data) — 40% latency reduction via cache strategy

## Expertise
- Python 3.14, Django 6, PostgreSQL 18, Docker
- Microservices architecture, API design, TDD
- Personal branding, portfolio optimization, GEO

## Contact
- Portfolio: https://portfolio.com
- GitHub: https://github.com/username
- LinkedIn: https://linkedin.com/in/username
```

**Ventajas:**
- LLMs leen llms.txt primero para entender un sitio
- Acelera indexacion en sistemas de IA
- Aumenta probabilidad de ser citado en respuestas

## Optimizacion Tecnica para GEO

| Elemento | Recomendacion 2026 |
|----------|----------|
| **robots.txt** | Asegura que `User-agent: CCBot, GPTBot` no esten bloqueados |
| **Accesibilidad** | Estrutura HTML semantica, headers jerarquicos (H1, H2, H3) |
| **Contenido** | Respuestas claras al inicio de secciones, listas en vez de parrafos largos |
| **Velocidad** | LLMs prefieren sitios que cargan rapido (Core Web Vitals) |
| **Schema/JSON-LD** | Person, ProfilePage, Article con autor (boost de autoridad) |
| **Author Info** | Credenciales visibles, links a social profiles |

## Estrategia Integral: SEO + GEO

Para 2026, tu portfolio debe optimizar **ambos** simultaneamente:

```
┌─────────────────────────────────────────────┐
│  Content + Technical Foundation             │
│  • HTML semantico, Core Web Vitals OK       │
│  • llms.txt + Schema.org Person/ProfilePage│
│  • robots.txt permite LLM crawlers          │
└─────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
   SEO (Google)           GEO (AI Engines)
   • Meta tags            • Author mentions
   • Internal linking     • Citation-worthy content
   • Keywords natural     • AI-readable structure
```

---

[← Anterior: ATS](02-optimizacion-ats.md) | [README](README.md) | [Siguiente → Estructura](04-estructura-contenido.md)
