# 04 - Commits

> [README](README.md) -> [01](01-contexto-y-decision.md) ->
> [02](02-flujo-y-archivos.md) -> [03](03-descomposicion.md) -> 04 ->
> [05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md)

Cubre la seccion 9 del formato. **10 commits** que implementan el plan,
cada uno con mensaje Conventional Commits en espanol pre-redactado,
verificacion incremental antes de commitear (no diferida al final),
trazabilidad a AC y a tareas (T1-T7) del [03-descomposicion.md](03-descomposicion.md).

## Reglas por commit

- Cada commit deja el repo verde: `pnpm exec biome check .` + el verify de
  la tarea pasan ANTES de commitear.
- Conventional Commits en espanol (`refactor`, `test`, `docs`, `chore`)
  segun el tipo. Subject < 70 chars, sin punto final, en imperativo.
- Body: lista de bullets con `-`. Cada bullet es un cambio concreto.
- Sin atribucion de IA (politica del repo, ver `.claude/rules/git-workflow.md`).
- El commit 10 incluye el `git rm -r docs/specs/drop-consent-banner/` y
  ejecuta la bateria completa de la seccion 11.

## Commit 1 — Plan

**Tarea**: ninguna (crear el plan).
**AC**: N/A (es la documentacion del plan).
**Mensaje**:

```
docs(specs): documenta plan drop-consent-banner

- Crea docs/specs/drop-consent-banner/ con 8 archivos (README + 01..07)
- Documenta contexto: banner GDPR mata la senal de tracking porque el
  default es localStorage.cf_consent=null y el gating bloquea POST /track
- Documenta solucion: tracking always-on sin UI ni gating, simplifica
  packages/ui/src/lib/track-event.ts, elimina CookieBanner, cookie-consent.ts,
  boton manage-consent del Footer, claves i18n cookieBanner y manageConsent
- Documenta 8 criterios de aceptacion (AC-1..AC-8) verificables con biome,
  tsc, astro check, vitest, build, rg y Playwright
- Decompone en 7 tareas con File Exclusivity + Interface Stability
- Lista 10 commits con verificacion incremental por commit
- Bateria E2E final en seccion 11 (gate del PR feature -> dev)
```

**Verify**: `ls docs/specs/drop-consent-banner/` lista 8 archivos
(`README.md` + `01..07.md`).
**Commit**: `git add docs/specs/drop-consent-banner/ && git commit -m "..."`

## Commit 2 — T2: track-event always-on

**Tarea**: T2.
**AC**: AC-2, AC-6 (parcial).
**Mensaje**:

```
refactor(ui): simplifica track-event a always-on

- Elimina las constantes STORAGE_CONSENT, QA_FLAG, QA_FLAG_VALUE y
  CONSENT_ACCEPTED de packages/ui/src/lib/track-event.ts
- Elimina las funciones hasTrackingConsent() y isTrackingForced()
- trackEvent() pasa a llamar directo a sendBeaconPayload(buildTrackPayload(...))
  sin gating de consentimiento ni bypass por query param
- Actualiza el docstring del modulo (quita la nota de GATING)
- Actualiza packages/ui/tests/unit/track-event.test.ts: elimina los
  bloques que probaban gating + flag QA, conserva los tests de
  buildTrackPayload, generateEventId, getSessionId, sendBeaconPayload,
  configureTracking y el happy path de trackEvent
- packages/ui/src/index.ts: deja de exportar hasTrackingConsent e
  isTrackingForced
```

**Verify**:

```
pnpm --filter @portfolio/ui exec vitest run track-event
pnpm exec biome check packages/ui/src/lib/track-event.ts \
  packages/ui/tests/unit/track-event.test.ts \
  packages/ui/src/index.ts
```

**Done**: tests verdes, biome ok, `index.ts` ya no exporta las funciones.

## Commit 3 — T3a: TrackingPixel sin listener consent

**Tarea**: T3a.
**AC**: AC-2, AC-3.
**Mensaje**:

```
refactor(ui): remueve listener consent-changed del TrackingPixel

- Elimina el listener portfolio:consent-changed del script en
  packages/ui/src/components/TrackingPixel.astro (lineas 99-102)
- page_load se sigue emitiendo en cold start via requestIdleCallback
  (codigo intacto), spa_navigation por astro:after-swap y page_exit
  por visibilitychange
- El flag window.__cfTrackingPixelInit sigue protegiendo contra doble
  registro en View Transitions
```

**Verify**:

```
pnpm exec astro check
pnpm exec biome check packages/ui/src/components/TrackingPixel.astro
```

**Done**: `rg -l "consent-changed" packages/ui/src/components/TrackingPixel.astro` -> 0 resultados.

## Commit 4 — T3b: Footer sin boton manage-consent

**Tarea**: T3b.
**AC**: AC-4.
**Mensaje**:

```
refactor(ui): remueve boton Gestionar consentimiento del Footer

- Elimina el <li> con el <button data-action="reopen-consent"> del
  template de packages/ui/src/components/Footer.astro
- Elimina el import REOPEN_BANNER_EVENT
- Elimina el <script> initManageConsent() y su registro en
  astro:after-swap
- Elimina los estilos .site-footer__consent y :focus-visible
  asociados
- El campo Props.strings.manageConsent queda sin uso temporalmente
  (lo elimina el commit 7 cuando recorta ComponentsStrings['footer'])
```

**Verify**:

```
pnpm exec astro check
pnpm exec biome check packages/ui/src/components/Footer.astro
```

**Done**: `rg -l "manage-consent|REOPEN_BANNER_EVENT" packages/ui/src/components/Footer.astro` -> 0 resultados.

## Commit 5 — T4: layout + paginas hub sin CookieBanner

**Tarea**: T4.
**AC**: AC-1.
**Mensaje**:

```
refactor(app-shared,hub): elimina CookieBanner del layout y paginas hub

- packages/app-shared/src/layouts/SitePageLayout.astro: elimina el
  import de CookieBanner y el <CookieBanner ... /> al cierre del
  layout (lineas 26 y 138 aprox)
- apps/hub/src/pages/index.astro: elimina el import y el <CookieBanner ... />
- apps/hub/src/pages/en/index.astro: idem
- apps/hub/src/pages/contact.astro: idem
- Las 6 apps usan el layout o lo inyectan a mano: ninguna instancia
  el banner ya
- El acceso a t.components.cookieBanner queda como dead code
  temporal; el commit 7 elimina la clave del schema y los YAMLs
```

**Verify**:

```
pnpm exec astro check
pnpm exec biome check packages/app-shared/src/layouts/SitePageLayout.astro \
  apps/hub/src/pages/index.astro \
  apps/hub/src/pages/en/index.astro \
  apps/hub/src/pages/contact.astro
pnpm --filter @portfolio/hub run build
pnpm --filter @portfolio/generic run build
```

**Done**: build de hub + generic pasa; `rg -l 'CookieBanner' apps packages -g '!dist' -g '!node_modules'` solo encuentra el archivo
`packages/ui/src/components/CookieBanner.astro` (que se borra en commit 6) y la libreria `cookie-consent.ts`.

## Commit 6 — T1: borra CookieBanner.astro y cookie-consent.ts

**Tarea**: T1.
**AC**: AC-5 (parcial), AC-6 (parcial).
**Depende de**: commits 2, 3, 4, 5 (no quedan consumidores).
**Mensaje**:

```
refactor(ui): elimina CookieBanner.astro y cookie-consent.ts

- Elimina packages/ui/src/components/CookieBanner.astro
- Elimina packages/ui/src/lib/cookie-consent.ts
- Elimina packages/ui/tests/unit/cookie-consent.test.ts
- Elimina los 7 exports relacionados de packages/ui/src/index.ts:
  ConsentValue, CONSENT_CHANGED_EVENT, isConsentValue,
  REOPEN_BANNER_EVENT, readConsent, STORAGE_KEY, writeConsent
- Quedan limpios todos los puntos de entrada: ningun componente, layout,
  pagina, util ni tests referencia el banner ni la libreria de consent
```

**Verify**:

```
pnpm exec tsc --noEmit
pnpm exec astro check
pnpm --filter @portfolio/ui exec vitest run
rg -l 'CookieBanner|cookie-consent|REOPEN_BANNER_EVENT|CONSENT_CHANGED_EVENT' \
  apps packages -g '!dist' -g '!node_modules' -g '!docs/specs'
# Esperado: 0 resultados
```

**Done**: los 3 archivos no existen, `index.ts` no los exporta, el barrido
da 0 resultados, tsc + astro check + vitest verdes.

## Commit 7 — T5: elimina claves i18n + schema Zod

**Tarea**: T5.
**AC**: AC-5, AC-6 (parcial).
**Depende de**: commits 4 y 5 (los archivos que recibian las props ya las
ignoran).
**Mensaje**:

```
refactor(content): elimina claves cookieBanner y footer.manageConsent

- packages/content/src/schemas.ts: elimina el sub-schema
  cookieBanner: z.object({ ... }) (6 campos) del ComponentsStringsSchema
- packages/content/src/schemas.ts: elimina la prop manageConsent del
  sub-schema footer
- packages/content/src/data/i18n/elements/elements.es.yaml: elimina el
  bloque cookieBanner (6 lineas) y la clave footer.manageConsent
- packages/content/src/data/i18n/elements/elements.en.yaml: idem
- Cambio breaking en ComponentsStrings: ya no tiene cookieBanner y
  footer pierde manageConsent. Los consumidores estan limpios desde
  los commits 4-6.
```

**Verify**:

```
pnpm --filter @portfolio/content run typecheck
pnpm --filter @portfolio/content exec vitest run
pnpm exec tsc --noEmit
pnpm exec astro check
rg -l 'cookieBanner|manageConsent' \
  apps packages -g '!dist' -g '!node_modules' -g '!docs/specs'
# Esperado: 0 resultados
```

**Done**: schema + YAMLs limpios; typecheck recursivo y vitest del
content pasan; ningun archivo source referencia las claves.

## Commit 8 — T7: actualiza unit tests restantes

**Tarea**: T7.
**AC**: AC-6 (parcial).
**Depende de**: commits 2 (track-event sin gating) y 7 (shape recortado).
**Mensaje**:

```
test(ui,app-shared): actualiza unit tests para tracking always-on

- packages/ui/tests/unit/scroll-depth.test.ts: elimina el setup
  beforeEach que seteaba localStorage.cf_consent='accepted'; los tests
  pasan sin ese setup porque trackEvent ya no requiere consentimiento
- packages/ui/tests/unit/click-tracking.test.ts: idem
- packages/app-shared/tests/unit/lib/build-strings.test.ts: elimina
  las assertions sobre t.components.cookieBanner.* y
  t.components.footer.manageConsent (claves ya no existen en
  ComponentsStrings)
```

**Verify**:

```
pnpm --filter @portfolio/ui exec vitest run scroll-depth click-tracking
pnpm --filter @portfolio/app-shared exec vitest run build-strings
pnpm exec biome check packages/ui/tests/unit/scroll-depth.test.ts \
  packages/ui/tests/unit/click-tracking.test.ts \
  packages/app-shared/tests/unit/lib/build-strings.test.ts
```

**Done**: 3 archivos de test sin setup/assertions de gating; tests verdes.

## Commit 9 — T6: actualiza specs E2E

**Tarea**: T6.
**AC**: AC-7, AC-1, AC-2, AC-4 (nuevos tests).
**Depende de**: commits 2-8.
**Mensaje**:

```
test(feature): elimina consent.spec y quita cf_track=force de E2E

- Elimina tests/feature/tracking/consent.spec.ts completo (8 tests del
  banner GDPR ya no aplican)
- tests/feature/tracking/track-pageload.spec.ts: quita todas las
  apariciones de ?cf_track=force (URLs simplificadas a subdomainUrl()/...)
- tests/feature/tracking/track-pageload.spec.ts: agrega 2 tests nuevos
  - 'Given carga inicial Then NO existe banner ni manage-consent [AC-1, AC-4]'
  - 'Given carga inicial sin opt-in Then emite page_load auto [AC-2]'
- tests/feature/contact/contact-funnel.spec.ts: quita ?cf_track=force
- tests/feature/contact/contact-session-link.spec.ts: quita ?cf_track=force
  y el cleanup de localStorage.cf_consent
- Las helpers disableSendBeacon y captureTrackRequests se inlinen en
  track-pageload.spec.ts (estaban solo en consent.spec.ts)
```

**Verify**:

```
pnpm exec biome check tests/feature/tracking/track-pageload.spec.ts \
  tests/feature/contact/contact-funnel.spec.ts \
  tests/feature/contact/contact-session-link.spec.ts

# Stack arriba
python3 devtools/run.py docker up --env=local
# Build estatico de las 6 apps (lo necesita el stack test/preview)
# El stack local sirve dev: si los tests fallan por HMR, usar --env=test
python3 devtools/run.py test_runner --module=feature --type=feature --env=local
```

**Done**: 4 specs (3 modificados + 0 eliminados restantes en `tracking/`),
suite verde, `rg -l 'cf_track=force' tests/feature -g '!node_modules'` -> 0.

## Commit 10 — Verificacion E2E iterativa + limpieza del plan

**Tarea**: la fase final del plan (seccion 11).
**AC**: todos (gate del PR).
**Depende de**: commits 1-9.
**Mensaje**:

```
chore(plan): cierra drop-consent-banner y elimina la carpeta del plan

- Bateria de verificacion E2E completa (seccion 11): biome + tsc +
  astro check + vitest --coverage + build de las 6 apps + Playwright
  contra el stack local
- Barrido global con rg sobre las 10 keywords del plan: 0 resultados
  en apps/ packages/ tests/ (excluyendo dist y node_modules)
- Verifica que ninguna apps/*/dist contiene CookieBanner ni el texto
  del banner en es ni en en
- Elimina docs/specs/drop-consent-banner/ (carpeta efimera del plan,
  cf. .claude/rules/plan-format.md "ciclo de vida")
```

**Verify** (bateria completa, ver
[06-verificacion-e2e.md](06-verificacion-e2e.md) para detalle):

```
# Parte A: barrido global
rg -l 'CookieBanner|cookie-consent|cf_consent|cf_track|REOPEN_BANNER_EVENT|CONSENT_CHANGED_EVENT|hasTrackingConsent|isTrackingForced|cookieBanner|manageConsent' \
  apps packages tests -g '!dist' -g '!node_modules' -g '!docs/specs'
# Esperado: 0 resultados

# Parte B: bateria completa
pnpm install
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec astro check
pnpm exec vitest run --coverage   # >=80% per-file
pnpm run build                    # 6 apps

# E2E
python3 devtools/run.py docker up --env=local
python3 devtools/run.py test_runner --module=feature --type=feature --env=local

# Build limpio del banner
rg -l 'auto-borran en 60|Permitis recolectar|let us collect|auto-delete in 60' apps/*/dist
# Esperado: 0 resultados
```

**Limpieza del plan**:

```
git rm -r docs/specs/drop-consent-banner/
```

**Commit final**: incluye TODOS los cambios anteriores que esten staged +
la eliminacion de la carpeta. El mensaje arriba lo refleja.

**Done**: bateria completa en verde; ningun archivo del repo referencia
las 10 keywords; `docs/specs/drop-consent-banner/` ya no existe; rama
`feature/drop-consent-banner` lista para `git push` + PR.

## Secuencia de ejecucion resumida

```
1 (plan)            -> escribir docs/specs/drop-consent-banner/
2 (T2)              -> track-event always-on
3 (T3a) | 4 (T3b)   -> TrackingPixel + Footer cleanup  (paralelo)
5 (T4)              -> SitePageLayout + 3 paginas hub
6 (T1)              -> borra CookieBanner.astro + cookie-consent.ts
7 (T5)              -> schema Zod + YAMLs
8 (T7) | 9 (T6)     -> tests unit + E2E  (paralelo)
10 (cierre)         -> bateria seccion 11 + git rm carpeta plan
```

3, 4 y 5 son paralelos entre si (archivos disjuntos). 8 y 9 son
paralelos entre si. El resto secuencial. Detalle de worktrees en
[05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md).

## Pull Request

- Base: `dev`
- Head: `feature/drop-consent-banner`
- Merge strategy: merge commit (politica del repo)
- Comando: `gh pr merge --merge --delete-branch`
- Body del PR: copiar la seccion "Problema / Solucion / Como probar / TODO"
  (template del repo, ver `.claude/rules/git-workflow.md` "Estructura del
  body de un PR").

## Navegacion

- Anterior: [03-descomposicion.md](03-descomposicion.md)
- Siguiente: [05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md)
