/**
 * @module dialogs/futuro-presente (engine)
 * @description Arbol de dialogo de la sala 8 (futuro, SINTETICA): un solo
 *   NPC — "Pablo del futuro" — que habla en primera persona de la vision
 *   profesional (informe 14 + ideas elegidas por el usuario 2026-07-05):
 *   el escalon Staff/Principal, la IA que pasa de herramienta a producto
 *   propio (indie/SaaS, emprendimiento LATAM), la multiplicacion via
 *   mentoria / open source / contenido publico, los nuevos rubros y el
 *   "siempre estudiante". Cierra invitando al CTA de contacto.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const FUTURO_PRESENTE_DIALOGS = {
  pablo: defineDialog({
    name: { es: 'Pablo — del futuro', en: 'Pablo — from the future' },
    chatter: [
      {
        es: 'El proximo commit es el que mas importa.',
        en: 'The next commit is the one that matters most.',
      },
      {
        es: 'Cada sala de este recorrido fue un rubro nuevo. La proxima tambien.',
        en: 'Every room in this journey was a new sector. So is the next one.',
      },
      {
        es: 'Al roadmap le falta un nodo: el tuyo.',
        en: 'The roadmap is missing one node: yours.',
      },
      {
        es: 'Los agentes ya escriben codigo; alguien decide cual vale la pena.',
        en: 'Agents already write code; someone decides which is worth it.',
      },
      {
        es: 'Spoiler: sale bien.',
        en: 'Spoiler: it turns out fine.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Soy Pablo — el de unas cuantas salas mas adelante. Esta es ' +
            'la unica sala que todavia no existe: se esta construyendo ' +
            'ahora mismo, commit a commit. ¿Que quieres saber del plan?',
          en:
            "I'm Pablo — the one a few rooms ahead. This is the only " +
            "room that doesn't exist yet: it is being built right now, " +
            'commit by commit. What do you want to know about the plan?',
        },
        options: [
          {
            label: {
              es: '¿Cual es el siguiente escalon?',
              en: "What's the next step up?",
            },
            next: 'staff-1',
          },
          {
            label: {
              es: '¿Que vas a construir con IA?',
              en: 'What will you build with AI?',
            },
            next: 'ia-1',
          },
          {
            label: {
              es: '¿Y ademas del codigo?',
              en: 'And beyond the code?',
            },
            next: 'mas-1',
          },
          {
            label: {
              es: '¿Como te contacto?',
              en: 'How do I reach you?',
            },
            next: 'contacto-1',
          },
        ],
      },
      'staff-1': {
        text: {
          es:
            'Staff / Principal Engineer — sin soltar el teclado. El ' +
            'escalon no es dejar de construir: es que lo que construyo ' +
            'desbloquee a mas gente. Decidir con codigo en la mano, no ' +
            'con diapositivas.',
          en:
            'Staff / Principal Engineer — without letting go of the ' +
            'keyboard. The step up is not to stop building: it is making ' +
            'what I build unblock more people. Deciding with code in ' +
            'hand, not slides.',
        },
        options: [
          {
            label: {
              es: '¿Y la arquitectura?',
              en: 'What about architecture?',
            },
            next: 'staff-2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      'staff-2': {
        text: {
          es:
            'Sistemas distribuidos robustos y observables, plataformas ' +
            'que multiplican equipos. Ya lo hice con microservicios y ' +
            'microfrontends en fintech; lo que viene es hacerlo a mas ' +
            'escala y con la IA dentro del proceso, no de adorno.',
          en:
            'Robust, observable distributed systems — platforms that ' +
            'multiply teams. I already did it with microservices and ' +
            'microfrontends in fintech; what comes next is doing it at ' +
            'larger scale with AI inside the process, not as decoration.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Nos vemos alla', en: 'See you there' }, next: null },
        ],
      },
      'ia-1': {
        text: {
          es:
            'Pase de usar la IA a construir CON ella: vibe coding a ' +
            'escala de equipo — harnesses, agentes, estandares que no se ' +
            'negocian. Este journey entero se construyo asi. El siguiente ' +
            'paso es obvio: productos de IA propios.',
          en:
            'I went from using AI to building WITH it: vibe coding at ' +
            'team scale — harnesses, agents, non-negotiable standards. ' +
            'This whole journey was built that way. The next step is ' +
            'obvious: AI products of my own.',
        },
        options: [
          {
            label: {
              es: '¿Que tipo de productos?',
              en: 'What kind of products?',
            },
            next: 'ia-2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      'ia-2': {
        text: {
          es:
            'Copilots de dominio, automatizaciones, herramientas dev. Y ' +
            'en paralelo: indie/SaaS a costo casi cero — como el backend ' +
            'serverless de este portfolio — hasta un producto para un ' +
            'problema LATAM de verdad. VE, PE, CL, MX: el recorrido ya ' +
            'me dio el mapa.',
          en:
            'Domain copilots, automations, dev tools. And in parallel: ' +
            'indie/SaaS at near-zero cost — like the serverless backend ' +
            'of this portfolio — up to a product for a real LATAM ' +
            'problem. VE, PE, CL, MX: the journey already gave me the map.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Nos vemos alla', en: 'See you there' }, next: null },
        ],
      },
      'mas-1': {
        text: {
          es:
            'Multiplicar. Mentoria y liderazgo tecnico dentro del ' +
            'equipo; open source, charlas y contenido tecnico publico ' +
            'hacia afuera. Lo aprendido no vale nada guardado en un ' +
            'cajon.',
          en:
            'Multiply. Mentorship and technical leadership inside the ' +
            'team; open source, talks and public technical content ' +
            'outward. What I learned is worthless locked in a drawer.',
        },
        options: [
          {
            label: {
              es: '¿Y que sigue despues?',
              en: 'And what comes after?',
            },
            next: 'mas-2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      'mas-2': {
        text: {
          es:
            'Seguir siendo estudiante: datos, seguridad, cloud avanzado. ' +
            'Y abrir rubros nuevos — energia, salud, farma, comida, ' +
            'fintech ya tienen su sala... ¿edtech? ¿logistica? ¿agro? El ' +
            'proximo reto decide la proxima sala.',
          en:
            'Stay a student: data, security, advanced cloud. And open ' +
            'new sectors — energy, health, pharma, food, fintech already ' +
            'have their rooms... edtech? logistics? agro? The next ' +
            'challenge decides the next room.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Nos vemos alla', en: 'See you there' }, next: null },
        ],
      },
      'contacto-1': {
        text: {
          es:
            'Facil: el holograma del centro de la sala. Pulsa E ahi y ' +
            'tienes el correo, LinkedIn y el CV. El futuro empieza con ' +
            'un "hola".',
          en:
            'Easy: the hologram at the center of the room. Press E there ' +
            'and you get the email, LinkedIn and the CV. The future ' +
            'starts with a "hello".',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Voy a saludar', en: 'Off to say hi' }, next: null },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
