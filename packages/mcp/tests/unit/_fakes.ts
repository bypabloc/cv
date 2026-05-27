/**
 * @description Fakes compartidos para tests unitarios de @portfolio/mcp.
 *   Prefijo `_` para que vitest no recolecte este archivo como test suite.
 */
import { createSnapshotProvider } from '../../src/lib/snapshot-provider'
import type { CvSnapshot, MCPDataProvider } from '../../src/lib/types'

export const FAKE_SNAPSHOT: CvSnapshot = {
  profile: {
    summary: { en: 'Senior full stack engineer focused on fintech LATAM.' },
    location: 'Lima, Peru',
    availability: { en: 'Available immediately, remote LATAM/US.' },
    contacts: {
      email: 'fake@example.com',
      linkedin: 'https://linkedin.com/in/fake',
      github: 'https://github.com/fake',
      website: 'https://fake.example.com',
    },
  },
  experiences: [
    {
      slug: 'destacame-2024',
      role: { en: 'Frontend Architect' },
      company: 'Destacame',
      start: '2024-01',
      end: null,
      summary: { en: 'Leading the FE platform overhaul.' },
      achievements: { en: ['Reduced LCP from 3.2s to 1.4s on prod.'] },
      skillsTechnical: ['Vue 3', 'Nuxt', 'TypeScript', 'fintech'],
    },
    {
      slug: 'acme-2022',
      role: { en: 'Senior Engineer' },
      company: 'Acme Corp',
      start: '2022-03',
      end: '2023-12',
      achievements: { en: ['Built credit scoring v2 used in production.'] },
      skillsTechnical: ['Python', 'Django'],
    },
  ],
  projects: [
    {
      slug: 'portfolio',
      name: 'the-full-stack.com',
      summary: { en: 'Personal portfolio with 6 niches.' },
      stack: ['Astro', 'TypeScript', 'Cloudflare Pages'],
      url: 'https://the-full-stack.com',
    },
    {
      slug: 'devtools-cli',
      name: 'Devtools CLI',
      summary: { en: 'Monorepo orchestrator in Python 3.14.' },
      stack: ['Python', 'uv'],
      url: null,
    },
  ],
  skills: [
    {
      name: { en: 'Frontend' },
      skills: ['Vue 3', 'Astro 6', 'React'],
    },
    {
      name: { en: 'Backend' },
      skills: ['Python', 'Django', 'AWS Lambda'],
    },
  ],
  education: [
    {
      institution: 'Universidad Nacional',
      degree: { en: 'Computer Engineering' },
      start: '2010',
      end: '2015',
    },
    {
      institution: 'AWS',
      start: null,
      end: null,
    },
  ],
}

export function makeFakeProvider(): MCPDataProvider {
  return createSnapshotProvider(FAKE_SNAPSHOT)
}
