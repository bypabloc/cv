# SPEC-201: CookieBanner + consentimiento GDPR

**Estado**: draft
**Fase**: 2
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `packages/ui/`, `packages/app-shared/`, `apps/*/`,
`tests/feature/`
**Dependencias**: SPEC-102 (pixel montado)
**Paralelizable con**: SPEC-200

> Anterior: [SPEC-200](SPEC-200-mapa-de-eventos.md) | Siguiente: [SPEC-202](SPEC-202-rediseno-schema-contacts.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de SPEC-102 (el pixel ya montado).

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases |
| `packages/ui/src/components/CookieBanner.astro` | Componente que ya existe; esta spec lo integra y pule (i18n + a11y) |
| `packages/ui/src/components/TrackingPixel.astro` | Escucha `portfolio:consent-changed`; misma key `cf_consent` |
| `packages/ui/src/index.ts` | Barrel de `@portfolio/ui` (se exporta `CookieBanner`) |
| `packages/app-shared/src/layouts/SitePageLayout.astro` | Layout de 5 apps donde se monta el banner; pasa `locale` |
| `apps/hub/src/layouts/PageLayout.astro` | hub no usa `SitePageLayout`: montar el banner aparte |
| `packages/ui/src/components/Footer.astro` | Se le agrega el enlace de gestion de consentimiento |
| `packages/ui/src/lib/track-event.ts` (de SPEC-200) | El gating de eventos usa la misma key `cf_consent` |
| `tests/feature/` | Patron de specs Playwright |

### Rules del proyecto aplicables

- `.claude/rules/astro-landing.md` — componentes Astro, TS strict, Biome
- `.claude/rules/design-system.md` — tokens del DS, dark/light, a11y
- skill `modern-portfolios` / `astro-portfolio` — WCAG AA, EU Accessibility Act
- `tests/feature/README.md` — specs Playwright

### Decisiones del interview que aplican

- `CookieBanner` se monta y el tracking queda gated por `cf_consent`.
- El componente NO se reescribe: se integra + se agrega i18n (`locale`) y se
  revisa accesibilidad.
- Consentimiento revocable via enlace en el `Footer` (requisito GDPR).
- `localStorage` (key `cf_consent`), no cookies.

## 1. Contexto

Fase 1 monta el `TrackingPixel` pero NO el banner de consentimiento. Sin
banner, nadie da `cf_consent` y el pixel queda inerte en produccion (cumple
GDPR por defecto, pero no se recolecta nada). Esta spec monta el banner real
para que el usuario pueda dar consentimiento informado y activar el tracking.

El EU Accessibility Act es obligatorio desde junio 2025 y el sitio recibe
visitantes de la UE; el consentimiento explicito para analytics es requerido.

### Hallazgos de exploracion

- `packages/ui/src/components/CookieBanner.astro` ya existe y esta completo:
  banner sticky-bottom, botones Aceptar/Rechazar, persiste `cf_consent`
  (`'accepted'` | `'rejected'`) en `localStorage`, despacha el evento
  `portfolio:consent-changed`. Solo se muestra si el usuario no respondio aun.
- El banner NO esta montado en ningun layout ni exportado en el barrel.
- `TrackingPixel.astro` ya escucha `portfolio:consent-changed` y re-dispara el
  tracking cuando el detalle es `accepted`.
- `SitePageLayout.astro` cubre 5 apps; `hub` usa `BaseLayout` directo.
- El flag `?cf_track=force` introducido en SPEC-102 sigue existiendo para E2E.

## 2. Solucion propuesta

Esta spec es principalmente de integracion: el componente ya esta hecho.

1. **Exportar `CookieBanner`** en `packages/ui/src/index.ts`.
2. **Montar `<CookieBanner />`** en `SitePageLayout.astro` (5 apps) y en el
   layout de `hub`.
3. **Revision del componente** para Fase 2:
   - Verificar que el texto del banner es correcto y esta en es/en segun el
     `locale` del layout (hoy el texto esta hardcodeado en espanol — agregar
     soporte de `locale` via prop).
   - Asegurar que el banner es accesible: navegable con teclado (Tab + Enter),
     `role`/`aria` correctos, contraste WCAG AA, respeta el foco.
   - Confirmar que el gating de `track-event.ts` (SPEC-200) usa la misma key
     `cf_consent` — toda emision de eventos pasa por ese gate.
4. **Pagina de gestion de consentimiento**: un enlace en el `Footer` que
   permita al usuario re-abrir el banner o cambiar su decision (requisito
   GDPR: el consentimiento debe ser revocable con la misma facilidad con que
   se otorga).
5. **E2E**: cubrir el flujo aceptar / rechazar / revocar.

### Decisiones clave

- **Decision 1: el componente no se reescribe** — `CookieBanner.astro` ya
  resuelve el caso; esta spec lo integra y lo pule (i18n + accesibilidad).
- **Decision 2: `localStorage`, no cookies** — el banner usa `localStorage`
  con key `cf_consent`. No se setean cookies de terceros; el "cookie banner"
  es en realidad un consent banner privacy-friendly. Esto simplifica el
  cumplimiento (no hay cookies que declarar).
- **Decision 3: consentimiento revocable** — un enlace en el Footer reabre el
  banner. GDPR exige que retirar el consentimiento sea tan facil como darlo.
- **Decision 4: i18n por `locale`** — el texto del banner pasa a depender del
  `locale` del layout (es/en), no hardcodeado.
- **Decision 5: rechazo persistente** — si el usuario rechaza, el banner no
  reaparece (se respeta `cf_consent='rejected'`); solo el enlace del Footer
  permite reconsiderar.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un visitante sin `cf_consent` previo, When abre cualquier
  pagina de las 6 apps, Then se muestra el banner con botones Aceptar y
  Rechazar.
- **AC-2**: Given el banner visible, When el usuario hace click en Rechazar,
  Then `cf_consent` queda en `'rejected'`, el banner se oculta y NO se envia
  ningun `POST /track`.
- **AC-3**: Given el banner visible, When el usuario hace click en Aceptar,
  Then `cf_consent` queda en `'accepted'`, el banner se oculta y se emite
  `page_load` en menos de 5 s.
- **AC-4**: Given un usuario que ya respondio (aceptado o rechazado), When
  vuelve a abrir el sitio, Then el banner NO se muestra.
- **AC-5**: Given el enlace de gestion de consentimiento en el Footer, When el
  usuario lo activa, Then el banner se reabre permitiendo cambiar la decision.
- **AC-6**: Given un usuario que tenia `cf_consent='accepted'`, When revoca el
  consentimiento (Rechazar desde el banner reabierto), Then deja de emitirse
  cualquier evento de tracking.
- **AC-7**: Given el banner, When el usuario navega solo con teclado, Then
  puede alcanzar y activar ambos botones con Tab + Enter, y el foco es visible.
- **AC-8**: Given el layout en `locale='en'`, When se renderiza el banner,
  Then el texto esta en ingles; con `locale='es'`, en espanol.
- **AC-9**: Given el banner montado, When se mide Lighthouse, Then no hay
  degradacion de Performance ni de Accessibility (ambos siguen en su umbral).
- **AC-10**: Given `packages/ui/src/index.ts`, When se importa `CookieBanner`,
  Then el componente esta exportado.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
TrackingPixel montado pero inerte: sin banner nadie da cf_consent.
?cf_track=force solo sirve para E2E.
```

### Despues

```text
1a visita -> banner [Aceptar] [Rechazar]
   Rechazar -> cf_consent='rejected' -> tracking OFF
   Aceptar  -> cf_consent='accepted' -> portfolio:consent-changed
            -> TrackingPixel + track-event emiten eventos
visitas siguientes -> banner NO aparece (decision recordada)
Footer -> "Gestionar consentimiento" -> reabre banner
   permite cambiar accepted <-> rejected
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos. El consentimiento vive solo en
`localStorage` del cliente.

## 6. Tests Requeridos

### 6.B. Unit Tests

**Frontend (Vitest, `packages/ui/tests/unit/`):**

- `cookie-banner` (logica cliente): `readConsent`/`writeConsent` con
  `localStorage`; despacho de `portfolio:consent-changed` `[AC-2][AC-3]`.
- i18n: el texto cambia segun `locale` `[AC-8]`.
- gating: `track-event` no emite con `cf_consent='rejected'` `[AC-2][AC-6]`.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check`.

### 6.D. E2E Tests (Playwright)

`tests/feature/tracking/consent.spec.ts`:

- WHEN primera visita THEN banner visible `[AC-1]`.
- WHEN click Rechazar THEN sin `POST /track` `[AC-2]`.
- WHEN click Aceptar THEN `POST /track` con `page_load` `[AC-3]`.
- WHEN segunda visita tras responder THEN banner ausente `[AC-4]`.
- WHEN activo el enlace del Footer THEN banner reaparece `[AC-5]`.
- WHEN reabro y rechazo tras haber aceptado THEN cesa el tracking `[AC-6]`.
- WHEN navego con teclado THEN ambos botones alcanzables y foco visible `[AC-7]`.

## 7. Archivos Afectados

### Modificar

- `packages/ui/src/components/CookieBanner.astro` — agregar prop `locale`
  (`'es' | 'en'`) y textos i18n; revisar `role`/`aria`, orden de foco,
  contraste; opcionalmente extraer un `data-action="reopen"` para el enlace
  del Footer.
  - Por que: cumplir i18n y accesibilidad; el componente base ya existe.
  - Verificar: `pnpm exec astro check`; `consent.spec.ts` `[AC-7][AC-8]`.
- `packages/ui/src/index.ts` — exportar `CookieBanner.astro`.
  - Por que: que los layouts lo importen desde `@portfolio/ui`.
  - Verificar: `pnpm exec tsc --noEmit`; `[AC-10]`.
- `packages/app-shared/src/layouts/SitePageLayout.astro` — montar
  `<CookieBanner locale={locale} />`.
  - Por que: cubre 5 de las 6 apps de una vez.
  - Verificar: `pnpm run build`; `[AC-1]` en 5 subdominios.
- `apps/hub/src/layouts/PageLayout.astro` (o `index.astro`) — montar
  `<CookieBanner />`.
  - Por que: hub no usa `SitePageLayout`.
  - Verificar: `[AC-1]` en `hub.localhost`.
- `packages/ui/src/components/Footer.astro` — agregar el enlace "Gestionar
  consentimiento" / "Manage consent" que reabre el banner (despacha un evento
  o invoca la API de reapertura del componente).
  - Por que: GDPR exige que revocar sea tan facil como otorgar.
  - Verificar: `consent.spec.ts` `[AC-5][AC-6]`.

### Crear

- `tests/feature/tracking/consent.spec.ts` — E2E del flujo de consentimiento.
  - Verificar: `python devtools/run.py test_runner --module=feature
    --type=feature --env=local`.
- Tests unit de la logica del banner (en `packages/ui/tests/unit/`).
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `CookieBanner.astro` (i18n + a11y) + `ui/index.ts` + unit | AC-7,8,10 | SPEC-102 | T2 |
| T2 | `Footer.astro` (enlace de gestion) | AC-5,6 | SPEC-102 | T1 |
| T3 | `SitePageLayout.astro` + `hub` layout | AC-1,4 | T1 | — |
| T4 | `consent.spec.ts` (E2E) | AC-1..AC-7 | T2,T3 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Fase 1 en `main`
- [ ] SPEC-200 alineado: `track-event.ts` usa la key `cf_consent`
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-10 cubiertos por tests que pasan
- [ ] Coverage >= 80% per-file en archivos modificados
- [ ] `pnpm exec tsc --noEmit` + `pnpm exec astro check` sin errores
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` de las 6 apps exitoso
- [ ] Lighthouse: Performance y Accessibility sin degradacion `[AC-9]`
- [ ] E2E `consent.spec.ts` verde contra el stack local
- [ ] Verificado en ambos modos (dark / light) y en es/en

> Anterior: [SPEC-200](SPEC-200-mapa-de-eventos.md) | Siguiente: [SPEC-202](SPEC-202-rediseno-schema-contacts.md)
