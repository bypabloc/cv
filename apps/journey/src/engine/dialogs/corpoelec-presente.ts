/**
 * @module dialogs/corpoelec-presente (engine)
 * @description Arboles de dialogo de la sala 1 presente: CORPOELEC (2013),
 *   subestacion y almacen donde Pablo, de pasante, construyo el sistema de
 *   inventario de activos electricos en PHP + jQuery, con modo offline y
 *   una base de datos comun para las sedes de Yaracuy, Carabobo y Lara.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CORPOELEC_PRESENTE_DIALOGS = {
  'tecnica-ronda': defineDialog({
    name: { es: 'Tecnica de ronda', en: 'Rounds technician' },
    chatter: [
      {
        es: 'Medidores en verde. Todo en orden.',
        en: 'Meters in the green. All good.',
      },
      {
        es: '¿Y tu casco? Quedate cerca de mi.',
        en: 'Where is your helmet? Stay close.',
      },
      {
        es: 'Antes esto era papel. Puro papel.',
        en: 'This used to be paper. All paper.',
      },
      {
        es: 'La planta suena bien hoy. Se nota.',
        en: 'The plant sounds right today.',
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
            'Bienvenido a la subestacion. Yo hago la ronda de inspeccion, ' +
            'asi que conozco cada rincon. ¿Que quieres saber?',
          en:
            'Welcome to the substation. I do the inspection rounds, so I ' +
            'know every corner of this place. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que es ese sistema del monitor?',
              en: 'What is that system on the monitor?',
            },
            next: 'sys-1',
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
          es: 'Claro que hay mas. ¿Por donde seguimos?',
          en: 'Of course there is more. Where to next?',
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
              es: 'Cuentame de las otras sedes',
              en: 'Tell me about the other sites',
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
          es: 'Lo mejor para el final: el campo. ¿O ya te vas?',
          en: 'Saved the best for last: the field. Or are you leaving?',
        },
        options: [
          {
            label: {
              es: '¿Como es el trabajo en campo?',
              en: 'What is field work like?',
            },
            next: 'campo-1',
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
            'no le digas que hablo bien del pasante. Se pone raro.',
          en:
            'Take care out there. And if you see the veteran by the ' +
            'transformer, do not tell him he praises the intern. He gets ' +
            'weird about it.',
        },
        options: [
          {
            label: { es: 'Hasta luego', en: 'See you' },
            next: null,
          },
        ],
      },

      'sys-1': {
        text: {
          es:
            '¿Ves esa tabla en el monitor? Es el inventario de activos ' +
            'electricos. Lo construyo un pasante en 2013, con PHP y ' +
            'jQuery. Nada lujoso, pero nos cambio la vida.',
          en:
            'See that table on the monitor? That is the electrical asset ' +
            'inventory. An intern built it in 2013, with PHP and jQuery. ' +
            'Nothing fancy, but it changed our lives.',
        },
        options: [
          {
            label: {
              es: '¿Como era antes del sistema?',
              en: 'What was it like before?',
            },
            next: 'sys-2',
          },
          {
            label: {
              es: '¿Un pasante lo hizo solo?',
              en: 'An intern built it alone?',
            },
            next: 'sys-alt',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-2': {
        text: {
          es:
            'Planillas de papel. Y no una copia: TRES, una por sede. ' +
            'Buscar un equipo era revisar carpeta por carpeta. Mas de ' +
            'veinte minutos, si tenias suerte.',
          en:
            'Paper spreadsheets. And not one copy: THREE, one per site. ' +
            'Finding a piece of equipment meant going folder by folder. ' +
            'Twenty plus minutes, if you were lucky.',
        },
        options: [
          {
            label: {
              es: '¿Veinte minutos por un equipo?',
              en: 'Twenty minutes for one item?',
            },
            next: 'sys-3',
          },
          {
            label: {
              es: '¿Y con el sistema, cuanto?',
              en: 'And with the system, how long?',
            },
            next: 'sys-4',
          },
        ],
      },
      'sys-3': {
        text: {
          es:
            'Minimo. Y si el papel estaba en otra sede, olvidalo: llamada, ' +
            'espera, que alguien busque alla... Un repuesto podia estar a ' +
            'una hora de camino y nadie lo sabia.',
          en:
            'At least. And if the paper was at another site, forget it: a ' +
            'phone call, waiting, someone searching over there... A spare ' +
            'could sit an hour away and nobody knew.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora como funciona?',
              en: 'And how does it work now?',
            },
            next: 'sys-4',
          },
          {
            label: { es: 'Que desastre', en: 'What a mess' },
            next: 'sys-3b',
          },
        ],
      },
      'sys-3b': {
        text: {
          es:
            'Lo era. Y lo peor: las tres copias nunca coincidian. Cada ' +
            'sede anotaba lo suyo y el papel no viaja solo. Duplicado no ' +
            'es respaldo, es confusion por triplicado.',
          en:
            'It was. Worst part: the three copies never matched. Each site ' +
            'logged its own and paper does not travel by itself. Duplicated ' +
            'is not backup, it is confusion in triplicate.',
        },
        options: [
          {
            label: {
              es: '¿Y el sistema arreglo eso?',
              en: 'Did the system fix that?',
            },
            next: 'sys-4',
          },
        ],
      },
      'sys-4': {
        text: {
          es:
            'Ahora escribes el activo, enter, y ahi esta: que es, donde ' +
            'esta, en que sede. Localizacion inmediata. De veinte minutos ' +
            'a un parpadeo. Yo lo uso en cada ronda.',
          en:
            'Now you type the asset, hit enter, and there it is: what it ' +
            'is, where it sits, at which site. Instant lookup. From twenty ' +
            'minutes to a blink. I use it every round.',
        },
        options: [
          {
            label: {
              es: '¿Que dijo el personal al verlo?',
              en: 'How did the staff react?',
            },
            next: 'sys-5',
          },
          {
            label: {
              es: '¿Con que estaba hecho?',
              en: 'What was it built with?',
            },
            next: 'sys-6',
          },
        ],
      },
      'sys-5': {
        text: {
          es:
            'Primero desconfianza, como con todo lo nuevo. Pero el pasante ' +
            'no lo diseño desde un escritorio: vino aqui, al campo, a ' +
            'preguntarnos como trabajamos. Eso se noto en el resultado.',
          en:
            'Distrust at first, like with anything new. But the intern did ' +
            'not design it from a desk: he came here, to the field, and ' +
            'asked us how we work. You could tell in the result.',
        },
        options: [
          {
            label: {
              es: '¿Como levanto los requerimientos?',
              en: 'How did he gather requirements?',
            },
            next: 'campo-2',
          },
          {
            label: {
              es: '¿Y todos terminaron usandolo?',
              en: 'And everyone ended up using it?',
            },
            next: 'sys-5b',
          },
        ],
      },
      'sys-5b': {
        text: {
          es:
            'Todos. Porque lo mejor no es la velocidad: es que las tres ' +
            'sedes por fin ven lo mismo. Una sola verdad en vez de tres ' +
            'papeles peleados entre si.',
          en:
            'Everyone. Because the best part is not the speed: it is that ' +
            'all three sites finally see the same thing. One truth instead ' +
            'of three quarreling papers.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de esas sedes',
              en: 'Tell me about those sites',
            },
            next: 'sedes-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-6': {
        text: {
          es:
            'PHP para el servidor y jQuery para la pantalla. Herramientas ' +
            'de la epoca, simples y confiables. Aqui no necesitabamos ' +
            'magia: necesitabamos encontrar las cosas.',
          en:
            'PHP on the server and jQuery for the screen. Tools of the ' +
            'time, simple and reliable. We did not need magic here: we ' +
            'needed to find our things.',
        },
        options: [
          {
            label: {
              es: '¿Simple fue mejor entonces?',
              en: 'So simple was better?',
            },
            next: 'sys-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-7': {
        text: {
          es:
            'Para nosotros, si. Lo importante era que aguantara nuestra ' +
            'realidad: red que se cae, tres sedes, gente con guantes y ' +
            'poco tiempo. Y eso lo aguanto desde el primer dia.',
          en:
            'For us, yes. What mattered was surviving our reality: a ' +
            'network that drops, three sites, people wearing gloves with ' +
            'little time. And it survived it from day one.',
        },
        options: [
          {
            label: {
              es: '¿Tu como lo usas en la ronda?',
              en: 'How do you use it on rounds?',
            },
            next: 'sys-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-8': {
        text: {
          es:
            'Antes de salir reviso la tabla: que hay en el almacen, que ' +
            'se movio, que falta. Llego a cada punto sabiendo que voy a ' +
            'encontrar. La ronda rinde el doble.',
          en:
            'Before heading out I check the table: what is in the ' +
            'warehouse, what moved, what is missing. I reach each stop ' +
            'knowing what to expect. Rounds are twice as productive.',
        },
        options: [
          {
            label: {
              es: '¿Que muestra la tabla?',
              en: 'What does the table show?',
            },
            next: 'sys-9',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-9': {
        text: {
          es:
            'Cada activo con su sede y su ubicacion. Y arriba, ese ' +
            'indicador que va de OFFLINE a ONLINE. La primera vez que lo ' +
            'vi pense que estaba roto. Era al reves: era la gracia.',
          en:
            'Every asset with its site and location. And on top, that ' +
            'badge flipping from OFFLINE to ONLINE. First time I saw it I ' +
            'thought it was broken. Quite the opposite: it was the trick.',
        },
        options: [
          {
            label: {
              es: '¿Por que es la gracia?',
              en: 'Why is it the trick?',
            },
            next: 'off-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sys-alt': {
        text: {
          es:
            'Solo, si. Pasante de 2013. Aqui muchos esperaban que viniera ' +
            'una empresa grande con algo carisimo. Vino un muchacho con ' +
            'preguntas y un cuaderno.',
          en:
            'Alone, yes. A 2013 intern. Many here expected some big ' +
            'company with something pricey. Instead came a young guy with ' +
            'questions and a notebook.',
        },
        options: [
          {
            label: {
              es: '¿Y como salio tan bien?',
              en: 'How did it turn out so well?',
            },
            next: 'sys-5',
          },
          {
            label: {
              es: '¿Que problema resolvia?',
              en: 'What problem did it solve?',
            },
            next: 'sys-2',
          },
        ],
      },

      'off-1': {
        text: {
          es:
            'Buen ojo. Ese OFFLINE que se vuelve ONLINE no es un error: ' +
            'es la funcion estrella. Aqui la conectividad va y viene, ' +
            'sobre todo en las sedes mas alejadas.',
          en:
            'Good eye. That OFFLINE flipping to ONLINE is not an error: ' +
            'it is the star feature. Connectivity here comes and goes, ' +
            'especially at the more remote sites.',
        },
        options: [
          {
            label: {
              es: '¿El sistema funciona sin red?',
              en: 'The system works without network?',
            },
            next: 'off-2',
          },
          {
            label: {
              es: '¿Tan mala era la conexion?',
              en: 'Was the connection that bad?',
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
            'Exacto. Si se cae la red, tu sigues registrando activos como ' +
            'si nada. Cuando vuelve la conexion, el sistema sincroniza ' +
            'solo lo pendiente. Nadie pierde trabajo.',
          en:
            'Exactly. If the network drops, you keep logging assets like ' +
            'nothing happened. When the connection returns, the system ' +
            'syncs the pending work by itself. Nothing gets lost.',
        },
        options: [
          {
            label: {
              es: '¿Y donde termina todo eso?',
              en: 'And where does it all end up?',
            },
            next: 'off-4',
          },
          {
            label: {
              es: '¿Lo viste fallar alguna vez?',
              en: 'Ever seen it fail?',
            },
            next: 'off-6',
          },
        ],
      },
      'off-3': {
        text: {
          es:
            'La red aqui es intermitente, y en 2013 mas todavia. Un ' +
            'sistema que solo sirviera con internet habria muerto la ' +
            'primera semana. El pasante lo entendio porque pregunto antes.',
          en:
            'The network here is intermittent, and in 2013 even more so. ' +
            'A system that only worked online would have died its first ' +
            'week. The intern got it because he asked first.',
        },
        options: [
          {
            label: {
              es: '¿Como registran sin conexion?',
              en: 'How do you log while offline?',
            },
            next: 'off-2',
          },
          {
            label: {
              es: '¿Eso fue clave para adoptarlo?',
              en: 'Was that key to adoption?',
            },
            next: 'off-5',
          },
        ],
      },
      'off-4': {
        text: {
          es:
            'Al sincronizar, todo cae a la base de datos comun de las ' +
            'tres sedes. Ese es el punto: una sola fuente. Los papeles de ' +
            'antes jamas se ponian de acuerdo; la base si.',
          en:
            'On sync, everything lands in the shared database of the ' +
            'three sites. That is the point: a single source. The old ' +
            'papers never agreed with each other; the database does.',
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
            'Total. Si la primera vez que se cayo la red el sistema se ' +
            'hubiera trabado, nadie lo usaba mas. En cambio siguio ' +
            'andando y la gente dijo: esto entiende como es aqui.',
          en:
            'Absolutely. If the system had frozen the first time the ' +
            'network dropped, nobody would touch it again. Instead it ' +
            'kept going and people said: this thing gets how it is here.',
        },
        options: [
          {
            label: {
              es: '¿Y la sincronizacion posterior?',
              en: 'And the later sync?',
            },
            next: 'off-4',
          },
          {
            label: {
              es: '¿Volverian al papel?',
              en: 'Would you go back to paper?',
            },
            next: 'off-8',
          },
        ],
      },
      'off-6': {
        text: {
          es:
            'Fallar, no. Una tarde entera nos quedamos sin red en plena ' +
            'recepcion de equipos. Seguimos registrando tranquilos y en ' +
            'la noche, cuando volvio la señal, subio todo solo.',
          en:
            'Fail, no. One whole afternoon we lost the network right in ' +
            'the middle of receiving equipment. We kept logging calmly ' +
            'and at night, when the signal returned, it all went up alone.',
        },
        options: [
          {
            label: {
              es: '¿Subio todo sin perder nada?',
              en: 'Everything synced, nothing lost?',
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
            'Todo. Lo pendiente espera su turno y se sube cuando hay ' +
            'conexion. Al dia siguiente las otras sedes ya veian lo que ' +
            'registramos a oscuras. Como si nada hubiera pasado.',
          en:
            'Everything. Pending work waits its turn and goes up when ' +
            'there is a connection. Next day the other sites already saw ' +
            'what we logged in the dark. As if nothing had happened.',
        },
        options: [
          {
            label: {
              es: '¿Las sedes ven todo al instante?',
              en: 'Sites see everything instantly?',
            },
            next: 'sedes-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'off-8': {
        text: {
          es:
            '¿Al papel? Ni loca. Seria como devolver la luz electrica y ' +
            'volver a las velas. Hay cosas que, una vez que funcionan, ya ' +
            'no se negocian.',
          en:
            'To paper? No way. It would be like returning electric light ' +
            'and going back to candles. Some things, once they work, are ' +
            'no longer negotiable.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },

      'sedes-1': {
        text: {
          es:
            'Somos tres sedes: Yaracuy, Carabobo y Lara. Antes cada una ' +
            'era una isla con sus propias planillas de papel. Tres islas, ' +
            'tres verdades distintas sobre los mismos equipos.',
          en:
            'We are three sites: Yaracuy, Carabobo and Lara. Each used to ' +
            'be an island with its own paper spreadsheets. Three islands, ' +
            'three different truths about the same equipment.',
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
              es: '¿Que problemas causaba eso?',
              en: 'What problems did that cause?',
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
            'equipo nuevo, Yaracuy y Carabobo lo ven. Puedo saber desde ' +
            'aqui que hay en el almacen de otra sede sin llamar.',
          en:
            'One shared database for all three. If Lara logs a new unit, ' +
            'Yaracuy and Carabobo see it. From here I can know what sits ' +
            'in another site warehouse without a phone call.',
        },
        options: [
          {
            label: {
              es: '¿Aunque una sede este sin red?',
              en: 'Even if a site is offline?',
            },
            next: 'off-2',
          },
          {
            label: {
              es: '¿Eso ahorra traslados?',
              en: 'Does that save trips?',
            },
            next: 'sedes-4',
          },
        ],
      },
      'sedes-3': {
        text: {
          es:
            'Pedias un repuesto que tu sede no tenia y era una odisea. A ' +
            'veces hasta se compraba algo que ya existia guardado en otra ' +
            'sede, porque nadie podia saberlo.',
          en:
            'You needed a spare your site did not have and it was an ' +
            'odyssey. Sometimes we even bought things another site ' +
            'already had in storage, because nobody could know.',
        },
        options: [
          {
            label: {
              es: '¿Compraban duplicado?',
              en: 'You bought duplicates?',
            },
            next: 'sedes-3b',
          },
          {
            label: {
              es: '¿Como era pedir a otra sede?',
              en: 'How was asking another site?',
            },
            next: 'sedes-6',
          },
        ],
      },
      'sedes-3b': {
        text: {
          es:
            'Pasaba. Si nadie sabia que Carabobo tenia el equipo ' +
            'guardado, se pedia otro. Con la base comun eso se acabo: ' +
            'primero miras la tabla, despues decides.',
          en:
            'It happened. If nobody knew Carabobo had the unit in ' +
            'storage, another one got ordered. With the shared database ' +
            'that ended: first you check the table, then you decide.',
        },
        options: [
          {
            label: {
              es: '¿Y los traslados entre sedes?',
              en: 'And the trips between sites?',
            },
            next: 'sedes-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'sedes-4': {
        text: {
          es:
            'Muchisimos menos. Antes viajabas a otra sede "a ver que ' +
            'hay". Ahora viajas solo cuando la tabla dice que el equipo ' +
            'esta ahi. El camion sale con destino, no con esperanza.',
          en:
            'Far fewer. You used to drive to another site just to see ' +
            'what was there. Now you only go when the table says the unit ' +
            'is there. The truck leaves with a destination, not with hope.',
        },
        options: [
          {
            label: {
              es: 'Buena frase: destino, no esperanza',
              en: 'Nice line: destination, not hope',
            },
            next: 'sedes-5',
          },
          {
            label: {
              es: '¿Que es lo que mas valoras tu?',
              en: 'What do you value the most?',
            },
            next: 'sedes-7',
          },
        ],
      },
      'sedes-5': {
        text: {
          es:
            'Me la dijo un chofer, no es mia. Pero resume bien lo que ' +
            'cambio: menos vueltas, menos llamadas, mas certeza. Y todo ' +
            'empezo con un pasante preguntando por que tardabamos tanto.',
          en:
            'A driver said it, not me. But it sums up what changed: fewer ' +
            'detours, fewer calls, more certainty. And it all started ' +
            'with an intern asking why we took so long.',
        },
        options: [
          {
            label: {
              es: '¿Como fue ese trabajo en campo?',
              en: 'How was that field work?',
            },
            next: 'campo-2',
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
            'Un ritual: llamabas, alla alguien dejaba lo que hacia para ' +
            'revisar carpetas, y te devolvian la llamada... con suerte el ' +
            'mismo dia. Hoy esa respuesta tarda lo que tarda un enter.',
          en:
            'A ritual: you called, someone there dropped their work to ' +
            'dig through folders, and they called you back... same day if ' +
            'lucky. Today that answer takes as long as pressing enter.',
        },
        options: [
          {
            label: {
              es: '¿La base comun mato el ritual?',
              en: 'The shared DB killed the ritual?',
            },
            next: 'sedes-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },
      'sedes-7': {
        text: {
          es:
            'La tranquilidad. Saber donde esta cada cosa sin depender de ' +
            'la memoria de nadie ni del papel de nadie. La informacion ' +
            'dejo de vivir en cabezas y carpetas.',
          en:
            'The peace of mind. Knowing where everything is without ' +
            'depending on anyone memory or anyone paper. Information ' +
            'stopped living in heads and folders.',
        },
        options: [
          {
            label: {
              es: '¿Y en el dia a dia del campo?',
              en: 'And in day-to-day field work?',
            },
            next: 'campo-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub2',
          },
        ],
      },

      'campo-1': {
        text: {
          es:
            'El campo es lo mio. Subestacion, tablero de medidores, ' +
            'almacen. Y regla numero uno: casco puesto siempre. Aqui hay ' +
            'alta tension de verdad, no de la de las peliculas.',
          en:
            'The field is my thing. Substation, meter panel, warehouse. ' +
            'Rule number one: helmet on, always. This is real high ' +
            'voltage, not the movie kind.',
        },
        options: [
          {
            label: {
              es: '¿El pasante tambien uso casco?',
              en: 'Did the intern wear a helmet too?',
            },
            next: 'campo-2',
          },
          {
            label: {
              es: '¿Como es la seguridad aqui?',
              en: 'How does safety work here?',
            },
            next: 'campo-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-2': {
        text: {
          es:
            'Casco amarillo como todos. Levanto los requerimientos aqui ' +
            'mismo, con el personal operativo: nos seguia en la ronda, ' +
            'preguntaba como buscabamos un equipo y anotaba todo.',
          en:
            'Yellow helmet like everyone. He gathered requirements right ' +
            'here, with the operations staff: he followed our rounds, ' +
            'asked how we searched for equipment and wrote it all down.',
        },
        options: [
          {
            label: {
              es: '¿Eso mejoro el sistema?',
              en: 'Did that improve the system?',
            },
            next: 'campo-4',
          },
          {
            label: {
              es: '¿Que preguntaba exactamente?',
              en: 'What did he ask exactly?',
            },
            next: 'campo-5',
          },
        ],
      },
      'campo-3': {
        text: {
          es:
            'Orgullo, sobre todo. Esta planta alumbra hogares que no ' +
            'conocemos. Cuando el tablero esta en verde y las torres ' +
            'zumban parejo, sabes que hiciste bien tu trabajo.',
          en:
            'Pride, mostly. This plant lights homes we will never see. ' +
            'When the panel is green and the towers hum steady, you know ' +
            'you did your job right.',
        },
        options: [
          {
            label: {
              es: 'Se nota que amas la planta',
              en: 'You clearly love this plant',
            },
            next: 'campo-3b',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-3b': {
        text: {
          es:
            'Por eso me gusto que el sistema naciera aqui adentro y no ' +
            'en una oficina lejana. Las herramientas buenas huelen a ' +
            'campo.',
          en:
            'That is why I liked that the system was born in here and ' +
            'not in some faraway office. Good tools smell like the field.',
        },
        options: [
          {
            label: {
              es: '¿Como se hizo en el campo?',
              en: 'How was it built in the field?',
            },
            next: 'campo-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-4': {
        text: {
          es:
            'Muchisimo. Por escucharnos entendio que la red se cae, que ' +
            'el almacen se maneja por cajas, que buscar tardaba veinte ' +
            'minutos. Resolvio lo que vivimos, no lo que alguien imagino.',
          en:
            'A lot. By listening he learned the network drops, the ' +
            'warehouse runs on boxes, searches took twenty minutes. He ' +
            'solved what we live, not what someone imagined.',
        },
        options: [
          {
            label: {
              es: '¿Y el resultado final?',
              en: 'And the final result?',
            },
            next: 'sys-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-5': {
        text: {
          es:
            'Cosas simples: ¿donde anotas esto? ¿cuanto tardas en hallar ' +
            'aquello? ¿que pasa si no hay red? Preguntas de quien quiere ' +
            'entender antes de construir. Ojala todos empezaran asi.',
          en:
            'Simple things: where do you log this? how long to find ' +
            'that? what happens with no network? Questions from someone ' +
            'who understands before building. Wish everyone started so.',
        },
        options: [
          {
            label: {
              es: '¿Que salio de esas preguntas?',
              en: 'What came out of those questions?',
            },
            next: 'campo-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-6': {
        text: {
          es:
            'Casco obligatorio, distancias marcadas y nada de improvisar ' +
            'cerca del transformador. La subestacion se respeta. Por eso ' +
            'los cascos amarillos que ves colgados en la entrada.',
          en:
            'Mandatory helmet, marked distances and no improvising near ' +
            'the transformer. You respect the substation. That is why you ' +
            'see those yellow helmets hanging by the entrance.',
        },
        options: [
          {
            label: {
              es: '¿Y ese tablero de medidores?',
              en: 'And that meter board?',
            },
            next: 'campo-7',
          },
          {
            label: {
              es: '¿Que se siente trabajar aqui?',
              en: 'What is working here like?',
            },
            next: 'campo-3',
          },
        ],
      },
      'campo-7': {
        text: {
          es:
            'El tablero es el pulso de la planta: tension, carga, todo a ' +
            'la vista. En mi ronda lo leo primero. Verde parejo, dia ' +
            'tranquilo. Una aguja inquieta, y la ronda cambia de plan.',
          en:
            'The board is the plant pulse: voltage, load, all in sight. ' +
            'On my rounds I read it first. Steady green, calm day. One ' +
            'restless needle, and the round changes plans.',
        },
        options: [
          {
            label: {
              es: '¿Y las torres de la ventana?',
              en: 'And the towers out the window?',
            },
            next: 'campo-8',
          },
          {
            label: {
              es: '¿Que se siente trabajar aqui?',
              en: 'What is working here like?',
            },
            next: 'campo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
          },
        ],
      },
      'campo-8': {
        text: {
          es:
            'Alta tension saliendo a recorrer el pais. Cada torre que ves ' +
            'por esa ventana carga luz para miles de casas. Bonitas de ' +
            'lejos, respetables de cerca.',
          en:
            'High voltage heading out across the country. Every tower you ' +
            'see through that window carries light for thousands of ' +
            'homes. Pretty from afar, demanding respect up close.',
        },
        options: [
          {
            label: {
              es: '¿Que se siente trabajar aqui?',
              en: 'What is working here like?',
            },
            next: 'campo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub3',
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
        es: 'Mmm. Los bujes suenan bien hoy.',
        en: 'Hmm. The bushings sound fine today.',
      },
      {
        es: '¿Turista? Aqui no hay recuerditos.',
        en: 'Tourist? No souvenirs around here.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Cuidado por donde pisas. Yo vigilo este transformador desde ' +
            'antes de que tu supieras que existe la corriente alterna. ' +
            '¿Que buscas?',
          en:
            'Watch your step. I have watched this transformer since ' +
            'before you knew alternating current existed. What do you ' +
            'want?',
        },
        options: [
          {
            label: {
              es: 'Hableme del transformador',
              en: 'Tell me about the transformer',
            },
            next: 'trafo-1',
          },
          {
            label: {
              es: '¿Y ese pasante del que hablan?',
              en: 'What about that intern?',
            },
            next: 'pasante-1',
          },
          {
            label: { es: 'Nada, ya me voy', en: 'Nothing, I am leaving' },
            next: null,
          },
        ],
      },

      'trafo-1': {
        text: {
          es:
            'Esta belleza sube y baja tension como quien respira. Media ' +
            'planta depende de que este señor amanezca de buen humor. Y ' +
            'de que yo lo escuche.',
          en:
            'This beauty steps voltage up and down like breathing. Half ' +
            'the plant depends on this gentleman waking up in a good ' +
            'mood. And on me listening to him.',
        },
        options: [
          {
            label: {
              es: '¿Que son esos bujes de arriba?',
              en: 'What are those bushings on top?',
            },
            next: 'trafo-5',
          },
          {
            label: {
              es: '¿Y las torres de la ventana?',
              en: 'And the towers out the window?',
            },
            next: 'trafo-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'trafo-2': {
        text: {
          es:
            'Alta tension rumbo a medio pais. Cada torre que ves carga ' +
            'luz para miles de casas. Bonitas de lejos, respetables de ' +
            'cerca. Como yo.',
          en:
            'High voltage heading across half the country. Every tower ' +
            'you see carries light for thousands of homes. Pretty from ' +
            'afar, demanding respect up close. Like me.',
        },
        options: [
          {
            label: {
              es: 'Ja. ¿Y la seguridad aqui?',
              en: 'Ha. What about safety here?',
            },
            next: 'trafo-3',
          },
          {
            label: {
              es: '¿Por que tanto casco?',
              en: 'Why so much helmet talk?',
            },
            next: 'casco-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'trafo-3': {
        text: {
          es:
            'Peligroso es el descuido, no la planta. Por eso el casco es ' +
            'obligatorio y las distancias se respetan. Treinta años sin ' +
            'un susto grave. Mi record, no me lo arruines.',
          en:
            'Carelessness is dangerous, not the plant. That is why ' +
            'helmets are mandatory and distances are respected. Thirty ' +
            'years without a big scare. My record, do not ruin it.',
        },
        options: [
          {
            label: {
              es: 'Prometido. ¿Algo mas del trafo?',
              en: 'Promise. More about the trafo?',
            },
            next: 'trafo-4',
          },
          {
            label: {
              es: '¿Como sabe que esta sano?',
              en: 'How do you know it is healthy?',
            },
            next: 'trafo-6',
          },
        ],
      },
      'trafo-4': {
        text: {
          es:
            'Solo esto: una maquina se cuida sabiendo QUE tienes y DONDE ' +
            'esta. Repuestos, piezas, aceite. Antes eso era un misterio ' +
            'de papel. Ahora esta en la tabla esa del monitor.',
          en:
            'Just this: you care for a machine by knowing WHAT you have ' +
            'and WHERE it is. Spares, parts, oil. That used to be a paper ' +
            'mystery. Now it lives in that table on the monitor.',
        },
        options: [
          {
            label: {
              es: '¿La tabla del pasante?',
              en: 'The intern table?',
            },
            next: 'pasante-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'trafo-5': {
        text: {
          es:
            'Porcelana. Por los bujes entra y sale la corriente sin que ' +
            'el tanque haga corto. Los reviso cada mañana: una grieta ' +
            'ahi y el dia se pone interesante. Y no del modo bueno.',
          en:
            'Porcelain. Current passes through the bushings without ' +
            'shorting against the tank. I check them every morning: one ' +
            'crack there and the day gets interesting. Not the good kind.',
        },
        options: [
          {
            label: {
              es: '¿Es peligroso estar aqui?',
              en: 'Is it dangerous in here?',
            },
            next: 'trafo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'trafo-6': {
        text: {
          es:
            'Por el zumbido. Un transformador sano canta parejo, como un ' +
            'panal tranquilo. Cuando cambia la nota, algo pasa. Treinta ' +
            'años oyendo la misma cancion: me se cada estrofa.',
          en:
            'By the hum. A healthy transformer sings steady, like a calm ' +
            'beehive. When the note changes, something is up. Thirty ' +
            'years hearing the same song: I know every verse.',
        },
        options: [
          {
            label: {
              es: '¿Y el inventario ayuda en eso?',
              en: 'Does the inventory help there?',
            },
            next: 'trafo-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'casco-1': {
        text: {
          es:
            'Porque la cabeza no trae repuesto, muchacho. El casco ' +
            'amarillo es lo primero que te pones y lo ultimo que ' +
            'cuestionas. Hasta el pasante lo entendio al primer dia.',
          en:
            'Because heads do not come with spares, kid. The yellow ' +
            'helmet is the first thing you put on and the last thing you ' +
            'question. Even the intern got it on day one.',
        },
        options: [
          {
            label: {
              es: '¿Y el record de seguridad?',
              en: 'And the safety record?',
            },
            next: 'trafo-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },

      'pasante-1': {
        text: {
          es:
            'El pasante ese... Mira, yo desconfio de todo lo que tenga ' +
            'pantalla. Pero el muchacho vino, pregunto, escucho. Y su ' +
            'sistema funciona hasta cuando se cae la red. No es poca cosa.',
          en:
            'That intern... Look, I distrust anything with a screen. But ' +
            'the kid came, asked, listened. And his system works even ' +
            'when the network drops. That is no small thing.',
        },
        options: [
          {
            label: {
              es: '¿O sea que le tiene aprecio?',
              en: 'So you are fond of him?',
            },
            next: 'pasante-2',
          },
          {
            label: {
              es: '¿Que hizo en el almacen?',
              en: 'What did he do in the warehouse?',
            },
            next: 'pasante-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pasante-2': {
        text: {
          es:
            'Yo no dije eso. Dije que funciona. Es distinto. ...Bueno, ' +
            'esta bien: el muchacho resulto bueno. Pero si se lo cuentas ' +
            'a la de la ronda, lo niego todo.',
          en:
            'I did not say that. I said it works. Different thing. ' +
            '...Fine, alright: the kid turned out good. But if you tell ' +
            'the rounds tech, I will deny everything.',
        },
        options: [
          {
            label: {
              es: 'Secreto guardado. ¿Y el almacen?',
              en: 'Secret kept. The warehouse?',
            },
            next: 'pasante-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pasante-3': {
        text: {
          es:
            '¿Ves esas cajas etiquetadas? Obra suya. Etiqueto hasta la ' +
            'ultima caja del almacen para meterla al inventario. Caja ' +
            'por caja, con este calor.',
          en:
            'See those labeled boxes? His doing. He labeled every last ' +
            'box in the warehouse to load it into the inventory. Box by ' +
            'box, in this heat.',
        },
        options: [
          {
            label: {
              es: '¿Y eso para que sirvio?',
              en: 'And what was that good for?',
            },
            next: 'pasante-4',
          },
          {
            label: {
              es: '¿Usted penso que se rendiria?',
              en: 'Did you think he would quit?',
            },
            next: 'pasante-6',
          },
        ],
      },
      'pasante-4': {
        text: {
          es:
            'Para que la tabla no mienta. Un inventario vale lo que vale ' +
            'su peor etiqueta. Antes buscar algo era veinte minutos de ' +
            'papeleo; ahora la de la ronda lo halla antes de mi cafe.',
          en:
            'So the table does not lie. An inventory is worth its worst ' +
            'label. Finding something took twenty minutes of paperwork; ' +
            'now the rounds tech finds it before I finish my coffee.',
        },
        options: [
          {
            label: {
              es: 'Todo un elogio viniendo de usted',
              en: 'High praise coming from you',
            },
            next: 'pasante-5',
          },
          {
            label: {
              es: '¿Que le diria si volviera?',
              en: 'What would you tell him now?',
            },
            next: 'pasante-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pasante-5': {
        text: {
          es:
            'No te acostumbres. Elogio uno por decada y este ya se ' +
            'gasto. Ahora dejame trabajar, que el transformador se pone ' +
            'celoso.',
          en:
            'Do not get used to it. One compliment per decade and that ' +
            'one is spent. Now let me work, the transformer gets jealous.',
        },
        options: [
          {
            label: { es: 'Entendido. Hasta luego', en: 'Got it. See you' },
            next: null,
          },
          {
            label: { es: 'Una cosa mas...', en: 'One more thing...' },
            next: 'hub',
          },
        ],
      },
      'pasante-6': {
        text: {
          es:
            'Aposte a que se rendia en la tercera fila de cajas. Perdi. ' +
            'Termino todas, polvo incluido, y todavia tuvo animo de ' +
            'preguntarme por los bujes. Muchacho terco.',
          en:
            'I bet he would quit by the third row of boxes. I lost. He ' +
            'finished them all, dust included, and still had the energy ' +
            'to ask me about the bushings. Stubborn kid.',
        },
        options: [
          {
            label: {
              es: '¿Y para que sirvio tanta caja?',
              en: 'And what were the boxes for?',
            },
            next: 'pasante-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
      'pasante-7': {
        text: {
          es:
            'Que siga preguntando antes de construir. Es lo que lo hizo ' +
            'distinto: primero entendio el campo, despues escribio el ' +
            'codigo. En ese orden. Anda, ya te di suficiente.',
          en:
            'To keep asking before building. That is what set him apart: ' +
            'first he understood the field, then he wrote the code. In ' +
            'that order. Go on, I have given you enough.',
        },
        options: [
          {
            label: { es: 'Gracias. Adios', en: 'Thanks. Goodbye' },
            next: null,
          },
          {
            label: { es: 'Volvamos', en: 'Back' },
            next: 'hub',
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
