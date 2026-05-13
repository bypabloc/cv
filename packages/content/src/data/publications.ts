/**
 * @module publications
 * @description 5 artículos publicados en Medium (2023).
 *   Fuente: .claude/docs/cv/07-publicaciones.md.
 */
import { type Publication, PublicationSchema } from '../schemas'

const raw: Publication[] = [
  {
    slug: 'docker-wsl2',
    title:
      'Instalando Docker y Docker-compose en WSL2 Ubuntu sin Naufragar en el Intento',
    platform: 'Medium',
    url: 'https://bypablo.medium.com/un-viaje-épico-en-código-instalando-docker-y-docker-compose-en-wsl2-ubuntu-sin-naufragar-en-el-b21f38a9571',
    date: '2023-06-04',
    summary: {
      es: 'Guía práctica para instalar Docker y Docker Compose en WSL2 (Ubuntu) sin frustrarse.',
      en: 'Practical guide to install Docker and Docker Compose on WSL2 (Ubuntu) without frustration.',
    },
    niches: ['architect', 'vibe', 'generic'],
  },
  {
    slug: 'typescript-tipos',
    title: 'Dominando el Mundo de los Tipos en TypeScript',
    platform: 'Medium',
    url: 'https://bypablo.medium.com/dominando-el-mundo-de-los-tipos-en-typescript-e543eb42eb9c',
    date: '2023-05-31',
    summary: {
      es: 'Tour por el sistema de tipos de TypeScript: qué son, cómo usarlos y por qué importan.',
      en: 'A tour of the TypeScript type system: what types are, how to use them and why they matter.',
    },
    niches: ['generic', 'architect'],
  },
  {
    slug: 'typescript-undefined',
    title: '¡Bienvenidos a TypeScript, no más "undefined"!',
    platform: 'Medium',
    url: 'https://bypablo.medium.com/bienvenidos-a-typescript-no-más-undefined-5e473f0f4670',
    date: '2023-05-30',
    summary: {
      es: 'Introducción a TypeScript desde JavaScript: ventajas, setup y los primeros tipos.',
      en: 'TypeScript intro from a JavaScript background: benefits, setup and first types.',
    },
    niches: ['generic'],
  },
  {
    slug: 'js-vs-ts',
    title:
      'JavaScript vs TypeScript: ¡El choque de titanes que desencadena una guerra de tipos!',
    platform: 'Medium',
    url: 'https://bypablo.medium.com/javascript-vs-typescript-el-choque-de-titanes-que-desencadena-una-guerra-de-tipos-dadc70c06766',
    date: '2023-05-29',
    summary: {
      es: 'Comparativa pragmática entre JavaScript y TypeScript: cuándo conviene cada uno.',
      en: 'Pragmatic comparison between JavaScript and TypeScript: when to use each.',
    },
    niches: ['generic'],
  },
  {
    slug: 'type-vs-interface-marvel',
    title:
      "Explorando 'type' e 'interface' en TypeScript: Un Enfoque en el Universo Marvel",
    platform: 'Medium',
    url: 'https://bypablo.medium.com/explorando-type-e-interface-en-typescript-un-enfoque-en-el-universo-marvel-4ad47317838e',
    date: '2023-05-28',
    summary: {
      es: "Diferencias prácticas entre 'type' e 'interface' en TypeScript, explicadas con analogías Marvel.",
      en: "Practical differences between 'type' and 'interface' in TypeScript, explained with Marvel analogies.",
    },
    niches: ['generic'],
  },
]

export const publications: Publication[] = raw.map((p) =>
  PublicationSchema.parse(p),
)
