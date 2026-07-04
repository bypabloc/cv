/**
 * @module audio (engine)
 * @description Audio ambiente PROCEDURAL via WebAudio (cero archivos, cero
 *   peso de red — coherente con procedural-first): perfiles por sala
 *   (aula: room-tone suave; corpoelec: hum electrico 60/120 Hz; cima: pad
 *   sintetico). SIEMPRE opt-in: el contexto se crea recien tras el gesto
 *   del usuario (toggle del HUD) — nunca autoplay. Movido 1:1 desde
 *   components/three/ambient-audio.ts (ya era vanilla).
 *
 *   ponytail: sintesis simple (osciladores + noise buffer). Si se quiere
 *   mas riqueza, el swap es a clips CC0 en AudioBufferSource — la interfaz
 *   (enable/disable/setRoom) no cambia.
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
