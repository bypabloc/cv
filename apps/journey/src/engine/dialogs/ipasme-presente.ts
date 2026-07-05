/**
 * @module dialogs/ipasme-presente (engine)
 * @description Arboles de dialogo de la sala 2 presente: IPASME (2014),
 *   servicio de salud de los docentes donde Pablo, de junior, construyo el
 *   sistema digital de historias medicas en Java de escritorio (POO + CRUD)
 *   que reemplazo el registro en papel. 5 NPCs con los 2 enfoques del canon
 *   (informe 09): Daniela Guerra y Jose Miguel Aponte (compañeros dev),
 *   Yuleima Rondon (enfermera) y Argenis Colmenares (archivista) como
 *   personal del sitio, y el Dr. Hector Villasmil (medico/jefe). Todos
 *   anclados a la data real: levantamiento con personal medico, datos
 *   sensibles con controles de acceso, busqueda de minutos a inmediata,
 *   app de escritorio Windows sin nube en 2014.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const IPASME_PRESENTE_DIALOGS = {
  yuleima: defineDialog({
    name: { es: 'Yuleima Rondon', en: 'Yuleima Rondon' },
    chatter: [
      {
        es: 'Antes corria al archivo. Ahora corro solo en emergencias.',
        en: 'I used to run to the archive. Now I only run for emergencies.',
      },
      {
        es: 'Cedula, enter, historia. Asi de simple.',
        en: 'ID number, enter, record. That simple.',
      },
      {
        es: 'Media hora por carpeta. Eso era antes.',
        en: 'Half an hour per folder. That was before.',
      },
      {
        es: 'Yo se lo pedi a Pablo. Y Pablo cumplio.',
        en: 'I asked Pablo for it. And Pablo delivered.',
      },
      {
        es: '¿Viste la camilla? Papel nuevo, como debe ser.',
        en: 'Seen the exam table? Fresh paper, as it should be.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Bienvenido al IPASME. Soy enfermera: triaje, signos vitales y ' +
            'media vida detras de una historia medica. En 2014 un muchacho ' +
            'llamado Pablo nos cambio el oficio. ¿Que quieres saber?',
          en:
            'Welcome to IPASME. I am a nurse: triage, vital signs and half ' +
            'a life spent chasing medical records. In 2014 a young man ' +
            'called Pablo changed this job for us. What do you want to know?',
        },
        options: [
          {
            label: { es: '¿Quien es ese Pablo?', en: 'Who is this Pablo?' },
            next: 'pablo-1',
          },
          {
            label: { es: '¿Como era antes?', en: 'What was it like before?' },
            next: 'antes-1',
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
            'Claro que hay mas: el doctor Villasmil y sus datos sensibles, ' +
            'o mi resumen de todo esto. ¿Que prefieres?',
          en:
            'Of course there is more: doctor Villasmil and his sensitive ' +
            'data, or my summary of the whole thing. Which one?',
        },
        options: [
          {
            label: {
              es: '¿Datos sensibles?',
              en: 'Sensitive data?',
            },
            next: 'datos-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Ve con Argenis, el del archivador: el sabe lo que era ese ' +
            'archivo por dentro. Y dile que Yuleima ya no le debe visitas.',
          en:
            'Go see Argenis by the filing cabinet: he knows what that ' +
            'archive was like from the inside. And tell him Yuleima owes ' +
            'him no more visits.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pablo-1': {
        text: {
          es:
            'Pablo llego en 2014, joven, callado, con un cuaderno. Yo ' +
            'esperaba que se encerrara con la computadora... y se sento a ' +
            'mi lado una mañana entera a ver como atendiamos de verdad: ' +
            'turno, signos, historia, doctor.',
          en:
            'Pablo arrived in 2014, young, quiet, notebook in hand. I ' +
            'expected him to lock himself away with the computer... and he ' +
            'sat next to me for a whole morning watching how we actually ' +
            'worked: queue, vitals, record, doctor.',
        },
        options: [
          {
            label: {
              es: '¿Y que aprendio ahi?',
              en: 'And what did he learn there?',
            },
            next: 'pablo-2',
          },
          {
            label: {
              es: '¿Tu le pediste digitalizar?',
              en: 'Did you ask him to digitise?',
            },
            next: 'pedi-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Aprendio que la historia medica es el cuello de botella. El ' +
            'doctor no puede ver al paciente sin su historia, y la historia ' +
            'vivia en un archivo con decadas de carpetas. Pablo lo anoto y ' +
            'dijo: eso lo arregla una pantalla.',
          en:
            'He learned the medical record is the bottleneck. The doctor ' +
            'cannot see a patient without their record, and the record ' +
            'lived in an archive with decades of folders. Pablo wrote it ' +
            'down and said: a screen can fix that.',
        },
        options: [
          {
            label: { es: '¿Y lo arreglo?', en: 'And did he fix it?' },
            next: 'ahora-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pedi-1': {
        text: {
          es:
            'Yo se lo pedi sin adornos: "mijo, si me ahorras el viaje al ' +
            'archivo te hago un altar". Perdia media hora por paciente ' +
            'entre ir, buscar y volver. Pablo se rio... y me tomo en serio.',
          en:
            'I asked him plainly: "sweetheart, save me the trip to the ' +
            'archive and I will build you an altar". I lost half an hour ' +
            'per patient going, searching and coming back. Pablo laughed... ' +
            'and took me seriously.',
        },
        options: [
          {
            label: { es: '¿Y cumplio?', en: 'And did he deliver?' },
            next: 'ahora-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Cada paciente era un viaje: bajar al archivo, pedir la ' +
            'carpeta, esperar que apareciera. Si estaba traspapelada, la ' +
            'consulta se caia. Yo he vuelto con tres carpetas de tres ' +
            'Perez distintos y ninguna era.',
          en:
            'Every patient meant a trip: down to the archive, request the ' +
            'folder, wait for it to show up. If it was misfiled, the ' +
            'consultation collapsed. I once came back with folders for ' +
            'three different Perez and none was right.',
        },
        options: [
          {
            label: { es: '¿Tres Perez?', en: 'Three Perez?' },
            next: 'antes-2',
          },
          {
            label: { es: '¿Y ahora?', en: 'And now?' },
            next: 'ahora-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'Perez, Perez y Perez. Sin la cedula a mano, el apellido no ' +
            'alcanza. El doctor esperando, el paciente en bata y yo ' +
            'abrazada a tres carpetas equivocadas. De eso se encargo el ' +
            'buscador de Pablo.',
          en:
            'Perez, Perez and Perez. Without the ID number, a surname is ' +
            'not enough. The doctor waiting, the patient in a gown and me ' +
            'hugging three wrong folders. Pablo’s search took care of ' +
            'that.',
        },
        options: [
          {
            label: {
              es: 'Cuentame ese buscador',
              en: 'Tell me about that search',
            },
            next: 'ahora-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ahora-1': {
        text: {
          es:
            'Cumplio. Ahora meto la cedula en el mostrador y la historia ' +
            'aparece al instante: antecedentes, consultas, todo. El viaje ' +
            'al archivo se acabo; el archivo de papel quedo casi vacio.',
          en:
            'He delivered. Now I type the ID number at the front desk and ' +
            'the record shows up instantly: history, consultations, ' +
            'everything. The archive trip is over; the paper archive is ' +
            'nearly empty now.',
        },
        options: [
          {
            label: { es: '¿Que tan rapido?', en: 'How fast exactly?' },
            next: 'ahora-2',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Me quedo con eso', en: 'That is enough for me' },
            next: null,
          },
        ],
      },
      'ahora-2': {
        text: {
          es:
            'De varios minutos — y a veces una mañana — a un enter. La ' +
            'primera vez que lo vi busque a tres pacientes seguidos solo ' +
            'por gusto. Pablo estaba atras, apuntando los tiempos en su ' +
            'cuaderno.',
          en:
            'From several minutes — sometimes a whole morning — to one ' +
            'enter key. The first time I saw it I looked up three patients ' +
            'in a row just for fun. Pablo stood behind me, timing it all ' +
            'in his notebook.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy contento', en: 'I leave happy' },
            next: null,
          },
        ],
      },
      'datos-1': {
        text: {
          es:
            'Una historia medica no es un papel cualquiera: es la vida ' +
            'intima de un docente. El doctor Villasmil le exigio a Pablo ' +
            'que no la viera cualquiera, y Pablo puso claves por rol: ' +
            'medico, admision, enfermeria. A mi me parece justo.',
          en:
            'A medical record is not just any paper: it is a teacher’s ' +
            'private life. Doctor Villasmil demanded that not just anyone ' +
            'could see it, and Pablo added role-based passwords: doctor, ' +
            'admissions, nursing. Fair, if you ask me.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Mi resumen: antes yo corria y el paciente esperaba; ahora la ' +
            'historia corre y yo atiendo. Eso hizo Pablo con veintipocos ' +
            'años y un cuaderno. Imaginate lo que hace hoy.',
          en:
            'My summary: before, I ran and the patient waited; now the ' +
            'record runs and I care for people. Pablo did that in his ' +
            'early twenties with a notebook. Imagine what he does today.',
        },
        options: [
          {
            label: {
              es: 'Bien dicho. Volvamos',
              en: 'Well said. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  argenis: defineDialog({
    name: { es: 'Argenis Colmenares', en: 'Argenis Colmenares' },
    chatter: [
      {
        es: 'Me sabia el archivo de memoria. Ahora me sobra memoria.',
        en: 'I knew the archive by heart. Now my memory has spare room.',
      },
      {
        es: 'Pasillo tres, estante B... ya no hace falta.',
        en: 'Aisle three, shelf B... not needed anymore.',
      },
      {
        es: 'Un tarjeton mal puesto era un dia perdido.',
        en: 'One misplaced tracer card meant a lost day.',
      },
      {
        es: 'Estos cajones estan casi vacios. Que belleza.',
        en: 'These drawers are nearly empty. Beautiful.',
      },
      {
        es: 'Pablo me pregunto hasta como numeraba. Hasta eso.',
        en: 'Pablo even asked how I numbered folders. Even that.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Yo era el archivista: decadas de historias medicas en ' +
            'carpetas manila, cada una con su numero. Hoy cuido un ' +
            'archivador medio vacio y no lo extraño. ¿Que quieres saber?',
          en:
            'I was the archivist: decades of medical records in manila ' +
            'folders, each with its number. Today I mind a half-empty ' +
            'filing cabinet and I do not miss the old one. What do you ' +
            'want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como funcionaba el archivo?',
              en: 'How did the archive work?',
            },
            next: 'arch-1',
          },
          {
            label: {
              es: '¿Que hizo Pablo contigo?',
              en: 'What did Pablo do with you?',
            },
            next: 'pablo-1',
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
            'Queda una cosa que poca gente pregunta: que se siente cuando ' +
            'te digitalizan el oficio.',
          en:
            'One thing is left that few people ask: how it feels when ' +
            'your trade gets digitised.',
        },
        options: [
          {
            label: { es: '¿Que se siente?', en: 'How does it feel?' },
            next: 'sent-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si pasas por el pasado — la grieta esa del muro — vas a ver ' +
            'mi archivo como era. Llevate cafe. Y paciencia.',
          en:
            'If you visit the past — that rift on the wall — you will see ' +
            'my archive as it was. Bring coffee. And patience.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'arch-1': {
        text: {
          es:
            'Cada paciente, una carpeta unica con numeracion a mano. Al ' +
            'sacarla, dejabamos un tarjeton en el hueco: quien la saco y ' +
            'cuando. Ese tarjeton era todo nuestro "sistema".',
          en:
            'Each patient, one unique folder numbered by hand. When it ' +
            'left the shelf, we placed a tracer card in the gap: who took ' +
            'it and when. That card was our entire "system".',
        },
        options: [
          {
            label: {
              es: '¿Y si el tarjeton fallaba?',
              en: 'And if the card failed?',
            },
            next: 'arch-2',
          },
          {
            label: {
              es: '¿Cuantas carpetas eran?',
              en: 'How many folders were there?',
            },
            next: 'arch-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'arch-2': {
        text: {
          es:
            'Si alguien sacaba una carpeta sin tarjeton, esa historia ' +
            'estaba perdida hasta nuevo aviso. Un cero mal escrito y no la ' +
            'encontraba nadie. Yo he perdido mañanas enteras por una ' +
            'carpeta traspapelada.',
          en:
            'If someone pulled a folder without leaving the card, that ' +
            'record was lost until further notice. One badly written zero ' +
            'and nobody could find it. I have lost entire mornings to a ' +
            'misfiled folder.',
        },
        options: [
          {
            label: { es: '¿Mañanas enteras?', en: 'Entire mornings?' },
            next: 'arch-4',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'arch-3': {
        text: {
          es:
            'Decadas. El IPASME atiende a los docentes y sus familias ' +
            'desde los años cincuenta: imaginate cuantas carpetas caben en ' +
            'setenta años. El cuarto del archivo no tenia fin.',
          en:
            'Decades. IPASME has cared for teachers and their families ' +
            'since the fifties: imagine how many folders fit in seventy ' +
            'years. The archive room had no end.',
        },
        options: [
          {
            label: {
              es: '¿Y si algo fallaba?',
              en: 'And when something failed?',
            },
            next: 'arch-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'arch-4': {
        text: {
          es:
            'Cuatro medicos esperando cuatro historias y yo solo. Eso era ' +
            'un martes normal. La cola de la mañana dependia de mis ' +
            'piernas y de mi memoria. Por eso, cuando Pablo aparecio, yo ' +
            'fui el primero en hablar.',
          en:
            'Four doctors waiting on four records and just me. That was a ' +
            'normal Tuesday. The morning queue depended on my legs and my ' +
            'memory. So when Pablo showed up, I was the first to talk.',
        },
        options: [
          {
            label: { es: '¿Que le dijiste?', en: 'What did you tell him?' },
            next: 'pablo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'Pablo no empezo programando: empezo preguntando. Como ' +
            'numeraba, como prestaba, que pasaba si dos carpetas chocaban ' +
            'de numero. Apunto mi sistema de tarjetones completo antes de ' +
            'escribir una linea.',
          en:
            'Pablo did not start by coding: he started by asking. How I ' +
            'numbered, how I lent folders, what happened when two numbers ' +
            'collided. He wrote down my whole tracer-card system before ' +
            'writing a single line.',
        },
        options: [
          {
            label: {
              es: '¿Para que tanto detalle?',
              en: 'Why so much detail?',
            },
            next: 'pablo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Porque el sistema copio lo que funcionaba y elimino lo que ' +
            'dolia. La numeracion unica quedo — ahora la valida la ' +
            'computadora — y el tarjeton murio: la pantalla dice quien ' +
            'tiene que historia, siempre.',
          en:
            'Because the system kept what worked and killed what hurt. ' +
            'The unique numbering stayed — the computer validates it now ' +
            '— and the tracer card died: the screen always knows who ' +
            'holds which record.',
        },
        options: [
          {
            label: {
              es: '¿Y tu trabajo cambio?',
              en: 'And did your job change?',
            },
            next: 'hoy-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'hoy-1': {
        text: {
          es:
            'Cambio para bien. Ya no soy el cuello de botella: soy el que ' +
            'garantiza que el expediente este completo. Y cuando la ' +
            'enfermera pide una historia, no corre nadie. Eso me lo dio ' +
            'ese muchacho.',
          en:
            'It changed for the better. I am no longer the bottleneck: I ' +
            'am the one who guarantees the file is complete. And when the ' +
            'nurse needs a record, nobody runs. That kid gave me that.',
        },
        options: [
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'sent-1': {
        text: {
          es:
            'Primero miedo, no te voy a mentir: pense que sobraba. Pablo ' +
            'me dijo: "usted no sobra, usted sabe lo que la pantalla no ' +
            'sabe". Y me puso a cargar el archivo historico al sistema. ' +
            'Termine siendo el que mas registros migro.',
          en:
            'Fear first, I will not lie: I thought I was obsolete. Pablo ' +
            'told me: "you are not obsolete, you know what the screen does ' +
            'not". He put me in charge of loading the historic archive. I ' +
            'ended up migrating more records than anyone.',
        },
        options: [
          {
            label: {
              es: 'Bonita historia. Volvamos',
              en: 'Nice story. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  villasmil: defineDialog({
    name: { es: 'Dr. Hector Villasmil', en: 'Dr. Hector Villasmil' },
    chatter: [
      {
        es: 'La historia clinica es del paciente, no del curioso.',
        en: 'The medical record belongs to the patient, not the curious.',
      },
      {
        es: 'Firme el visto bueno cuando vi que seguia nuestro flujo.',
        en: 'I signed off once I saw it followed our flow.',
      },
      {
        es: 'Sin historia no hay consulta. Asi de serio.',
        en: 'No record, no consultation. That serious.',
      },
      {
        es: '¿Su cedula? Es la costumbre. Bienvenido.',
        en: 'Your ID? Force of habit. Welcome.',
      },
      {
        es: 'Del papel no extraño nada. Nada.',
        en: 'I miss nothing about paper. Nothing.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Doctor Hector Villasmil, medicina general. Cuando trajeron al ' +
            'muchacho del sistema yo era el mas esceptico... y termine ' +
            'firmando el visto bueno. ¿Que quiere saber?',
          en:
            'Doctor Hector Villasmil, general medicine. When they brought ' +
            'in the system kid I was the biggest sceptic... and I ended up ' +
            'signing the approval. What would you like to know?',
        },
        options: [
          {
            label: { es: '¿Por que esceptico?', en: 'Why the scepticism?' },
            next: 'esc-1',
          },
          {
            label: {
              es: '¿Que exigio usted?',
              en: 'What did you demand?',
            },
            next: 'datos-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, siga usted', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Puedo contarle del flujo de atencion, si le interesa la ' +
            'cocina del asunto.',
          en:
            'I can walk you through the care flow, if you like seeing ' +
            'behind the counter.',
        },
        options: [
          {
            label: { es: 'Cuenteme el flujo', en: 'Tell me the flow' },
            next: 'flujo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Cuidese. Y si va a mirar el archivo del pasado, respire hondo ' +
            'antes de entrar: el papel tenia su olor.',
          en:
            'Take care. And if you go look at the old archive, take a deep ' +
            'breath before entering: paper had its own smell.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'esc-1': {
        text: {
          es:
            'Porque la medicina esta llena de sistemas hechos por gente ' +
            'que jamas piso un consultorio. Formularios que no calzan, ' +
            'campos que sobran, y el paciente esperando mientras uno pelea ' +
            'con una pantalla.',
          en:
            'Because medicine is full of systems built by people who ' +
            'never set foot in a consulting room. Forms that do not fit, ' +
            'useless fields, and the patient waiting while you fight a ' +
            'screen.',
        },
        options: [
          {
            label: { es: '¿Y Pablo?', en: 'And Pablo?' },
            next: 'esc-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'esc-2': {
        text: {
          es:
            'Pablo hizo lo contrario: se sento en mi consulta — con ' +
            'permiso del paciente — y cronometro el flujo real: admision, ' +
            'signos, consulta, farmacia. El sistema salio con la forma de ' +
            'NUESTRO trabajo, no al reves.',
          en:
            'Pablo did the opposite: he sat in my consultations — with the ' +
            'patient’s permission — and timed the real flow: ' +
            'admissions, vitals, consultation, pharmacy. The system came ' +
            'out shaped like OUR work, not the other way around.',
        },
        options: [
          {
            label: {
              es: '¿Que exigio usted?',
              en: 'What did you demand?',
            },
            next: 'datos-1',
          },
          {
            label: {
              es: '¿Y firmo el visto bueno?',
              en: 'And you signed off?',
            },
            next: 'visto-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'datos-1': {
        text: {
          es:
            'Una sola cosa, innegociable: que la historia no la viera ' +
            'cualquiera. Datos de salud de docentes y sus familias — eso ' +
            'es sagrado. Le exigi controles de acceso y Pablo los puso: ' +
            'claves por rol y validacion de cada campo.',
          en:
            'One thing, non-negotiable: not just anyone could open a ' +
            'record. Health data of teachers and their families — that is ' +
            'sacred. I demanded access controls and Pablo built them: ' +
            'role-based passwords and validation on every field.',
        },
        options: [
          {
            label: { es: '¿Como funcionan?', en: 'How do they work?' },
            next: 'datos-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'datos-2': {
        text: {
          es:
            'Cada quien ve lo suyo: admision registra, enfermeria toma ' +
            'signos, y el detalle clinico lo vemos los medicos. Ademas el ' +
            'sistema valida los datos al entrar — se acabaron las ' +
            'historias con la edad en el campo del telefono.',
          en:
            'Everyone sees their part: admissions registers, nursing takes ' +
            'vitals, and we doctors see the clinical detail. The system ' +
            'also validates data on entry — no more records with the age ' +
            'typed into the phone field.',
        },
        options: [
          {
            label: {
              es: '¿Eso era nuevo en 2014?',
              en: 'Was that new in 2014?',
            },
            next: 'datos-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'datos-3': {
        text: {
          es:
            'Para nosotros, si. Y para el muchacho tambien: fue su primer ' +
            'contacto con datos sensibles. Años despues supe que termino ' +
            'trabajando en banca — no me extraña: el que aprende a cuidar ' +
            'una historia clinica aprende a cuidar cualquier dato.',
          en:
            'For us, yes. And for the kid too: it was his first contact ' +
            'with sensitive data. Years later I heard he ended up in ' +
            'banking — no surprise: whoever learns to guard a medical ' +
            'record learns to guard any data.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'visto-1': {
        text: {
          es:
            'Lo firme el dia que una paciente llego sin cita, de otra ' +
            'unidad, y su historia aparecio en pantalla en segundos. Antes ' +
            'eso era "vuelva mañana". Ese dia el papel perdio la ' +
            'discusion.',
          en:
            'I signed it the day a patient arrived without an appointment, ' +
            'from another unit, and her record showed on screen in ' +
            'seconds. That used to mean "come back tomorrow". Paper lost ' +
            'the argument that day.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
        ],
      },
      'flujo-1': {
        text: {
          es:
            'Turno en recepcion, admision busca la historia, enfermeria ' +
            'toma signos, el medico consulta y todo termina en farmacia o ' +
            'laboratorio. El cuello siempre fue el segundo paso: buscar la ' +
            'historia. Pablo lo volvio instantaneo y la fila entera se ' +
            'movio.',
          en:
            'Ticket at reception, admissions fetches the record, nursing ' +
            'takes vitals, the doctor consults and it all ends at pharmacy ' +
            'or the lab. The bottleneck was always step two: fetching the ' +
            'record. Pablo made it instant and the whole line moved.',
        },
        options: [
          {
            label: { es: '¿Y hoy?', en: 'And today?' },
            next: 'flujo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'flujo-2': {
        text: {
          es:
            'Hoy la consulta empieza a la hora que dice el turno. El ' +
            'paciente lo nota, aunque no sepa por que. Detras de esa ' +
            'puntualidad hay un CRUD en Java, me dijeron. Yo le digo "el ' +
            'sistema de Pablo" y todos me entienden.',
          en:
            'Today the consultation starts at the time on the ticket. ' +
            'Patients notice, even without knowing why. Behind that ' +
            'punctuality there is a CRUD in Java, they tell me. I call it ' +
            '"Pablo’s system" and everyone understands.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  daniela: defineDialog({
    name: { es: 'Daniela Guerra', en: 'Daniela Guerra' },
    chatter: [
      {
        es: 'Clase Paciente, clase Consulta, clase Historia. POO con fe.',
        en: 'Class Patient, class Consultation, class Record. OOP with faith.',
      },
      {
        es: 'Java de escritorio. En 2014 la nube quedaba lejos de aqui.',
        en: 'Desktop Java. In 2014 the cloud was far from here.',
      },
      {
        es: 'Pablo hablaba mejor con las enfermeras que conmigo. En serio.',
        en: 'Pablo talked better with the nurses than with me. Seriously.',
      },
      {
        es: 'Un CRUD limpio vale mas que mil trucos.',
        en: 'A clean CRUD beats a thousand tricks.',
      },
      {
        es: 'Aprendimos juntos. El se clavaba y yo lo seguia.',
        en: 'We learned together. He dug deep and I followed.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Daniela, desarrolladora. Con Pablo aprendimos Java en el ' +
            'mismo escritorio: el sistema de historias medicas fue nuestra ' +
            'escuela de verdad. ¿Que quieres saber?',
          en:
            'Daniela, developer. Pablo and I learned Java at the same ' +
            'desk: the medical records system was our real school. What ' +
            'do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era programar con Pablo?',
              en: 'What was coding with Pablo like?',
            },
            next: 'pablo-1',
          },
          {
            label: {
              es: '¿Por que Java de escritorio?',
              en: 'Why desktop Java?',
            },
            next: 'java-1',
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
            '¿Te cuento del dia que migramos el archivo historico? Fue ' +
            'epico y casi nos morimos.',
          en:
            'Want the story of the day we migrated the historic archive? ' +
            'Epic, and it nearly killed us.',
        },
        options: [
          { label: { es: 'Cuentame', en: 'Tell me' }, next: 'migra-1' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Pasa por el showcase junto a la puerta: la app esta viva ahi, ' +
            'con su gris Windows y todo. Dale al buscador, que era nuestro ' +
            'orgullo.',
          en:
            'Stop by the showcase next to the door: the app lives there, ' +
            'Windows grey and all. Try the search, it was our pride.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pablo-1': {
        text: {
          es:
            'Pablo se clavaba con la POO. Decia que si la clase Paciente ' +
            'estaba bien hecha, el resto del sistema salia solo. Le daba ' +
            'vueltas al modelo de datos hasta que las piezas encajaban... ' +
            'y despues programaba rapido.',
          en:
            'Pablo obsessed over OOP. He said that if the Patient class ' +
            'was well built, the rest of the system would follow. He ' +
            'turned the data model over until the pieces clicked... and ' +
            'then he coded fast.',
        },
        options: [
          {
            label: { es: '¿Y tenia razon?', en: 'And was he right?' },
            next: 'pablo-2',
          },
          {
            label: {
              es: '¿Que mas lo distinguia?',
              en: 'What else set him apart?',
            },
            next: 'gente-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Tenia razon. Paciente, Consulta, RegistroClinico: cada clase ' +
            'con su responsabilidad y el CRUD consistente en todo el ' +
            'sistema. Cuando habia que agregar un campo, se agregaba en un ' +
            'lugar y no se rompia nada. Bases solidas, como dice el.',
          en:
            'He was right. Patient, Consultation, ClinicalRecord: each ' +
            'class with its responsibility and a consistent CRUD across ' +
            'the system. Adding a field meant touching one place without ' +
            'breaking anything. Solid foundations, as he says.',
        },
        options: [
          {
            label: { es: '¿Bases para que?', en: 'Foundations for what?' },
            next: 'pablo-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-3': {
        text: {
          es:
            'Para todo lo que vino. Eso que aprendimos ahi — modelar bien, ' +
            'validar, no repetir — es ingenieria de software basica, pero ' +
            'nadie te la enseña como un sistema real con pacientes reales ' +
            'esperando en la sala.',
          en:
            'For everything that came after. What we learned there — ' +
            'model well, validate, do not repeat yourself — is basic ' +
            'software engineering, but nothing teaches it like a real ' +
            'system with real patients waiting in the lobby.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'java-1': {
        text: {
          es:
            'Porque era lo que habia y lo que servia: PCs Windows en el ' +
            'mostrador, sin internet confiable, cero nube. Una app de ' +
            'escritorio en Java con su base local era la respuesta honesta ' +
            'para 2014 aqui.',
          en:
            'Because it was what we had and what worked: Windows PCs at ' +
            'the counter, unreliable internet, zero cloud. A desktop Java ' +
            'app with a local database was the honest answer for 2014 ' +
            'here.',
        },
        options: [
          {
            label: { es: '¿Swing y todo eso?', en: 'Swing and all that?' },
            next: 'java-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'java-2': {
        text: {
          es:
            'Formularios densos, tablas con rejilla, GroupBox... la ' +
            'estetica gris de la epoca. No era bonito: era CLARO. La ' +
            'recepcionista con dos dias de practica ya volaba. Pablo decia ' +
            'que la interfaz debia parecerse a la planilla que la gente ya ' +
            'conocia.',
          en:
            'Dense forms, gridded tables, GroupBox... the grey aesthetic ' +
            'of the era. It was not pretty: it was CLEAR. The receptionist ' +
            'flew after two days of practice. Pablo said the interface ' +
            'should resemble the paper form people already knew.',
        },
        options: [
          {
            label: {
              es: '¿Y la gente lo agarro rapido?',
              en: 'Did people pick it up fast?',
            },
            next: 'gente-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'gente-1': {
        text: {
          es:
            'Rapidisimo, y ahi esta el secreto: Pablo hablaba con las ' +
            'enfermeras y los archivistas mejor que con nosotros los devs. ' +
            'Levantaba requerimientos tomando cafe. Despues volvia y me ' +
            'decia: "Daniela, el formulario va en este orden porque asi ' +
            'atienden ellos".',
          en:
            'Very fast, and there lies the secret: Pablo talked with the ' +
            'nurses and archivists better than with us devs. He gathered ' +
            'requirements over coffee. Then he would come back and say: ' +
            '"Daniela, the form goes in this order because that is how ' +
            'they work".',
        },
        options: [
          {
            label: {
              es: '¿Eso es levantar requerimientos?',
              en: 'Is that requirements gathering?',
            },
            next: 'gente-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'gente-2': {
        text: {
          es:
            'Eso ES levantar requerimientos: entender el flujo real antes ' +
            'de escribir codigo. Yo aprendi Java con Pablo, pero eso otro ' +
            '— escuchar primero — fue la leccion mas cara que me lleve ' +
            'gratis.',
          en:
            'That IS requirements gathering: understanding the real flow ' +
            'before writing code. I learned Java with Pablo, but that ' +
            'other thing — listening first — was the most expensive lesson ' +
            'I got for free.',
        },
        options: [
          {
            label: {
              es: 'Bonito. Volvamos',
              en: 'Nice. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'migra-1': {
        text: {
          es:
            'Decadas de carpetas manila que habia que volver registros ' +
            'digitales. Argenis dictaba, nosotros cargabamos, el validador ' +
            'de Pablo escupia errores de fechas imposibles... Semanas asi. ' +
            'El dia que el contador llego a cero pendientes, Argenis ' +
            'abrazo el archivador.',
          en:
            'Decades of manila folders had to become digital records. ' +
            'Argenis dictated, we typed, Pablo’s validator spat out ' +
            'impossible-date errors... Weeks of that. The day the pending ' +
            'counter hit zero, Argenis hugged the filing cabinet.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  josemiguel: defineDialog({
    name: { es: 'Jose Miguel Aponte', en: 'Jose Miguel Aponte' },
    chatter: [
      {
        es: 'PC del mostrador tres: instalada. Faltan cero.',
        en: 'Counter PC number three: installed. Zero left.',
      },
      {
        es: 'Java en Windows, maquina por maquina. Asi era 2014.',
        en: 'Java on Windows, machine by machine. That was 2014.',
      },
      {
        es: 'Yo reportaba bugs y Pablo decia: gracias. GRACIAS.',
        en: 'I reported bugs and Pablo said: thanks. THANKS.',
      },
      {
        es: '¿Nube? Aqui la unica nube era la del aguacero.',
        en: 'Cloud? The only cloud here came with the rain.',
      },
      {
        es: 'Si la maquina prende, el sistema corre. Esa era la promesa.',
        en: 'If the machine boots, the system runs. That was the promise.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Jose Miguel, desarrollo y soporte. Yo instalaba el sistema en ' +
            'cada PC del instituto y probaba todo lo que Pablo construia. ' +
            '¿Que quieres saber?',
          en:
            'Jose Miguel, development and support. I installed the system ' +
            'on every PC in the institute and tested everything Pablo ' +
            'built. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como se instalaba?',
              en: 'How was it installed?',
            },
            next: 'insta-1',
          },
          {
            label: {
              es: '¿Como era Pablo con los bugs?',
              en: 'How was Pablo with bugs?',
            },
            next: 'bugs-1',
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
          es: '¿Te cuento mi prueba favorita? La del corte de luz.',
          en: 'Want my favourite test? The power-cut one.',
        },
        options: [
          { label: { es: 'Dale', en: 'Go ahead' }, next: 'luz-1' },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Cualquier cosa, aqui estoy: siempre hay una PC mas que ' +
            'atender. Antes de irte, mira el monitor del mostrador — esa ' +
            'ficha la instale yo.',
          en:
            'If you need anything, I am here: there is always one more PC ' +
            'to service. Before you go, check the counter monitor — I ' +
            'installed that very screen.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'insta-1': {
        text: {
          es:
            'A la antigua: maquina por maquina. App de escritorio Java ' +
            'para Windows con su base de datos local — en 2014, y aqui, no ' +
            'habia nube que valiera. Mostrador, consultorios, admision: ' +
            'cada PC su instalacion y su prueba.',
          en:
            'The old way: machine by machine. A desktop Java app for ' +
            'Windows with its local database — in 2014, and here, no cloud ' +
            'was an option. Counter, consulting rooms, admissions: every ' +
            'PC got its install and its test.',
        },
        options: [
          {
            label: {
              es: '¿Y las actualizaciones?',
              en: 'And the updates?',
            },
            next: 'insta-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'insta-2': {
        text: {
          es:
            'Version nueva, ronda nueva. Yo cargaba el instalador y un ' +
            'checklist de Pablo: abrir ficha, buscar historia, registrar ' +
            'consulta. Si algo fallaba en la PC vieja de admision — porque ' +
            'siempre era esa — anotaba y volviamos.',
          en:
            'New version, new round. I carried the installer and a ' +
            'checklist from Pablo: open a file, search a record, register ' +
            'a consultation. If something failed on the old admissions PC ' +
            '— it was always that one — I noted it and we went back.',
        },
        options: [
          {
            label: { es: '¿Y fallaba mucho?', en: 'Did it fail often?' },
            next: 'bugs-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bugs-1': {
        text: {
          es:
            'Fallaba lo normal, y ahi Pablo me sorprendio: yo le llegaba ' +
            'con la lista de bugs y el la recibia sin ponerse a la ' +
            'defensiva. Ni una excusa. Los anotaba, preguntaba como ' +
            'reproducirlos y al dia siguiente aparecian corregidos.',
          en:
            'It failed the normal amount, and that is where Pablo ' +
            'surprised me: I would arrive with my bug list and he took it ' +
            'without getting defensive. Not one excuse. He noted them, ' +
            'asked how to reproduce them, and next day they were fixed.',
        },
        options: [
          {
            label: { es: '¿Eso es raro?', en: 'Is that unusual?' },
            next: 'bugs-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bugs-2': {
        text: {
          es:
            'Rarisimo. Todos defienden su codigo como si fuera un hijo. ' +
            'Pablo defendia el SISTEMA: si el bug existia, era mas ' +
            'importante que su orgullo. Con esa actitud, el que reporta se ' +
            'anima a reportar mas. Terminamos puliendolo entre todos.',
          en:
            'Very unusual. Everyone defends their code like a child. ' +
            'Pablo defended the SYSTEM: if the bug existed, it mattered ' +
            'more than his pride. With that attitude, reporters dare to ' +
            'report more. We ended up polishing it together.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'luz-1': {
        text: {
          es:
            'Se fue la luz a mitad de un registro — cosa comun — y cuando ' +
            'volvio, la historia estaba completa: nada corrupto, nada ' +
            'perdido. La base local aguanto. Pablo habia validado y ' +
            'guardado por pasos justo para eso. Ese dia le crei todo.',
          en:
            'The power died mid-record — a common thing — and when it came ' +
            'back, the record was intact: nothing corrupted, nothing lost. ' +
            'The local database held. Pablo had validated and saved in ' +
            'steps exactly for that. I believed everything he said after ' +
            'that day.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
