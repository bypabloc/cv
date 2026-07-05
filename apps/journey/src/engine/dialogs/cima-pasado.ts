/**
 * @module dialogs/cima-pasado (engine)
 * @description Arboles de dialogo del "antes" de la cima (sepia): la
 *   operacion pre-arquitecto — campañas lanzadas a mano que tardan horas,
 *   Chile y Mexico coordinados a punta de telefono y papeles, un frontend
 *   monolitico donde los equipos se pisan y entidades nuevas que tardan
 *   meses. El runner que lleva papeles a pie entre escritorios y el
 *   operador que sostiene la "integracion" al telefono; ambos cierran con
 *   el rumor del arquitecto que viene a ordenar todo.
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
        es: '¿Alguien vio la planilla de Mexico?',
        en: 'Has anyone seen the Mexico form?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Un visitante? Dame un segundo... uf. Bienvenido al reino ' +
            'del papel: cada equipo en su silo, dos paises que ' +
            'coordinar y yo corriendo en el medio. ¿Que quieres saber?',
          en:
            'A visitor? Give me a second... phew. Welcome to the ' +
            'kingdom of paper: every team in its own silo, two ' +
            'countries to coordinate and me running in between. What ' +
            'do you want to know?',
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
            'Pasa de todo, y todo a mano. Campañas que tardan horas en ' +
            'salir y dos paises que se hablan por telefono. ¿Por donde ' +
            'sigo?',
          en:
            'Everything goes on, and all of it by hand. Campaigns that ' +
            'take hours to go out and two countries talking to each ' +
            'other by phone. Where do I go next?',
        },
        options: [
          {
            label: {
              es: 'Las campañas a mano',
              en: 'The handmade campaigns',
            },
            next: 'c1',
          },
          {
            label: {
              es: 'Lo de los dos paises',
              en: 'The two-country thing',
            },
            next: 'p1',
          },
          { label: { es: '¿Algo mas?', en: 'Anything else?' }, next: 'hub3' },
        ],
      },
      hub3: {
        text: {
          es:
            'Queda el tablero gigante donde los equipos se pisan y la ' +
            'historia de la entidad nueva que tardo meses. Elige tu ' +
            'dolor favorito.',
          en:
            'There is still the giant board where the teams step on ' +
            'each other, and the story of the new entity that took ' +
            'months. Pick your favorite pain.',
        },
        options: [
          {
            label: { es: 'El tablero gigante', en: 'The giant board' },
            next: 'm1',
          },
          {
            label: {
              es: 'La entidad de los meses',
              en: 'The months-long entity',
            },
            next: 'x1',
          },
          {
            label: { es: '¿Y algo bueno?', en: 'Anything good?' },
            next: 'hub4',
          },
        ],
      },
      hub4: {
        text: {
          es:
            'Lo bueno: mi sueño imposible, un rumor fresquito de ' +
            'pasillo y, si quieres, quien soy yo en todo este enredo.',
          en:
            'The good part: my impossible dream, a fresh hallway rumor ' +
            'and, if you want, who I am in this whole mess.',
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
            label: { es: 'El rumor del pasillo', en: 'The hallway rumor' },
            next: 'r1',
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
            'Mira la pila: ordenes, planillas, aprobaciones. Cada ' +
            'equipo vive en su silo y no se hablan entre ellos, asi ' +
            'que los papeles viajan como yo: a pie, de escritorio en ' +
            'escritorio.',
          en:
            'Look at the pile: orders, forms, approvals. Every team ' +
            'lives in its own silo and they do not talk to each other, ' +
            'so the papers travel like me: on foot, desk to desk.',
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
            'Porque no hay nada que conecte a los equipos. Ningun ' +
            'sistema los orquesta. Si finanzas necesita algo de ' +
            'operaciones, alguien tiene que llevarlo caminando. Ese ' +
            'alguien soy yo.',
          en:
            'Because nothing connects the teams. No system ' +
            'orchestrates them. If finance needs something from ' +
            'operations, someone has to walk it over. That someone is ' +
            'me.',
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
            'dos pisos y tres equipos se acusaron durante una semana. ' +
            'Estaba en mi bolsillo. No se lo digas a nadie.',
          en:
            'You redo it from scratch. Once a paper vanished between ' +
            'two floors and three teams blamed each other for a week. ' +
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
            'esta empresa. Toda integracion entre equipos pasa por ' +
            'estos zapatos o por el telefono de alla.',
          en:
            'I say it half joking, half serious: my legs are the API of ' +
            'this company. Every integration between teams goes through ' +
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
            'media empresa, y a Mexico entero, con ese aparato.',
          en:
            'The phone is the other half of the system. What does not ' +
            'travel on paper travels in a call. The operator over there ' +
            'holds half the company, and all of Mexico, with that ' +
            'device.',
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
            'Ah, las campañas. Se lanzan a mano, pieza por pieza, y ' +
            'toman horas. La ultima se comio seis horas y dos turnos ' +
            'de cafe. Cada campaña nueva es una expedicion.',
          en:
            'Ah, the campaigns. They are launched by hand, piece by ' +
            'piece, and they take hours. The last one ate six hours ' +
            'and two coffee shifts. Every new campaign is an ' +
            'expedition.',
        },
        options: [
          {
            label: { es: '¿Seis horas?', en: 'Six hours?' },
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
            'Cada equipo manda su parte por separado: una lista por ' +
            'aqui, una planilla por alla, una cifra dictada desde ' +
            'Mexico. Alguien junta todo a mano y arma la campaña pieza ' +
            'a pieza.',
          en:
            'Every team sends its part separately: a list from here, a ' +
            'form from there, a figure dictated from Mexico. Someone ' +
            'gathers it all by hand and builds the campaign piece by ' +
            'piece.',
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
            'La noche antes de un lanzamiento doble: Chile y Mexico el ' +
            'mismo dia. Todos armando campañas a mano hasta la ' +
            'madrugada. Yo dormi en la escalera, entre viaje y viaje.',
          en:
            'The night before a double launch: Chile and Mexico on the ' +
            'same day. Everyone assembling campaigns by hand until ' +
            'dawn. I slept on the staircase between trips.',
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
            'Que todo estuviera conectado. Que lanzar una campaña ' +
            'tomara minutos y no horas. Alguien lo dijo una vez en una ' +
            'reunion y todos se rieron. Yo no me rei.',
          en:
            'Everything being connected. Launching a campaign taking ' +
            'minutes instead of hours. Someone said it once in a ' +
            'meeting and everybody laughed. I did not laugh.',
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
            'Operamos en dos paises. Aqui ayudamos a la gente a salir ' +
            'de sus deudas; en Mexico damos creditos por niveles. ' +
            'Suena bonito hasta que ves como se coordina.',
          en:
            'We operate in two countries. Here we help people get out ' +
            'of debt; in Mexico we offer tiered credits. It sounds ' +
            'lovely until you see how it is coordinated.',
        },
        options: [
          {
            label: {
              es: '¿Como se coordina?',
              en: 'How is it coordinated?',
            },
            next: 'p2',
          },
          {
            label: {
              es: '¿Creditos por niveles?',
              en: 'Tiered credits?',
            },
            next: 'p2b',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p2: {
        text: {
          es:
            'A punta de telefono y papeles. Cada cifra cruza la ' +
            'frontera dictada en una llamada de larga distancia, y la ' +
            'version escrita la corro yo entre escritorios.',
          en:
            'By phone and paper, plain and simple. Every figure ' +
            'crosses the border dictated over a long-distance call, ' +
            'and I run the written version between desks.',
        },
        options: [
          {
            label: {
              es: '¿Y los horarios?',
              en: 'What about the time zones?',
            },
            next: 'p3',
          },
          {
            label: {
              es: '¿Que puede salir mal?',
              en: 'What can go wrong?',
            },
            next: 'p5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p2b: {
        text: {
          es:
            'Empiezas con un credito chico y, si pagas bien, subes de ' +
            'nivel. La idea es buena. El papeleo para sostenerla entre ' +
            'dos paises es el villano de la pelicula.',
          en:
            'You start with a small credit and, if you pay well, you ' +
            'move up a tier. The idea is good. The paperwork holding it ' +
            'together across two countries is the villain of the movie.',
        },
        options: [
          {
            label: {
              es: '¿Como se coordina?',
              en: 'How is it coordinated?',
            },
            next: 'p2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p3: {
        text: {
          es:
            'Cuando alla arranca el dia, aqui ya vamos por el tercer ' +
            'cafe. Quedan pocas horas en que los dos paises estan ' +
            'despiertos a la vez, y en esa ventana se decide todo. A ' +
            'gritos.',
          en:
            'When their day starts over there, we are on our third ' +
            'coffee here. There are only a few hours when both ' +
            'countries are awake at the same time, and everything gets ' +
            'decided in that window. Loudly.',
        },
        options: [
          {
            label: { es: 'Eso no escala', en: 'That does not scale' },
            next: 'p4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p5: {
        text: {
          es:
            'Una vez la llamada con Mexico se corto a la mitad y ' +
            'lanzamos con cifras viejas. Una semana entera cuadrando ' +
            'numeros a mano. El operador todavia suspira cuando lo ' +
            'cuenta.',
          en:
            'Once the call with Mexico dropped halfway through and we ' +
            'launched with stale figures. A whole week squaring numbers ' +
            'by hand. The operator still sighs when he tells it.',
        },
        options: [
          { label: { es: '¿Y entonces?', en: 'So what then?' }, next: 'p4' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p4: {
        text: {
          es:
            'Alguien tendria que orquestar los dos paises: que los ' +
            'datos crucen la frontera solos, sin larga distancia ni ' +
            'planillas viajeras. Ese dia jubilo mis zapatos con ' +
            'honores.',
          en:
            'Someone would have to orchestrate both countries: data ' +
            'crossing the border on its own, no long distance, no ' +
            'traveling forms. That day I retire my shoes with honors.',
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
      m1: {
        text: {
          es:
            'El sistema que ven los clientes es UN solo tablero ' +
            'gigante donde trabajan todos los equipos a la vez. ' +
            'Imagina cuatro pintores sobre el mismo lienzo, codo ' +
            'contra codo.',
          en:
            'The system our clients see is ONE giant board where every ' +
            'team works at the same time. Picture four painters on the ' +
            'same canvas, elbow against elbow.',
        },
        options: [
          {
            label: { es: '¿Y que pasa?', en: 'And what happens?' },
            next: 'm2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m2: {
        text: {
          es:
            'Que se pisan. Un equipo mueve un boton y a otro se le ' +
            'rompe su pantalla. Nadie sabe quien toco que, y de pronto ' +
            'todos corren por el pasillo... como yo, pero sin mi ' +
            'tecnica.',
          en:
            'They step on each other. One team moves a button and ' +
            'another team watches its screen break. Nobody knows who ' +
            'touched what, and suddenly everyone is running down the ' +
            'hallway... like me, but without my technique.',
        },
        options: [
          {
            label: {
              es: '¿Y los lanzamientos?',
              en: 'What about releases?',
            },
            next: 'm3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m3: {
        text: {
          es:
            'Cuando un equipo publica, los demas se congelan y cruzan ' +
            'los dedos. Una tarde entera de "no toques nada". Es mi ' +
            'unico momento tranquilo para entregar papeles.',
          en:
            'When one team publishes, the rest freeze and cross their ' +
            'fingers. A whole afternoon of "do not touch anything". It ' +
            'is my only quiet window to deliver papers.',
        },
        options: [
          {
            label: {
              es: '¿Nadie lo separa?',
              en: 'Does nobody split it up?',
            },
            next: 'm4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m4: {
        text: {
          es:
            'Se habla de partirlo en piezas, una por equipo, para que ' +
            'cada quien avance en paralelo sin chocar. Suena a ' +
            'sueño... y ultimamente los sueños andan contagiosos por ' +
            'aqui.',
          en:
            'There is talk of splitting it into pieces, one per team, ' +
            'so everyone can move in parallel without crashing. Sounds ' +
            'like a dream... and lately dreams have been contagious ' +
            'around here.',
        },
        options: [
          {
            label: { es: '¿Contagiosos como?', en: 'Contagious how?' },
            next: 'r1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      x1: {
        text: {
          es:
            'Una entidad financiera nueva quiso sumarse a la ' +
            'plataforma. ¿Sabes cuanto tardo? Meses. Yo gaste dos ' +
            'pares de zapatos solo en ese proyecto.',
          en:
            'A new financial entity wanted to join the platform. Do ' +
            'you know how long it took? Months. I wore out two pairs ' +
            'of shoes on that project alone.',
        },
        options: [
          {
            label: { es: '¿Por que meses?', en: 'Why months?' },
            next: 'x2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      x2: {
        text: {
          es:
            'Porque todo se rehace a mano: cada pantalla, cada ' +
            'formulario, cada color. Es como construir la casa entera ' +
            'de nuevo solo porque llego un vecino.',
          en:
            'Because everything is rebuilt by hand: every screen, ' +
            'every form, every color. It is like building the whole ' +
            'house again just because a neighbor arrived.',
        },
        options: [
          {
            label: {
              es: '¿No se puede copiar la base?',
              en: 'Can the base not be copied?',
            },
            next: 'x3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      x3: {
        text: {
          es:
            'Deberia poderse: misma base, otro logo, lista en dias. ' +
            'Pero hoy nadie sabe por donde cortar sin que se caiga el ' +
            'resto. Otro sueño para la lista.',
          en:
            'It should be possible: same base, different logo, ready ' +
            'in days. But today nobody knows where to cut without the ' +
            'rest collapsing. Another dream for the list.',
        },
        options: [
          {
            label: {
              es: '¿Y quien haria eso?',
              en: 'And who would do that?',
            },
            next: 'r1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      d1: {
        text: {
          es:
            'Mi sueño: una sola plataforma que orqueste todo. Los ' +
            'equipos sin pisarse, los dos paises hablandose solos y ' +
            'las campañas listas en minutos, sin sangre ni cafe frio.',
          en:
            'My dream: one single platform orchestrating everything. ' +
            'Teams not stepping on each other, both countries talking ' +
            'on their own and campaigns ready in minutes, without ' +
            'blood or cold coffee.',
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
            'Cierra los ojos: una campaña se arma en minutos. Un dato ' +
            'cruza la frontera sin telefono. Y ningun papel viaja a ' +
            'pie nunca mas. ¿Lo ves?',
          en:
            'Close your eyes: a campaign assembles in minutes. A ' +
            'figure crosses the border without a phone. And no paper ' +
            'ever travels on foot again. Can you see it?',
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
            'Como un director de orquesta. Hoy cada equipo toca su ' +
            'propia cancion en su propia sala, y Mexico toca la suya a ' +
            'kilometros. Orquestar es que todas suenen juntas, a ' +
            'tiempo, sin gritarse.',
          en:
            'Like an orchestra conductor. Today every team plays its ' +
            'own song in its own room, and Mexico plays theirs miles ' +
            'away. Orchestrating means all of them sounding together, ' +
            'on time, without shouting.',
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
            'Quiza ya existe. Justo ahora corre un rumor por los ' +
            'pasillos que me tiene con la sonrisa torcida. Preguntame ' +
            'por el rumor: me encanta contarlo.',
          en:
            'Maybe that someone already exists. Right now there is a ' +
            'rumor going around the hallways that has me grinning ' +
            'sideways. Ask me about the rumor: I love telling it.',
        },
        options: [
          {
            label: { es: 'Cuentame el rumor', en: 'Tell me the rumor' },
            next: 'r1',
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
      r1: {
        text: {
          es:
            'El rumor: contrataron a un arquitecto. De software, ' +
            'dicen, y viene a ordenar todo esto: los silos, el tablero ' +
            'gigante, los dos paises. Llega cualquier dia de estos.',
          en:
            'The rumor: they hired an architect. A software one, they ' +
            'say, coming to put all of this in order: the silos, the ' +
            'giant board, the two countries. Arriving any day now.',
        },
        options: [
          {
            label: { es: '¿Y tu le crees?', en: 'And do you believe it?' },
            next: 'r2',
          },
          {
            label: { es: '¿Que dice la gente?', en: 'What do people say?' },
            next: 'r3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r2: {
        text: {
          es:
            'Yo si le creo. Alguien que mire el edificio completo y no ' +
            'solo su pedazo es justo lo que falta. Ya estoy ensayando ' +
            'mi cara de "te lo dije".',
          en:
            'I do believe it. Someone who looks at the whole building ' +
            'and not just their own piece is exactly what is missing. ' +
            'I am already rehearsing my "told you so" face.',
        },
        options: [
          {
            label: { es: '¿Y si falla?', en: 'What if it fails?' },
            next: 'r4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r3: {
        text: {
          es:
            'Mitad y mitad. El operador dice que ya vio tres ' +
            'reorganizaciones y que ninguna apago su telefono. Yo le ' +
            'digo que ninguna de esas trajo un arquitecto.',
          en:
            'Half and half. The operator says he has seen three ' +
            'reorganizations and none of them silenced his phone. I ' +
            'tell him none of those brought an architect.',
        },
        options: [
          {
            label: {
              es: '¿Por que tu si le crees?',
              en: 'Why do you believe it?',
            },
            next: 'r2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r4: {
        text: {
          es:
            'Si falla, sigo corriendo, que tampoco es tan malo. Pero ' +
            'no va a fallar. Y tu... je, tu hueles a futuro. No me ' +
            'cuentes el final: solo dime si debo estirar antes.',
          en:
            'If it fails, I keep running, which is not so bad. But it ' +
            'will not fail. And you... heh, you smell of the future. ' +
            'Do not tell me the ending: just tell me whether I should ' +
            'stretch first.',
        },
        options: [
          {
            label: {
              es: 'Estira, por si acaso',
              en: 'Stretch, just in case',
            },
            next: null,
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
        es: '¿Mexico? No cuelgue, aqui sigo.',
        en: 'Mexico? Do not hang up, I am still here.',
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
            'gusto. Aqui la integracion entre equipos, y entre paises, ' +
            'es este telefono y quien lo atiende: yo. ¿Que necesitas?',
          en:
            'Hold, please do not hang up... Ah, you are flesh and ' +
            'bone! What a treat. Around here, integration between ' +
            'teams, and between countries, is this phone and whoever ' +
            'answers it: me. What do you need?',
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
            'Mi dia tiene tres deportes: esperar en linea, anotar a ' +
            'mano y marcarle a Mexico. Campeon regional en los tres. ' +
            '¿Cual te cuento?',
          en:
            'My day has three sports: waiting on hold, writing by ' +
            'hand and dialing Mexico. Regional champion at all three. ' +
            'Which one do you want?',
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
          {
            label: { es: 'La linea con Mexico', en: 'The Mexico line' },
            next: 'mx1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t1: {
        text: {
          es:
            'Tal cual. Si un equipo necesita algo de otro, no hay ' +
            'sistema que los conecte: hay una llamada. Marcan, ' +
            'pregunto, transfiero, repito. Soy la centralita humana.',
          en:
            'Exactly. If one team needs something from another, there ' +
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
            'Casi todo. Una cifra de cobranza para finanzas, una fecha ' +
            'para campañas, un nivel de credito desde Mexico: todo ' +
            'entra por este auricular y sale por mi boca o por mi ' +
            'lapiz.',
          en:
            'Almost everything. A collections figure for finance, a ' +
            'date for campaigns, a credit tier from Mexico: it all ' +
            'comes in through this handset and leaves through my mouth ' +
            'or my pencil.',
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
            'El dia que me resfrie, los equipos simplemente dejaron de ' +
            'hablarse. Volvieron los papelitos por debajo de las ' +
            'puertas. Prefiero no faltar.',
          en:
            'The day I caught a cold, the teams simply stopped talking ' +
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
            'operacion en dos paises. Cuando lo piensas mucho da ' +
            'vertigo, asi que mejor atiendo la siguiente llamada.',
          en:
            'A cable, a notebook and my memory: that holds up half an ' +
            'operation across two countries. It gets dizzying if you ' +
            'think about it too long, so I just answer the next call.',
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
            'equipo, me dejan en linea, y mientras tanto suena esa ' +
            'melodia que ya vive en mi cabeza.',
          en:
            'Half my working day is hold music. I call a team, they ' +
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
            'Lo que dictan del otro lado, yo lo escribo a mano. ' +
            'Cifras, nombres, niveles de credito. Mi libreta es la ' +
            'base de datos oficial de esta empresa, me temo.',
          en:
            'Whatever the other side dictates, I write down by hand. ' +
            'Figures, names, credit tiers. My notebook is the official ' +
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
            'Se las doy al runner y el las lleva a pie al escritorio ' +
            'que toque. Llamada, libreta, piernas: ese es todo nuestro ' +
            'protocolo de datos.',
          en:
            'I hand them to the runner and he carries them on foot to ' +
            'whichever desk needs them. Call, notebook, legs: that is ' +
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
      mx1: {
        text: {
          es:
            'Mexico da creditos por niveles; aca la gente sale de sus ' +
            'deudas. Todo lo que une a los dos paises pasa por esta ' +
            'linea de larga distancia. Si se corta, se corta el pais ' +
            'entero.',
          en:
            'Mexico runs tiered credits; here people work their way ' +
            'out of debt. Everything joining the two countries goes ' +
            'through this long-distance line. If it drops, a whole ' +
            'country drops with it.',
        },
        options: [
          {
            label: {
              es: '¿Que viaja por ahi?',
              en: 'What travels through it?',
            },
            next: 'mx2',
          },
          {
            label: {
              es: '¿Y se corta seguido?',
              en: 'Does it drop often?',
            },
            next: 'mx3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      mx2: {
        text: {
          es:
            'Cifras de campañas, niveles de credito, aprobaciones. ' +
            'Todo dictado y deletreado: "M de Maria, X de xilofono". ' +
            'Una cifra mal oida en la frontera cuesta una semana.',
          en:
            'Campaign figures, credit tiers, approvals. All dictated ' +
            'and spelled out: "M as in Mary, X as in xylophone". One ' +
            'misheard figure at the border costs a week.',
        },
        options: [
          { label: { es: '¿Una semana?', en: 'A week?' }, next: 'mx3' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      mx3: {
        text: {
          es:
            'Se corto a mitad de un lanzamiento y salieron numeros ' +
            'viejos. Dias cuadrando a mano de los dos lados. Desde ' +
            'entonces le hablo bonito al telefono, por si acaso.',
          en:
            'It dropped in the middle of a launch and stale numbers ' +
            'went out. Days squaring figures by hand on both sides. ' +
            'Since then I speak sweetly to the phone, just in case.',
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
      do1: {
        text: {
          es:
            'Sueño con que los equipos y los paises hablen solos, sin ' +
            'mi en el medio dictando letra por letra. Que la ' +
            'informacion cruce la frontera sin esperar el tono de ' +
            'marcado.',
          en:
            'I dream of teams and countries talking to each other on ' +
            'their own, without me in the middle dictating letter by ' +
            'letter. Information crossing the border without waiting ' +
            'for a dial tone.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que harias?',
              en: 'And what would you do?',
            },
            next: 'do2',
          },
          {
            label: {
              es: '¿Crees que pase?',
              en: 'Do you think it will happen?',
            },
            next: 'r1',
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
      r1: {
        text: {
          es:
            'Ja. Te llego el rumor, ¿verdad? Que contrataron a un ' +
            'arquitecto que viene a ordenar todo. Yo he visto tres ' +
            'reorganizaciones y ninguna apago este telefono.',
          en:
            'Ha. The rumor reached you, right? That they hired an ' +
            'architect who is coming to put everything in order. I ' +
            'have seen three reorganizations and none of them silenced ' +
            'this phone.',
        },
        options: [
          {
            label: {
              es: '¿Y si esta vez es distinto?',
              en: 'What if this time is different?',
            },
            next: 'r2',
          },
          {
            label: {
              es: 'El runner si le cree',
              en: 'The runner does believe it',
            },
            next: 'r3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r2: {
        text: {
          es:
            'Distinto seria que alguien mirara el sistema completo en ' +
            'vez de parchar su pedazo. Si este arquitecto hace eso... ' +
            'bueno. Le doy una semana antes de volver a dudar.',
          en:
            'Different would be someone looking at the whole system ' +
            'instead of patching their own piece. If this architect ' +
            'does that... fine. I give him a week before I go back to ' +
            'doubting.',
        },
        options: [
          {
            label: { es: 'Algo es algo', en: 'That is something' },
            next: 'r4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r3: {
        text: {
          es:
            'El runner le cree a cualquiera que corra en su misma ' +
            'direccion. Pero te confieso algo: guarde una hoja en ' +
            'blanco en la libreta. Por si hay que anotar un milagro.',
          en:
            'The runner believes anyone running in his same direction. ' +
            'But I will confess something: I saved a blank page in my ' +
            'notebook. In case a miracle needs writing down.',
        },
        options: [
          { label: { es: '¿Un milagro?', en: 'A miracle?' }, next: 'r4' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      r4: {
        text: {
          es:
            'Si algun dia este telefono suena menos y las campañas ' +
            'salen en minutos, invito el cafe. Y oye... tu hueles ' +
            'raro. A futuro. No se si me gusta o me asusta.',
          en:
            'If someday this phone rings less and campaigns go out in ' +
            'minutes, coffee is on me. And hey... you smell odd. Of ' +
            'the future. I cannot tell if I like it or fear it.',
        },
        options: [
          {
            label: {
              es: 'Guarda esa hoja en blanco',
              en: 'Keep that blank page',
            },
            next: null,
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
