---
title: Tecnologias Recomendadas
parent: modern-portfolios
section: 06
---

[← Anterior: Diseno Visual](05-diseno-visual-ux.md) | [README](README.md) | [Siguiente → Personal Branding](07-personal-branding.md)

# Tecnologias Recomendadas

## Static Site Generators (Recomendacion 2026)

**Recomendacion clara para portfolios**: **Astro** > Next.js para mayoria de casos.

| Caracteristica | Astro | Next.js | Hugo | Nuxt |
|---------|---------|---------|---------|---------|
| **Performance** | ~40% faster, 90% less JS | Good (+ server overhead) | Excellent (GO) | Good (Vue) |
| **Learning curve** | Easy (HTML-first) | Medium (React required) | Steep (Go templates) | Medium (Vue) |
| **Content focus** | Default | Heavy JS | Best | Good |
| **Portfolio use** | Ideal | Overkill | Good | Good |

**Por que Astro para portfolios:**

1. **Zero JavaScript by default** — sin overhead innecesario
2. **Static generation rapida** — builds en segundos, no minutos
3. **Markdown-native** — escribe case studies en `.md` directamente
4. **Partial hydration** — si necesitas interactividad (contact form), solo eso hidrata

**Por que Next.js SI para aplicaciones:**
- Si tu portfolio incluye dashboard, login, CMS, o estado complejo -> Next.js

## Hosting Recomendado (2026)

Para portfolios, ranking por valor:

| Plataforma | Free Tier | Bandwidth | Best For | Precio |
|---------|---------|---------|---------|---------|
| **Cloudflare Pages** | Unlimited | Unlimited | **RECOMENDADO: portfolios** | Free (Worker limits aplicables) |
| **Netlify** | Limited | 100GB/mo | JAMstack, forms integradas | Free + paid |
| **Vercel** | Limited | 50GB/mo | Next.js, pero costo mas alto | Free + expensive overage |

**Recomendacion 2026:**
- **Astro portfolio -> Cloudflare Pages** (mejor performance, no overage bills)
- **Next.js app -> Vercel** (integracion perfecta)
- **Contenido dinamico -> Netlify** (features JAMstack mejores)

## Headless CMS (Si necesitas contenido dinamico)

**Opciones 2026:**

| CMS | Tipo | Costo | Ideal para |
|---------|---------|---------|---------|
| **Sanity** | Cloud | Free (5M API calls/mo) | Contenido estructurado, flexible |
| **Contentful** | Cloud | Free tier limitado | Multidispositivo, contenido complejo |
| **Ghost** | Self-hosted | $29/mo | Blog + portfolio |
| **Headless WP** | Self-hosted | Free (pero hosting) | Familiar con WordPress |

**Para la mayoria de portfolios:** Markdown + Git (Astro nativo) > CMS adicional.

---

[← Anterior: Diseno Visual](05-diseno-visual-ux.md) | [README](README.md) | [Siguiente → Personal Branding](07-personal-branding.md)
