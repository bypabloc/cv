/**
 * @module dialogs/corpoelec-presente (engine)
 * @description Arboles de dialogo de la sala 1 presente: CORPOELEC (2013),
 *   subestacion y almacen donde Pablo, de pasante, construyo el sistema de
 *   inventario de activos electricos en PHP + jQuery, con modo offline y
 *   una base de datos comun para las sedes de Yaracuy, Carabobo y Lara.
 *   Los dos tecnicos trabajaron con Pablo: el les levanto requerimientos,
 *   los capacito, les dejo guias documentadas y les cambio la produccion
 *   (busquedas de 20+ min en papel a 0,2 s).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CORPOELEC_PRESENTE_DIALOGS = {
  'tecnica-ronda': defineDialog({
    name: { es: 'Tecnica de ronda', en: 'Rounds technician' },
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
        es: '¿Y tu casco? Quedate cerca de mi.',
        en: 'Where is your helmet? Stay close.',
      },
      {
        es: 'Reviso, anoto, sigo. Ronda es ronda.',
        en: 'Check, log, move on. Rounds are rounds.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Bienvenido a la subestacion. Yo hago la ronda de inspeccion ' +
            'y en 2013 trabaje codo a codo con Pablo, el pasante que ' +
            'construyo el sistema del monitor. ¿Que quieres saber?',
          en:
            'Welcome to the substation. I do the inspection rounds, and ' +
            'in 2013 I worked side by side with Pablo, the intern who ' +
            'built the system on that monitor. What do you want to know?',
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
            label: { es: 'Nada, sigue tu ronda', en: 'Nothing, carry on' },
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
            'Cuidate ahi afuera. Y si ves al veterano del transformador, ' +
            'preguntale por Pablo: lo niega todo, pero quiere a ese ' +
            'muchacho como a un hijo.',
          en:
            'Take care out there. And if you see the veteran by the ' +
            'transformer, ask him about Pablo: he denies everything, but ' +
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
            'y aparecio aqui, con casco amarillo, siguiendome la ronda.',
          en:
            'Pablo arrived in 2013 as an intern, here to build the asset ' +
            'inventory. I expected someone glued to a desk... and he ' +
            'showed up here, yellow helmet on, following my rounds.',
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
            'Claro. Yo le dije a Pablo que el buscador debia aceptar el ' +
            'codigo con o sin ceros adelante, porque asi los dictamos ' +
            'aqui. A la semana ya lo tenia cambiado.',
          en:
            'Of course. I told Pablo the search box had to take the code ' +
            'with or without leading zeros, because that is how we call ' +
            'them out here. Within a week he had it changed.',
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
            'buscan ustedes? Si algo no calzaba con la ronda, lo ' +
            'ajustaba. Por eso el sistema se siente hecho a nuestra ' +
            'medida.',
          en:
            'Every week Pablo brought the screen over and asked: is this ' +
            'how you search? If something did not match the rounds, he ' +
            'adjusted it. That is why the system feels tailor-made.',
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
            'Gracias, Pablo. Mi ronda rinde el doble y nadie vuelve a ' +
            'perder una mañana por un papel. Y que ese cuaderno suyo ' +
            'vale mas que muchos titulos.',
          en:
            'Thank you, Pablo. My rounds are twice as productive and ' +
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
              es: '¿Que cambio en tu ronda?',
              en: 'What changed in your rounds?',
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
            'Ahora antes de salir consulto la tabla: que hay, que se ' +
            'movio, que falta. Llego a cada punto sabiendo que voy a ' +
            'encontrar. Desde Pablo, la ronda rinde el doble.',
          en:
            'Now before heading out I check the table: what is there, ' +
            'what moved, what is missing. I reach each stop knowing what ' +
            'to expect. Since Pablo, rounds are twice as productive.',
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
            'Hasta al veterano del transformador, que juraba que jamas ' +
            'tocaria una computadora. Pablo le enseño con paciencia de ' +
            'santo. Hoy busca sus repuestos solo... aunque lo niegue.',
          en:
            'Even the veteran by the transformer, who swore he would ' +
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

  'tecnico-subestacion': defineDialog({
    name: { es: 'Tecnico veterano', en: 'Veteran technician' },
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
            label: { es: 'Me despido', en: 'I will head out' },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Anda con cuidado. Y lo que te conte de Pablo queda entre ' +
            'nosotros: si la de la ronda pregunta, yo lo niego todo.',
          en:
            'Move along carefully. And what I told you about Pablo stays ' +
            'between us: if the rounds tech asks, I deny everything.',
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
            'bien: Pablo resulto bueno. Pero si se lo cuentas a la de la ' +
            'ronda, lo niego.',
          en:
            'I did not say that. I said he listened. Different thing. ' +
            '...Fine: Pablo turned out good. But if you tell the rounds ' +
            'tech, I deny it.',
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
            'reves. La de la ronda lo bautizo bien: el pasante que nos ' +
            'escuchaba en vez de imponernos el sistema. Por una vez ' +
            'coincido con ella.',
          en:
            'That the system adapted to how WE work, not the other way ' +
            'around. The rounds tech named him well: the intern who ' +
            'listened to us instead of imposing the system on us. For ' +
            'once, she and I agree.',
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
} satisfies Record<string, NpcDialog>
