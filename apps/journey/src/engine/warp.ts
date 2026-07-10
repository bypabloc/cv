/**
 * @module warp (engine)
 * @description Tunel de cruce dimensional (rediseño 2026-07-10): overlay
 *   WebGL de UN quad fullscreen con shader propio, renderizado ENCIMA del
 *   frame en una escena + camara orto aparte. NO es EffectComposer ni
 *   postfx del mundo (el canon toon limpio queda intacto): +1 draw call y
 *   SOLO mientras hay un cruce en curso. Reemplaza al fade CSS 'warp' /
 *   'dream' en tier full. Dos modos, ambos continuos y fluidos: 'warp' =
 *   tunel-wormhole (succion ~0.85 s, tunel sostenido durante la carga,
 *   vineta radial que abre ~1.15 s); 'dream' = despertar de un sueño
 *   (bruma calida + parpados que se abren, salida ~1.5 s). El HUD
 *   conserva el fade DOM para tier reduced y reduced-motion.
 */
import {
  Color,
  Mesh,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  ShaderMaterial,
  type WebGLRenderer,
} from 'three'

export type WarpStyle = 'warp' | 'dream'

export interface WarpTunnel {
  /** Mismo contrato que hud.fade: resuelve al cubrir / al revelar. */
  fade(on: boolean, style: WarpStyle): Promise<void>
  /** Un paso del overlay; llamar DESPUES del render principal. */
  render(): void
  dispose(): void
}

/** Paleta por estilo: 'warp' azul-blanco-gris (cruce entre salas, misma
 *  familia que el wormhole re-decidido 2026-07-10), 'dream' ambar/papel
 *  (grieta al pasado) — misma familia que TEAR_STYLES. */
const WARP_PALETTES = {
  warp: { a: '#eaf3ff', b: '#3d6fb0', warm: 0 },
  dream: { a: '#ffd9a0', b: '#b4763c', warm: 1 },
} as const

/** Duraciones por estilo: el despertar del sueño es mas lento y suave. */
const COVER_MS = {
  warp: { in: 850, out: 1150 },
  dream: { in: 900, out: 1500 },
} as const

const WARP_VERT = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`

// Dos modos, ambos CONTINUOS y fluidos (cero glitch, cero bandas):
// - warp (uWarm=0): tunel-wormhole — streaks radiales torcidos fluyendo,
//   anillos, nucleo blanco; la cobertura cierra/abre como vineta radial.
// - dream (uWarm=1): "despertar de un sueño" — bruma calida con nubes que
//   derivan lento y PARPADOS que se cierran/abren desde el centro (el
//   reveal de salida es literalmente abrir los ojos).
const WARP_FRAG = `
  uniform float uTime;
  uniform float uCover;
  uniform float uWarm;
  uniform vec3 uColA;
  uniform vec3 uColB;
  uniform float uAspect;
  varying vec2 vUv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
  }
  float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  void main() {
    vec2 p = (vUv - 0.5) * vec2(uAspect, 1.0);
    float r = length(p);

    if (uWarm > 0.5) {
      // DREAM: bruma calida + parpados (despertar de un sueño)
      float clouds = vnoise(p * 2.2 + vec2(uTime * 0.07, uTime * 0.05));
      vec3 col = mix(vec3(1.0), uColA, smoothstep(0.05, 0.85, r));
      col = mix(col, uColB, clouds * 0.22);
      // apertura de parpados: cerrados con cover=1, abren desde el centro
      float aperture = (1.0 - uCover * 1.35) * 0.62;
      float lid = smoothstep(
        aperture, aperture + 0.14 + clouds * 0.1, abs(vUv.y - 0.5)
      );
      // luz entrando por el filo del parpado al abrir los ojos
      float rim = smoothstep(0.0, 0.5, lid) * smoothstep(1.0, 0.5, lid);
      col += vec3(1.0, 0.98, 0.9) * rim * 0.8;
      if (lid < 0.004) {
        discard;
      }
      gl_FragColor = vec4(col, lid);
      return;
    }

    // WARP: tunel de dilatacion espacio-tiempo — streaks torcidos fluyendo
    // (continuo), con la misma lente gravitacional del wormheole (el
    // radio se comprime hacia el centro) para que atravesar el portal se
    // sienta como la MISMA fisica, no un efecto distinto.
    float ang = atan(p.y, p.x);
    float rLens = pow(min(r, 1.0), 1.5);
    float twist = ang + (1.0 - rLens) * 1.8 + uTime * 0.25;
    float t = uTime * 4.2;
    float split = 0.05 * uCover;
    float sG = pow(vnoise(vec2(twist * 8.0, rLens * 3.2 - t)), 3.0);
    float sR = pow(vnoise(vec2((twist + split) * 8.0, rLens * 3.2 - t)), 3.0);
    float sB = pow(vnoise(vec2((twist - split) * 8.0, rLens * 3.2 - t)), 3.0);
    float ring = pow(0.5 + 0.5 * sin(rLens * 16.0 - t * 2.0), 6.0);
    vec3 col = mix(vec3(1.0), uColA, smoothstep(0.0, 0.32, rLens));
    col = mix(col, uColB, smoothstep(0.3, 0.75, rLens));
    col = mix(col, vec3(0.01, 0.012, 0.02), smoothstep(0.7, 1.15, rLens));
    col += uColA * sG * 0.85;
    // fringe cromatico sutil DENTRO de la familia azul-blanco-gris (antes
    // magenta/cian fijos, rompian la paleta pedida por el dueno).
    col += mix(uColB, vec3(1.0), 0.6) * sR * 0.35;
    col += mix(uColB, vec3(0.5, 0.6, 0.75), 0.4) * sB * 0.35;
    col += mix(uColB, vec3(1.0), 0.5) * ring * 0.4;
    // anillo de fotones: linea nitida justo en el horizonte (rRaw real,
    // no el radio comprimido) — la firma visual de la curvatura extrema.
    col += vec3(1.0) * smoothstep(0.05, 0.0, abs(r - 0.62)) * 0.7;
    col += vec3(1.0) * smoothstep(0.16, 0.0, rLens);

    // vineta radial que cierra (succion) y abre (llegada), sin bandas
    float rev = (1.0 - uCover) * 1.4 - 0.32;
    float alpha = smoothstep(rev, rev + 0.3, r + sG * 0.18);
    if (alpha < 0.004) {
      discard;
    }
    gl_FragColor = vec4(col, alpha);
  }
`

export function createWarpTunnel(renderer: WebGLRenderer): WarpTunnel {
  const scene = new Scene()
  // el vertex shader ignora la camara (quad en clip space); three la exige
  const camera = new OrthographicCamera(-1, 1, 1, -1, 0, 1)
  const colA = new Color(WARP_PALETTES.warp.a)
  const colB = new Color(WARP_PALETTES.warp.b)
  const material = new ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uCover: { value: 0 },
      uWarm: { value: 0 },
      uColA: { value: colA },
      uColB: { value: colB },
      uAspect: { value: 1 },
    },
    vertexShader: WARP_VERT,
    fragmentShader: WARP_FRAG,
    transparent: true,
    depthTest: false,
    depthWrite: false,
  })
  const quad = new Mesh(new PlaneGeometry(2, 2), material)
  quad.frustumCulled = false
  scene.add(quad)

  let cover = 0
  let anim: {
    from: number
    to: number
    start: number
    dur: number
    resolve(): void
  } | null = null

  /** Cierra la animacion en curso (resuelve su promesa). */
  function settle(): void {
    if (anim) {
      anim.resolve()
      anim = null
    }
  }

  return {
    fade(on, style) {
      const pal = WARP_PALETTES[style]
      colA.set(pal.a)
      colB.set(pal.b)
      material.uniforms.uWarm.value = pal.warm
      settle() // un fade nuevo pisa al anterior (mismo contrato que el HUD)
      return new Promise((resolve) => {
        anim = {
          from: cover,
          to: on ? 1 : 0,
          start: performance.now(),
          dur: COVER_MS[style][on ? 'in' : 'out'],
          resolve,
        }
      })
    },

    render() {
      const now = performance.now()
      if (anim) {
        const k = Math.min(1, (now - anim.start) / anim.dur)
        // succion acelerando al entrar; reveal suavizado al salir
        const e = anim.to > anim.from ? k * k : k * k * (3 - 2 * k)
        cover = anim.from + (anim.to - anim.from) * e
        if (k >= 1) {
          cover = anim.to
          settle()
        }
      }
      if (cover <= 0) {
        return
      }
      material.uniforms.uTime.value = now / 1000
      material.uniforms.uCover.value = cover
      const el = renderer.domElement
      material.uniforms.uAspect.value = el.width / Math.max(el.height, 1)
      const prevAutoClear = renderer.autoClear
      renderer.autoClear = false
      renderer.render(scene, camera)
      renderer.autoClear = prevAutoClear
    },

    dispose() {
      settle()
      quad.geometry.dispose()
      material.dispose()
    },
  }
}
