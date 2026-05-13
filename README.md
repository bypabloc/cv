# Portfolio multi-niche — Pablo Contreras (bypabloc)

> Monorepo Astro 5+ con 6 sitios estaticos desplegados en Cloudflare Pages.
> Cada sitio cuenta la misma historia profesional con un acento diferente.

## Sitios

| App | URL | Posicionamiento |
|-----|-----|-----------------|
| [apps/hub](apps/hub) | `the-full-stack.com` | Landing selector con 5 cards |
| [apps/generic](apps/generic) | `hub.the-full-stack.com` | Full Stack Senior — todas las skills |
| [apps/fintech](apps/fintech) | `fintech.the-full-stack.com` | Senior Full Stack Fintech LATAM |
| [apps/architect](apps/architect) | `architect.the-full-stack.com` | Frontend Architect + Microservicios |
| [apps/leader](apps/leader) | `leader.the-full-stack.com` | Tech Lead / Engineering Manager |
| [apps/vibe](apps/vibe) | `vibe.the-full-stack.com` | Vibe Coding / Claude Code / Dev tools |

## Stack

- **Astro 5+** static output, View Transitions, i18n (es default + en)
- **Tailwind v4** via `@tailwindcss/vite` + CSS vars del DS
- **TypeScript** strict + Biome v2 (linter + formatter)
- **Vitest** + happy-dom (unit tests, coverage v8)
- **pnpm 10** workspaces
- **Cloudflare Pages** (6 proyectos, deploy via GitHub Actions)

## Estructura del monorepo

```
.
├── apps/
│   ├── hub/         # the-full-stack.com (selector)
│   ├── generic/     # hub.the-full-stack.com
│   ├── fintech/     # fintech.the-full-stack.com
│   ├── architect/   # architect.the-full-stack.com
│   ├── leader/      # leader.the-full-stack.com
│   └── vibe/        # vibe.the-full-stack.com
├── packages/
│   ├── content/     # Zod schemas + datos del CV + filters/sort por nicho
│   ├── ui/          # Design system, componentes Astro, theme toggle
│   ├── seo/         # JSON-LD Person, llms.txt, sitemap, robots
│   ├── cv-pdf/      # Render CV a HTML (+ PDF opcional con Puppeteer)
│   └── app-shared/  # Layouts y secciones reutilizadas por las 6 apps
├── cloudflare/      # Docs de Cloudflare Pages
├── .github/         # CI/CD GitHub Actions
└── .claude/         # Rules, skills, hooks del agente
```

## Quick start

```bash
# Instalar
pnpm install

# Dev server (cualquier app)
pnpm --filter @portfolio/generic run dev
# -> http://localhost:4321

# Build todos
pnpm -r run build

# Build una sola app
pnpm --filter @portfolio/fintech run build

# Lint + typecheck
pnpm exec biome check .
pnpm -r --filter "./packages/*" run typecheck
pnpm -r --filter "./apps/*" exec astro check

# Tests + coverage
pnpm -r --filter "./packages/*" run test:coverage
```

## Scripts del root

| Script | Que hace |
|--------|----------|
| `pnpm run dev` | Dev server para todas las apps en paralelo |
| `pnpm run build` | Build todas las apps |
| `pnpm run preview` | Preview de todos los builds |
| `pnpm run lint` | Biome check |
| `pnpm run lint:fix` | Biome write |
| `pnpm run typecheck` | tsc + astro check |
| `pnpm run test` | Vitest en todos los packages |
| `pnpm run test:coverage` | Vitest con coverage v8 |
| `pnpm run clean` | Limpia dist, .astro, node_modules/.vite, coverage |

## Filosofía

- **GEO > SEO**: cada sitio tiene su propio JSON-LD Person, llms.txt y sitemap. Apuntamos a aparecer en respuestas de ChatGPT/Claude/Perplexity.
- **ATS-friendly**: `/cv.html` se genera del mismo content y es ATS-parseable.
- **Lighthouse 95+**: no librerías de animación pesadas. Vanilla CSS + IntersectionObserver minimal. View Transitions Astro 5+.
- **DRY**: 1 sola fuente de verdad de datos del CV en `packages/content`. Cada app filtra por nicho.
- **i18n**: español default + inglés via Astro i18n built-in. NO duplicar copy — content collections bilingues.

## Deploy

Push a `main` dispara `.github/workflows/deploy.yml` que solo rebuilda lo que cambió (path filtering por carpeta). Si cambia un `packages/*`, rebuild de las 6 apps.

Setup inicial: ver [cloudflare/pages-config.md](cloudflare/pages-config.md).

## Documentación detallada

- [.claude/docs/cv/](.claude/docs/cv/) — Datos del CV (fuente original)
- [.claude/rules/](.claude/rules/) — Convenciones del proyecto
- [cloudflare/pages-config.md](cloudflare/pages-config.md) — Setup Cloudflare
- [.claude/docs/README-research-portfolio-2026.md](.claude/docs/README-research-portfolio-2026.md) — Investigaciones 2026 que sustentan las decisiones de stack
