# portfolio

> Monorepo de 6 sitios Astro (pnpm workspaces) para el portfolio multi-niche
> de Pablo Contreras (bypabloc). Output estatico desplegado en Cloudflare Pages.

## Sitios

| App | URL | Posicionamiento |
|-----|-----|-----------------|
| `apps/hub` | `the-full-stack.com` | Landing selector con 5 cards |
| `apps/generic` | `hub.the-full-stack.com` | Full Stack Senior — todas las skills |
| `apps/fintech` | `fintech.the-full-stack.com` | Senior Full Stack Fintech LATAM |
| `apps/architect` | `architect.the-full-stack.com` | Frontend Architect + Microservicios |
| `apps/leader` | `leader.the-full-stack.com` | Tech Lead / Engineering Manager |
| `apps/vibe` | `vibe.the-full-stack.com` | Vibe Coding / Claude Code / Dev tools |

## Packages

| Package | Responsabilidad |
|---------|-----------------|
| `packages/content` | Zod schemas + datos del CV (singleton). Filters + sort por nicho |
| `packages/ui` | Design system, componentes Astro, theme toggle, animaciones |
| `packages/seo` | JSON-LD Person, llms.txt, sitemap, robots.txt builders |
| `packages/cv-pdf` | Render CV a HTML (ATS-friendly) + PDF opcional (Puppeteer) |
| `packages/app-shared` | SitePageLayout + CvSections + AboutSection compartidos |

## Comandos

Root scripts (operan sobre todo el monorepo):

- `pnpm install` — instalar deps
- `pnpm run dev` — dev server en paralelo
- `pnpm run build` — build de todas las apps
- `pnpm run lint` / `lint:fix` — Biome
- `pnpm run typecheck` — tsc + astro check
- `pnpm run test` / `test:coverage` — Vitest en packages
- `pnpm run clean` — limpia dist, .astro, coverage

Filtrar por workspace: `pnpm --filter @portfolio/<app> run <script>`.

Stack: Astro 5+ + TypeScript strict + Biome v2 + Vitest + Tailwind v4 + pnpm 10.
E2E opt-in: Playwright (no configurado en v1).

NUNCA mezclar `npm` o `yarn` — solo `pnpm`.

## Reglas criticas (siempre activas)

- SIEMPRE archivos temporales en `./tmp/` del proyecto, NUNCA `/tmp/` del sistema
- SIEMPRE `rm -f` para eliminar (evita prompts interactivos)
- SIEMPRE tokens del Design System via `var(--color-*)`, NUNCA hex inline
- SIEMPRE fonts self-hosted via `@fontsource/*`, NUNCA Google Fonts CDN
- SIEMPRE TypeScript strict, NUNCA `any` (usar `unknown` con narrow)
- SIEMPRE Conventional Commits en espanol (subject + body)
- NUNCA atribucion de IA en commits, PRs, issues, ni comentarios
- NUNCA `find`, `grep -E/-r/-rn` en Bash (aliases rotos en WSL2): usar
  Glob / Grep / Read / Edit tools
- NUNCA declarar trabajo "listo" sin ejecutar las verificaciones de
  [verify-before-done](.claude/rules/verify-before-done.md)

## Arbol de conocimiento

Antes de trabajar, identifica que contexto necesitas:

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Reglas generales | [.claude/rules/general.md](.claude/rules/general.md) | Indice de reglas + estructura del repo |
| Astro + Biome + TS | [.claude/rules/astro-landing.md](.claude/rules/astro-landing.md) | Antes de crear componente / pagina / utility |
| Design System | [.claude/rules/design-system.md](.claude/rules/design-system.md) | Tokens CSS, dark/light, tipografia, fonts |
| Docstrings | [.claude/rules/docstring-standard.md](.claude/rules/docstring-standard.md) | Antes de documentar cualquier unidad de codigo |
| Verify-before-done | [.claude/rules/verify-before-done.md](.claude/rules/verify-before-done.md) | Antes de reportar trabajo completado |
| Git workflow | [.claude/rules/git-workflow.md](.claude/rules/git-workflow.md) | Antes de commit / push / PR |
| Git hooks | [.claude/rules/git-hooks.md](.claude/rules/git-hooks.md) | Quality gates pre-commit / pre-push |
| Security | [.claude/rules/security.md](.claude/rules/security.md) | Secrets, CSP, headers, supply chain |
| Plan format | [.claude/rules/plan-format.md](.claude/rules/plan-format.md) | En plan mode o al planificar features |
| Harness protocol | [.claude/rules/harness-protocol.md](.claude/rules/harness-protocol.md) | Subagentes, feature_list, current/history |
| Markdown docs | [.claude/rules/markdown-docs.md](.claude/rules/markdown-docs.md) | Editar archivos de `docs/` |
| Skills (frontmatter) | [.claude/rules/skills.md](.claude/rules/skills.md) | Crear / modificar skills |
| Testing config Claude | [.claude/rules/claude-config-testing.md](.claude/rules/claude-config-testing.md) | Antes de commitear cambios en `.claude/*` |
| CV (contenido) | [.claude/docs/cv/README.md](.claude/docs/cv/README.md) | Datos del CV (perfil, experiencia, proyectos) |
| Estrategia portfolio 2026 | invocar skill `astro-portfolio` | Decisiones de SEO/GEO/ATS/AI literacy/diseno |

## Skills disponibles

Invocables manualmente con `/<nombre>` o automaticamente segun keywords del
prompt. Detalles del frontmatter: [.claude/rules/skills.md](.claude/rules/skills.md).

| Skill | Uso |
|-------|-----|
| `astro-portfolio` | Referencia obligatoria para cualquier decision de estructura, SEO, GEO, ATS, diseno o stack del portfolio |
| `animations-css` | Animaciones CSS (scroll-driven, view transitions, micro-interactions) — NO usar libs como motion / gsap / aos |
| `codebase-audit` | Auditoria de calidad: dead code, complexity, duplication, tech debt |
| `dependency-upgrade` | Workflows de upgrade con pnpm (audit, outdated, CVE, majors) |
| `fix-hooks` | Reparar errores de pre-commit / pre-push iterativamente |
| `github-actions` | Workflows CI + testing local con `act` (nektos/act) |
| `mermaid` | Crear / modificar diagramas `.mmd` en `docs/diagrams/` |
| `research` | Deep research de tecnologias y librerias (skill con web habilitada) |
| `spec-workflow` | Descomponer features en specs + tareas atomicas |
| `tdd-workflow` | TDD obligatorio (Red-Green-Refactor) antes de implementar |

## Convenciones (resumen)

- Componentes Astro: `PascalCase.astro` (ej. `ExperienceCard.astro`)
- Paginas: kebab-case (`user-profile.astro`)
- Utilities: kebab-case (`format-date.ts`)
- Branches: `feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/` con `/` obligatorio
- Tests: mirror de `src/` en `tests/unit/`, BDD-style en `it()` (`Given/When/Then`), asserts EXACTOS
- Coverage minimo: 80% per-file en archivos modificados
- Comunicacion: respuestas tecnicas directas, sin validacion emocional ni preambulos

## Documentacion (zonas)

`docs/` tiene dos zonas separadas — NO mezclar:

- **Producto** (Knowledge Tree navegable): `cv/`, `guide/`, `design-system/`,
  `diagrams/`, `specs/`, `claude/` — cambia raramente, audiencia: reviewers
- **Harness interno**: `progress/`, `<area>/feature_list.json`,
  `CHECKPOINTS.md` — cambia constantemente, audiencia: el orquestador

Reglas: [.claude/rules/markdown-docs.md](.claude/rules/markdown-docs.md)
y [.claude/rules/harness-protocol.md](.claude/rules/harness-protocol.md).

## Gotchas

- WSL2: `find` esta aliasado a `fd`, `grep -E/-r/-rn` a `rg`. Cada uso
  rompe la ejecucion — usar Glob / Grep / Read / Edit tools.
- Hooks en `.claude/hooks/` + `.git-hooks/` son enforcement real; CLAUDE.md
  no enforza por si solo. Ver [.claude/hooks/README.md](.claude/hooks/README.md).
- `attribution.commit` y `attribution.pr` estan vacios en
  [.claude/settings.json](.claude/settings.json) — defensa en profundidad
  contra atribucion de IA.
- Branches `main`, `master`, `dev`, `release` estan protegidas: el hook
  `protect-branch.sh` bloquea `git push` directo.
