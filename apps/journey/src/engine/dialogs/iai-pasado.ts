/**
 * @module dialogs/iai-pasado (engine)
 * @description Arboles de dialogo de la sala 3 pasado: IAI (2015) antes
 *   del sistema. La oficina tecnica de obra publica en Excel y papel:
 *   APUs que se rehacen a mano con cada publicacion de indices del BCV,
 *   valuaciones en tres papeles que no cuadran, el consolidado que tarda
 *   jornadas y la carpeta de obra que nadie encuentra. 3 NPCs frustrados
 *   (canon, informe 16): Belkis Camacaro rehaciendo cuarenta APU, el Ing.
 *   Gregorio Salcedo con la valuacion de la calle 19 repartida en papeles,
 *   y Pastor Rivas, maestro de obra, esperando la firma para que le paguen
 *   a su gente. Belkis y Gregorio reaparecen en el presente usando el
 *   sistema: el arco antes/despues.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const IAI_PASADO_DIALOGS = {
  belkis: defineDialog({
    name: { es: 'Belkis Camacaro', en: 'Belkis Camacaro' },
    chatter: [
      {
        es: 'Indices nuevos del BCV. Otra vez. OTRA VEZ.',
        en: 'New BCV indexes. Again. AGAIN.',
      },
      {
        es: 'Cuarenta APU a mano. Cuarenta.',
        en: 'Forty unit-price analyses by hand. Forty.',
      },
      {
        es: 'Si me equivoco en un numero, se firma mal el presupuesto.',
        en: 'One wrong digit and the budget gets signed wrong.',
      },
      {
        es: 'La calculadora ya no da mas. Yo tampoco.',
        en: 'The calculator has had it. So have I.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Que? Perdon, estoy contando. El BCV publico indices nuevos ' +
            'esta mañana. ¿Sabes que significa eso? Cuarenta APU. A mano. ' +
            'Otra vez. Habla rapido que pierdo la cuenta.',
          en:
            'What? Sorry, I am counting. The BCV published new indexes ' +
            'this morning. Do you know what that means? Forty unit-price ' +
            'analyses. By hand. Again. Talk fast, I am losing count.',
        },
        options: [
          {
            label: {
              es: '¿Por que a mano?',
              en: 'Why by hand?',
            },
            next: 'mano-1',
          },
          {
            label: {
              es: '¿Y si te equivocas?',
              en: 'And if you make a mistake?',
            },
            next: 'error-1',
          },
          {
            label: { es: 'Te dejo contar', en: 'I will let you count' },
            next: null,
          },
        ],
      },
      'mano-1': {
        text: {
          es:
            'Porque cada APU es una hojita con materiales, mano de obra y ' +
            'equipos, y cuando el indice cambia, cambia TODO: cada ' +
            'precio, cada subtotal, cada porcentaje. Y el Excel de la PC ' +
            'vieja no es de fiar — cada quien tiene su copia distinta.',
          en:
            'Because every analysis is a sheet of materials, labour and ' +
            'equipment, and when the index moves, EVERYTHING moves: every ' +
            'price, every subtotal, every percentage. And the spreadsheet ' +
            'on the old PC cannot be trusted — everyone has a different ' +
            'copy.',
        },
        options: [
          {
            label: {
              es: '¿Cuanto te toma?',
              en: 'How long does it take?',
            },
            next: 'tiempo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'tiempo-1': {
        text: {
          es:
            'Una semana, si nadie me interrumpe. Y siempre me ' +
            'interrumpen: que el inspector necesita un numero, que la ' +
            'presidenta pide el consolidado... El presupuesto de la via ' +
            'agricola lleva TRES actualizaciones este año.',
          en:
            'A week, if nobody interrupts me. And they always do: the ' +
            'inspector needs a figure, the president wants the ' +
            'consolidated report... The rural road budget has been redone ' +
            'THREE times this year.',
        },
        options: [
          {
            label: {
              es: '¿Nadie puede ayudarte?',
              en: 'Can nobody help you?',
            },
            next: 'ayuda-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'error-1': {
        text: {
          es:
            'Si me equivoco en UN numero, el error se arrastra por todo ' +
            'el presupuesto y la presidenta firma una resolucion mal ' +
            'calculada. Despues aparece la contraloria preguntando, y la ' +
            'que dio el precio fui yo. Ese es el peso que cargo cada vez.',
          en:
            'If I get ONE digit wrong, the error drags through the whole ' +
            'budget and the president signs a miscalculated resolution. ' +
            'Then the comptroller comes asking, and the one who priced it ' +
            'was me. That is the weight I carry every time.',
        },
        options: [
          {
            label: {
              es: '¿Nadie puede ayudarte?',
              en: 'Can nobody help you?',
            },
            next: 'ayuda-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'ayuda-1': {
        text: {
          es:
            'Dicen que unos tesistas de la universidad andan proponiendo ' +
            'un sistema para esto. Un muchacho Pablo, que pregunta mucho ' +
            'y anota todo. Yo le dije: si me quitas los indices de ' +
            'encima, te enseño el oficio completo. Veremos.',
          en:
            'Word is some thesis students from the university are ' +
            'proposing a system for this. A kid called Pablo, who asks a ' +
            'lot and writes everything down. I told him: take the indexes ' +
            'off my back and I will teach you the whole trade. We shall ' +
            'see.',
        },
        options: [
          {
            label: { es: 'Ojala cumplan', en: 'Hope they deliver' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si cruzas de vuelta al presente, me cuentas como me fue. ' +
            'Ahora si, dejame: voy por el APU numero doce.',
          en:
            'If you cross back to the present, tell me how it went for ' +
            'me. Now really, let me be: I am on analysis number twelve.',
        },
        options: [{ label: { es: 'Suerte', en: 'Good luck' }, next: null }],
      },
    },
  }),

  gregorio: defineDialog({
    name: { es: 'Ing. Gregorio Salcedo', en: 'Eng. Gregorio Salcedo' },
    chatter: [
      {
        es: 'Tres papeles, tres montos, una sola calle.',
        en: 'Three papers, three amounts, one single street.',
      },
      {
        es: 'Mi Excel no cuadra con el de presupuestos. Como siempre.',
        en: 'My spreadsheet does not match the budget one. As usual.',
      },
      {
        es: 'La presidenta quiere el consolidado para el viernes.',
        en: 'The president wants the consolidated report by Friday.',
      },
      {
        es: '¿Alguien vio la carpeta de la via agricola?',
        en: 'Has anyone seen the rural road folder?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Tengo la valuacion de la calle 19 en tres papeles distintos ' +
            'y ninguno cuadra con mi Excel. Y la presidenta quiere el ' +
            'consolidado de todas las obras para el viernes. ¿Tu que ' +
            'necesitas?',
          en:
            'I have the street 19 valuation on three different papers and ' +
            'none of them matches my spreadsheet. And the president wants ' +
            'the consolidated report of every job by Friday. What do you ' +
            'need?',
        },
        options: [
          {
            label: {
              es: '¿Tres papeles distintos?',
              en: 'Three different papers?',
            },
            next: 'papeles-1',
          },
          {
            label: {
              es: '¿Y el consolidado?',
              en: 'And the consolidated report?',
            },
            next: 'consolidado-1',
          },
          {
            label: { es: 'Lo dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'papeles-1': {
        text: {
          es:
            'La hoja de medicion que hice en la obra, la copia que paso a ' +
            'limpio en la oficina y la planilla que me devolvio ' +
            'presupuestos. Tres versiones del mismo avance, cada una con ' +
            'un monto. ¿Cual firmo? Porque mi firma es la que vale.',
          en:
            'The measurement sheet I made on site, the clean copy I wrote ' +
            'at the office and the sheet the budget desk sent back. Three ' +
            'versions of the same progress, each with its own amount. ' +
            'Which one do I sign? Because my signature is the one that ' +
            'counts.',
        },
        options: [
          {
            label: {
              es: '¿Y mientras no firmas?',
              en: 'And while you do not sign?',
            },
            next: 'firma-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'firma-1': {
        text: {
          es:
            'Mientras yo no conformo la valuacion, el contratista no ' +
            'cobra y su gente tampoco. Ahi afuera esta Pastor, el maestro ' +
            'de obra, dando vueltas por su plata. No es que yo quiera ' +
            'demorar: es que no puedo firmar numeros que no cuadran.',
          en:
            'Until I sign off the valuation, the contractor does not get ' +
            'paid and neither do his people. Pastor, the site foreman, is ' +
            'out there circling for his money. It is not that I want to ' +
            'delay: I just cannot sign numbers that do not match.',
        },
        options: [
          {
            label: {
              es: '¿Que lo arreglaria?',
              en: 'What would fix it?',
            },
            next: 'arreglo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'consolidado-1': {
        text: {
          es:
            'El consolidado es copiar los numeros de CADA obra, carpeta ' +
            'por carpeta, a una planilla. Jornadas enteras. Y cuando ' +
            'termine, los primeros numeros ya van a estar viejos. Asi no ' +
            'se dirige un instituto, pero es lo que hay.',
          en:
            'The consolidated report means copying the numbers of EVERY ' +
            'job, folder by folder, into one sheet. Whole workdays. And by ' +
            'the time I finish, the first numbers will already be stale. ' +
            'That is no way to run an institute, but it is what we have.',
        },
        options: [
          {
            label: {
              es: '¿Que lo arreglaria?',
              en: 'What would fix it?',
            },
            next: 'arreglo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'arreglo-1': {
        text: {
          es:
            'Un solo lugar donde vivan los numeros. Uno. Que la medicion ' +
            'que cargo yo sea la misma que ve presupuestos y la misma que ' +
            'suma el consolidado. Los tesistas de Pablo andan ofreciendo ' +
            'justo eso. Si lo logran, les firmo lo que quieran.',
          en:
            'One single place where the numbers live. One. The ' +
            'measurement I enter being the same one the budget desk sees ' +
            'and the same one the consolidated report adds up. Pablo’s ' +
            'thesis crew is offering exactly that. If they pull it off, I ' +
            'will sign whatever they want.',
        },
        options: [
          {
            label: { es: 'Cruzare a ver', en: 'I will cross over and see' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si ves a Pastor, dile que estoy en eso. La calle 19 se va a ' +
            'pagar — cuando los numeros cuadren.',
          en:
            'If you see Pastor, tell him I am on it. Street 19 will get ' +
            'paid — once the numbers match.',
        },
        options: [{ label: { es: 'Le digo', en: 'Will do' }, next: null }],
      },
    },
  }),

  pastor: defineDialog({
    name: { es: 'Pastor Rivas', en: 'Pastor Rivas' },
    chatter: [
      {
        es: 'Tercer viaje esta semana. TERCERO.',
        en: 'Third trip this week. THIRD.',
      },
      {
        es: 'La cuadrilla pregunta y yo no tengo respuesta.',
        en: 'The crew keeps asking and I have no answer.',
      },
      {
        es: 'La obra esta lista. El papel es lo que falta.',
        en: 'The works are done. It is the paper that is missing.',
      },
      {
        es: 'Sin firma no hay pago. Y sin pago no hay comida.',
        en: 'No signature, no pay. And no pay, no food on the table.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Buenas. Pastor Rivas, maestro de obra de la calle 19. Vine a ' +
            'ver si conformaron la valuacion, porque hasta que no la ' +
            'firmen, a mi gente no le pagan. Llevo tres viajes esta ' +
            'semana. ¿Tu sabes algo?',
          en:
            'Morning. Pastor Rivas, site foreman on street 19. I came to ' +
            'see if the valuation got signed off, because until it is, my ' +
            'people do not get paid. Three trips this week already. Do you ' +
            'know anything?',
        },
        options: [
          {
            label: {
              es: '¿Por que tarda tanto?',
              en: 'Why does it take so long?',
            },
            next: 'tarda-1',
          },
          {
            label: {
              es: '¿Como esta tu cuadrilla?',
              en: 'How is your crew doing?',
            },
            next: 'cuadrilla-1',
          },
          {
            label: { es: 'No se nada, disculpa', en: 'I know nothing, sorry' },
            next: null,
          },
        ],
      },
      'tarda-1': {
        text: {
          es:
            'Porque los numeros andan repartidos en papeles. El ingeniero ' +
            'Gregorio no es flojo — es el mas serio de aqui —, pero tiene ' +
            'la valuacion en tres hojas que no cuadran y no va a firmar a ' +
            'ciegas. Y mientras las cuadra, mi gente espera.',
          en:
            'Because the numbers are scattered across papers. Engineer ' +
            'Gregorio is no slacker — he is the most serious man here — ' +
            'but the valuation sits on three sheets that do not match and ' +
            'he will not sign blind. And while he squares them, my people ' +
            'wait.',
        },
        options: [
          {
            label: {
              es: '¿La obra si esta lista?',
              en: 'Is the work actually done?',
            },
            next: 'obra-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'obra-1': {
        text: {
          es:
            'Lista y bien hecha: el asfaltado quedo parejo, con sus ' +
            'pendientes y sus drenajes. La obra fisica avanza mas rapido ' +
            'que el papeleo — esa es la verdad de este pais. Lo que se ' +
            'tranca no es el cemento, son las planillas.',
          en:
            'Done and done well: the asphalt came out even, slopes and ' +
            'drains in place. The physical works move faster than the ' +
            'paperwork — that is the truth around here. It is not the ' +
            'cement that jams, it is the forms.',
        },
        options: [
          {
            label: {
              es: '¿Y que esperas que pase?',
              en: 'What do you hope happens?',
            },
            next: 'espera-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'cuadrilla-1': {
        text: {
          es:
            'Aguantando. Son doce hombres con familia, y la quincena ' +
            'depende de una firma que depende de unos papeles que no ' +
            'aparecen. Yo doy la cara por ellos, por eso vengo yo y no ' +
            'mando a nadie. Pero ya no se que decirles.',
          en:
            'Holding on. Twelve men with families, and the fortnight’s ' +
            'pay depends on a signature that depends on papers that do ' +
            'not show up. I answer for them, that is why I come myself ' +
            'instead of sending someone. But I am running out of things ' +
            'to tell them.',
        },
        options: [
          {
            label: {
              es: '¿Y que esperas que pase?',
              en: 'What do you hope happens?',
            },
            next: 'espera-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'espera-1': {
        text: {
          es:
            'Que algun dia esto sea apretar un boton: la medicion entra, ' +
            'el cuadro sale, el ingeniero firma y mi gente cobra la ' +
            'semana que trabajo. Dicen que unos estudiantes andan en eso. ' +
            'Yo les hago el altar si lo logran.',
          en:
            'That one day this becomes pressing a button: the measurement ' +
            'goes in, the sheet comes out, the engineer signs and my ' +
            'people collect the week they worked. They say some students ' +
            'are on it. I will build them an altar if they pull it off.',
        },
        options: [
          {
            label: { es: 'Ojala sea pronto', en: 'Hopefully soon' },
            next: 'bye',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Bueno, voy a preguntar una vez mas antes de agarrar camino. ' +
            'Si cruzas al presente, fijate si por fin pagan a tiempo.',
          en:
            'Well, I will ask one more time before hitting the road. If ' +
            'you cross to the present, check whether they finally pay on ' +
            'time.',
        },
        options: [{ label: { es: 'Asi hare', en: 'I will' }, next: null }],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
