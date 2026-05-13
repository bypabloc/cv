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
      es: 'Genera documentación clara y bien formateada de la estructura de directorios e incluye contenido de archivos cuando sea necesario. Nació de la necesidad real de pasarle contexto estructural a un LLM sin copiar manualmente.',
      en: 'Generates clear, well-formatted documentation of a directory tree, optionally including file contents. Born from the actual need to feed structural context to an LLM without copy-pasting.',
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
    isConfidential: true,
  },
]

export const projects: Project[] = raw.map((p) => ProjectSchema.parse(p))
