/**
 * @module dialogs/aula-presente (engine)
 * @description Arboles de dialogo de la Sala 0 presente: aula/laboratorio
 *   universitario (~2015). La estudiante de ronda (rescate de las dos tesis,
 *   red cliente-servidor del proyecto IAI, capacitacion de ~6 estudiantes),
 *   la tesista aliviada y el tesista de los sockets (C, puerto 8080,
 *   ping-pong en 2ms, base de datos comun).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const AULA_PRESENTE_DIALOGS = {
  'estudiante-ronda': defineDialog({
    name: { es: 'Estudiante de ronda', en: 'Student on rounds' },
    chatter: [
      {
        es: 'Ping... pong. Me encanta ese sonido.',
        en: 'Ping... pong. I love that sound.',
      },
      {
        es: '¿Ya viste las pizarras de RETOS y APRENDIZAJES?',
        en: 'Have you seen the CHALLENGES and LESSONS boards?',
      },
      {
        es: 'Meses trabados... y en una semana, listos.',
        en: 'Months stuck... and in one week, back on track.',
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
            '¡Hola! Bienvenido al laboratorio. Aqui pasamos de dos tesis ' +
            'trabadas a un sistema corriendo en red. Yo hago la ronda: ' +
            'reviso que cada PC responda. ¿Que te cuento?',
          en:
            'Hi! Welcome to the lab. We went from two stuck theses to a ' +
            'system running on the network. I do the rounds: I check ' +
            'that every PC responds. What can I tell you?',
        },
        options: [
          {
            label: {
              es: 'Las dos tesis bloqueadas',
              en: 'The two blocked theses',
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
              es: '¿Que se aprende aqui?',
              en: 'What do you learn here?',
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
            'corria hacia la fecha de grado.',
          en:
            'Two thesis projects were blocked for months. Months. The ' +
            'students came in, typed, deleted... and the clock kept ' +
            'running toward graduation day.',
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
              es: '¿Y como salieron?',
              en: 'And how did they get out?',
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
            'de alla casi no dormia. Preguntale: hoy ya lo cuenta ' +
            'sonriendo.',
          en:
            'There was real fear: no thesis, no degree. The student ' +
            'over there barely slept. Ask her: today she tells it with ' +
            'a smile.',
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
              es: '¿Quien los rescato?',
              en: 'Who rescued them?',
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
              es: '¿Quien los rescato?',
              en: 'Who rescued them?',
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
            'En 2015 llego el asesor de proyectos de grado, con el ' +
            'proyecto academico IAI bajo el brazo. No toco nada al ' +
            'llegar: pregunto, leyo y escucho.',
          en:
            'In 2015 the thesis advisor arrived, with the IAI academic ' +
            'project under his arm. He touched nothing on arrival: he ' +
            'asked, read and listened.',
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
            'El primer dia solo escucho y leyo todo lo que habia: ' +
            'borradores, notas, codigo. Decia que opinar antes de ' +
            'entender sale caro.',
          en:
            'On day one he only listened and read everything there ' +
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
            'El diagnostico fue directo: no faltaba capacidad, faltaba ' +
            'foco. Demasiados frentes abiertos y ninguna meta medible.',
          en:
            'The diagnosis was direct: ability was not missing, focus ' +
            'was. Too many open fronts and not a single measurable ' +
            'goal.',
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
            'Del diagnostico salio un plan de rescate: recortar cada ' +
            'tesis a su nucleo, ordenar los pasos y ponerles entregas ' +
            'claras.',
          en:
            'From the diagnosis came a rescue plan: cut each thesis ' +
            'down to its core, order the steps and set clear ' +
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
            'la falta de plan. El mismo metodo las reencamino a las ' +
            'dos.',
          en:
            'They were two different theses, but the problem was the ' +
            'same: no plan. The same method got both back on track.',
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
            'En mas o menos una semana, las dos estaban reencaminadas. ' +
            'Una semana contra meses de bloqueo. No fue magia: fue ' +
            'metodo.',
          en:
            'In about one week, both were back on track. One week ' +
            'against months of blockage. It was not magic: it was ' +
            'method.',
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
            'Dos habitos: diagnosticar antes de tocar nada y documentar ' +
            'cada decision. Suena simple. Lo dificil es hacerlo ' +
            'siempre.',
          en:
            'Two habits: diagnose before touching anything and document ' +
            'every decision. It sounds simple. The hard part is doing ' +
            'it always.',
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
            'cada paso. El te recita el servidor de sockets sin ' +
            'respirar.',
          en:
            'There they are, typing. She finally compiles and ' +
            'celebrates every step. He recites the socket server ' +
            'without taking a breath.',
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
            'de plan. Una semana bien dirigida vale mas que un ' +
            'semestre a ciegas.',
          en:
            'That being stuck for months is not lack of talent: it is ' +
            'lack of a plan. One well-guided week beats a blind ' +
            'semester.',
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
              es: '¿Que mas se aprende aqui?',
              en: 'What else do you learn here?',
            },
            next: 'aprenderIntro',
          },
        ],
      },
      redIntro: {
        text: {
          es:
            'Cada pupitre tiene una PC conectada a la red local del ' +
            'aula. Es una arquitectura cliente-servidor que diseño el ' +
            'asesor.',
          en:
            'Every desk has a PC connected to the local network of the ' +
            'room. It is a client-server architecture designed by the ' +
            'advisor.',
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
            'El asesor. Separar cliente y servidor sobre la red local ' +
            'hizo el sistema mas claro: cada parte con su ' +
            'responsabilidad.',
          en:
            'The advisor. Splitting client and server over the local ' +
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
            'Cada PC corre un servidor de sockets escrito en C. Hace ' +
            'bind al puerto 8080, listen, y se queda esperando ' +
            'conexiones.',
          en:
            'Every PC runs a socket server written in C. It binds to ' +
            'port 8080, listens, and stays there waiting for ' +
            'connections.',
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
            'Porque C no esconde nada: bind, listen, accept, a mano. ' +
            'Si entiendes sockets en C, entiendes lo que corre debajo ' +
            'de todo lo demas.',
          en:
            'Because C hides nothing: bind, listen, accept, by hand. ' +
            'If you understand sockets in C, you understand what runs ' +
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
            'En red local, 2ms es un latido sano. Lo medimos siempre, ' +
            'porque lo que no se mide no se puede diagnosticar.',
          en:
            'On a local network, 2ms is a healthy heartbeat. We always ' +
            'measure it, because what is not measured cannot be ' +
            'diagnosed.',
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
            'Diagnostico, no panico: ¿responde el puerto 8080? ¿corre ' +
            'el proceso? ¿esta el cable? Se revisa en orden y se anota ' +
            'lo encontrado.',
          en:
            'Diagnosis, not panic: does port 8080 answer? Is the ' +
            'process running? Is the cable in? You check in order and ' +
            'write down findings.',
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
            'Nosotros. El asesor capacito a unos seis estudiantes para ' +
            'sostener la solucion sin el. Yo soy una de ellos; por eso ' +
            'la ronda.',
          en:
            'We do. The advisor trained about six students to sustain ' +
            'the solution without him. I am one of them; hence the ' +
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
            'tiempo. Doce rondas al dia. Si algo tarda de mas, se ' +
            'investiga.',
          en:
            'I walk past the PCs, fire a ping on each one and write ' +
            'down the time. Twelve rounds a day. If one takes too ' +
            'long, we investigate.',
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
            'Aqui se aprende mas que a programar: arquitectura, ' +
            'diagnostico y documentacion. Todo dentro del proyecto ' +
            'academico IAI.',
          en:
            'Here you learn more than programming: architecture, ' +
            'diagnosis and documentation. All within the IAI academic ' +
            'project.',
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
            'Fuimos unos seis estudiantes. El asesor no daba recetas: ' +
            'nos enseño a diagnosticar y a sostener el sistema por ' +
            'nuestra cuenta.',
          en:
            'We were about six students. The advisor gave no recipes: ' +
            'he taught us to diagnose and to sustain the system on our ' +
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
            'Esa era la meta: que la solucion no dependiera de una ' +
            'sola persona. Si el asesor no esta, el laboratorio sigue ' +
            'andando.',
          en:
            'That was the goal: that the solution would not depend on ' +
            'one person. If the advisor is away, the lab keeps ' +
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
            'Mira alrededor: todo corre y el no esta en esta sala. La ' +
            'mejor señal de una buena capacitacion es dejar de ' +
            'necesitar al maestro.',
          en:
            'Look around: everything runs and he is not in this room. ' +
            'The best sign of good training is no longer needing the ' +
            'teacher.',
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
            'Cada decision quedo escrita: diagramas, pasos, hasta el ' +
            'ping-pong. Aqui la documentacion tecnica es habito, no ' +
            'castigo.',
          en:
            'Every decision was written down: diagrams, steps, even ' +
            'the ping-pong. Here technical documentation is a habit, ' +
            'not a punishment.',
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
            'Antes de tocar, entender. Es la regla numero uno del ' +
            'asesor. Un buen diagnostico ahorra semanas de arreglos a ' +
            'ciegas.',
          en:
            'Before touching, understand. That is rule number one from ' +
            'the advisor. A good diagnosis saves weeks of blind fixes.',
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
            'Lo mejor: esos habitos se van con uno. Diagnostico y ' +
            'documentacion sirven en cualquier proyecto, no solo en ' +
            'esta aula.',
          en:
            'The best part: those habits leave with you. Diagnosis and ' +
            'documentation work on any project, not only in this ' +
            'classroom.',
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
            'El mayor: dos tesis con meses de bloqueo. Hoy vive en la ' +
            'pizarra de APRENDIZAJES, con su fecha de 2015 y todo.',
          en:
            'The biggest: two theses blocked for months. Today it ' +
            'lives on the LESSONS board, with its 2015 date and all.',
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
            'Asi es. Mi plan: seguir documentando y algun dia ' +
            'capacitar yo a los siguientes seis. La ronda no se hereda ' +
            'sola.',
          en:
            'It does. My plan: keep documenting and someday train the ' +
            'next six myself. The rounds do not inherit themselves.',
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
        es: 'Paso tres del plan: casi listo.',
        en: 'Step three of the plan: almost done.',
      },
      {
        es: 'Meses trabada... nunca mas.',
        en: 'Months stuck... never again.',
      },
      {
        es: 'Hoy si me voy a graduar.',
        en: 'Today I really will graduate.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Hm? Perdona, estaba celebrando: mi tesis compila. Hace ' +
            'unos meses no te habria ni mirado, estaba hundida. ¿Que ' +
            'quieres saber?',
          en:
            'Hm? Sorry, I was celebrating: my thesis compiles. A few ' +
            'months ago I would not even have looked up, I was ' +
            'sinking. What do you want to know?',
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
              es: 'El plan de rescate',
              en: 'The rescue plan',
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
            'semana llego el asesor al laboratorio. El universo tiene ' +
            'su timing.',
          en:
            'Once. I closed the laptop and said "this is it". That ' +
            'same week the advisor arrived at the lab. The universe ' +
            'has its timing.',
        },
        options: [
          {
            label: {
              es: '¿Que hizo el asesor?',
              en: 'What did the advisor do?',
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
            'Llego en 2015, como asesor de proyectos de grado. Lo ' +
            'primero que dijo fue algo como "primero entendamos, ' +
            'despues opinamos".',
          en:
            'He arrived in 2015 as a thesis advisor. The first thing ' +
            'he said was something like "first we understand, then we ' +
            'give opinions".',
        },
        options: [
          {
            label: {
              es: '¿Y entendio?',
              en: 'And did he understand?',
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
            'Leyo mis borradores, mis notas, todo. Y me devolvio un ' +
            'diagnostico que dolio de lo preciso: no me faltaba ' +
            'capacidad, me faltaba plan.',
          en:
            'He read my drafts, my notes, everything. And he handed ' +
            'back a diagnosis so precise it hurt: I was not lacking ' +
            'ability, I was lacking a plan.',
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
            'Recortamos la tesis a su nucleo y la partimos en pasos ' +
            'con entregas claras. De "terminar la tesis" a "hoy cierro ' +
            'este capitulo".',
          en:
            'We cut the thesis down to its core and split it into ' +
            'steps with clear deliverables. From "finish the thesis" ' +
            'to "close this chapter today".',
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
            'En una semana estaba reencaminada. Una semana, despues de ' +
            'meses. Llore un poco. De alegria, que conste en acta.',
          en:
            'In one week I was back on track. One week, after months. ' +
            'I cried a little. Tears of joy, for the record.',
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
            'Escribir el diagnostico. Ver el problema en papel lo ' +
            'achica: deja de ser un monstruo y pasa a ser una lista de ' +
            'pasos.',
          en:
            'Writing the diagnosis down. Seeing the problem on paper ' +
            'shrinks it: it stops being a monster and becomes a list ' +
            'of steps.',
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
            'Primero graduarme. Despues quiero quedarme cerca del ' +
            'grupo que sostiene el sistema del laboratorio: son unos ' +
            'seis y enseñan bien.',
          en:
            'First, graduate. Then I want to stay close to the group ' +
            'that sustains the lab system: about six of them, and they ' +
            'teach well.',
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
            'unos meses me viera, no me lo creeria. El habito se pega.',
          en:
            'I even document without being asked. If my past self from ' +
            'months ago saw me, she would not believe it. The habit ' +
            'sticks.',
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
            'El te dira que documentar no es opcional y que su ' +
            'servidor responde en dos milisegundos. Tiene razon. Pero ' +
            'no se lo digas de mi parte.',
          en:
            'He will tell you documenting is not optional and that his ' +
            'server answers in two milliseconds. He is right. But do ' +
            'not tell him I said so.',
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
            'alivio hubo una semana y un buen plan. Ojala lo hubiera ' +
            'sabido antes.',
          en:
            'That asking for help in time is not failing. Between fear ' +
            'and relief there was one week and a good plan. I wish I ' +
            'had known sooner.',
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
        es: 'bind, listen, accept. Como la vida.',
        en: 'bind, listen, accept. Like life.',
      },
      {
        es: 'Dos milisegundos. Ni uno mas.',
        en: 'Two milliseconds. Not one more.',
      },
      {
        es: 'Si no esta documentado, no existe.',
        en: 'If it is not documented, it does not exist.',
      },
      {
        es: 'El servidor escucha. Aprende de el.',
        en: 'The server listens. Learn from it.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Necesitas algo? Estoy contando milisegundos. Es broma. A ' +
            'medias. Puedo hablarte del servidor, de la base de datos ' +
            'o de documentar.',
          en:
            'Need something? I am counting milliseconds. Joking. Half ' +
            'joking. I can talk about the server, the database, or ' +
            'documenting.',
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
            'Cada PC del aula corre un servidor de sockets escrito en ' +
            'C. Hace bind al puerto 8080, listen, y espera conexiones. ' +
            'Paciencia de monje.',
          en:
            'Every PC in the room runs a socket server written in C. ' +
            'It binds to port 8080, listens, and waits for ' +
            'connections. Monk-level patience.',
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
            'El cliente manda "ping". El servidor responde "pong". Dos ' +
            'milisegundos. He visto conversaciones humanas mucho menos ' +
            'eficientes.',
          en:
            'The client sends "ping". The server answers "pong". Two ' +
            'milliseconds. I have seen far less efficient human ' +
            'conversations.',
        },
        options: [
          {
            label: {
              es: '¿Por que en C?',
              en: 'Why in C?',
            },
            next: 'sockTres',
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
      sockTres: {
        text: {
          es:
            'Porque C no perdona ni esconde. Si entiendes bind, listen ' +
            'y accept a mano, entiendes lo que corre debajo de ' +
            'cualquier cosa moderna.',
          en:
            'Because C forgives nothing and hides nothing. If you ' +
            'understand bind, listen and accept by hand, you ' +
            'understand what runs under anything modern.',
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
            'En red local, es lo esperado. Lo importante es medirlo ' +
            'siempre: un numero que no mides es una opinion, y las ' +
            'opiniones no compilan.',
          en:
            'On a local network, it is what you expect. The key is to ' +
            'always measure it: an unmeasured number is an opinion, ' +
            'and opinions do not compile.',
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
            'Entonces tengo trabajo. Diagnostico en orden: ¿corre el ' +
            'proceso? ¿escucha el 8080? ¿esta el cable? Y todo se ' +
            'anota. Todo.',
          en:
            'Then I have work to do. Diagnosis in order: is the ' +
            'process running? Is 8080 listening? Is the cable in? And ' +
            'everything gets written down. Everything.',
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
            'El asesor, en 2015: cliente-servidor sobre la red local. ' +
            'Arquitectura simple y clara. Lo simple bien hecho ' +
            'envejece bien.',
          en:
            'The advisor, in 2015: client-server over the local ' +
            'network. Simple, clear architecture. Simple done well ' +
            'ages well.',
        },
        options: [
          {
            label: {
              es: '¿El mismo del rescate de tesis?',
              en: 'The one from the thesis rescue?',
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
            'Documentar no es opcional. El codigo dice como; el ' +
            'documento dice por que. Y el "por que" es lo primero que ' +
            'se olvida.',
          en:
            'Documenting is not optional. The code says how; the ' +
            'document says why. And the "why" is the first thing you ' +
            'forget.',
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
            'No. Cuando el asesor hablo de diagnostico y documentacion ' +
            'como habitos, pense: burocracia. Despues lei mi propio ' +
            'codigo de hace un mes, sin documentar. No entendi nada. ' +
            'Fin del debate.',
          en:
            'No. When the advisor talked about diagnosis and ' +
            'documentation as habits, I thought: bureaucracy. Then I ' +
            'read my own month-old undocumented code. I understood ' +
            'nothing. End of debate.',
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
            'El mismo. Mi tesis estuvo meses trabada. Su plan de ' +
            'rescate me reencamino en una semana. No fue magia: fue ' +
            'diagnostico. Y si, esta documentado.',
          en:
            'The same one. My thesis was stuck for months. His rescue ' +
            'plan got me back on track in one week. It was not magic: ' +
            'it was diagnosis. And yes, it is documented.',
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
            'vivo, funcionalmente inutil. Ahora avanzo. Paso a paso, ' +
            'con entregas claras.',
          en:
            'Like an accept() that never receives a connection: ' +
            'technically alive, functionally useless. Now I move. Step ' +
            'by step, with clear deliverables.',
        },
        options: [
          {
            label: {
              es: 'Bonita metafora',
              en: 'Nice metaphor',
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
      rescTres: {
        text: {
          es:
            'No es metafora, es diagnostico. La otra tesista lo cuenta ' +
            'con lagrimas de alegria. Yo lo cuento en milisegundos. ' +
            'Cada quien.',
          en:
            'It is not a metaphor, it is a diagnosis. The other thesis ' +
            'student tells it with tears of joy. I tell it in ' +
            'milliseconds. To each their own.',
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
} satisfies Record<string, NpcDialog>
