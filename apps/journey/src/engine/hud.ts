/**
 * @module hud (engine)
 * @description HUD DOM puro (port del Hud.tsx de R3F): indicador de zona,
 *   prompt de interaccion, fichas retos/aprendizajes, contacto,
 *   teletransporte, fade de esclusa, loader, overlays manga (screentone +
 *   vineta + sepia/grano del pasado) y controles tactiles. Todo el texto
 *   es HTML — nunca pixeles WebGL (regla dura del plan).
 */
import { profile } from '@portfolio/content'
import type { Locale, RoomDef } from '../lib/rooms'
import { sfx } from './audio'
import type { NpcDialog } from './dialog'
import {
  type CameraMode,
  type EngineState,
  type FichaKind,
  type InteractableBubble,
  isUiOpen,
} from './state'
import { PAST_CAPTIONS } from './themes'

const STRINGS = {
  es: {
    exit: 'Ver CV 2D',
    loading: 'Cargando el mundo 3D…',
    controlsThird:
      'WASD / flechas — caminar · arrastra — camara · E — interactuar · V — POV · M — mapa',
    controlsPov:
      'WASD / flechas — caminar · mouse — mirar · E — interactuar · V — 3ª persona · M — mapa',
    controlsThirdTouch:
      'joystick — caminar · arrastra — camara · E — interactuar',
    controlsPovTouch: 'joystick — caminar · arrastra — mirar · E — interactuar',
    clickToStart: 'Click para explorar',
    corridorTo: 'Rumbo a',
    roomOf: (n: number, total: number) => `Sala ${n} de ${total}`,
    interactKey: 'E',
    retos: 'Retos',
    aprendizajes: 'Aprendizajes',
    close: 'Cerrar (Esc)',
    map: 'Mapa (M)',
    mapTitle: 'Teletransporte',
    audioOn: 'Sonido: ON',
    audioOff: 'Sonido: OFF',
    cameraThird: 'Camara: 3ª (V)',
    cameraPov: 'Camara: POV (V)',
    tour: 'Tour',
    tourStop: 'Detener tour',
    tourHint: 'Tour automatico — cualquier tecla o el joystick lo detiene',
    contactTitle: 'Hablemos',
    contactBody: 'Disponible para roles de arquitectura y liderazgo tecnico.',
    email: 'Email',
  },
  en: {
    exit: 'View 2D CV',
    loading: 'Loading the 3D world…',
    controlsThird:
      'WASD / arrows — walk · drag — camera · E — interact · V — POV · M — map',
    controlsPov:
      'WASD / arrows — walk · mouse — look · E — interact · V — 3rd person · M — map',
    controlsThirdTouch: 'joystick — walk · drag — camera · E — interact',
    controlsPovTouch: 'joystick — walk · drag — look · E — interact',
    clickToStart: 'Click to explore',
    corridorTo: 'Heading to',
    roomOf: (n: number, total: number) => `Room ${n} of ${total}`,
    interactKey: 'E',
    retos: 'Challenges',
    aprendizajes: 'Learnings',
    close: 'Close (Esc)',
    map: 'Map (M)',
    mapTitle: 'Teleport',
    audioOn: 'Sound: ON',
    audioOff: 'Sound: OFF',
    cameraThird: 'Camera: 3rd (V)',
    cameraPov: 'Camera: POV (V)',
    tour: 'Tour',
    tourStop: 'Stop tour',
    tourHint: 'Auto tour — any key or the joystick stops it',
    contactTitle: "Let's talk",
    contactBody: 'Open to architecture and tech-leadership roles.',
    email: 'Email',
  },
} as const

const CSS = `
.jny-hud { position: absolute; inset: 0; pointer-events: none; z-index: 10;
  font-family: var(--font-sans, sans-serif); }
.jny-panel { background: color-mix(in srgb, var(--color-grey-95, #0a0a0a) 84%, transparent);
  color: var(--color-grey-5, #f7f7f5);
  border: 2px solid color-mix(in srgb, var(--color-grey-5, #f7f7f5) 22%, transparent);
  border-radius: var(--radius-md, 12px); padding: 0.6rem 0.9rem;
  font-size: 0.85rem; line-height: 1.45; backdrop-filter: blur(6px); }
.jny-btn { pointer-events: auto; cursor: pointer; font: inherit; }
.jny-top-left { position: absolute; top: 12px; left: 12px; max-width: min(60vw, 520px); }
.jny-top-right { position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; }
.jny-bottom-right { position: absolute; bottom: 12px; right: 12px; display: flex; gap: 8px; }
.jny-hints { position: absolute; bottom: 12px; left: 12px; font-size: 0.72rem; opacity: 0.85; }
.jny-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
.jny-prompt { position: absolute; bottom: 22%; left: 50%; transform: translateX(-50%);
  white-space: nowrap; }
.jny-prompt kbd { border: 1px solid currentColor; border-radius: 4px;
  padding: 0 0.35em; margin-right: 0.5em; }
.jny-crosshair { position: absolute; top: 50%; left: 50%; width: 5px; height: 5px;
  margin: -2.5px 0 0 -2.5px; border-radius: 50%;
  background: color-mix(in srgb, var(--color-grey-5, #f7f7f5) 85%, transparent); }
.jny-aside { position: absolute; top: 50%; right: 24px; transform: translateY(-50%);
  width: min(420px, calc(100vw - 48px)); max-height: 76vh; overflow-y: auto;
  pointer-events: auto; padding: 1.1rem 1.25rem; }
.jny-modal { width: min(380px, calc(100vw - 48px)); pointer-events: auto;
  padding: 1.1rem 1.2rem; }
.jny-link { display: block; padding: 0.5rem 0.8rem; border-radius: 8px;
  border: 1px solid color-mix(in srgb, currentColor 35%, transparent);
  color: inherit; text-decoration: none; text-align: left;
  background: color-mix(in srgb, var(--color-primary, #4f6ef7) 22%, transparent); }
.jny-close { margin-top: 0.9rem; background: transparent; color: inherit;
  border: 1px solid currentColor; border-radius: 6px; padding: 0.3rem 0.7rem; }
.jny-caption { position: absolute; bottom: 56px; left: 50%; transform: translateX(-50%);
  width: min(440px, calc(100vw - 24px)); }
.jny-dialog { position: absolute; bottom: 76px; left: 50%; transform: translateX(-50%);
  width: min(560px, calc(100vw - 32px)); max-height: 46vh; overflow-y: auto;
  pointer-events: auto; padding: 0.9rem 1.1rem; }
.jny-dialog-name { margin: 0 0 0.35rem; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-primary, #4f6ef7); }
.jny-dialog-text { margin: 0 0 0.7rem; line-height: 1.5; }
.jny-dialog-options { display: flex; flex-direction: column; gap: 0.45rem; }
.jny-bubble { position: absolute; transform: translate(-50%, calc(-100% - 14px));
  max-width: 240px; background: #f7f4ea; color: #1c1822;
  border: 2px solid #1c1822; border-radius: 14px; padding: 0.4rem 0.65rem;
  font-size: 0.78rem; line-height: 1.35; pointer-events: none; z-index: 12;
  display: none; }
.jny-bubble::after { content: ''; position: absolute; left: 50%; bottom: -10px;
  transform: translateX(-50%); border: 6px solid transparent;
  border-top: 10px solid #1c1822; border-bottom: 0; }
.jny-fade { position: absolute; inset: 0; background: #0b0b10; opacity: 0;
  transition: opacity 350ms ease; pointer-events: none; z-index: 40; }
.jny-dream { position: absolute; inset: 0; pointer-events: none; z-index: 41;
  opacity: 0; visibility: hidden;
  transition: opacity 620ms ease, visibility 0s linear 620ms;
  background: radial-gradient(circle at 50% 45%, #ffffff 0%, #fdf6e6 55%, #e8dcc0 100%); }
.jny-dream.on { opacity: 1; visibility: visible;
  transition: opacity 520ms ease; backdrop-filter: blur(12px) brightness(1.3); }
.jny-loader { position: absolute; inset: 0; display: grid; place-items: center;
  background: #0b0b10; color: var(--color-grey-5, #f7f7f5); z-index: 50; }
.jny-screentone { position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(circle, rgba(0,0,0,0.35) 1px, transparent 1px);
  background-size: 4px 4px; opacity: 0.06; mix-blend-mode: multiply; }
.jny-vignette { position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 58%, rgba(0,0,0,0.4) 100%); }
.jny-grain { position: absolute; inset: 0; pointer-events: none; opacity: 0.16;
  background-image: radial-gradient(circle, rgba(255,255,255,0.35) 1px, transparent 1px);
  background-size: 3px 3px; animation: jny-grain 0.7s steps(4) infinite;
  mix-blend-mode: overlay; display: none; }
.jny-glitch { position: absolute; inset: 0; pointer-events: none; background: #d8c8a8;
  opacity: 0; display: none; }
.jny-glitch.on { display: block; animation: jny-glitch-in 450ms steps(5) forwards; }
@keyframes jny-glitch-in {
  0% { opacity: 1; transform: translateX(0); }
  20% { opacity: 0.6; transform: translateX(-6px); }
  40% { opacity: 0.9; transform: translateX(5px); }
  60% { opacity: 0.5; transform: translateX(-3px); }
  100% { opacity: 0; transform: translateX(0); }
}
@keyframes jny-grain { 0% { background-position: 0 0; } 100% { background-position: 90px 60px; } }
.jny-joystick { position: absolute; bottom: 84px; left: 26px; width: 120px; height: 120px;
  border-radius: 50%; background: color-mix(in srgb, var(--color-grey-5, #f7f7f5) 12%, transparent);
  border: 2px solid color-mix(in srgb, var(--color-grey-5, #f7f7f5) 25%, transparent);
  pointer-events: auto; touch-action: none; }
.jny-stick { position: absolute; top: 50%; left: 50%; width: 52px; height: 52px;
  margin: -26px 0 0 -26px; border-radius: 50%;
  background: color-mix(in srgb, var(--color-grey-5, #f7f7f5) 55%, transparent); }
.jny-action { position: absolute; bottom: 104px; right: 30px; width: 74px; height: 74px;
  border-radius: 50%; background: color-mix(in srgb, var(--color-primary, #4f6ef7) 85%, transparent);
  color: #fff; font-size: 1rem; font-weight: 700; border: 2px solid #0b0b10;
  pointer-events: auto; touch-action: none; }
@media (max-width: 640px) {
  .jny-panel { font-size: 0.7rem; padding: 0.35rem 0.55rem; }
  .jny-top-left { max-width: 42vw; }
  .jny-hints { max-width: 52vw; font-size: 0.62rem; }
}
`

export interface HudActions {
  onExit(): void
  onTeleport(index: number): void
  onToggleAudio(on: boolean): void
  onToggleCamera(): void
  onStartTour(): void
  onStopTour(): void
}

export interface HudDeps {
  container: HTMLElement
  /** Wrapper del canvas (recibe el filter sepia del pasado). */
  canvasWrap: HTMLElement
  locale: Locale
  rooms: readonly RoomDef[]
  state: EngineState
  actions: HudActions
  /** Boton Tour visible (reduced siempre; full solo con ?tour). */
  showTourButton: boolean
}

export interface Hud {
  setZoneLabel(text: string): void
  /** Recalcula el indicador de zona desde el estado (zona o pasado). */
  setZoneFromState(): void
  showPrompt(label: string | null): void
  setCameraMode(mode: CameraMode): void
  setPointerLocked(locked: boolean): void
  openFicha(roomIndex: number, kind: FichaKind): void
  /** Panel de texto libre (la historia del pasado, expandida con E). */
  openStory(title: string, paragraphs: readonly string[]): void
  /** Panel de conversacion con un NPC (arbol de opciones 1-9/click). */
  openDialog(npc: NpcDialog, onClose?: () => void): void
  /** Burbuja de habla suelta del NPC activo (null la oculta). */
  setBubble(bubble: InteractableBubble | null): void
  /** Reposiciona la burbuja proyectando su anclaje 3D (cada frame). */
  updateBubble(
    project: (
      x: number,
      y: number,
      z: number,
    ) => { x: number; y: number; behind: boolean },
  ): void
  openContact(): void
  toggleTeleport(): void
  closeAll(): void
  /** 'dark' (esclusa/teleport) o 'dream' (portal al pasado: white-out). */
  fade(on: boolean, style?: 'dark' | 'dream'): Promise<void>
  setPastMode(on: boolean): void
  setAudio(on: boolean): void
  setTour(on: boolean): void
  showLoader(on: boolean): void
  touch: {
    joystick: HTMLElement
    stick: HTMLElement
    actionButton: HTMLElement
  } | null
  dispose(): void
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag)
  node.className = className
  if (text !== undefined) {
    node.textContent = text
  }
  return node
}

function button(
  className: string,
  text: string,
  onClick: () => void,
): HTMLButtonElement {
  const node = el('button', className, text)
  node.type = 'button'
  node.addEventListener('click', onClick)
  return node
}

export function createHud(deps: HudDeps): Hud {
  const { container, locale, rooms, state, actions } = deps
  const t = STRINGS[locale]
  const root = el('div', 'jny-hud')
  const style = document.createElement('style')
  style.textContent = CSS
  root.appendChild(style)

  // overlays de composicion 2D (firma manga)
  const screentone = el('div', 'jny-screentone')
  const vignette = el('div', 'jny-vignette')
  const grain = el('div', 'jny-grain')
  const glitch = el('div', 'jny-glitch')
  screentone.setAttribute('aria-hidden', 'true')
  vignette.setAttribute('aria-hidden', 'true')
  grain.setAttribute('aria-hidden', 'true')
  glitch.setAttribute('aria-hidden', 'true')

  // indicador de zona
  const zoneLabel = el('div', 'jny-panel jny-top-left')

  // top-right: audio + camara + salida (el audio arranca ON: los SFX
  // suenan desde el primer gesto; el toggle silencia TODO)
  const audioBtn = button(
    'jny-panel jny-btn',
    state.audioOn ? t.audioOn : t.audioOff,
    () => {
      state.audioOn = !state.audioOn
      hud.setAudio(state.audioOn)
      actions.onToggleAudio(state.audioOn)
    },
  )
  audioBtn.setAttribute('aria-pressed', state.audioOn ? 'true' : 'false')
  const cameraBtn = button('jny-panel jny-btn', t.cameraThird, () => {
    actions.onToggleCamera()
  })
  const exitBtn = button('jny-panel jny-btn', t.exit, () => actions.onExit())
  const topRight = el('div', 'jny-top-right')
  topRight.append(audioBtn, cameraBtn, exitBtn)

  // bottom-right: tour (opcional) + mapa
  const bottomRight = el('div', 'jny-bottom-right')
  const tourBtn = button('jny-panel jny-btn', t.tour, () => {
    if (state.tourOn) {
      actions.onStopTour()
    } else {
      actions.onStartTour()
    }
  })
  if (deps.showTourButton) {
    bottomRight.appendChild(tourBtn)
  }
  const mapBtn = button('jny-panel jny-btn', t.map, () => hud.toggleTeleport())
  bottomRight.appendChild(mapBtn)

  // hints + click-to-start + crosshair + prompt
  const hints = el('div', 'jny-panel jny-hints', t.controlsThird)
  const clickToStart = el('div', 'jny-panel jny-center')
  clickToStart.style.textAlign = 'center'
  clickToStart.style.fontSize = '1rem'
  clickToStart.textContent = t.clickToStart
  clickToStart.style.display = 'none'
  const crosshair = el('div', 'jny-crosshair')
  crosshair.style.display = 'none'
  const prompt = el('div', 'jny-panel jny-prompt')
  prompt.style.display = 'none'
  const promptKbd = el('kbd', '', t.interactKey)
  const promptText = document.createElement('span')
  prompt.append(promptKbd, promptText)

  // caption del tour (textos de la etapa)
  const caption = el('div', 'jny-panel jny-caption')
  caption.style.display = 'none'

  // paneles: ficha / contacto / teletransporte
  const ficha = el('aside', 'jny-panel jny-aside')
  ficha.style.display = 'none'
  const contact = el('aside', 'jny-panel jny-modal jny-center')
  contact.style.display = 'none'
  contact.setAttribute('aria-label', t.contactTitle)
  const teleport = el('nav', 'jny-panel jny-modal jny-center')
  teleport.style.display = 'none'
  teleport.setAttribute('aria-label', t.mapTitle)

  // panel de conversacion con NPCs + burbuja manga de habla suelta
  const dialog = el('aside', 'jny-panel jny-dialog')
  dialog.style.display = 'none'
  const bubble = el('div', 'jny-bubble')
  bubble.setAttribute('aria-hidden', 'true')

  // contenido estatico del panel de contacto
  {
    const title = el('h2', '', t.contactTitle)
    title.style.margin = '0'
    const body = el('p', '', t.contactBody)
    body.style.opacity = '0.8'
    const links = el('div', '')
    links.style.cssText =
      'display:flex;flex-direction:column;gap:0.5rem;margin-top:0.8rem'
    const email = el('a', 'jny-link', t.email)
    email.setAttribute('href', `mailto:${profile.contacts.email}`)
    const linkedin = el('a', 'jny-link', 'LinkedIn')
    linkedin.setAttribute('href', profile.contacts.linkedin)
    linkedin.setAttribute('target', '_blank')
    linkedin.setAttribute('rel', 'noreferrer')
    const github = el('a', 'jny-link', 'GitHub')
    github.setAttribute('href', profile.contacts.github)
    github.setAttribute('target', '_blank')
    github.setAttribute('rel', 'noreferrer')
    links.append(email, linkedin, github)
    contact.append(
      title,
      body,
      links,
      button('jny-close jny-btn', t.close, () => hud.closeAll()),
    )
    contact.style.textAlign = 'center'
  }

  // contenido estatico del teletransporte (las salas no cambian)
  {
    const title = el('h2', '', t.mapTitle)
    title.style.margin = '0 0 0.7rem'
    const list = el('div', '')
    list.style.cssText = 'display:flex;flex-direction:column;gap:0.5rem'
    for (const def of rooms) {
      const texts = def.texts[locale]
      list.appendChild(
        button(
          'jny-link jny-btn',
          `${t.roomOf(def.order + 1, rooms.length)} — ${texts.title} (${texts.period})`,
          () => {
            hud.closeAll()
            actions.onTeleport(def.order)
          },
        ),
      )
    }
    teleport.append(title, list)
  }

  // fade (negro) + fade de sueño (white-out del portal) + loader
  const fadeEl = el('div', 'jny-fade')
  fadeEl.setAttribute('aria-hidden', 'true')
  const dreamEl = el('div', 'jny-dream')
  dreamEl.setAttribute('aria-hidden', 'true')
  const loader = el('div', 'jny-loader', t.loading)
  loader.style.display = 'none'

  // controles tactiles (solo pointer coarse)
  let touch: Hud['touch'] = null
  const coarse = window.matchMedia('(pointer: coarse)').matches
  if (coarse) {
    const joystick = el('div', 'jny-joystick')
    const stick = el('div', 'jny-stick')
    joystick.appendChild(stick)
    // el handler real (pointerdown) lo cablea controls
    const actionButton = el('button', 'jny-action', t.interactKey)
    actionButton.type = 'button'
    root.append(joystick, actionButton)
    touch = { joystick, stick, actionButton }
  }

  root.append(
    screentone,
    vignette,
    grain,
    glitch,
    zoneLabel,
    topRight,
    bottomRight,
    hints,
    clickToStart,
    crosshair,
    prompt,
    caption,
    ficha,
    contact,
    teleport,
    dialog,
    bubble,
    fadeEl,
    dreamEl,
    loader,
  )
  container.appendChild(root)

  let cameraMode: CameraMode = 'third'
  let pointerLocked = false
  let currentPrompt: string | null = null
  let dialogOnClose: (() => void) | null = null
  let dialogOptions: HTMLButtonElement[] = []
  let bubbleSpec: InteractableBubble | null = null

  /** Renderiza un nodo del arbol; las opciones avanzan o cierran. */
  function renderDialogNode(npc: NpcDialog, id: string): void {
    const node = npc.nodes[id]
    if (!node) {
      hud.closeAll()
      return
    }
    dialog.replaceChildren()
    dialogOptions = []
    const name = el('p', 'jny-dialog-name', npc.name[locale])
    const text = el('p', 'jny-dialog-text', node.text[locale])
    const list = el('div', 'jny-dialog-options')
    node.options.forEach((option, index) => {
      const item = button(
        'jny-link jny-btn',
        `${index + 1}. ${option.label[locale]}`,
        () => {
          sfx.play('blip')
          if (option.next === null) {
            hud.closeAll()
            return
          }
          renderDialogNode(npc, option.next)
        },
      )
      list.appendChild(item)
      dialogOptions.push(item)
    })
    const hint = el('p', '', t.close)
    hint.style.cssText = 'margin:0.6rem 0 0;font-size:0.66rem;opacity:0.55'
    dialog.append(name, text, list, hint)
  }

  /** Teclas 1-9 eligen la opcion del dialogo abierto. */
  function onDialogKey(event: KeyboardEvent): void {
    if (state.ui !== 'dialog') {
      return
    }
    const { code } = event
    const digit = code.startsWith('Digit')
      ? Number(code.slice(5))
      : code.startsWith('Numpad')
        ? Number(code.slice(6))
        : Number.NaN
    if (Number.isInteger(digit)) {
      dialogOptions[digit - 1]?.click()
    }
  }
  window.addEventListener('keydown', onDialogKey)

  function hintsFor(mode: CameraMode): string {
    if (touch) {
      return mode === 'pov' ? t.controlsPovTouch : t.controlsThirdTouch
    }
    return mode === 'pov' ? t.controlsPov : t.controlsThird
  }

  function refreshOverlayState(): void {
    const uiOpen = isUiOpen(state)
    const pov = cameraMode === 'pov'
    // en touch no hay pointer-lock: ni "click para explorar" ni crosshair
    const lookReady = pointerLocked || touch !== null
    clickToStart.style.display = pov && !lookReady && !uiOpen ? '' : 'none'
    crosshair.style.display = pov && lookReady && !uiOpen ? '' : 'none'
    prompt.style.display = currentPrompt && !uiOpen ? '' : 'none'
    hints.textContent = hintsFor(cameraMode)
  }

  function updateCaption(): void {
    if (!state.tourOn || state.zone.kind !== 'room') {
      caption.style.display = 'none'
      return
    }
    const room = rooms[state.zone.index]
    if (!room) {
      caption.style.display = 'none'
      return
    }
    const texts = room.texts[locale]
    caption.replaceChildren()
    const head = el('strong', '', `${texts.title} · ${texts.period}`)
    const retos = el('p', '', `${t.retos}: ${texts.retos[0] ?? ''}`)
    retos.style.cssText = 'margin:0.3rem 0 0;opacity:0.85'
    const apr = el('p', '', `${t.aprendizajes}: ${texts.aprendizajes[0] ?? ''}`)
    apr.style.cssText = 'margin:0.25rem 0 0;opacity:0.85'
    const hint = el('p', '', t.tourHint)
    hint.style.cssText = 'margin:0.35rem 0 0;font-size:0.7rem;opacity:0.6'
    caption.append(head, retos, apr, hint)
    caption.style.display = ''
  }

  const hud: Hud = {
    setZoneLabel(text) {
      zoneLabel.textContent = text
    },

    setZoneFromState() {
      const past = state.past
      if (past !== null) {
        const def = rooms[past]
        hud.setZoneLabel(def ? PAST_CAPTIONS[def.id][locale] : '')
        updateCaption()
        return
      }
      const { zone } = state
      if (zone.kind === 'room') {
        const room = rooms[zone.index]
        if (room) {
          const texts = room.texts[locale]
          hud.setZoneLabel(
            `${t.roomOf(zone.index + 1, rooms.length)} — ${texts.title} (${texts.period})`,
          )
        }
      } else {
        const target = rooms[zone.index + 1]
        hud.setZoneLabel(
          target ? `${t.corridorTo} ${target.texts[locale].title}` : '',
        )
      }
      updateCaption()
    },

    showPrompt(label) {
      currentPrompt = label
      promptText.textContent = label ? ` ${label}` : ''
      refreshOverlayState()
    },

    setCameraMode(mode) {
      cameraMode = mode
      cameraBtn.textContent = mode === 'pov' ? t.cameraPov : t.cameraThird
      refreshOverlayState()
    },

    setPointerLocked(locked) {
      pointerLocked = locked
      refreshOverlayState()
    },

    openFicha(roomIndex, kind) {
      const def = rooms[roomIndex]
      if (!def) {
        return
      }
      state.ui = 'ficha'
      state.ficha = { roomIndex, kind }
      const texts = def.texts[locale]
      ficha.setAttribute('aria-label', t[kind])
      ficha.replaceChildren()
      const meta = el('p', '', `${texts.title} · ${texts.period}`)
      meta.style.cssText = 'margin:0;opacity:0.7;font-size:0.72rem'
      const title = el('h2', '', t[kind])
      title.style.cssText = 'margin:0.15rem 0 0.6rem;font-size:1.05rem'
      const list = el('ul', '')
      list.style.cssText = 'margin:0;padding-left:1.1rem'
      for (const item of texts[kind]) {
        const li = el('li', '', item)
        li.style.marginBottom = '0.45rem'
        list.appendChild(li)
      }
      ficha.append(
        meta,
        title,
        list,
        button('jny-close jny-btn', t.close, () => hud.closeAll()),
      )
      ficha.style.display = ''
      refreshOverlayState()
    },

    openStory(title, paragraphs) {
      state.ui = 'ficha'
      ficha.setAttribute('aria-label', title)
      ficha.replaceChildren()
      const heading = el('h2', '', title)
      heading.style.cssText = 'margin:0 0 0.6rem;font-size:1.05rem'
      ficha.appendChild(heading)
      for (const text of paragraphs) {
        const paragraph = el('p', '', text)
        paragraph.style.cssText =
          'margin:0 0 0.55rem;opacity:0.9;line-height:1.45'
        ficha.appendChild(paragraph)
      }
      ficha.appendChild(
        button('jny-close jny-btn', t.close, () => hud.closeAll()),
      )
      ficha.style.display = ''
      refreshOverlayState()
    },

    openDialog(npc, onClose) {
      hud.closeAll()
      state.ui = 'dialog'
      dialogOnClose = onClose ?? null
      renderDialogNode(npc, npc.start)
      dialog.style.display = ''
      refreshOverlayState()
    },

    setBubble(spec) {
      bubbleSpec = spec
      const line = spec?.lines[Math.floor(Math.random() * spec.lines.length)]
      if (line) {
        bubble.textContent = line[locale]
      } else {
        bubble.style.display = 'none'
      }
    },

    updateBubble(project) {
      if (!bubbleSpec || bubbleSpec.lines.length === 0 || isUiOpen(state)) {
        bubble.style.display = 'none'
        return
      }
      const anchor = bubbleSpec.anchor()
      const point = project(anchor.x, anchor.y, anchor.z)
      if (point.behind) {
        bubble.style.display = 'none'
        return
      }
      bubble.style.display = ''
      bubble.style.left = `${point.x}px`
      bubble.style.top = `${point.y}px`
    },

    openContact() {
      state.ui = 'contact'
      contact.style.display = ''
      refreshOverlayState()
    },

    toggleTeleport() {
      if (state.ui === 'teleport') {
        hud.closeAll()
        return
      }
      hud.closeAll()
      state.ui = 'teleport'
      teleport.style.display = ''
      refreshOverlayState()
    },

    closeAll() {
      state.ui = 'none'
      state.ficha = null
      ficha.style.display = 'none'
      contact.style.display = 'none'
      teleport.style.display = 'none'
      dialog.style.display = 'none'
      dialogOptions = []
      const done = dialogOnClose
      dialogOnClose = null
      done?.()
      refreshOverlayState()
    },

    fade(on, mode = 'dark') {
      if (mode === 'dream') {
        dreamEl.classList.toggle('on', on)
        return new Promise((resolve) => {
          window.setTimeout(resolve, on ? 560 : 650)
        })
      }
      fadeEl.style.opacity = on ? '1' : '0'
      return new Promise((resolve) => {
        window.setTimeout(resolve, 380)
      })
    },

    setPastMode(on) {
      deps.canvasWrap.style.filter = on
        ? 'sepia(0.72) saturate(0.55) contrast(1.06) brightness(0.92)'
        : ''
      deps.canvasWrap.style.transition = 'filter 400ms ease'
      grain.style.display = on ? '' : 'none'
      glitch.classList.toggle('on', on)
      hud.setZoneFromState()
    },

    setAudio(on) {
      audioBtn.textContent = on ? t.audioOn : t.audioOff
      audioBtn.setAttribute('aria-pressed', on ? 'true' : 'false')
    },

    setTour(on) {
      tourBtn.textContent = on ? t.tourStop : t.tour
      updateCaption()
    },

    showLoader(on) {
      loader.style.display = on ? '' : 'none'
    },

    touch,

    dispose() {
      window.removeEventListener('keydown', onDialogKey)
      root.remove()
    },
  }

  // estado inicial de overlays/hints (en touch: texto de joystick)
  refreshOverlayState()

  return hud
}
