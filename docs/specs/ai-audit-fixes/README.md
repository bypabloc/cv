# Spec: fixes del ai_audit (accesibilidad + performance)

> Resolver los hallazgos persistentes del `ai_audit` de prod (2026-06-14):
> contraste de color (accessibility 97 -> 100 en 5 niches) y Speed Index de
> architect (perf 98 -> 99/100). El "vibe 1/5" que motivo el trabajo era un
> falso negativo flaky del scanner externo (ya estable en 4/5). El robots.txt
> 50/100 es un ceiling intencional de Cloudflare Free (se documenta, no se
> toca). Plan Small.

## Cuando leer

| Tema | Archivo | Cuando |
|------|---------|--------|
| Contexto + decision + AC | este README (secciones 1-3) | Antes de implementar |
| Diagnostico del audit | este README (seccion 1) | Para entender que es real vs flaky |
| Commits | este README (seccion 9) | Al ejecutar |
| Verificacion E2E | este README (seccion 11) | Gate de cierre |

## Estado por fase

- [ ] Fase 1 — fix de contraste (token DS)
- [ ] Fase 2 — fix de Speed Index (architect)
- [ ] Fase 3 — documentar ceiling de robots.txt
- [ ] Fase 11 — verificacion E2E (re-audit + build)

## Decisiones no-reabribles

- **vibe 1/5 = flaky**, NO es bug. Verificado en 4 corridas: vibe estable en
  4/5 (botAccessControl 100, identico a los otros 5 niches). NO se "arregla"
  por codigo. El objetivo del loop (vibe >= 3/5) ya se cumple.
- **robots.txt 50/100 = ceiling intencional de Cloudflare Free.** El bloqueo
  "Manage AI bots" que inyecta `Disallow: /` a GPTBot/ClaudeBot NO es
  desactivable por API en plan Free (403 con cualquier token — muro de plan,
  dashboard-only). Decision del dueno (2026-06-14): dejarlo como esta +
  documentar. NO se toca el robots.txt del repo (ya es correcto).
- **Contraste:** se arregla con un cambio de 1 token en el DS
  (`--color-text-muted`: grey-40 -> grey-30), que sube los 5 niches a la vez.
- **Speed Index:** se ataca con `content-visibility: auto` sobre el bloque
  denso de `ArchitectureDiagram`, sin reordenar ni cambiar la UX.

---

## 1. Contexto / Problema

El comando `python devtools/run.py ai_audit` (prod, 6 niches x 3 tools)
arrojo (2026-06-14):

| Target | isitagentready | lighthouse_psi | validators | Avg |
|--------|:---:|:---:|:---:|:---:|
| hub | 4/5 | 100 | 88 | 89 |
| apex / fintech / leader / architect | 4/5 | 99 | 88 | 89 |
| **vibe** | **1/5** (flaky) | 99 | 88 | 69 |

### Hallazgos de exploracion

1. **vibe 1/5 = FLAKY.** Re-scan directo (3x) + via comando oficial (1x):
   vibe da `score=4, botAccessControl=100`, identico a los demas. El 0 puntual
   fue un timeout del scanner externo al fetchear el robots.txt. NO es codigo.
2. **Contraste (accessibility 97 en 5 niches, hub=100).** El token
   `--color-text-muted` = `grey-40` (#7a7a74) en dark mode rinde **3.83:1**
   sobre `--color-surface-2` (chips de SkillsGrid / TimelineItem /
   ProjectBentoCard), bajo el umbral AA 4.5:1. hub no renderiza `CvSections`
   -> no tiene esos chips -> 100. Los 5 niches que renderizan CvSections
   fallan. El fix de 1 token los arregla a todos.
3. **Speed Index architect (perf 98).** architect es el unico niche con
   `ArchitectureDiagram` (un `<pre>` ASCII denso) above-the-fold. 1 punto,
   borderline, pero el dueno pidio intentar optimizar. Fix de menor riesgo:
   `content-visibility: auto` en la seccion (no reordenar).
4. **robots.txt 50/100 (validators).** Cloudflare "Manage AI bots" (Free,
   dashboard-only) prepende `Disallow: /` a GPTBot/ClaudeBot al edge. El
   validator da 50 (neutral, intencional). No es desactivable por API en Free.
   Decision: documentar como ceiling.

---

## 2. Solucion Propuesta

Tres cambios independientes, file-exclusive:

1. **Contraste:** en `packages/ui/src/styles/tokens.css`, cambiar el token
   dark-mode `--color-text-muted` de `var(--color-grey-40)` a
   `var(--color-grey-30)` (#9e9e99, ya en la paleta). Ratios con grey-30:
   surface-2 = 6.14:1, surface = 6.74:1, bg = 7.36:1 — todos pasan AA. Como
   todos los chips que fallan consumen el mismo token, un cambio los arregla
   a todos. Sin tocar componentes (respeta "var(--color-*), nunca hex").
2. **Speed Index:** en `packages/app-shared/src/components/ArchitectureDiagram.astro`,
   agregar `content-visibility: auto` + `contain-intrinsic-size` a la seccion
   `.arch` para que el browser difiera el paint del bloque denso hasta que se
   acerca al viewport. No cambia orden ni contenido.
3. **robots.txt:** documentar en `.claude/rules/ai-audit.md` (junto al ceiling
   de isitagentready) que robots.txt=50 en el validator es el estado esperado
   con Cloudflare Content Signals activo en Free, NO una regresion.

### Decisiones clave

- **Decision 1: grey-30 y no un hex nuevo** — grey-30 ya existe en la paleta;
  evita introducir un `--color-grey-35` o un hex inline. Mantiene la jerarquia
  (sigue subordinado a `--color-text` #f7f7f5).
- **Decision 2: content-visibility en vez de reordenar** — reordenar el
  diagrama abajo del fold tocaria `get-niche-extras.ts` + `CvSections.astro`
  (lib compartida de 5 apps, blast radius alto) y cambiaria la UX intencional.
  `content-visibility: auto` es local a un solo componente, cero blast radius.
- **Decision 3: robots.txt no se toca** — el repo ya es correcto; el bloqueo
  vive en el edge de Cloudflare (Free, sin API). Documentar > intentar un
  fallback que el research confirmo que NO funciona.

---

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el sitio en dark mode, When Lighthouse audita un niche que
  renderiza CvSections (fintech/architect/leader/vibe/generic), Then la
  categoria accessibility da **>= 100** (sin hallazgo de color-contrast).
- **AC-2**: Given el token `--color-text-muted` en dark mode, When se mide su
  contraste sobre `--color-surface-2` (#1f1f1b), Then el ratio es **>= 4.5:1**
  (AA para texto normal).
- **AC-3**: Given el niche architect, When Lighthouse mide Speed Index, Then la
  categoria performance da **>= 99** (sin hallazgo de Speed Index), o se
  documenta que el cambio no movio la metrica (es ruido).
- **AC-4**: Given el cambio de token, When se buildean las 6 apps, Then el
  build pasa y no hay hex inline nuevo (Biome verde).
- **AC-5**: Given `.claude/rules/ai-audit.md`, When se lee la seccion de
  ceiling, Then documenta que robots.txt=50 (validators) es el estado esperado
  con Cloudflare Content Signals en Free, NO una regresion.
- **AC-6**: Given el `ai_audit` re-corrido en prod tras el deploy, When se mira
  vibe, Then isitagentready da **>= 3/5** (objetivo del loop; ya se cumple en
  4/5 de forma estable).

---

## 4. Diagrama de Flujo

N/A — el cambio no altera flujos de control.

## 5. Diagrama ER

N/A — no hay base de datos ni content collections nuevas.

## 6. Tests Requeridos

### 6.B. Unit Tests

No hay logica nueva (cambios de CSS token + content-visibility + docs). Los
unit tests existentes de packages/ui no deben romperse por el cambio de token.
Verificacion: `pnpm --filter @portfolio/ui exec vitest run`.

### 6.C. Typecheck / Conformance

- `pnpm exec biome check .` (cero hex inline nuevo, formato OK)
- `pnpm run typecheck` (sin cambios de tipos, debe seguir verde)

### 6.D. E2E

N/A para unit. La verificacion real es la **re-medicion del ai_audit en prod**
post-deploy (seccion 11 Parte C).

---

## 7. Archivos Afectados

### Modificar

- `packages/ui/src/styles/tokens.css` — `--color-text-muted` dark:
  grey-40 -> grey-30 + actualizar el comentario WCAG
  - Verificar: `pnpm exec biome check packages/ui/src/styles/tokens.css`
  - Verificar: ratio grey-30 sobre surface-2 >= 4.5:1
- `packages/app-shared/src/components/ArchitectureDiagram.astro` — agregar
  `content-visibility: auto` + `contain-intrinsic-size` a `.arch`
  - Verificar: `pnpm --filter @portfolio/architect run build`
- `.claude/rules/ai-audit.md` — documentar el ceiling de robots.txt=50
  - Verificar: lectura — la seccion de ceiling menciona robots.txt + Cloudflare
- `docs/specs/ai-audit-fixes/` — la carpeta del plan (efimera)
  - Verificar: se elimina en el ultimo commit

---

## 8. Descomposicion para Paralelizacion

N/A — 3 cambios atomicos en archivos disjuntos, secuencia trivial. No amerita
worktrees ni fan-out (el guardarrail de concurrencia aplica: esto es trabajo
deterministico, se hace inline).

---

## 9. Commits

1. `docs(specs): plan de fixes del ai_audit (contraste + speed index)` — la
   carpeta del plan.
2. `fix(ui): sube contraste de text-muted a AA en superficies elevadas` —
   tokens.css grey-40 -> grey-30. Cubre AC-1, AC-2, AC-4.
3. `perf(app-shared): difiere paint del diagrama de arquitectura` —
   content-visibility en ArchitectureDiagram. Cubre AC-3.
4. `docs(rules): documenta el ceiling de robots.txt=50 en ai-audit` —
   ai-audit.md. Cubre AC-5.
5. `test(specs): verificacion E2E del ai_audit + elimina la carpeta del plan`
   — re-audit + `git rm -r docs/specs/ai-audit-fixes/`. Cubre AC-6.

Un solo PR `fix/ai-audit-accessibility-perf -> dev`. Promocion `dev -> main`
con merge commit.

---

## 10. Paralelizacion con git worktrees

N/A — cambio secuencial, 3 archivos disjuntos. No hay base concurrente.

---

## 11. Verificacion E2E iterativa

### Parte A — refactor de tests

No hay tests que referencien codigo eliminado (no se elimina codigo). Confirmar
que los unit de packages/ui siguen verdes tras el cambio de token.

### Parte B — bateria de comandos reales (gate del PR)

```bash
pnpm exec biome check .
pnpm run typecheck
pnpm --filter @portfolio/ui exec vitest run
pnpm run build            # las 6 apps
```

Bucle "no parar hasta verde". Solo con todo verde: `git push` + PR + merge a dev.

### Parte C — verificacion de despliegue REAL (post-merge a main)

Tras promover a main y que `deploy-apps.yml` despliegue:

1. Mirar el workflow (cada job verde).
2. `curl` a cada URL canonica de prod (200 + marcador).
3. Re-correr `python devtools/run.py ai_audit` en prod y confirmar:
   - accessibility de los 5 niches CvSections sube a 100 (AC-1).
   - vibe isitagentready >= 3/5 (AC-6 — ya en 4/5).
   - architect performance >= 99 o se documenta que es ruido (AC-3).

Bucle de correccion identico a Parte B. El plan NO se declara listo hasta que
el re-audit de prod confirma las mejoras.

---

## 12. Definition of Done

- [ ] AC-1..AC-6 cubiertos.
- [ ] Biome + typecheck + unit + build de las 6 apps verdes.
- [ ] Re-audit de prod confirma accessibility 100 en los 5 niches CvSections.
- [ ] vibe >= 3/5 confirmado en prod (objetivo del loop).
- [ ] ceiling de robots.txt documentado.
- [ ] carpeta del plan eliminada en el ultimo commit.
