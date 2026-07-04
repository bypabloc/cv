/**
 * @module audio (engine)
 * @description Audio PROCEDURAL via WebAudio (cero archivos, cero peso de
 *   red — coherente con procedural-first). Dos capas:
 *   - AmbientAudio: room-tone por sala (hum electrico, pad, aire).
 *   - SfxEngine: efectos por proximidad (tecleo de NPCs, hum de portales,
 *     holograma, brisa del A/C), pasos (jugador + NPCs caminantes) y
 *     one-shots (puerta, boot de PC, whoosh de portal).
 *   El contexto se crea recien tras el PRIMER gesto del usuario (autoplay
 *   policy); el toggle del HUD silencia TODO (ambiente + SFX).
 *
 *   ponytail: sintesis simple (osciladores + noise buffer). Si se quiere
 *   mas riqueza, el swap es a clips CC0 en AudioBufferSource — la interfaz
 *   (enable/disable/setRoom/feed/play) no cambia.
 */
import type { RoomId } from '../lib/rooms'

interface Voice {
  stop: () => void
}

function makeNoiseBuffer(ctx: AudioContext, seconds = 2): AudioBuffer {
  const buffer = ctx.createBuffer(1, ctx.sampleRate * seconds, ctx.sampleRate)
  const data = buffer.getChannelData(0)
  let last = 0
  for (let i = 0; i < data.length; i += 1) {
    // brown-ish noise: integracion de ruido blanco
    const white = Math.random() * 2 - 1
    last = (last + 0.02 * white) / 1.02
    data[i] = last * 3.5
  }
  return buffer
}

function noiseVoice(
  ctx: AudioContext,
  out: GainNode,
  cutoffHz: number,
  gain: number,
): Voice {
  const source = ctx.createBufferSource()
  source.buffer = makeNoiseBuffer(ctx)
  source.loop = true
  const filter = ctx.createBiquadFilter()
  filter.type = 'lowpass'
  filter.frequency.value = cutoffHz
  const g = ctx.createGain()
  g.gain.value = gain
  source.connect(filter).connect(g).connect(out)
  source.start()
  return {
    stop: () => {
      source.stop()
      source.disconnect()
    },
  }
}

function oscVoice(
  ctx: AudioContext,
  out: GainNode,
  frequency: number,
  gain: number,
  type: OscillatorType = 'sine',
  detune = 0,
): Voice {
  const osc = ctx.createOscillator()
  osc.type = type
  osc.frequency.value = frequency
  osc.detune.value = detune
  const g = ctx.createGain()
  g.gain.value = gain
  osc.connect(g).connect(out)
  osc.start()
  return {
    stop: () => {
      osc.stop()
      osc.disconnect()
    },
  }
}

function profileFor(ctx: AudioContext, out: GainNode, room: RoomId): Voice[] {
  switch (room) {
    case 'corpoelec':
      // hum electrico: fundamental 60 Hz + armonico 120 + aire
      return [
        oscVoice(ctx, out, 60, 0.05, 'sine'),
        oscVoice(ctx, out, 120, 0.028, 'triangle'),
        noiseVoice(ctx, out, 500, 0.02),
      ]
    case 'cima':
      // pad sintetico premium: dos senos detuneados + sub
      return [
        oscVoice(ctx, out, 110, 0.03, 'sine', -6),
        oscVoice(ctx, out, 165, 0.022, 'sine', 6),
        oscVoice(ctx, out, 55, 0.025, 'sine'),
      ]
    default:
      // aula: room-tone calido (solo aire filtrado)
      return [noiseVoice(ctx, out, 320, 0.035)]
  }
}

/** Singleton del audio ambiente. Crear/activar SOLO tras gesto de usuario. */
export class AmbientAudio {
  private ctx: AudioContext | null = null
  private master: GainNode | null = null
  private voices: Voice[] = []
  private room: RoomId | null = null

  enable(room: RoomId): void {
    if (!this.ctx) {
      this.ctx = new AudioContext()
      this.master = this.ctx.createGain()
      this.master.gain.value = 0.6
      this.master.connect(this.ctx.destination)
    }
    void this.ctx.resume()
    this.setRoom(room, true)
  }

  disable(): void {
    this.stopVoices()
    this.room = null
    if (this.ctx) {
      void this.ctx.suspend()
    }
  }

  setRoom(room: RoomId, force = false): void {
    if (!this.ctx || !this.master) {
      return
    }
    if (!force && (this.room === room || this.ctx.state !== 'running')) {
      return
    }
    this.stopVoices()
    this.room = room
    this.voices = profileFor(this.ctx, this.master, room)
  }

  private stopVoices(): void {
    for (const voice of this.voices) {
      voice.stop()
    }
    this.voices = []
  }
}

export const ambientAudio = new AmbientAudio()

// ---------------------------------------------------------------------------
// SFX: emitters por proximidad (keep-alive) + one-shots + pasos
// ---------------------------------------------------------------------------

/**
 * Fuentes continuas alimentadas por keep-alive: el dueño (NPC, portal,
 * holograma, A/C) llama `feed(id, kind, x, z)` en su update de CADA frame;
 * una fuente que deja de alimentarse >0.3 s se apaga sola — cero wiring de
 * dispose entre salas.
 */
export type FeedKind = 'typing' | 'portal' | 'holo' | 'breeze'

/** Efectos disparados una vez (volumen fijo, no posicionales). */
export type OneShot = 'door' | 'boot' | 'whoosh' | 'breeze-on'

/** Alcance (m) por tipo de fuente: mas alla, gain 0. */
const FEED_RANGE: Record<FeedKind, number> = {
  typing: 5,
  portal: 7.5,
  holo: 5,
  breeze: 6,
}

interface Feed {
  kind: FeedKind
  x: number
  z: number
  lastFed: number
  gain: GainNode
  voices: Voice[]
  /** typing: momento del proximo click programado. */
  nextClick: number
}

/** gain 0..1 por distancia (curva suave hacia el borde del rango). */
function proximityGain(d: number, range: number): number {
  const k = 1 - d / range
  return k <= 0 ? 0 : k * k
}

export class SfxEngine {
  private ctx: AudioContext | null = null
  private master: GainNode | null = null
  private noise: AudioBuffer | null = null
  private muted = false
  private listenerX = 0
  private listenerZ = 0
  private now = 0
  private readonly feeds = new Map<string, Feed>()

  /** Crea/reanuda el contexto. Llamar SOLO tras un gesto del usuario. */
  unlock(): void {
    if (!this.ctx) {
      this.ctx = new AudioContext()
      this.master = this.ctx.createGain()
      this.master.gain.value = this.muted ? 0 : 0.9
      this.master.connect(this.ctx.destination)
      this.noise = makeNoiseBuffer(this.ctx, 1.5)
    }
    void this.ctx.resume()
  }

  /** El toggle del HUD silencia TODO el sfx (el ambiente va aparte). */
  setMuted(on: boolean): void {
    this.muted = on
    if (this.ctx && this.master) {
      this.master.gain.setTargetAtTime(on ? 0 : 0.9, this.ctx.currentTime, 0.1)
    }
    if (on) {
      this.stopAllFeeds()
    }
  }

  /** Posicion del jugador (referencia de proximidad), cada frame. */
  setListener(x: number, z: number): void {
    this.listenerX = x
    this.listenerZ = z
  }

  /**
   * Keep-alive de una fuente continua: llamar cada frame mientras exista.
   * Si deja de llamarse (la sala se desmonto), la voz muere sola.
   */
  feed(id: string, kind: FeedKind, x: number, z: number): void {
    if (!this.ctx || !this.master || this.muted) {
      return
    }
    let feed = this.feeds.get(id)
    if (!feed) {
      const gain = this.ctx.createGain()
      gain.gain.value = 0
      gain.connect(this.master)
      feed = {
        kind,
        x,
        z,
        lastFed: this.now,
        gain,
        voices: this.startFeedVoices(kind, gain),
        nextClick: this.now + Math.random() * 0.3,
      }
      this.feeds.set(id, feed)
    }
    feed.x = x
    feed.z = z
    feed.lastFed = this.now
  }

  /** Un paso en (x, z): volumen por distancia (self = el jugador). */
  stepAt(x: number, z: number, self = false): void {
    const ctx = this.ctx
    if (!ctx || !this.master || this.muted) {
      return
    }
    const gain = self ? 0.16 : 0.3 * proximityGain(this.distanceTo(x, z), 7)
    if (gain < 0.01) {
      return
    }
    // golpe sordo: noise burst lowpass + variacion leve de tono
    this.burst({
      duration: 0.07,
      gain: gain * (0.85 + Math.random() * 0.3),
      filterType: 'lowpass',
      frequency: 260 + Math.random() * 80,
    })
  }

  /** One-shots de interaccion (volumen fijo — el jugador esta al lado). */
  play(name: OneShot): void {
    const ctx = this.ctx
    if (!ctx || !this.master || this.muted) {
      return
    }
    if (name === 'door') {
      // chirrido de madera: sawtooth barriendo hacia abajo + golpe seco
      this.sweep({
        type: 'sawtooth',
        from: 170,
        to: 70,
        duration: 0.42,
        gain: 0.045,
      })
      this.burst({
        duration: 0.05,
        gain: 0.12,
        filterType: 'lowpass',
        frequency: 400,
        delay: 0.4,
      })
      return
    }
    if (name === 'boot') {
      // beep doble de encendido
      this.beep(660, 0.07, 0.055, 0)
      this.beep(990, 0.09, 0.055, 0.11)
      return
    }
    if (name === 'whoosh') {
      // succion temporal: noise con bandpass barriendo hacia arriba
      this.burst({
        duration: 0.9,
        gain: 0.3,
        filterType: 'bandpass',
        frequency: 320,
        frequencyTo: 2400,
      })
      return
    }
    // breeze-on: el A/C arranca (swell de aire)
    this.burst({
      duration: 1.6,
      gain: 0.22,
      filterType: 'lowpass',
      frequency: 900,
      attack: 0.8,
    })
  }

  /** Scheduling de clicks + gain por distancia + poda de feeds muertos. */
  update(dt: number): void {
    this.now += dt
    const ctx = this.ctx
    if (!ctx || !this.master) {
      return
    }
    for (const [id, feed] of this.feeds) {
      if (this.now - feed.lastFed > 0.3) {
        for (const voice of feed.voices) {
          voice.stop()
        }
        feed.gain.disconnect()
        this.feeds.delete(id)
        continue
      }
      const prox = proximityGain(
        this.distanceTo(feed.x, feed.z),
        FEED_RANGE[feed.kind],
      )
      feed.gain.gain.setTargetAtTime(prox, ctx.currentTime, 0.12)
      if (feed.kind === 'typing' && prox > 0.02 && this.now >= feed.nextClick) {
        // rafagas de tecleo con pausas de "pensar"
        feed.nextClick =
          this.now +
          (Math.random() < 0.16
            ? 0.5 + Math.random() * 0.9
            : 0.06 + Math.random() * 0.13)
        this.burst({
          duration: 0.028,
          gain: 0.4,
          filterType: 'bandpass',
          frequency: 2200 + Math.random() * 1800,
          out: feed.gain,
        })
      }
    }
  }

  dispose(): void {
    this.stopAllFeeds()
    if (this.ctx) {
      void this.ctx.close()
      this.ctx = null
      this.master = null
      this.noise = null
    }
  }

  private distanceTo(x: number, z: number): number {
    return Math.hypot(x - this.listenerX, z - this.listenerZ)
  }

  private stopAllFeeds(): void {
    for (const feed of this.feeds.values()) {
      for (const voice of feed.voices) {
        voice.stop()
      }
      feed.gain.disconnect()
    }
    this.feeds.clear()
  }

  /** Voces continuas de un feed (el gain lo modula update por distancia). */
  private startFeedVoices(kind: FeedKind, out: GainNode): Voice[] {
    const ctx = this.ctx
    if (!ctx) {
      return []
    }
    if (kind === 'portal') {
      // hum grave del vortice + aire oscuro
      return [
        oscVoice(ctx, out, 46, 0.16, 'sine'),
        oscVoice(ctx, out, 92, 0.05, 'triangle'),
        this.noiseLoop(out, 220, 0.09),
      ]
    }
    if (kind === 'holo') {
      // shimmer cristalino: dos senos batiendo
      return [
        oscVoice(ctx, out, 620, 0.02, 'sine'),
        oscVoice(ctx, out, 623.5, 0.02, 'sine'),
      ]
    }
    if (kind === 'breeze') {
      return [this.noiseLoop(out, 850, 0.16)]
    }
    // typing: sin loop — los clicks los agenda update()
    return []
  }

  private noiseLoop(out: GainNode, cutoffHz: number, gain: number): Voice {
    const ctx = this.ctx
    if (!ctx || !this.noise) {
      // sin contexto todavia: voz muda (no hay nada que detener)
      return { stop: () => undefined }
    }
    const source = ctx.createBufferSource()
    source.buffer = this.noise
    source.loop = true
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = cutoffHz
    const g = ctx.createGain()
    g.gain.value = gain
    source.connect(filter).connect(g).connect(out)
    source.start()
    return {
      stop: () => {
        source.stop()
        source.disconnect()
      },
    }
  }

  /** Rafaga de ruido filtrado con envolvente (click, paso, whoosh, aire). */
  private burst(opts: {
    duration: number
    gain: number
    filterType: BiquadFilterType
    frequency: number
    frequencyTo?: number
    attack?: number
    delay?: number
    out?: GainNode
  }): void {
    const ctx = this.ctx
    const master = opts.out ?? this.master
    if (!ctx || !master || !this.noise) {
      return
    }
    const t0 = ctx.currentTime + (opts.delay ?? 0)
    const source = ctx.createBufferSource()
    source.buffer = this.noise
    source.loop = true
    const filter = ctx.createBiquadFilter()
    filter.type = opts.filterType
    filter.frequency.setValueAtTime(opts.frequency, t0)
    if (opts.frequencyTo !== undefined) {
      filter.frequency.linearRampToValueAtTime(
        opts.frequencyTo,
        t0 + opts.duration,
      )
    }
    const g = ctx.createGain()
    const attack = Math.min(opts.attack ?? 0.008, opts.duration / 2)
    g.gain.setValueAtTime(0, t0)
    g.gain.linearRampToValueAtTime(opts.gain, t0 + attack)
    g.gain.exponentialRampToValueAtTime(0.001, t0 + opts.duration)
    source.connect(filter).connect(g).connect(master)
    source.start(t0)
    source.stop(t0 + opts.duration + 0.05)
    source.onended = () => source.disconnect()
  }

  /** Oscilador con barrido de frecuencia (chirrido de puerta). */
  private sweep(opts: {
    type: OscillatorType
    from: number
    to: number
    duration: number
    gain: number
  }): void {
    const ctx = this.ctx
    if (!ctx || !this.master) {
      return
    }
    const t0 = ctx.currentTime
    const osc = ctx.createOscillator()
    osc.type = opts.type
    osc.frequency.setValueAtTime(opts.from, t0)
    osc.frequency.linearRampToValueAtTime(opts.to, t0 + opts.duration)
    const g = ctx.createGain()
    g.gain.setValueAtTime(0, t0)
    g.gain.linearRampToValueAtTime(opts.gain, t0 + 0.03)
    g.gain.exponentialRampToValueAtTime(0.001, t0 + opts.duration)
    osc.connect(g).connect(this.master)
    osc.start(t0)
    osc.stop(t0 + opts.duration + 0.02)
    osc.onended = () => osc.disconnect()
  }

  /** Beep cuadrado corto (boot de PC, tablero). */
  private beep(
    frequency: number,
    duration: number,
    gain: number,
    delay: number,
  ): void {
    const ctx = this.ctx
    if (!ctx || !this.master) {
      return
    }
    const t0 = ctx.currentTime + delay
    const osc = ctx.createOscillator()
    osc.type = 'square'
    osc.frequency.value = frequency
    const g = ctx.createGain()
    g.gain.setValueAtTime(0, t0)
    g.gain.linearRampToValueAtTime(gain, t0 + 0.006)
    g.gain.exponentialRampToValueAtTime(0.001, t0 + duration)
    osc.connect(g).connect(this.master)
    osc.start(t0)
    osc.stop(t0 + duration + 0.02)
    osc.onended = () => osc.disconnect()
  }
}

export const sfx = new SfxEngine()
