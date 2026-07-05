/**
 * @module dialogs/corpoelec-presente (engine)
 * @description Arboles de dialogo de la sala 1 presente: CORPOELEC (2013),
 *   subestacion y almacen donde Pablo, de pasante, construyo el sistema de
 *   inventario de activos electricos en PHP + jQuery, con modo offline y
 *   una base de datos comun para las sedes de Yaracuy, Carabobo y Lara.
 *   5 NPCs con los 2 enfoques del canon (informe 08): Yorman y Genesis
 *   (compañeros dev que construyeron con Pablo), Wilmer Colina
 *   (almacenista veterano) y Dubraska Piña (administrativa) como personal
 *   del sitio, y el Ing. Rafael Betancourt (jefe). Todos anclados a la
 *   data real: requerimientos en campo, offline por diseño, 3 sedes en
 *   una BD comun, capacitacion + guias, busquedas de 20+ min a 0,2 s.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CORPOELEC_PRESENTE_DIALOGS = {
  dubraska: defineDialog({
    name: { es: 'Dubraska Piña', en: 'Dubraska Piña' },
    chatter: [
      {
        es: 'Del papel al enter. Pablo nos cambio la vida.',
        en: 'From paper to enter. Pablo changed our lives.',
      },
      {
        es: 'El 0042... yo estuve en esa primera busqueda.',
        en: 'The 0042... I was there for that first search.',
      },
      {
        es: 'Cero coma dos segundos. Todavia sonrio.',
        en: 'Zero point two seconds. Still smiling.',
      },
      {
        es: '¿Y tu casco? Aqui se usa hasta en la oficina.',
        en: 'Where is your helmet? We wear them even at the desk.',
      },
      {
        es: 'Cierre del dia: cuadrado a la primera. Otra vez.',
        en: 'Daily closing: balanced on the first try. Again.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Bienvenido. Yo administro el inventario de esta sede: ' +
            'registros, asignaciones y cierres. En 2013 trabaje codo a ' +
            'codo con Pablo, el pasante que construyo el sistema del ' +
            'monitor. ¿Que quieres saber?',
          en:
            'Welcome. I run the inventory admin for this site: records, ' +
            'assignments and closings. In 2013 I worked side by side ' +
            'with Pablo, the intern who built the system on that ' +
            'monitor. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Quien es ese Pablo?',
              en: 'Who is this Pablo?',
            },
            next: 'pablo-1',
          },
          {
            label: {
              es: 'Cuentame la primera busqueda',
              en: 'Tell me about the first search',
            },
            next: 'busca-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, sigue con lo tuyo', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Claro que hay mas. Con Pablo dio para rato. ¿Por donde ' +
            'seguimos?',
          en:
            'Of course there is more. Pablo gave us plenty of stories. ' +
            'Where to next?',
        },
        options: [
          {
            label: {
              es: '¿Por que dice OFFLINE ahi?',
              en: 'Why does it say OFFLINE there?',
            },
            next: 'off-1',
          },
          {
            label: {
              es: 'Cuentame de las tres sedes',
              en: 'Tell me about the three sites',
            },
            next: 'sedes-1',
          },
          {
            label: { es: '¿Algo mas?', en: 'Anything else?' },
            next: 'hub3',
          },
        ],
      },
      hub3: {
        text: {
          es:
            'Queda lo mejor: como nos capacito Pablo y ese codigo verde ' +
            'del monitor. ¿O ya te vas?',
          en:
            'The best is left: how Pablo trained us and that green code ' +
            'on the monitor. Or are you leaving?',
        },
        options: [
          {
            label: {
              es: '¿Como los capacito Pablo?',
              en: 'How did Pablo train you?',
            },
            next: 'capa-1',
          },
          {
            label: {
              es: '¿Que es ese codigo verde?',
              en: 'What is that green code?',
            },
            next: 'code-1',
          },
          {
            label: {
              es: 'Volvamos al principio',
              en: 'Back to the beginning',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Cuidate ahi afuera. Y si ves a Wilmer, el veterano del ' +
            'almacen, preguntale por Pablo: lo niega todo, pero quiere ' +
            'a ese muchacho como a un hijo.',
          en:
            'Take care out there. And if you see Wilmer, the warehouse ' +
            'veteran, ask him about Pablo: he denies everything, but ' +
            'he loves that kid like a son.',
        },
        options: [
          {
            label: { es: 'Hasta luego', en: 'See you' },
            next: null,
          },
        ],
      },

      'pablo-1': {
        text: {
          es:
            'Pablo llego en 2013, de pasante, a construir el inventario ' +
            'de activos. Yo esperaba a alguien pegado a un escritorio... ' +
            'y aparecio aqui, con casco amarillo, sentandose conmigo a ' +
            'ver como cuadraba yo las planillas.',
          en:
            'Pablo arrived in 2013 as an intern, here to build the asset ' +
            'inventory. I expected someone glued to a desk... and he ' +
            'showed up here, yellow helmet on, sitting with me to watch ' +
            'how I balanced the paper records.',
        },
        options: [
          {
            label: {
              es: '¿Que te preguntaba?',
              en: 'What did he ask you?',
            },
            next: 'pablo-2',
          },
          {
            label: {
              es: '¿Confiaste en el de entrada?',
              en: 'Did you trust him right away?',
            },
            next: 'pablo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'De todo: como buscaba yo un equipo, donde anotaba, que ' +
            'pasaba si se iba la red. Pablo apuntaba cada respuesta en ' +
            'su cuaderno. Nuestro trabajo real termino dentro del sistema.',
          en:
            'Everything: how I searched for equipment, where I logged, ' +
            'what happened when the network died. Pablo wrote every ' +
            'answer in his notebook. Our real work ended up in the system.',
        },
        options: [
          {
            label: {
              es: '¿Eso era levantar requerimientos?',
              en: 'Was that requirements gathering?',
            },
            next: 'pablo-4',
          },
          {
            label: {
              es: '¿Y que salio de tanto apunte?',
              en: 'What came out of those notes?',
            },
            next: 'busca-1',
          },
        ],
      },
      'pablo-3': {
        text: {
          es:
            'Al principio no. Aqui ya habian venido a "modernizarnos" ' +
            'sin preguntar nada, y todo termino en un cajon. Pablo fue ' +
            'distinto desde el primer dia.',
          en:
            'Not at first. People had come to "modernize" us before ' +
            'without asking a thing, and it all ended in a drawer. Pablo ' +
            'was different from day one.',
        },
        options: [
          {
            label: {
              es: '¿Distinto como?',
              en: 'Different how?',
            },
            next: 'pablo-5',
          },
          {
            label: {
              es: '¿Que hacia el en cambio?',
              en: 'What did he do instead?',
            },
            next: 'pablo-4',
          },
        ],
      },
      'pablo-4': {
        text: {
          es:
            'Pablo levanto los requerimientos con nosotros, el personal ' +
            'operativo: recorrio las tres sedes, dibujo las pantallas en ' +
            'papel y nos las mostro antes de programar una sola linea.',
          en:
            'Pablo gathered the requirements with us, the operations ' +
            'staff: he toured the three sites, sketched the screens on ' +
            'paper and showed them to us before coding a single line.',
        },
        options: [
          {
            label: {
              es: '¿Y ustedes le corregian?',
              en: 'And you corrected him?',
            },
            next: 'pablo-6',
          },
          {
            label: {
              es: '¿Tambien los capacito?',
              en: 'Did he train you too?',
            },
            next: 'capa-1',
          },
        ],
      },
      'pablo-5': {
        text: {
          es:
            'Aqui lo bautizamos asi: el pasante que nos escuchaba en vez ' +
            'de imponernos el sistema. La frase es mia, que conste. Y ' +
            'Pablo se la gano dia a dia.',
          en:
            'We gave him a name here: the intern who listened to us ' +
            'instead of imposing the system on us. My phrase, for the ' +
            'record. And Pablo earned it day after day.',
        },
        options: [
          {
            label: {
              es: '¿Que le dirias hoy?',
              en: 'What would you tell him today?',
            },
            next: 'pablo-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'pablo-6': {
        text: {
          es:
            'Claro. Yo le pedi a Pablo un reporte de equipos por sede ' +
            'antes de cada cierre, y que el buscador aceptara el codigo ' +
            'con o sin ceros adelante, porque asi los dictamos aqui. A ' +
            'la semana ya tenia las dos cosas.',
          en:
            'Of course. I asked Pablo for a per-site equipment report ' +
            'before every closing, and for the search box to take codes ' +
            'with or without leading zeros, because that is how we call ' +
            'them out here. Within a week he had both.',
        },
        options: [
          {
            label: {
              es: '¿Les mostraba avances?',
              en: 'Did he show you progress?',
            },
            next: 'pablo-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'pablo-7': {
        text: {
          es:
            'Cada semana Pablo traia la pantalla y preguntaba: ¿asi ' +
            'buscan ustedes? Si algo no calzaba con el cierre o con el ' +
            'almacen, lo ajustaba. Por eso el sistema se siente hecho a ' +
            'nuestra medida.',
          en:
            'Every week Pablo brought the screen over and asked: is this ' +
            'how you search? If something did not match the closing or ' +
            'the warehouse, he adjusted it. That is why the system feels ' +
            'tailor-made.',
        },
        options: [
          {
            label: {
              es: 'Cuentame la primera busqueda',
              en: 'Tell me about the first search',
            },
            next: 'busca-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'pablo-8': {
        text: {
          es:
            'Gracias, Pablo. Mis cierres cuadran a la primera y nadie ' +
            'vuelve a perder una mañana por un papel. Y que ese cuaderno ' +
            'suyo vale mas que muchos titulos.',
          en:
            'Thank you, Pablo. My closings balance on the first try and ' +
            'nobody loses a whole morning to a piece of paper anymore. ' +
            'And that notebook of his is worth more than many diplomas.',
        },
        options: [
          {
            label: {
              es: 'Bien merecido. Volvamos',
              en: 'Well deserved. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: null,
          },
        ],
      },

      'busca-1': {
        text: {
          es:
            '¿Ves las dos pantallas del monitor? La de "carpeta 7 de 38, ' +
            'mas de veinte minutos" era nuestra vida. La de "0,2 s" es ' +
            'lo que Pablo nos dejo. Yo vivi las dos.',
          en:
            'See the two screens on the monitor? The one with "folder 7 ' +
            'of 38, twenty plus minutes" was our life. The "0.2 s" one ' +
            'is what Pablo left us. I lived both.',
        },
        options: [
          {
            label: {
              es: '¿Como era ese antes?',
              en: 'What was the before like?',
            },
            next: 'busca-2',
          },
          {
            label: {
              es: 'Cuentame la del 0042',
              en: 'Tell me the 0042 story',
            },
            next: 'busca-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'busca-2': {
        text: {
          es:
            'Planillas de papel, carpeta por carpeta. Buscar un equipo ' +
            'eran veinte minutos con suerte; por un aislador llegamos a ' +
            'perder una mañana entera. Pablo cronometro todo eso en su ' +
            'cuaderno.',
          en:
            'Paper spreadsheets, folder by folder. Finding one unit took ' +
            'twenty minutes if lucky; we once lost a whole morning over ' +
            'an insulator. Pablo timed all of it in his notebook.',
        },
        options: [
          {
            label: {
              es: '¿Y el dia del 0042?',
              en: 'And the 0042 day?',
            },
            next: 'busca-3',
          },
          {
            label: {
              es: '¿Que costaba tanta demora?',
              en: 'What did the delay cost?',
            },
            next: 'busca-4',
          },
        ],
      },
      'busca-3': {
        text: {
          es:
            'El dia de la demo, Pablo me dijo: pideme un equipo. Yo ' +
            'solte "transformador 0042" para hundirlo. Enter... 0,2 ' +
            'segundos: sede, deposito y responsable en pantalla. El ' +
            'almacen entero aplaudio.',
          en:
            'On demo day Pablo told me: ask me for any unit. I said ' +
            '"transformer 0042" to sink him. Enter... 0.2 seconds: site, ' +
            'depot and responsible on screen. The whole warehouse ' +
            'applauded.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que hiciste?',
              en: 'And what did you do?',
            },
            next: 'busca-5',
          },
          {
            label: {
              es: '¿Que cambio despues?',
              en: 'What changed afterwards?',
            },
            next: 'busca-6',
          },
        ],
      },
      'busca-4': {
        text: {
          es:
            'Cuadrillas paradas esperando un repuesto, camiones saliendo ' +
            '"a ver que hay" y compras duplicadas de cosas que ya ' +
            'teniamos. La demora costaba produccion, no solo paciencia.',
          en:
            'Crews standing around waiting for a spare, trucks leaving ' +
            '"to see what is there" and duplicate purchases of things we ' +
            'already had. The delay cost production, not just patience.',
        },
        options: [
          {
            label: {
              es: '¿Y el dia del 0042?',
              en: 'And the 0042 day?',
            },
            next: 'busca-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'busca-5': {
        text: {
          es:
            'Le hice repetirlo tres veces, convencida de que era truco. ' +
            'Pedi el 0087, el 0113, uno de Lara... todos al instante. ' +
            'Ahi entendi que Pablo nos habia devuelto horas de vida.',
          en:
            'I made him repeat it three times, sure it was a trick. I ' +
            'asked for 0087, 0113, one from Lara... all instant. That is ' +
            'when I understood Pablo had given us hours of life back.',
        },
        options: [
          {
            label: {
              es: '¿Que cambio en tu trabajo?',
              en: 'What changed in your work?',
            },
            next: 'busca-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'busca-6': {
        text: {
          es:
            'Ahora antes de cada cierre consulto la tabla: que hay, que ' +
            'se movio, que falta. Cierro el mes sabiendo que los numeros ' +
            'cuadran. Desde Pablo, el cierre sale a la primera.',
          en:
            'Now before every closing I check the table: what is there, ' +
            'what moved, what is missing. I close the month knowing the ' +
            'numbers balance. Since Pablo, closings work first try.',
        },
        options: [
          {
            label: {
              es: 'Ponlo en numeros',
              en: 'Put it in numbers',
            },
            next: 'busca-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'busca-7': {
        text: {
          es:
            'De mas de veinte minutos por busqueda a 0,2 segundos. De ' +
            'perder mañanas a no perder ninguna. Y entregado dentro del ' +
            'año previsto. Pablo cumplio con todo lo que prometio.',
          en:
            'From twenty plus minutes per search to 0.2 seconds. From ' +
            'losing mornings to losing none. Delivered within the ' +
            'planned year. Pablo delivered on everything he promised.',
        },
        options: [
          {
            label: {
              es: '¿Y la produccion de la central?',
              en: 'And the plant production?',
            },
            next: 'busca-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'busca-8': {
        text: {
          es:
            'La central respira distinto: menos cuadrillas esperando, ' +
            'menos viajes en vano, cero compras repetidas. Cuando el ' +
            'papeleo deja de estorbar, la energia fluye. Gracias, Pablo.',
          en:
            'The plant breathes differently: fewer crews waiting, fewer ' +
            'wasted trips, zero repeated purchases. When paperwork stops ' +
            'getting in the way, the energy flows. Thanks, Pablo.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
          {
            label: {
              es: 'Gran historia. Me voy',
              en: 'Great story. I will go',
            },
            next: null,
          },
        ],
      },

      'off-1': {
        text: {
          es:
            'Buen ojo. Ese OFFLINE que se vuelve ONLINE es la funcion ' +
            'estrella. Pablo pregunto primero como era la red aqui... y ' +
            'la respuesta fue: a veces no hay.',
          en:
            'Good eye. That OFFLINE flipping to ONLINE is the star ' +
            'feature. Pablo asked first what the network was like ' +
            'here... and the answer was: sometimes there is none.',
        },
        options: [
          {
            label: {
              es: '¿Como funciona sin red?',
              en: 'How does it work without network?',
            },
            next: 'off-2',
          },
          {
            label: {
              es: '¿Lo viste en accion?',
              en: 'Did you see it in action?',
            },
            next: 'off-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-2': {
        text: {
          es:
            'Si se cae la red, tu sigues registrando como si nada. ' +
            'Cuando vuelve, el sistema de Pablo sincroniza solo lo ' +
            'pendiente. Nadie pierde trabajo.',
          en:
            'If the network drops, you keep logging like nothing ' +
            'happened. When it returns, the system Pablo built syncs the ' +
            'pending work on its own. Nobody loses work.',
        },
        options: [
          {
            label: {
              es: '¿Y a donde va todo eso?',
              en: 'And where does it all go?',
            },
            next: 'off-4',
          },
          {
            label: {
              es: '¿Lo viste en accion?',
              en: 'Did you see it in action?',
            },
            next: 'off-3',
          },
        ],
      },
      'off-3': {
        text: {
          es:
            'Una tarde entera sin red en plena recepcion de equipos. ' +
            'Pablo estaba aqui esa semana y ni se inmuto: sigan ' +
            'registrando, dijo. En la noche subio todo solo.',
          en:
            'A whole afternoon without network right while receiving ' +
            'equipment. Pablo was here that week and did not flinch: ' +
            'keep logging, he said. At night it all went up by itself.',
        },
        options: [
          {
            label: {
              es: '¿El ya lo habia avisado?',
              en: 'Had he warned you before?',
            },
            next: 'off-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-4': {
        text: {
          es:
            'A la base de datos comun de las tres sedes. Una sola fuente ' +
            'de verdad. Los papeles de antes jamas se ponian de acuerdo; ' +
            'la base que armo Pablo, si.',
          en:
            'Into the shared database of the three sites. A single ' +
            'source of truth. The old papers never agreed with each ' +
            'other; the database Pablo put together does.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de esa base comun',
              en: 'Tell me about that shared DB',
            },
            next: 'sedes-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-5': {
        text: {
          es:
            'En la capacitacion Pablo lo repitio mil veces: si se va la ' +
            'red, ustedes sigan, que el sistema se encarga. Costaba ' +
            'creerle... hasta que lo vimos con nuestros ojos.',
          en:
            'During training Pablo repeated it a thousand times: if the ' +
            'network goes, you keep working, the system handles it. Hard ' +
            'to believe... until we saw it with our own eyes.',
        },
        options: [
          {
            label: {
              es: '¿Y le creyeron desde entonces?',
              en: 'And you believed him since?',
            },
            next: 'off-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-6': {
        text: {
          es:
            'Desde esa noche, ciegamente. Un sistema que aguanta nuestra ' +
            'realidad se gana el puesto. ¿Volver al papel? Ni loca.',
          en:
            'Blindly, since that night. A system that survives our ' +
            'reality earns its place. Back to paper? No way.',
        },
        options: [
          {
            label: {
              es: '¿Por que era tan clave el offline?',
              en: 'Why was offline so critical?',
            },
            next: 'off-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-7': {
        text: {
          es:
            'Porque hay sedes con conectividad de a ratos. Un sistema ' +
            'solo-online habria muerto la primera semana. Pablo lo ' +
            'diseño offline porque nos pregunto antes de programar.',
          en:
            'Because some sites get connectivity in bursts. An ' +
            'online-only system would have died its first week. Pablo ' +
            'designed it offline because he asked us before coding.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
          {
            label: {
              es: 'Eso lo explica todo',
              en: 'That explains everything',
            },
            next: null,
          },
        ],
      },

      'sedes-1': {
        text: {
          es:
            'Yaracuy, Carabobo y Lara. Tres sedes que eran tres islas de ' +
            'papel, cada una con su propia verdad. Pablo visito las tres ' +
            'para levantar los requerimientos con cada equipo.',
          en:
            'Yaracuy, Carabobo and Lara. Three sites that were three ' +
            'paper islands, each with its own truth. Pablo visited all ' +
            'three to gather requirements with every crew.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora estan conectadas?',
              en: 'And now they are connected?',
            },
            next: 'sedes-2',
          },
          {
            label: {
              es: '¿Que problemas daba el papel?',
              en: 'What problems did paper cause?',
            },
            next: 'sedes-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'sedes-2': {
        text: {
          es:
            'Una base de datos comun para las tres. Si Lara registra un ' +
            'equipo, Yaracuy y Carabobo lo ven. Se que hay en otra sede ' +
            'sin levantar el telefono, gracias a Pablo.',
          en:
            'One shared database for all three. If Lara logs a unit, ' +
            'Yaracuy and Carabobo see it. I know what sits at another ' +
            'site without picking up the phone, thanks to Pablo.',
        },
        options: [
          {
            label: {
              es: '¿Eso ahorro traslados?',
              en: 'Did that save trips?',
            },
            next: 'sedes-4',
          },
          {
            label: {
              es: '¿Y si una sede esta sin red?',
              en: 'And if a site is offline?',
            },
            next: 'off-2',
          },
        ],
      },
      'sedes-3': {
        text: {
          es:
            'Planillas duplicadas y peleadas entre si. Llegamos a ' +
            'comprar equipos que ya existian guardados en otra sede, ' +
            'porque nadie podia saberlo.',
          en:
            'Duplicated spreadsheets quarreling with each other. We even ' +
            'bought equipment that already sat in storage at another ' +
            'site, because nobody could know.',
        },
        options: [
          {
            label: {
              es: '¿Y la base comun lo arreglo?',
              en: 'Did the shared DB fix it?',
            },
            next: 'sedes-2',
          },
          {
            label: {
              es: '¿Como era pedir a otra sede?',
              en: 'How was asking another site?',
            },
            next: 'sedes-5',
          },
        ],
      },
      'sedes-4': {
        text: {
          es:
            'Muchisimos. Antes el camion salia "a ver que hay". Ahora ' +
            'sale solo cuando la tabla de Pablo dice que el equipo esta ' +
            'ahi. Destino, no esperanza.',
          en:
            'Plenty. The truck used to leave "to see what is there". Now ' +
            'it only leaves when the table Pablo built says the unit is ' +
            'there. Destination, not hope.',
        },
        options: [
          {
            label: {
              es: '¿Y Pablo cumplio los plazos?',
              en: 'Did Pablo meet the deadlines?',
            },
            next: 'sedes-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'sedes-5': {
        text: {
          es:
            'Un ritual: llamada, alguien alla dejaba todo para revisar ' +
            'carpetas, y te respondian... con suerte el mismo dia. Pablo ' +
            'convirtio ese ritual en un enter.',
          en:
            'A ritual: a phone call, someone there dropped everything to ' +
            'dig through folders, and they got back to you... same day ' +
            'if lucky. Pablo turned that ritual into one enter.',
        },
        options: [
          {
            label: {
              es: '¿Como lo logro la base comun?',
              en: 'How did the shared DB do it?',
            },
            next: 'sedes-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'sedes-6': {
        text: {
          es:
            'Dentro del año previsto, con las tres sedes andando. Un ' +
            'pasante, tres estados, cero drama. Y encima Pablo nos ' +
            'capacito antes de irse.',
          en:
            'Within the planned year, with all three sites running. One ' +
            'intern, three states, zero drama. And on top of that Pablo ' +
            'trained us before leaving.',
        },
        options: [
          {
            label: {
              es: '¿Como fue esa capacitacion?',
              en: 'How was that training?',
            },
            next: 'capa-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },

      'capa-1': {
        text: {
          es:
            'Pablo capacito al personal de cada sede, y yo estuve en el ' +
            'primer grupo. Nada de charlas eternas: practica real, con ' +
            'nuestras cajas y nuestros codigos.',
          en:
            'Pablo trained the staff at every site, and I was in the ' +
            'first group. No endless lectures: real practice, with our ' +
            'own boxes and our own codes.',
        },
        options: [
          {
            label: {
              es: '¿Como eran las sesiones?',
              en: 'What were the sessions like?',
            },
            next: 'capa-2',
          },
          {
            label: {
              es: '¿Y las guias que dejo?',
              en: 'And the guides he left?',
            },
            next: 'capa-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'capa-2': {
        text: {
          es:
            'Pablo se sentaba al lado de cada uno, sin jerga rara. ' +
            'Registrabamos equipos de verdad y buscabamos los nuestros. ' +
            'Al final nadie queria soltar el teclado.',
          en:
            'Pablo sat next to each of us, no weird jargon. We logged ' +
            'real equipment and searched for our own. By the end nobody ' +
            'wanted to let go of the keyboard.',
        },
        options: [
          {
            label: {
              es: '¿Capacito hasta a los duros?',
              en: 'Did he train the tough ones?',
            },
            next: 'capa-4',
          },
          {
            label: {
              es: '¿Y las guias?',
              en: 'And the guides?',
            },
            next: 'capa-3',
          },
        ],
      },
      'capa-3': {
        text: {
          es:
            'Pablo documento guias paso a paso, con pantallazos y todo. ' +
            'Siguen pegadas en el almacen. Ante la duda, primero la ' +
            'guia; casi siempre la respuesta esta ahi.',
          en:
            'Pablo documented step-by-step guides, screenshots and all. ' +
            'They are still pinned up in the warehouse. When in doubt, ' +
            'guide first; the answer is almost always there.',
        },
        options: [
          {
            label: {
              es: '¿Tan claras son?',
              en: 'Are they that clear?',
            },
            next: 'capa-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'capa-4': {
        text: {
          es:
            'Hasta a Wilmer, el veterano del almacen, que juraba que ' +
            'jamas tocaria una computadora. Pablo le enseño con ' +
            'paciencia de santo. Hoy busca sus repuestos solo... aunque ' +
            'lo niegue.',
          en:
            'Even Wilmer, the warehouse veteran, who swore he would ' +
            'never touch a computer. Pablo taught him with the patience ' +
            'of a saint. Now he looks up his own spares... and denies it.',
        },
        options: [
          {
            label: {
              es: '¿Y eso que demuestra?',
              en: 'And what does that prove?',
            },
            next: 'capa-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'capa-5': {
        text: {
          es:
            'Escritas para entenderse hasta con los guantes puestos, ' +
            'como deciamos aqui. Pablo escribia pensando en quien iba a ' +
            'leer, no en lucirse.',
          en:
            'Written to be understood even with gloves on, as we used to ' +
            'say here. Pablo wrote thinking of the reader, not of ' +
            'showing off.',
        },
        options: [
          {
            label: {
              es: '¿Y sirvieron a la larga?',
              en: 'Did they pay off long term?',
            },
            next: 'capa-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'capa-6': {
        text: {
          es:
            'La prueba es esta: Pablo termino su pasantia, se fue... y ' +
            'el sistema siguio andando con nosotros. Capacitar y ' +
            'documentar fue tan importante como programar.',
          en:
            'Here is the proof: Pablo finished his internship, left... ' +
            'and the system kept running with us. Training and ' +
            'documenting mattered as much as coding.',
        },
        options: [
          {
            label: {
              es: '¿Que le dirias hoy a Pablo?',
              en: 'What would you tell Pablo now?',
            },
            next: 'pablo-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },

      'code-1': {
        text: {
          es:
            'Ese codigo verde es del sistema: PHP con sus mysql_query y ' +
            'jQuery para la pantalla. Yo no leo codigo, pero Pablo me ' +
            'mostro cual linea hacia la busqueda. Brujeria buena, dije.',
          en:
            'That green code is from the system: PHP with its ' +
            'mysql_query calls and jQuery for the screen. I do not read ' +
            'code, but Pablo showed me which line ran the search. Good ' +
            'witchcraft, I said.',
        },
        options: [
          {
            label: {
              es: '¿Herramientas viejas, no?',
              en: 'Old tools, right?',
            },
            next: 'code-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'code-2': {
        text: {
          es:
            'De la epoca, 2013. Pablo decia: simple y que funcione aqui. ' +
            'Y funciono: rapido, offline y en tres sedes. La verdadera ' +
            'brujeria fue escuchar primero.',
          en:
            'Of the era, 2013. Pablo used to say: simple, and working ' +
            'here. And it worked: fast, offline and across three sites. ' +
            'The real witchcraft was listening first.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
          {
            label: {
              es: 'Buena leccion. Adios',
              en: 'Good lesson. Goodbye',
            },
            next: null,
          },
        ],
      },
    },
  }),

  wilmer: defineDialog({
    name: { es: 'Wilmer Colina', en: 'Wilmer Colina' },
    chatter: [
      {
        es: 'Este transformador y yo somos colegas.',
        en: 'This transformer and I are colleagues.',
      },
      {
        es: 'Sin casco no te me acerques mucho.',
        en: 'No helmet? Keep your distance then.',
      },
      {
        es: 'El muchacho Pablo... buen oido, ese.',
        en: 'That Pablo kid... good ears on him.',
      },
      {
        es: 'Treinta años de carpetas y un enter las jubilo.',
        en: 'Thirty years of folders, retired by one enter.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Cuidado por donde pisas. Yo vigilo este transformador desde ' +
            'antes de que llegara internet por aqui. Y si: trabaje con ' +
            'Pablo, el pasante de 2013. ¿Que buscas?',
          en:
            'Watch your step. I have watched this transformer since ' +
            'before the internet reached this place. And yes: I worked ' +
            'with Pablo, the 2013 intern. What do you want?',
        },
        options: [
          {
            label: {
              es: 'Hableme de Pablo',
              en: 'Tell me about Pablo',
            },
            next: 'pablo-1',
          },
          {
            label: {
              es: 'El dia que el tablero revivio',
              en: 'The day the board came back',
            },
            next: 'tablero-1',
          },
          {
            label: {
              es: 'Hay mas historias, ¿no?',
              en: 'There are more stories, right?',
            },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, ya me voy', en: 'Nothing, I am leaving' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Historias sobran. Del almacen, del transformador, de mi ' +
            '"conversion"... aunque esa palabra no me gusta. ¿Que ' +
            'quieres?',
          en:
            'Plenty of stories. The warehouse, the transformer, my ' +
            '"conversion"... though I do not like that word. What will ' +
            'it be?',
        },
        options: [
          {
            label: {
              es: 'Las cajas del almacen',
              en: 'The warehouse boxes',
            },
            next: 'cajas-1',
          },
          {
            label: {
              es: 'Su famosa conversion',
              en: 'Your famous conversion',
            },
            next: 'conv-1',
          },
          {
            label: {
              es: 'Hableme del transformador',
              en: 'Tell me about the transformer',
            },
            next: 'trafo-1',
          },
          {
            label: {
              es: 'Lo de "quien se llevo el radio"',
              en: 'The "who took the radio" thing',
            },
            next: 'radio-1',
          },
          {
            label: { es: 'Me despido', en: 'I will head out' },
            next: 'bye',
          },
        ],
      },

      'radio-1': {
        text: {
          es:
            'Mi cruzada personal. Antes nadie sabia quien se llevo un ' +
            'radio ni si volvio. Y si se dañaba, no quedaba registro: el ' +
            'equipo moria en silencio. Se lo pedi a Pablo tal cual: ' +
            'quiero saber quien lo tomo y a quien se le daño.',
          en:
            'My personal crusade. Nobody used to know who took a radio ' +
            'or whether it came back. And if it broke, there was no ' +
            'record: the unit died in silence. I asked Pablo for it in ' +
            'those words: I want to know who took it and on whose watch ' +
            'it broke.',
        },
        options: [
          {
            label: {
              es: '¿Y Pablo se lo dio?',
              en: 'And did Pablo deliver?',
            },
            next: 'radio-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'radio-2': {
        text: {
          es:
            'Lo metio al sistema completo: historial de asignaciones y ' +
            'registro de daños por equipo. Hoy escribo el codigo del ' +
            'radio y me dice quien lo tiene, desde cuando y que le ' +
            'paso. Un pasante oyendo al almacenista: eso no se ve todos ' +
            'los dias.',
          en:
            'He built the whole thing into the system: assignment ' +
            'history and damage log per unit. Today I type the radio ' +
            'code and it tells me who has it, since when and what ' +
            'happened to it. An intern listening to the warehouse ' +
            'keeper: you do not see that every day.',
        },
        options: [
          {
            label: {
              es: 'Bien pedido. Volvamos',
              en: 'Well asked. Back',
            },
            next: 'hub2',
          },
          {
            label: {
              es: 'Me voy con esa. Adios',
              en: 'I will leave on that. Bye',
            },
            next: null,
          },
        ],
      },
      bye: {
        text: {
          es:
            'Anda con cuidado. Y lo que te conte de Pablo queda entre ' +
            'nosotros: si Dubraska pregunta, yo lo niego todo.',
          en:
            'Move along carefully. And what I told you about Pablo stays ' +
            'between us: if Dubraska asks, I deny everything.',
        },
        options: [
          {
            label: { es: 'Trato hecho. Adios', en: 'Deal. Goodbye' },
            next: null,
          },
        ],
      },

      'pablo-1': {
        text: {
          es:
            'Pablo... Mira, yo desconfio de todo lo que tenga pantalla. ' +
            'Y me llega un pasante a "inventariar" mi almacen. Pero el ' +
            'muchacho no impuso nada: vino, pregunto y escucho.',
          en:
            'Pablo... Look, I distrust anything with a screen. And in ' +
            'comes an intern to "inventory" my warehouse. But the kid ' +
            'imposed nothing: he came, asked and listened.',
        },
        options: [
          {
            label: {
              es: '¿Que le pregunto a usted?',
              en: 'What did he ask you?',
            },
            next: 'pablo-2',
          },
          {
            label: {
              es: '¿O sea que le tiene aprecio?',
              en: 'So you are fond of him?',
            },
            next: 'pablo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Donde estaba cada repuesto. Le dije: en mi cabeza, ' +
            'muchacho. Pablo anoto todo y me contesto: su cabeza no ' +
            'puede ser el unico respaldo de esta central. Tenia razon, ' +
            'el condenado.',
          en:
            'Where every spare was. I told him: in my head, kid. Pablo ' +
            'wrote it all down and answered: your head cannot be the ' +
            'only backup this plant has. He was right, the rascal.',
        },
        options: [
          {
            label: {
              es: '¿Y que hizo con eso?',
              en: 'And what did he do with it?',
            },
            next: 'pablo-4',
          },
          {
            label: {
              es: '¿De ahi salieron las cajas?',
              en: 'Is that where the boxes came from?',
            },
            next: 'cajas-1',
          },
        ],
      },
      'pablo-3': {
        text: {
          es:
            'Yo no dije eso. Dije que escuchaba. Es distinto. ...Esta ' +
            'bien: Pablo resulto bueno. Pero si se lo cuentas a ' +
            'Dubraska, lo niego.',
          en:
            'I did not say that. I said he listened. Different thing. ' +
            '...Fine: Pablo turned out good. But if you tell Dubraska, ' +
            'I deny it.',
        },
        options: [
          {
            label: {
              es: '¿Que lo convencio de Pablo?',
              en: 'What won you over about Pablo?',
            },
            next: 'pablo-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pablo-4': {
        text: {
          es:
            'Que el sistema se adapto a como trabajamos NOSOTROS, no al ' +
            'reves. Dubraska lo bautizo bien: el pasante que nos ' +
            'escuchaba en vez de imponernos el sistema. Por una vez ' +
            'coincido con ella.',
          en:
            'That the system adapted to how WE work, not the other way ' +
            'around. Dubraska named him well: the intern who listened ' +
            'to us instead of imposing the system on us. For once, she ' +
            'and I agree.',
        },
        options: [
          {
            label: {
              es: '¿Que le diria hoy a Pablo?',
              en: 'What would you tell Pablo now?',
            },
            next: 'pablo-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pablo-5': {
        text: {
          es:
            'Que siga preguntando antes de construir. Pablo primero ' +
            'entendio la central y despues escribio el codigo. En ese ' +
            'orden. Por eso su sistema sigue vivo y mi almacen en paz.',
          en:
            'To keep asking before building. Pablo first understood the ' +
            'plant and then wrote the code. In that order. That is why ' +
            'his system is still alive and my warehouse at peace.',
        },
        options: [
          {
            label: {
              es: 'Se lo dire si lo veo',
              en: 'I will tell him if I see him',
            },
            next: 'hub',
          },
          {
            label: { es: 'Gracias. Adios', en: 'Thanks. Goodbye' },
            next: null,
          },
        ],
      },

      'tablero-1': {
        text: {
          es:
            '¿Ves ese tablero en verde? Una tarde de 2013 se puso rojo: ' +
            'falla en la subestacion y un repuesto urgente. Antes eso ' +
            'eran horas de carpetas y llamadas. Ese dia fue un enter en ' +
            'el sistema de Pablo.',
          en:
            'See that board in green? One afternoon in 2013 it went red: ' +
            'substation fault and an urgent spare needed. That used to ' +
            'mean hours of folders and calls. That day it took one enter ' +
            'in the system Pablo built.',
        },
        options: [
          {
            label: {
              es: '¿Como termino la falla?',
              en: 'How did the fault end?',
            },
            next: 'tablero-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'tablero-2': {
        text: {
          es:
            'Buscamos la pieza en la tabla: 0,2 segundos y aparecio ' +
            'guardada en Carabobo. El camion salio con destino, no a ' +
            'ciegas, y esa misma noche el tablero volvio al verde. El ' +
            'dia que el tablero volvio a la vida, le decimos.',
          en:
            'We looked the part up in the table: 0.2 seconds and there ' +
            'it was, stored in Carabobo. The truck left with a ' +
            'destination, not blind, and that same night the board went ' +
            'back to green. The day the board came back to life, we say.',
        },
        options: [
          {
            label: {
              es: '¿Pablo estaba ese dia?',
              en: 'Was Pablo there that day?',
            },
            next: 'tablero-3',
          },
          {
            label: {
              es: '¿Antes cuanto habria tardado?',
              en: 'How long would it take before?',
            },
            next: 'tablero-4',
          },
        ],
      },
      'tablero-3': {
        text: {
          es:
            'Estaba, terminando su pasantia. ¿Y sabes que hizo cuando ' +
            'todos celebraban? Saco el cuaderno y anoto que se podia ' +
            'mejorar. Asi era Pablo: la fiesta cinco minutos, las notas ' +
            'toda la vida.',
          en:
            'He was, wrapping up his internship. And you know what he ' +
            'did while everyone celebrated? He pulled out the notebook ' +
            'and wrote down what could be better. That was Pablo: five ' +
            'minutes of party, a lifetime of notes.',
        },
        options: [
          {
            label: {
              es: '¿Que le diria hoy?',
              en: 'What would you tell him now?',
            },
            next: 'pablo-5',
          },
          {
            label: {
              es: '¿Y antes del sistema?',
              en: 'And before the system?',
            },
            next: 'tablero-4',
          },
        ],
      },
      'tablero-4': {
        text: {
          es:
            'Años atras una falla parecida nos tuvo dos dias a media ' +
            'marcha, porque el repuesto "no existia"... y estaba ' +
            'guardado en Lara. Con la base comun de Pablo, eso no vuelve ' +
            'a pasar.',
          en:
            'Years back a similar fault kept us two days at half ' +
            'capacity, because the spare "did not exist"... and it sat ' +
            'in storage in Lara. With the shared database Pablo built, ' +
            'that never happens again.',
        },
        options: [
          {
            label: {
              es: '¿Y usted termino usandolo?',
              en: 'And you ended up using it?',
            },
            next: 'conv-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },

      'cajas-1': {
        text: {
          es:
            '¿Ves esas cajas etiquetadas? Obra de Pablo. Etiqueto hasta ' +
            'la ultima caja del almacen para meterla al inventario. Caja ' +
            'por caja, con este calor.',
          en:
            'See those labeled boxes? All Pablo. He labeled every last ' +
            'box in the warehouse to load it into the inventory. Box by ' +
            'box, in this heat.',
        },
        options: [
          {
            label: {
              es: '¿Usted lo ayudo?',
              en: 'Did you help him?',
            },
            next: 'cajas-2',
          },
          {
            label: {
              es: '¿Y sirvio de algo?',
              en: 'And was it worth it?',
            },
            next: 'cajas-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'cajas-2': {
        text: {
          es:
            'Dos semanas juntos: yo dictaba de memoria que habia en cada ' +
            'caja y Pablo etiquetaba y registraba. Aposte a que se ' +
            'rendia en la tercera fila. Perdi la apuesta y gane un ' +
            'sistema.',
          en:
            'Two weeks side by side: I dictated from memory what was in ' +
            'each box and Pablo labeled and logged. I bet he would quit ' +
            'by the third row. I lost the bet and won a system.',
        },
        options: [
          {
            label: {
              es: '¿Y sirvio de algo?',
              en: 'And was it worth it?',
            },
            next: 'cajas-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'cajas-3': {
        text: {
          es:
            'Un inventario vale lo que vale su peor etiqueta. Por eso la ' +
            'tabla de Pablo no miente: hoy el 0042 aparece antes de que ' +
            'se me enfrie el cafe.',
          en:
            'An inventory is worth its worst label. That is why the ' +
            'table Pablo built does not lie: today the 0042 shows up ' +
            'before my coffee gets cold.',
        },
        options: [
          {
            label: {
              es: '¿Y el dia del tablero?',
              en: 'And the board day?',
            },
            next: 'tablero-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },

      'conv-1': {
        text: {
          es:
            'Al principio me negue a tocar el aparato. Pablo no se burlo ' +
            'ni una vez: se sento conmigo tardes enteras, hasta que el ' +
            'teclado dejo de ganarme.',
          en:
            'At first I refused to touch the thing. Pablo never mocked ' +
            'me once: he sat with me whole afternoons, until the ' +
            'keyboard stopped beating me.',
        },
        options: [
          {
            label: {
              es: '¿Y las guias que dejo?',
              en: 'And the guides he left?',
            },
            next: 'conv-2',
          },
          {
            label: {
              es: '¿Recuerda su primera busqueda?',
              en: 'Remember your first search?',
            },
            next: 'conv-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'conv-2': {
        text: {
          es:
            'Pablo me dejo guias impresas, paso a paso, con dibujitos. ' +
            'Escritas para que hasta yo las siguiera, y mira que soy ' +
            'caso dificil. Las guardo en ese cajon como oro.',
          en:
            'Pablo left me printed guides, step by step, little pictures ' +
            'included. Written so even I could follow them, and I am a ' +
            'tough case. I keep them in that drawer like gold.',
        },
        options: [
          {
            label: {
              es: '¿Y hoy las usa?',
              en: 'Do you use them today?',
            },
            next: 'conv-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'conv-3': {
        text: {
          es:
            'Escribi con dos dedos, temblando, y enter: 0,2 segundos. ' +
            'Murmure: treinta años buscando carpetas como un tonto. ' +
            'Pablo tuvo la decencia de no reirse.',
          en:
            'I typed with two fingers, shaking, and enter: 0.2 seconds. ' +
            'I muttered: thirty years digging through folders like a ' +
            'fool. Pablo had the decency not to laugh.',
        },
        options: [
          {
            label: {
              es: '¿Y desde entonces?',
              en: 'And since then?',
            },
            next: 'conv-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'conv-4': {
        text: {
          es:
            'Desde entonces las tres sedes vemos lo mismo y ya no llamo ' +
            'a Lara por cada tuerca. Hasta les enseño el sistema a los ' +
            'nuevos... con las guias de Pablo, claro.',
          en:
            'Since then the three sites see the same thing and I no ' +
            'longer call Lara over every bolt. I even teach the system ' +
            'to the new hires... with the guides from Pablo, of course.',
        },
        options: [
          {
            label: {
              es: '¿Usted, enseñando el sistema?',
              en: 'You, teaching the system?',
            },
            next: 'conv-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'conv-5': {
        text: {
          es:
            'La vida da vueltas. El que renegaba de las pantallas, ' +
            'repartiendo guias. Elogio uno por decada, y el de esta ya ' +
            'se lo llevo Pablo.',
          en:
            'Life comes full circle. The man who cursed screens, handing ' +
            'out guides. One compliment per decade, and this decade it ' +
            'went to Pablo.',
        },
        options: [
          {
            label: {
              es: 'Bien ganado. Volvamos',
              en: 'Well earned. Back',
            },
            next: 'hub2',
          },
          {
            label: {
              es: 'Me voy con esa. Adios',
              en: 'I will leave on that. Bye',
            },
            next: null,
          },
        ],
      },

      'trafo-1': {
        text: {
          es:
            'Esta belleza sube y baja tension como quien respira. Y una ' +
            'maquina asi se cuida sabiendo QUE tienes y DONDE esta: ' +
            'repuestos, piezas, aceite. Antes era un misterio de papel; ' +
            'ahora vive en la tabla de Pablo.',
          en:
            'This beauty steps voltage up and down like breathing. And ' +
            'you care for a machine like this by knowing WHAT you have ' +
            'and WHERE it is: spares, parts, oil. It used to be a paper ' +
            'mystery; now it lives in the table Pablo built.',
        },
        options: [
          {
            label: {
              es: '¿Como sabe que esta sano?',
              en: 'How do you know it is healthy?',
            },
            next: 'trafo-2',
          },
          {
            label: {
              es: '¿La tabla lo salvo alguna vez?',
              en: 'Did the table ever save it?',
            },
            next: 'tablero-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
      'trafo-2': {
        text: {
          es:
            'Por el zumbido: un transformador sano canta parejo. Treinta ' +
            'años oyendo la misma cancion. Pero donde duerme cada ' +
            'repuesto... eso mi oido no lo sabe. Eso lo sabe el enter de ' +
            'Pablo.',
          en:
            'By the hum: a healthy transformer sings steady. Thirty ' +
            'years hearing the same song. But where each spare sleeps... ' +
            'my ear does not know that. The enter Pablo gave us knows.',
        },
        options: [
          {
            label: {
              es: 'Cuenteme lo del tablero',
              en: 'Tell me about the board',
            },
            next: 'tablero-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub2',
          },
        ],
      },
    },
  }),

  yorman: defineDialog({
    name: { es: 'Yorman Rodriguez', en: 'Yorman Rodriguez' },
    chatter: [
      {
        es: 'mysql_query... que tiempos aquellos.',
        en: 'mysql_query... those were the days.',
      },
      {
        es: 'Commit del viernes: "funciona en las 3 sedes".',
        en: 'Friday commit: "works across all 3 sites".',
      },
      {
        es: 'Offline primero. Pablo tenia razon.',
        en: 'Offline first. Pablo was right.',
      },
      {
        es: 'jQuery en 2013 era magia pura.',
        en: 'jQuery in 2013 was pure magic.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Hola, soy Yorman, del equipo de desarrollo. Con Pablo ' +
            'construimos este sistema en 2013: el CRUD en PHP, las ' +
            'tablas en jQuery y la base de datos que une las tres ' +
            'sedes. ¿Que te cuento?',
          en:
            'Hey, I am Yorman, from the dev team. Pablo and I built ' +
            'this system back in 2013: the CRUD in PHP, the jQuery ' +
            'tables and the database that joins the three sites. What ' +
            'can I tell you?',
        },
        options: [
          {
            label: {
              es: '¿Como construyeron el CRUD?',
              en: 'How did you build the CRUD?',
            },
            next: 'crud-1',
          },
          {
            label: {
              es: 'Hablame de la base de datos',
              en: 'Tell me about the database',
            },
            next: 'bd-1',
          },
          {
            label: {
              es: '¿Por que offline?',
              en: 'Why offline?',
            },
            next: 'off-1',
          },
          {
            label: { es: 'Nada, sigue codeando', en: 'Nothing, keep coding' },
            next: null,
          },
        ],
      },
      'crud-1': {
        text: {
          es:
            'PHP del 2013, sin frameworks: formularios para registrar ' +
            'equipos y asociarlos a personas y dependencias, y jQuery ' +
            'para que la tabla se sintiera viva. Pablo repetia: simple ' +
            'y que funcione AQUI, con lo que hay.',
          en:
            '2013-era PHP, no frameworks: forms to register equipment ' +
            'and link it to people and departments, plus jQuery so the ' +
            'grid felt alive. Pablo kept saying: simple, and working ' +
            'HERE, with what we have.',
        },
        options: [
          {
            label: {
              es: '¿Que fue lo mas dificil?',
              en: 'What was the hardest part?',
            },
            next: 'crud-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'crud-2': {
        text: {
          es:
            'Que cada pantalla calzara con el trabajo real. Pablo venia ' +
            'del campo con el cuaderno lleno y me decia: el almacenista ' +
            'dicta los codigos sin ceros, la administrativa cierra por ' +
            'sede. El codigo salia de esas notas, no al reves.',
          en:
            'Making every screen match the real work. Pablo came back ' +
            'from the field with a full notebook and told me: the ' +
            'warehouse keeper calls codes without zeros, the admin ' +
            'closes by site. The code came out of those notes, not the ' +
            'other way around.',
        },
        options: [
          {
            label: {
              es: '¿Y la base de datos?',
              en: 'And the database?',
            },
            next: 'bd-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bd-1': {
        text: {
          es:
            'Relacional y sin adornos: equipo, responsable, sede. Cada ' +
            'asignacion es una fila con su fecha, asi el historial sale ' +
            'gratis. La modelamos con Pablo en una pizarra antes de ' +
            'escribir una sola tabla.',
          en:
            'Relational and plain: equipment, responsible, site. Every ' +
            'assignment is a row with its date, so the history comes ' +
            'for free. Pablo and I modeled it on a whiteboard before ' +
            'writing a single table.',
        },
        options: [
          {
            label: {
              es: '¿Por que era tan importante?',
              en: 'Why did it matter so much?',
            },
            next: 'bd-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bd-2': {
        text: {
          es:
            'Porque antes habia una copia en papel por sede y ninguna ' +
            'coincidia. Una sola base para Yaracuy, Carabobo y Lara ' +
            'acabo con las planillas duplicadas: un dato, una fila, una ' +
            'verdad.',
          en:
            'Because before there was one paper copy per site and none ' +
            'of them matched. A single database for Yaracuy, Carabobo ' +
            'and Lara ended the duplicated records: one fact, one row, ' +
            'one truth.',
        },
        options: [
          {
            label: {
              es: '¿Y como aguanta sin red?',
              en: 'How does it survive offline?',
            },
            next: 'off-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'off-1': {
        text: {
          es:
            'Esa fue la pelea buena de Pablo. Yo queria empezar por la ' +
            'tabla bonita; el insistio en el modo offline DESDE el ' +
            'diseño, no como parche. Si la red se cae, la sede sigue ' +
            'registrando local y sincroniza cuando vuelve.',
          en:
            'That was Pablo at his best. I wanted to start with the ' +
            'pretty grid; he insisted on offline mode FROM the design, ' +
            'not as a patch. If the network drops, the site keeps ' +
            'logging locally and syncs when it returns.',
        },
        options: [
          {
            label: {
              es: '¿Y tenia razon?',
              en: 'And was he right?',
            },
            next: 'off-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'off-2': {
        text: {
          es:
            'Toda. Aqui la conectividad va y viene, y el sistema ni se ' +
            'entera: quedo desplegado en los tres estados funcionando ' +
            'offline. Si lo hubieramos hecho solo-online, no pasaba de ' +
            'la primera semana.',
          en:
            'Completely. Connectivity here comes and goes, and the ' +
            'system does not even notice: it shipped to all three ' +
            'states running offline. Online-only, it would not have ' +
            'survived its first week.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste de Pablo?',
              en: 'What did you learn from Pablo?',
            },
            next: 'pablo-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'Que primero se entiende la operacion y despues se abre el ' +
            'editor. Pablo era el pasante y termino marcando como ' +
            'trabajabamos todos: campo, cuaderno, diseño, codigo. En ' +
            'ese orden.',
          en:
            'That first you understand the operation and then you open ' +
            'the editor. Pablo was the intern and ended up shaping how ' +
            'we all worked: field, notebook, design, code. In that ' +
            'order.',
        },
        options: [
          {
            label: {
              es: 'Buena escuela. Volvamos',
              en: 'Good school. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: null,
          },
        ],
      },
    },
  }),

  genesis: defineDialog({
    name: { es: 'Genesis Marcano', en: 'Genesis Marcano' },
    chatter: [
      {
        es: 'Guia de la sede Lara: lista y plastificada.',
        en: 'Lara site guide: done and laminated.',
      },
      {
        es: 'Pantallazo, flecha roja, paso 3. Asi se documenta.',
        en: 'Screenshot, red arrow, step 3. That is documentation.',
      },
      {
        es: 'Hoy toca revisar las notas de campo.',
        en: 'Field notes review day today.',
      },
      {
        es: 'El cuaderno de Pablo deberia estar en un museo.',
        en: 'That notebook of Pablo belongs in a museum.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Soy Genesis, tambien del equipo de desarrollo. Con Pablo ' +
            'me toco la parte que nadie ve: levantar requerimientos en ' +
            'campo y escribir las guias de cada sede. ¿Que quieres ' +
            'saber?',
          en:
            'I am Genesis, also on the dev team. With Pablo I handled ' +
            'the part nobody sees: gathering requirements in the field ' +
            'and writing the guides for each site. What do you want to ' +
            'know?',
        },
        options: [
          {
            label: {
              es: '¿Como era el trabajo de campo?',
              en: 'What was fieldwork like?',
            },
            next: 'campo-1',
          },
          {
            label: {
              es: 'Hablame de las guias',
              en: 'Tell me about the guides',
            },
            next: 'guias-1',
          },
          {
            label: { es: 'Nada, sigue con eso', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      'campo-1': {
        text: {
          es:
            'Pablo iba a campo ANTES de codear. Recorrimos las tres ' +
            'sedes preguntando al personal operativo como buscaban, ' +
            'donde anotaban, que se perdia. Volviamos con el cuaderno ' +
            'lleno y las pantallas dibujadas en papel.',
          en:
            'Pablo went to the field BEFORE coding. We toured the ' +
            'three sites asking the operations staff how they ' +
            'searched, where they logged, what got lost. We came back ' +
            'with a full notebook and the screens sketched on paper.',
        },
        options: [
          {
            label: {
              es: '¿Y eso cambio el sistema?',
              en: 'Did that change the system?',
            },
            next: 'campo-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'campo-2': {
        text: {
          es:
            'Lo definio. El modo offline salio de escuchar "aqui la ' +
            'red se va"; el historial de asignaciones, de escuchar a ' +
            'Wilmer; los reportes por sede, de escuchar a Dubraska. ' +
            'Nada de eso estaba en el enunciado de la pasantia.',
          en:
            'It defined it. Offline mode came from hearing "the ' +
            'network drops here"; the assignment history came from ' +
            'listening to Wilmer; the per-site reports, from listening ' +
            'to Dubraska. None of that was in the internship brief.',
        },
        options: [
          {
            label: {
              es: '¿Y las guias que escribieron?',
              en: 'And the guides you wrote?',
            },
            next: 'guias-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'guias-1': {
        text: {
          es:
            'Una guia basica por sede, paso a paso, con pantallazos. ' +
            'Pablo insistia en escribir para quien iba a leer: el ' +
            'personal de cada sede, no otros programadores. Todavia ' +
            'estan pegadas en los almacenes.',
          en:
            'One basic guide per site, step by step, with screenshots. ' +
            'Pablo insisted on writing for the reader: the staff at ' +
            'each site, not other programmers. They are still pinned ' +
            'up in the warehouses.',
        },
        options: [
          {
            label: {
              es: '¿Sirvieron de verdad?',
              en: 'Did they actually help?',
            },
            next: 'guias-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'guias-2': {
        text: {
          es:
            'La prueba: Pablo entrego dentro del año, capacito al ' +
            'personal de cada sede y se fue... y el sistema siguio ' +
            'andando sin nosotros encima. Documentar y capacitar valio ' +
            'tanto como el codigo.',
          en:
            'The proof: Pablo delivered within the year, trained the ' +
            'staff at every site and left... and the system kept ' +
            'running without us hovering. Documenting and training ' +
            'were worth as much as the code.',
        },
        options: [
          {
            label: {
              es: '¿Que quedo de esa epoca?',
              en: 'What remains from that time?',
            },
            next: 'guias-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'guias-3': {
        text: {
          es:
            'La costumbre. Aqui ya nadie construye nada sin pasar por ' +
            'el campo primero y sin dejar la guia escrita. Eso lo ' +
            'trajo un pasante de 2013. Y el cafe con Wilmer, que sigue ' +
            'contando lo del radio a todo el que pasa.',
          en:
            'The habit. Nobody here builds anything anymore without ' +
            'going through the field first and leaving a written ' +
            'guide. A 2013 intern brought that in. And coffee with ' +
            'Wilmer, who still tells the radio story to everyone who ' +
            'walks by.',
        },
        options: [
          {
            label: {
              es: 'Buena herencia. Volvamos',
              en: 'Fine legacy. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: null,
          },
        ],
      },
    },
  }),

  rafael: defineDialog({
    name: { es: 'Ing. Rafael Betancourt', en: 'Eng. Rafael Betancourt' },
    chatter: [
      {
        es: 'Tres estados, un inventario. Quien lo diria.',
        en: 'Three states, one inventory. Who would have thought.',
      },
      {
        es: 'El informe del cierre llego solo. Me gusta.',
        en: 'The closing report arrived on its own. I like that.',
      },
      {
        es: 'Firmo mas rapido de lo que antes buscabamos.',
        en: 'I sign faster than we used to search.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ingeniero Betancourt, a cargo de esta sede. Si vienes por ' +
            'la historia del sistema de inventario, llegaste al que ' +
            'firmo aquella pasantia en 2013. ¿Que quieres saber?',
          en:
            'Engineer Betancourt, in charge of this site. If you are ' +
            'here for the story of the inventory system, you found the ' +
            'man who signed off that internship in 2013. What do you ' +
            'want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que entrego la pasantia?',
              en: 'What did the internship deliver?',
            },
            next: 'balance-1',
          },
          {
            label: {
              es: '¿Que tenia Pablo de especial?',
              en: 'What made Pablo special?',
            },
            next: 'clave-1',
          },
          {
            label: { es: 'Nada, gracias', en: 'Nothing, thanks' },
            next: null,
          },
        ],
      },
      'balance-1': {
        text: {
          es:
            'Un sistema de inventario funcionando en tres estados — ' +
            'Yaracuy, Carabobo y Lara — con modo offline y una base ' +
            'comun, entregado dentro del año y con el personal de cada ' +
            'sede capacitado. Eso, de un pasante. Yo he visto proyectos ' +
            'con presupuesto entregar menos.',
          en:
            'An inventory system running in three states — Yaracuy, ' +
            'Carabobo and Lara — with offline mode and a shared ' +
            'database, delivered within the year with the staff of ' +
            'every site trained. From an intern. I have seen funded ' +
            'projects deliver less.',
        },
        options: [
          {
            label: {
              es: '¿Y en numeros?',
              en: 'And in numbers?',
            },
            next: 'balance-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'balance-2': {
        text: {
          es:
            'Localizar un equipo pasaba de varios minutos de papel — a ' +
            'veces una mañana — a una consulta inmediata, y unas tres ' +
            'sedes quedaron en una sola base, aproximadamente sin ' +
            'planillas duplicadas desde entonces. Los numeros exactos ' +
            'los tiene el sistema; yo firmo el resumen.',
          en:
            'Locating a unit went from several minutes of paperwork — ' +
            'sometimes a whole morning — to an immediate lookup, and ' +
            'roughly three sites ended up on a single database, with ' +
            'no duplicated records to speak of since. The system keeps ' +
            'the exact numbers; I sign the summary.',
        },
        options: [
          {
            label: {
              es: '¿Que tenia Pablo de especial?',
              en: 'What made Pablo special?',
            },
            next: 'clave-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'clave-1': {
        text: {
          es:
            'Que entendio la operacion real, no solo el codigo. Antes ' +
            'de programar se fue a campo con el personal: al almacen ' +
            'con Wilmer, a los cierres con Dubraska. Cuando me trajo ' +
            'el diseño, ya era la central en pantallas.',
          en:
            'He understood the real operation, not just the code. ' +
            'Before programming he went to the field with the staff: ' +
            'the warehouse with Wilmer, the closings with Dubraska. By ' +
            'the time he brought me the design, it was already the ' +
            'plant on screens.',
        },
        options: [
          {
            label: {
              es: '¿Lo volveria a contratar?',
              en: 'Would you hire him again?',
            },
            next: 'clave-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'clave-2': {
        text: {
          es:
            'Sin leer el curriculum. Un profesional que escucha ' +
            'primero, entrega a tiempo y deja al equipo capacitado no ' +
            'abunda. Donde este trabajando hoy, estan en buenas manos.',
          en:
            'Without reading the resume. A professional who listens ' +
            'first, delivers on time and leaves the team trained is a ' +
            'rare find. Wherever he works today, they are in good ' +
            'hands.',
        },
        options: [
          {
            label: {
              es: 'Se lo dire. Volvamos',
              en: 'I will pass it on. Back',
            },
            next: 'hub',
          },
          {
            label: { es: 'Gracias, ingeniero', en: 'Thanks, engineer' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
