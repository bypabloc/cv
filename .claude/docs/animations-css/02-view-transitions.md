# View Transitions API

> Anima transiciones entre estados del DOM (single page) o entre paginas
> distintas (multi-page, sin SPA). Astro 6 incluye soporte nativo.
>
> Soporte 2026: Chrome 126+, Edge 126+, Safari 18.2+, Firefox 144+ — > 85%
> de share global. Es ranking #3 en State of CSS 2025 de incompatibilidades,
> pero ya viable con fallback graceful.

## Conceptos

### Same-document (SPA-like)

```ts
// Cambio de estado anidado en una sola pagina
document.startViewTransition(() => {
  applyDOMChanges()
})
```

El browser captura snapshots antes/despues y hace un crossfade automatico.

### Cross-document (MPA)

Para navegacion entre paginas del mismo origin, basta con CSS:

```css
@view-transition {
  navigation: auto;
}
```

Cuando el usuario hace clic en un link interno, el browser hace un fade
suave entre paginas. Sin JS adicional.

### Elementos compartidos

Si dos paginas tienen un elemento con el mismo `view-transition-name`, el
browser anima la transicion (escala, posicion, color):

```css
.hero-logo {
  view-transition-name: rz-hero-logo;
}
```

## Astro 6 — `<ClientRouter />`

Astro provee un componente que habilita transitions cross-document con
sintaxis declarativa:

```astro
---
import { ClientRouter } from 'astro:transitions'
---
<head>
  <ClientRouter />
</head>
```

Con eso, los links internos hacen view transition automatico (con polyfill
para Safari < 18).

Sin embargo: en el landing portfolio **NO usamos ClientRouter** por dos razones:
1. **Bundle**: agrega ~5KB para una feature ya nativa en 85% de browsers.
2. **Las paginas son lo suficientemente diferentes** (CL vs PE vs Pronto vs
   index): un crossfade entre ellas no aporta narrativa adicional.

Cuando agreguemos morph entre states dentro de una misma pagina (ej. abrir
detail de un plan en pricing), evaluaremos `document.startViewTransition`
nativo.

## Cuando si usarlo

- **Single-element morph**: card que se expande a detail (mismo origen,
  mismo nombre `view-transition-name`).
- **Tab switcher animado**: cambia el contenido visible sin recargar.
- **Filter result list**: items que aparecen/desaparecen suavemente.

## Pseudo-elementos de la transition

```css
::view-transition-old(rz-hero-logo) {
  animation: fade-out 200ms cubic-bezier(0.2, 0, 0, 1);
}
::view-transition-new(rz-hero-logo) {
  animation: fade-in 200ms cubic-bezier(0.2, 0, 0, 1);
}
```

## Browser support

- **Chrome 126+**: cross-document + same-document
- **Safari 18.2+**: cross-document + same-document
- **Firefox 144+ (oct 2025)**: cross-document + same-document
- **Polyfill**: existe pero es pesado (~10KB). Mejor: graceful degradation
  (sin transition, navegacion normal).

## prefers-reduced-motion

Las view transitions respetan automaticamente la preferencia del SO.
Si el usuario la activo, el browser hace un cambio instantaneo sin animar.

Adicionalmente, podemos overridear:

```css
@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation: none !important;
  }
}
```

## Fuentes

- [MDN - View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API)
- [MDN - Using View Transitions](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using)
- [Chrome - View transitions docs](https://developer.chrome.com/docs/web-platform/view-transitions)
- [Chrome - Cross-document view transitions](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)
- [Astro - View Transitions guide](https://docs.astro.build/en/guides/view-transitions/)
