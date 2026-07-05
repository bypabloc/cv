/**
 * @module dialogs/cima-presente (engine)
 * @description Arboles de dialogo de la sala 2 presente: LA CIMA (Destacame,
 *   fintech de Chile y Mexico, 2022-hoy). War room azul donde Pablo, como
 *   lead y arquitecto fullstack, orquesta microservicios Django para dos
 *   paises, forks por entidad financiera y vibe coding con guardrails.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CIMA_PRESENTE_DIALOGS = {
  'dev-ronda': defineDialog({
    name: { es: 'Dev de ronda', en: 'Dev on a stroll' },
    chatter: [
      {
        es: 'El grafo del muro quedo bonito, ¿eh?',
        en: 'The wall graph came out nice, right?',
      },
      {
        es: 'Cafe, deploy, cafe. Rutina sagrada.',
        en: 'Coffee, deploy, coffee. Sacred routine.',
      },
      {
        es: 'Este azul de la sala me pone productiva.',
        en: 'This blue room gets me productive.',
      },
      {
        es: 'Campaña lista en 4 minutos. Ya ni sorprende.',
        en: 'Campaign out in 4 minutes. Old news here.',
      },
      {
        es: '¿Viste el panel? Todo verde. Dia normal.',
        en: 'Seen the panel? All green. A normal day.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Bienvenido al war room. Aqui orquestamos productos fintech ' +
            'para Chile y Mexico. Yo ando dando una vuelta entre deploys, ' +
            'asi que pregunta lo que quieras.',
          en:
            'Welcome to the war room. Here we orchestrate fintech ' +
            'products for Chile and Mexico. I am on a stroll between ' +
            'deploys, so ask away.',
        },
        options: [
          {
            label: {
              es: '¿Que es ese grafo del muro?',
              en: 'What is that graph on the wall?',
            },
            next: 'micro-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: {
              es: 'Solo pasaba. Sigue tu vuelta',
              en: 'Just passing by',
            },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es: 'Claro. Esta sala da para rato. ¿Por donde seguimos?',
          en: 'Sure. This room has plenty to tell. Where to next?',
        },
        options: [
          {
            label: {
              es: 'Cuentame del admin de campañas',
              en: 'Tell me about the campaign admin',
            },
            next: 'camp-1',
          },
          {
            label: {
              es: '¿Que es el panel de vibe coding?',
              en: 'What is the vibe coding panel?',
            },
            next: 'vibe-1',
          },
          {
            label: { es: '¿Algo mas?', en: 'Anything else?' },
            next: 'hub3',
          },
        ],
      },
      hub3: {
        text: {
          es: 'Queda lo mejor: el jefe y sus forks. ¿O ya te vas?',
          en: 'The best is left: the boss and his forks. Or leaving?',
        },
        options: [
          {
            label: {
              es: '¿Como es trabajar con Pablo?',
              en: 'What is working with Pablo like?',
            },
            next: 'lid-1',
          },
          {
            label: {
              es: '¿Y esa puerta de PROXIMAMENTE?',
              en: 'And that COMING SOON door?',
            },
            next: 'prox-1',
          },
          {
            label: {
              es: 'Me voy. Gracias por el tour',
              en: 'I will go. Thanks',
            },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Vuelve cuando quieras. Y si ves el panel en verde, aplaude ' +
            'bajito: aqui eso es arte diario.',
          en:
            'Come back anytime. And if the panel is green, clap softly: ' +
            'around here that is daily art.',
        },
        options: [
          { label: { es: 'Hasta luego', en: 'See you' }, next: null },
          {
            label: { es: 'Espera, una cosa mas', en: 'Wait, one more thing' },
            next: 'hub',
          },
        ],
      },
      'micro-1': {
        text: {
          es:
            'Ese es nuestro mapa: seis microservicios Django. Gateway al ' +
            'frente, y detras scoring, pagos, campañas, usuarios y ' +
            'deudas. Cada uno con su oficio.',
          en:
            'That is our map: six Django microservices. Gateway up ' +
            'front, and behind it scoring, payments, campaigns, users ' +
            'and debts. Each with its own trade.',
        },
        options: [
          {
            label: {
              es: '¿Que hace cada pieza?',
              en: 'What does each piece do?',
            },
            next: 'micro-2',
          },
          {
            label: {
              es: '¿Por que partirlo en piezas?',
              en: 'Why split it into pieces?',
            },
            next: 'micro-5',
          },
          {
            label: { es: 'Volvamos a otros temas', en: 'Back to other topics' },
            next: 'hub',
          },
        ],
      },
      'micro-2': {
        text: {
          es:
            'El gateway es la puerta: recibe todo y enruta al servicio ' +
            'correcto. Nadie habla con los de adentro sin pasar por ahi.',
          en:
            'The gateway is the door: it takes everything in and routes ' +
            'to the right service. Nobody talks to the inner ones ' +
            'without going through it.',
        },
        options: [
          {
            label: { es: '¿Y el de scoring?', en: 'And the scoring one?' },
            next: 'micro-3',
          },
          {
            label: { es: '¿Pagos y deudas?', en: 'Payments and debts?' },
            next: 'micro-4',
          },
        ],
      },
      'micro-3': {
        text: {
          es:
            'Scoring evalua a cada persona que pide un credito. Datos ' +
            'entran, señal sale. Es el cerebro serio de la casa.',
          en:
            'Scoring evaluates each person applying for credit. Data ' +
            'goes in, a signal comes out. The serious brain of the house.',
        },
        options: [
          {
            label: {
              es: '¿Y el resto de servicios?',
              en: 'And the rest of the services?',
            },
            next: 'micro-4',
          },
          {
            label: {
              es: '¿Quien diseño todo esto?',
              en: 'Who designed all of this?',
            },
            next: 'micro-arch',
          },
        ],
      },
      'micro-4': {
        text: {
          es:
            'Pagos cobra, deudas ordena lo que se debe, usuarios sabe ' +
            'quien es quien y campañas hace que la gente se entere. ' +
            'Juntos son la orquesta.',
          en:
            'Payments collects, debts sorts what is owed, users knows ' +
            'who is who and campaigns gets the word out. Together they ' +
            'are the orchestra.',
        },
        options: [
          {
            label: {
              es: '¿Por que microservicios?',
              en: 'Why microservices?',
            },
            next: 'micro-5',
          },
          {
            label: {
              es: '¿Como hablan entre si?',
              en: 'How do they talk to each other?',
            },
            next: 'micro-6',
          },
        ],
      },
      'micro-arch': {
        text: {
          es:
            'Pablo. El armo la arquitectura y la defiende con diagramas. ' +
            'Si mueves una caja del grafo, aparece a los cinco minutos.',
          en:
            'Pablo. He built the architecture and defends it with ' +
            'diagrams. Move one box on the graph and he shows up within ' +
            'five minutes.',
        },
        options: [
          {
            label: {
              es: '¿Y por que asi, en piezas?',
              en: 'And why like this, in pieces?',
            },
            next: 'micro-5',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'micro-5': {
        text: {
          es:
            'Porque cada pieza crece y falla por separado. Si campañas ' +
            'tiene un pico, pagos ni se entera. Django en cada una y ' +
            'contratos claros entre todas.',
          en:
            'Because each piece grows and fails on its own. If ' +
            'campaigns spikes, payments does not even notice. Django in ' +
            'each one, clear contracts between all.',
        },
        options: [
          {
            label: {
              es: '¿Y lo de Chile y Mexico?',
              en: 'And the Chile-Mexico thing?',
            },
            next: 'micro-6',
          },
          {
            label: {
              es: '¿Y el frontend? ¿Tambien en piezas?',
              en: 'And the frontend? Pieces too?',
            },
            next: 'mf-1',
          },
          {
            label: {
              es: 'Suficiente arquitectura por hoy',
              en: 'Enough architecture for today',
            },
            next: 'hub',
          },
        ],
      },
      'micro-6': {
        text: {
          es:
            'La misma plataforma opera los dos paises. Pablo orquesta ' +
            'eso: mismo core, y cada pais con su configuracion y sus ' +
            'entidades.',
          en:
            'The same platform runs both countries. Pablo orchestrates ' +
            'that: same core, and each country with its own config and ' +
            'entities.',
        },
        options: [
          {
            label: {
              es: '¿Que cambia entre paises?',
              en: 'What changes between countries?',
            },
            next: 'micro-7',
          },
          {
            label: {
              es: '¿Es un deploy o dos?',
              en: 'Is it one deploy or two?',
            },
            next: 'micro-8',
          },
        ],
      },
      'micro-7': {
        text: {
          es:
            'Reglas, formatos, entidades financieras distintas. Lo que ' +
            'no cambia es el nucleo: eso se decide una vez y sirve dos ' +
            'veces.',
          en:
            'Rules, formats, different financial entities. What does ' +
            'not change is the core: decided once, useful twice.',
        },
        options: [
          {
            label: {
              es: '¿Y como se deploya eso?',
              en: 'And how is that deployed?',
            },
            next: 'micro-8',
          },
          {
            label: { es: 'Entendido. Sigamos', en: 'Got it. Moving on' },
            next: 'micro-9',
          },
        ],
      },
      'micro-8': {
        text: {
          es:
            'Un pipeline, dos destinos. El core viaja igual; la config ' +
            'decide si aterriza en Chile o en Mexico. Ver los dos ' +
            'tableros en verde no envejece.',
          en:
            'One pipeline, two destinations. The core travels the same; ' +
            'config decides if it lands in Chile or Mexico. Seeing both ' +
            'boards green never gets old.',
        },
        options: [
          {
            label: {
              es: '¿Como fue salir en Mexico?',
              en: 'How was going live in Mexico?',
            },
            next: 'micro-10',
          },
          {
            label: { es: 'Cierra la idea', en: 'Wrap up the idea' },
            next: 'micro-9',
          },
        ],
      },
      'micro-10': {
        text: {
          es:
            'Intenso. Semanas coordinando con los equipos de alla y el ' +
            'dia D todos mirando el panel. Cuando se puso verde, hasta ' +
            'el lead sonrio. Y eso es dificil.',
          en:
            'Intense. Weeks coordinating with the teams over there, and ' +
            'on D-day everyone watching the panel. When it went green, ' +
            'even the lead smiled. That is rare.',
        },
        options: [
          {
            label: { es: 'Buen final. Sigamos', en: 'Nice ending. Moving on' },
            next: 'micro-9',
          },
        ],
      },
      'micro-9': {
        text: {
          es:
            'En resumen: seis servicios, dos paises, un solo dolor de ' +
            'cabeza bien administrado. ¿Seguimos con otro tema?',
          en:
            'In short: six services, two countries, one well-managed ' +
            'headache. Shall we pick another topic?',
        },
        options: [
          {
            label: { es: 'Si, volvamos', en: 'Yes, back we go' },
            next: 'hub',
          },
          {
            label: {
              es: '¿Y el frontend como se organiza?',
              en: 'How is the frontend organized?',
            },
            next: 'mf-1',
          },
          {
            label: {
              es: 'No, gracias. Buen tour',
              en: 'No, thanks. Good tour',
            },
            next: null,
          },
        ],
      },
      'mf-1': {
        text: {
          es:
            'Y no es solo backend: Pablo tambien definio la ' +
            'arquitectura de microfrontends. Antes el frontend era un ' +
            'bloque unico y los equipos chocaban en cada merge.',
          en:
            'And it is not just backend: Pablo also defined the ' +
            'microfrontend architecture. Before, the frontend was one ' +
            'single block and teams collided on every merge.',
        },
        options: [
          {
            label: {
              es: '¿Que cambio con eso?',
              en: 'What changed with that?',
            },
            next: 'mf-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'mf-2': {
        text: {
          es:
            'Ahora cada equipo tiene su pieza y deploya sin pedir ' +
            'permiso. Varios equipos en paralelo, menos acoplamiento, ' +
            'cero fila de espera.',
          en:
            'Now each team owns its piece and deploys without asking ' +
            'permission. Several teams in parallel, less coupling, no ' +
            'waiting line.',
        },
        options: [
          {
            label: { es: '¿Tu lo viviste?', en: 'Did you live through it?' },
            next: 'mf-3',
          },
          {
            label: { es: 'Buen dato. Volvamos', en: 'Good one. Back we go' },
            next: 'hub',
          },
        ],
      },
      'mf-3': {
        text: {
          es:
            'Si. Una vez espere tres dias para mergear un boton. Con ' +
            'los microfrontends de Pablo, mi equipo saca lo suyo el ' +
            'mismo dia. Eso es producir mas sin correr mas.',
          en:
            'Yes. I once waited three days to merge a button. With ' +
            'the microfrontends Pablo set up, my team ships its part ' +
            'the same day. That is producing more without running more.',
        },
        options: [
          {
            label: { es: 'Gran mejora. Volvamos', en: 'Great gain. Back' },
            next: 'hub',
          },
          {
            label: {
              es: 'Con eso me quedo. Adios',
              en: 'I will keep that. Bye',
            },
            next: null,
          },
        ],
      },
      'camp-1': {
        text: {
          es:
            'El admin de campañas es mi historia favorita. Antes, armar ' +
            'una campaña eran horas de trabajo manual. Horas. En plural ' +
            'y con sueño.',
          en:
            'The campaign admin is my favorite story. Before, building ' +
            'a campaign took hours of manual work. Hours. Plural, and ' +
            'sleepy ones.',
        },
        options: [
          {
            label: { es: '¿Que era lo manual?', en: 'What was manual?' },
            next: 'camp-2',
          },
          {
            label: { es: '¿Y ahora como es?', en: 'And how is it now?' },
            next: 'camp-4',
          },
          {
            label: { es: 'Mejor otro tema', en: 'Another topic instead' },
            next: 'hub',
          },
        ],
      },
      'camp-2': {
        text: {
          es:
            'Copiar listas, cruzar segmentos a mano, validar campo por ' +
            'campo. Un dia entero podia irse en una sola campaña.',
          en:
            'Copying lists, crossing segments by hand, validating field ' +
            'by field. A whole day could go into a single campaign.',
        },
        options: [
          {
            label: {
              es: '¿Y nadie se equivocaba?',
              en: 'And nobody made mistakes?',
            },
            next: 'camp-2a',
          },
          {
            label: { es: '¿Que cambio?', en: 'What changed?' },
            next: 'camp-3',
          },
        ],
      },
      'camp-2a': {
        text: {
          es:
            'Claro que si. Un filtro mal puesto y el mensaje llegaba a ' +
            'quien no era. Cada error costaba horas extra de limpieza.',
          en:
            'Of course they did. One bad filter and the message reached ' +
            'the wrong people. Each mistake cost extra hours of cleanup.',
        },
        options: [
          {
            label: { es: '¿Que cambio entonces?', en: 'So what changed?' },
            next: 'camp-3',
          },
        ],
      },
      'camp-3': {
        text: {
          es:
            'Pablo rediseño el flujo completo del admin: automatizo lo ' +
            'repetible y dejo a las personas solo las decisiones.',
          en:
            'Pablo redesigned the whole admin flow: automated the ' +
            'repeatable parts and left people only the decisions.',
        },
        options: [
          {
            label: {
              es: '¿Hubo resistencia al cambio?',
              en: 'Was there resistance?',
            },
            next: 'camp-3a',
          },
          {
            label: {
              es: '¿Trabajaste con el en eso?',
              en: 'Did you work with him on it?',
            },
            next: 'camp-3b',
          },
          {
            label: { es: '¿Y el resultado?', en: 'And the result?' },
            next: 'camp-4',
          },
        ],
      },
      'camp-3a': {
        text: {
          es:
            'Al principio dudas, como siempre. A la segunda campaña sin ' +
            'trasnochar, nadie quiso volver al metodo viejo.',
          en:
            'Doubts at first, as always. By the second campaign without ' +
            'an all-nighter, nobody wanted the old method back.',
        },
        options: [
          {
            label: { es: '¿Y el resultado final?', en: 'And the end result?' },
            next: 'camp-4',
          },
        ],
      },
      'camp-3b': {
        text: {
          es:
            'Yo estuve en ese proyecto con el. Pablo revisaba mis PRs ' +
            'explicando cada porque y me dejo piezas clave del flujo. ' +
            'Aprendi mas ahi que en dos años de tutoriales.',
          en:
            'I was on that project with him. Pablo reviewed my PRs ' +
            'explaining every why and trusted me with key parts of ' +
            'the flow. I learned more there than in two years of ' +
            'tutorials.',
        },
        options: [
          {
            label: { es: '¿Y el resultado?', en: 'And the result?' },
            next: 'camp-4',
          },
        ],
      },
      'camp-4': {
        text: {
          es:
            'Mira el panel: campañas en 4 minutos. De horas a minutos, ' +
            'literal. Ese numero es la mejor placa de la sala.',
          en:
            'Look at the panel: campaigns in 4 minutes. From hours to ' +
            'minutes, literally. That number is the best plaque in here.',
        },
        options: [
          {
            label: {
              es: '¿Que se automatizo exactamente?',
              en: 'What got automated exactly?',
            },
            next: 'camp-5',
          },
          {
            label: {
              es: '¿Que gano el equipo?',
              en: 'What did the team gain?',
            },
            next: 'camp-6',
          },
        ],
      },
      'camp-5': {
        text: {
          es:
            'Validaciones, armado de segmentos, programacion del envio. ' +
            'Lo que era copiar y pegar ahora es apretar un boton bien ' +
            'diseñado.',
          en:
            'Validations, segment building, send scheduling. What used ' +
            'to be copy-paste is now pressing one well-designed button.',
        },
        options: [
          {
            label: {
              es: '¿Y que gano el equipo?',
              en: 'And what did the team gain?',
            },
            next: 'camp-6',
          },
        ],
      },
      'camp-6': {
        text: {
          es:
            'Tiempo para pensar. Ahora se lanzan mas campañas y ' +
            'mejores, porque la energia va a la estrategia y no al ' +
            'copipegue.',
          en:
            'Time to think. Now more and better campaigns ship, because ' +
            'the energy goes into strategy, not copy-paste.',
        },
        options: [
          {
            label: { es: 'Gran historia. Sigamos', en: 'Great story. Go on' },
            next: 'camp-7',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'camp-7': {
        text: {
          es:
            'Si algun dia ves a alguien sonreirle a un formulario de ' +
            'admin, es de los nuestros. Trauma superado.',
          en:
            'If you ever see someone smiling at an admin form, they are ' +
            'one of us. Trauma overcome.',
        },
        options: [
          {
            label: { es: 'Ja. Volvamos', en: 'Ha. Back we go' },
            next: 'hub',
          },
          {
            label: {
              es: 'Con eso me quedo. Adios',
              en: 'I will keep that. Bye',
            },
            next: null,
          },
        ],
      },
      'vibe-1': {
        text: {
          es:
            'Ese panel muestra nuestro desarrollo asistido por IA. Aqui ' +
            'se le dice vibe coding, pero con casco y cinturon.',
          en:
            'That panel shows our AI-assisted development. Around here ' +
            'we call it vibe coding, but with helmet and seatbelt.',
        },
        options: [
          {
            label: {
              es: '¿Como funciona en el dia a dia?',
              en: 'How does it work day to day?',
            },
            next: 'vibe-2',
          },
          {
            label: { es: '¿No es riesgoso?', en: 'Is it not risky?' },
            next: 'vibe-4',
          },
          {
            label: { es: 'Prefiero otro tema', en: 'Another topic, please' },
            next: 'hub',
          },
        ],
      },
      'vibe-2': {
        text: {
          es:
            'La IA escribe borradores, propone refactors, arma tests. ' +
            'Nosotros dirigimos, revisamos y decidimos que entra.',
          en:
            'The AI writes drafts, proposes refactors, builds tests. We ' +
            'steer, review and decide what gets in.',
        },
        options: [
          {
            label: {
              es: '¿Cual es la regla de oro?',
              en: 'What is the golden rule?',
            },
            next: 'vibe-3',
          },
        ],
      },
      'vibe-3': {
        text: {
          es:
            'La IA propone, el equipo dispone. Lo dice Pablo tanto que ' +
            'deberia estar bordado en un cojin de la sala.',
          en:
            'The AI proposes, the team disposes. Pablo says it so often ' +
            'it should be embroidered on a cushion in this room.',
        },
        options: [
          {
            label: { es: '¿Y los guardrails?', en: 'And the guardrails?' },
            next: 'vibe-4',
          },
          {
            label: { es: '¿Como lo adoptaron?', en: 'How did you adopt it?' },
            next: 'vibe-5',
          },
        ],
      },
      'vibe-4': {
        text: {
          es:
            'Nada llega a produccion sin review humano y sin tests. La ' +
            'IA acelera el borrador; la calidad la firma una persona.',
          en:
            'Nothing reaches production without human review and tests. ' +
            'The AI speeds up the draft; a person signs off on quality.',
        },
        options: [
          {
            label: {
              es: '¿Como se incorporo al equipo?',
              en: 'How was it brought to the team?',
            },
            next: 'vibe-5',
          },
          {
            label: {
              es: '¿Y funciona de verdad?',
              en: 'And does it really work?',
            },
            next: 'vibe-6',
          },
        ],
      },
      'vibe-5': {
        text: {
          es:
            'Pablo lo metio de a poco: reglas claras, casos acotados y ' +
            'midiendo. Primero tareas chicas, despues todo el flujo.',
          en:
            'Pablo brought it in gradually: clear rules, bounded cases, ' +
            'always measuring. Small tasks first, then the whole flow.',
        },
        options: [
          {
            label: {
              es: '¿Y los escepticos del equipo?',
              en: 'And the team skeptics?',
            },
            next: 'vibe-7',
          },
          {
            label: { es: '¿El resultado?', en: 'The result?' },
            next: 'vibe-6',
          },
        ],
      },
      'vibe-7': {
        text: {
          es:
            'Habia, claro. Los convencio el diff: cuando ves un buen ' +
            'refactor propuesto en minutos, la discusion cambia sola.',
          en:
            'There were, of course. The diff convinced them: when you ' +
            'see a good refactor proposed in minutes, the debate shifts ' +
            'on its own.',
        },
        options: [
          {
            label: {
              es: '¿Y el resultado global?',
              en: 'And the overall result?',
            },
            next: 'vibe-6',
          },
        ],
      },
      'vibe-6': {
        text: {
          es:
            'Mas velocidad sin soltar el volante. Productivo y seguro, ' +
            'que era el punto. El panel de la esquina lleva la cuenta.',
          en:
            'More speed without letting go of the wheel. Productive and ' +
            'safe, which was the point. The corner panel keeps score.',
        },
        options: [
          {
            label: { es: 'Me convence. Sigamos', en: 'Convinced. Moving on' },
            next: 'vibe-8',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'vibe-8': {
        text: {
          es:
            'Si te queda la duda, mira los commits: todos con review, ' +
            'todos con tests. La vibra es libre; el merge, no.',
          en:
            'If you still doubt it, check the commits: all reviewed, ' +
            'all tested. The vibe is free; the merge is not.',
        },
        options: [
          {
            label: { es: 'Buena frase. Volvamos', en: 'Good line. Back we go' },
            next: 'hub',
          },
          {
            label: {
              es: 'Con eso cierro. Gracias',
              en: 'That closes it. Thanks',
            },
            next: null,
          },
        ],
      },
      'lid-1': {
        text: {
          es:
            'Pablo lidera el equipo: somos entre 4 y 6 segun la epoca. ' +
            'Es lead y arquitecto, pero sigue metido en el codigo.',
          en:
            'Pablo leads the team: we are 4 to 6 depending on the ' +
            'season. He is lead and architect, but still deep in the ' +
            'code.',
        },
        options: [
          {
            label: { es: '¿Como es su estilo?', en: 'What is his style?' },
            next: 'lid-2',
          },
          {
            label: {
              es: '¿Y las reorganizaciones?',
              en: 'And the reorganizations?',
            },
            next: 'lid-3',
          },
          {
            label: { es: 'Mejor otro tema', en: 'Another topic instead' },
            next: 'hub',
          },
        ],
      },
      'lid-2': {
        text: {
          es:
            'Da contexto y confia. Explica el porque, marca el rumbo y ' +
            'te deja ejecutar. Y cuando algo se traba, se sienta contigo.',
          en:
            'He gives context and trusts. Explains the why, sets the ' +
            'course and lets you execute. And when something jams, he ' +
            'sits down with you.',
        },
        options: [
          {
            label: {
              es: '¿Sobrevivieron reorganizaciones?',
              en: 'Did you survive reorgs?',
            },
            next: 'lid-3',
          },
          {
            label: {
              es: '¿Y lo de las entidades?',
              en: 'And the entities thing?',
            },
            next: 'ent-1',
          },
        ],
      },
      'lid-3': {
        text: {
          es:
            'Varias. El equipo cambio de forma mas de una vez y Pablo ' +
            'mantuvo el rumbo: prioridades claras y cero drama.',
          en:
            'Several. The team changed shape more than once and Pablo ' +
            'kept the course: clear priorities and zero drama.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de las entidades',
              en: 'Tell me about the entities',
            },
            next: 'ent-1',
          },
          {
            label: { es: 'Cierra el tema', en: 'Wrap up the topic' },
            next: 'lid-4',
          },
        ],
      },
      'ent-1': {
        text: {
          es:
            'Hacemos implementaciones completas con entidades ' +
            'financieras. No es tirar una API por la ventana: es ' +
            'acompañar de punta a punta.',
          en:
            'We do full implementations with financial entities. It is ' +
            'not throwing an API over the wall: it is walking it end to ' +
            'end.',
        },
        options: [
          {
            label: { es: '¿Con cuales entidades?', en: 'With which entities?' },
            next: 'ent-2',
          },
          {
            label: {
              es: '¿Y los forks del escritorio?',
              en: 'And the desk forks?',
            },
            next: 'fork-1',
          },
        ],
      },
      'ent-2': {
        text: {
          es:
            'Santander, Scotiabank, Lider. Pablo trabaja directo con ' +
            'los equipos tech de cada una, sin intermediarios.',
          en:
            'Santander, Scotiabank, Lider. Pablo works directly with ' +
            'the tech teams of each one, no middlemen.',
        },
        options: [
          {
            label: {
              es: '¿Como es ese trabajo directo?',
              en: 'How is that direct work?',
            },
            next: 'ent-3',
          },
          {
            label: { es: 'Hablemos de los forks', en: 'Let us talk forks' },
            next: 'fork-1',
          },
        ],
      },
      'ent-3': {
        text: {
          es:
            'Cada entidad tiene sus procesos y sus tiempos. Pablo se ' +
            'sienta con sus devs, ajusta la integracion y la deja ' +
            'andando.',
          en:
            'Each entity has its processes and its pace. Pablo sits ' +
            'with their devs, tunes the integration and gets it running.',
        },
        options: [
          {
            label: {
              es: '¿Y como escala eso? ¿Forks?',
              en: 'How does that scale? Forks?',
            },
            next: 'fork-1',
          },
        ],
      },
      'fork-1': {
        text: {
          es:
            'Mira el ultrawide: santander/, scotiabank/, lider/. El ' +
            'code-base central se forkea por entidad financiera.',
          en:
            'Look at the ultrawide: santander/, scotiabank/, lider/. ' +
            'The central code-base is forked per financial entity.',
        },
        options: [
          {
            label: {
              es: '¿Como funciona el fork?',
              en: 'How does a fork work?',
            },
            next: 'fork-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'fork-2': {
        text: {
          es:
            'Hay un core comun con el design system, y cada entidad ' +
            'recibe su fork con su marca y sus particularidades.',
          en:
            'There is a common core with the design system, and each ' +
            'entity gets its fork with its brand and its quirks.',
        },
        options: [
          {
            label: {
              es: '¿Cuanto tarda un fork nuevo?',
              en: 'How long does a new fork take?',
            },
            next: 'fork-2a',
          },
          {
            label: {
              es: '¿Y no se desalinean?',
              en: 'Do they not drift apart?',
            },
            next: 'fork-3',
          },
        ],
      },
      'fork-2a': {
        text: {
          es:
            'Dias. Cuando entra una entidad nueva, Pablo levanta el ' +
            'fork con su marca y queda andando en dias, no en meses. ' +
            'La primera vez nadie lo creia.',
          en:
            'Days. When a new entity signs, Pablo spins up the fork ' +
            'with their brand and it is running in days, not months. ' +
            'The first time nobody believed it.',
        },
        options: [
          {
            label: {
              es: '¿Y no se desalinean?',
              en: 'Do they not drift apart?',
            },
            next: 'fork-3',
          },
        ],
      },
      'fork-3': {
        text: {
          es:
            'Esa es la gracia: el design system compartido mantiene la ' +
            'consistencia. Cambias el core y todos los forks heredan.',
          en:
            'That is the trick: the shared design system keeps the ' +
            'consistency. Change the core and every fork inherits it.',
        },
        options: [
          {
            label: { es: '¿Nunca diverge nada?', en: 'Nothing ever diverges?' },
            next: 'fork-4',
          },
          {
            label: { es: 'Cierra el tema', en: 'Wrap up the topic' },
            next: 'lid-4',
          },
        ],
      },
      'fork-4': {
        text: {
          es:
            'Se vigila. Lo especifico vive en el fork; lo comun vuelve ' +
            'al core. Si algo se repite dos veces, Pablo lo sube al ' +
            'centro.',
          en:
            'It is watched. Entity-specific code lives in the fork; ' +
            'common code goes back to the core. If something repeats ' +
            'twice, Pablo moves it to the center.',
        },
        options: [
          {
            label: { es: 'Buen sistema. Cierra', en: 'Good system. Wrap up' },
            next: 'lid-4',
          },
        ],
      },
      'lid-4': {
        text: {
          es:
            'En resumen: un lead que arma la arquitectura, cuida al ' +
            'equipo y le habla de tu a tu al banco. Combo raro y util.',
          en:
            'In short: a lead who builds the architecture, looks after ' +
            'the team and talks eye to eye with the bank. Rare, useful ' +
            'combo.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: {
              es: 'Con esto me sobra. Gracias',
              en: 'That is plenty. Thanks',
            },
            next: null,
          },
        ],
      },
      'prox-1': {
        text: {
          es:
            'Esa puerta dice PROXIMAMENTE y hasta ahi te puedo contar, ' +
            'porque ni yo se que va ahi. Aqui siempre se esta ' +
            'construyendo algo.',
          en:
            'That door says COMING SOON and that is all I can tell you, ' +
            'because not even I know what goes there. Something is ' +
            'always being built here.',
        },
        options: [
          {
            label: {
              es: '¿Y ese holograma de alla?',
              en: 'And that hologram over there?',
            },
            next: 'prox-2',
          },
          {
            label: {
              es: 'Misterio aceptado. Volvamos',
              en: 'Mystery accepted. Back',
            },
            next: 'hub',
          },
        ],
      },
      'prox-2': {
        text: {
          es:
            'Es el canal de contacto directo con Pablo. Si despues de ' +
            'todo esto quieres hablarle, ahi lo tienes brillando.',
          en:
            'It is the direct contact channel with Pablo. If after all ' +
            'this you want to talk to him, there it is, glowing.',
        },
        options: [
          {
            label: { es: 'Bueno saberlo. Volvamos', en: 'Good to know. Back' },
            next: 'hub',
          },
          {
            label: {
              es: 'Ire a verlo. Gracias',
              en: 'I will check it. Thanks',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'lead-reunion': defineDialog({
    name: { es: 'Lead en reunion', en: 'Lead in a meeting' },
    chatter: [
      {
        es: 'Cinco minutos y cierro esta reunion.',
        en: 'Five minutes and I close this meeting.',
      },
      {
        es: 'Accion sin dueño no es accion.',
        en: 'An action with no owner is not an action.',
      },
      {
        es: 'Chile ya almorzo, Mexico recien va.',
        en: 'Chile had lunch, Mexico is on its way.',
      },
      {
        es: 'La agenda es corta. Como debe ser.',
        en: 'Short agenda. As it should be.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Disculpa la corbata, vengo de coordinar con Mexico. Soy ' +
            'lead aqui y me sobran cinco minutos, asi que aprovecha.',
          en:
            'Excuse the tie, I just finished coordinating with Mexico. ' +
            'I am a lead here and I have five spare minutes, so make ' +
            'them count.',
        },
        options: [
          {
            label: {
              es: '¿Como coordinan Chile y Mexico?',
              en: 'How do Chile and Mexico sync?',
            },
            next: 'co-1',
          },
          {
            label: { es: 'Hay mas temas, imagino', en: 'More topics, I guess' },
            next: 'hub2',
          },
          {
            label: { es: 'Te dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es: 'Claro que hay. Poco tiempo, buenos temas. ¿Cual va?',
          en: 'Of course there are. Little time, good topics. Which one?',
        },
        options: [
          {
            label: {
              es: '¿Que tal las reorganizaciones?',
              en: 'How about the reorgs?',
            },
            next: 're-1',
          },
          {
            label: {
              es: 'Dicen que sus reuniones rinden',
              en: 'I hear your meetings deliver',
            },
            next: 'ac-1',
          },
          {
            label: {
              es: '¿Que cambio Pablo en la produccion?',
              en: 'What did Pablo change in output?',
            },
            next: 'pr-1',
          },
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
        ],
      },
      'co-1': {
        text: {
          es:
            'Una operacion, dos paises. Pablo orquesta los productos ' +
            'para ambos y esta mesa es donde se sincroniza todo.',
          en:
            'One operation, two countries. Pablo orchestrates the ' +
            'products for both, and this table is where it all syncs.',
        },
        options: [
          {
            label: { es: '¿Y los husos horarios?', en: 'And the time zones?' },
            next: 'co-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'co-2': {
        text: {
          es:
            'Ese reloj doble no es decoracion. Buscamos las horas que ' +
            'sirven a ambos lados y las cuidamos como oro.',
          en:
            'That double clock is not decoration. We find the hours ' +
            'that work on both sides and guard them like gold.',
        },
        options: [
          {
            label: {
              es: '¿Algun choque de calendario?',
              en: 'Any calendar clashes?',
            },
            next: 'co-2a',
          },
          {
            label: {
              es: '¿Como se mantiene el orden?',
              en: 'How do you keep order?',
            },
            next: 'co-3',
          },
        ],
      },
      'co-2a': {
        text: {
          es:
            'Feriados. Un pais celebra, el otro deploya. Aprendimos a ' +
            'mirar dos calendarios antes de prometer fechas.',
          en:
            'Holidays. One country celebrates, the other deploys. We ' +
            'learned to check two calendars before promising dates.',
        },
        options: [
          {
            label: {
              es: '¿Y como se ordena todo eso?',
              en: 'And how is all that sorted?',
            },
            next: 'co-3',
          },
        ],
      },
      'co-3': {
        text: {
          es:
            'Agenda comun, prioridades unicas. Pablo mantiene una sola ' +
            'lista para los dos paises: si todo es urgente, nada lo es.',
          en:
            'Shared agenda, single priorities. Pablo keeps one list for ' +
            'both countries: if everything is urgent, nothing is.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: {
              es: 'Claro y conciso. Gracias',
              en: 'Clear and short. Thanks',
            },
            next: 'bye',
          },
        ],
      },
      're-1': {
        text: {
          es:
            'Reorganizaciones hubo varias. Equipos que cambian de ' +
            'nombre, de foco, de tamaño. Lo normal en una empresa viva.',
          en:
            'There were several reorgs. Teams changing name, focus, ' +
            'size. The usual in a living company.',
        },
        options: [
          {
            label: {
              es: '¿Y como las pasaron?',
              en: 'How did you get through?',
            },
            next: 're-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      're-2': {
        text: {
          es:
            'Con Pablo llevando equipos de 4 a 6 personas a traves de ' +
            'cada cambio. La estructura se movia; el trabajo, no.',
          en:
            'With Pablo carrying teams of 4 to 6 people through each ' +
            'change. The structure moved; the work did not.',
        },
        options: [
          {
            label: {
              es: '¿Como se comunica un cambio asi?',
              en: 'How do you announce a change?',
            },
            next: 're-2a',
          },
          {
            label: { es: '¿Tu como lo viviste?', en: 'How was it for you?' },
            next: 're-2b',
          },
          {
            label: { es: '¿Que aprendieron?', en: 'What did you learn?' },
            next: 're-3',
          },
        ],
      },
      're-2a': {
        text: {
          es:
            'De frente y temprano. Primero el porque, despues el como, ' +
            'y al final los nombres. En ese orden duele menos.',
          en:
            'Straight and early. First the why, then the how, and the ' +
            'names last. In that order it hurts less.',
        },
        options: [
          {
            label: { es: '¿Y que aprendieron?', en: 'And what did you learn?' },
            next: 're-3',
          },
        ],
      },
      're-2b': {
        text: {
          es:
            'En una reorganizacion herede la mitad del equipo de ' +
            'Pablo. Su traspaso fue tan ordenado que en una semana ' +
            'entregabamos igual que antes. Eso no se improvisa.',
          en:
            "In one reorg I inherited half of Pablo's team. His " +
            'handover was so tidy that within a week we were ' +
            'delivering as before. You do not improvise that.',
        },
        options: [
          {
            label: { es: '¿Y que aprendieron?', en: 'And what did you learn?' },
            next: 're-3',
          },
        ],
      },
      're-3': {
        text: {
          es:
            'Que la gente aguanta cambios si el rumbo es claro. Los ' +
            'titulos cambian; el respeto y el codigo quedan.',
          en:
            'That people endure change if the course is clear. Titles ' +
            'change; respect and code remain.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: { es: 'Buena leccion. Gracias', en: 'Good lesson. Thanks' },
            next: 'bye',
          },
        ],
      },
      'ac-1': {
        text: {
          es:
            'Regla de esta mesa: toda reunion termina con acciones. Si ' +
            'no salio una accion, era un correo largo.',
          en:
            'Rule of this table: every meeting ends with actions. If no ' +
            'action came out, it was a long email.',
        },
        options: [
          {
            label: {
              es: '¿Como es una accion bien hecha?',
              en: 'What makes a proper action?',
            },
            next: 'ac-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'ac-2': {
        text: {
          es:
            'Dueño, fecha y resultado esperado. Las tres cosas o no ' +
            'cuenta. Lo anotamos antes de levantarnos de la silla.',
          en:
            'Owner, date and expected outcome. All three or it does not ' +
            'count. We write it down before leaving the chair.',
        },
        options: [
          {
            label: {
              es: '¿Quien vigila que se cumpla?',
              en: 'Who checks it gets done?',
            },
            next: 'ac-2a',
          },
          {
            label: {
              es: '¿Quien corta la reunion?',
              en: 'Who cuts the meeting off?',
            },
            next: 'ac-3',
          },
        ],
      },
      'ac-2a': {
        text: {
          es:
            'La proxima reunion abre revisando las acciones de la ' +
            'anterior. Nadie quiere ser el pendiente eterno de la lista.',
          en:
            'The next meeting opens by reviewing the previous actions. ' +
            'Nobody wants to be the eternal pending item on the list.',
        },
        options: [
          {
            label: {
              es: '¿Y quien corta la reunion?',
              en: 'And who cuts the meeting?',
            },
            next: 'ac-3',
          },
        ],
      },
      'ac-3': {
        text: {
          es:
            'Pablo, sin culpa. Cuando ya hay decision, se acabo la ' +
            'reunion. Los mejores debates son los que terminan.',
          en:
            'Pablo, guilt-free. Once there is a decision, the meeting ' +
            'is over. The best debates are the ones that end.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: { es: 'Aprendido. Te dejo seguir', en: 'Noted. Carry on' },
            next: 'bye',
          },
        ],
      },
      'pr-1': {
        text: {
          es:
            'Te doy numeros, que es lo mio. Campañas que costaban ' +
            'horas de una persona hoy salen en 4 minutos con el admin ' +
            'que construyo Pablo. Esa capacidad vuelve al equipo.',
          en:
            'I will give you numbers, that is my thing. Campaigns ' +
            'that cost hours of one person now ship in 4 minutes with ' +
            'the admin Pablo built. That capacity goes back to the ' +
            'team.',
        },
        options: [
          {
            label: { es: '¿Y en el frontend?', en: 'And on the frontend?' },
            next: 'pr-2',
          },
          {
            label: { es: '¿Algun otro numero?', en: 'Any other number?' },
            next: 'pr-3',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'pr-2': {
        text: {
          es:
            'Con los microfrontends que definio Pablo, varios equipos ' +
            'avanzan en paralelo sin pisarse. Antes coordinar un ' +
            'release era mi peor semana; ahora casi ni me entero.',
          en:
            'With the microfrontends Pablo defined, several teams ' +
            'move in parallel without stepping on each other. ' +
            'Coordinating a release used to be my worst week; now I ' +
            'barely notice.',
        },
        options: [
          {
            label: { es: '¿Algun otro numero?', en: 'Any other number?' },
            next: 'pr-3',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'pr-3': {
        text: {
          es:
            'Entidades nuevas. Antes prometia meses para levantar una ' +
            'plataforma; ahora Pablo forkea el core y en dias esta ' +
            'andando con la marca del banco. Prometo dias y cumplo.',
          en:
            'New entities. I used to promise months to stand up a ' +
            'platform; now Pablo forks the core and in days it runs ' +
            "with the bank's brand. I promise days and deliver.",
        },
        options: [
          {
            label: {
              es: '¿Como se siente vender eso?',
              en: 'How does selling that feel?',
            },
            next: 'pr-4',
          },
          {
            label: { es: 'Impresionante. Volvamos', en: 'Impressive. Back' },
            next: 'hub',
          },
        ],
      },
      'pr-4': {
        text: {
          es:
            'Comodo. Santander, Scotiabank, Lider: mismo design ' +
            'system, cada uno con su marca. Yo firmo fechas tranquilo ' +
            'porque Pablo las hace verdad.',
          en:
            'Comfortable. Santander, Scotiabank, Lider: same design ' +
            'system, each with its own brand. I sign dates calmly ' +
            'because Pablo makes them come true.',
        },
        options: [
          {
            label: { es: 'Buen duo. Volvamos', en: 'Good duo. Back we go' },
            next: 'hub',
          },
          {
            label: {
              es: 'Con eso me sobra. Gracias',
              en: 'That is plenty. Thanks',
            },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Gracias por la visita. Yo vuelvo a lo mio: quedan tres ' +
            'acciones sin dueño y eso no puede amanecer asi.',
          en:
            'Thanks for the visit. Back to my thing: three actions ' +
            'still have no owner and that cannot see the sunrise.',
        },
        options: [
          {
            label: { es: 'Suerte con eso', en: 'Good luck with that' },
            next: null,
          },
        ],
      },
    },
  }),
  'dev-observabilidad': defineDialog({
    name: { es: 'Dev de observabilidad', en: 'Observability dev' },
    chatter: [
      {
        es: 'p95 en 95. Antes era 180. Respira.',
        en: 'p95 at 95. Used to be 180. Breathe.',
      },
      {
        es: 'Verde. Verde. Verde. Me encanta.',
        en: 'Green. Green. Green. Love it.',
      },
      {
        es: 'Un grafico bonito vale mil logs.',
        en: 'A pretty chart beats a thousand logs.',
      },
      {
        es: 'Si algo parpadea, yo lo veo primero.',
        en: 'If something blinks, I see it first.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Mira ese panel: p95 de 95 milisegundos, antes 180. Y ' +
            'uptime de 99.99, antes 99.97. Yo lo cuido como a una ' +
            'mascota. ¿Que quieres saber?',
          en:
            'Look at that panel: p95 of 95 milliseconds, down from ' +
            '180. And 99.99 uptime, up from 99.97. I look after it ' +
            'like a pet. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que significan esos numeros?',
              en: 'What do those numbers mean?',
            },
            next: 'me-1',
          },
          {
            label: {
              es: 'Hay mas cosas aqui, ¿no?',
              en: 'There is more, right?',
            },
            next: 'hub2',
          },
          {
            label: {
              es: 'Solo miraba. Sigue tu',
              en: 'Just looking. Carry on',
            },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es: 'Hay panel para rato. ¿Que te muestro?',
          en: 'Plenty of panel to go around. What shall I show you?',
        },
        options: [
          {
            label: {
              es: '¿Como deployan a dos paises?',
              en: 'How do you deploy to two countries?',
            },
            next: 'de-1',
          },
          {
            label: {
              es: 'Explicame el grafo del muro',
              en: 'Explain the wall graph',
            },
            next: 'gr-1',
          },
          {
            label: { es: 'Volvamos al panel', en: 'Back to the panel' },
            next: 'hub',
          },
        ],
      },
      'me-1': {
        text: {
          es:
            'El p95 dice que el 95 por ciento de las requests responde ' +
            'en 95 milisegundos o menos. Hace un tiempo eran 180. ' +
            'Rapido de verdad, no rapido de folleto.',
          en:
            'The p95 says 95 percent of requests respond in 95 ' +
            'milliseconds or less. A while back it was 180. Actually ' +
            'fast, not brochure fast.',
        },
        options: [
          {
            label: {
              es: '¿Como bajaron de 180 a 95?',
              en: 'How did you go from 180 to 95?',
            },
            next: 'me-1a',
          },
          {
            label: { es: '¿Y el uptime?', en: 'And the uptime?' },
            next: 'me-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'me-1a': {
        text: {
          es:
            'Fue una cruzada de Pablo. Se sento conmigo varias ' +
            'semanas: cache donde dolia, queries afinadas, llamadas de ' +
            'mas que sobraban. De 180 a 95, medido, no contado.',
          en:
            'It was a crusade Pablo led. He sat with me for weeks: ' +
            'cache where it hurt, tuned queries, extra calls removed. ' +
            'From 180 to 95, measured, not told.',
        },
        options: [
          {
            label: {
              es: '¿Como fue trabajar asi con el?',
              en: 'How was working with him?',
            },
            next: 'me-1b',
          },
          {
            label: { es: '¿Y el uptime?', en: 'And the uptime?' },
            next: 'me-2',
          },
        ],
      },
      'me-1b': {
        text: {
          es:
            'Mi mejor pairing. Pablo no te da la respuesta: te ' +
            'pregunta hasta que la ves tu. Ahora cazo milisegundos sin ' +
            'ayuda, pero el metodo es suyo.',
          en:
            'My best pairing ever. Pablo does not hand you the ' +
            'answer: he asks until you see it yourself. Now I hunt ' +
            'milliseconds on my own, but the method is his.',
        },
        options: [
          {
            label: { es: '¿Y el uptime?', en: 'And the uptime?' },
            next: 'me-2',
          },
          {
            label: { es: 'Gran historia. Volvamos', en: 'Great story. Back' },
            next: 'hub',
          },
        ],
      },
      'me-2': {
        text: {
          es:
            '99.99 por ciento de uptime, y venimos de 99.97. En un ' +
            'año eso es apenas un ratito caido. La gente no nota ' +
            'nada, y asi debe ser.',
          en:
            '99.99 percent uptime, up from 99.97. Over a year that is ' +
            'barely a moment down. People notice nothing, and that is ' +
            'how it should be.',
        },
        options: [
          {
            label: {
              es: '¿Es de un pais o de los dos?',
              en: 'One country or both?',
            },
            next: 'me-2a',
          },
          {
            label: { es: '¿Como lo logran?', en: 'How do you pull it off?' },
            next: 'me-3',
          },
        ],
      },
      'me-2a': {
        text: {
          es:
            'De la plataforma completa. Si Mexico sufre, el numero ' +
            'sufre. Por eso los dos paises se cuidan juntos.',
          en:
            'The whole platform. If Mexico suffers, the number suffers. ' +
            'That is why both countries are looked after together.',
        },
        options: [
          {
            label: { es: '¿Y como lo logran?', en: 'And how do you do it?' },
            next: 'me-3',
          },
        ],
      },
      'me-3': {
        text: {
          es:
            'Alertas que avisan antes del incendio, deploys chicos y ' +
            'reversibles, y review de todo lo que entra. La receta la ' +
            'instalo Pablo. Aburrido a proposito.',
          en:
            'Alerts that warn before the fire, small reversible ' +
            'deploys, and review on everything that gets in. Pablo ' +
            'installed the recipe. Boring on purpose.',
        },
        options: [
          {
            label: { es: '¿Aburrido es bueno?', en: 'Boring is good?' },
            next: 'me-4',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'me-4': {
        text: {
          es:
            'En observabilidad, aburrido es el paraiso. Los graficos ' +
            'emocionantes son los que te arruinan la cena.',
          en:
            'In observability, boring is paradise. Exciting charts are ' +
            'the ones that ruin your dinner.',
        },
        options: [
          {
            label: { es: 'Ja, cierto. Volvamos', en: 'Ha, true. Back we go' },
            next: 'hub',
          },
          {
            label: {
              es: 'Me quedo con esa. Adios',
              en: 'Keeping that one. Bye',
            },
            next: null,
          },
        ],
      },
      'de-1': {
        text: {
          es:
            'Deployamos a dos paises: Chile y Mexico. Mismo core, ' +
            'configuracion por pais, y este panel vigilando ambos.',
          en:
            'We deploy to two countries: Chile and Mexico. Same core, ' +
            'per-country config, and this panel watching both.',
        },
        options: [
          {
            label: { es: '¿Como no se mezclan?', en: 'How do they not mix?' },
            next: 'de-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'de-2': {
        text: {
          es:
            'Cada pais tiene su configuracion y sus entidades, pero el ' +
            'nucleo es el mismo. Pablo lo diseño asi: una sola verdad, ' +
            'dos destinos.',
          en:
            'Each country has its config and its entities, but the ' +
            'core is the same. Pablo designed it that way: one truth, ' +
            'two destinations.',
        },
        options: [
          {
            label: {
              es: '¿Y cuando corre la orquestacion?',
              en: 'And when orchestration runs?',
            },
            next: 'de-3',
          },
          {
            label: {
              es: '¿La primera vez fue tan suave?',
              en: 'Was the first time that smooth?',
            },
            next: 'de-2a',
          },
        ],
      },
      'de-2a': {
        text: {
          es:
            'La primera vez nadie respiraba. Cuando ambos tableros ' +
            'quedaron verdes a la vez, alguien aplaudio. No dire quien. ' +
            'Fui yo.',
          en:
            'The first time nobody breathed. When both boards went ' +
            'green at once, someone clapped. I will not say who. It was ' +
            'me.',
        },
        options: [{ label: { es: '¿Y ahora?', en: 'And now?' }, next: 'de-3' }],
      },
      'de-3': {
        text: {
          es:
            'Ahora es rutina: corre la orquestacion y el panel se pone ' +
            'verde. Ese verde es mi color favorito y no acepto debate.',
          en:
            'Now it is routine: orchestration runs and the panel goes ' +
            'green. That green is my favorite color, no debate accepted.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: {
              es: 'Larga vida al verde. Adios',
              en: 'Long live green. Bye',
            },
            next: null,
          },
        ],
      },
      'gr-1': {
        text: {
          es:
            'El grafo del muro es la ciudad: seis microservicios ' +
            'Django conectados. Lo uso para saber donde mirar cuando ' +
            'algo parpadea.',
          en:
            'The wall graph is the city: six connected Django ' +
            'microservices. I use it to know where to look when ' +
            'something blinks.',
        },
        options: [
          {
            label: { es: '¿Quien esta al frente?', en: 'Who sits up front?' },
            next: 'gr-2',
          },
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
        ],
      },
      'gr-2': {
        text: {
          es:
            'El gateway recibe todo. Detras: scoring, pagos, campañas, ' +
            'usuarios y deudas. Cada linea del grafo es una ' +
            'conversacion entre ellos.',
          en:
            'The gateway takes everything in. Behind it: scoring, ' +
            'payments, campaigns, users and debts. Each line on the ' +
            'graph is a conversation between them.',
        },
        options: [
          {
            label: { es: '¿Cual parpadea mas?', en: 'Which one blinks most?' },
            next: 'gr-2a',
          },
          {
            label: {
              es: '¿Quien diseño esta ciudad?',
              en: 'Who designed this city?',
            },
            next: 'gr-3',
          },
        ],
      },
      'gr-2a': {
        text: {
          es:
            'Campañas, cuando hay lanzamiento. Pero desde que el ' +
            'admin de Pablo arma todo en 4 minutos, hasta ese pico ' +
            'llega ordenado.',
          en:
            'Campaigns, on launch days. But since the admin Pablo ' +
            'built sets everything up in 4 minutes, even that spike ' +
            'arrives tidy.',
        },
        options: [
          {
            label: {
              es: '¿Y quien diseño la ciudad?',
              en: 'And who designed the city?',
            },
            next: 'gr-3',
          },
        ],
      },
      'gr-3': {
        text: {
          es:
            'Pablo. Arquitectura suya, y se nota: cuando algo falla, el ' +
            'grafo te dice donde buscar. Un mapa que ahorra madrugadas.',
          en:
            'Pablo. His architecture, and it shows: when something ' +
            'fails, the graph tells you where to look. A map that saves ' +
            'you late nights.',
        },
        options: [
          {
            label: { es: 'Volvamos a los temas', en: 'Back to the topics' },
            next: 'hub',
          },
          {
            label: { es: 'Gran mapa. Hasta luego', en: 'Great map. See you' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
