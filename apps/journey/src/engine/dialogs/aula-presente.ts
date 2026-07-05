/**
 * @module dialogs/aula-presente (engine)
 * @description Arboles de dialogo de la Sala 0 presente: aula/laboratorio
 *   universitario (~2015). Los tres NPCs recuerdan como Pablo colaboro con
 *   cada uno: la estudiante de ronda (una de los ~6 que Pablo capacito para
 *   sostener la red cliente-servidor del proyecto IAI), la tesista aliviada
 *   (su tesis fue una de las dos que Pablo reencamino en una semana) y el
 *   tesista de los sockets (Pablo le enseño C, el puerto 8080 y el primer
 *   pong en 2ms).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const AULA_PRESENTE_DIALOGS = {
  'estudiante-ronda': defineDialog({
    name: { es: 'Estudiante de ronda', en: 'Student on rounds' },
    chatter: [
      {
        es: 'Ping... pong. Pablo decia que era el latido del aula.',
        en: 'Ping... pong. Pablo called it the heartbeat of the room.',
      },
      {
        es: '¿Ya viste las pizarras de RETOS y APRENDIZAJES?',
        en: 'Have you seen the CHALLENGES and LESSONS boards?',
      },
      {
        es: 'Meses trabados... y Pablo los reencamino en una semana.',
        en: 'Months stuck... and Pablo turned it around in a week.',
      },
      {
        es: 'Este laboratorio es mi lugar favorito.',
        en: 'This lab is my favorite place.',
      },
      {
        es: 'Ronda numero doce del dia. Todo en orden.',
        en: 'Round twelve of the day. All in order.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¡Hola! Bienvenido al laboratorio. Yo soy una de los seis ' +
            'que Pablo capacito para sostener este sistema. Hago la ' +
            'ronda: reviso que cada PC responda. ¿Que te cuento?',
          en:
            'Hi! Welcome to the lab. I am one of the six students ' +
            'Pablo trained to sustain this system. I do the rounds: ' +
            'I check that every PC responds. What can I tell you?',
        },
        options: [
          {
            label: {
              es: 'Las dos tesis que Pablo rescato',
              en: 'The two theses Pablo rescued',
            },
            next: 'tesisIntro',
          },
          {
            label: {
              es: 'La red del laboratorio',
              en: 'The lab network',
            },
            next: 'redIntro',
          },
          {
            label: {
              es: '¿Que aprendiste de Pablo?',
              en: 'What did you learn from Pablo?',
            },
            next: 'aprenderIntro',
          },
          {
            label: {
              es: 'Me despido',
              en: 'I will head out',
            },
            next: null,
          },
        ],
      },
      tesisIntro: {
        text: {
          es:
            'Dos proyectos de grado llevaban meses bloqueados. Meses. ' +
            'Los tesistas venian, tecleaban, borraban... y el reloj ' +
            'corria hacia la fecha de grado. Hasta que llego Pablo.',
          en:
            'Two thesis projects were blocked for months. Months. The ' +
            'students came in, typed, deleted... and the clock kept ' +
            'running toward graduation day. Until Pablo arrived.',
        },
        options: [
          {
            label: {
              es: '¿Por que se trabaron?',
              en: 'Why did they get stuck?',
            },
            next: 'tesisCausa',
          },
          {
            label: {
              es: '¿Que hizo Pablo?',
              en: 'What did Pablo do?',
            },
            next: 'tesisAsesor',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      tesisCausa: {
        text: {
          es:
            'No era falta de esfuerzo. Era falta de rumbo: sin un ' +
            'diagnostico claro, cada semana cavaban mas hondo en la ' +
            'misma zanja.',
          en:
            'It was not lack of effort. It was lack of direction: with ' +
            'no clear diagnosis, every week they dug deeper into the ' +
            'same ditch.',
        },
        options: [
          {
            label: {
              es: '¿Como se sentian?',
              en: 'How did they feel?',
            },
            next: 'tesisMiedo',
          },
          {
            label: {
              es: '¿Nadie los guiaba?',
              en: 'Was nobody guiding them?',
            },
            next: 'tesisAntes',
          },
        ],
      },
      tesisMiedo: {
        text: {
          es:
            'Habia miedo de verdad: sin tesis no hay grado. La tesista ' +
            'de alla casi no dormia. Preguntale por Pablo: hoy lo ' +
            'cuenta sonriendo.',
          en:
            'There was real fear: no thesis, no degree. The student ' +
            'over there barely slept. Ask her about Pablo: today she ' +
            'tells it with a smile.',
        },
        options: [
          {
            label: {
              es: '¿Y nadie los guiaba?',
              en: 'And nobody guided them?',
            },
            next: 'tesisAntes',
          },
          {
            label: {
              es: '¿Que hizo Pablo?',
              en: 'What did Pablo do?',
            },
            next: 'tesisAsesor',
          },
        ],
      },
      tesisAntes: {
        text: {
          es:
            'Trabajaban duro, pero sin plan. Y el esfuerzo sin plan es ' +
            'como un programa sin main: mucho codigo y nada arranca.',
          en:
            'They worked hard, but with no plan. And effort without a ' +
            'plan is like a program without a main: lots of code and ' +
            'nothing starts.',
        },
        options: [
          {
            label: {
              es: '¿Y que hizo Pablo?',
              en: 'And what did Pablo do?',
            },
            next: 'tesisAsesor',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      tesisAsesor: {
        text: {
          es:
            'En 2015 llego Pablo como asesor de proyectos de grado, ' +
            'con el proyecto academico IAI bajo el brazo. No toco nada ' +
            'al llegar: pregunto, leyo y escucho.',
          en:
            'In 2015 Pablo arrived as thesis advisor, with the IAI ' +
            'academic project under his arm. He touched nothing on ' +
            'arrival: he asked, read and listened.',
        },
        options: [
          {
            label: {
              es: '¿Que hizo el primer dia?',
              en: 'What did he do on day one?',
            },
            next: 'tesisDia1',
          },
          {
            label: {
              es: '¿Y el diagnostico?',
              en: 'And the diagnosis?',
            },
            next: 'tesisDiagnostico',
          },
        ],
      },
      tesisDia1: {
        text: {
          es:
            'El primer dia Pablo solo escucho y leyo todo lo que ' +
            'habia: borradores, notas, codigo. Decia que opinar antes ' +
            'de entender sale caro.',
          en:
            'On day one Pablo only listened and read everything there ' +
            'was: drafts, notes, code. He said giving opinions before ' +
            'understanding is expensive.',
        },
        options: [
          {
            label: {
              es: '¿Y que encontro?',
              en: 'And what did he find?',
            },
            next: 'tesisDiagnostico',
          },
          {
            label: {
              es: 'Sabia decision',
              en: 'Wise call',
            },
            next: 'hub',
          },
        ],
      },
      tesisDiagnostico: {
        text: {
          es:
            'El diagnostico de Pablo fue directo: no faltaba ' +
            'capacidad, faltaba foco. Demasiados frentes abiertos y ' +
            'ninguna meta medible.',
          en:
            'The diagnosis from Pablo was direct: ability was not ' +
            'missing, focus was. Too many open fronts and not a ' +
            'single measurable goal.',
        },
        options: [
          {
            label: {
              es: '¿Y el plan?',
              en: 'And the plan?',
            },
            next: 'tesisPlan',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      tesisPlan: {
        text: {
          es:
            'Del diagnostico Pablo saco un plan de rescate: recortar ' +
            'cada tesis a su nucleo, ordenar los pasos y ponerles ' +
            'entregas claras.',
          en:
            'From the diagnosis Pablo built a rescue plan: cut each ' +
            'thesis down to its core, order the steps and set clear ' +
            'deliverables.',
        },
        options: [
          {
            label: {
              es: '¿Entregas claras?',
              en: 'Clear deliverables?',
            },
            next: 'tesisEntregas',
          },
          {
            label: {
              es: '¿Funciono?',
              en: 'Did it work?',
            },
            next: 'tesisSemana',
          },
        ],
      },
      tesisEntregas: {
        text: {
          es:
            'Cada dia tenia una meta chica y medible. Nada de "avanzar ' +
            'en la tesis": era "hoy cierro este capitulo" o "hoy corre ' +
            'esta prueba".',
          en:
            'Each day had a small, measurable goal. No "make progress ' +
            'on the thesis": it was "close this chapter today" or "run ' +
            'this test today".',
        },
        options: [
          {
            label: {
              es: '¿Y funciono?',
              en: 'And did it work?',
            },
            next: 'tesisSemana',
          },
          {
            label: {
              es: '¿Las dos tesis por igual?',
              en: 'Both theses alike?',
            },
            next: 'tesisAmbas',
          },
        ],
      },
      tesisAmbas: {
        text: {
          es:
            'Eran dos tesis distintas, pero el problema era el mismo: ' +
            'la falta de plan. El mismo metodo de Pablo las reencamino ' +
            'a las dos.',
          en:
            'They were two different theses, but the problem was the ' +
            'same: no plan. The same method from Pablo got both back ' +
            'on track.',
        },
        options: [
          {
            label: {
              es: '¿En cuanto tiempo?',
              en: 'How long did it take?',
            },
            next: 'tesisSemana',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      tesisSemana: {
        text: {
          es:
            'En mas o menos una semana por tesis, Pablo las dejo ' +
            'reencaminadas. Una semana contra meses de bloqueo. No fue ' +
            'magia: fue metodo.',
          en:
            'In about one week each, Pablo had them back on track. ' +
            'One week against months of blockage. It was not magic: ' +
            'it was method.',
        },
        options: [
          {
            label: {
              es: '¿Cual era el secreto?',
              en: 'What was the secret?',
            },
            next: 'tesisSecreto',
          },
          {
            label: {
              es: '¿Como lo celebraron?',
              en: 'How did you celebrate?',
            },
            next: 'tesisCelebrar',
          },
          {
            label: {
              es: '¿Y los tesistas hoy?',
              en: 'And the students today?',
            },
            next: 'tesisHoy',
          },
        ],
      },
      tesisCelebrar: {
        text: {
          es:
            '¡Quedo en la pizarra! El dia que las dos tesis volvieron ' +
            'a moverse, alguien escribio APRENDIZAJES en mayusculas ' +
            'gigantes.',
          en:
            'It went on the board! The day both theses moved again, ' +
            'someone wrote LESSONS in giant capital letters.',
        },
        options: [
          {
            label: {
              es: '¿Y los tesistas hoy?',
              en: 'And the students today?',
            },
            next: 'tesisHoy',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      tesisSecreto: {
        text: {
          es:
            'Dos habitos de Pablo: diagnosticar antes de tocar nada y ' +
            'documentar cada decision. Suena simple. Lo dificil es ' +
            'hacerlo siempre.',
          en:
            'Two habits from Pablo: diagnose before touching anything ' +
            'and document every decision. It sounds simple. The hard ' +
            'part is doing it always.',
        },
        options: [
          {
            label: {
              es: '¿Y los tesistas hoy?',
              en: 'And the students today?',
            },
            next: 'tesisHoy',
          },
          {
            label: {
              es: 'Buena historia',
              en: 'Good story',
            },
            next: 'hub',
          },
        ],
      },
      tesisHoy: {
        text: {
          es:
            'Ahi los tienes, tecleando. Ella por fin compila y celebra ' +
            'cada paso. El te recita el servidor de sockets que armo ' +
            'con Pablo sin respirar.',
          en:
            'There they are, typing. She finally compiles and ' +
            'celebrates every step. He recites the socket server he ' +
            'built with Pablo without taking a breath.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste tu?',
              en: 'What did you learn?',
            },
            next: 'tesisLeccion',
          },
          {
            label: {
              es: 'Ire a hablarles',
              en: 'I will go talk to them',
            },
            next: 'hub',
          },
        ],
      },
      tesisLeccion: {
        text: {
          es:
            'Que estar meses trabado no es falta de talento: es falta ' +
            'de plan. Una semana bien guiada vale mas que un semestre ' +
            'a ciegas. Eso me lo mostro Pablo.',
          en:
            'That being stuck for months is not lack of talent: it is ' +
            'lack of a plan. One well-guided week beats a blind ' +
            'semester. Pablo showed me that.',
        },
        options: [
          {
            label: {
              es: 'Gran leccion',
              en: 'Great lesson',
            },
            next: 'hub',
          },
          {
            label: {
              es: '¿Que mas te enseño Pablo?',
              en: 'What else did Pablo teach?',
            },
            next: 'aprenderIntro',
          },
        ],
      },
      redIntro: {
        text: {
          es:
            'Cada pupitre tiene una PC conectada a la red local del ' +
            'aula. Es la arquitectura cliente-servidor que diseño ' +
            'Pablo para el proyecto IAI.',
          en:
            'Every desk has a PC connected to the local network of ' +
            'the room. It is the client-server architecture Pablo ' +
            'designed for the IAI project.',
        },
        options: [
          {
            label: {
              es: '¿Para que sirve?',
              en: 'What is it for?',
            },
            next: 'redUso',
          },
          {
            label: {
              es: '¿Como funciona por dentro?',
              en: 'How does it work inside?',
            },
            next: 'redSocket',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      redUso: {
        text: {
          es:
            'Soporta un sistema de gestion de obras: los clientes ' +
            'consultan y registran, y el servidor coordina todo sobre ' +
            'la red local.',
          en:
            'It supports a construction works management system: ' +
            'clients query and record, and the server coordinates it ' +
            'all over the LAN.',
        },
        options: [
          {
            label: {
              es: '¿Gestion de obras?',
              en: 'Works management?',
            },
            next: 'redObras',
          },
          {
            label: {
              es: '¿Quien la diseño?',
              en: 'Who designed it?',
            },
            next: 'redDiseno',
          },
        ],
      },
      redObras: {
        text: {
          es:
            'Obras de construccion: avances, materiales, responsables. ' +
            'Antes era papel y memoria; ahora todo entra ordenado por ' +
            'el servidor.',
          en:
            'Construction works: progress, materials, people in ' +
            'charge. It used to be paper and memory; now it all enters ' +
            'ordered through the server.',
        },
        options: [
          {
            label: {
              es: '¿Quien diseño esto?',
              en: 'Who designed this?',
            },
            next: 'redDiseno',
          },
          {
            label: {
              es: '¿Y por dentro?',
              en: 'And under the hood?',
            },
            next: 'redSocket',
          },
        ],
      },
      redDiseno: {
        text: {
          es:
            'Pablo. Separar cliente y servidor sobre la red local hizo ' +
            'el sistema mas claro: cada parte con su responsabilidad.',
          en:
            'Pablo did. Splitting client and server over the local ' +
            'network made the system clearer: each part with its own ' +
            'responsibility.',
        },
        options: [
          {
            label: {
              es: '¿Por que cliente-servidor?',
              en: 'Why client-server?',
            },
            next: 'redPorque',
          },
          {
            label: {
              es: '¿Y por dentro?',
              en: 'And under the hood?',
            },
            next: 'redSocket',
          },
        ],
      },
      redPorque: {
        text: {
          es:
            'Un servidor que coordina y muchos clientes que consultan. ' +
            'Una sola fuente de verdad y menos caos. Y en red local, ' +
            'vuela.',
          en:
            'One server that coordinates and many clients that query. ' +
            'A single source of truth and less chaos. And on a LAN, it ' +
            'flies.',
        },
        options: [
          {
            label: {
              es: '¿Como se conectan?',
              en: 'How do they connect?',
            },
            next: 'redSocket',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      redSocket: {
        text: {
          es:
            'Cada PC corre servidor.c, un servidor de sockets escrito ' +
            'en C. Hace bind al puerto 8080, listen, y se queda ' +
            'esperando conexiones.',
          en:
            'Every PC runs servidor.c, a socket server written in C. ' +
            'It binds to port 8080, listens, and stays there waiting ' +
            'for connections.',
        },
        options: [
          {
            label: {
              es: '¿Por que en C?',
              en: 'Why in C?',
            },
            next: 'redC',
          },
          {
            label: {
              es: '¿Y que responde?',
              en: 'And what does it answer?',
            },
            next: 'redPingpong',
          },
        ],
      },
      redC: {
        text: {
          es:
            'Pablo lo decia siempre: C no esconde nada. Si entiendes ' +
            'bind, listen y accept a mano, entiendes lo que corre ' +
            'debajo de todo lo demas.',
          en:
            'Pablo always said it: C hides nothing. If you understand ' +
            'bind, listen and accept by hand, you understand what runs ' +
            'under everything else.',
        },
        options: [
          {
            label: {
              es: '¿Y que responde el servidor?',
              en: 'And what does the server say?',
            },
            next: 'redPingpong',
          },
          {
            label: {
              es: 'Respeto',
              en: 'Respect',
            },
            next: 'hub',
          },
        ],
      },
      redPingpong: {
        text: {
          es:
            'El cliente manda "ping" y el servidor responde "pong" en ' +
            'dos milisegundos. Simple, medible y vivo.',
          en:
            'The client sends "ping" and the server answers "pong" in ' +
            'two milliseconds. Simple, measurable and alive.',
        },
        options: [
          {
            label: {
              es: '¿Solo ping y pong?',
              en: 'Just ping and pong?',
            },
            next: 'redSimple',
          },
          {
            label: {
              es: '¿2ms es bueno?',
              en: 'Is 2ms good?',
            },
            next: 'red2ms',
          },
        ],
      },
      redSimple: {
        text: {
          es:
            'Es la prueba de vida de la red. Si el ping-pong responde, ' +
            'la base funciona; sobre eso se construye todo lo demas.',
          en:
            'It is the heartbeat of the network. If the ping-pong ' +
            'answers, the foundation works; everything else is built ' +
            'on top.',
        },
        options: [
          {
            label: {
              es: '¿Y los dos milisegundos?',
              en: 'And the two milliseconds?',
            },
            next: 'red2ms',
          },
          {
            label: {
              es: 'Tiene sentido',
              en: 'Makes sense',
            },
            next: 'hub',
          },
        ],
      },
      red2ms: {
        text: {
          es:
            'En red local, 2ms es un latido sano. Lo medimos siempre; ' +
            'Pablo repetia que lo que no se mide no se puede ' +
            'diagnosticar.',
          en:
            'On a local network, 2ms is a healthy heartbeat. We ' +
            'always measure it; Pablo repeated that what is not ' +
            'measured cannot be diagnosed.',
        },
        options: [
          {
            label: {
              es: '¿Y si algo falla?',
              en: 'What if something fails?',
            },
            next: 'redFalla',
          },
          {
            label: {
              es: '¿Quien mantiene esto?',
              en: 'Who maintains this?',
            },
            next: 'redMantener',
          },
        ],
      },
      redFalla: {
        text: {
          es:
            'Diagnostico, no panico. Asi nos entreno Pablo: ¿responde ' +
            'el puerto 8080? ¿corre el proceso? ¿esta el cable? Se ' +
            'revisa en orden y se anota lo encontrado.',
          en:
            'Diagnosis, not panic. That is how Pablo trained us: does ' +
            'port 8080 answer? Is the process running? Is the cable ' +
            'in? You check in order and write down findings.',
        },
        options: [
          {
            label: {
              es: '¿Quien mantiene la red?',
              en: 'Who maintains the network?',
            },
            next: 'redMantener',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      redMantener: {
        text: {
          es:
            'Nosotros. Pablo capacito a unos seis estudiantes para ' +
            'sostener la solucion sin el. Yo soy una de ellos; por eso ' +
            'la ronda.',
          en:
            'We do. Pablo trained about six students to sustain the ' +
            'solution without him. I am one of them; hence the ' +
            'rounds.',
        },
        options: [
          {
            label: {
              es: '¿Como fue esa capacitacion?',
              en: 'How was that training?',
            },
            next: 'aprenderCapacitacion',
          },
          {
            label: {
              es: '¿En que consiste tu ronda?',
              en: 'What are your rounds like?',
            },
            next: 'redRonda',
          },
          {
            label: {
              es: 'Impresionante',
              en: 'Impressive',
            },
            next: 'hub',
          },
        ],
      },
      redRonda: {
        text: {
          es:
            'Recorro las PCs, lanzo un ping en cada una y anoto el ' +
            'tiempo, como nos mostro Pablo. Doce rondas al dia. Si ' +
            'algo tarda de mas, se investiga.',
          en:
            'I walk past the PCs, fire a ping on each one and write ' +
            'down the time, the way Pablo showed us. Twelve rounds a ' +
            'day. If one takes too long, we investigate.',
        },
        options: [
          {
            label: {
              es: '¿Y si falla algo?',
              en: 'What if something fails?',
            },
            next: 'redFalla',
          },
          {
            label: {
              es: 'Dedicacion total',
              en: 'Total dedication',
            },
            next: 'hub',
          },
        ],
      },
      aprenderIntro: {
        text: {
          es:
            'De Pablo aprendi mas que a programar: arquitectura, ' +
            'diagnostico y documentacion. Todo dentro del proyecto ' +
            'academico IAI.',
          en:
            'From Pablo I learned more than programming: ' +
            'architecture, diagnosis and documentation. All within ' +
            'the IAI academic project.',
        },
        options: [
          {
            label: {
              es: '¿Como fue la capacitacion?',
              en: 'How was the training?',
            },
            next: 'aprenderCapacitacion',
          },
          {
            label: {
              es: '¿Por que tanta documentacion?',
              en: 'Why so much documentation?',
            },
            next: 'aprenderDoc',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      aprenderCapacitacion: {
        text: {
          es:
            'Fuimos unos seis estudiantes. Pablo no daba recetas: nos ' +
            'enseño a diagnosticar y a sostener el sistema por nuestra ' +
            'cuenta.',
          en:
            'We were about six students. Pablo gave no recipes: he ' +
            'taught us to diagnose and to sustain the system on our ' +
            'own.',
        },
        options: [
          {
            label: {
              es: '¿Sostenerlo sin el?',
              en: 'Sustain it without him?',
            },
            next: 'aprenderSostener',
          },
          {
            label: {
              es: '¿Que mas les enseño?',
              en: 'What else did he teach?',
            },
            next: 'aprenderDoc',
          },
        ],
      },
      aprenderSostener: {
        text: {
          es:
            'Esa era la meta de Pablo: que la solucion no dependiera ' +
            'de una sola persona. Si el no esta, el laboratorio sigue ' +
            'andando.',
          en:
            'That was the goal Pablo set: that the solution would not ' +
            'depend on one person. If he is away, the lab keeps ' +
            'running.',
        },
        options: [
          {
            label: {
              es: '¿Y funciono?',
              en: 'And did it work?',
            },
            next: 'aprenderFunciono',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      aprenderFunciono: {
        text: {
          es:
            'Mira alrededor: todo corre y Pablo no esta en esta sala. ' +
            'La mejor señal de una buena capacitacion es dejar de ' +
            'necesitar al maestro.',
          en:
            'Look around: everything runs and Pablo is not in this ' +
            'room. The best sign of good training is no longer ' +
            'needing the teacher.',
        },
        options: [
          {
            label: {
              es: '¿Y la documentacion?',
              en: 'And the documentation?',
            },
            next: 'aprenderDoc',
          },
          {
            label: {
              es: 'Bien dicho',
              en: 'Well said',
            },
            next: 'hub',
          },
        ],
      },
      aprenderDoc: {
        text: {
          es:
            'Pablo dejo cada decision escrita: diagramas, pasos, hasta ' +
            'el ping-pong. Gracias a el, aqui la documentacion tecnica ' +
            'es habito, no castigo.',
          en:
            'Pablo left every decision written down: diagrams, steps, ' +
            'even the ping-pong. Thanks to him, technical ' +
            'documentation here is a habit, not a punishment.',
        },
        options: [
          {
            label: {
              es: '¿No es aburrido documentar?',
              en: 'Is documenting not boring?',
            },
            next: 'aprenderAburrido',
          },
          {
            label: {
              es: '¿Y el diagnostico?',
              en: 'And the diagnosis?',
            },
            next: 'aprenderDiagnostico',
          },
        ],
      },
      aprenderAburrido: {
        text: {
          es:
            'Aburrido es pasar meses trabado por no haber escrito ' +
            'nada. Comparado con eso, documentar es una fiesta.',
          en:
            'Boring is spending months stuck because nothing was ' +
            'written down. Compared to that, documenting is a party.',
        },
        options: [
          {
            label: {
              es: 'Touche',
              en: 'Touche',
            },
            next: 'hub',
          },
          {
            label: {
              es: '¿Y esas pizarras?',
              en: 'What about those boards?',
            },
            next: 'aprenderPizarras',
          },
        ],
      },
      aprenderDiagnostico: {
        text: {
          es:
            'Antes de tocar, entender. Es la regla numero uno de ' +
            'Pablo. Un buen diagnostico ahorra semanas de arreglos a ' +
            'ciegas.',
          en:
            'Before touching, understand. That is rule number one ' +
            'from Pablo. A good diagnosis saves weeks of blind fixes.',
        },
        options: [
          {
            label: {
              es: '¿Y las pizarras?',
              en: 'And the boards?',
            },
            next: 'aprenderPizarras',
          },
          {
            label: {
              es: '¿Sirve fuera de aqui?',
              en: 'Does it work outside here?',
            },
            next: 'aprenderHabito',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      aprenderHabito: {
        text: {
          es:
            'Lo mejor: los habitos que nos dejo Pablo se van con uno. ' +
            'Diagnostico y documentacion sirven en cualquier proyecto, ' +
            'no solo en esta aula.',
          en:
            'The best part: the habits Pablo left us travel with you. ' +
            'Diagnosis and documentation work on any project, not ' +
            'only in this classroom.',
        },
        options: [
          {
            label: {
              es: '¿Y las pizarras?',
              en: 'And the boards?',
            },
            next: 'aprenderPizarras',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      aprenderPizarras: {
        text: {
          es:
            'En una pizarra anotamos RETOS y en la otra APRENDIZAJES. ' +
            'Cuando un reto cruza de pizarra, se celebra. Con ' +
            'aplausos, si.',
          en:
            'On one board we write CHALLENGES and on the other ' +
            'LESSONS. When a challenge crosses boards, we celebrate. ' +
            'With applause, yes.',
        },
        options: [
          {
            label: {
              es: '¿Cual fue el mayor reto?',
              en: 'What was the biggest one?',
            },
            next: 'aprenderReto',
          },
          {
            label: {
              es: 'Me gusta ese sistema',
              en: 'I like that system',
            },
            next: 'hub',
          },
        ],
      },
      aprenderReto: {
        text: {
          es:
            'El mayor: dos tesis con meses de bloqueo que Pablo ' +
            'reencamino. Hoy vive en la pizarra de APRENDIZAJES, con ' +
            'su fecha de 2015 y todo.',
          en:
            'The biggest: two theses blocked for months that Pablo ' +
            'got back on track. Today it lives on the LESSONS board, ' +
            'with its 2015 date and all.',
        },
        options: [
          {
            label: {
              es: 'Cuentame esa historia',
              en: 'Tell me that story',
            },
            next: 'tesisIntro',
          },
          {
            label: {
              es: 'Aqui todo conecta',
              en: 'Everything connects here',
            },
            next: 'aprenderFuturo',
          },
        ],
      },
      aprenderFuturo: {
        text: {
          es:
            'Asi es. Mi plan: seguir documentando como Pablo y algun ' +
            'dia capacitar yo a los siguientes seis. La ronda no se ' +
            'hereda sola.',
          en:
            'It does. My plan: keep documenting like Pablo and ' +
            'someday train the next six myself. The rounds do not ' +
            'inherit themselves.',
        },
        options: [
          {
            label: {
              es: 'Buena meta',
              en: 'Good goal',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Me despido',
              en: 'I will head out',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'tesista-uno': defineDialog({
    name: { es: 'Tesista aliviada', en: 'Relieved thesis student' },
    chatter: [
      {
        es: '¡Compila! ¡Por fin compila!',
        en: 'It compiles! It finally compiles!',
      },
      {
        es: 'Paso tres del plan de Pablo: casi listo.',
        en: 'Step three of the plan from Pablo: almost done.',
      },
      {
        es: 'Meses trabada... nunca mas.',
        en: 'Months stuck... never again.',
      },
      {
        es: 'Gracias a Pablo, hoy si me voy a graduar.',
        en: 'Thanks to Pablo, today I really will graduate.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Hm? Perdona, estaba celebrando: mi tesis compila. Era ' +
            'una de las dos que llevaban meses trabadas, hasta que ' +
            'Pablo se sento conmigo. ¿Que quieres saber?',
          en:
            'Hm? Sorry, I was celebrating: my thesis compiles. It was ' +
            'one of the two stuck for months, until Pablo sat down ' +
            'with me. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como fue estar bloqueada?',
              en: 'What was being blocked like?',
            },
            next: 'miedoUno',
          },
          {
            label: {
              es: 'El dia que llego Pablo',
              en: 'The day Pablo arrived',
            },
            next: 'planLlegada',
          },
          {
            label: {
              es: '¿En que vas ahora?',
              en: 'Where are you now?',
            },
            next: 'ahoraUno',
          },
          {
            label: {
              es: 'Te dejo trabajar',
              en: 'I will let you work',
            },
            next: null,
          },
        ],
      },
      miedoUno: {
        text: {
          es:
            'Meses sin avanzar de verdad. Escribia, borraba, volvia a ' +
            'escribir. La fecha de grado se acercaba y yo seguia en el ' +
            'mismo parrafo.',
          en:
            'Months with no real progress. I wrote, deleted, wrote ' +
            'again. Graduation day was getting closer and I was still ' +
            'on the same paragraph.',
        },
        options: [
          {
            label: {
              es: '¿Que era lo peor?',
              en: 'What was the worst part?',
            },
            next: 'miedoDos',
          },
          {
            label: {
              es: '¿Pensaste en rendirte?',
              en: 'Did you think of quitting?',
            },
            next: 'miedoCuatro',
          },
        ],
      },
      miedoDos: {
        text: {
          es:
            'Lo peor era no saber por donde empezar cada dia. Todo ' +
            'parecia urgente y nada avanzaba. El miedo a no graduarme ' +
            'dormia conmigo.',
          en:
            'The worst was not knowing where to start each day. ' +
            'Everything felt urgent and nothing moved. The fear of not ' +
            'graduating slept next to me.',
        },
        options: [
          {
            label: {
              es: '¿Y tu familia?',
              en: 'And your family?',
            },
            next: 'miedoTres',
          },
          {
            label: {
              es: '¿Pensaste en rendirte?',
              en: 'Did you think of quitting?',
            },
            next: 'miedoCuatro',
          },
        ],
      },
      miedoTres: {
        text: {
          es:
            'Cada domingo alguien preguntaba "¿y la tesis?" y yo ' +
            'cambiaba de tema con un talento que deberia dar creditos ' +
            'academicos.',
          en:
            'Every Sunday someone asked "how is the thesis going?" and ' +
            'I changed the subject with a talent that should earn ' +
            'academic credits.',
        },
        options: [
          {
            label: {
              es: '¿Pensaste en rendirte?',
              en: 'Did you think of quitting?',
            },
            next: 'miedoCuatro',
          },
          {
            label: {
              es: '¿Y como saliste?',
              en: 'And how did you get out?',
            },
            next: 'planLlegada',
          },
        ],
      },
      miedoCuatro: {
        text: {
          es:
            'Una vez. Cerre la laptop y dije "hasta aqui". Esa misma ' +
            'semana Pablo llego al laboratorio. El universo tiene su ' +
            'timing.',
          en:
            'Once. I closed the laptop and said "this is it". That ' +
            'same week Pablo arrived at the lab. The universe has its ' +
            'timing.',
        },
        options: [
          {
            label: {
              es: '¿Que hizo Pablo?',
              en: 'What did Pablo do?',
            },
            next: 'planLlegada',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      planLlegada: {
        text: {
          es:
            'Pablo llego en 2015 como asesor de proyectos de grado. ' +
            'El primer dia no toco mi codigo: se sento a mi lado, me ' +
            'escucho y leyo todo lo que yo habia escrito.',
          en:
            'Pablo arrived in 2015 as thesis advisor. On day one he ' +
            'did not touch my code: he sat next to me, listened, and ' +
            'read everything I had written.',
        },
        options: [
          {
            label: {
              es: '¿Y que te dijo?',
              en: 'And what did he tell you?',
            },
            next: 'planDiagnostico',
          },
          {
            label: {
              es: '¿Cuanto tardo?',
              en: 'How long did it take?',
            },
            next: 'planSemana',
          },
        ],
      },
      planDiagnostico: {
        text: {
          es:
            'Me devolvio un diagnostico que dolio de lo preciso: no ' +
            'me faltaba capacidad, me faltaba plan. Y mi alcance era ' +
            'tres tesis en una.',
          en:
            'He handed back a diagnosis so precise it hurt: I was not ' +
            'lacking ability, I was lacking a plan. And my scope was ' +
            'three theses in one.',
        },
        options: [
          {
            label: {
              es: '¿Y el plan?',
              en: 'And the plan?',
            },
            next: 'planPasos',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      planPasos: {
        text: {
          es:
            'Pablo recorto mi tesis a su nucleo y la partio conmigo ' +
            'en pasos con entregas claras. De "terminar la tesis" a ' +
            '"hoy cierro este capitulo".',
          en:
            'Pablo cut my thesis down to its core and split it with ' +
            'me into steps with clear deliverables. From "finish the ' +
            'thesis" to "close this chapter today".',
        },
        options: [
          {
            label: {
              es: '¿Funciono?',
              en: 'Did it work?',
            },
            next: 'planSemana',
          },
          {
            label: {
              es: '¿Que fue lo que mas sirvio?',
              en: 'What helped the most?',
            },
            next: 'planEscribir',
          },
        ],
      },
      planSemana: {
        text: {
          es:
            'En una semana estaba reencaminada. Una semana, despues ' +
            'de meses. Cuando Pablo dijo "listo, ya tienes rumbo", ' +
            'llore. De alivio, que conste en acta.',
          en:
            'In one week I was back on track. One week, after months. ' +
            'When Pablo said "done, you have a course now", I cried. ' +
            'Tears of relief, for the record.',
        },
        options: [
          {
            label: {
              es: '¿Que fue lo que mas sirvio?',
              en: 'What helped the most?',
            },
            next: 'planEscribir',
          },
          {
            label: {
              es: '¿Y ahora?',
              en: 'And now?',
            },
            next: 'ahoraUno',
          },
        ],
      },
      planEscribir: {
        text: {
          es:
            'Escribir el diagnostico, como me enseño Pablo. Ver el ' +
            'problema en papel lo achica: deja de ser un monstruo y ' +
            'pasa a ser una lista de pasos.',
          en:
            'Writing the diagnosis down, the way Pablo taught me. ' +
            'Seeing the problem on paper shrinks it: it stops being a ' +
            'monster and becomes a list of steps.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora en que vas?',
              en: 'And where are you now?',
            },
            next: 'ahoraUno',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      ahoraUno: {
        text: {
          es:
            'Avanzo cada dia un paso del plan. Hoy mi tesis compila y ' +
            'cada version queda anotada. Mirame: soy otra persona.',
          en:
            'I move one step of the plan each day. Today my thesis ' +
            'compiles and every version gets written down. Look at me: ' +
            'I am a new person.',
        },
        options: [
          {
            label: {
              es: '¿Y despues del grado?',
              en: 'And after graduation?',
            },
            next: 'ahoraDos',
          },
          {
            label: {
              es: '¿Documentas todo?',
              en: 'Do you document everything?',
            },
            next: 'ahoraTres',
          },
        ],
      },
      ahoraDos: {
        text: {
          es:
            'Primero graduarme. Despues quiero unirme al grupo que ' +
            'Pablo capacito para sostener el sistema del laboratorio: ' +
            'son unos seis y enseñan bien.',
          en:
            'First, graduate. Then I want to join the group Pablo ' +
            'trained to sustain the lab system: about six of them, ' +
            'and they teach well.',
        },
        options: [
          {
            label: {
              es: '¿Documentas todo?',
              en: 'Do you document everything?',
            },
            next: 'ahoraTres',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      ahoraTres: {
        text: {
          es:
            'Hasta documento sin que me lo pidan. Si mi yo de hace ' +
            'unos meses me viera, no me lo creeria. Los habitos de ' +
            'Pablo se pegan.',
          en:
            'I even document without being asked. If my past self ' +
            'from months ago saw me, she would not believe it. The ' +
            'habits from Pablo stick.',
        },
        options: [
          {
            label: {
              es: '¿Y el otro tesista?',
              en: 'And the other student?',
            },
            next: 'ahoraCuatro',
          },
          {
            label: {
              es: '¿Que aprendiste de todo esto?',
              en: 'What did you learn from this?',
            },
            next: 'leccionUno',
          },
        ],
      },
      ahoraCuatro: {
        text: {
          es:
            'Al de alla Pablo le enseño sockets y a debuggear la red. ' +
            'Te recitara su servidor y sus dos milisegundos sin ' +
            'respirar. Pero no le digas que te lo dije.',
          en:
            'Pablo taught the guy over there sockets and how to debug ' +
            'the network. He will recite his server and his two ' +
            'milliseconds nonstop. But do not tell him I said so.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste de todo esto?',
              en: 'What did you learn from this?',
            },
            next: 'leccionUno',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      leccionUno: {
        text: {
          es:
            'Que pedir ayuda a tiempo no es fracasar. Del miedo al ' +
            'alivio hubo una semana y el plan de Pablo. Ojala lo ' +
            'hubiera conocido antes.',
          en:
            'That asking for help in time is not failing. Between ' +
            'fear and relief there was one week and the plan from ' +
            'Pablo. I wish I had met him sooner.',
        },
        options: [
          {
            label: {
              es: 'Gracias por contarlo',
              en: 'Thanks for sharing',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Sigue asi',
              en: 'Keep it up',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'tesista-dos': defineDialog({
    name: { es: 'Tesista de los sockets', en: 'Socket thesis student' },
    chatter: [
      {
        es: 'bind, listen, accept. Como me enseño Pablo.',
        en: 'bind, listen, accept. Just like Pablo taught me.',
      },
      {
        es: 'Dos milisegundos. Ni uno mas.',
        en: 'Two milliseconds. Not one more.',
      },
      {
        es: 'Si no esta documentado, no existe. Regla de Pablo.',
        en: 'If it is not documented, it does not exist. Rule from Pablo.',
      },
      {
        es: 'Aquel primer pong... todavia lo escucho.',
        en: 'That first pong... I can still hear it.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Necesitas algo? Estoy contando milisegundos. Es broma. ' +
            'A medias. Puedo hablarte de mi servidor, de la base de ' +
            'datos o de lo que aprendi con Pablo.',
          en:
            'Need something? I am counting milliseconds. Joking. Half ' +
            'joking. I can talk about my server, the database, or ' +
            'what I learned with Pablo.',
        },
        options: [
          {
            label: {
              es: 'El servidor de sockets',
              en: 'The socket server',
            },
            next: 'sockUno',
          },
          {
            label: {
              es: 'La base de datos comun',
              en: 'The common database',
            },
            next: 'bdUno',
          },
          {
            label: {
              es: 'Eso de documentar',
              en: 'That documenting thing',
            },
            next: 'docUno',
          },
          {
            label: {
              es: 'Sigue contando',
              en: 'Keep counting',
            },
            next: null,
          },
        ],
      },
      sockUno: {
        text: {
          es:
            'Mi tesis es cliente-servidor: servidor.c en C hace bind ' +
            'al puerto 8080, listen, y espera conexiones. Pablo me ' +
            'enseño cada llamada, a mano, sin atajos.',
          en:
            'My thesis is client-server: servidor.c in C binds to ' +
            'port 8080, listens, and waits for connections. Pablo ' +
            'taught me every call, by hand, no shortcuts.',
        },
        options: [
          {
            label: {
              es: '¿Y que responde?',
              en: 'And what does it answer?',
            },
            next: 'sockDos',
          },
          {
            label: {
              es: '¿Por que en C?',
              en: 'Why in C?',
            },
            next: 'sockTres',
          },
        ],
      },
      sockDos: {
        text: {
          es:
            'El cliente manda "ping". El servidor responde "pong". ' +
            'Dos milisegundos. He visto conversaciones humanas mucho ' +
            'menos eficientes.',
          en:
            'The client sends "ping". The server answers "pong". Two ' +
            'milliseconds. I have seen far less efficient human ' +
            'conversations.',
        },
        options: [
          {
            label: {
              es: '¿Como fue el primer pong?',
              en: 'How was the first pong?',
            },
            next: 'pongPrimero',
          },
          {
            label: {
              es: '¿Por que en C?',
              en: 'Why in C?',
            },
            next: 'sockTres',
          },
        ],
      },
      sockTres: {
        text: {
          es:
            'Porque C no perdona ni esconde. Pablo me lo dijo el ' +
            'primer dia: si entiendes bind, listen y accept a mano, ' +
            'entiendes lo que corre debajo de todo lo moderno.',
          en:
            'Because C forgives nothing and hides nothing. Pablo told ' +
            'me on day one: if you understand bind, listen and accept ' +
            'by hand, you understand what runs under anything modern.',
        },
        options: [
          {
            label: {
              es: '¿2ms es bueno?',
              en: 'Is 2ms good?',
            },
            next: 'sockCuatro',
          },
          {
            label: {
              es: '¿Y si no responde?',
              en: 'What if it does not answer?',
            },
            next: 'sockCinco',
          },
        ],
      },
      sockCuatro: {
        text: {
          es:
            'En red local, es lo esperado. Pablo me enseño a medirlo ' +
            'siempre: un numero que no mides es una opinion, y las ' +
            'opiniones no compilan.',
          en:
            'On a local network, it is what you expect. Pablo taught ' +
            'me to always measure it: an unmeasured number is an ' +
            'opinion, and opinions do not compile.',
        },
        options: [
          {
            label: {
              es: '¿Y si un dia no responde?',
              en: 'And if one day it is silent?',
            },
            next: 'sockCinco',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      sockCinco: {
        text: {
          es:
            'Entonces diagnostico en orden, como me entreno Pablo: ' +
            '¿corre el proceso? ¿escucha el 8080? ¿esta el cable? Y ' +
            'todo se anota. Todo.',
          en:
            'Then diagnosis in order, the way Pablo drilled me: is ' +
            'the process running? Is 8080 listening? Is the cable in? ' +
            'And everything gets written down. Everything.',
        },
        options: [
          {
            label: {
              es: 'Metodico',
              en: 'Methodical',
            },
            next: 'hub',
          },
          {
            label: {
              es: '¿Anotar tambien eso?',
              en: 'Write even that down?',
            },
            next: 'docUno',
          },
        ],
      },
      pongPrimero: {
        text: {
          es:
            'Semanas peleando con la red y nada. Una tarde Pablo se ' +
            'quedo conmigo a debuggear: IPs, cables, el bind, todo en ' +
            'orden. Y de pronto: pong. Grite tan fuerte que toda el ' +
            'aula volteo.',
          en:
            'Weeks fighting the network and nothing. One afternoon ' +
            'Pablo stayed with me to debug: IPs, cables, the bind, ' +
            'all in order. And suddenly: pong. I yelled so loud the ' +
            'whole room turned around.',
        },
        options: [
          {
            label: {
              es: '¿Que cambio ese dia?',
              en: 'What changed that day?',
            },
            next: 'rescTres',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      bdUno: {
        text: {
          es:
            'Todos los clientes hablan con una base de datos comun a ' +
            'traves del servidor. Una sola fuente de verdad para todo ' +
            'el sistema.',
          en:
            'All clients talk to a common database through the server. ' +
            'A single source of truth for the whole system.',
        },
        options: [
          {
            label: {
              es: '¿Que guarda?',
              en: 'What does it store?',
            },
            next: 'bdDos',
          },
          {
            label: {
              es: '¿Por que una sola?',
              en: 'Why a single one?',
            },
            next: 'bdTres',
          },
        ],
      },
      bdDos: {
        text: {
          es:
            'Datos del sistema de gestion de obras: avances, ' +
            'materiales, responsables. Todo entra ordenado o no entra.',
          en:
            'Data for the construction works management system: ' +
            'progress, materials, people in charge. It enters ordered ' +
            'or it does not enter.',
        },
        options: [
          {
            label: {
              es: '¿Por que una BD comun?',
              en: 'Why a common database?',
            },
            next: 'bdTres',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      bdTres: {
        text: {
          es:
            'La alternativa es que cada quien guarde su archivo y ' +
            'despues nadie sepa cual vale. No, gracias. Una BD, un ' +
            'servidor, cero dramas.',
          en:
            'The alternative is everyone keeping their own file and ' +
            'then nobody knowing which one counts. No, thanks. One ' +
            'database, one server, zero drama.',
        },
        options: [
          {
            label: {
              es: '¿Y quien diseño esto?',
              en: 'And who designed this?',
            },
            next: 'bdCuatro',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      bdCuatro: {
        text: {
          es:
            'Pablo, en 2015: cliente-servidor sobre la red local del ' +
            'laboratorio. Arquitectura simple y clara. Lo simple bien ' +
            'hecho envejece bien.',
          en:
            'Pablo did, in 2015: client-server over the local network ' +
            'of the lab. Simple, clear architecture. Simple done well ' +
            'ages well.',
        },
        options: [
          {
            label: {
              es: '¿El mismo que rescato tu tesis?',
              en: 'The one who rescued your thesis?',
            },
            next: 'rescUno',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      docUno: {
        text: {
          es:
            'Documentar no es opcional; eso me lo enseño Pablo. El ' +
            'codigo dice como; el documento dice por que. Y el "por ' +
            'que" es lo primero que se olvida.',
          en:
            'Documenting is not optional; Pablo taught me that. The ' +
            'code says how; the document says why. And the "why" is ' +
            'the first thing you forget.',
        },
        options: [
          {
            label: {
              es: '¿Siempre pensaste asi?',
              en: 'Did you always think so?',
            },
            next: 'docDos',
          },
          {
            label: {
              es: '¿Que documentas?',
              en: 'What do you document?',
            },
            next: 'docTres',
          },
        ],
      },
      docDos: {
        text: {
          es:
            'No. Cuando Pablo hablo de diagnostico y documentacion ' +
            'como habitos, pense: burocracia. Despues lei mi propio ' +
            'codigo de hace un mes, sin documentar. No entendi nada. ' +
            'Fin del debate.',
          en:
            'No. When Pablo talked about diagnosis and documentation ' +
            'as habits, I thought: bureaucracy. Then I read my own ' +
            'month-old undocumented code. I understood nothing. End ' +
            'of debate.',
        },
        options: [
          {
            label: {
              es: '¿Que documentas hoy?',
              en: 'What do you document today?',
            },
            next: 'docTres',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      docTres: {
        text: {
          es:
            'Todo: el diagnostico de cada falla, cada decision del ' +
            'diseño, hasta el ping-pong de 2ms. Mi regla: si no esta ' +
            'escrito, no existe.',
          en:
            'Everything: the diagnosis of every failure, every design ' +
            'decision, even the 2ms ping-pong. My rule: if it is not ' +
            'written, it does not exist.',
        },
        options: [
          {
            label: {
              es: '¿Y si esta escrito dos veces?',
              en: 'And if it is written twice?',
            },
            next: 'docCuatro',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      docCuatro: {
        text: {
          es:
            'Si esta escrito dos veces distinto, existe mal. Una ' +
            'fuente de verdad, tambien en los documentos. Como la base ' +
            'de datos.',
          en:
            'If it is written twice differently, it exists wrongly. ' +
            'One source of truth, in documents too. Like the database.',
        },
        options: [
          {
            label: {
              es: 'Coherente',
              en: 'Consistent',
            },
            next: 'hub',
          },
          {
            label: {
              es: '¿Tu tesis tambien se trabo?',
              en: 'Did your thesis get stuck too?',
            },
            next: 'rescUno',
          },
        ],
      },
      rescUno: {
        text: {
          es:
            'Si. Mi tesis estuvo meses trabada; era una de las dos ' +
            'que Pablo rescato. Su plan me reencamino en una semana. ' +
            'No fue magia: fue diagnostico. Y esta documentado.',
          en:
            'Yes. My thesis was stuck for months; it was one of the ' +
            'two Pablo rescued. His plan got me back on track in one ' +
            'week. It was not magic: it was diagnosis. Documented.',
        },
        options: [
          {
            label: {
              es: '¿Como era estar trabado?',
              en: 'What was being stuck like?',
            },
            next: 'rescDos',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      rescDos: {
        text: {
          es:
            'Como un accept() que nunca recibe conexion: tecnicamente ' +
            'vivo, funcionalmente inutil. Apagaba la pantalla cuando ' +
            'alguien pasaba, de pura pena.',
          en:
            'Like an accept() that never receives a connection: ' +
            'technically alive, functionally useless. I switched the ' +
            'screen off when anyone walked by, out of embarrassment.',
        },
        options: [
          {
            label: {
              es: '¿Y como saliste?',
              en: 'And how did you get out?',
            },
            next: 'pongPrimero',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      rescTres: {
        text: {
          es:
            'Desde ese pong tecleo con la pantalla encendida, a la ' +
            'vista de todos. La otra tesista lo cuenta con lagrimas ' +
            'de alegria. Yo lo cuento en milisegundos. Cada quien.',
          en:
            'Since that pong I type with the screen on, in plain ' +
            'sight. The other thesis student tells it with tears of ' +
            'joy. I tell it in milliseconds. To each their own.',
        },
        options: [
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Sigue midiendo',
              en: 'Keep measuring',
            },
            next: null,
          },
        ],
      },
    },
  }),
  profesor: defineDialog({
    name: { es: 'Profesor de la catedra', en: 'Course professor' },
    chatter: [
      {
        es: 'En años de catedra se ven pocos alumnos asi.',
        en: 'In years of teaching you meet few students like him.',
      },
      {
        es: 'Dos tesis rescatadas en una semana. Una semana.',
        en: 'Two theses rescued in one week. One week.',
      },
      {
        es: 'La documentacion de ese proyecto era de nivel profesional.',
        en: 'The documentation of that project was professional-grade.',
      },
      {
        es: 'Un lider no nace en la pizarra: se ve en el laboratorio.',
        en: 'A leader is not born at the blackboard: you see it in the lab.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Adelante. Soy el profesor de la catedra de sistemas. Si ' +
            'busca referencias de Pablo Contreras, llego al lugar ' +
            'indicado: fue de los mejores ingenieros de software que ' +
            'pasaron por esta aula. ¿Que le interesa saber?',
          en:
            'Come in. I teach the systems course here. If you are ' +
            'looking for references on Pablo Contreras, you came to ' +
            'the right place: he was one of the best software ' +
            'engineers to pass through this classroom. What would you ' +
            'like to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era como ingeniero?',
              en: 'What was he like as an engineer?',
            },
            next: 'ingeniero',
          },
          {
            label: {
              es: 'El rescate de las dos tesis',
              en: 'The rescue of the two theses',
            },
            next: 'rescate',
          },
          {
            label: {
              es: '¿Y como lider de equipo?',
              en: 'And as a team lead?',
            },
            next: 'lider',
          },
          {
            label: {
              es: 'Gracias, profesor',
              en: 'Thank you, professor',
            },
            next: null,
          },
        ],
      },
      ingeniero: {
        text: {
          es:
            'Riguroso. Diseño una arquitectura cliente-servidor sobre ' +
            'la red local — una PC como servidor central — y elimino ' +
            'las copias de datos desincronizadas del proyecto. Y lo ' +
            'documento todo: cada decision con su porque.',
          en:
            'Rigorous. He designed a client-server architecture over ' +
            'the local network — one PC as the central server — and ' +
            'removed the out-of-sync data copies from the project. ' +
            'And he documented everything: every decision with its why.',
        },
        options: [
          {
            label: {
              es: '¿Eso era comun en un alumno?',
              en: 'Was that common in a student?',
            },
            next: 'raro',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      raro: {
        text: {
          es:
            'Nada comun. Los alumnos entregan codigo; Pablo entregaba ' +
            'sistemas: con arquitectura, con plan de hitos, con ' +
            'riesgos gestionados. Por eso hablo de el como ingeniero ' +
            'de software y no como estudiante.',
          en:
            'Not common at all. Students hand in code; Pablo handed ' +
            'in systems: with architecture, with milestones, with ' +
            'managed risks. That is why I speak of him as a software ' +
            'engineer, not as a student.',
        },
        options: [
          {
            label: {
              es: '¿Y las tesis rescatadas?',
              en: 'And the rescued theses?',
            },
            next: 'rescate',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      rescate: {
        text: {
          es:
            'Dos equipos llevaban meses bloqueados con sus proyectos ' +
            'de grado. Pablo diagnostico los puntos de falla, armo un ' +
            'plan de trabajo y en mas o menos una semana ambos ' +
            'proyectos estaban listos para defensa. Sin recortar el ' +
            'alcance.',
          en:
            'Two teams had been stuck on their final projects for ' +
            'months. Pablo diagnosed the failure points, put together ' +
            'a work plan and in roughly one week both projects were ' +
            'ready for their defense. Without cutting scope.',
        },
        options: [
          {
            label: {
              es: '¿Como lo logro tan rapido?',
              en: 'How did he do it so fast?',
            },
            next: 'metodo',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      metodo: {
        text: {
          es:
            'No fue magia: fue diagnostico. Encontro donde fallaba el ' +
            'codigo heredado, prioritizo lo critico para la entrega y ' +
            'ademas capacito a los tesistas para defender su propia ' +
            'solucion. El cuadro del plan esta ahi en la pared.',
          en:
            'It was not magic: it was diagnosis. He found where the ' +
            'inherited code failed, prioritized what was critical for ' +
            'delivery and also coached the students to defend their ' +
            'own solution. The plan is framed right there on the wall.',
        },
        options: [
          {
            label: {
              es: '¿Y como lider?',
              en: 'And as a leader?',
            },
            next: 'lider',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      lider: {
        text: {
          es:
            'Coordino un equipo de unas tres personas y llevo su ' +
            'proyecto de grado a una entrega exitosa, dentro del ' +
            'plazo. Distribuia tareas, hacia seguimiento y explicaba ' +
            'el razonamiento de cada decision. Liderazgo temprano, ' +
            'del que se ve poco.',
          en:
            'He coordinated a team of about three people and took ' +
            'their final project to a successful delivery, on time. ' +
            'He distributed tasks, tracked progress and explained the ' +
            'reasoning behind every decision. Early leadership, the ' +
            'kind you rarely see.',
        },
        options: [
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Gracias, profesor',
              en: 'Thank you, professor',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'companero-proyecto': defineDialog({
    name: { es: 'Compañero del proyecto', en: 'Project teammate' },
    chatter: [
      {
        es: 'Presupuestos y avances de obra, todo sale del sistema.',
        en: 'Budgets and site progress, it all comes out of the system.',
      },
      {
        es: 'Antes consolidar datos era una jornada entera. Ya no.',
        en: 'Consolidating data used to take a full day. Not anymore.',
      },
      {
        es: 'Eramos tres. Pablo nos hizo sentir un equipo de verdad.',
        en: 'We were three. Pablo made us feel like a real team.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Que tal? Estoy con el sistema de gestion de obras — el ' +
            'proyecto que sacamos adelante con Pablo. Eramos un ' +
            'equipo chico, unas tres personas, y el lo lideraba. ' +
            '¿Quieres que te cuente?',
          en:
            'Hey! I am working on the construction-site management ' +
            'system — the project we pulled off with Pablo. We were a ' +
            'small team, about three people, and he led it. Want me ' +
            'to tell you about it?',
        },
        options: [
          {
            label: {
              es: '¿Que hacia el sistema?',
              en: 'What did the system do?',
            },
            next: 'sistema',
          },
          {
            label: {
              es: '¿Como era trabajar con Pablo?',
              en: 'What was working with Pablo like?',
            },
            next: 'equipo',
          },
          {
            label: {
              es: 'Sigo mi camino',
              en: 'I will keep going',
            },
            next: null,
          },
        ],
      },
      sistema: {
        text: {
          es:
            'Gestion de obras: presupuestos, avances, reportes. Antes ' +
            'consolidar todo eso era trabajo manual de jornadas; con ' +
            'el sistema salia directo en reportes. Y corria en red ' +
            'local, con una PC como servidor central para que todos ' +
            'compartieramos los mismos datos.',
          en:
            'Site management: budgets, progress, reports. ' +
            'Consolidating all that used to be days of manual work; ' +
            'with the system it came straight out as reports. And it ' +
            'ran on a local network, with one PC as the central ' +
            'server so we all shared the same data.',
        },
        options: [
          {
            label: {
              es: '¿Quien diseño esa red?',
              en: 'Who designed that network?',
            },
            next: 'red',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      red: {
        text: {
          es:
            'Pablo. El diagrama cliente-servidor que esta enmarcado ' +
            'en la pared es de esa epoca: una PC servidor, los demas ' +
            'conectados, cero copias desincronizadas. Suena obvio ' +
            'hoy; en ese laboratorio fue una revolucion.',
          en:
            'Pablo. The client-server diagram framed on the wall is ' +
            'from that time: one server PC, the rest connected, zero ' +
            'out-of-sync copies. It sounds obvious today; in that lab ' +
            'it was a revolution.',
        },
        options: [
          {
            label: {
              es: '¿Y el equipo?',
              en: 'And the team?',
            },
            next: 'equipo',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      equipo: {
        text: {
          es:
            'Ordenado sin ser rigido. Repartia las tareas, seguia el ' +
            'avance y cuando algo se trababa se sentaba contigo hasta ' +
            'destrabarlo. Entregamos dentro del plazo y cada uno ' +
            'podia explicar su parte. Eso ultimo era lo que mas le ' +
            'importaba.',
          en:
            'Organized without being rigid. He split the tasks, ' +
            'tracked progress and when something got stuck he sat ' +
            'with you until it was unstuck. We delivered on time and ' +
            'each of us could explain our part. That last bit was ' +
            'what he cared about most.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste de el?',
              en: 'What did you learn from him?',
            },
            next: 'aprendi',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      aprendi: {
        text: {
          es:
            'Que la arquitectura no es un dibujo: es poder justificar ' +
            'cada decision. La documentacion del proyecto explicaba ' +
            'los porques, no solo los comos. Todavia escribo mis docs ' +
            'imitando esas.',
          en:
            'That architecture is not a drawing: it is being able to ' +
            'justify every decision. The project documentation ' +
            'explained the whys, not just the hows. I still write my ' +
            'docs imitating those.',
        },
        options: [
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Me despido',
              en: 'I will head out',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'companero-ayudado': defineDialog({
    name: { es: 'Estudiante desatascado', en: 'Unstuck student' },
    chatter: [
      {
        es: 'Yo estaba TRABADO. Pablo me desatasco en una tarde.',
        en: 'I was STUCK. Pablo unstuck me in one afternoon.',
      },
      {
        es: 'No me dio el codigo: me enseño a leer el error.',
        en: 'He did not give me the code: he taught me to read the error.',
      },
      {
        es: 'Ahora el servidor me responde el pong. A la primera.',
        en: 'Now the server answers my pong. On the first try.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¡Mira! El socket ya conecta. Semanas peleando con esto y ' +
            'Pablo me lo desenredo... sin tocar mi teclado. Soy uno ' +
            'de los seis que capacito para sostener la red del ' +
            'laboratorio. ¿Que quieres saber?',
          en:
            'Look! The socket finally connects. Weeks fighting this ' +
            'and Pablo untangled it... without touching my keyboard. ' +
            'I am one of the six he trained to sustain the lab ' +
            'network. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como te ayudo?',
              en: 'How did he help you?',
            },
            next: 'ayuda',
          },
          {
            label: {
              es: '¿Que es eso de los seis?',
              en: 'What is that about the six?',
            },
            next: 'seis',
          },
          {
            label: {
              es: 'Suerte con el socket',
              en: 'Good luck with the socket',
            },
            next: null,
          },
        ],
      },
      ayuda: {
        text: {
          es:
            'Me hacia preguntas. "¿Que dice el error? ¿Que esperabas ' +
            'que pasara?" Y de pregunta en pregunta el bug aparecio ' +
            'solo. Despues me explico la implementacion completa, con ' +
            'el razonamiento detras de cada decision.',
          en:
            'He asked me questions. "What does the error say? What ' +
            'did you expect to happen?" And question by question the ' +
            'bug showed itself. Then he explained the full ' +
            'implementation, with the reasoning behind every decision.',
        },
        options: [
          {
            label: {
              es: '¿Y funciono?',
              en: 'Did it work?',
            },
            next: 'funciono',
          },
          {
            label: {
              es: 'Otro tema',
              en: 'Another topic',
            },
            next: 'hub',
          },
        ],
      },
      funciono: {
        text: {
          es:
            'Funciono tanto que ahora puedo defender mi solucion sin ' +
            'mirar apuntes. Esa era su vara: no que compile — que la ' +
            'puedas explicar.',
          en:
            'It worked so well that now I can defend my solution ' +
            'without notes. That was his bar: not that it compiles — ' +
            'that you can explain it.',
        },
        options: [
          {
            label: {
              es: '¿Que es eso de los seis?',
              en: 'What about the six?',
            },
            next: 'seis',
          },
          {
            label: {
              es: 'Volver',
              en: 'Back',
            },
            next: 'hub',
          },
        ],
      },
      seis: {
        text: {
          es:
            'Cuando rescato los dos proyectos de grado, no se llevo ' +
            'el conocimiento con el: nos capacito a unos seis ' +
            'estudiantes de los dos equipos para que la solucion se ' +
            'sostuviera sola. La estudiante de la ronda es otra de ' +
            'nosotros.',
          en:
            'When he rescued the two final projects, he did not take ' +
            'the knowledge with him: he trained about six of us ' +
            'across the two teams so the solution could stand on its ' +
            'own. The student doing the rounds is another one of us.',
        },
        options: [
          {
            label: {
              es: '¿Como te ayudo a ti?',
              en: 'How did he help you?',
            },
            next: 'ayuda',
          },
          {
            label: {
              es: 'Me despido',
              en: 'I will head out',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
