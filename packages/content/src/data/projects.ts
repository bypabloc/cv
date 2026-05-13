/**
 * @module projects
 * @description Side projects + case studies destacados.
 *   - FastStruct: extensión VS Code pública.
 *   - CV-Astro: este propio portfolio (meta case study).
 *   - Destacame Debt Chile / Mexico Credit: case studies confidenciales (no repo).
 */
import { type Project, ProjectSchema } from '../schemas'

const raw: Project[] = [
  {
    slug: 'faststruct',
    name: 'FastStruct',
    summary: {
      es: 'Extensión de VS Code para visualizar y documentar la estructura de un proyecto en segundos, optimizando workflows con IA.',
      en: 'VS Code extension that visualizes and documents a project structure in seconds, optimized for AI workflows.',
    },
    description: {
      es: 'Genera documentación clara y bien formateada de la estructura de directorios e incluye contenido de archivos cuando sea necesario. Nació antes de Claude Code para pasarle contexto estructural a la interfaz web de Claude sin copiar manualmente.',
      en: 'Generates clear, well-formatted documentation of a directory tree, optionally including file contents. Born before Claude Code to feed structural context to the Claude web interface without copy-pasting.',
    },
    url: 'https://marketplace.visualstudio.com/items?itemName=the-full-stack.faststruct',
    repo: 'https://github.com/bypabloc/faststruct',
    status: 'active',
    niches: ['vibe', 'architect', 'generic'],
    priority: { vibe: 100, architect: 70, generic: 80 },
    stack: ['TypeScript', 'VS Code Extension API', 'Node.js'],
    caseStudy: {
      es: 'Problema: pasarle estructura de proyecto a Claude/ChatGPT requería pegar manualmente cada path. Solución: extensión que genera markdown estructurado con un click. Impacto: workflow personal 5x más rápido al instruir IAs.',
      en: 'Problem: feeding project structure to Claude/ChatGPT meant pasting each path manually. Solution: an extension that produces structured markdown in one click. Impact: 5x faster personal workflow when instructing AIs.',
    },
    caseStudyDetailed: {
      problem: {
        es: 'Antes de Claude Code (mayo 2025) usaba la interfaz web de Claude para programar. Pasarle el contexto de un proyecto significaba copiar archivo por archivo manualmente.',
        en: 'Before Claude Code (May 2025) I used the Claude web interface to code. Sharing project context meant copy-pasting file by file manually.',
      },
      process: {
        es: 'Construí FastStruct como extensión VS Code en TypeScript: comando único que escanea workspace, respeta .gitignore, formatea en markdown estructurado y copia al portapapeles. Patrones de exclusión configurables.',
        en: 'I built FastStruct as a TypeScript VS Code extension: single command that scans the workspace, honors .gitignore, formats structured markdown and copies to clipboard. Configurable exclusion patterns.',
      },
      result: {
        es: 'Workflow personal 5x más rápido para instruir IAs. Publicada en Marketplace, sigue siendo útil incluso ahora con Claude Code para casos donde necesito contexto compacto para sub-agentes o resumenes externos.',
        en: '5x faster personal workflow when instructing AIs. Published in the Marketplace, still useful even now with Claude Code for cases where I need compact context for sub-agents or external summaries.',
      },
    },
    metrics: {
      speedup: '5x faster context handoff',
      adoption: 'Marketplace published',
      precursor: 'Pre-Claude-Code era (< May 2025)',
    },
    isConfidential: false,
  },
  {
    slug: 'mvp-template-full-stack',
    name: 'MVP template Full Stack',
    summary: {
      es: 'Template público que uso de referencia para nuevos proyectos: estructura .claude/ con skills, rules, hooks, devtools CLI, conformance y testing.',
      en: 'Public template I use as reference for new projects: .claude/ structure with skills, rules, hooks, devtools CLI, conformance and testing.',
    },
    description: {
      es: 'Blueprint del flujo vibe coding completo: Astro 6 + Django stack-ready, harness de Claude Code estandarizado, quality gates en pre-commit/pre-push, devtools CLI en Python 3.14 con uv. Mismo patrón que adopté en Destacame al introducir Claude Code en el equipo.',
      en: 'Blueprint of the full vibe coding workflow: Astro 6 + Django stack-ready, standardized Claude Code harness, quality gates in pre-commit/pre-push, Python 3.14 + uv devtools CLI. Same pattern I adopted at Destacame when rolling out Claude Code in the team.',
    },
    url: 'https://github.com/bypabloc/mvp-template-full-stack',
    repo: 'https://github.com/bypabloc/mvp-template-full-stack',
    status: 'active',
    niches: ['vibe', 'architect', 'generic'],
    priority: { vibe: 92, architect: 75, generic: 65 },
    stack: [
      'Claude Code',
      'Astro 6',
      'TypeScript',
      'Python 3.14',
      'Django',
      'Biome v2',
      'uv',
    ],
    caseStudy: {
      es: 'Blueprint para arrancar proyectos full stack con flujo vibe coding estandarizado: harness Claude Code + quality gates + devtools CLI. Mismo patrón usado al implementar Claude Code en Destacame.',
      en: 'Blueprint to bootstrap full stack projects with a standardized vibe coding workflow: Claude Code harness + quality gates + devtools CLI. Same pattern used when rolling out Claude Code at Destacame.',
    },
    metrics: {
      coverage: 'Skills + Rules + Hooks + Devtools',
      role: 'Reference for Destacame Claude Code rollout',
      stack: 'Astro + Django + Python 3.14 + uv',
    },
    isConfidential: false,
  },
  {
    slug: 'cv-builder',
    name: 'CV builder (bypabloc/cv)',
    summary: {
      es: 'CV builder construido en una sola noche con Claude Code (12 mayo 2026). Demo end-to-end del flujo vibe coding moderno: data → render → deploy.',
      en: 'CV builder shipped in a single night with Claude Code (May 12, 2026). End-to-end demo of the modern vibe coding workflow: data → render → deploy.',
    },
    description: {
      es: 'Proyecto que empecé la noche del 12/05/2026 y terminé al día siguiente. Demuestra cómo construir una herramienta funcional en pocas horas usando Claude Code como copiloto. Código revisado, testeado y mantenido por mí — la IA es herramienta, no autor.',
      en: 'Project I started on the night of 2026-05-12 and finished the next day. Demonstrates building a functional tool in a few hours using Claude Code as a copilot. Code reviewed, tested and maintained by me — AI is a tool, not an author.',
    },
    url: 'https://github.com/bypabloc/cv',
    repo: 'https://github.com/bypabloc/cv',
    status: 'active',
    niches: ['vibe', 'generic'],
    priority: { vibe: 98, generic: 70 },
    stack: ['TypeScript', 'Claude Code', 'Astro', 'Vibe Coding'],
    caseStudy: {
      es: 'Problema: necesitaba un CV builder propio que pudiera iterar rápido. Solución: vibe coding session con Claude Code, prompts iterativos, code review en cada commit. Impacto: MVP funcional en una noche.',
      en: 'Problem: I needed a CV builder I could iterate on fast. Solution: vibe coding session with Claude Code, iterative prompts, code review on every commit. Impact: working MVP in one night.',
    },
    caseStudyDetailed: {
      problem: {
        es: 'Necesitaba un CV builder propio para iterar rápido sobre datos del CV sin tocar a mano cada exportación. Calendario apretado: una noche disponible.',
        en: 'I needed my own CV builder to iterate fast on CV data without hand-editing each export. Tight timeline: one night available.',
      },
      process: {
        es: 'Sesión vibe coding con Claude Code el 12/05/2026: prompts iterativos para definir esquema de datos, render, themes y export. Code review humano en cada commit. Nada de copy-paste sin entender.',
        en: 'Vibe coding session with Claude Code on 2026-05-12: iterative prompts to define data schema, render, themes and export. Human code review on every commit. No copy-paste without understanding.',
      },
      result: {
        es: 'MVP funcional en una sola noche, repo público en bypabloc/cv. Demuestra que la combinación Claude Code + revision humana entrega producto sin sacrificar mantenibilidad.',
        en: 'Working MVP in a single night, public repo at bypabloc/cv. Demonstrates that Claude Code + human review combo ships product without sacrificing maintainability.',
      },
    },
    metrics: {
      timeline: 'Built in one night (May 12-13, 2026)',
      ai_tool: 'Claude Code as copilot',
      attribution: '0 AI attribution in commits (company policy)',
    },
    isConfidential: false,
  },
  {
    slug: 'portfolio-astro',
    name: 'Portfolio multi-nicho',
    summary: {
      es: 'Este mismo portfolio: monorepo Astro 6 con 5 sitios independientes desplegados en Cloudflare Pages, optimizado para GEO/LLM-SEO.',
      en: 'This very portfolio: an Astro 6 monorepo with 5 independent sites deployed to Cloudflare Pages, optimized for GEO/LLM-SEO.',
    },
    description: {
      es: 'Arquitectura monorepo con DS unificado, content collections compartidas, filtrado por nicho, dark/light/system theme y JSON-LD Person por sitio. Meta caso de estudio del stack.',
      en: 'Monorepo architecture with a unified DS, shared content collections, niche-based filtering, dark/light/system theming and per-site JSON-LD Person. Meta case study of the stack.',
    },
    url: 'https://the-full-stack.com',
    repo: 'https://github.com/bypabloc/portfolio',
    status: 'active',
    niches: ['vibe', 'architect', 'generic'],
    priority: { vibe: 95, architect: 80, generic: 75 },
    stack: ['Astro 6', 'TypeScript', 'Biome v2', 'pnpm', 'Cloudflare Pages'],
    isConfidential: false,
  },
  {
    slug: 'destacame-debt-chile',
    name: 'Sistema de saldar deudas (Chile)',
    summary: {
      es: 'Plataforma fintech B2C que ayuda a usuarios chilenos a negociar y saldar deudas con instituciones financieras.',
      en: 'Fintech B2C platform that helps Chilean users negotiate and settle debts with financial institutions.',
    },
    description: {
      es: 'Producto desarrollado en Destacame como Arquitecto Frontend. Integra microservicios Django + frontend Vue/Nuxt y maneja flujos sensibles de PII y compliance financiero.',
      en: 'Product built at Destacame as Frontend Architect. Integrates Django microservices with a Vue/Nuxt frontend and handles sensitive PII flows and financial compliance.',
    },
    status: 'active',
    niches: ['fintech', 'architect', 'generic'],
    priority: { fintech: 100, architect: 90, generic: 70 },
    stack: [
      'Vue',
      'Nuxt',
      'TypeScript',
      'Django',
      'Python',
      'AWS',
      'Microservicios',
    ],
    caseStudy: {
      es: 'Problema: los usuarios chilenos no tenían un canal claro para regularizar deudas y las instituciones perdían cobranzas. Solución: orquestación entre microservicios fintech con un flujo guiado de elegibilidad → oferta → pago. Impacto: mejora medible en la eficiencia operativa de cobranza y en la experiencia del usuario final (detalles bajo NDA).',
      en: 'Problem: Chilean users lacked a clear channel to regularize debts and institutions lost collections. Solution: orchestration across fintech microservices with a guided eligibility → offer → payment flow. Impact: measurable improvement in collection operational efficiency and end-user experience (details under NDA).',
    },
    caseStudyDetailed: {
      problem: {
        es: 'Los usuarios chilenos no tenian un canal claro para regularizar deudas y las instituciones financieras perdian cobranzas significativas. Datos sensibles (PII) + compliance financiero LATAM.',
        en: 'Chilean users lacked a clear channel to regularize debts and financial institutions were losing significant collections. Sensitive data (PII) + LATAM financial compliance.',
      },
      process: {
        es: 'Como Frontend Architect orqueste microservicios Django con frontend Vue/Nuxt: elegibilidad → oferta → pago. Manejo de PII con encriptacion en transito y reposo. Integracion con bureaus + verificacion KYC.',
        en: 'As Frontend Architect I orchestrated Django microservices with Vue/Nuxt frontend: eligibility → offer → payment. PII handling with encryption in transit and at rest. Bureau integrations + KYC verification.',
      },
      result: {
        es: 'Mejora medible en eficiencia operativa de cobranza y experiencia del usuario final. Plataforma sigue en produccion sirviendo el mercado chileno (metricas detalladas bajo NDA).',
        en: 'Measurable improvement in collection operational efficiency and end-user experience. Platform still in production serving the Chilean market (detailed metrics under NDA).',
      },
    },
    metrics: {
      market: 'Chile',
      compliance: 'PCI DSS aware · KYC · PII handling',
      architecture: 'Vue/Nuxt + Django microservices + AWS',
    },
    isConfidential: true,
  },
  {
    slug: 'destacame-credit-mexico',
    name: 'Producto de créditos (México)',
    summary: {
      es: 'Producto fintech que ofrece créditos personales con diferentes niveles a usuarios en México.',
      en: 'Fintech product offering tiered personal credit to users in Mexico.',
    },
    description: {
      es: 'Producto desarrollado en Destacame para el mercado mexicano. Frontend Vue/Nuxt + microservicios Django + integraciones con bureaus de crédito.',
      en: 'Product built at Destacame for the Mexican market. Vue/Nuxt frontend + Django microservices + credit-bureau integrations.',
    },
    status: 'active',
    niches: ['fintech', 'architect', 'generic'],
    priority: { fintech: 95, architect: 85, generic: 65 },
    stack: [
      'Vue',
      'Nuxt',
      'TypeScript',
      'Django',
      'Python',
      'AWS',
      'Microservicios',
    ],
    caseStudy: {
      es: 'Problema: los usuarios mexicanos necesitaban créditos accesibles con onboarding rápido. Solución: producto con niveles de crédito, scoring integrado y flujo de aprobación que minimiza fricción. Impacto: contribución al portafolio fintech LATAM de Destacame en el mercado mexicano (detalles bajo NDA).',
      en: 'Problem: Mexican users needed accessible credit with fast onboarding. Solution: tiered-credit product with embedded scoring and a low-friction approval flow. Impact: contribution to Destacame LATAM fintech portfolio in the Mexican market (details under NDA).',
    },
    caseStudyDetailed: {
      problem: {
        es: 'Mercado mexicano requeria creditos personales accesibles con onboarding rapido. Restricciones regulatorias locales + fricciones de KYC + integracion con bureaus de credito.',
        en: 'Mexican market required accessible personal credit with fast onboarding. Local regulatory constraints + KYC friction + credit bureau integrations.',
      },
      process: {
        es: 'Producto con tramos de credito + scoring embebido + flujo de aprobacion de baja friccion. Frontend Vue/Nuxt + microservicios Django + integraciones con bureaus mexicanos. Decisiones de arquitectura documentadas para sucesores.',
        en: 'Tiered-credit product + embedded scoring + low-friction approval flow. Vue/Nuxt frontend + Django microservices + Mexican credit bureau integrations. Documented architecture decisions for successors.',
      },
      result: {
        es: 'Contribucion clave al portafolio fintech LATAM de Destacame en el mercado mexicano. Reutilizacion de patrones del producto Chile con adaptacion regulatoria local (metricas bajo NDA).',
        en: 'Key contribution to Destacame LATAM fintech portfolio in the Mexican market. Pattern reuse from the Chilean product with local regulatory adaptation (metrics under NDA).',
      },
    },
    metrics: {
      market: 'México',
      product: 'Tiered credit + embedded scoring',
      architecture: 'Vue/Nuxt + Django + Bureau integrations',
    },
    isConfidential: true,
  },
]

export const projects: Project[] = raw.map((p) => ProjectSchema.parse(p))
