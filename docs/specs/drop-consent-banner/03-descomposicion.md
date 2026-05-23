# 03 - Descomposicion para paralelizacion

> [README](README.md) -> [01](01-contexto-y-decision.md) ->
> [02](02-flujo-y-archivos.md) -> 03 -> [04-commits.md](04-commits.md)

Cubre la seccion 8 del formato de plan. Cada tarea atomica pasa 3 checks
(File Exclusivity, Interface Stability, Bounded Scope) y trae 6 campos
(Archivos, AC, Depende de, Paralelizable con, Verify, Done). El plan
descompone el trabajo en **7 tareas**.

## Reglas

- **File Exclusivity** (FE): dos tareas no editan el mismo archivo. Si el
  archivo aparece en ambas, la tarea con la edicion mas grande lo hace
  y la otra se mueve a despues.
- **Interface Stability** (IS): si una tarea cambia una interfaz publica
  (export, schema Zod, prop de componente), las tareas que la consumen
  van DESPUES (no en paralelo).
- **Bounded Scope** (BS): la tarea cabe en un commit y se verifica con un
  solo comando (`vitest run <archivo>`, `astro check`, `pnpm run build`,
  etc.). No se mezclan dominios.

Limite del proyecto: max ~5-7 agentes concurrentes. El plan se queda en 7
tareas + commits 1 y 10 secuenciales (plan + cierre).

## T1 — Eliminar artefactos del banner

- **Archivos**:
  - `packages/ui/src/components/CookieBanner.astro` (borrar)
  - `packages/ui/src/lib/cookie-consent.ts` (borrar)
  - `packages/ui/tests/unit/cookie-consent.test.ts` (borrar)
  - `packages/ui/src/index.ts` (modificar: quitar exports lineas 15-23)
- **AC**: AC-5, AC-6 (parcial)
- **Depende de**: T2, T3a, T3b, T4 (ningun consumidor restante)
- **Paralelizable con**: T5, T7 (si T5 NO toca `index.ts` — confirmado: T5
  toca `schemas.ts` y YAMLs, no `index.ts`)
- **Verify**: `pnpm exec tsc --noEmit && pnpm exec astro check && rg -l 'cookie-consent|CookieBanner' apps packages -g '!dist' -g '!node_modules'` -> 0 resultados
- **Done**: archivos borrados, exports de `index.ts` removidos, build de `ui` limpio
- **Checks**: FE OK (T2/T3 no tocan estos archivos). IS OK (los consumidores ya quitaron sus imports en commits previos). BS OK (un dominio: eliminacion del modulo banner).

## T2 — Simplificar track-event.ts (always-on)

- **Archivos**:
  - `packages/ui/src/lib/track-event.ts` (modificar)
  - `packages/ui/tests/unit/track-event.test.ts` (modificar)
- **AC**: AC-2, AC-6 (parcial)
- **Depende de**: nada (es la base)
- **Paralelizable con**: T3a, T3b, T5, T7 (archivos disjuntos)
- **Verify**: `pnpm --filter @portfolio/ui exec vitest run track-event`
- **Done**:
  - `track-event.ts` no exporta `hasTrackingConsent` ni `isTrackingForced`.
  - `track-event.ts` no contiene las constantes `STORAGE_CONSENT`,
    `QA_FLAG`, `QA_FLAG_VALUE`, `CONSENT_ACCEPTED`.
  - `trackEvent()` retorna `sendBeaconPayload(buildTrackPayload(...))`.
  - El test file no tiene bloques de gating; tests existentes pasan.
- **Checks**: FE OK (solo 2 archivos, propios). IS PARTIAL — `track-event.ts`
  ya no exporta `hasTrackingConsent` ni `isTrackingForced`; el unico
  consumidor externo es `packages/ui/src/index.ts:53-54` que T1 limpia.
  Como T1 depende de T2 y de los demas, no hay carrera. BS OK.

## T3a — TrackingPixel sin listener consent

- **Archivos**:
  - `packages/ui/src/components/TrackingPixel.astro` (modificar: borrar
    listener `portfolio:consent-changed` lineas 99-102)
- **AC**: AC-2, AC-3
- **Depende de**: nada
- **Paralelizable con**: T2, T3b, T4, T5, T7 (archivos disjuntos)
- **Verify**: `pnpm exec astro check` + lectura manual del diff
- **Done**: `TrackingPixel.astro` no contiene `portfolio:consent-changed`,
  el resto del flujo (`page_load` + `after-swap` + `visibilitychange`)
  intacto.
- **Checks**: FE OK. IS OK (no expone interfaz publica). BS OK.

## T3b — Footer sin boton manage-consent

- **Archivos**:
  - `packages/ui/src/components/Footer.astro` (modificar: borrar `<li>` del
    boton, el `<script>` que registra `REOPEN_BANNER_EVENT`, el import)
- **AC**: AC-4
- **Depende de**: nada
- **Paralelizable con**: T2, T3a, T4, T5, T7 (archivos disjuntos)
- **Verify**: `pnpm exec astro check` + lectura manual del diff
- **Done**: `Footer.astro` no tiene `data-testid="manage-consent"`, no
  importa `REOPEN_BANNER_EVENT`, el resto del Footer (links sociales,
  copyright) intacto. El campo `strings.manageConsent` ya no se referencia
  en el template — el `Props.strings.manageConsent` se elimina cuando T5
  actualiza el schema; mientras tanto el campo queda sin uso pero TS no
  rompe porque sigue declarado en `schemas.ts`.
- **Checks**: FE OK. IS PARTIAL — el componente sigue recibiendo
  `strings: ComponentsStrings['footer']` que sigue teniendo
  `manageConsent` hasta que T5 lo borre. Por eso T3b puede ir ANTES de
  T5 sin romper: solo deja de usar el campo. T5 lo borra del schema
  despues sin afectar al Footer.

## T4 — Quitar CookieBanner del layout y paginas hub

- **Archivos**:
  - `packages/app-shared/src/layouts/SitePageLayout.astro` (modificar)
  - `apps/hub/src/pages/index.astro` (modificar)
  - `apps/hub/src/pages/en/index.astro` (modificar)
  - `apps/hub/src/pages/contact.astro` (modificar)
- **AC**: AC-1
- **Depende de**: nada
- **Paralelizable con**: T2, T3a, T3b, T5, T7 (archivos disjuntos)
- **Verify**: `pnpm exec astro check && pnpm --filter @portfolio/hub run build`
- **Done**: ninguno de los 4 archivos contiene `import CookieBanner` ni
  `<CookieBanner ... />`. Cada uno sigue importando `TrackingPixel` y
  `Footer` como antes.
  - El `<CookieBanner ... />` se elimina junto con el prop `strings`. Las
    paginas hub usan `t.components.cookieBanner` para pasar el prop — al
    quitar el componente, el acceso a la clave queda como dead code y T5
    la elimina del schema/yaml.
- **Checks**: FE OK (4 archivos distintos, ningun otro los toca). IS OK
  (el layout sigue exponiendo la misma API a las apps). BS OK.

## T5 — Eliminar claves i18n + schema Zod

- **Archivos**:
  - `packages/content/src/schemas.ts` (modificar: borrar bloque
    `cookieBanner` y prop `manageConsent` en `footer`)
  - `packages/content/src/data/i18n/elements/elements.es.yaml` (modificar)
  - `packages/content/src/data/i18n/elements/elements.en.yaml` (modificar)
- **AC**: AC-5, AC-6 (parcial — assertion eliminado del build-strings.test.ts)
- **Depende de**: T3b y T4 (los archivos que dejaban de USAR las claves
  pero todavia las recibian via props). Si T5 va ANTES de que T3b y T4
  dejen de pasar los props, Zod rompe el parse del YAML por shape mismatch.
  -> Por eso T5 NO es paralela con T3b/T4: va DESPUES.
- **Paralelizable con**: T1, T2, T3a (no tocan estos archivos), T7
- **Verify**: `pnpm --filter @portfolio/content run typecheck && pnpm --filter @portfolio/content exec vitest run`
- **Done**:
  - `schemas.ts` no exporta el sub-schema `cookieBanner` ni la prop
    `manageConsent` en `footer`.
  - los 2 YAMLs no tienen `cookieBanner:` ni `footer.manageConsent`.
  - los tests de `pkg-content` pasan (Zod valida el shape recortado).
- **Checks**: FE OK. IS BREAKING — `ComponentsStrings['footer']` pierde
  `manageConsent`, `ComponentsStrings['cookieBanner']` desaparece. Los
  consumidores (Footer, CookieBanner, SitePageLayout, paginas hub) ya
  estan limpios en commits previos. BS OK.

## T6 — Actualizar specs E2E

- **Archivos**:
  - `tests/feature/tracking/consent.spec.ts` (borrar)
  - `tests/feature/tracking/track-pageload.spec.ts` (modificar: quitar
    `?cf_track=force`, agregar tests nuevos)
  - `tests/feature/contact/contact-funnel.spec.ts` (modificar)
  - `tests/feature/contact/contact-session-link.spec.ts` (modificar)
- **AC**: AC-7, AC-1 (via nuevo test), AC-2 (via nuevo test), AC-4 (via nuevo test)
- **Depende de**: T1, T2, T3a, T3b, T4, T5 (los specs corren contra el
  build final; si T1-T5 no terminaron, el spec falla)
- **Paralelizable con**: T7 (archivos disjuntos: T6 toca tests/feature/,
  T7 toca packages/ui/tests/unit y packages/app-shared/tests/unit)
- **Verify**: `python3 devtools/run.py docker up --env=local && python3 devtools/run.py test_runner --module=feature --type=feature --env=local`
- **Done**: `consent.spec.ts` no existe; los 3 specs restantes no
  contienen la cadena `cf_track=force`; los nuevos tests pasan.
- **Checks**: FE OK. IS OK (los specs son test code, no exponen interfaz).
  BS OK.

## T7 — Actualizar unit tests restantes

- **Archivos**:
  - `packages/ui/tests/unit/scroll-depth.test.ts` (modificar: quitar setup
    `localStorage.cf_consent`)
  - `packages/ui/tests/unit/click-tracking.test.ts` (modificar: idem)
  - `packages/app-shared/tests/unit/lib/build-strings.test.ts` (modificar:
    quitar assertions sobre `cookieBanner` y `manageConsent`)
- **AC**: AC-6 (parcial)
- **Depende de**: T2 (track-event ya emite sin gating), T5 (el shape de
  ComponentsStrings ya esta recortado para el assertion del build-strings)
- **Paralelizable con**: T1, T6 (archivos disjuntos)
- **Verify**:
  ```
  pnpm --filter @portfolio/ui exec vitest run scroll-depth
  pnpm --filter @portfolio/ui exec vitest run click-tracking
  pnpm --filter @portfolio/app-shared exec vitest run build-strings
  ```
- **Done**: los 3 archivos no tienen setup ni assertions de gating /
  cookieBanner; los tests pasan en verde.
- **Checks**: FE OK. IS OK. BS OK.

## Dependencias resumidas (grafo)

```
            (commit 1: plan)
                 |
                 v
        +--------+--------+
        |        |        |
        v        v        v
       T2      T3a     T3b      T4
        |        |       |       |
        |        |       v       v
        |        |       T5  <---+
        |        |       |
        v        v       v
       T7 <-----+        |
        |                |
        v                |
        T1 <-------------+
              |
              v
            T6
              |
              v
        (commit 10: cierre)
```

## Paralelizacion practica (3 streams)

- **Stream A**: T2 -> T7 (track-event)
- **Stream B**: T3a + T3b + T4 (UI cleanup, paralelo entre si)
- **Stream C**: T5 despues que B termine -> T1 despues que A + B + C
  terminen -> T6 al final.

Detalle de comandos / worktrees en
[05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md).

## Navegacion

- Anterior: [02-flujo-y-archivos.md](02-flujo-y-archivos.md)
- Siguiente: [04-commits.md](04-commits.md)
