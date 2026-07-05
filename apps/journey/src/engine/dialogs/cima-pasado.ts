/**
 * @module dialogs/cima-pasado (engine)
 * @description Arboles de dialogo del "antes" de la cima (sepia): procesos
 *   manuales y silos en un solo pais. El runner que lleva papeles a pie
 *   entre areas y el operador que sostiene la "integracion" al telefono.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CIMA_PASADO_DIALOGS = {
  'runner-papeles': defineDialog({
    name: { es: 'Runner de papeles', en: 'Paper runner' },
    chatter: [
      {
        es: '¡Permiso, papeles urgentes!',
        en: 'Coming through, urgent papers!',
      },
      {
        es: 'Tercer viaje de la mañana... o cuarto.',
        en: 'Third trip this morning... or fourth.',
      },
      { es: 'Mis piernas son el API.', en: 'My legs are the API.' },
      {
        es: 'Si yo me detengo, todo se detiene.',
        en: 'If I stop, everything stops.',
      },
      {
        es: '¿Alguien vio la planilla azul?',
        en: 'Has anyone seen the blue form?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Un visitante? Dame un segundo... uf. Bienvenido al reino ' +
            'del papel: cada area en su silo y yo corriendo entre ' +
            'todas. ¿Que quieres saber?',
          en:
            'A visitor? Give me a second... phew. Welcome to the ' +
            'kingdom of paper: every area in its own silo and me ' +
            'running between all of them. What do you want to know?',
        },
        options: [
          {
            label: {
              es: 'Los silos y tus papeles',
              en: 'The silos and your papers',
            },
            next: 's1',
          },
          {
            label: { es: '¿Que mas pasa aqui?', en: 'What else goes on?' },
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
          es:
            'Pasa de todo, y todo a mano. Tenemos un admin de campañas ' +
            'que se arma pieza por pieza y un mapa que solo tiene un ' +
            'pais. ¿Por donde sigo?',
          en:
            'Everything goes on, and all of it by hand. We have a ' +
            'campaign admin assembled piece by piece and a map with ' +
            'only one country on it. Where do I go next?',
        },
        options: [
          {
            label: {
              es: 'El admin de campañas',
              en: 'The campaign admin',
            },
            next: 'c1',
          },
          {
            label: { es: 'Lo del unico pais', en: 'The one-country thing' },
            next: 'p1',
          },
          { label: { es: '¿Algo mas?', en: 'Anything else?' }, next: 'hub3' },
        ],
      },
      hub3: {
        text: {
          es:
            'Queda lo mejor: mi sueño imposible. Y bueno, si quieres ' +
            'tambien te cuento quien soy yo en todo este enredo.',
          en:
            'The best part is left: my impossible dream. And well, if ' +
            'you want I can also tell you who I am in this whole mess.',
        },
        options: [
          {
            label: {
              es: 'Tu sueño imposible',
              en: 'Your impossible dream',
            },
            next: 'd1',
          },
          {
            label: { es: '¿Tu quien eres?', en: 'Who are you anyway?' },
            next: 'w1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s1: {
        text: {
          es:
            'Mira la pila: ordenes, planillas, aprobaciones. Cada area ' +
            'vive en su silo y no se hablan entre ellas, asi que los ' +
            'papeles viajan como yo: a pie.',
          en:
            'Look at the pile: orders, forms, approvals. Every area ' +
            'lives in its own silo and they do not talk to each other, ' +
            'so the papers travel like me: on foot.',
        },
        options: [
          {
            label: { es: '¿Por que a pie?', en: 'Why on foot?' },
            next: 's2',
          },
          {
            label: {
              es: '¿Que llevas exactamente?',
              en: 'What exactly do you carry?',
            },
            next: 's2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s2: {
        text: {
          es:
            'Porque no hay nada que conecte a las areas. Ningun sistema ' +
            'las orquesta. Si finanzas necesita algo de operaciones, ' +
            'alguien tiene que llevarlo caminando. Ese alguien soy yo.',
          en:
            'Because nothing connects the areas. No system orchestrates ' +
            'them. If finance needs something from operations, someone ' +
            'has to walk it over. That someone is me.',
        },
        options: [
          {
            label: {
              es: '¿Y si se pierde un papel?',
              en: 'What if a paper gets lost?',
            },
            next: 's3',
          },
          {
            label: {
              es: '¿Cuantos viajes haces?',
              en: 'How many trips do you make?',
            },
            next: 's3b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s2b: {
        text: {
          es:
            'Hoy: dos ordenes de compra, una planilla de campaña y una ' +
            'aprobacion que necesita tres firmas. Cada firma vive en un ' +
            'piso distinto, claro.',
          en:
            'Today: two purchase orders, a campaign form and an ' +
            'approval that needs three signatures. Each signature lives ' +
            'on a different floor, of course.',
        },
        options: [
          {
            label: { es: '¿Tres firmas?', en: 'Three signatures?' },
            next: 's8',
          },
          {
            label: {
              es: '¿Y si se pierde algo?',
              en: 'What if something gets lost?',
            },
            next: 's3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s8: {
        text: {
          es:
            'Firma uno aprueba, firma dos revisa a la firma uno y firma ' +
            'tres desconfia de las otras dos. Tres pisos, tres esperas, ' +
            'un solo papel.',
          en:
            'Signature one approves, signature two double-checks ' +
            'signature one, and signature three distrusts the other ' +
            'two. Three floors, three waits, one single paper.',
        },
        options: [
          {
            label: {
              es: '¿Y si falta una firma?',
              en: 'What if a signature is missing?',
            },
            next: 's3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s3: {
        text: {
          es:
            'Se rehace desde cero. Una vez un papel desaparecio entre ' +
            'dos pisos y tres areas se acusaron durante una semana. ' +
            'Estaba en mi bolsillo. No se lo digas a nadie.',
          en:
            'You redo it from scratch. Once a paper vanished between ' +
            'two floors and three areas blamed each other for a week. ' +
            'It was in my pocket. Do not tell anyone.',
        },
        options: [
          {
            label: {
              es: '¿Nadie propone algo mejor?',
              en: 'Does nobody suggest better?',
            },
            next: 's4',
          },
          {
            label: {
              es: '¿Y los dias de lluvia?',
              en: 'What about rainy days?',
            },
            next: 's7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s3b: {
        text: {
          es:
            'Perdi la cuenta hace tiempo. Se que empiezo con el sol y ' +
            'termino con las luces del pasillo. Mis zapatos llevan la ' +
            'estadistica real.',
          en:
            'I lost count long ago. I know I start with the sun and ' +
            'finish under the hallway lights. My shoes keep the real ' +
            'statistics.',
        },
        options: [
          {
            label: { es: 'Eso no escala', en: 'That does not scale' },
            next: 's4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s7: {
        text: {
          es:
            'Con lluvia envuelvo todo en plastico y rezo. Una vez una ' +
            'planilla llego borrosa y hubo que dictarla entera por ' +
            'telefono. El operador todavia me lo recuerda.',
          en:
            'When it rains I wrap everything in plastic and pray. Once ' +
            'a form arrived smudged and it had to be dictated whole ' +
            'over the phone. The operator still reminds me of it.',
        },
        options: [
          {
            label: {
              es: '¿Nadie propone algo mejor?',
              en: 'Does nobody suggest better?',
            },
            next: 's4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s4: {
        text: {
          es:
            'Yo lo digo en broma y en serio: mis piernas son el API de ' +
            'esta empresa. Toda integracion entre areas pasa por estos ' +
            'zapatos o por el telefono de alla.',
          en:
            'I say it half joking, half serious: my legs are the API of ' +
            'this company. Every integration between areas goes through ' +
            'these shoes or through that phone over there.',
        },
        options: [
          { label: { es: '¿El... que?', en: 'The... what?' }, next: 's5' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s5: {
        text: {
          es:
            'Ni idea de donde saque la palabra. Alguien dijo que en el ' +
            'futuro los sistemas se hablaran solos por algo llamado ' +
            'asi. Mientras llega, el mensajero soy yo.',
          en:
            'No idea where I picked up the word. Someone said that in ' +
            'the future systems will talk to each other through ' +
            'something called that. Until it arrives, the messenger is ' +
            'me.',
        },
        options: [
          {
            label: { es: '¿Y el telefono?', en: 'And the phone?' },
            next: 's6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s6: {
        text: {
          es:
            'El telefono es la otra mitad del sistema. Lo que no viaja ' +
            'en papel, viaja en llamada. El operador de alla sostiene ' +
            'media empresa con ese aparato.',
          en:
            'The phone is the other half of the system. What does not ' +
            'travel on paper travels in a call. The operator over there ' +
            'holds half the company with that device.',
        },
        options: [
          {
            label: {
              es: '¿Que hace exactamente?',
              en: 'What does he do exactly?',
            },
            next: 's9',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s9: {
        text: {
          es:
            'Espera en linea, anota a mano lo que le dictan y me pasa ' +
            'las notas para que las lleve. Llamada, papel, piernas. Ese ' +
            'es el flujo completo.',
          en:
            'He waits on hold, writes down by hand what they dictate ' +
            'and hands me the notes to deliver. Call, paper, legs. That ' +
            'is the whole flow.',
        },
        options: [
          {
            label: { es: 'Ire a saludarlo', en: 'I will go say hi' },
            next: null,
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c1: {
        text: {
          es:
            'Ah, el admin de campañas. Se arma a mano, pieza por pieza, ' +
            'y toma horas. Horas de verdad, de las que duelen. Cada ' +
            'campaña nueva es una expedicion.',
          en:
            'Ah, the campaign admin. It is assembled by hand, piece by ' +
            'piece, and it takes hours. Real hours, the painful kind. ' +
            'Every new campaign is an expedition.',
        },
        options: [
          {
            label: { es: '¿Horas de verdad?', en: 'Actual hours?' },
            next: 'c2',
          },
          {
            label: { es: '¿Como se arma?', en: 'How is it assembled?' },
            next: 'c2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c2: {
        text: {
          es:
            'Entras con cafe caliente y sales cuando ya esta frio el ' +
            'tercero. Copiar datos de un lado, pegarlos en otro, ' +
            'revisar, corregir, volver a revisar.',
          en:
            'You walk in with hot coffee and walk out when the third ' +
            'cup has gone cold. Copy data from one place, paste it in ' +
            'another, check, fix, check again.',
        },
        options: [
          {
            label: {
              es: '¿Y si hay un error?',
              en: 'What if there is a mistake?',
            },
            next: 'c3',
          },
          { label: { es: '¿La peor vez?', en: 'The worst time?' }, next: 'c6' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c2b: {
        text: {
          es:
            'Cada area manda su parte por separado: una lista por aqui, ' +
            'una planilla por alla. Alguien junta todo a mano y arma la ' +
            'campaña pieza a pieza.',
          en:
            'Every area sends its part separately: a list from here, a ' +
            'form from there. Someone gathers it all by hand and builds ' +
            'the campaign piece by piece.',
        },
        options: [
          {
            label: { es: '¿Quien lo revisa?', en: 'Who reviews it?' },
            next: 'c3b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c3: {
        text: {
          es:
            'Un error y se rehace desde el principio. No hay forma de ' +
            'arreglar solo un pedazo: nadie sabe que pedazo toco a que ' +
            'otro. Mejor empezar de nuevo.',
          en:
            'One mistake and you redo it from the start. There is no ' +
            'way to fix just one piece: nobody knows which piece ' +
            'touched which. Better to start over.',
        },
        options: [
          {
            label: {
              es: '¿Nadie automatiza esto?',
              en: 'Does nobody automate this?',
            },
            next: 'c4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c3b: {
        text: {
          es:
            'Se revisa a ojo, linea por linea. Otra ronda de horas. Y ' +
            'aun asi, algo siempre se escapa: un numero cruzado, un ' +
            'nombre en la lista equivocada.',
          en:
            'It is checked by eye, line by line. Another round of ' +
            'hours. And even so, something always slips: a crossed ' +
            'number, a name on the wrong list.',
        },
        options: [
          {
            label: {
              es: '¿Y cuando se escapa?',
              en: 'And when something slips?',
            },
            next: 'c3',
          },
          {
            label: { es: '¿Quien sufre mas?', en: 'Who suffers the most?' },
            next: 'c8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c8: {
        text: {
          es:
            'El equipo de campañas. Los veo salir con la mirada ' +
            'perdida, abrazando carpetas. Gente talentosa gastando el ' +
            'dia en pegar papeles. Duele un poco.',
          en:
            'The campaign team. I see them leave with a distant stare, ' +
            'hugging folders. Talented people spending the whole day ' +
            'gluing papers together. It hurts a little.',
        },
        options: [
          {
            label: {
              es: '¿Nadie automatiza esto?',
              en: 'Does nobody automate this?',
            },
            next: 'c4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c6: {
        text: {
          es:
            'La noche antes de un lanzamiento. Todos armando el admin a ' +
            'mano hasta la madrugada. Yo dormi en la escalera, entre ' +
            'viaje y viaje. Buen colchon, mala almohada.',
          en:
            'The night before a launch. Everyone assembling the admin ' +
            'by hand until dawn. I slept on the staircase between ' +
            'trips. Good mattress, bad pillow.',
        },
        options: [
          { label: { es: '¿Y el cafe?', en: 'And the coffee?' }, next: 'c7' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c7: {
        text: {
          es:
            'El cafe es la unica infraestructura confiable de esta ' +
            'empresa. Nunca falla, nunca pide firmas y no necesita tres ' +
            'pisos de aprobacion.',
          en:
            'Coffee is the only reliable infrastructure in this ' +
            'company. It never fails, never asks for signatures and ' +
            'does not need three floors of approval.',
        },
        options: [
          {
            label: { es: 'Eso no es vida', en: 'That is no way to live' },
            next: 'c4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c4: {
        text: {
          es:
            'Automatizar suena a ciencia ficcion aqui. Cada silo guarda ' +
            'sus datos como un dragon guarda oro. Para automatizar, ' +
            'primero tendrian que hablarse.',
          en:
            'Automation sounds like science fiction around here. Every ' +
            'silo hoards its data like a dragon hoards gold. To ' +
            'automate, they would first have to talk to each other.',
        },
        options: [
          {
            label: { es: '¿Que haria falta?', en: 'What would it take?' },
            next: 'c5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      c5: {
        text: {
          es:
            'Que todo estuviera conectado. Que armar una campaña tomara ' +
            'minutos y no horas. Lo pienso mientras corro y se me ' +
            'acelera el paso solo de imaginarlo.',
          en:
            'Everything being connected. Building a campaign taking ' +
            'minutes instead of hours. I think about it while I run and ' +
            'my pace quickens just from imagining it.',
        },
        options: [
          {
            label: { es: 'Suena a un sueño', en: 'Sounds like a dream' },
            next: 'd1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p1: {
        text: {
          es:
            'Operamos en un solo pais. Uno. El mapa de la oficina tiene ' +
            'una sola bandera y aun asi apenas alcanzamos a movernos ' +
            'dentro de el.',
          en:
            'We operate in a single country. One. The office map has a ' +
            'single flag on it and even so we can barely keep up moving ' +
            'inside it.',
        },
        options: [
          {
            label: {
              es: '¿Por que no expandirse?',
              en: 'Why not expand?',
            },
            next: 'p2',
          },
          {
            label: {
              es: '¿Te gustaria salir?',
              en: 'Would you like to go abroad?',
            },
            next: 'p2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p2: {
        text: {
          es:
            'Con estos procesos, expandirse es impensable. Si un papel ' +
            'tarda una mañana en cruzar el edificio, imagina cruzar una ' +
            'frontera. Ni mis piernas dan para eso.',
          en:
            'With these processes, expanding is unthinkable. If a paper ' +
            'takes a whole morning to cross the building, imagine ' +
            'crossing a border. Not even my legs can cover that.',
        },
        options: [
          {
            label: { es: '¿Que haria falta?', en: 'What would it take?' },
            next: 'p3',
          },
          {
            label: { es: '¿Tan grave es?', en: 'Is it that bad?' },
            next: 'p5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p2b: {
        text: {
          es:
            'Me encantaria ver otros paises. Pero mi metodo de ' +
            'integracion no pasa aduana: no hay visa para un runner con ' +
            'una pila de planillas.',
          en:
            'I would love to see other countries. But my integration ' +
            'method does not clear customs: there is no visa for a ' +
            'runner with a pile of forms.',
        },
        options: [
          { label: { es: 'Ja, cierto', en: 'Ha, true' }, next: 'p3' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p5: {
        text: {
          es:
            'Piensa: cada dato entre paises seria una llamada de larga ' +
            'distancia o un sobre viajando dias. La operacion se ' +
            'quedaria dormida esperando.',
          en:
            'Think about it: every piece of data between countries ' +
            'would be a long-distance call or an envelope traveling for ' +
            'days. The operation would fall asleep waiting.',
        },
        options: [
          { label: { es: 'Entiendo', en: 'I see' }, next: 'p3' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p3: {
        text: {
          es:
            'Expandirse asi seria multiplicar los silos por cada pais ' +
            'nuevo. Mas pilas, mas llamadas, mas runners. El mismo ' +
            'caos, pero en varios idiomas.',
          en:
            'Expanding like this would multiply the silos by every new ' +
            'country. More piles, more calls, more runners. The same ' +
            'chaos, but in several languages.',
        },
        options: [
          { label: { es: '¿Entonces que?', en: 'Then what?' }, next: 'p4' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p4: {
        text: {
          es:
            'Primero habria que ordenar la casa: conectar lo que ya ' +
            'existe aqui. Con una base asi, cruzar fronteras dejaria de ' +
            'ser un sueño lejano.',
          en:
            'First the house needs to be put in order: connect what ' +
            'already exists here. With that base, crossing borders ' +
            'would stop being a distant dream.',
        },
        options: [
          {
            label: {
              es: '¿Como se conecta todo?',
              en: 'How does it all connect?',
            },
            next: 'd1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d1: {
        text: {
          es:
            'Mi sueño: una sola plataforma que orqueste todo. Las areas ' +
            'conectadas, los datos fluyendo solos, y las campañas ' +
            'armandose sin sangre ni cafe frio.',
          en:
            'My dream: one single platform orchestrating everything. ' +
            'Areas connected, data flowing on its own, and campaigns ' +
            'assembling themselves without blood or cold coffee.',
        },
        options: [
          {
            label: { es: '¿Como seria?', en: 'What would it be like?' },
            next: 'd2',
          },
          {
            label: {
              es: '¿Quien la construiria?',
              en: 'Who would build it?',
            },
            next: 'd2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d2: {
        text: {
          es:
            'Cierra los ojos: finanzas pide un dato y le llega solo. ' +
            'Una campaña se arma en minutos. Y ningun papel viaja a pie ' +
            'nunca mas. ¿Lo ves?',
          en:
            'Close your eyes: finance asks for a piece of data and it ' +
            'just arrives. A campaign assembles in minutes. And no ' +
            'paper ever travels on foot again. Can you see it?',
        },
        options: [
          {
            label: { es: '¿Y tu trabajo?', en: 'What about your job?' },
            next: 'd3',
          },
          { label: { es: '¿Orquestar?', en: 'Orchestrating?' }, next: 'd6' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d2b: {
        text: {
          es:
            'Alguien que entienda cada silo por dentro y no le tenga ' +
            'miedo a unirlos. Alguien terco, ademas: aqui el "siempre ' +
            'se hizo asi" pesa toneladas.',
          en:
            'Someone who understands every silo from the inside and is ' +
            'not afraid of joining them. Someone stubborn, too: around ' +
            'here "it has always been done this way" weighs tons.',
        },
        options: [
          {
            label: {
              es: '¿Existe alguien asi?',
              en: 'Does someone like that exist?',
            },
            next: 'd3b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d6: {
        text: {
          es:
            'Como un director de orquesta. Hoy cada area toca su propia ' +
            'cancion en su propia sala. Orquestar es que todas suenen ' +
            'juntas, a tiempo, sin gritarse.',
          en:
            'Like an orchestra conductor. Today every area plays its ' +
            'own song in its own room. Orchestrating means all of them ' +
            'sounding together, on time, without shouting.',
        },
        options: [
          {
            label: { es: 'Bonita imagen', en: 'That is a nice image' },
            next: 'd4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d3: {
        text: {
          es:
            '¿Mi trabajo? Correria igual, pero por gusto. Hay un parque ' +
            'cerca que llevo mirando desde hace tiempo. Sin planillas, ' +
            'las piernas son libertad.',
          en:
            'My job? I would keep running, but for the joy of it. There ' +
            'is a park nearby I have been eyeing for a long time. ' +
            'Without forms, legs mean freedom.',
        },
        options: [
          {
            label: {
              es: 'Ojala llegue ese dia',
              en: 'I hope that day comes',
            },
            next: 'd4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d3b: {
        text: {
          es:
            'Quiza. A veces pasa por aqui gente joven con esa mirada de ' +
            '"esto se puede hacer mejor". Uno de esos, un dia, no va a ' +
            'soltar la idea.',
          en:
            'Maybe. Sometimes young people pass through here with that ' +
            '"this can be done better" look in their eyes. One of them, ' +
            'one day, will not let go of the idea.',
        },
        options: [
          {
            label: {
              es: '¿Y si ya viene en camino?',
              en: 'What if they are on their way?',
            },
            next: 'd4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d4: {
        text: {
          es:
            'Yo creo que va a pasar. Algun dia esto sera una sola ' +
            'maquina bien afinada y estos pasillos sonaran distinto. ' +
            'Menos pasos mios, mas cosas andando.',
          en:
            'I believe it will happen. Someday this will be one ' +
            'well-tuned machine and these hallways will sound ' +
            'different. Fewer steps from me, more things moving.',
        },
        options: [
          {
            label: {
              es: '¿Y si ya llego ese dia?',
              en: 'What if that day already came?',
            },
            next: 'd5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d5: {
        text: {
          es:
            'Je. Tienes cara de venir de un lugar donde eso ya paso. No ' +
            'me cuentes el final: dejame la sorpresa. Pero camina ' +
            'despacio al salir, por si acaso.',
          en:
            'Heh. You have the face of someone coming from a place ' +
            'where that already happened. Do not tell me the ending: ' +
            'leave me the surprise. But walk out slowly, just in case.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Me despido', en: 'I will say goodbye' }, next: null },
        ],
      },
      w1: {
        text: {
          es:
            'Soy el runner. Mi cargo no aparece en ningun organigrama, ' +
            'pero si falto un dia, la empresa entera se entera. ' +
            'Literal: nadie mas lleva las noticias.',
          en:
            'I am the runner. My title does not appear on any org ' +
            'chart, but if I miss one day, the whole company notices. ' +
            'Literally: nobody else carries the news.',
        },
        options: [
          {
            label: { es: '¿Como es tu dia?', en: 'What is your day like?' },
            next: 'w2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w2: {
        text: {
          es:
            'Recojo papeles, subo pisos, espero sellos, bajo pisos, ' +
            'entrego papeles. Repite hasta que anochece. Los sellos son ' +
            'mi jefe de verdad.',
          en:
            'I pick up papers, climb floors, wait for stamps, go down ' +
            'floors, deliver papers. Repeat until nightfall. The stamps ' +
            'are my real boss.',
        },
        options: [
          {
            label: { es: '¿Y esos zapatos?', en: 'And those shoes?' },
            next: 'w3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w3: {
        text: {
          es:
            'Van varios pares este año. Ya ni los cuento: los jubilo ' +
            'con honores y una pequeña ceremonia. El de la repisa cruzo ' +
            'el edificio mas veces que el gerente.',
          en:
            'Several pairs this year already. I stopped counting: I ' +
            'retire them with honors and a small ceremony. The one on ' +
            'the shelf crossed the building more times than the ' +
            'manager.',
        },
        options: [
          {
            label: {
              es: '¿De donde sacas animo?',
              en: 'Where do you find the spirit?',
            },
            next: 'd7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d7: {
        text: {
          es:
            'De pensar que esto va a cambiar. Y de preguntarle a los ' +
            'visitantes como tu si alla afuera ya cambio. Algunos ' +
            'sonrien de una forma que me da esperanza.',
          en:
            'From believing this will change. And from asking visitors ' +
            'like you whether out there it already has. Some of them ' +
            'smile in a way that gives me hope.',
        },
        options: [
          {
            label: {
              es: 'En algunos lugares, si',
              en: 'In some places, it has',
            },
            next: 'd4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
    },
  }),
  'operador-telefono': defineDialog({
    name: { es: 'Operador de telefono', en: 'Phone operator' },
    chatter: [
      {
        es: 'Si, si... deletreamelo, por favor.',
        en: 'Yes, yes... spell it out for me, please.',
      },
      {
        es: 'No me cuelgue, sigo aqui.',
        en: 'Do not hang up, I am still here.',
      },
      {
        es: 'Linea dos, espere. Linea tres, espere.',
        en: 'Line two, hold. Line three, hold.',
      },
      {
        es: 'Esa musiquita de espera me persigue.',
        en: 'That hold music haunts me.',
      },
      {
        es: 'Aja... ¿con M de Maria?',
        en: 'Uh-huh... M as in Mary?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Espere, no cuelgue... ¡Ah, eres de carne y hueso! Que ' +
            'gusto. Aqui la integracion entre areas es este telefono y ' +
            'quien lo atiende: yo. ¿Que necesitas?',
          en:
            'Hold, please do not hang up... Ah, you are flesh and bone! ' +
            'What a treat. Around here, integration between areas is ' +
            'this phone and whoever answers it: me. What do you need?',
        },
        options: [
          {
            label: {
              es: '¿La integracion es una llamada?',
              en: 'Integration is a phone call?',
            },
            next: 't1',
          },
          {
            label: { es: 'Cuentame de tu dia', en: 'Tell me about your day' },
            next: 'hub2',
          },
          {
            label: { es: 'Sigue con lo tuyo', en: 'Carry on with your work' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Mi dia tiene dos deportes: esperar en linea y anotar a ' +
            'mano lo que dictan del otro lado. Campeon regional en ' +
            'ambos. ¿Cual te cuento?',
          en:
            'My day has two sports: waiting on hold and writing down by ' +
            'hand whatever the other side dictates. Regional champion ' +
            'at both. Which one do you want?',
        },
        options: [
          {
            label: { es: 'Esperar en linea', en: 'Waiting on hold' },
            next: 'e1',
          },
          {
            label: { es: 'Anotar a mano', en: 'Writing by hand' },
            next: 'n1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t1: {
        text: {
          es:
            'Tal cual. Si un area necesita algo de otra, no hay sistema ' +
            'que las conecte: hay una llamada. Marcan, pregunto, ' +
            'transfiero, repito. Soy la centralita humana.',
          en:
            'Exactly. If one area needs something from another, there ' +
            'is no system connecting them: there is a phone call. They ' +
            'dial, I ask, I transfer, I repeat. I am the human ' +
            'switchboard.',
        },
        options: [
          {
            label: {
              es: '¿Todo pasa por ti?',
              en: 'Does everything go through you?',
            },
            next: 't2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t2: {
        text: {
          es:
            'Casi todo. Un dato de ventas para finanzas, una fecha para ' +
            'campañas, una aprobacion urgente: todo entra por este ' +
            'auricular y sale por mi boca o por mi lapiz.',
          en:
            'Almost everything. A sales figure for finance, a date for ' +
            'campaigns, an urgent approval: it all comes in through ' +
            'this handset and leaves through my mouth or my pencil.',
        },
        options: [
          {
            label: {
              es: '¿Y si un dia faltas?',
              en: 'What if you miss a day?',
            },
            next: 't3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t3: {
        text: {
          es:
            'El dia que me resfrie, las areas simplemente dejaron de ' +
            'hablarse. Volvieron los papelitos por debajo de las ' +
            'puertas. Prefiero no faltar.',
          en:
            'The day I caught a cold, the areas simply stopped talking ' +
            'to each other. Little notes under the doors made a ' +
            'comeback. I prefer not to miss work.',
        },
        options: [
          {
            label: {
              es: 'Vaya responsabilidad',
              en: 'That is some responsibility',
            },
            next: 't4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t4: {
        text: {
          es:
            'Un cable, una libreta y mi memoria: eso sostiene media ' +
            'operacion. Cuando lo piensas mucho da vertigo, asi que ' +
            'mejor atiendo la siguiente llamada.',
          en:
            'A cable, a notebook and my memory: that holds up half the ' +
            'operation. It gets dizzying if you think about it too ' +
            'long, so I just answer the next call.',
        },
        options: [
          {
            label: {
              es: '¿No hay otra forma?',
              en: 'Is there no other way?',
            },
            next: 'do1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      e1: {
        text: {
          es:
            'La mitad de mi jornada es musica de espera. Llamo a un ' +
            'area, me dejan en linea, y mientras tanto suena esa ' +
            'melodia que ya vive en mi cabeza.',
          en:
            'Half my working day is hold music. I call an area, they ' +
            'put me on hold, and meanwhile that melody plays, the one ' +
            'that lives in my head now.',
        },
        options: [
          {
            label: { es: '¿Te la sabes?', en: 'Do you know it by heart?' },
            next: 'e2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      e2: {
        text: {
          es:
            'De memoria. La tarareo dormido, dice mi señora. ' +
            'Ta-ra-ra-ri... perdona, ya empece otra vez. Es mas ' +
            'pegajosa que los sellos del tercer piso.',
          en:
            'By heart. I hum it in my sleep, my wife says. ' +
            'Ta-ra-ra-ree... sorry, there I go again. It is stickier ' +
            'than the stamps on the third floor.',
        },
        options: [
          {
            label: {
              es: '¿Y mientras esperas?',
              en: 'And while you wait?',
            },
            next: 'e3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      e3: {
        text: {
          es:
            'Mientras espero en una linea, entra otra llamada. Y otra. ' +
            'Las notas se apilan junto al telefono como una torre que ' +
            'se inclina un poco mas cada hora.',
          en:
            'While I wait on one line, another call comes in. And ' +
            'another. The notes pile up next to the phone like a tower ' +
            'leaning a little more every hour.',
        },
        options: [
          {
            label: {
              es: '¿Como no te vuelves loco?',
              en: 'How do you stay sane?',
            },
            next: 'e4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      e4: {
        text: {
          es:
            'Respirar, anotar, repetir. Y mirar al runner pasar ' +
            'corriendo: si el aguanta con las piernas, yo aguanto con ' +
            'el oido. Nos entendemos sin hablar.',
          en:
            'Breathe, write, repeat. And watch the runner sprint by: if ' +
            'he endures with his legs, I endure with my ear. We ' +
            'understand each other without a word.',
        },
        options: [{ label: { es: 'Volver', en: 'Back' }, next: 'hub' }],
      },
      n1: {
        text: {
          es:
            'Lo que dictan del otro lado, yo lo escribo a mano. Cifras, ' +
            'nombres, fechas. Mi libreta es la base de datos oficial de ' +
            'esta empresa, me temo.',
          en:
            'Whatever the other side dictates, I write down by hand. ' +
            'Figures, names, dates. My notebook is the official ' +
            'database of this company, I am afraid.',
        },
        options: [
          {
            label: {
              es: '¿Y si escuchas mal?',
              en: 'What if you mishear?',
            },
            next: 'n2',
          },
          {
            label: {
              es: '¿A donde van las notas?',
              en: 'Where do the notes go?',
            },
            next: 'n3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      n2: {
        text: {
          es:
            'Un numero mal oido puede torcer una campaña entera. Por ' +
            'eso pido que me deletreen todo, letra por letra, aunque ' +
            'tardemos el doble.',
          en:
            'One misheard number can derail a whole campaign. That is ' +
            'why I ask them to spell everything out, letter by letter, ' +
            'even if it takes us twice as long.',
        },
        options: [
          {
            label: {
              es: '¿Deletrean todo?',
              en: 'They spell out everything?',
            },
            next: 'n2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      n2b: {
        text: {
          es:
            '"M de Maria, A de Antonio, R de Ramon..." Asi todo el dia. ' +
            'Hay tardes en que sueño que el alfabeto me llama por ' +
            'telefono para quejarse.',
          en:
            '"M as in Mary, A as in Anthony, R as in Robert..." All day ' +
            'long. Some evenings I dream the alphabet phones me in just ' +
            'to complain.',
        },
        options: [{ label: { es: 'Volver', en: 'Back' }, next: 'hub' }],
      },
      n3: {
        text: {
          es:
            'Se las doy al runner y el las lleva a pie al area que ' +
            'toque. Llamada, libreta, piernas: ese es todo nuestro ' +
            'protocolo de datos.',
          en:
            'I hand them to the runner and he carries them on foot to ' +
            'whichever area needs them. Call, notebook, legs: that is ' +
            'our entire data protocol.',
        },
        options: [
          {
            label: {
              es: 'Lo conoci, buen tipo',
              en: 'I met him, good fellow',
            },
            next: 'n4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      n4: {
        text: {
          es:
            'El mejor. Sus piernas y mi telefono son todo el sistema. ' +
            'Si algun dia esto se conecta de verdad, a los dos nos ' +
            'deben unas vacaciones largas.',
          en:
            'The best. His legs and my phone are the entire system. If ' +
            'this place ever gets truly connected, the two of us are ' +
            'owed one long vacation.',
        },
        options: [
          {
            label: {
              es: '¿Y crees que cambie?',
              en: 'Do you think it will change?',
            },
            next: 'do1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      do1: {
        text: {
          es:
            'Sueño con que las areas hablen solas, sin mi en el medio ' +
            'dictando letra por letra. Que la informacion viaje sin ' +
            'esperar el tono de marcado.',
          en:
            'I dream of the areas talking to each other on their own, ' +
            'without me in the middle dictating letter by letter. ' +
            'Information traveling without waiting for a dial tone.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que harias?',
              en: 'And what would you do?',
            },
            next: 'do2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      do2: {
        text: {
          es:
            'Atenderia personas, no planillas. Una voz que pregunta ' +
            'como estas y de verdad quiere saber. Si ese dia llega, ' +
            'brindo con el runner. Con cafe, claro.',
          en:
            'I would tend to people, not forms. A voice asking how you ' +
            'are doing and truly wanting to know. If that day comes, I ' +
            'toast with the runner. With coffee, of course.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          { label: { es: 'Hasta luego', en: 'See you later' }, next: null },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
