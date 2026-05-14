# Comparacion de modos: Managed vs Non-Interactive vs Invisible

> Tres modos de widget Turnstile con distintos niveles de UX y proteccion.
> Elegir segun el caso de uso.

[← Arquitectura](./01-architecture.md) | [Siguiente: Frontend →](./03-frontend-integration.md)

## Resumen rapido

| Modo | Widget visible | UX | Proteccion | Ideal para | Config |
|------|----------------|-----|-----------|-----------|--------|
| **Managed** | Checkbox (a veces) | Excelente | Adaptativa (mejor) | **FORM de contacto** | `data-theme="managed"` |
| **Non-Interactive** | No | Buena | Basada en signals | Tracking pixel | `data-theme="non-interactive"` |
| **Invisible** | No, hidden | Perfecta | Basada en signals | Tracking pixel | `data-theme="invisible"` |

## Managed (RECOMENDADO para form de contacto)

### Como funciona

Cloudflare decide **automaticamente** si mostrar un desafio basandose en risk score
del visitante. Risk signals incluyen:

- Comportamiento del browser (mouse movement, scroll, keyboard)
- Headers HTTP (User-Agent, referer)
- Network patterns (velocidad de conexion, tiempo de respuesta)
- Actividad sospechosa (velocidad inhuman, patrones bot)

### UX

- Usuarios legit: **ningun desafio**, pasan invisiblemente (invisible)
- Usuarios sospechosos: **checkbox interactivo** ("I'm not a robot")
- Usuarios muy sospechosos: **desafio mas duro** (PoW, API probes)

### Ventajas

- **Mejor UX**: 95% usuarios no ven nada (zero friction)
- **Mejor proteccion**: adaptive difficulty segun risk
- **Cloudflare lo mantiene**: tipos de desafio evolucionan automaticamente

### Desventajas

- No puedes elegir que tipo de desafio mostrar (black box)
- Si Cloudflare tiene algun problema, tienes zero fallback

## Non-Interactive (OPCIONAL: tracking pixel)

### Como funciona

**Invisible**, siempre. Corre desafios de proof-of-work y APIs probes
**sin interaccion del usuario**. Genera token si pasa; falla silenciosamente si no.

### UX

Perfecta — usuario NO ve nada. Ideal para tracking pixel o endpoint que
necesita "confirma que eres un browser real" sin molestar.

### Ventajas

- Invisible, zero UX friction
- Automatico (no requiere callback custom)

### Desventajas

- **Menos efectivo contra bots sofisticados** (no hay interaccion como barrera)
- Si el bot tiene poder computacional, puede pasar PoW

## Invisible

### Como funciona

Identico a Non-Interactive pero **widget completamente oculto** (no aparece
ni el badge pequeno de Cloudflare). Ideal si quieres "desaparicion total".

### UX

Perfecta. Usuario no ve nada, no hay badge.

### Ventajas

- Invisible 100% (ni badge visible)
- Cero friccion

### Desventajas

- Mismo: menos efectivo contra bots sofisticados
- Requisito legal en muchas jurisdicciones: si muestras un widget, debe
  poder identificarse. Hidden completo en Invisible podria violar normas.

## Decision para este portfolio

### Form de contacto

**USAR MANAGED**. Razon: balanceo optimo entre UX (la mayoria pasa invisible)
y proteccion (adapt a risk). El usuario que spammea veras un checkbox y
sera rechazado. El usuario legit no ve nada.

Config Astro:

```astro
<div
  class="cf-turnstile"
  data-sitekey="..."
  data-theme="managed"
  data-callback="onTurnstileSuccess"
/>
```

### Tracking pixel

**USAR INVISIBLE** (o Non-Interactive). Razon: necesitas confirmar que
es un browser real, sin molestar al usuario. Hidden es perfecta porque
el pixel ya es invisible.

```astro
<div
  id="tracking-widget"
  class="cf-turnstile"
  data-sitekey="..."
  data-theme="invisible"
  data-action="track"
  data-cdata="pixel_visitor"
/>
```

## Anti-pattern comun

Usar Invisible para TODOS los formularios (form de contacto + tracking).
Problema: Invisible es menos efectivo y podrias generar tokens falsos.
Para form, Managed + checkbox es **mejor**. Para tracking, Invisible es OK.
