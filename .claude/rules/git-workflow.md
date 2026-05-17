---
description: "Workflow de Git: conventional commits, branching strategy, PR process, merge strategy rebase-only, y quality gates obligatorios"
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
- `stage` — release candidate (`*.portfolio.stage.the-full-stack.com`)
- `dev` — desarrollo, rama base para features (`*.portfolio.dev.the-full-stack.com`)

Ramas de trabajo (efimeras, separador `/` obligatorio para VS Code):

- `feature/<nombre>` — nuevas funcionalidades / paginas
- `fix/<nombre>` — correcciones
- `chore/<nombre>` — mantenimiento, deps, configs
- `docs/<nombre>` — solo cambios de documentacion
- `release/<nombre>` — promocion de entorno (ver flujo abajo)

## Flujo de promocion dev -> stage -> main (OBLIGATORIO)

Las ramas de entorno se promueven SIEMPRE en cadena, nunca salteando:

```text
feature/* --PR--> dev --PR--> stage --PR--> main
```

Reglas duras:

- Un PR a `main` SOLO puede tener como head `stage` (o una `release/*`
  rebaseada desde `stage`). NUNCA `dev -> main` directo.
- Un PR a `stage` SOLO puede tener como head `dev` (o una `release/*`).
- Enforced por el workflow `branch-flow-guard.yml` + ruleset de GitHub.

**Por que NUNCA `dev -> main` directo**: si un commit llega a `main` sin
pasar por `stage`, la siguiente promocion `dev -> stage` (merge rebase)
le reescribe el hash. Resultado: el mismo cambio con SHA distinto en
`main` y en `stage` -> el PR `stage -> main` da conflicto fantasma.

### Como promover

1. `dev -> stage`: `gh pr create --base stage --head dev`.
2. `stage -> main`: `gh pr create --base main --head stage`.
3. Si el PR `stage -> main` da conflicto (commits que llegaron a `main`
   sin pasar por `stage`): crear `release/promote-stage-to-main` desde
   `origin/stage`, `git rebase origin/main` (git salta los commits ya
   aplicados por patch-id), abrir el PR desde esa `release/*`.

### Resincronizar tras un hotfix directo a main

Si por emergencia un fix entra directo a `main`, propagarlo el MISMO dia
a `stage` y `dev` para evitar la divergencia: PR `main -> stage` y
`stage -> dev` (o cherry-pick controlado). No dejar ramas divergentes.

## Merge strategy

- **Rebase-only** — no merge commits, no squash. Configurado en GitHub:
  solo `allow_rebase_merge` habilitado.
- Historial lineal entre `dev`, `stage` y `main`
- NUNCA force push en ramas compartidas
- Resolver conflictos con rebase, no merge
- `delete_branch_on_merge` activo: las ramas de trabajo se borran al mergear

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

- Target: `dev` para features/fixes/chores. Promocion a `stage` y `main`
  solo via el flujo en cadena (ver "Flujo de promocion" arriba) — NUNCA
  un PR de feature directo a `stage` o `main`.
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
git checkout main && git pull --rebase
git checkout -b feature/nueva-funcionalidad
# ... desarrollo + tests ...
pnpm exec biome check .             # antes de stage
pnpm exec tsc --noEmit
pnpm exec vitest run
git add -p                          # staging selectivo
git commit -m "feat(scope): subject en espanol"
git push origin feature/nueva-funcionalidad
# crear PR → main (o dev si existe)
```
