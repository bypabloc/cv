---
name: github-actions
description: >
  GitHub Actions CI workflow reference + local testing with act (nektos/act)
  for this Astro 6 portfolio. ALWAYS invoke for any CI/GitHub Actions request.
  Triggers: "CI", "CI/CD", "github actions", "workflow", "pipeline", "act",
  "ci.yml", "validar workflow", "correr CI localmente", "CI falla", "fix CI",
  "modificar CI", "agregar step CI".
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git:*), Bash(act:*), Bash(pnpm:*)
argument-hint: "accion: test | validate | modify | reference | act-setup | all"
metadata:
  version: "2.0"
---

# GitHub Actions + act - CI Local Testing

Referencia para el CI de GitHub Actions y testing local con act.

## Pre-requisitos OBLIGATORIOS

Antes de responder, lee la documentacion relevante:

| Argumento / Tema | Archivo a leer |
|-----------------|----------------|
| `act-setup`, `act`, `instalar act`, `configurar act` | `.claude/docs/github-actions-act/01-act-reference.md` |
| `test`, `probar`, `validate`, `validar`, `ejecutar` | `.claude/docs/github-actions-act/02-ci-workflow.md` |
| `modify`, `modificar`, `agregar`, `add`, `cambiar` | `.claude/docs/github-actions-act/02-ci-workflow.md` + `.github/workflows/ci.yml` |
| `reference`, `referencia`, `all`, `todo` | Todos los archivos en `.claude/docs/github-actions-act/` |
| Sin argumento | `.claude/docs/github-actions-act/README.md` |

## Workflow

### 1. Identificar la necesidad del usuario

- **Probar/validar CI**: Sugerir comandos `act` apropiados
- **Modificar workflow**: Leer ci.yml actual, proponer cambios
- **Debugging CI**: Analizar errores, sugerir flags de debug
- **Setup act**: Guiar instalacion y configuracion

### 2. Leer documentacion relevante

Usar Read tool para cargar los docs correspondientes segun el tema.

### 3. Leer estado actual del CI

Si el usuario quiere modificar o debuggear, leer:

- `.github/workflows/ci.yml` — Workflow actual (si existe)
- `.actrc` — Configuracion de act (si existe)
- `.git-hooks/pre-push` — Hook que ejecuta el CI (si existe)

Si el proyecto todavia no tiene `.github/workflows/ci.yml`, sugerir crearlo
con los pasos minimos del stack:

```yaml
# .github/workflows/ci.yml (template Astro 6 + pnpm)
name: ci
on:
  pull_request:
    branches: [main, master, dev]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec biome check .
      - run: pnpm exec tsc --noEmit
      - run: pnpm exec astro check
      - run: pnpm exec vitest run --coverage
      - run: pnpm run build
```

### 4. Responder con comandos act

SIEMPRE incluir al final de la respuesta una seccion con los comandos `act` para que el usuario pueda probar los cambios localmente.

## Comandos act para probar CI

### Validacion rapida (SIEMPRE sugerir primero)

```bash
# Validar sintaxis YAML
act --validate

# Dry run (sin ejecutar contenedores)
act -n

# Listar jobs
act -l
```

### Ejecucion completa

```bash
# Simular PR
act pull_request

# Job especifico
act -j quality

# Con verbose para debug
act pull_request --verbose

# Reusar contenedores (iteraciones rapidas)
act pull_request --reuse
```

### Debug

```bash
# Logs detallados de Docker
act pull_request --verbose

# No enmascarar secretos (para debug)
act pull_request --insecure-secrets

# Grafo de dependencias
act -g
```

## Estructura del CI del proyecto

```text
.github/workflows/ci.yml          # Workflow principal (si existe)
.actrc                             # Config act (si existe)
.secrets                           # Secretos para act (NO committear, agregar a .gitignore)
.git-hooks/pre-commit              # Hook local (si existe)
.git-hooks/pre-push                # Hook local (si existe)
```

## Reglas

- SIEMPRE leer `.github/workflows/ci.yml` antes de sugerir modificaciones (si existe)
- SIEMPRE sugerir `act --validate` y `act -n` antes de `act pull_request`
- SIEMPRE incluir seccion "Probar con act" al final de cualquier respuesta sobre CI
- NO modificar el workflow sin leer el estado actual
- Si se modifica el workflow, sugerir el flujo completo: validate -> dry run -> run -> push
- Pasos minimos esperados en CI para este proyecto: install, biome check, tsc/astro check, vitest, build
