# 01 - Contexto + Solucion + AC

[README](README.md) | [02 packages/seo >](02-fase-packages-seo.md)

## 1. Contexto / Problema

Audit `ai_audit` corrio contra prod 2026-05-25 y dio promedio
**63/100** en 6 niches. Findings detallados:

### Hallazgos clave

- **robots.txt**: prod sirve la version managed de Cloudflare
  "Content Signals" (Disallow para Amazonbot, Applebot-Extended,
  Bytespider, CCBot, ClaudeBot, Google-Extended, etc.). El robots.txt
  del repo (allow-all + AI bots) NO se respeta. Es decision del
  owner.
- **sitemap.xml**: el sitio sirve `/sitemap-index.xml` (XML 200) pero
  NO `/sitemap.xml` (404 → Astro renderea home). Validator del audit
  chequea solo `/sitemap.xml` → falla.
- **isitagentready (level 2/5)**:
  - contentAccessibility 0% — Markdown content negotiation falta
    (requiere Worker, fuera de scope).
  - discovery 0% — falta `Link` headers + `.well-known/api-catalog`
    + OAuth metadata (N/A: portfolio sin OAuth).
  - discoverability 67% — Link headers falta.
- **lighthouse_psi (99/100)**: unica falla es `color-contrast`
  (accessibility 97). Tokens `--color-text-subtle` y
  `--color-text-muted` no pasan WCAG AA en small text.
- **JSON-LD**: ya tiene ProfilePage + Person. Falta WebSite.

### Arquitectura compartida descubierta

`packages/seo` exporta builders (`buildHeaders`, `buildLlmsTxt`,
`buildRobotsTxt`) que `apps/*/scripts/build-public-assets.mjs`
usa en prebuild para generar los publicos. Implica que TODO cambio
"compartido entre apps" se hace UNA vez en `packages/seo` y se
refleja en los 6 prebuild scripts (cambio pequeno por app).

## 2. Solucion Propuesta

5 grupos de cambios, ordenados por scope:

1. **packages/seo**: 3 builders nuevos + actualizar `buildHeaders`
   - `buildHeaders` agrega 3 directivas `Link` (sitemap, llms,
     api-catalog) + override `Content-Type` para `.well-known/api-catalog`
   - nuevo `buildRedirects` → genera `/sitemap.xml → /sitemap-index.xml 301`
   - nuevo `buildApiCatalog` → JSON shape RFC9727 + endpoints serverless
   - nuevo `buildWebSiteSchema` → JSON-LD WebSite (complementa ProfilePage)
   - tests en `packages/seo/tests/unit/` para cada builder

2. **packages/ui**: subir 2 tokens de color (dark + light)
   - `--color-text-subtle` (dark) y `--color-text-muted` (light)
     1 paso de la escala greys para pasar WCAG AA

3. **devtools/ai_audit**: validator
   - `validate_robots_ai_bots` detecta firma "Cloudflare Managed
     Content Signals" y devuelve `neutral` (no `fail`)
   - `tools/validators.py._fetch_all` fallback a `sitemap-index.xml`
     si `sitemap.xml` 404
   - tests nuevos en `devtools/tests/unit/src/ai_audit/`

4. **apps/*/scripts/build-public-assets.mjs**: actualizar los 6
   - llamar `buildRedirects`, `buildApiCatalog` y escribir
     `_redirects` y `.well-known/api-catalog`
   - cambio identico en los 6 (cada uno ~5 lineas nuevas)

5. **packages/app-shared**: incluir `buildWebSiteSchema` en el
   JSON-LD del layout (donde ya se incluye ProfilePage)

Cierre: validar skills con `claude -p`, re-correr audit, comparar,
eliminar carpeta del plan, push, PR a dev.

### Decisiones clave

- **Decision 1**: NO desactivar Cloudflare Content Signals — mantiene
  postura anti AI-training. Validator se adapta (`neutral`).
- **Decision 2**: Markdown content negotiation se DEFIERE — requiere
  Worker. Si abre valor concreto, plan separado.
- **Decision 3**: Sitemap se sirve en ambos paths via redirect
  `_redirects`, no via duplicacion fisica.
- **Decision 4**: API Catalog usa shape `RFC9727` (linkset) —
  estandar reconocido por crawlers IA.
- **Decision 5**: Color contrast: subir 1 paso de escala greys.
  Cambio visual minimo, ganancia WCAG AA garantizada.
- **Decision 6**: TODO archivo compartido vive en `packages/*`,
  nunca duplicado en `apps/*/public/`.

## 3. Criterios de Aceptacion

- **AC-1**: Given un audit corriendo en prod, When termina, Then el
  promedio sube de 63 a >= 85.
- **AC-2**: Given `validators` tool chequea sitemap, When prod sirve
  `/sitemap-index.xml`, Then check pasa (status `pass`).
- **AC-3**: Given el validator de robots.txt detecta firma
  Cloudflare-managed, When AI bots estan bloqueados dentro de ese
  bloque, Then status `neutral` con detalle `managed: true`.
- **AC-4**: Given un audit lighthouse_psi en prod, When termina,
  Then `accessibility` == 100.
- **AC-5**: Given prod redeployado, When un crawler hace HEAD al
  home, Then incluye 3 headers `Link` (sitemap, llms, api-catalog).
- **AC-6**: Given `/.well-known/api-catalog` se sirve, When se
  descarga, Then es JSON valido con shape `{linkset: [...]}` (RFC9727).
- **AC-7**: Given un crawler parsea el home, When extrae JSON-LD,
  Then encuentra TANTO `ProfilePage` (con Person) COMO `WebSite`.
- **AC-8**: Given los archivos modificados de `.claude/*`, When se
  ejecuta `claude -p` con 5 prompts en espanol (matriz
  claude-config-testing.md), Then todos retornan `num_turns > 1` y
  el contenido refleja stack actual (3 tools, sin menciones de las
  descartadas).
- **AC-9**: Given el codigo final, When `pnpm run build` corre, Then
  los 6 sites compilan sin errores.
- **AC-10**: Given el codigo final, When `python devtools/run.py
  test_runner --module=devtools --type=unit` corre, Then los 785+
  tests pasan.

[README](README.md) | [02 packages/seo >](02-fase-packages-seo.md)
