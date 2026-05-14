# Integracion del widget en Astro / JavaScript

> Como cargar el script, renderizar el widget, manejar callbacks,
> y gestionar tokens en el frontend.

[← Modos](./02-modes-comparison.md) | [Siguiente: Backend Python →](./04-backend-validation-python.md)

## 1. Cargar el script de Turnstile

En el layout principal (`src/layouts/BaseLayout.astro`):

```astro
---
// En el frontmatter (TypeScript)
// No necesitas importar nada, el script global lo hace
---

<html lang="es">
  <head>
    <!-- ... otros metas ... -->
    <script
      async
      defer
      src="https://challenges.cloudflare.com/turnstile/v0/api.js"
    ></script>
  </head>
  <body>
    <slot />
  </body>
</html>
```

**Flags importantes:**
- `async` — descarga sin bloquear HTML parsing
- `defer` — ejecuta despues que HTML se carga

Despues de cargar, la API global `turnstile` estara disponible en `window`.

## 2. Renderizar el widget (forma implicita)

La forma mas simple: agregar un `<div>` con clase `cf-turnstile`:

```astro
---
// En un componente Astro
interface Props {
  sitekey: string
  onSuccess?: (token: string) => void
}

const { sitekey } = Astro.props
---

<div
  class="cf-turnstile"
  data-sitekey={sitekey}
  data-theme="managed"
  data-callback="onTurnstileSuccess"
></div>

<script>
  // Callback global que Turnstile invoca automaticamente
  window.onTurnstileSuccess = (token: string) => {
    console.log('Token Turnstile:', token)
    // Guardar token en un input hidden del form
    const input = document.querySelector('input[name="cf-token"]')
    if (input) input.value = token
  }
</script>
```

El widget se renderiza automaticamente cuando el script termina de cargar.

## 3. Renderizar el widget (forma explicita con turnstile.render())

Para control mas fino (SPAs, Astro Islands con hydration):

```astro
---
// Componente Astro con client:load
interface Props {
  sitekey: string
  containerId: string
}

const { sitekey, containerId } = Astro.props
---

<div id={containerId}></div>

<script define:vars={{ sitekey, containerId }}>
  // Usar define:vars para pasar variables Astro a cliente
  if (window.turnstile) {
    window.turnstile.render(`#${containerId}`, {
      sitekey: sitekey,
      theme: 'managed',
      callback: (token) => {
        console.log('Token generado:', token)
        // Dispatch evento custom o llamar handler
        document.dispatchEvent(
          new CustomEvent('turnstile-token', { detail: { token } })
        )
      },
      'error-callback': () => {
        console.error('Error en Turnstile')
      },
      'expired-callback': () => {
        console.warn('Token expirado, regenerando')
        window.turnstile.reset(`#${containerId}`)
      },
      'timeout-callback': () => {
        console.warn('Timeout en Turnstile')
      },
    })
  } else {
    console.error('Script Turnstile no cargo')
  }
</script>
```

## 4. Opciones de configuracion

| Opcion | Tipo | Descripcion |
|--------|------|-------------|
| `sitekey` | string | PUBLICA, no exponer secret |
| `theme` | "light" \| "dark" \| "auto" | Tema visual |
| `callback` | function | Invocado cuando token generado |
| `error-callback` | function | Invocado si hay error |
| `expired-callback` | function | Token expiro (5 min) |
| `timeout-callback` | function | Timeout en desafio |
| `action` | string | Identificador custom (max 32 chars) |
| `cdata` | string | Datos adicionales custom |
| `size` | "normal" \| "compact" \| "flexible" | Tamano widget |
| `appearance` | "always" \| "execute" \| "interaction-only" | Cuando mostrar |
| `language` | "es" \| "en" \| "auto" | Idioma |

## 5. Manejo de tokens y expiración

Tokens expiran **5 minutos** desde generacion. Patron correcto:

```javascript
let lastToken = null
let tokenGeneratedAt = null

window.onTurnstileSuccess = (token) => {
  lastToken = token
  tokenGeneratedAt = Date.now()

  // Llenar input hidden del form
  document.querySelector('input[name="cf-token"]').value = token

  // Habilitar boton submit
  document.querySelector('button[type="submit"]').disabled = false
}

// Antes de submit, verificar que token NO expiro
document.querySelector('form').addEventListener('submit', (e) => {
  const ageMs = Date.now() - tokenGeneratedAt
  const ageMins = ageMs / 1000 / 60

  if (ageMins > 5) {
    e.preventDefault()
    console.error('Token expirado, regenerando')
    // Llamar regenerar
    window.turnstile.reset()
    alert('Por favor resuelve el captcha nuevamente')
    return
  }

  // Token fresco, OK para submit
  console.log('Token valido, enviando form')
})
```

## 6. Form HTML con token Turnstile

```astro
---
// Componente ContactForm.astro
interface Props {
  turnstileSitekey: string
}

const { turnstileSitekey } = Astro.props
---

<form method="POST" action="/api/contact">
  <label>
    Nombre
    <input type="text" name="name" required />
  </label>

  <label>
    Email
    <input type="email" name="email" required />
  </label>

  <label>
    Mensaje
    <textarea name="message" required></textarea>
  </label>

  <!-- Widget Turnstile -->
  <div
    class="cf-turnstile"
    data-sitekey={turnstileSitekey}
    data-theme="managed"
    data-callback="onTurnstileSuccess"
  ></div>

  <!-- Token Turnstile (enviado con form) -->
  <input type="hidden" name="cf-token" value="" />

  <button type="submit">Enviar</button>
</form>

<script>
  window.onTurnstileSuccess = (token) => {
    const input = document.querySelector('input[name="cf-token"]')
    if (input) input.value = token
    console.log('Token Turnstile recibido:', token)
  }
</script>
```

## 7. Errores comunes

- ❌ Exponiendo sitekey en variable de entorno `SECRET_*` — debe ser PUBLIC
- ❌ No cargar el script con `async defer` — causa race conditions
- ❌ Ignorar token expiración — siempre verificar timestamp
- ❌ No validar token en backend — lo hace cualquiera puede spammear
- ❌ Llamar `turnstile.render()` antes de que el script cargue
