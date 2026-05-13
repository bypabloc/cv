---
title: Diseno Visual y UX
parent: modern-portfolios
section: 05
---

[← Anterior: Estructura](04-estructura-contenido.md) | [README](README.md) | [Siguiente → Tecnologias](06-tecnologias.md)

# Diseno Visual y UX

## Tendencias Visuales 2025-2026

El panorama visual se divide en **tres esteticas competitivas**:

| Estetica | Caracteristica | Usado por | Riesgo |
|----------|---------|---------|---------|
| **Nature Distilled** | Earthy tones, minimalismo sofisticado | Design studios, agencies | Puede parecer corporate |
| **Maximalism** | Rich colors, bold fonts, densa composition | Edgy brands, creatives | Si no esta bien hecho, parece amateur |
| **Retrofuturism** | Neon, chrome, pixel art, sci-fi vibes | Tech companies, portfolios | Muy especifico, puede datar rapido |

**Recomendacion para developers 2026**: Minimalismo funcional con **animated micro-interactions** (no animaciones grandes que ralenticen). La tendencia ganadora es:

```
[Interfaz limpia y rapida] + [Animaciones sutiles] = Portfolio efectivo
```

## Dark Mode + Light Mode (OBLIGATORIO)

**Dato de 2026**: 82.7% de usuarios usan dark mode en dispositivos. Entre tech audiences, el numero es 81.9%.

**Recomendacion:**
- Dark mode como default
- Toggle visible (esquina superior derecha, tipicamente)
- Ambos modos deben verse bien (no es "agregar dark theme", es disenar DOS interfaces)

**Herramientas recomendadas:**
- `next-themes` (Next.js)
- CSS variables con `:root.dark` override (Astro, HTML puro)
- Tailwind v4 `dark:` utilities

## Core Web Vitals (CRITICO)

Google tightenó los umbrales en Marzo 2026:

| Metrica | Umbral 2025 | Umbral Marzo 2026 | Estado de Industria |
|---------|---------|---------|---------|
| **LCP** (loading) | 2.5s | **2.0s** | 62% de mobile pages lo alcanzan (mas dificil) |
| **INP** (interactivity) | 200ms | 200ms | Estable |
| **CLS** (layout shift) | < 0.1 | < 0.1 | 81% de mobile pages OK (mejor metrica) |

**Objetivo para tu portfolio:** 100% en Core Web Vitals en mobile + desktop.

**Herramientas de validacion:**
- Google PageSpeed Insights (gratis, oficial)
- GTmetrix (mas detalles)
- WebPageTest

## Accesibilidad (WCAG 2.2, Obligatorio)

**Context:** EU Accessibility Act obligatorio desde Junio 2025, ADA deadline en Abril 2026.

**Minimo cumplimiento: WCAG AA**

| Requisito | Implementacion |
|----------|---------|
| 4.5:1 color contrast | Verificar con WebAIM Contrast Checker |
| Keyboard accessibility | Todos los botones navegables con Tab |
| Image alt text | Describir imagen, no "image.jpg" |
| Semantic HTML | `<button>` no `<div onclick>`, `<nav>`, `<main>`, etc |
| Form labels | Cada input tiene label asociado |

**Herramienta:** axe DevTools (Chrome extension, free)

**Anti-pattern:** "Agrego accessibility al final". WCAG AA debe ser built-in desde diseno.

---

[← Anterior: Estructura](04-estructura-contenido.md) | [README](README.md) | [Siguiente → Tecnologias](06-tecnologias.md)
