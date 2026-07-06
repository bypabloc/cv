/**
 * @module dialogs/aula-presente (engine)
 * @description Arboles de dialogo de la Sala 0 presente: aula/laboratorio
 *   de la UPTYAB (universidad pura, 2011-2016). Los 6 NPCs hablan de la
 *   vida universitaria — clases, laboratorio de redes, practicas, Pablo
 *   ayudando a otros y liderando equipos de catedra. Las historias de
 *   2015 (el sistema del IAI y la tesis rescatada de PROSALUD) NO se
 *   cuentan aqui: viven en sus propias salas; el profesor solo las
 *   ANTICIPA (foreshadowing de una linea, sin spoiler).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const AULA_PRESENTE_DIALOGS = {
  'estudiante-ronda': defineDialog({
    name: { es: 'Estudiante de ronda', en: 'Student on rounds' },
    chatter: [
      {
        es: 'Ping... pong. El latido del laboratorio.',
        en: 'Ping... pong. The heartbeat of the lab.',
      },
      {
        es: '¿Ya viste las pizarras de RETOS y APRENDIZAJES?',
        en: 'Have you seen the CHALLENGES and LESSONS boards?',
      },
      {
        es: 'Esta semana me toca a mi cuidar el laboratorio.',
        en: 'This week it is my turn to look after the lab.',
      },
      {
        es: 'Este laboratorio es mi lugar favorito del campus.',
        en: 'This lab is my favorite place on campus.',
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
            '¡Hola! Bienvenido al laboratorio de la UPTYAB. Esta semana ' +
            'me toca la ronda: reviso que cada PC responda y que la red ' +
            'siga viva. ¿Que te cuento?',
          en:
            'Hi! Welcome to the UPTYAB lab. This week I am on rounds: I ' +
            'check that every PC responds and that the network stays ' +
            'alive. What can I tell you?',
        },
        options: [
          {
            label: {
              es: 'La ronda y el laboratorio',
              en: 'The rounds and the lab',
            },
            next: 'rondaIntro',
          },
          {
            label: {
              es: '¿Como es estudiar aqui?',
              en: 'What is studying here like?',
            },
            next: 'uniIntro',
          },
          {
            label: {
              es: 'Cuentame de Pablo',
              en: 'Tell me about Pablo',
            },
            next: 'pabloIntro',
          },
          {
            label: { es: 'Me despido', en: 'I will head out' },
            next: null,
          },
        ],
      },
      rondaIntro: {
        text: {
          es:
            'El laboratorio se cuida entre todos: el rol de la ronda ' +
            'rota cada semana. Toca revisar cables, reiniciar la PC que ' +
            'se colgo y anotar que maquina anda rara.',
          en:
            'We all look after the lab together: the rounds role ' +
            'rotates every week. You check cables, reboot the PC that ' +
            'froze and note down which machine acts up.',
        },
        options: [
          {
            label: {
              es: '¿Y como sabes que la red vive?',
              en: 'How do you know the network is alive?',
            },
            next: 'rondaPing',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      rondaPing: {
        text: {
          es:
            'Ping a cada maquina. Si el servidor del aula contesta ' +
            'pong en dos milisegundos, todo bien. Fue Pablo el que nos ' +
            'enseño a leer esa señal como un latido: si late, vive.',
          en:
            'Ping every machine. If the classroom server answers pong ' +
            'in two milliseconds, all good. It was Pablo who taught us ' +
            'to read that signal like a heartbeat: if it beats, it lives.',
        },
        options: [
          {
            label: {
              es: '¿Que pasa si una PC no responde?',
              en: 'What if a PC does not respond?',
            },
            next: 'rondaFalla',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      rondaFalla: {
        text: {
          es:
            'Primero el cable, despues la tarjeta, despues la config. ' +
            'En ese orden, siempre. Diagnosticar antes de tocar: eso ' +
            'tambien lo aprendimos aqui, a la mala.',
          en:
            'First the cable, then the card, then the config. In that ' +
            'order, always. Diagnose before touching: we learned that ' +
            'here too, the hard way.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Gracias por el dato', en: 'Thanks for the tip' },
            next: null,
          },
        ],
      },
      uniIntro: {
        text: {
          es:
            'Ingenieria Informatica en la Universidad Politecnica ' +
            'Territorial de Yaracuy. Programacion, bases de datos, ' +
            'redes, sistemas operativos... y mucho laboratorio. Aqui se ' +
            'aprende haciendo.',
          en:
            'Informatics Engineering at the Yaracuy Territorial ' +
            'Polytechnic University. Programming, databases, networks, ' +
            'operating systems... and a lot of lab time. Here you learn ' +
            'by doing.',
        },
        options: [
          {
            label: {
              es: '¿Cual es la materia mas dura?',
              en: 'Which course is the toughest?',
            },
            next: 'uniDura',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      uniDura: {
        text: {
          es:
            'Depende a quien le preguntes: para unos punteros en C, ' +
            'para otros normalizar bases de datos. Para mi, madrugar ' +
            'despues de trabajar de noche. Mas de uno aqui se paga la ' +
            'carrera trabajando.',
          en:
            'Depends who you ask: for some it is C pointers, for ' +
            'others database normalization. For me, waking up early ' +
            'after working nights. More than one of us here pays for ' +
            'their degree by working.',
        },
        options: [
          {
            label: {
              es: '¿Pablo tambien trabajaba?',
              en: 'Did Pablo work too?',
            },
            next: 'uniPabloTrabajo',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      uniPabloTrabajo: {
        text: {
          es:
            'Si: reparaba aires acondicionados para pagarse la carrera. ' +
            'Llegaba del trabajo, se sentaba en esa PC y seguia ' +
            'estudiando por su cuenta con tutoriales. Nunca entendi de ' +
            'donde sacaba la energia.',
          en:
            'Yes: he fixed air conditioners to pay his way through. He ' +
            'would come from work, sit at that PC and keep studying on ' +
            'his own with tutorials. I never understood where the ' +
            'energy came from.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Que constancia', en: 'What perseverance' },
            next: null,
          },
        ],
      },
      pabloIntro: {
        text: {
          es:
            'Pablo es el que siempre esta ayudando a alguien. Si una ' +
            'practica no te sale, te hace lugar, mira tu pantalla y te ' +
            'pregunta cosas hasta que TU encuentras el error.',
          en:
            'Pablo is the one always helping someone. If a practice ' +
            'will not work, he makes room for you, looks at your ' +
            'screen and asks you questions until YOU find the bug.',
        },
        options: [
          {
            label: {
              es: '¿No te da el codigo y ya?',
              en: 'He does not just give you the code?',
            },
            next: 'pabloMetodo',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      pabloMetodo: {
        text: {
          es:
            'Nunca. Dice que el codigo regalado se olvida y el error ' +
            'encontrado se recuerda. Molesta un poco al principio... ' +
            'hasta que un dia depuras sola y entiendes por que lo hacia.',
          en:
            'Never. He says gifted code gets forgotten and a bug you ' +
            'found yourself gets remembered. It is a bit annoying at ' +
            'first... until one day you debug alone and understand why ' +
            'he did it.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Buen metodo', en: 'Good method' },
            next: null,
          },
        ],
      },
    },
  }),

  'companera-lab': defineDialog({
    name: { es: 'Compañera de laboratorio', en: 'Lab partner' },
    chatter: [
      {
        es: 'Compila... compila... ¡compilo!',
        en: 'Compiling... compiling... it compiled!',
      },
      {
        es: 'Una practica mas y entrego la de redes.',
        en: 'One more practice and I submit the networks one.',
      },
      {
        es: 'El diagrama primero, el codigo despues. Ya aprendi.',
        en: 'Diagram first, code second. I learned my lesson.',
      },
      {
        es: 'Este semestre si apruebo bases de datos.',
        en: 'This semester I am passing databases for sure.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Hola, dame un segundo que guardo... listo. Estoy con la ' +
            'practica de redes: cliente y servidor conversando en la ' +
            'red local del aula. ¿Que quieres saber?',
          en:
            'Hi, one second while I save... done. I am on the networks ' +
            'practice: a client and a server talking over the ' +
            'classroom local network. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como es la practica?',
              en: 'What is the practice like?',
            },
            next: 'practicaIntro',
          },
          {
            label: {
              es: '¿Estudian en grupo?',
              en: 'Do you study in groups?',
            },
            next: 'grupoIntro',
          },
          {
            label: { es: 'Sigue con lo tuyo', en: 'Back to your work' },
            next: null,
          },
        ],
      },
      practicaIntro: {
        text: {
          es:
            'Cada equipo monta su par cliente-servidor y el profesor ' +
            'desconecta un cable a proposito para ver quien diagnostica ' +
            'mas rapido. La primera vez entramos en panico. Ahora nos ' +
            'reimos.',
          en:
            'Each team builds their client-server pair and the ' +
            'professor unplugs a cable on purpose to see who diagnoses ' +
            'fastest. The first time we panicked. Now we laugh.',
        },
        options: [
          {
            label: {
              es: '¿Y quien diagnostica mas rapido?',
              en: 'And who diagnoses fastest?',
            },
            next: 'practicaPablo',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      practicaPablo: {
        text: {
          es:
            'Pablo, casi siempre. Pero no por magia: tiene un metodo. ' +
            'Va descartando por capas — cable, tarjeta, config, ' +
            'codigo — y anota lo que descarta. Nos obligo a todos a ' +
            'hacer lo mismo.',
          en:
            'Pablo, almost always. But not by magic: he has a method. ' +
            'He rules things out layer by layer — cable, card, config, ' +
            'code — and writes down what he rules out. He made us all ' +
            'do the same.',
        },
        options: [
          {
            label: {
              es: '¿Anotar? ¿Como un registro?',
              en: 'Write it down? Like a log?',
            },
            next: 'practicaDoc',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      practicaDoc: {
        text: {
          es:
            'Un cuaderno de decisiones: que probamos, que fallo, por ' +
            'que elegimos tal diseño. El profesor ahora lo pide en ' +
            'todas las entregas. Culpa de Pablo, gracias a Pablo.',
          en:
            'A decision notebook: what we tried, what failed, why we ' +
            'chose this design. The professor now requires it in every ' +
            'submission. Pablo is to blame, Pablo deserves the thanks.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Buena costumbre', en: 'Good habit' },
            next: null,
          },
        ],
      },
      grupoIntro: {
        text: {
          es:
            'Si, en equipos de tres o cuatro. Reparto de tareas, ' +
            'integracion al final... y el clasico compañero que ' +
            'desaparece la semana de la entrega. De todo se aprende.',
          en:
            'Yes, in teams of three or four. Splitting tasks, ' +
            'integrating at the end... and the classic teammate who ' +
            'vanishes on submission week. You learn from everything.',
        },
        options: [
          {
            label: {
              es: '¿Y como se organizan?',
              en: 'How do you organize?',
            },
            next: 'grupoOrganizar',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      grupoOrganizar: {
        text: {
          es:
            'Cuando Pablo esta en el equipo, se nota: pizarra, tareas ' +
            'claras por persona, y el diagrama del sistema ANTES de la ' +
            'primera linea de codigo. Al principio parecia perder ' +
            'tiempo. Nunca mas integramos a ciegas.',
          en:
            'When Pablo is on the team, you can tell: whiteboard, ' +
            'clear tasks per person, and the system diagram BEFORE the ' +
            'first line of code. At first it felt like wasted time. We ' +
            'never integrated blindly again.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Suena a lider', en: 'Sounds like a leader' },
            next: 'grupoLider',
          },
        ],
      },
      grupoLider: {
        text: {
          es:
            'Sin el titulo, si. Nadie lo nombro lider de nada: se gano ' +
            'el rol explicando, repartiendo bien y entregando su parte ' +
            'primero. Asi da gusto seguir a alguien.',
          en:
            'Without the title, yes. Nobody appointed him leader of ' +
            'anything: he earned the role by explaining, splitting work ' +
            'fairly and delivering his part first. That makes someone ' +
            'easy to follow.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Gracias', en: 'Thanks' },
            next: null,
          },
        ],
      },
    },
  }),

  'estudiante-sockets': defineDialog({
    name: { es: 'Estudiante de los sockets', en: 'Socket student' },
    chatter: [
      {
        es: 'bind... listen... accept. Ya me lo sueño.',
        en: 'bind... listen... accept. I dream about it now.',
      },
      {
        es: '¡Pong en dos milisegundos! Miralo tu mismo.',
        en: 'Pong in two milliseconds! See for yourself.',
      },
      {
        es: 'El puerto 8080 es MI puerto.',
        en: 'Port 8080 is MY port.',
      },
      {
        es: 'Un segfault mas y aprendo otra cosa nueva.',
        en: 'One more segfault and I learn something new again.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¡Mira la pantalla! Cliente y servidor en C, conversando ' +
            'por la red del aula. Mi primer socket. ¿Quieres que te ' +
            'cuente como fue?',
          en:
            'Look at the screen! A client and a server in C, talking ' +
            'over the classroom network. My first socket. Want to hear ' +
            'how it went?',
        },
        options: [
          {
            label: {
              es: 'Cuentame lo del primer pong',
              en: 'Tell me about the first pong',
            },
            next: 'pongIntro',
          },
          {
            label: {
              es: '¿Quien te enseño sockets?',
              en: 'Who taught you sockets?',
            },
            next: 'maestroIntro',
          },
          {
            label: { es: 'Sigue programando', en: 'Keep coding' },
            next: null,
          },
        ],
      },
      pongIntro: {
        text: {
          es:
            'Tres noches peleando: el bind fallaba, el listen no ' +
            'escuchaba, y yo culpaba a la PC. Cuando por fin el ' +
            'servidor devolvio "pong"... grite. El profesor me saco ' +
            'del laboratorio por el escandalo.',
          en:
            'Three nights fighting: bind failed, listen would not ' +
            'listen, and I blamed the PC. When the server finally ' +
            'returned "pong"... I screamed. The professor kicked me ' +
            'out of the lab for the ruckus.',
        },
        options: [
          {
            label: {
              es: '¿Y que habia fallado?',
              en: 'So what was wrong?',
            },
            next: 'pongBug',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      pongBug: {
        text: {
          es:
            'Un puntero. SIEMPRE es un puntero. Pasaba la estructura ' +
            'mal y el socket recibia basura. Pablo lo vio en cinco ' +
            'minutos... pero no me lo dijo: me hizo imprimir cada valor ' +
            'hasta que lo vi yo.',
          en:
            'A pointer. It is ALWAYS a pointer. I was passing the ' +
            'struct wrong and the socket got garbage. Pablo saw it in ' +
            'five minutes... but did not tell me: he made me print ' +
            'every value until I saw it myself.',
        },
        options: [
          {
            label: {
              es: '¿Te molesto que no te lo dijera?',
              en: 'Did it bother you he would not tell?',
            },
            next: 'pongLeccion',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      pongLeccion: {
        text: {
          es:
            'En el momento si. Pero el siguiente segfault lo encontre ' +
            'solo en diez minutos. Ahi entendi: no me habia dado un ' +
            'pez, me habia enseñado a pescar punteros.',
          en:
            'In the moment, yes. But the next segfault I found alone ' +
            'in ten minutes. Then I got it: he had not given me a ' +
            'fish, he had taught me to fish for pointers.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Gran leccion', en: 'Great lesson' },
            next: null,
          },
        ],
      },
      maestroIntro: {
        text: {
          es:
            'La teoria el profesor, la practica Pablo. El ya habia ' +
            'hecho estas practicas y en vez de irse temprano se ' +
            'quedaba a ayudar al que viniera atras. Conmigo se quedo ' +
            'muchas tardes.',
          en:
            'The theory came from the professor, the practice from ' +
            'Pablo. He had already done these exercises and instead of ' +
            'leaving early he stayed to help whoever came behind. With ' +
            'me he stayed many afternoons.',
        },
        options: [
          {
            label: {
              es: '¿Que mas te enseño?',
              en: 'What else did he teach you?',
            },
            next: 'maestroMas',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      maestroMas: {
        text: {
          es:
            'A leer el error antes de googlearlo. A dibujar la red ' +
            'antes de cablearla. Y a respetar el servidor del aula: ' +
            '"una PC que sirve a todas las demas merece cuidado", ' +
            'decia. Como si fuera una mascota.',
          en:
            'To read the error before googling it. To draw the ' +
            'network before wiring it. And to respect the classroom ' +
            'server: "a PC that serves all the others deserves care", ' +
            'he said. Like it was a pet.',
        },
        options: [
          {
            label: {
              es: '¿El servidor del aula?',
              en: 'The classroom server?',
            },
            next: 'maestroServer',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      maestroServer: {
        text: {
          es:
            'Esa PC del rincon: una maquina normal que hace de ' +
            'servidor central para todo el laboratorio. Datos en un ' +
            'solo lugar, todos conectados. Simple y poderoso. Pablo le ' +
            'tenia un cariño especial a esa idea.',
          en:
            'That PC in the corner: a normal machine acting as the ' +
            'central server for the whole lab. Data in one place, ' +
            'everyone connected. Simple and powerful. Pablo had a ' +
            'special fondness for that idea.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Gracias', en: 'Thanks' },
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
        es: 'Trabajar de dia, estudiar de noche... y aun asi, primero.',
        en: 'Working by day, studying by night... and still first.',
      },
      {
        es: 'Un lider no nace en la pizarra: se ve en el laboratorio.',
        en: 'A leader is not born at the blackboard: you see it in the lab.',
      },
      {
        es: 'Lo que ese muchacho hizo despues... eso es otra historia.',
        en: 'What that young man did later... that is another story.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Adelante. Soy el profesor de la catedra de sistemas. Si ' +
            'busca referencias de Pablo Contreras, llego al lugar ' +
            'indicado: fue de los mejores estudiantes que pasaron por ' +
            'esta aula. ¿Que le interesa saber?',
          en:
            'Come in. I teach the systems course here. If you are ' +
            'looking for references on Pablo Contreras, you came to the ' +
            'right place: he was one of the best students to pass ' +
            'through this classroom. What would you like to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era como estudiante?',
              en: 'What was he like as a student?',
            },
            next: 'estudiante',
          },
          {
            label: {
              es: '¿Es cierto que trabajaba ademas?',
              en: 'Is it true he also worked?',
            },
            next: 'disciplina',
          },
          {
            label: {
              es: '¿Y que hizo despues del aula?',
              en: 'And what did he do after the classroom?',
            },
            next: 'despues',
          },
          {
            label: { es: 'Gracias, profesor', en: 'Thank you, professor' },
            next: null,
          },
        ],
      },
      estudiante: {
        text: {
          es:
            'De los que preguntan "por que" hasta que el tema se ' +
            'rinde. No memorizaba: entendia. Y lo que entendia, lo ' +
            'explicaba a los demas mejor que algunos colegas mios, ' +
            'dicho con respeto.',
          en:
            'The kind who asks "why" until the topic surrenders. He ' +
            'did not memorize: he understood. And what he understood, ' +
            'he explained to others better than some of my colleagues, ' +
            'with all due respect.',
        },
        options: [
          {
            label: {
              es: '¿En que destacaba mas?',
              en: 'Where did he stand out most?',
            },
            next: 'potencial',
          },
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
        ],
      },
      potencial: {
        text: {
          es:
            'En ver el sistema completo. Un alumno normal resuelve el ' +
            'ejercicio; Pablo preguntaba quien lo iba a usar, que ' +
            'pasaba si fallaba y como se mantenia despues. Cabeza de ' +
            'arquitecto en cuerpo de estudiante.',
          en:
            'In seeing the whole system. A normal student solves the ' +
            'exercise; Pablo asked who would use it, what happened if ' +
            'it failed and how it would be maintained later. An ' +
            'architect mind in a student body.',
        },
        options: [
          {
            label: {
              es: '¿Y como lider de equipos?',
              en: 'And as a team leader?',
            },
            next: 'lider',
          },
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
        ],
      },
      lider: {
        text: {
          es:
            'Los laboratorios grupales aqui son un caos hermoso. Los ' +
            'equipos de Pablo eran la excepcion: tareas claras, un ' +
            'diagrama en la pizarra y un cuaderno donde justificaba ' +
            'cada decision. Documentar es un habito raro incluso en ' +
            'profesionales; el lo traia de fabrica.',
          en:
            'Group labs here are a beautiful chaos. Pablo’s teams ' +
            'were the exception: clear tasks, a diagram on the ' +
            'whiteboard and a notebook justifying every decision. ' +
            'Documenting is a rare habit even among professionals; he ' +
            'came with it built in.',
        },
        options: [
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
          {
            label: { es: 'Impresionante', en: 'Impressive' },
            next: null,
          },
        ],
      },
      disciplina: {
        text: {
          es:
            'Cierto. Reparaba aires acondicionados para pagarse la ' +
            'carrera. Llegaba con las manos curtidas del trabajo y aun ' +
            'asi entregaba primero. Y de noche seguia aprendiendo solo, ' +
            'con tutoriales de internet. Esa disciplina no se enseña.',
          en:
            'True. He repaired air conditioners to pay for his ' +
            'degree. He arrived with work-worn hands and still ' +
            'delivered first. And at night he kept learning on his ' +
            'own, with internet tutorials. That discipline cannot be ' +
            'taught.',
        },
        options: [
          {
            label: {
              es: '¿Autodidacta ademas?',
              en: 'Self-taught as well?',
            },
            next: 'autodidacta',
          },
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
        ],
      },
      autodidacta: {
        text: {
          es:
            'Desde 2012, mas o menos. Llegaba al aula sabiendo cosas ' +
            'que el pensum tocaria dos semestres despues. Yo le daba ' +
            'la base; el hambre la ponia el. La universidad enciende ' +
            'la mecha, pero la polvora era suya.',
          en:
            'Since 2012 or so. He would arrive knowing things the ' +
            'curriculum would not touch for two more semesters. I gave ' +
            'him the foundation; the hunger was his. University lights ' +
            'the fuse, but the gunpowder was his own.',
        },
        options: [
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
          {
            label: { es: 'Gracias, profesor', en: 'Thank you, professor' },
            next: null,
          },
        ],
      },
      despues: {
        text: {
          es:
            'Ah, eso no me corresponde contarlo a mi. Solo le adelanto ' +
            'algo: lo del instituto de obras publicas y el rescate de ' +
            'una tesis ajena... eso mirelo unas salas mas adelante. ' +
            'Vale la pena llegar.',
          en:
            'Ah, that story is not mine to tell. I will only give you ' +
            'a hint: the public-works institute and the rescue of ' +
            'someone else’s thesis... look for that a few rooms ' +
            'ahead. It is worth the walk.',
        },
        options: [
          {
            label: {
              es: 'Me guardo la intriga',
              en: 'I will keep the suspense',
            },
            next: null,
          },
          {
            label: { es: 'Otra pregunta', en: 'Another question' },
            next: 'hub',
          },
        ],
      },
    },
  }),

  'companero-proyecto': defineDialog({
    name: { es: 'Compañero de proyecto', en: 'Project teammate' },
    chatter: [
      {
        es: 'Integrar el viernes lo que se reparte el lunes: esa es la ley.',
        en: 'Integrate on Friday what you split on Monday: that is the law.',
      },
      {
        es: 'Mi parte ya esta. Bueno... casi.',
        en: 'My part is done. Well... almost.',
      },
      {
        es: 'El diagrama de Pablo sigue en la pizarra. Nadie lo borra.',
        en: 'Pablo’s diagram is still on the whiteboard. Nobody erases it.',
      },
      {
        es: 'Entregamos a tiempo. TODAVIA no lo creo.',
        en: 'We delivered on time. I STILL cannot believe it.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Que tal? Estoy con la entrega del proyecto de catedra: ' +
            'nos toco un sistema de inventario para un negocio ' +
            'inventado. Pablo esta en mi equipo — por eso vamos bien. ' +
            '¿Que quieres saber?',
          en:
            'Hey! I am on our course project delivery: we got an ' +
            'inventory system for a made-up business. Pablo is on my ' +
            'team — that is why we are on track. What do you want to ' +
            'know?',
        },
        options: [
          {
            label: {
              es: '¿Como trabaja en equipo?',
              en: 'How does he work in a team?',
            },
            next: 'equipo',
          },
          {
            label: {
              es: '¿Que aprendiste de el?',
              en: 'What did you learn from him?',
            },
            next: 'aprendi',
          },
          {
            label: { es: 'Suerte con la entrega', en: 'Good luck with it' },
            next: null,
          },
        ],
      },
      equipo: {
        text: {
          es:
            'Primero escucha lo que cada uno sabe hacer. Despues ' +
            'reparte para que cada quien brille en lo suyo... y se ' +
            'queda con lo mas dificil el. La pizarra siempre tiene el ' +
            'mapa: quien hace que y como se conecta todo.',
          en:
            'First he listens to what each of us is good at. Then he ' +
            'splits the work so everyone shines at their thing... and ' +
            'keeps the hardest part for himself. The whiteboard always ' +
            'has the map: who does what and how it all connects.',
        },
        options: [
          {
            label: {
              es: '¿Y si alguien se atrasa?',
              en: 'What if someone falls behind?',
            },
            next: 'atraso',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      atraso: {
        text: {
          es:
            'No te deja caer. Se sienta contigo, corta tu tarea en ' +
            'pedazos mas chicos y te desbloquea el primero. Dice que ' +
            'un equipo entrega junto o no entrega. Aqui eso es casi ' +
            'una filosofia exotica.',
          en:
            'He does not let you sink. He sits with you, cuts your ' +
            'task into smaller pieces and unblocks the first one. He ' +
            'says a team delivers together or does not deliver. Around ' +
            'here that is almost an exotic philosophy.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Buen compañero', en: 'Good teammate' },
            next: null,
          },
        ],
      },
      aprendi: {
        text: {
          es:
            'Que el diagrama no es burocracia: es ver el choque de ' +
            'trenes ANTES de que pase. Y que "funciona en mi maquina" ' +
            'no es entregar. Probamos todo en la red del aula antes de ' +
            'presentarlo.',
          en:
            'That the diagram is not bureaucracy: it is seeing the ' +
            'train crash BEFORE it happens. And that "works on my ' +
            'machine" is not delivering. We test everything on the ' +
            'classroom network before presenting.',
        },
        options: [
          {
            label: {
              es: '¿Eso tambien es de Pablo?',
              en: 'Is that also from Pablo?',
            },
            next: 'costumbre',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      costumbre: {
        text: {
          es:
            'Si. Y se pega. Ahora me sale solo: dibujar antes de ' +
            'programar, anotar por que decidimos algo, probar en la ' +
            'red de verdad. Cuando trabajemos en serio, esto va a ' +
            'valer oro.',
          en:
            'Yes. And it rubs off. Now it comes naturally: draw ' +
            'before coding, note down why we decided something, test ' +
            'on the real network. When we work for real, this will be ' +
            'worth gold.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Sin duda', en: 'No doubt' },
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
        es: 'Casi dejo la materia. CASI.',
        en: 'I almost dropped the course. ALMOST.',
      },
      {
        es: 'Los punteros ya no me dan miedo. Bueno, menos.',
        en: 'Pointers do not scare me anymore. Well, less.',
      },
      {
        es: 'Una tarde de Pablo vale por tres clases. No le digan al profe.',
        en: 'One afternoon with Pablo equals three lectures. Do not tell the professor.',
      },
      {
        es: 'Ahora el atascado le explica a otro atascado. Cadena de favores.',
        en: 'Now the unstuck one helps the next stuck one. Pay it forward.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¡Hola! ¿Sabes que estuve a punto de retirar programacion? ' +
            'No entendia punteros ni con dibujos. Pablo me desatasco en ' +
            'una tarde. Ahora hasta me gusta. ¿Que quieres saber?',
          en:
            'Hi! You know I almost withdrew from programming? I could ' +
            'not understand pointers even with drawings. Pablo unstuck ' +
            'me in one afternoon. Now I even like it. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Como te desatasco?',
              en: 'How did he unstuck you?',
            },
            next: 'ayuda',
          },
          {
            label: {
              es: '¿Y como vas ahora?',
              en: 'How are you doing now?',
            },
            next: 'ahora',
          },
          {
            label: { es: 'Me alegro por ti', en: 'Happy for you' },
            next: null,
          },
        ],
      },
      ayuda: {
        text: {
          es:
            'No me dio la respuesta: me dio una analogia. "El puntero ' +
            'no es la casa, es la direccion escrita en un papel." ' +
            'Despues me hizo dibujar la memoria en el cuaderno, caja ' +
            'por caja, hasta que el segfault tuvo sentido.',
          en:
            'He did not give me the answer: he gave me an analogy. ' +
            '"The pointer is not the house, it is the address written ' +
            'on a note." Then he made me draw memory in my notebook, ' +
            'box by box, until the segfault made sense.',
        },
        options: [
          {
            label: {
              es: '¿Y funciono a la primera?',
              en: 'Did it work right away?',
            },
            next: 'funciono',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      funciono: {
        text: {
          es:
            'A la tercera. Pero la diferencia es que las dos primeras ' +
            'veces ENTENDI por que fallaba. Antes fallaba a ciegas; ' +
            'ahora fallo con mapa. Es otra vida.',
          en:
            'On the third try. But the difference is that the first ' +
            'two times I UNDERSTOOD why it failed. Before, I failed ' +
            'blind; now I fail with a map. It is a different life.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Gran cambio', en: 'Big change' },
            next: null,
          },
        ],
      },
      ahora: {
        text: {
          es:
            'Aprobe el parcial y ahora ayudo yo a un compañero de ' +
            'primer semestre. Pablo dice que explicarle a otro es la ' +
            'prueba final de que entendiste. Tiene razon: enseñando se ' +
            'me acomodaron las ideas.',
          en:
            'I passed the midterm and now I am helping a first-semester ' +
            'classmate myself. Pablo says explaining to someone else is ' +
            'the final proof that you understood. He is right: teaching ' +
            'put my own ideas in order.',
        },
        options: [
          {
            label: {
              es: '¿La cadena de favores?',
              en: 'The pay-it-forward chain?',
            },
            next: 'cadena',
          },
          {
            label: { es: 'Otro tema', en: 'Another topic' },
            next: 'hub',
          },
        ],
      },
      cadena: {
        text: {
          es:
            'Asi le decimos: el que fue ayudado, ayuda al siguiente. ' +
            'Empezo con Pablo y ya somos varios en la cadena. El aula ' +
            'entera funciona mejor asi.',
          en:
            'That is what we call it: whoever got helped, helps the ' +
            'next one. It started with Pablo and now several of us are ' +
            'links in the chain. The whole classroom works better this ' +
            'way.',
        },
        options: [
          {
            label: { es: 'Volvamos al inicio', en: 'Back to the start' },
            next: 'hub',
          },
          {
            label: { es: 'Hermosa costumbre', en: 'Beautiful habit' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
