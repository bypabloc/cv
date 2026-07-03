/**
 * @component Hud
 * @description Overlay DOM sobre el canvas: indicador de sala, prompt de
 *   interaccion, hints de controles, ficha de retos/aprendizajes (DOM real,
 *   accesible) y salida al CV 2D. Todo el texto es HTML — nunca pixeles
 *   dentro del WebGL (regla dura del plan).
 */
import { profile } from '@portfolio/content'
import { type CSSProperties, useState } from 'react'
import type { JourneyLayout } from '../../lib/layout'
import type { Locale, RoomDef } from '../../lib/rooms'
import { useJourneyStore } from '../../lib/store'
import { PAST_CAPTIONS } from './rooms/palettes'

interface HudProps {
  rooms: readonly RoomDef[]
  layout: JourneyLayout
  locale: Locale
  onExit: () => void
}

const HUD_STRINGS = {
  es: {
    exit: 'Ver CV 2D',
    controls:
      'WASD / flechas — caminar · mouse — mirar · E — interactuar · M — mapa',
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
    contactTitle: 'Hablemos',
    contactBody: 'Disponible para roles de arquitectura y liderazgo tecnico.',
    email: 'Email',
    downloadCv: 'Descargar CV',
  },
  en: {
    exit: 'View 2D CV',
    controls: 'WASD / arrows — walk · mouse — look · E — interact · M — map',
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
    contactTitle: "Let's talk",
    contactBody: 'Open to architecture and tech-leadership roles.',
    email: 'Email',
    downloadCv: 'Download CV',
  },
} as const

const panelStyle: CSSProperties = {
  background:
    'color-mix(in srgb, var(--color-grey-95, #0a0a0a) 82%, transparent)',
  color: 'var(--color-grey-5, #f7f7f5)',
  border:
    '1px solid color-mix(in srgb, var(--color-grey-5, #f7f7f5) 14%, transparent)',
  borderRadius: 'var(--radius-md, 12px)',
  padding: '0.6rem 0.9rem',
  fontSize: '0.85rem',
  lineHeight: 1.45,
  pointerEvents: 'none',
  backdropFilter: 'blur(6px)',
}

const contactLinkStyle: CSSProperties = {
  display: 'block',
  padding: '0.5rem 0.8rem',
  borderRadius: 8,
  border: '1px solid color-mix(in srgb, currentColor 35%, transparent)',
  color: 'inherit',
  textDecoration: 'none',
  background:
    'color-mix(in srgb, var(--color-primary, #4f6ef7) 22%, transparent)',
}

export function Hud({ rooms, layout, locale, onExit }: HudProps) {
  const zone = useJourneyStore((s) => s.zone)
  const activeId = useJourneyStore((s) => s.activeInteractableId)
  const interactables = useJourneyStore((s) => s.interactables)
  const ficha = useJourneyStore((s) => s.ficha)
  const closeFicha = useJourneyStore((s) => s.closeFicha)
  const isLocked = useJourneyStore((s) => s.isLocked)
  const past = useJourneyStore((s) => s.past)
  const contactOpen = useJourneyStore((s) => s.contactOpen)
  const closeContact = useJourneyStore((s) => s.closeContact)
  const teleportMenuOpen = useJourneyStore((s) => s.teleportMenuOpen)
  const toggleTeleportMenu = useJourneyStore((s) => s.toggleTeleportMenu)
  const audioOn = useJourneyStore((s) => s.audioOn)
  const toggleAudio = useJourneyStore((s) => s.toggleAudio)
  const [fading, setFading] = useState(false)
  const t = HUD_STRINGS[locale]
  const pastDef = past !== null ? rooms[past] : null

  const zoneLabel = (() => {
    if (pastDef) {
      return PAST_CAPTIONS[pastDef.id][locale]
    }
    if (zone.kind === 'room') {
      const room = rooms[zone.index]
      if (!room) {
        return ''
      }
      const texts = room.texts[locale]
      return `${t.roomOf(zone.index + 1, rooms.length)} — ${texts.title} (${texts.period})`
    }
    const target = rooms[zone.index + 1]
    return target ? `${t.corridorTo} ${target.texts[locale].title}` : ''
  })()

  const prompt = activeId ? interactables[activeId]?.label[locale] : null
  const fichaRoom = ficha ? rooms[ficha.roomIndex] : null

  const teleportTo = (index: number) => {
    const target = layout.rooms[index]
    if (!target) {
      return
    }
    const spawn = { x: 0, z: target.z - target.depth / 2 + 1.5 }
    setFading(true)
    const store = useJourneyStore.getState()
    store.closeAllUi()
    window.setTimeout(() => {
      const st = useJourneyStore.getState()
      if (st.past !== null) {
        st.exitPast(spawn)
      } else {
        st.requestTeleport(spawn)
      }
      st.setZone({ kind: 'room', index })
    }, 180)
    window.setTimeout(() => setFading(false), 620)
  }

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        fontFamily: 'var(--font-sans, sans-serif)',
        zIndex: 10,
      }}
    >
      {/* indicador de sala */}
      <div style={{ ...panelStyle, position: 'absolute', top: 12, left: 12 }}>
        {zoneLabel}
      </div>

      {/* salida al CV 2D + toggle de audio (opt-in) */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          right: 12,
          display: 'flex',
          gap: 8,
        }}
      >
        <button
          type="button"
          aria-pressed={audioOn}
          onClick={toggleAudio}
          style={{ ...panelStyle, pointerEvents: 'auto', cursor: 'pointer' }}
        >
          {audioOn ? t.audioOn : t.audioOff}
        </button>
        <button
          type="button"
          onClick={onExit}
          style={{ ...panelStyle, pointerEvents: 'auto', cursor: 'pointer' }}
        >
          {t.exit}
        </button>
      </div>

      {/* boton del menu de teletransporte */}
      <button
        type="button"
        onClick={toggleTeleportMenu}
        style={{
          ...panelStyle,
          position: 'absolute',
          bottom: 12,
          right: 12,
          pointerEvents: 'auto',
          cursor: 'pointer',
        }}
      >
        {t.map}
      </button>

      {/* menu de teletransporte (tecla M) */}
      {teleportMenuOpen && (
        <nav
          aria-label={t.mapTitle}
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 'min(380px, calc(100vw - 48px))',
            pointerEvents: 'auto',
            padding: '1.1rem 1.2rem',
          }}
        >
          <h2 style={{ margin: '0 0 0.7rem', fontSize: '1.05rem' }}>
            {t.mapTitle}
          </h2>
          <div
            style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
          >
            {rooms.map((def) => (
              <button
                key={def.id}
                type="button"
                onClick={() => teleportTo(def.order)}
                style={{
                  ...contactLinkStyle,
                  cursor: 'pointer',
                  textAlign: 'left',
                  font: 'inherit',
                }}
              >
                {t.roomOf(def.order + 1, rooms.length)} —{' '}
                {def.texts[locale].title} ({def.texts[locale].period})
              </button>
            ))}
          </div>
        </nav>
      )}

      {/* fade del teletransporte */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          background: '#07070b',
          opacity: fading ? 1 : 0,
          transition: 'opacity 180ms ease',
          pointerEvents: 'none',
        }}
      />

      {/* crosshair */}
      {isLocked && !ficha && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            width: 5,
            height: 5,
            marginLeft: -2.5,
            marginTop: -2.5,
            borderRadius: '50%',
            background:
              'color-mix(in srgb, var(--color-grey-5, #f7f7f5) 85%, transparent)',
          }}
        />
      )}

      {/* prompt de interaccion */}
      {isLocked && !ficha && prompt && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            bottom: '22%',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          <kbd
            style={{
              border: '1px solid currentColor',
              borderRadius: 4,
              padding: '0 0.35em',
              marginRight: '0.5em',
            }}
          >
            {t.interactKey}
          </kbd>
          {prompt}
        </div>
      )}

      {/* click para tomar el control */}
      {!isLocked && !ficha && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '1rem',
            textAlign: 'center',
          }}
        >
          {t.clickToStart}
          <div style={{ fontSize: '0.75rem', opacity: 0.75, marginTop: 4 }}>
            {t.controls}
          </div>
        </div>
      )}

      {/* hints de controles */}
      {isLocked && !ficha && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            bottom: 12,
            left: 12,
            fontSize: '0.72rem',
            opacity: 0.85,
          }}
        >
          {t.controls}
        </div>
      )}

      {/* panel de contacto (CTA de la CIMA) */}
      {contactOpen && (
        <aside
          aria-label={t.contactTitle}
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 'min(360px, calc(100vw - 48px))',
            pointerEvents: 'auto',
            padding: '1.2rem 1.3rem',
            textAlign: 'center',
          }}
        >
          <h2 style={{ margin: 0, fontSize: '1.15rem' }}>{t.contactTitle}</h2>
          <p style={{ opacity: 0.8, fontSize: '0.85rem' }}>{t.contactBody}</p>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              marginTop: '0.8rem',
            }}
          >
            <a
              href={`mailto:${profile.contacts.email}`}
              style={contactLinkStyle}
            >
              {t.email}
            </a>
            <a
              href={profile.contacts.linkedin}
              target="_blank"
              rel="noreferrer"
              style={contactLinkStyle}
            >
              LinkedIn
            </a>
            <a
              href={profile.contacts.github}
              target="_blank"
              rel="noreferrer"
              style={contactLinkStyle}
            >
              GitHub
            </a>
          </div>
          <button
            type="button"
            onClick={closeContact}
            style={{
              marginTop: '0.9rem',
              background: 'transparent',
              color: 'inherit',
              border: '1px solid currentColor',
              borderRadius: 6,
              padding: '0.3rem 0.7rem',
              cursor: 'pointer',
            }}
          >
            {t.close}
          </button>
        </aside>
      )}

      {/* ficha retos / aprendizajes */}
      {ficha && fichaRoom && (
        <aside
          aria-label={t[ficha.kind]}
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            right: 24,
            transform: 'translateY(-50%)',
            width: 'min(420px, calc(100vw - 48px))',
            maxHeight: '76vh',
            overflowY: 'auto',
            pointerEvents: 'auto',
            padding: '1.1rem 1.25rem',
          }}
        >
          <header style={{ marginBottom: '0.6rem' }}>
            <p style={{ margin: 0, opacity: 0.7, fontSize: '0.72rem' }}>
              {fichaRoom.texts[locale].title} · {fichaRoom.texts[locale].period}
            </p>
            <h2 style={{ margin: '0.15rem 0 0', fontSize: '1.05rem' }}>
              {t[ficha.kind]}
            </h2>
          </header>
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            {fichaRoom.texts[locale][ficha.kind].map((item) => (
              <li key={item} style={{ marginBottom: '0.45rem' }}>
                {item}
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={closeFicha}
            style={{
              marginTop: '0.8rem',
              background: 'transparent',
              color: 'inherit',
              border: '1px solid currentColor',
              borderRadius: 6,
              padding: '0.3rem 0.7rem',
              cursor: 'pointer',
            }}
          >
            {t.close}
          </button>
        </aside>
      )}
    </div>
  )
}
