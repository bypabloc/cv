# 07 - Validacion y Definition of Done

> [README](README.md) -> [01](01-contexto-y-decision.md) ->
> [02](02-flujo-y-archivos.md) -> [03](03-descomposicion.md) ->
> [04](04-commits.md) -> [05](05-paralelizacion-worktrees.md) ->
> [06](06-verificacion-e2e.md) -> 07

Cubre la seccion 12 del formato. Dos checklists separadas:
**Pre-implementacion** (antes de tocar codigo) y **Definition of Done**
(antes de declarar el plan completo y abrir el PR).

## Pre-implementacion

Verificar ANTES del commit 2 (primera tarea de codigo). Si alguno falla,
NO arrancar la implementacion.

- [ ] La rama actual es `feature/drop-consent-banner` (no `dev`, `stage`,
      `main`, `master`).
      Comando: `git branch --show-current`
- [ ] Los 8 archivos del plan existen en `docs/specs/drop-consent-banner/`
      (`README.md`, `01-contexto-y-decision.md`, `02-flujo-y-archivos.md`,
      `03-descomposicion.md`, `04-commits.md`,
      `05-paralelizacion-worktrees.md`, `06-verificacion-e2e.md`,
      `07-definition-of-done.md`).
      Comando: `ls docs/specs/drop-consent-banner/ | wc -l` -> 8
- [ ] El commit 1 ya esta hecho en la rama: `git log --oneline -1` muestra
      "docs(specs): documenta plan drop-consent-banner".
- [ ] Los 8 AC (AC-1..AC-8) numerados estan en `01-contexto-y-decision.md`
      y cada uno tiene al menos un test que lo cubre (ver matriz en
      seccion 3, "Trazabilidad AC -> tests").
- [ ] Los tests TDD-1..TDD-5 estan listados en
      `02-flujo-y-archivos.md` (seccion 6.A).
- [ ] Fixtures necesarios existen:
  - [ ] `tests/feature/fixtures/index.js` exporta `subdomainUrl`, `test`,
        `expect`, `Page` (verificado: lo usan los specs actuales).
  - [ ] No hace falta crear fixtures nuevos para los E2E del plan.
- [ ] Dependencias instaladas y limpias: `pnpm install` sin warnings.
- [ ] Dev server arranca limpio en al menos una app: `pnpm --filter
      @portfolio/generic exec astro dev --port 4322` (test rapido — Ctrl+C
      tras ver el "Local:" linea, no se queda corriendo).
- [ ] No hay breaking changes en APIs publicas externas al monorepo (el
      cambio de `ComponentsStrings` es interno; no se exporta a un npm
      package consumido afuera).
- [ ] `git status --short` esta limpio (solo el commit del plan en el
      `git log`; sin archivos sin commitear).

## Definition of Done

Verificar antes de declarar el plan completo y abrir el PR
`feature/drop-consent-banner -> dev`.

### Trazabilidad AC

- [ ] **AC-1** Banner ausente del DOM (E2E + visual preview).
      Test: `tests/feature/tracking/track-pageload.spec.ts` ('Given
      carga inicial Then NO existe banner ni manage-consent').
- [ ] **AC-2** `page_load` emitido en cold start sin opt-in (E2E POST
      capture).
      Test: `tests/feature/tracking/track-pageload.spec.ts` ('Given
      carga inicial sin opt-in Then emite page_load auto').
- [ ] **AC-3** `spa_navigation` + `page_exit` se emiten sin gating (E2E).
      Test: `tests/feature/tracking/track-pageload.spec.ts` (test
      existente simplificado sin `?cf_track=force`).
- [ ] **AC-4** Boton `manage-consent` no existe en el DOM (E2E +
      assertion en `build-strings.test.ts` removido).
- [ ] **AC-5** `pnpm exec biome check . && pnpm exec tsc --noEmit && pnpm
      exec astro check` -> exit 0; barrido `rg` sobre 10 keywords -> 0
      resultados.
- [ ] **AC-6** Vitest recursivo verde; `cookie-consent.test.ts` no
      existe; bloques de gating eliminados en
      `track-event.test.ts`/`scroll-depth.test.ts`/`click-tracking.test.ts`;
      assertion sobre `cookieBanner`/`manageConsent` eliminado en
      `build-strings.test.ts`.
- [ ] **AC-7** Playwright suite verde; `consent.spec.ts` no existe;
      cero `cf_track=force` en `tests/feature/{tracking,contact}/`.
- [ ] **AC-8** `pnpm run build` verde para las 6 apps; barrido `rg`
      sobre `apps/*/dist/` -> 0 resultados para 8 cadenas (5 keywords +
      3 textos del banner en es/en).

### Bateria seccion 11 — Parte A

- [ ] Barrido A.1 (source): `rg` sobre 10 keywords devuelve 0
      resultados.
- [ ] Barrido A.2 (dist): `rg` sobre 8 cadenas devuelve 0 resultados.
- [ ] Archivos huerfanos A.3: `cookie-consent.test.ts` y
      `consent.spec.ts` no existen.

### Bateria seccion 11 — Parte B

- [ ] B0 `pnpm install` -> exit 0, sin warnings de `allow-builds`.
- [ ] B1 `pnpm exec biome check .` -> exit 0.
- [ ] B2 `pnpm exec tsc --noEmit` -> exit 0.
- [ ] B3 `pnpm exec astro check` -> exit 0.
- [ ] B4 `pnpm exec vitest run --coverage` -> exit 0; coverage per-file
      >= 80% en los 6 archivos modificados (ver lista en seccion 11 B4).
- [ ] B5 `pnpm run build` -> exit 0, 6 `apps/*/dist/index.html` existen.
- [ ] B6 = A.2 sobre dist -> 0 resultados.
- [ ] B7 Preview visual de las 6 apps: ningun banner abajo; Footer
      muestra solo copyright + linkedin + github (sin "Gestionar
      consentimiento" / "Manage consent").
- [ ] B8 Playwright via `python3 devtools/run.py test_runner
      --module=feature --type=feature --env=local` -> todos los tests
      verdes.

### Documentacion y artefactos

- [ ] Body del PR redactado siguiendo el template del repo (Problema /
      Solucion / Como probar / TODO) — ver
      `.claude/rules/git-workflow.md`.
- [ ] PR title < 70 chars, en imperativo, en espanol, sin punto final.
      Ejemplo: `refactor(ui): elimina banner GDPR y deja tracking
      always-on`.
- [ ] No hay atribucion de IA en commits, PR, ni comentarios (politica
      del repo, ver
      `~/.claude/CLAUDE.md` -> "Git Attribution").
- [ ] El ultimo commit del plan incluye `git rm -r
      docs/specs/drop-consent-banner/` (ciclo de vida de la carpeta del
      plan, ver `.claude/rules/plan-format.md` "ciclo de vida").

### Gate de cierre (regla del repo)

- [ ] El `git push origin feature/drop-consent-banner` ocurre SOLO con
      la bateria de la seccion 11 verde completa — NO antes.
- [ ] El PR a `dev` se crea SOLO con la bateria en verde — NO antes.
- [ ] CI del repo (`quality-gates` + `e2e-tests`) pasa antes de
      `gh pr merge --merge --delete-branch`.

### Estado final esperado

- `feature/drop-consent-banner` mergeada a `dev` con merge commit.
- 10 commits limpios en el historial.
- 0 archivos en `apps/`, `packages/`, `tests/` referencian las 10
  keywords del plan.
- `docs/specs/drop-consent-banner/` ya no existe en `dev`.
- 6 apps en preview muestran tracking activo desde el primer page view
  (verificable abriendo devtools -> Network -> `/track` -> hay POST).
- 0 banners visibles en cualquier ruta.

## Anti-patrones (recordatorio)

- Marcar un AC como done sin que su test asociado pase.
- Considerar el plan "casi listo" porque pasan 7 de 8 AC: TODO el
  Definition of Done debe estar verde.
- Saltarse la Parte A del `rg` porque "ya hice el grep manualmente":
  rg con las 10 keywords es la fuente de verdad.
- `git push --force` o reescribir historial despues de abrir el PR.
- Cerrar el plan sin eliminar `docs/specs/drop-consent-banner/`.

## Navegacion

- Anterior: [06-verificacion-e2e.md](06-verificacion-e2e.md)
- Volver al inicio: [README](README.md)
