# Spec: agent discovery .well-known (categoria discovery de isitagentready)

> Mejorar la categoria `discovery` de isitagentready (hoy ~todo-fail) de forma
> HONESTA: servir 3 archivos `.well-known` legitimos que describen la API
> publica de CV (api-catalog RFC 9727, a2a agent-card, agent-skills index)
> extendiendo el `_worker.js` de Cloudflare Pages Advanced Mode que ya existe,
> y arreglar el bug de los `.well-known` OAuth que hoy sirven el HTML del home
> (SPA fallback) -> 404 limpio. Plan Small/Medium.

## Cuando leer

| Tema | Archivo | Cuando |
|------|---------|--------|
| Contexto + decision + AC | este README (1-3) | Antes de implementar |
| Arquitectura del Worker | este README (seccion 2) | Para entender donde van las rutas |
| Commits | este README (seccion 9) | Al ejecutar |
| Verificacion | este README (seccion 11) | Gate de cierre |

## Estado por fase

- [ ] Fase 1 — builders nuevos en packages/seo (agent-card, agent-skills)
- [ ] Fase 2 — extender el Worker (rutas nuevas + 404 OAuth)
- [ ] Fase 3 — postbuild de las 6 apps genera los JSON nuevos
- [ ] Fase 11 — verificacion (curl + ai_audit + re-scan isitagentready)

## Decisiones no-reabribles (del dueno, 2026-06-14)

- **NO se implementa OIDC real.** El portfolio publico no tiene auth para
  agentes; un OIDC provider seria semanas de backend de seguridad critico por
  1 punto, exponiendo el admin privado. Los checks OAuth (oauthDiscovery,
  oauthProtectedResource, authMd) quedan en `fail` POR DISENO correcto. Se
  arreglan a 404 limpio (no HTML basura), no a stub.
- **SI se implementan los 3 discovery legitimos**: describen la API publica de
  lectura del CV (real), no auth. Es el camino de alto ROI.
- **Techo realista: 4/5** (Agent-Integrated). El 5/5 (Agent-Native) requiere
  auth de agentes que este sitio intencionalmente no tiene. El objetivo es
  dejar la categoria `discovery` honesta y limpia, NO forzar el 5/5.

## 1. Contexto / Problema

isitagentready escanea el apex `the-full-stack.com` (4/5, Agent-Integrated). La
unica categoria con fallos es `discovery`:

| check | estado | naturaleza |
|---|---|---|
| `mcpServerCard` | pass | ya servido por el Worker |
| `apiCatalog` | fail | "HTML instead of JSON": el Worker sirve `/api-catalog.json` pero el check pide `/.well-known/api-catalog` SIN `.json` (RFC 9727) -> cae al SPA fallback |
| `a2aAgentCard` | fail | `/.well-known/agent-card.json` no existe -> SPA fallback (HTML) |
| `agentSkills` | fail | `/.well-known/agent-skills/index.json` no existe -> SPA fallback |
| `oauthDiscovery` | fail | OAuth/OIDC metadata; el sitio NO tiene auth de agentes (por diseno) |
| `oauthProtectedResource` | fail | idem |
| `authMd` | fail | `/auth.md` sirve HTML basura (SPA fallback); no hay auth de agentes |
| `webMcp` | fail | WebMCP in-page tools; fuera de scope |

### Hallazgos de exploracion

- El routing de `.well-known/*` lo hace UN Worker monolitico
  `packages/markdown-export/src/lib/build-pages-worker.ts` (Cloudflare Pages
  Advanced Mode, `dist/_worker.js`). Las Pages Functions en `dist/functions/`
  NO corren en prod; el Worker SI.
- El Worker hoy rutea `/.well-known/api-catalog.json` y
  `/.well-known/mcp/server-card.json` desde JSONs inlineados en
  `dist/_worker-data/`. Todo lo no-ruteado cae a `env.ASSETS.fetch` (SPA
  fallback -> el HTML del home). POR ESO los `.well-known` faltantes y los
  OAuth devuelven HTML 200 en vez de JSON o 404.
- Los builders viven en `packages/seo/src/lib/build-*.ts`. Existe
  `buildApiCatalog` (RFC 9727 linkset) y `buildMcpServerCard`. Faltan
  `buildAgentCard` y `buildAgentSkills`.
- El postbuild `apps/<niche>/scripts/postbuild-functions.mjs` genera los JSON
  en `_worker-data/` y bundlea el Worker. Mismo source en los 6 niches.

## 2. Solucion Propuesta

Extender la infraestructura existente, sin tocar Cloudflare config:

1. **packages/seo**: agregar `buildAgentCard` (A2A Agent Card) y
   `buildAgentSkills` (skills discovery index), siguiendo el patron de
   `buildApiCatalog`/`buildMcpServerCard` (funcion pura -> JSON string, con
   tests unit). Reusan los 3 MCP tools de `@portfolio/mcp` (igual que el
   server card) para no duplicar la lista de skills.
2. **build-pages-worker.ts**: agregar rutas al Worker:
   - `GET /.well-known/api-catalog` (SIN `.json`) -> mismo JSON linkset, con
     `content-type: application/linkset+json` (cubre el check RFC 9727).
   - `GET /.well-known/agent-card.json` -> nuevo JSON.
   - `GET /.well-known/agent-skills/index.json` -> nuevo JSON.
   - `GET /.well-known/oauth-authorization-server`,
     `/.well-known/openid-configuration`, `/.well-known/oauth-protected-resource`,
     `/auth.md` -> **404 limpio** (`Response('', {status:404})`), para que dejen
     de servir el HTML del home (honestidad: no hay OAuth).
3. **postbuild-functions.mjs** (los 6 niches): generar `agent-card.json` y
   `agent-skills/index.json` en `_worker-data/` e inlinearlos en el Worker.

### Decisiones clave

- **Decision 1: extender el Worker, NO usar _redirects** — el Worker ya
  intercepta `.well-known/*`; agregar rutas es trivial y consistente. El
  `_redirects` no aplica (el Worker corre antes).
- **Decision 2: 404 para los OAuth, no stub** — honestidad. Un stub OIDC
  mentiria sobre capacidades inexistentes. 404 es la respuesta correcta para
  un recurso que no existe.
- **Decision 3: agent-card y agent-skills reusan los 3 MCP tools** — fuente
  unica de verdad (get_cv_section, list_projects, search_experience), igual
  que el server card. No se inventan skills nuevas.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el apex en prod, When un agente hace `GET /.well-known/api-catalog`
  (sin `.json`) con `Accept: application/linkset+json`, Then responde **200**
  con `content-type: application/linkset+json` y un JSON linkset valido (NO HTML).
- **AC-2**: Given el apex, When `GET /.well-known/agent-card.json`, Then responde
  **200** con `application/json` y un A2A Agent Card valido (name, version,
  capabilities, skills derivadas de los 3 MCP tools).
- **AC-3**: Given el apex, When `GET /.well-known/agent-skills/index.json`, Then
  responde **200** con `application/json` y un index de skills valido.
- **AC-4**: Given el apex, When `GET /.well-known/openid-configuration` (y
  `/oauth-authorization-server`, `/oauth-protected-resource`, `/auth.md`), Then
  responde **404** (NO el HTML del home).
- **AC-5**: Given el re-scan de isitagentready tras el deploy, Then los checks
  `apiCatalog`, `a2aAgentCard`, `agentSkills` pasan a **pass**; los OAuth siguen
  `fail` (esperado, por diseno). El nivel se mantiene >= 4/5.
- **AC-6**: Given los builders nuevos, When se corren los unit tests de
  packages/seo, Then pasan con coverage >= 80% per-file.
- **AC-7**: Given vibe, When se re-corre ai_audit, Then isitagentready >= 3/5
  (objetivo del loop; ya en 4/5).

## 4. Diagrama de Flujo

N/A — no altera flujos de control de la app (solo agrega rutas al Worker).

## 5. Diagrama ER

N/A — sin base de datos ni content collections nuevas.

## 6. Tests Requeridos

### 6.A/6.B. Unit (Vitest, packages/seo)

- `tests/unit/build-agent-card.test.ts` — shape A2A valido, skills = 3 tools,
  trailing newline. [AC-2]
- `tests/unit/build-agent-skills.test.ts` — index valido, 3 skills. [AC-3]
- Coverage >= 80% per-file. [AC-6]

### 6.C. Typecheck

- `pnpm run typecheck` (los builders nuevos tipados, el Worker source valido).

### 6.D. E2E

N/A unit. La verificacion real es curl a prod + re-scan isitagentready (sec 11).

## 7. Archivos Afectados

### Crear
- `packages/seo/src/lib/build-agent-card.ts` — A2A Agent Card builder
  - Verificar: `pnpm --filter @portfolio/seo exec vitest run tests/unit/build-agent-card.test.ts`
- `packages/seo/src/lib/build-agent-skills.ts` — skills index builder
  - Verificar: idem agent-skills
- `packages/seo/tests/unit/build-agent-card.test.ts`
- `packages/seo/tests/unit/build-agent-skills.test.ts`

### Modificar
- `packages/seo/src/index.ts` — exportar los 2 builders nuevos
  - Verificar: `pnpm --filter @portfolio/seo run typecheck`
- `packages/markdown-export/src/lib/build-pages-worker.ts` — rutas nuevas +
  404 OAuth
  - Verificar: build de un niche, curl al dist servido local
- `apps/{generic,hub,fintech,architect,leader,vibe}/scripts/postbuild-functions.mjs`
  — generar los 2 JSON nuevos en `_worker-data/`
  - Verificar: `pnpm --filter @portfolio/<niche> run build` + grep en dist

### Eliminar
- `docs/specs/agent-discovery-wellknown/` — la carpeta del plan (efimera), en
  el ultimo commit.

## 8. Descomposicion para Paralelizacion

N/A — secuencial. Fase 1 (builders) -> Fase 2 (Worker, depende de los builders)
-> Fase 3 (postbuild, depende de ambos). Archivos disjuntos pero con dependencia
de orden; no amerita worktrees.

## 9. Commits

1. `docs(specs): plan de agent discovery .well-known`
2. `feat(seo): builders de A2A agent-card y agent-skills index` — Fase 1 + tests. AC-2,3,6.
3. `feat(markdown-export): rutea .well-known agent discovery + 404 OAuth en el Worker` — Fase 2. AC-1,4.
4. `feat(apps): genera agent-card y agent-skills en el postbuild de los 6 niches` — Fase 3. AC-2,3.
5. `test(specs): verificacion + elimina la carpeta del plan` — sec 11 + `git rm -r`. AC-5,7.

Un PR `feature/agent-discovery-wellknown -> dev`. Promocion `dev -> main` con merge commit.

## 10. Paralelizacion con git worktrees

N/A — cambio secuencial con dependencia de orden entre fases.

## 11. Verificacion E2E iterativa

### Parte A — refactor de tests
Ningun test referencia codigo eliminado. Los builders nuevos tienen sus tests.

### Parte B — bateria local (gate del PR)
```bash
pnpm exec biome check .
pnpm run typecheck
pnpm --filter @portfolio/seo exec vitest run
pnpm run build            # 6 apps
# servir un dist y curl a las rutas nuevas:
#   /.well-known/api-catalog -> 200 linkset+json
#   /.well-known/agent-card.json -> 200 json
#   /.well-known/agent-skills/index.json -> 200 json
#   /.well-known/openid-configuration -> 404
```
Bucle "no parar hasta verde". Solo con todo verde: push + PR + merge a dev.

### Parte C — verificacion de despliegue REAL (post-merge a main)
Tras promover a main + deploy:
1. Mirar el workflow (cada job verde).
2. `curl` a las 4 rutas en prod (3x 200 con el content-type correcto + 1x 404 OAuth).
3. Re-correr `python devtools/run.py ai_audit` y re-scan isitagentready: confirmar
   apiCatalog/a2aAgentCard/agentSkills = pass, OAuth = fail (esperado), nivel >= 4/5,
   vibe >= 3/5 (AC-5, AC-7).
Bucle de correccion identico a Parte B. El plan no se declara listo hasta que las
rutas reales en prod responden correcto.

## 12. Definition of Done

- [ ] AC-1..AC-7 cubiertos.
- [ ] Biome + typecheck + unit (>=80%) + build 6 apps verdes.
- [ ] curl en prod: 3 rutas 200 con content-type correcto, OAuth 404.
- [ ] re-scan isitagentready: discovery sube (3 checks pass), nivel >= 4/5.
- [ ] vibe >= 3/5 confirmado.
- [ ] carpeta del plan eliminada en el ultimo commit.
