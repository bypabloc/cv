/**
 * @module dialogs/ipasme-pasado (engine)
 * @description Arboles de dialogo de la sala 2 pasado: IPASME (2014) antes
 *   del sistema. El Departamento de Historias Medicas en papel: decadas de
 *   carpetas manila con numeracion a mano, tarjetones en los huecos,
 *   busquedas de varios minutos por paciente y una cola que no baja. 3 NPCs
 *   frustrados (canon, informe 09): Argenis Colmenares hurgando el archivo
 *   (cuatro medicos esperando), Yuleima Rondon cargando carpetas de los
 *   tres Perez, y Petra Salazar en recepcion viendo crecer la cola. Argenis
 *   y Yuleima reaparecen en el presente: el arco antes/despues del sistema.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const IPASME_PASADO_DIALOGS = {
  argenis: defineDialog({
    name: { es: 'Argenis Colmenares', en: 'Argenis Colmenares' },
    chatter: [
      {
        es: 'Cuatro medicos, cuatro historias, un archivista.',
        en: 'Four doctors, four records, one archivist.',
      },
      {
        es: 'Pasillo tres, estante B, tercera fila... creo.',
        en: 'Aisle three, shelf B, third row... I think.',
      },
      {
        es: '¿Y este hueco? ¿QUIEN saco esta carpeta?',
        en: 'And this gap? WHO pulled this folder?',
      },
      {
        es: 'Un cero mal puesto y se pierde una vida de consultas.',
        en: 'One bad zero and a lifetime of visits goes missing.',
      },
      {
        es: 'No me toquen las pilas, que tienen orden. Mi orden.',
        en: 'Do not touch the stacks, they have order. My order.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Este es el archivo de historias medicas del IPASME: decadas ' +
            'de carpetas manila y un solo yo. Si buscas algo, formate; si ' +
            'preguntas, rapido, que tengo cuatro medicos esperando.',
          en:
            'This is the IPASME medical records archive: decades of ' +
            'manila folders and just one of me. If you need something, ' +
            'queue up; if you have questions, be quick, four doctors are ' +
            'waiting on me.',
        },
        options: [
          {
            label: {
              es: '¿Como encuentras una carpeta?',
              en: 'How do you find a folder?',
            },
            next: 'num-1',
          },
          {
            label: {
              es: '¿Que es ese hueco con tarjeton?',
              en: 'What is that gap with a card?',
            },
            next: 'tarj-1',
          },
          {
            label: {
              es: '¿Siempre es asi el dia?',
              en: 'Is every day like this?',
            },
            next: 'dia-1',
          },
          {
            label: { es: 'Me voy. Suerte', en: 'I will go. Good luck' },
            next: null,
          },
        ],
      },
      'num-1': {
        text: {
          es:
            'Numeracion unica escrita a mano: cada paciente su numero, ' +
            'cada numero su carpeta. Yo me se el archivo de memoria — ' +
            'pasillo, estante, altura. El problema no soy yo: es que la ' +
            'mano escribe y la mano se equivoca.',
          en:
            'Unique numbering written by hand: each patient a number, ' +
            'each number a folder. I know this archive by heart — aisle, ' +
            'shelf, height. I am not the problem: the hand writes and the ' +
            'hand makes mistakes.',
        },
        options: [
          {
            label: {
              es: '¿Y si se equivoca?',
              en: 'And when it does?',
            },
            next: 'num-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'num-2': {
        text: {
          es:
            'Un cero mal puesto y la carpeta queda enterrada donde nadie ' +
            'la busca. La historia existe, el paciente existe... pero no ' +
            'se encuentran. Eso puede tardar dias en aparecer. O no ' +
            'aparecer.',
          en:
            'One bad zero and the folder gets buried where nobody looks. ' +
            'The record exists, the patient exists... but they never ' +
            'meet. That can take days to surface. Or never surface.',
        },
        options: [
          {
            label: {
              es: '¿No hay otra forma?',
              en: 'Is there no other way?',
            },
            next: 'num-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'num-3': {
        text: {
          es:
            'Dicen que en otros lados hay computadoras para esto. Aqui hay ' +
            'un muchacho nuevo que anda preguntando como numero y como ' +
            'presto las carpetas. Anota todo en un cuaderno. No se que ' +
            'trama, pero pregunta bien.',
          en:
            'They say other places have computers for this. Here there is ' +
            'a new kid going around asking how I number and how I lend ' +
            'folders. Writes everything in a notebook. No idea what he is ' +
            'up to, but he asks the right questions.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Ojala funcione', en: 'Hope it works out' },
            next: null,
          },
        ],
      },
      'tarj-1': {
        text: {
          es:
            'El tarjeton es nuestra ley: cuando una carpeta sale, dejo un ' +
            'tarjeton en su hueco con quien la tiene y desde cuando. Ese ' +
            'hueco de ahi tiene tarjeton... y la carpeta no vuelve desde ' +
            'hace dos semanas.',
          en:
            'The tracer card is our law: when a folder leaves, I place a ' +
            'card in its gap saying who has it and since when. That gap ' +
            'over there has its card... and the folder has not come back ' +
            'in two weeks.',
        },
        options: [
          {
            label: {
              es: '¿Y eso que significa?',
              en: 'And what does that mean?',
            },
            next: 'tarj-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'tarj-2': {
        text: {
          es:
            'Significa que la historia de ese docente esta de paseo. Si el ' +
            'vuelve a consulta hoy, no hay historia: a reconstruir de ' +
            'memoria o a esperar. Un tarjeton mal puesto — o ignorado — es ' +
            'una historia perdida.',
          en:
            'It means that teacher’s record is out wandering. If he ' +
            'comes back for a consultation today, there is no record: ' +
            'rebuild it from memory or wait. A misplaced — or ignored — ' +
            'tracer card is a lost record.',
        },
        options: [
          {
            label: {
              es: 'Que sistema tan fragil',
              en: 'Such a fragile system',
            },
            next: 'frag-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'frag-1': {
        text: {
          es:
            'Fragil, pero es el que hay. Setenta años de expedientes no se ' +
            'cargan solos a ninguna computadora. Aunque el muchacho ese ' +
            'del cuaderno diga que si...',
          en:
            'Fragile, but it is what we have. Seventy years of files do ' +
            'not load themselves into any computer. Even if that notebook ' +
            'kid says otherwise...',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Animo', en: 'I will go. Hang in there' },
            next: null,
          },
        ],
      },
      'dia-1': {
        text: {
          es:
            'Hoy es un martes normal: cuatro medicos esperando cuatro ' +
            'historias y soy uno solo. Si una carpeta esta traspapelada, ' +
            'se acabo mi mañana. La cola de alla afuera no baja porque yo ' +
            'no doy mas.',
          en:
            'Today is a normal Tuesday: four doctors waiting on four ' +
            'records and there is only one of me. If a folder is misfiled, ' +
            'my morning is over. The queue out there never shrinks because ' +
            'I cannot go any faster.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Animo con eso', en: 'Hang in there' }, next: null },
        ],
      },
    },
  }),

  yuleima: defineDialog({
    name: { es: 'Yuleima Rondon', en: 'Yuleima Rondon' },
    chatter: [
      {
        es: 'Tres Perez y ninguna carpeta es la buena.',
        en: 'Three Perez and none of the folders is right.',
      },
      {
        es: 'El doctor espera, el paciente espera... y yo corro.',
        en: 'The doctor waits, the patient waits... and I run.',
      },
      {
        es: 'Media consulta se va en buscar un papel.',
        en: 'Half the consultation goes into chasing paper.',
      },
      {
        es: 'Ay, mis piernas. Este archivo me las va a cobrar.',
        en: 'Oh, my legs. This archive will bill me for them.',
      },
      {
        es: '¿Otra historia? Voy. Otra vez.',
        en: 'Another record? Going. Again.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Soy la enfermera de medicina general... y la mensajera del ' +
            'archivo, parece. Cada consulta empieza conmigo bajando por ' +
            'una carpeta. ¿Que quieres?',
          en:
            'I am the general medicine nurse... and the archive courier, ' +
            'apparently. Every consultation starts with me going down for ' +
            'a folder. What do you need?',
        },
        options: [
          {
            label: {
              es: '¿Por que corres tanto?',
              en: 'Why all the running?',
            },
            next: 'corre-1',
          },
          {
            label: {
              es: '¿Que paso con los Perez?',
              en: 'What happened with the Perez?',
            },
            next: 'perez-1',
          },
          {
            label: { es: 'Me voy. Animo', en: 'I will go. Hang in there' },
            next: null,
          },
        ],
      },
      'corre-1': {
        text: {
          es:
            'El doctor no puede atender sin la historia, y la historia ' +
            'vive alla abajo, en el reino de Argenis. Ir, pedir, esperar, ' +
            'volver: media consulta en el viaje. Multiplica eso por todos ' +
            'los pacientes del dia.',
          en:
            'The doctor cannot see anyone without the record, and the ' +
            'record lives down there, in Argenis’s kingdom. Go, ' +
            'request, wait, return: half a consultation spent on the ' +
            'trip. Multiply that by every patient of the day.',
        },
        options: [
          {
            label: {
              es: '¿Y no se puede mejorar?',
              en: 'Can it not be improved?',
            },
            next: 'corre-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'corre-2': {
        text: {
          es:
            'Yo que se... dicen que un muchacho anda mirando como ' +
            'trabajamos, con un cuaderno. Yo le dije: mijo, si me ahorras ' +
            'el viaje al archivo, te hago un altar. Se rio. Ojala no se ' +
            'este riendo de mi.',
          en:
            'How would I know... they say some kid is studying how we ' +
            'work, notebook and all. I told him: sweetheart, save me the ' +
            'archive trip and I will build you an altar. He laughed. I ' +
            'hope he is not laughing at me.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Algo me dice que no',
              en: 'Something tells me he is not',
            },
            next: null,
          },
        ],
      },
      'perez-1': {
        text: {
          es:
            'El doctor me manda por la historia del señor Perez. Bajo. Hay ' +
            'TRES Perez. Subo con las tres carpetas y ninguna es: era ' +
            'Peres, con ese. El paciente ya se habia ido. Eso fue ayer.',
          en:
            'The doctor sends me for Mr Perez’s record. I go down. ' +
            'There are THREE Perez. I come back with all three folders ' +
            'and none is right: it was Peres, with an s. The patient had ' +
            'already left. That was yesterday.',
        },
        options: [
          {
            label: { es: '¿Pasa seguido?', en: 'Does it happen often?' },
            next: 'perez-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'perez-2': {
        text: {
          es:
            'Cada semana. Sin el numero de historia a la mano, el apellido ' +
            'no alcanza y las carpetas no opinan. Necesitariamos... no se, ' +
            'algo que busque por cedula y no se equivoque.',
          en:
            'Every week. Without the record number at hand, a surname is ' +
            'not enough and folders do not talk. We would need... I do ' +
            'not know, something that searches by ID and never gets it ' +
            'wrong.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Ya llegara', en: 'It will come' }, next: null },
        ],
      },
    },
  }),

  petra: defineDialog({
    name: { es: 'Petra Salazar', en: 'Petra Salazar' },
    chatter: [
      {
        es: 'La cola no baja. No baja nunca.',
        en: 'The queue never shrinks. Never.',
      },
      {
        es: 'Turno 84... y van por el 51.',
        en: 'Ticket 84... and they are on 51.',
      },
      {
        es: 'Si el archivo cierra, no hay atencion. Asi de simple.',
        en: 'If the archive closes, nobody gets seen. That simple.',
      },
      {
        es: 'Docentes y familiares, todos esperan lo mismo: su carpeta.',
        en: 'Teachers and families, all waiting for the same: their folder.',
      },
      {
        es: 'Diez minutos por historia. Sumale la cola.',
        en: 'Ten minutes per record. Add the queue on top.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Recepcion del IPASME, buenos dias. Turnos, afiliados y ' +
            'paciencia: de eso vivo. ¿Que necesitas?',
          en:
            'IPASME reception, good morning. Tickets, members and ' +
            'patience: that is my trade. What do you need?',
        },
        options: [
          {
            label: {
              es: '¿Por que la cola es tan larga?',
              en: 'Why is the queue so long?',
            },
            next: 'cola-1',
          },
          {
            label: {
              es: '¿Quienes se atienden aqui?',
              en: 'Who gets seen here?',
            },
            next: 'afil-1',
          },
          {
            label: { es: 'Me voy. Paciencia', en: 'I will go. Patience' },
            next: null,
          },
        ],
      },
      'cola-1': {
        text: {
          es:
            'Cada afiliado son diez minutos de buscar su historia antes de ' +
            'que lo vean. Diez minutos que se apilan: a las nueve de la ' +
            'mañana ya llevamos una hora de retraso. Y si el archivo ' +
            'cierra, no hay atencion — asi de simple.',
          en:
            'Every member means ten minutes of record-hunting before they ' +
            'are seen. Ten minutes that pile up: by nine in the morning ' +
            'we are already an hour behind. And if the archive closes, ' +
            'nobody gets seen — that simple.',
        },
        options: [
          {
            label: {
              es: '¿El archivo manda tanto?',
              en: 'Does the archive rule everything?',
            },
            next: 'cola-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cola-2': {
        text: {
          es:
            'Manda todo. La consulta no existe sin la historia. Por eso ' +
            'cuando se traspapela una carpeta la gente se molesta conmigo ' +
            '— como si yo la hubiera escondido. Yo solo doy los turnos, ' +
            'mi amor.',
          en:
            'It rules everything. No record, no consultation. That is why ' +
            'people get angry at me when a folder is misfiled — as if I ' +
            'had hidden it myself. I just hand out tickets, dear.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Paciencia', en: 'Patience' }, next: null },
        ],
      },
      'afil-1': {
        text: {
          es:
            'Docentes del Ministerio de Educacion y sus familias. Miles y ' +
            'miles: esto atiende muchisima gente al dia entre medicina, ' +
            'odontologia y laboratorio. Cada uno con su expediente en ' +
            'papel. Por ahora.',
          en:
            'Ministry of Education teachers and their families. Thousands ' +
            'upon thousands: this place sees a lot of people daily across ' +
            'medicine, dentistry and the lab. Each with a paper file. For ' +
            'now.',
        },
        options: [
          {
            label: { es: '¿Por ahora?', en: 'For now?' },
            next: 'afil-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'afil-2': {
        text: {
          es:
            'Rumores. Que viene un sistema, que las carpetas van a vivir ' +
            'en una computadora, que un muchacho anda midiendo los tiempos ' +
            'de la cola. Yo lo he visto: apunta todo. Si eso baja la cola, ' +
            'yo le pongo su nombre a un turno.',
          en:
            'Rumours. A system is coming, folders will live inside a ' +
            'computer, some kid is out there timing the queue. I have ' +
            'seen him: he writes everything down. If that shortens the ' +
            'queue, I will name a ticket after him.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Ojala', en: 'Hopefully' }, next: null },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
