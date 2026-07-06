/**
 * @module dialogs/destacame-presente (engine)
 * @description Arboles de dialogo de la sala 6 presente: Destacame, la
 *   fintech chilena de inclusion financiera (2021-hoy, CL+MX). 5 NPCs
 *   del canon (informe 13; la dev frontend se renombro a Camila
 *   Espinoza para no chocar con la Camila Fuentes de GoodMeal): Camila
 *   (dev frontend) y Diego Riquelme (dev fullstack) hablan de construir
 *   con Pablo — Vue/Nuxt, PagaloAqui, microservicios Django —; Rodrigo
 *   Salinas (representante de banco de visita) y Valentina Cardenas
 *   (PM/stakeholder) hablan de lo que pidieron y recibieron; Ana Sofia
 *   Herrera (lead MX) cierra con el liderazgo, la expansion a Mexico y
 *   el vibe coding.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const DESTACAME_PRESENTE_DIALOGS = {
  camila: defineDialog({
    name: { es: 'Camila Espinoza', en: 'Camila Espinoza' },
    chatter: [
      {
        es: 'Este form valida el RUT antes de tocar el backend.',
        en: 'This form validates the RUT before touching the backend.',
      },
      {
        es: 'Nuxt + TypeScript... el stack quedo redondo.',
        en: 'Nuxt + TypeScript... the stack came out solid.',
      },
      {
        es: 'Cero deuda tecnica nueva este sprint. Cero.',
        en: 'Zero new tech debt this sprint. Zero.',
      },
      {
        es: 'Un flujo de pago no puede fallar. No puede.',
        en: 'A payment flow cannot fail. It just cannot.',
      },
      {
        es: 'El componente de deuda quedo reutilizable al fin.',
        en: 'The debt component is finally reusable.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Camila, frontend fintech. Aca cada pantalla mueve plata ' +
            'de verdad: deudas, descuentos, pagos con bancos. ¿Que ' +
            'quieres saber?',
          en:
            'Camila, fintech frontend. Every screen here moves real ' +
            'money: debts, discounts, bank payments. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era el frontend cuando llego Pablo?',
              en: 'What was the frontend like when Pablo arrived?',
            },
            next: 'vue-1',
          },
          {
            label: {
              es: '¿Que tiene de especial un flujo de pago?',
              en: 'What is special about a payment flow?',
            },
            next: 'pago-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'vue-1': {
        text: {
          es:
            'Heredado y fragil. Pablo entro en 2021 y se puso a ' +
            'migrar interfaces a Vue y Nuxt, refactorizando ' +
            'componentes para bajar la deuda tecnica. Cada refactor ' +
            'acortaba el time-to-ship del siguiente cambio — se ' +
            'notaba sprint a sprint.',
          en:
            'Legacy and fragile. Pablo joined in 2021 and started ' +
            'migrating interfaces to Vue and Nuxt, refactoring ' +
            'components to cut tech debt. Every refactor shortened ' +
            'the time-to-ship of the next change — you could feel it ' +
            'sprint by sprint.',
        },
        options: [
          {
            label: {
              es: '¿Y eso en que termino?',
              en: 'And where did that end up?',
            },
            next: 'vue-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'vue-2': {
        text: {
          es:
            'En interfaces que hoy usan miles de personas en Chile ' +
            'para entender y resolver sus deudas. Y en estandares: lo ' +
            'que Pablo dejo escrito sobre como se construye un ' +
            'componente aca, lo seguimos usando. Despues se volvio el ' +
            'arquitecto de todo esto.',
          en:
            'In interfaces thousands of people in Chile use today to ' +
            'understand and settle their debts. And in standards: ' +
            'what Pablo wrote down about how a component is built ' +
            'here, we still follow. Later he became the architect of ' +
            'all this.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Buen legado', en: 'A good legacy' }, next: null },
        ],
      },
      'pago-1': {
        text: {
          es:
            'Que no hay segunda oportunidad. En PagaloAqui la gente ' +
            'paga deudas vencidas con Santander o Scotiabank: datos ' +
            'sensibles, montos reales, WebPay al final. Validacion en ' +
            'cada paso y presentacion clara del monto — eso lo ' +
            'aprendi del trabajo de Pablo.',
          en:
            'That there is no second chance. On PagaloAqui people pay ' +
            'overdue debts with Santander or Scotiabank: sensitive ' +
            'data, real amounts, WebPay at the end. Validation at ' +
            'every step and a clear amount on screen — I learned that ' +
            'from Pablo’s work.',
        },
        options: [
          {
            label: {
              es: '¿Que pasa si algo falla?',
              en: 'What if something fails?',
            },
            next: 'pago-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pago-2': {
        text: {
          es:
            'El formulario te frena ANTES de que el banco te rebote. ' +
            'Un RUT mal escrito, un monto raro, una sesion vencida: ' +
            'todo se valida en el cliente y se confirma en el ' +
            'backend. Aburrido de robusto. Asi debe ser el fintech.',
          en:
            'The form stops you BEFORE the bank bounces you. A ' +
            'mistyped RUT, an odd amount, an expired session: all ' +
            'validated client-side and confirmed in the backend. ' +
            'Boringly robust. That is how fintech should be.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Aburrido es bueno', en: 'Boring is good' },
            next: null,
          },
        ],
      },
    },
  }),

  diego: defineDialog({
    name: { es: 'Diego Riquelme', en: 'Diego Riquelme' },
    chatter: [
      {
        es: 'El servicio de scoring respondio en 90 ms. Rico.',
        en: 'The scoring service answered in 90 ms. Sweet.',
      },
      {
        es: 'Django + Vue: el mismo dev puede tocar ambos lados.',
        en: 'Django + Vue: the same dev can touch both sides.',
      },
      {
        es: 'La campaña de hoy salio en cuatro minutos.',
        en: 'Today’s campaign went out in four minutes.',
      },
      {
        es: 'Otro microservicio al aire. Sin drama.',
        en: 'Another microservice live. No drama.',
      },
      {
        es: 'Full stack no es un titulo, es no tener excusas.',
        en: 'Full stack is not a title, it is having no excuses.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Diego, fullstack. Vi a Pablo entrar como frontend puro ' +
            'y en ocho meses ya escribia Python con nosotros. ¿Que te ' +
            'cuento?',
          en:
            'Diego, full stack. I watched Pablo join as pure frontend ' +
            'and within eight months he was writing Python with us. ' +
            'What shall I tell you?',
        },
        options: [
          {
            label: {
              es: '¿Como fue ese salto a full stack?',
              en: 'How was that jump to full stack?',
            },
            next: 'stack-1',
          },
          {
            label: {
              es: '¿Que es eso del admin de campañas?',
              en: 'What is this campaign admin thing?',
            },
            next: 'campana-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'stack-1': {
        text: {
          es:
            'Deliberado. Pablo llego dominando Vue y Nuxt, y se puso ' +
            'a aprender Python y Django desde cero PARA crecer a full ' +
            'stack. En ocho meses paso de frontend puro a construir ' +
            'microservicios Django integrados con el frontend. El ' +
            'equipo gano versatilidad de la buena.',
          en:
            'Deliberate. Pablo arrived mastering Vue and Nuxt, and ' +
            'set out to learn Python and Django from scratch TO grow ' +
            'full stack. In eight months he went from pure frontend ' +
            'to building Django microservices wired into the ' +
            'frontend. The team gained the good kind of versatility.',
        },
        options: [
          {
            label: {
              es: '¿Microservicios para que?',
              en: 'Microservices for what?',
            },
            next: 'stack-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'stack-2': {
        text: {
          es:
            'Para que cada producto viva solo: scoring, pagos, ' +
            'campañas, usuarios. Backend Python/Django hablando con ' +
            'frontends Vue/Nuxt. Si un servicio se cae, el resto ' +
            'sigue; si un equipo necesita tocar pagos, no pisa a ' +
            'nadie. Esa fue la arquitectura que Pablo empujo.',
          en:
            'So each product lives on its own: scoring, payments, ' +
            'campaigns, users. Python/Django backends talking to ' +
            'Vue/Nuxt frontends. If one service falls, the rest keep ' +
            'going; if a team needs to touch payments, they step on ' +
            'nobody. That was the architecture Pablo pushed.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Solido', en: 'Solid' }, next: null },
        ],
      },
      'campana-1': {
        text: {
          es:
            'Nuestra herramienta interna favorita. Lanzar una ' +
            'campaña — elegir a quien, con que oferta, por que canal ' +
            '— se hacia A MANO y tomaba horas. Pablo construyo un ' +
            'admin que lo automatizo: hoy son minutos.',
          en:
            'Our favourite internal tool. Launching a campaign — ' +
            'picking who, with which offer, through which channel — ' +
            'was done BY HAND and took hours. Pablo built an admin ' +
            'that automated it: today it takes minutes.',
        },
        options: [
          {
            label: {
              es: '¿Y que cambio en el dia a dia?',
              en: 'And what changed day to day?',
            },
            next: 'campana-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'campana-2': {
        text: {
          es:
            'Que el equipo de campañas dejo de vivir pegado a las ' +
            'planillas. Configuran, revisan, lanzan — y a otra cosa. ' +
            'Cuando una herramienta interna te devuelve horas cada ' +
            'semana, eso es impacto aunque ningun cliente la vea.',
          en:
            'The campaigns team stopped living inside spreadsheets. ' +
            'They configure, review, launch — and move on. When an ' +
            'internal tool gives you hours back every week, that is ' +
            'impact even if no customer ever sees it.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Horas a minutos', en: 'Hours to minutes' },
            next: null,
          },
        ],
      },
    },
  }),

  rodrigo: defineDialog({
    name: { es: 'Rodrigo Salinas', en: 'Rodrigo Salinas' },
    chatter: [
      {
        es: 'La tasa de regularizacion subio de nuevo este mes.',
        en: 'The regularisation rate went up again this month.',
      },
      {
        es: 'Co-branded, pero la experiencia es impecable.',
        en: 'Co-branded, and the experience is spotless.',
      },
      {
        es: 'WebPay confirmo al tiro. Asi da gusto.',
        en: 'WebPay confirmed instantly. That is the way.',
      },
      {
        es: 'Del banco me preguntan como lo hicieron tan rapido.',
        en: 'The bank keeps asking how they built it so fast.',
      },
      {
        es: 'Cien por ciento online. Cero sucursal.',
        en: 'One hundred percent online. Zero branch visits.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Rodrigo Salinas, del banco — vengo de visita a revisar ' +
            'el portal de pagos. Nosotros pedimos esto; ellos lo ' +
            'construyeron. ¿Que quieres saber?',
          en:
            'Rodrigo Salinas, from the bank — visiting to review the ' +
            'payments portal. We asked for this; they built it. What ' +
            'do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que le pidieron a Destacame?',
              en: 'What did you ask Destacame for?',
            },
            next: 'pedido-1',
          },
          {
            label: {
              es: '¿Y el resultado?',
              en: 'And the result?',
            },
            next: 'resultado-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'pedido-1': {
        text: {
          es:
            'Un flujo para que un cliente con deuda vencida pagara ' +
            'online, sin pisar una sucursal. Con la marca del banco — ' +
            'Santander, Santander Consumer, Scotiabank — cada uno con ' +
            'su portal co-branded, y WebPay al final. Eso es ' +
            'PagaloAqui.',
          en:
            'A flow for a customer with overdue debt to pay online, ' +
            'without setting foot in a branch. Under the bank’s brand ' +
            '— Santander, Santander Consumer, Scotiabank — each with ' +
            'its co-branded portal, and WebPay at the end. That is ' +
            'PagaloAqui.',
        },
        options: [
          {
            label: {
              es: '¿Por que no lo hizo el banco?',
              en: 'Why didn’t the bank build it?',
            },
            next: 'pedido-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pedido-2': {
        text: {
          es:
            'Porque un banco tarda trimestres en lo que este equipo ' +
            'saca en semanas. Ellos ya sabian de deudas, descuentos y ' +
            'morosidad — nosotros pusimos la cartera y la marca. Cada ' +
            'entidad recibio su portal con el mismo motor detras.',
          en:
            'Because a bank takes quarters for what this team ships ' +
            'in weeks. They already knew debt, discounts and ' +
            'delinquency — we brought the portfolio and the brand. ' +
            'Each entity got its portal with the same engine behind.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Buen trato', en: 'A good deal' }, next: null },
        ],
      },
      'resultado-1': {
        text: {
          es:
            'Clientes que llevaban meses en mora regularizando en una ' +
            'sesion: entran, ven su deuda clara, aceptan el descuento ' +
            'y pagan seguro con WebPay. Rapido para el cliente, ' +
            'recuperacion para el banco. Todos ganan.',
          en:
            'Customers months into delinquency regularising in one ' +
            'session: they log in, see their debt clearly, take the ' +
            'discount and pay safely through WebPay. Fast for the ' +
            'customer, recovery for the bank. Everybody wins.',
        },
        options: [
          {
            label: {
              es: '¿Y la parte de Pablo?',
              en: 'And Pablo’s part?',
            },
            next: 'resultado-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'resultado-2': {
        text: {
          es:
            'Las interfaces por las que pasa cada pago: los ' +
            'formularios que validan, las pantallas que muestran el ' +
            'monto sin letra chica. Con datos sensibles no se ' +
            'improvisa, y aca nunca senti que improvisaran.',
          en:
            'The interfaces every payment goes through: the forms ' +
            'that validate, the screens that show the amount with no ' +
            'fine print. You do not improvise with sensitive data, ' +
            'and here I never felt they did.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Confianza', en: 'Trust' }, next: null },
        ],
      },
    },
  }),

  valentina: defineDialog({
    name: { es: 'Valentina Cardenas', en: 'Valentina Cardenas' },
    chatter: [
      {
        es: 'El roadmap de este trimestre por fin cierra.',
        en: 'This quarter’s roadmap finally adds up.',
      },
      {
        es: 'Chile y Mexico comparten mas de lo que crees.',
        en: 'Chile and Mexico share more than you would think.',
      },
      {
        es: 'Requerimiento claro, interfaz clara. Casi siempre.',
        en: 'Clear requirement, clear interface. Almost always.',
      },
      {
        es: 'Los equipos ya no se pisan. Que descanso.',
        en: 'The teams no longer step on each other. What a relief.',
      },
      {
        es: 'El usuario de deuda no quiere lujo: quiere claridad.',
        en: 'A user in debt does not want luxury: they want clarity.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Valentina, de producto. Yo traigo los problemas — ' +
            'deudas, scores, creditos en dos paises — y este equipo ' +
            'los vuelve pantallas que la gente entiende. ¿Que quieres ' +
            'saber?',
          en:
            'Valentina, product. I bring the problems — debts, ' +
            'scores, credit across two countries — and this team ' +
            'turns them into screens people understand. What do you ' +
            'want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como trabajaban con Pablo?',
              en: 'How did you work with Pablo?',
            },
            next: 'producto-1',
          },
          {
            label: {
              es: '¿Que cambio cuando paso a arquitecto?',
              en: 'What changed when he became architect?',
            },
            next: 'arqui-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'producto-1': {
        text: {
          es:
            'Yo llegaba con el requerimiento y Pablo lo devolvia ' +
            'convertido en una interfaz clara. Colaboraba de verdad ' +
            'con producto y diseño: preguntaba el porque, proponia ' +
            'mejor UX, y cuidaba la consistencia entre pantallas como ' +
            'nadie.',
          en:
            'I would arrive with the requirement and Pablo would hand ' +
            'it back as a clear interface. He truly collaborated with ' +
            'product and design: asked the why, proposed better UX, ' +
            'and guarded consistency across screens like no one else.',
        },
        options: [
          {
            label: {
              es: '¿Un ejemplo concreto?',
              en: 'A concrete example?',
            },
            next: 'producto-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'producto-2': {
        text: {
          es:
            'La plataforma para saldar deudas en Chile y los ' +
            'creditos por niveles en Mexico. Dos paises, dos ' +
            'regulaciones, una sola forma de mostrar plata en ' +
            'pantalla. Ese conocimiento del dominio — deuda y credito ' +
            'en CL y MX — ordeno el producto entero.',
          en:
            'The debt-settlement platform in Chile and the tiered ' +
            'credit product in Mexico. Two countries, two ' +
            'regulations, one single way of showing money on screen. ' +
            'That domain knowledge — debt and credit across CL and ' +
            'MX — put the whole product in order.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Dominio real', en: 'Real domain' }, next: null },
        ],
      },
      'arqui-1': {
        text: {
          es:
            'Que dejamos de reinventar. Pablo definio estandares y ' +
            'patrones de frontend ENTRE equipos: microfrontends con ' +
            'reglas claras. Ahora cada equipo avanza en paralelo sin ' +
            'pisarse, y una feature nueva arranca sobre base ' +
            'conocida.',
          en:
            'We stopped reinventing. Pablo defined frontend ' +
            'standards and patterns ACROSS teams: microfrontends ' +
            'with clear rules. Now each team moves in parallel ' +
            'without collisions, and a new feature starts on known ' +
            'ground.',
        },
        options: [
          {
            label: {
              es: '¿Y para producto que significa?',
              en: 'And what does that mean for product?',
            },
            next: 'arqui-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'arqui-2': {
        text: {
          es:
            'Predictibilidad. Antes preguntaba "¿cuanto tarda?" y la ' +
            'respuesta era un suspiro. Hoy los equipos estiman sobre ' +
            'patrones que conocen. Menos acoplamiento, mas entregas — ' +
            'eso me cambio el roadmap.',
          en:
            'Predictability. I used to ask "how long?" and the ' +
            'answer was a sigh. Today teams estimate on patterns ' +
            'they know. Less coupling, more delivery — that changed ' +
            'my roadmap.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Roadmap feliz', en: 'A happy roadmap' },
            next: null,
          },
        ],
      },
    },
  }),

  anasofia: defineDialog({
    name: { es: 'Ana Sofia Herrera', en: 'Ana Sofia Herrera' },
    chatter: [
      {
        es: 'La daily de Mexico es en una hora. Puntuales.',
        en: 'Mexico’s daily is in an hour. Be on time.',
      },
      {
        es: 'Reorganizacion y aun asi entregamos. Otra vez.',
        en: 'A reorg and we still delivered. Again.',
      },
      {
        es: 'La IA no reemplaza al equipo: le quita lo repetitivo.',
        en: 'AI does not replace the team: it removes the repetitive.',
      },
      {
        es: 'Tres años aca y el rol sigue creciendo.',
        en: 'Three years here and the role keeps growing.',
      },
      {
        es: 'Plataforma: que los demas equipos vuelen.',
        en: 'Platform: making the other teams fly.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ana Sofia, lead — Pablo me reporta a mi. Lo he visto ' +
            'liderar equipos de cuatro a seis personas a traves de ' +
            'reorganizaciones enteras. ¿Que quieres saber?',
          en:
            'Ana Sofia, lead — Pablo reports to me. I have watched ' +
            'him lead teams of four to six through entire reorgs. ' +
            'What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como lidera Pablo?',
              en: 'How does Pablo lead?',
            },
            next: 'lead-1',
          },
          {
            label: {
              es: '¿Que es eso del vibe coding?',
              en: 'What is this vibe coding thing?',
            },
            next: 'vibe-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'lead-1': {
        text: {
          es:
            'Sosteniendo la entrega cuando todo se mueve. Lidero el ' +
            'equipo de optimizacion y despues el de plataforma, ' +
            'atravesando reorganizaciones y reducciones sin soltar ' +
            'el ritmo. Mas de tres años aca, y cada año con mas ' +
            'responsabilidad.',
          en:
            'By keeping delivery steady while everything moves. He ' +
            'led the optimisation team and then platform, through ' +
            'reorgs and downsizing without dropping the pace. Over ' +
            'three years here, each one with more responsibility.',
        },
        options: [
          {
            label: {
              es: '¿Y la expansion a Mexico?',
              en: 'And the expansion to Mexico?',
            },
            next: 'lead-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'lead-2': {
        text: {
          es:
            'Por eso estoy yo aca. Los productos fintech que este ' +
            'equipo orquesta operan en Chile Y en Mexico: alla la ' +
            'gente consulta gratis su Score de Buro y accede a ' +
            'creditos por niveles. Misma plataforma, dos paises — y ' +
            'la arquitectura lo aguanta.',
          en:
            'That is why I am here. The fintech products this team ' +
            'orchestrates run in Chile AND Mexico: over there people ' +
            'check their Buro score for free and access tiered ' +
            'credit. Same platform, two countries — and the ' +
            'architecture holds it.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Dos banderas', en: 'Two flags' }, next: null },
        ],
      },
      'vibe-1': {
        text: {
          es:
            'Desarrollo asistido por IA, metido al flujo del equipo ' +
            'de forma productiva y SEGURA. Pablo no lo adopto por ' +
            'moda: definio donde ayuda — tareas repetitivas, ' +
            'refactors, tests — y donde no se suelta la mano.',
          en:
            'AI-assisted development, folded into the team’s flow in ' +
            'a productive and SAFE way. Pablo did not adopt it for ' +
            'fashion: he defined where it helps — repetitive tasks, ' +
            'refactors, tests — and where you never let go of the ' +
            'wheel.',
        },
        options: [
          {
            label: {
              es: '¿Y funciono?',
              en: 'Did it work?',
            },
            next: 'vibe-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'vibe-2': {
        text: {
          es:
            'Las tareas repetitivas se acortaron, medible. Y lo mas ' +
            'dificil: el equipo lo uso con criterio, porque habia ' +
            'reglas claras desde el dia uno. Adoptar IA bien es un ' +
            'problema de liderazgo, no de herramientas.',
          en:
            'Repetitive tasks got measurably shorter. And the hard ' +
            'part: the team used it with judgement, because the ' +
            'rules were clear from day one. Adopting AI well is a ' +
            'leadership problem, not a tooling one.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Criterio primero', en: 'Judgement first' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
