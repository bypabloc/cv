---
description: "Workflow de Git: conventional commits, branching strategy, PR process, merge strategy merge-commit-only, y quality gates obligatorios"
---

# Git Workflow Standards - Portfolio

> Reglas de Git para todo el proyecto.

## Conventional Commits (obligatorio)

Idioma: **espanol** para subject y body. Terminos tecnicos en ingles cuando sea mas claro (`refactor`, `linter`, `coverage`, `typecheck`, nombres de archivos, comandos, identificadores de codigo).

### Formato

```
<type>(<scope>): <subject en imperativo, minusculas, sin punto final>
<linea en blanco>
- <bullet 1: que cambio, en imperativo>
- <bullet 2: ...>
- <bullet N: ...>
```

### Reglas

- **Subject**: maximo 70 caracteres, en imperativo (`agrega`, `corrige`, `actualiza`), sin punto final, todo en minusculas excepto identificadores de codigo o nombres propios.
- **Body**: lista de bullets con `-`. Cada bullet describe un cambio concreto en imperativo. Sin parrafos largos.
- **Sin atribucion de IA**: NUNCA `Co-Authored-By: Claude`, `Generated with Claude Code`, emoji robot, ni URLs `claude.ai/code/session`. Politica de empresa.
- **Sin emojis** en el mensaje (excepto si el codigo realmente los usa, ej. tabla de roles).
- **Subject sin scope** valido solo para cambios que tocan multiples areas no relacionadas (raro). Preferir scope.

### Ejemplo completo

```
docs(rules): alinea plan-format con best practices 2026

- Agrega nota del workflow Explore-Plan-Implement-Commit y fase opcional de Interview
- Agrega tabla de scope-based ceremony (Micro/Small/Medium/Large) para que hotfixes salten el template
- Nueva seccion 3: criterios de aceptacion numerados en notacion BDD/EARS como fuente de verdad
- Cambia el formato de TDD flows a WHEN/THEN y exige referencia a AC en cada test
- Agrega comandos de verificacion por archivo en la seccion de Archivos Afectados
- Nueva seccion 8 (condicional): descomposicion para paralelizacion con reglas de file-exclusivity para git worktrees
- Expande la seccion 9 con Definition of Done ademas del checklist pre-implementacion
- Vuelve condicionales los diagramas de flujo y documenta anti-patrones
```

### Tipos validos

| Tipo | Cuando usarlo |
|------|---------------|
| `feat` | Nueva funcionalidad para el usuario |
| `fix` | Correccion de bug |
| `docs` | Solo cambios en documentacion (`.md`, comentarios, READMEs) |
| `style` | Formato, espacios, tabs, comas — sin cambio de logica |
| `refactor` | Cambio de codigo que no agrega features ni corrige bugs |
| `test` | Agregar o corregir tests sin tocar codigo de produccion |
| `chore` | Tareas de mantenimiento: deps, build, configs, hooks |
| `perf` | Mejora de rendimiento |
| `ci` | Cambios en pipelines de CI/CD |
| `security` | Parches de seguridad o hardening |

### Scopes comunes

Scopes comunes en este portfolio: `pages`, `components`, `layouts`, `content`, `lib`, `styles`, `config`, `ci`, `rules`, `skills`, `hooks`, `tests`, `deps`, `docs`.

### Mas ejemplos cortos

```text
feat(pages): agrega pagina /projects con grid de proyectos destacados
fix(components): corrige overflow del Hero en viewport <380px
refactor(lib): extrae format-date a su propio modulo
test(lib): agrega unit tests para format-date con locale es/en
chore(deps): actualiza astro a 6.2.0
ci(github): agrega step de lighthouse-ci en build
security(config): agrega CSP estricta en vercel.json
docs(cv): actualiza experiencia 2024-2026
style(components): unifica spacing del Footer con tokens del DS
```

## Branching strategy

Ramas de entorno (protegidas, deploy automatico a Cloudflare Pages):

- `main` — produccion / live site desplegado (`the-full-stack.com`)
- `dev` — desarrollo, rama base para features (`*.portfolio.dev.the-full-stack.com`)

Ramas de trabajo (efimeras, separador `/` obligatorio para VS Code):

- `feature/<nombre>` — nuevas funcionalidades / paginas
- `fix/<nombre>` — correcciones
- `chore/<nombre>` — mantenimiento, deps, configs
- `docs/<nombre>` — solo cambios de documentacion

> La promocion de entorno se hace con un PR directo `dev -> main`
> (merge commit). NO se usan ramas `release/*`: con merge commit las ramas
> no divergen, asi que no hace falta una rama puente rebaseada (ver
> "Flujo de promocion" abajo).

## Flujo de promocion dev -> main (OBLIGATORIO)

Las features pasan por `dev` antes de llegar a produccion, nunca directo:

```text
feature/* --PR--> dev --PR--> main
```

TODOS los PRs se mergean con **merge commit** (una sola estrategia, ver
"Merge strategy" abajo).

Reglas duras:

- Un PR a `main` SOLO puede tener como head `dev`. NUNCA una feature branch
  directo a `main`.
- Enforced por el workflow `branch-flow-guard.yml` + ruleset de GitHub.

### Como promover

1. `dev -> main`: `gh pr create --base main --head dev`, mergear con
   `gh pr merge --merge` (NUNCA `--delete-branch`: `dev` es permanente).

El PR de promocion es directo `dev -> main`: sin conflictos, sin
`release/*` branches, sin rebase manual. El merge commit preserva los
SHAs de los commits promovidos, asi que las dos ramas comparten
exactamente los mismos commits (mas un merge commit por promocion). No
hay divergencia.

### Resincronizar tras un hotfix directo a main

Si por emergencia un fix entra directo a `main`, propagarlo el MISMO dia
a `dev` con merge commit (PR `main -> dev`). No dejar ramas divergentes.

## Merge strategy

**Merge commit para TODOS los PRs** — una sola estrategia, sin excepciones:

- Feature -> `dev`: `gh pr merge --merge --delete-branch` (la feature
  branch es efimera, se borra al mergear).
- Promocion `dev -> main`: `gh pr merge --merge` (SIN `--delete-branch` —
  las ramas de entorno son permanentes).

En GitHub solo esta habilitado `allow_merge_commit`; `allow_rebase_merge`
y `allow_squash_merge` estan deshabilitados.

### Por que merge commit y NO rebase

El rebase RE-APLICA cada commit con un SHA nuevo. Si se rebasea al
promover `dev -> main`, el commit `feat: X` que estaba en `dev` como
`abc123` aparece en `main` como `def456`: mismo contenido, hash distinto.
git identifica commits por SHA, no por contenido — entonces el siguiente
PR `dev -> main` ve `abc123` y `def456` como commits diferentes que
tocan las mismas lineas y da **conflicto fantasma**.

El merge commit PRESERVA los SHAs: el commit `abc123` de `dev` se mergea
a `main` siendo `abc123`. `main` y `dev` comparten el SHA -> cero
divergencia, cero conflicto. Por eso TODO se mergea con merge commit.

Trade-off aceptado: la historia tiene un merge commit por cada PR (no es
100% lineal), a cambio de cero divergencia entre `dev`/`main` y un unico
metodo de merge para todos los PRs.

- NUNCA force push en ramas compartidas (`dev`, `main`)
- Conflictos en una feature branch se resuelven con `git merge origin/dev`
  (o `git rebase origin/dev` dentro de la propia feature branch antes de
  abrir el PR — el rebase local de una feature no afecta la divergencia)

## Antes de cada commit

1. `git status && git diff` — revisar cambios
2. Quality gates (manual o via `.git-hooks/pre-commit` si existe):
   - `pnpm exec biome check .` (lint + format)
   - `pnpm exec tsc --noEmit` (typecheck TS)
   - `pnpm exec astro check` (typecheck Astro)
   - `pnpm exec vitest run --changed` (tests relacionados)
3. Todos los tests deben pasar

## Antes de cada push

1. Quality gates via `.git-hooks/pre-push` (si existe), o manualmente:
   - Todo lo de pre-commit
   - `pnpm exec vitest run --coverage` (coverage >= 80% per-file)
   - `pnpm run build` (build estatico exitoso)
2. NUNCA `git push --no-verify` en ramas compartidas

## Pull Requests

- Target: `dev` para features/fixes/chores. Promocion a `main` solo via el
  flujo en cadena (ver "Flujo de promocion" arriba) — NUNCA un PR de feature
  directo a `main`.
- CI ejecuta mismos quality gates que pre-push
- Trigger: PRs a `main`/`master`/`dev`
- Template automatico: `.github/pull_request_template.md` (si existe)

### Principios de PRs

- **Pequenos y atomicos**: subdividir tareas grandes en multiples PRs. Un PR con cientos de lineas se aprueba lento y captura menos bugs en review.
- **Un proposito por PR**: si el subject empieza con "X y Y", probablemente son dos PRs.
- **Tests incluidos**: si el proyecto tiene tests del modulo afectado, este PR debe agregar/modificar los que correspondan (TDD obligatorio en `tdd-workflow` skill).

### Estructura del body de un PR (obligatoria)

El template tiene cuatro secciones, todas requeridas:

1. **Problema** — que problema resuelve, conciso. Si son varios, enumerar `1.`, `2.`, `3.` (con tarea de tracker al lado si aplica).
2. **Solucion** — que se hizo. Si arriba se enumeraron problemas, mantener la **misma numeracion paralela** (Problema 1 -> Solucion 1) para que el reviewer pueda saltar puntualmente.
3. **Como probar** — pasos reproducibles que cualquier reviewer pueda seguir. NO "lo probe local". Incluir URLs del preview deploy, comandos para correr local (`pnpm run dev`), capturas si hay cambios visuales.
4. **TODO** — tareas pendientes que escapan del scope pero no afectan la solucion (refactors, optimizaciones). Vacio si no aplica. Esto distingue scope actual de deuda explicita y evita TODOs escondidos en codigo.

Si por urgencia se mergea con comentarios pendientes, registrar issue separado y referenciar su ID tanto en el PR como en los comentarios sin resolver.

## Workflow diario

```bash
git checkout dev && git pull         # dev es la rama base de features
git checkout -b feature/nueva-funcionalidad
# ... desarrollo + tests ...
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec vitest run
git add -p                           # staging selectivo
git commit -m "feat(scope): subject en espanol"
git push origin feature/nueva-funcionalidad
# crear PR -> dev, mergear con merge commit (gh pr merge --merge --delete-branch)
```
