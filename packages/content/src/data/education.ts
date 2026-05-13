/**
 * @module education
 * @description Educación formal e informal. Fuente: .claude/docs/cv/03-educacion.md.
 */
import { type Education, EducationSchema } from '../schemas'

const raw: Education[] = [
  {
    slug: 'uptyab',
    institution:
      'Universidad Politécnica Territorial de Yaracuy Arístides Bastidas (UPTYAB)',
    degree: {
      es: 'Ingeniería Informática',
      en: 'Informatics Engineering',
    },
    start: '2011',
    end: '2016',
    url: 'http://www.uptyab.edu.ve/web/index.php',
    description: {
      es: 'Adquirí conocimientos en programación, bases de datos, redes, sistemas operativos y arquitectura de software.',
      en: 'Acquired knowledge in programming, databases, networks, operating systems and software architecture.',
    },
  },
  {
    slug: 'udemy',
    institution: 'Udemy — Desarrollo Web',
    start: '2017',
    end: 'Actual',
    url: 'https://udemy.com',
    description: {
      es: 'Múltiples cursos de desarrollo web: JavaScript, React, Vue, Node, SQL y más, manteniendo la filosofía de aprender a mi ritmo.',
      en: 'Multiple web development courses: JavaScript, React, Vue, Node, SQL and more, keeping the philosophy of self-paced continuous learning.',
    },
  },
  {
    slug: 'youtube-autodidacta',
    institution: 'YouTube — Desarrollo Web (autodidacta)',
    start: '2012',
    end: 'Actual',
    url: 'https://youtube.com',
    description: {
      es: 'Desde 2013 accedo a material gratuito y de paga en línea; no paro de aprender.',
      en: 'Since 2013 I have leveraged free and paid online material; I never stop learning.',
    },
  },
]

export const education: Education[] = raw.map((e) => EducationSchema.parse(e))
