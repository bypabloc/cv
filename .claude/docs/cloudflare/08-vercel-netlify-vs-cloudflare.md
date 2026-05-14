# Comparacion: Cloudflare Pages vs Vercel vs Netlify

> Por que elegimos Cloudflare Pages para este portfolio. Pricing 2026 y
> trade-offs concretos.

[← Script](./07-script-idempotente.md) | [README](./README.md) | [Siguiente: Workers Static Assets →](./09-workers-static-assets-future.md)

## Veredicto rapido

**Cloudflare Pages** para este caso. Razones:

1. Free tier permite uso comercial (Vercel Hobby NO lo permite)
2. Bandwidth ilimitado (Vercel: 100GB/mes, Netlify: ~30GB)
3. 500 builds/mes/proyecto × 6 proyectos = 3000 builds/mes total
4. SSL automatico, DNS unificado con el hosting
5. Plan upgrade barato y opcional ($5/proyecto solo si necesitas 5+
   concurrent builds)

## Tabla comparativa (2026)

| Capacidad | Cloudflare Pages Free | Vercel Hobby | Netlify Free |
|-----------|----------------------|--------------|---------------|
| Builds/mes | 500/proyecto | 100 soft | ~20 (300 credits / 15 each) |
| Bandwidth | **Unlimited** | 100 GB | ~30 GB |
| Concurrent builds | 1 | 1 | 1 |
| Custom domains | 100/proyecto | 50/proyecto | Sin limite explicito |
| Uso comercial | **Permitido** | **PROHIBIDO** | Permitido |
| SSL automatico | Si | Si | Si |
| Edge locations | 300+ | 70+ | 50+ |
| Pricing del primer plan pagado | $5/proyecto/mes | $20/mes | $19/mes |
| Limit upgrade Pro | 5,000 builds, unlimited bw | Unlimited | Unlimited |

### Pricing modelo concreto (portfolio con ~100-1000 visits/mes)

| Plataforma | Costo mensual estimado | Notas |
|-----------|------------------------|-------|
| Cloudflare Pages | **$0** | Free tier cubre todo |
| Vercel | **$20/mes** | Hobby prohibe comercial → forzado a Pro |
| Netlify | $0-$19/mes | Free funciona pero bandwidth tight con 6 apps |

## Por que NO Vercel

- **Commercial use prohibido en Hobby tier**: tu portfolio es comercial
  (CV → contratos). Vercel ToS exige Pro ($20/mes) para cualquier uso
  con fin comercial, incluso si no monetizas directamente.
- 100 GB bandwidth cap: 6 apps con ~500MB/visit cada una agotan en
  ~33k visits/mes. Hoy sobra, pero si crece toca pagar.
- DX excelente para Next.js, pero Astro estatico no aprovecha las
  ventajas (preview deployments, edge functions, ISR).

## Por que NO Netlify

- Bandwidth ~30GB free, lo cual es tight para 6 apps simultaneas (cada
  carga inicial de 1-2MB con sitio entero × 6 = saturas rapido).
- Pricing por credits es opaco: builds y bandwidth comparten una bolsa,
  dificil de predecir.
- Build credits limitan a ~20-30 builds/mes (vs 3000 en CF).

## Por que SI Cloudflare Pages

### Ventajas concretas

1. **Free tier permanente para uso comercial**: portfolio crece sin
   miedo a tener que migrar por costos.
2. **Bandwidth ilimitado**: si tu portfolio se viraliza, no te corta el
   gas.
3. **Latencia global**: 300+ edge locations vs 70 de Vercel. Mejor para
   audiencia LATAM (tu mercado: Chile, Mexico).
4. **DNS unificado**: si tu dominio ya esta en CF DNS, todo (DNS + CDN
   + hosting + WAF + SSL) se gestiona desde 1 dashboard.
5. **Sin lock-in**: build es plain Astro static, podes migrar a Vercel
   /Netlify en cualquier momento subiendo el `dist/`.

### Limitaciones (no aplican aqui)

- **Workers/SSR**: si necesitas server-side rendering, CF Pages tiene
  Pages Functions o migrar a Workers Static Assets. Astro static no
  los necesita.
- **Image optimization**: CF tiene Images ($5/mes) pero no es necesario
  para portfolio (las imagenes se pueden optimizar en build con
  @astrojs/sharp).
- **Analytics**: CF Web Analytics es free y basico. Si quieres mas:
  Plausible, Fathom, Vercel Analytics (paid).

## Cuando elegir cada uno (general)

| Caso | Recomendacion |
|------|---------------|
| Portfolio/CV (este caso) | **Cloudflare Pages** |
| Next.js SSR/ISR pesado | Vercel (Astro funciona OK pero Vercel optimiza Next) |
| JAMstack con muchas Functions | Netlify (Functions integrados son simples) |
| E-commerce escala / global | Cloudflare (Pages + Workers + R2 + KV) |
| SaaS B2B con SSR | Vercel (DX para developers/equipos) |
| Side project sin presupuesto | Cloudflare (free tier indefinido) |

## Limites del free tier de CF que SI podrias tocar

| Limite | Cuando preocuparte |
|--------|--------------------|
| 500 builds/mes/proyecto | Si haces 100+ pushes/dia a main |
| 1 concurrent build | Si tenes prisa por deployar 6 cambios simultaneos |
| 100MB max file | Si vas a servir videos sin CDN externo |
| 20K files/deployment | Si tu build genera muchos chunks |
| 25MB max `_headers`/`_redirects` | Improbable |

Si tocas algun limite: Pages Pro ($5/proyecto/mes) lo soluciona.

## Migration path entre proveedores

Como el build es `pnpm build` → `dist/` estatico, migrar entre los 3 es
trivial:

| Desde | Hacia | Pasos |
|-------|-------|-------|
| CF Pages → Vercel | Conectar repo + Vercel detecta Astro automatic |
| Vercel → Netlify | Idem |
| Netlify → CF Pages | Igual + ajustar build command para pnpm |

Los `_headers` files son sintaxis comun de Cloudflare y Netlify (Vercel
usa `vercel.json` con sintaxis distinta).

## TL;DR

Para este portfolio: **Cloudflare Pages, free tier, 6 proyectos
separados**. Sin razones tecnicas o economicas para pagar o cambiar de
proveedor en el futuro previsible.
