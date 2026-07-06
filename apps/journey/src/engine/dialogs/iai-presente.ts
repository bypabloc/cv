/**
 * @module dialogs/iai-presente (engine)
 * @description Arboles de dialogo de la sala 3 presente: IAI (Instituto
 *   Autonomo de Infraestructura del Estado Yaracuy, 2015), donde Pablo
 *   lidero su proyecto de grado: el sistema de gestion de obras,
 *   presupuestos (partidas COVENIN + APU) y valuaciones — app de
 *   escritorio Java con una PC como servidor central en red local. 5 NPCs
 *   con los 2 enfoques del canon (informe 16): Keiber Mendoza y Marielys
 *   Ochoa (tesistas/dev del equipo), Ing. Gregorio Salcedo (inspector de
 *   obra) y Belkis Camacaro (analista de presupuestos) como personal del
 *   sitio, y la Ing. Maritza Oropeza (presidenta del instituto). Todos
 *   anclados a la data real: primer liderazgo de Pablo (~3 personas),
 *   red cliente-servidor que elimino copias desincronizadas, consolidado
 *   de jornadas manuales a reportes del sistema, documentacion completa.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const IAI_PRESENTE_DIALOGS = {
  keiber: defineDialog({
    name: { es: 'Keiber Mendoza', en: 'Keiber Mendoza' },
    chatter: [
      {
        es: 'Pablo reparte, uno entrega. Asi funcionaba el equipo.',
        en: 'Pablo assigns, you deliver. That is how the team worked.',
      },
      {
        es: 'Documentamos hasta el porque de cada tabla.',
        en: 'We documented even the why of every table.',
      },
      {
        es: 'La defensa fue un paseo. En serio.',
        en: 'The defense was a walk in the park. Seriously.',
      },
      {
        es: 'Java en serio: Swing, DAOs y paciencia.',
        en: 'Real Java: Swing, DAOs and patience.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Epa. Soy Keiber, tesista del equipo de Pablo — el que armo ' +
            'los modulos de presupuesto. Este sistema fue nuestro proyecto ' +
            'de grado, pero funciono como un desarrollo de verdad. ¿Que ' +
            'quieres saber?',
          en:
            'Hey. I am Keiber, one of the thesis teammates on Pablo’s crew ' +
            '— I built the budget modules. This system was our degree ' +
            'project, but it ran like a real development. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Como lideraba Pablo?',
              en: 'How did Pablo lead?',
            },
            next: 'lider-1',
          },
          {
            label: {
              es: '¿Que construyeron?',
              en: 'What did you build?',
            },
            next: 'sistema-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, sigue en lo tuyo', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Claro: la red local del servidor, o mi resumen de todo el ' +
            'año. ¿Que prefieres?',
          en:
            'Sure: the server’s local network, or my summary of the whole ' +
            'year. Which one?',
        },
        options: [
          {
            label: { es: '¿La red local?', en: 'The local network?' },
            next: 'red-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'lider-1': {
        text: {
          es:
            'Pablo repartia las tareas y seguia el avance de cada quien ' +
            'sin perseguir a nadie. Hitos claros, riesgos anotados, y si ' +
            'algo se trancaba, se sentaba contigo hasta destrancarlo. ' +
            'Primer lider que tuve — y eso que eramos tres estudiantes.',
          en:
            'Pablo split the tasks and tracked everyone’s progress without ' +
            'chasing anyone. Clear milestones, risks written down, and if ' +
            'something got stuck he sat with you until it moved. First ' +
            'lead I ever had — and we were just three students.',
        },
        options: [
          {
            label: {
              es: '¿Y la documentacion?',
              en: 'And the documentation?',
            },
            next: 'doc-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'doc-1': {
        text: {
          es:
            'Documento TODO: cada decision de arquitectura con su porque. ' +
            'Cuando llego la defensa del proyecto, los jurados preguntaban ' +
            'y nosotros ya teniamos la respuesta escrita. La defensa fue ' +
            'un paseo.',
          en:
            'He documented EVERYTHING: every architecture decision with ' +
            'its why. When the thesis defense came, the panel asked and we ' +
            'already had the answer in writing. The defense was a walk in ' +
            'the park.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste tu?',
              en: 'What did you learn?',
            },
            next: 'java-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'java-1': {
        text: {
          es:
            'Java en serio. Una cosa es pasar la materia y otra es armar ' +
            'las pantallas de presupuesto en Swing, con tablas que validan ' +
            'y consultas que no se caen. Aqui aprendi a programar de ' +
            'verdad.',
          en:
            'Real Java. Passing the course is one thing; building the ' +
            'budget screens in Swing, with validating tables and queries ' +
            'that do not fall over, is another. This is where I truly ' +
            'learned to code.',
        },
        options: [
          {
            label: { es: '¿Que construyeron?', en: 'What did you build?' },
            next: 'sistema-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-1': {
        text: {
          es:
            'Un sistema de gestion de obras publicas: presupuestos con ' +
            'partidas COVENIN, los APU de cada partida y las valuaciones ' +
            'de avance. Todo lo que aqui se hacia en Excel y papel, en una ' +
            'app de escritorio.',
          en:
            'A public-works management system: budgets with COVENIN line ' +
            'items, the unit-price analyses behind each item and the ' +
            'progress valuations. Everything this office did in Excel and ' +
            'paper, in one desktop app.',
        },
        options: [
          {
            label: {
              es: '¿Por que era dificil?',
              en: 'Why was it hard?',
            },
            next: 'dominio-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'dominio-1': {
        text: {
          es:
            'Porque el dominio esta regulado: partidas codificadas, ' +
            'tabuladores de mano de obra, porcentajes que no se inventan. ' +
            'Belkis — la de los sellos — nos enseño como se arma una ' +
            'partida de verdad. Sin ella no habia sistema.',
          en:
            'Because the domain is regulated: coded line items, labour ' +
            'wage tables, percentages you do not make up. Belkis — the one ' +
            'with the stamps — taught us how a real line item is built. ' +
            'Without her there would be no system.',
        },
        options: [
          {
            label: { es: 'Ire a hablarle', en: 'I will go talk to her' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'red-1': {
        text: {
          es:
            'La torre esa que dice SERVIDOR — NO APAGAR es el corazon de ' +
            'todo. Pablo la monto como servidor central y cableo los ' +
            'puestos. Eso preguntaselo a Marielys, que vivio la guerra de ' +
            'las copias.',
          en:
            'That tower saying SERVER — DO NOT TURN OFF is the heart of it ' +
            'all. Pablo set it up as the central server and wired the ' +
            'desks. Ask Marielys about it — she lived through the copy ' +
            'wars.',
        },
        options: [
          {
            label: { es: 'Le preguntare', en: 'I will ask her' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Resumen: tres estudiantes, un año, un instituto de obras ' +
            'entero que dejo el papel. Pablo liderando, documentando y ' +
            'programando a la vez. Entregamos a tiempo y el sistema quedo ' +
            'funcionando. ¿Que mas se le pide a una tesis?',
          en:
            'Summary: three students, one year, a whole public-works ' +
            'institute leaving paper behind. Pablo leading, documenting ' +
            'and coding at once. We delivered on time and the system kept ' +
            'running. What more can you ask of a thesis?',
        },
        options: [
          { label: { es: 'Nada mal', en: 'Not bad at all' }, next: 'bye' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Pasa por el showcase junto a la puerta: ahi corre el sistema ' +
            'de verdad. Y salud con el ventilador, que San Felipe no ' +
            'perdona.',
          en:
            'Check the showcase by the door: the real system runs there. ' +
            'And stay close to the fan — San Felipe heat shows no mercy.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },
    },
  }),

  marielys: defineDialog({
    name: { es: 'Marielys Ochoa', en: 'Marielys Ochoa' },
    chatter: [
      {
        es: 'Una sola base de datos. UNA. Antes habia seis.',
        en: 'One database. ONE. There used to be six.',
      },
      {
        es: 'El servidor no se apaga. Nunca. Por eso la etiqueta.',
        en: 'The server never goes off. Ever. Hence the label.',
      },
      {
        es: '¿Ves ese cable? Va derecho a la PC-servidor.',
        en: 'See that cable? Straight to the server PC.',
      },
      {
        es: 'Mis pantallas de partidas quedaron finas.',
        en: 'My line-item screens came out sharp.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Hola, soy Marielys, del equipo de tesis. Yo arme las ' +
            'pantallas de partidas y presupuestos. Y te advierto: si ' +
            'tocas la torre del servidor, te persigo. ¿Que quieres saber?',
          en:
            'Hi, I am Marielys, from the thesis team. I built the ' +
            'line-item and budget screens. Fair warning: touch the server ' +
            'tower and I will chase you. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que paso con las copias?',
              en: 'What happened with the copies?',
            },
            next: 'copias-1',
          },
          {
            label: {
              es: '¿Como es la red?',
              en: 'How does the network work?',
            },
            next: 'red-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, gracias', en: 'Nothing, thanks' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Tambien te puedo contar de mis pantallas o darte mi resumen ' +
            'del proyecto. Tu decides.',
          en:
            'I can also tell you about my screens or give you my summary ' +
            'of the project. Your call.',
        },
        options: [
          {
            label: { es: '¿Tus pantallas?', en: 'Your screens?' },
            next: 'pantallas-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'copias-1': {
        text: {
          es:
            'Antes cada quien tenia SU copia del presupuesto: una en la ' +
            'PC vieja, otra en un pendrive, otra impresa con tachones. ' +
            'Nada cuadraba con nada. Sumar dos hojas iguales con numeros ' +
            'distintos era el deporte de la oficina.',
          en:
            'Before, everyone had THEIR copy of the budget: one on the old ' +
            'PC, one on a pendrive, one printed and scribbled over. ' +
            'Nothing matched anything. Adding two identical sheets with ' +
            'different numbers was the office sport.',
        },
        options: [
          {
            label: {
              es: '¿Y como se arreglo?',
              en: 'And how was it fixed?',
            },
            next: 'red-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'red-1': {
        text: {
          es:
            'Pablo diseño la red: una PC como servidor central con la ' +
            'base de datos, y los demas puestos conectados por cable como ' +
            'clientes. Un solo dato, una sola verdad. Se acabaron las ' +
            'versiones desincronizadas.',
          en:
            'Pablo designed the network: one PC as the central server ' +
            'holding the database, and the other desks wired to it as ' +
            'clients. One piece of data, one truth. Desynchronised ' +
            'versions were over.',
        },
        options: [
          {
            label: { es: '¿Y funciono?', en: 'And did it work?' },
            next: 'funciono-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'funciono-1': {
        text: {
          es:
            'Funciono tan bien que dio miedo. Belkis guardaba una partida ' +
            'y el inspector la veia al instante desde su puesto. En 2015, ' +
            'en un instituto publico, montado por un estudiante. Por eso ' +
            'la etiqueta: SERVIDOR — NO APAGAR.',
          en:
            'It worked so well it was scary. Belkis saved a line item and ' +
            'the inspector saw it instantly from his desk. In 2015, in a ' +
            'public institute, set up by a student. Hence the label: ' +
            'SERVER — DO NOT TURN OFF.',
        },
        options: [
          {
            label: { es: 'Gran historia', en: 'Great story' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pantallas-1': {
        text: {
          es:
            'Formularios Swing con tablas de partidas: codigo COVENIN, ' +
            'descripcion, unidad, cantidad, precio unitario. Validando ' +
            'cada campo, porque un cero de mas aqui es una obra mal ' +
            'presupuestada alla afuera.',
          en:
            'Swing forms with line-item tables: COVENIN code, description, ' +
            'unit, quantity, unit price. Validating every field, because ' +
            'one extra zero here is a mispriced road out there.',
        },
        options: [
          {
            label: {
              es: '¿Quien te enseño el dominio?',
              en: 'Who taught you the domain?',
            },
            next: 'dominio-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'dominio-1': {
        text: {
          es:
            'Belkis, la analista. Nos sento con una partida real y nos ' +
            'desarmo el APU pieza por pieza. Pablo anotaba todo en su ' +
            'cuaderno — de ahi salieron los modelos del sistema.',
          en:
            'Belkis, the analyst. She sat us down with a real line item ' +
            'and took the unit-price analysis apart piece by piece. Pablo ' +
            'wrote it all in his notebook — the system’s models came from ' +
            'there.',
        },
        options: [
          {
            label: { es: 'Ire a verla', en: 'I will go see her' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Mi resumen: de seis copias que no cuadraban a una base ' +
            'central en red local. De rehacer hojas a guardar y listo. Y ' +
            'un lider estudiante que documentaba mas que los ingenieros. ' +
            'Firmo donde sea que eso fue un buen año.',
          en:
            'My summary: from six mismatched copies to one central ' +
            'database on a local network. From redoing sheets to save-and-' +
            'done. And a student lead who documented more than the ' +
            'engineers. I will sign anywhere that it was a good year.',
        },
        options: [
          { label: { es: 'Buen cierre', en: 'Good closing' }, next: 'bye' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Mira el diagrama de red en la pared — esta enmarcado, como ' +
            'debe ser. Y no toques el servidor, ¿ok?',
          en:
            'Look at the network diagram on the wall — framed, as it ' +
            'should be. And do not touch the server, ok?',
        },
        options: [{ label: { es: 'Prometido', en: 'Promise' }, next: null }],
      },
    },
  }),

  gregorio: defineDialog({
    name: { es: 'Ing. Gregorio Salcedo', en: 'Eng. Gregorio Salcedo' },
    chatter: [
      {
        es: 'Entre valuacion y valuacion, la ley da de 5 a 45 dias.',
        en: 'Between valuations, the law allows 5 to 45 days.',
      },
      {
        es: 'El cuadro demostrativo ya no lo armo yo. Lo arma el sistema.',
        en: 'I no longer build the progress sheet. The system does.',
      },
      {
        es: 'La curva S la pedi yo. Cortesia del inspector.',
        en: 'The S-curve was my request. Courtesy of the inspector.',
      },
      {
        es: 'Hoja de medicion, fotos de testigo, y a conformar.',
        en: 'Measurement sheet, witness photos, then sign-off.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ingeniero Gregorio Salcedo, inspector de obras. Yo conformo ' +
            'las valuaciones: certifico que lo que el contratista cobra ' +
            'es lo que de verdad ejecuto. ¿Que quieres saber?',
          en:
            'Engineer Gregorio Salcedo, works inspector. I certify the ' +
            'valuations: what the contractor bills is what was actually ' +
            'executed. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que es una valuacion?',
              en: 'What is a valuation?',
            },
            next: 'val-1',
          },
          {
            label: {
              es: '¿Como era tu trabajo antes?',
              en: 'What was your job like before?',
            },
            next: 'antes-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Siga usted, ingeniero', en: 'Carry on, engineer' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Puedo contarte de los plazos de ley o darte mi resumen del ' +
            'sistema. Lo que prefieras.',
          en:
            'I can tell you about the legal deadlines or give you my ' +
            'summary of the system. Whichever you prefer.',
        },
        options: [
          {
            label: { es: '¿Los plazos?', en: 'The deadlines?' },
            next: 'plazos-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'val-1': {
        text: {
          es:
            'El avance fisico y financiero de una obra en un periodo: ' +
            'cuanto se ejecuto de cada partida y cuanto vale. La preparo ' +
            'con las mediciones en sitio y la conformo con mi firma — sin ' +
            'esa firma, nadie cobra.',
          en:
            'The physical and financial progress of a job over a period: ' +
            'how much of each line item was executed and what it is ' +
            'worth. I prepare it from on-site measurements and sign it ' +
            'off — without that signature, nobody gets paid.',
        },
        options: [
          {
            label: { es: '¿Y la curva S?', en: 'And the S-curve?' },
            next: 'curva-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'curva-1': {
        text: {
          es:
            'Esa vista la pedi yo: avance fisico contra financiero en una ' +
            'sola grafica. Si la curva de plata sube mas rapido que la de ' +
            'obra, algo anda mal. Pablo la agrego al sistema en una ' +
            'semana. Buen muchacho.',
          en:
            'I asked for that view myself: physical versus financial ' +
            'progress in one chart. If the money curve climbs faster than ' +
            'the works curve, something is wrong. Pablo added it to the ' +
            'system within a week. Good kid.',
        },
        options: [
          {
            label: { es: '¿Como era antes?', en: 'How was it before?' },
            next: 'antes-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-1': {
        text: {
          es:
            'A mano: hojas de medicion en la obra, fotos de testigo, y de ' +
            'vuelta en la oficina a cotejar TODO contra un Excel que ' +
            'nunca cuadraba con el de presupuestos. Tres papeles para el ' +
            'mismo numero y ninguno igual.',
          en:
            'By hand: measurement sheets on site, witness photos, then ' +
            'back at the office cross-checking EVERYTHING against a ' +
            'spreadsheet that never matched the budget one. Three papers ' +
            'for the same number and none of them equal.',
        },
        options: [
          { label: { es: '¿Y ahora?', en: 'And now?' }, next: 'ahora-1' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ahora-1': {
        text: {
          es:
            'Cargo las mediciones y el sistema me arma el cuadro ' +
            'demostrativo de lo ejecutado: partidas, cantidades, montos. ' +
            'Yo reviso, conformo y listo. Mis dias se van en inspeccionar ' +
            'obra, que es mi trabajo — no en papeleo.',
          en:
            'I load the measurements and the system builds the progress ' +
            'sheet of executed work: items, quantities, amounts. I review, ' +
            'sign off, done. My days go into inspecting works, which is my ' +
            'job — not into paperwork.',
        },
        options: [
          {
            label: { es: 'Asi da gusto', en: 'That is how it should be' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'plazos-1': {
        text: {
          es:
            'La normativa da entre 5 y 45 dias entre valuacion y ' +
            'valuacion. Antes ese tiempo se me iba en armar papeles. ' +
            'Ahora el papeleo sale del sistema y el plazo se usa para lo ' +
            'que es: verificar la obra.',
          en:
            'The rules allow between 5 and 45 days from one valuation to ' +
            'the next. That time used to vanish into paperwork. Now the ' +
            'paperwork comes out of the system and the period is spent on ' +
            'what it is for: verifying the works.',
        },
        options: [
          {
            label: { es: '¿Y ahora que cambio?', en: 'And what changed?' },
            next: 'ahora-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Mi resumen de inspector: un grupo de muchachos me quito de ' +
            'encima anos de planillas. La valuacion que antes era una ' +
            'pelea de papeles hoy es un reporte que sale solo. Eso, en ' +
            'obra publica, vale oro.',
          en:
            'My inspector’s summary: a group of kids lifted years of ' +
            'spreadsheets off my back. The valuation that used to be a ' +
            'paper fight is now a report that writes itself. In public ' +
            'works, that is worth gold.',
        },
        options: [
          {
            label: { es: 'Vale oro, si', en: 'Worth gold indeed' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si quieres ver la curva S, esta en la demo del sistema, ' +
            'junto a la puerta. Yo sigo: la calle 19 no se inspecciona ' +
            'sola.',
          en:
            'If you want to see the S-curve, it is in the system demo by ' +
            'the door. I am off: street 19 does not inspect itself.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },
    },
  }),

  belkis: defineDialog({
    name: { es: 'Belkis Camacaro', en: 'Belkis Camacaro' },
    chatter: [
      {
        es: 'El BCV publico indices nuevos. Antes eso era llorar.',
        en: 'The BCV published new indexes. That used to mean tears.',
      },
      {
        es: 'Cuarenta APU en un clic. CUARENTA.',
        en: 'Forty unit-price analyses in one click. FORTY.',
      },
      {
        es: 'Yo le enseñe a Pablo que es una partida.',
        en: 'I taught Pablo what a line item is.',
      },
      {
        es: 'Materiales, mano de obra, equipos... y los porcentajes.',
        en: 'Materials, labour, equipment... and the percentages.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Belkis Camacaro, analista de presupuestos. Veinte años ' +
            'armando partidas y APU para las obras del estado. Y si, el ' +
            'sello de CONFORME es mio. ¿Que quieres saber?',
          en:
            'Belkis Camacaro, budget analyst. Twenty years building line ' +
            'items and unit-price analyses for state works. And yes, the ' +
            'APPROVED stamp is mine. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que es un APU?',
              en: 'What is a unit-price analysis?',
            },
            next: 'apu-1',
          },
          {
            label: {
              es: '¿Que pasaba con los indices?',
              en: 'What about the indexes?',
            },
            next: 'bcv-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, señora Belkis', en: 'Nothing, Ms. Belkis' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Tambien esta la historia de como Pablo aprendio el oficio, o ' +
            'mi resumen. Escoge.',
          en:
            'There is also the story of how Pablo learned the trade, or my ' +
            'summary. Pick one.',
        },
        options: [
          {
            label: {
              es: '¿Como aprendio Pablo?',
              en: 'How did Pablo learn?',
            },
            next: 'pablo-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'apu-1': {
        text: {
          es:
            'El Analisis de Precios Unitarios: de donde sale el precio de ' +
            'cada partida. Materiales con sus rendimientos, mano de obra ' +
            'con el tabulador y el FCAS, equipos... y encima los ' +
            'porcentajes de administracion, utilidad y financiamiento.',
          en:
            'The unit-price analysis: where each line item’s price comes ' +
            'from. Materials with their yields, labour with the wage table ' +
            'and social-cost factor, equipment... plus the percentages for ' +
            'administration, profit and financing.',
        },
        options: [
          {
            label: { es: '¿Y la partida?', en: 'And the line item?' },
            next: 'partida-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'partida-1': {
        text: {
          es:
            'La partida es la unidad del presupuesto: codigo COVENIN, ' +
            'descripcion, unidad — metros cubicos, kilos —, cantidad del ' +
            'computo metrico y su precio unitario. Un presupuesto de obra ' +
            'son decenas de esas, y cada una con su APU detras.',
          en:
            'The line item is the budget’s unit: COVENIN code, ' +
            'description, unit — cubic metres, kilos —, quantity from the ' +
            'takeoff and its unit price. A works budget is dozens of ' +
            'those, each with its own analysis behind it.',
        },
        options: [
          {
            label: {
              es: '¿Y tu se lo enseñaste a Pablo?',
              en: 'And you taught Pablo this?',
            },
            next: 'pablo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bcv-1': {
        text: {
          es:
            'Cada vez que el Banco Central publicaba indices nuevos, los ' +
            'precios quedaban viejos y habia que rehacer los APU. A MANO. ' +
            'Cuarenta analisis, uno por uno, con la calculadora y el ' +
            'miedo de equivocarme en un numero.',
          en:
            'Every time the Central Bank published new indexes, prices ' +
            'went stale and the analyses had to be redone. BY HAND. Forty ' +
            'of them, one by one, calculator in hand and fearing one wrong ' +
            'digit.',
        },
        options: [
          { label: { es: '¿Y ahora?', en: 'And now?' }, next: 'ahora-1' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ahora-1': {
        text: {
          es:
            'Ahora actualizo los indices y aprieto Recalcular. El sistema ' +
            'rehace los APU y el presupuesto completo al instante. Lo que ' +
            'era una semana de angustia es un clic. Todavia me rio sola ' +
            'cuando lo hago.',
          en:
            'Now I update the indexes and hit Recalculate. The system ' +
            'redoes the analyses and the whole budget instantly. What used ' +
            'to be a week of anguish is one click. I still laugh to myself ' +
            'when I do it.',
        },
        options: [
          {
            label: { es: 'Un clic bien ganado', en: 'A well-earned click' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'Pablo no llego a imponer pantallas: llego a preguntar. Se ' +
            'sento aqui con su cuaderno y me dijo "enseñeme como arma ' +
            'usted una partida". Le desarme un APU completo. Todo lo que ' +
            'el sistema calcula, lo aprendio de este escritorio.',
          en:
            'Pablo did not arrive imposing screens: he arrived asking. He ' +
            'sat right here with his notebook and said "teach me how you ' +
            'build a line item". I took a whole analysis apart for him. ' +
            'Everything the system computes, he learned at this desk.',
        },
        options: [
          {
            label: {
              es: 'Levantamiento de verdad',
              en: 'Real requirements work',
            },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Mi resumen: los muchachos convirtieron mi calculadora en un ' +
            'boton. Los indices ya no me quitan el sueño y el presupuesto ' +
            'sale cuadrado a la primera. Que Dios me los bendiga a los ' +
            'tres.',
          en:
            'My summary: those kids turned my calculator into a button. ' +
            'Indexes no longer keep me up at night and the budget balances ' +
            'on the first try. God bless all three of them.',
        },
        options: [
          { label: { es: 'Amen', en: 'Amen' }, next: 'bye' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si vas al showcase, busca la demo del APU: esa pantalla la ' +
            'cuadramos entre Pablo y yo. Y cuidado con mis sellos.',
          en:
            'If you go to the showcase, find the unit-price demo: Pablo ' +
            'and I squared that screen together. And mind my stamps.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },
    },
  }),

  maritza: defineDialog({
    name: { es: 'Ing. Maritza Oropeza', en: 'Eng. Maritza Oropeza' },
    chatter: [
      {
        es: 'El consolidado, en mi escritorio. Ya no espero jornadas.',
        en: 'The consolidated report, on my desk. No more waiting days.',
      },
      {
        es: 'Firme la carta de aceptacion con gusto.',
        en: 'I signed the acceptance letter gladly.',
      },
      {
        es: 'Obra que no se mide es obra que no avanza.',
        en: 'Works you do not measure are works that do not move.',
      },
      {
        es: 'San Felipe no se asfalta solo.',
        en: 'San Felipe does not asphalt itself.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ingeniera Maritza Oropeza, presidenta del instituto. ' +
            'Vialidad, asfaltado, edificaciones: todo lo que el estado ' +
            'construye pasa por este despacho. ¿Que necesita?',
          en:
            'Engineer Maritza Oropeza, president of the institute. Roads, ' +
            'asphalt, buildings: everything the state builds goes through ' +
            'this office. What do you need?',
        },
        options: [
          {
            label: {
              es: '¿Que exige su cargo?',
              en: 'What does your role demand?',
            },
            next: 'cargo-1',
          },
          {
            label: {
              es: '¿Que cambio con el sistema?',
              en: 'What did the system change?',
            },
            next: 'cambio-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, presidenta', en: 'Nothing, president' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Puedo hablarle del instituto o del proyecto de grado que ' +
            'aprobe. Usted dira.',
          en:
            'I can tell you about the institute or about the degree ' +
            'project I approved. Your call.',
        },
        options: [
          {
            label: { es: '¿Que es el IAI?', en: 'What is the IAI?' },
            next: 'iai-1',
          },
          {
            label: {
              es: '¿El proyecto de grado?',
              en: 'The degree project?',
            },
            next: 'grado-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cargo-1': {
        text: {
          es:
            'Firmar resoluciones y contratos de obra. Y no se firma a ' +
            'ciegas: necesito el consolidado de TODAS las obras — avance ' +
            'fisico, avance financiero, valuaciones conformadas — antes ' +
            'de poner mi nombre en un papel.',
          en:
            'Signing resolutions and works contracts. And you do not sign ' +
            'blind: I need the consolidated view of ALL the works — ' +
            'physical progress, financial progress, signed-off valuations ' +
            '— before my name goes on paper.',
        },
        options: [
          {
            label: {
              es: '¿Y antes como lo conseguia?',
              en: 'And how did you get it before?',
            },
            next: 'antes-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Lo pedia... y esperaba. Jornadas enteras de la oficina ' +
            'tecnica copiando numeros de carpeta en carpeta para armarme ' +
            'una planilla. Cuando llegaba, ya habia numeros viejos ' +
            'adentro.',
          en:
            'I asked for it... and waited. Whole workdays of the technical ' +
            'office copying numbers folder by folder to build me one ' +
            'sheet. By the time it arrived, some numbers inside were ' +
            'already stale.',
        },
        options: [
          {
            label: { es: '¿Y ahora?', en: 'And now?' },
            next: 'cambio-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cambio-1': {
        text: {
          es:
            'Ahora lo pido y sale del sistema: todas las obras, su avance ' +
            'y sus montos, al momento. Firmo con la foto real del ' +
            'instituto, no con la de hace dos semanas. Eso cambia como se ' +
            'gobierna una institucion.',
          en:
            'Now I ask and it comes out of the system: every job, its ' +
            'progress and its amounts, on the spot. I sign with the real ' +
            'picture of the institute, not the one from two weeks ago. ' +
            'That changes how you run an institution.',
        },
        options: [
          {
            label: {
              es: '¿Y el proyecto de grado?',
              en: 'And the degree project?',
            },
            next: 'grado-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'grado-1': {
        text: {
          es:
            'Cuando Pablo me planteo hacer aqui su proyecto de grado, ' +
            'firme la carta de aceptacion sin dudarlo. Tres estudiantes ' +
            'resolvieron un problema que este instituto arrastraba hace ' +
            'años. Ojala todas las tesis fueran asi.',
          en:
            'When Pablo proposed doing his degree project here, I signed ' +
            'the acceptance letter without hesitation. Three students ' +
            'solved a problem this institute had dragged for years. I wish ' +
            'every thesis were like that.',
        },
        options: [
          {
            label: { es: 'Buena apuesta', en: 'Good bet' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'iai-1': {
        text: {
          es:
            'El Instituto Autonomo de Infraestructura del Estado Yaracuy: ' +
            'el brazo de obra publica de la gobernacion. Asfaltado de ' +
            'calles, vialidad agricola, edificaciones, drenajes. Desde ' +
            'San Felipe para todo el estado.',
          en:
            'The Autonomous Infrastructure Institute of Yaracuy State: the ' +
            'governorate’s public-works arm. Street asphalting, rural ' +
            'roads, buildings, drainage. From San Felipe for the whole ' +
            'state.',
        },
        options: [
          {
            label: {
              es: '¿Y que cambio el sistema?',
              en: 'And what did the system change?',
            },
            next: 'cambio-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Recorra la sala: la valla de la calle 19 es obra nuestra. Y ' +
            'el sistema que la presupuesto, obra de esos muchachos.',
          en:
            'Walk the room: the street 19 site sign is our work. And the ' +
            'system that budgeted it, the work of those kids.',
        },
        options: [
          {
            label: { es: 'Gracias, presidenta', en: 'Thanks, president' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
