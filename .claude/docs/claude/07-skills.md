# 7. Skills 2.0 (Referencia Rapida)

[Volver al indice](README.md) | [Anterior: Rules](06-rules.md) | [Siguiente: Documentacion (CLAUDE.md)](08-docs.md)

> Referencia practica consolidada de Skills 2.0 para Claude Code. Incluye el Agent Skills Open Standard (agentskills.io), subagentes, hooks, dynamic context injection, y evals. Para deep dives teoricos, ver los capitulos [01](01-introduccion.md), [02](02-contexto-y-personalizacion.md), [03](03-automatizacion-y-extensibilidad.md), y [04](04-optimizacion-y-configuracion.md).

## Que son Skills 2.0

Skills son la evolucion del sistema `.claude/commands/` hacia una plataforma de agentes programables. Un skill es un directorio con un `SKILL.md` (requerido) mas archivos opcionales (scripts, references, assets). No ejecutan codigo directamente — **preparan a Claude** con contexto especializado y permisos para resolver problemas.

Skills siguen el **Agent Skills Open Standard** ([agentskills.io](https://agentskills.io/specification)), lanzado por Anthropic en diciembre 2025. Adoptado por 26+ plataformas: OpenAI (Codex CLI, ChatGPT), VS Code Copilot, Gemini CLI.

### Que cambio respecto a Commands

Commands y skills estan unificados. `.claude/commands/deploy.md` y `.claude/skills/deploy/SKILL.md` ambos crean `/deploy`. Commands existentes siguen funcionando sin migracion.

| Feature | Commands (legacy) | Skills 2.0 |
|---------|-------------------|------------|
| Ubicacion | `.claude/commands/*.md` | `.claude/skills/<name>/SKILL.md` |
| Archivos auxiliares | No soportados | Directorio completo (scripts/, references/, assets/) |
| Auto-invocacion | No soportada | Claude auto-carga segun `description` |
| Frontmatter | Limitado | YAML completo (model, context, hooks, allowed-tools) |
| Subagentes | No soportados | `context: fork` ejecuta en contexto aislado |
| Context dinamico | No soportado | `` !`command` `` inyecta output de shell |
| Hooks | No soportados | Hooks de ciclo de vida scoped al skill |
| Restriccion de tools | No soportada | Campo `allowed-tools` |
| Override de modelo | No soportado | Campo `model` |

Si un skill y un command comparten nombre, el skill tiene precedencia. Se recomienda skills para trabajo nuevo.

## Quick Start: Crear un Skill en 5 Minutos

### 1. Crear estructura

```bash
mkdir -p .claude/skills/mi-skill
```

### 2. Escribir SKILL.md

```yaml
---
name: mi-skill
description: >
  Hace X para Y. ALWAYS invoke when the user mentions Z, needs to do A,
  or says "do B". Do not attempt Z without this skill.
allowed-tools: Read, Grep, Glob
---

# Mi Skill

## Workflow
1. Paso 1
2. Paso 2
3. Paso 3

## Reglas
- SIEMPRE hacer X antes de Y
- NUNCA asumir Z sin verificar
```

### 3. Probar

```text
# Invocacion directa
/mi-skill argumento

# Auto-activacion (escribir algo que matchee la description)
> Necesito hacer Z para este archivo
```

### 4. Verificar carga

```text
/context    # Ver skills activos, budget, warnings
```

## Frontmatter Reference

### Agent Skills Open Standard (agentskills.io)

Campos del estandar abierto, compatibles con 26+ plataformas:

```yaml
---
name: skill-name          # Requerido. 1-64 chars, lowercase+guiones, debe matchear directorio
description: What it does  # Requerido. 1-1024 chars
license: Apache-2.0       # Opcional
compatibility: Requires git, docker  # Opcional, max 500 chars
metadata:                  # Opcional, key-value arbitrario
  author: example-org
  version: "1.0"
allowed-tools: Read Grep Glob  # Opcional, espacio-delimitado
---
```

### Extensiones Claude Code (sobre el estandar)

| Campo | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `name` | string | Nombre del directorio | Display name y slash command. Solo minusculas, numeros, guiones. Max 64 chars |
| `description` | string | Primer parrafo del markdown | Que hace y cuando usarlo. Max 1024 chars. **Clave para auto-activacion** |
| `argument-hint` | string | - | Hint en autocompletado. Ej: `[issue-number]`, `[file] [format]` |
| `disable-model-invocation` | boolean | `false` | `true` impide auto-activacion por Claude |
| `user-invocable` | boolean | `true` | `false` oculta del menu `/` |
| `allowed-tools` | string/list | - | Tools pre-aprobados durante ejecucion |
| `model` | string | - | Override de modelo (ej: `claude-haiku-4-5-20251001`) |
| `context` | string | - | `fork` para ejecutar en subagente aislado |
| `agent` | string | - | Tipo de subagente: `Explore`, `Plan`, `general-purpose`, custom |
| `hooks` | object | - | Hooks de ciclo de vida scoped al skill |
| `license` | string | - | Licencia (estandar abierto) |
| `compatibility` | string | - | Requisitos de entorno (estandar abierto) |
| `metadata` | object | - | Key-value arbitrario (estandar abierto) |

## Features Nuevas en Skills 2.0

### Subagentes (`context: fork`)

Skills pueden ejecutarse en subagentes aislados con su propio context window. El contenido del SKILL.md se convierte en el prompt del subagente. No tiene acceso al historial de la conversacion.

```yaml
---
name: deep-research
description: >
  Deep research into a topic. ALWAYS invoke for research tasks.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# Deep Research

Investiga exhaustivamente el tema: $ARGUMENTS

## Proceso
1. Buscar en codebase local
2. Buscar en web
3. Sintetizar hallazgos
4. Retornar reporte estructurado
```

El campo `agent` especifica que subagente usar:
- **Built-in**: `Explore`, `Plan`, `general-purpose`
- **Custom**: agentes definidos en `.claude/agents/`

### Dynamic Context Injection (`` !`command` ``)

Ejecuta comandos de shell antes de enviar el contenido del skill a Claude. El output reemplaza el placeholder:

```yaml
---
name: pr-summary
context: fork
---

# PR Summary

## Estado actual
- Branch: !`git branch --show-current`
- Ultimo commit: !`git log --oneline -1`
- Archivos sin commit: !`git status --short`

## Diff
!`gh pr diff`

## Changed files
!`gh pr diff --name-only`
```

### Hooks en Skills (ciclo de vida)

Skills pueden definir hooks `PreToolUse`, `PostToolUse` y `Stop` scoped a la duracion del skill:

```yaml
---
name: secure-operations
description: >
  Secure operations with pre-execution validation.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "./scripts/lint-check.sh"
---

# Secure Operations

Todas las operaciones Bash son validadas antes de ejecutarse.
Todos los archivos escritos son validados con lint despues.
```

### Skills Bundled (incluidos en Claude Code)

| Skill | Proposito |
|-------|-----------|
| `/simplify` | Spawns 3 agentes paralelos: code reuse, quality, efficiency |
| `/batch <instruction>` | Descompone trabajo en 5-30 unidades, 1 agente por unidad en worktrees aislados |
| `/debug` | Lee session debug log |
| `/loop [interval] <prompt>` | Ejecucion recurrente en intervalo |
| `/claude-api` | Carga referencia de Claude API para tu lenguaje |

### Evals y Benchmarks (Skills 2.0 Eval System)

4 modos operacionales para testing de skills:

| Modo | Proposito | Metodo |
|------|-----------|--------|
| **Create** | Construir skills desde lenguaje natural | Generacion asistida |
| **Eval** | Testear con prompts reales | 4 sub-agentes: Executor, Grader, Comparator, Analyzer |
| **Improve** | Optimizar descriptions y triggers | Iteracion automatica |
| **Benchmark** | Comparar metricas de rendimiento | Pass rate, tiempo, consumo de tokens |

A/B testing usa analisis comparativo ciego. Trigger tuning usa split 60/40 train/test con hasta 5 ciclos iterativos.

## Estructura de Directorio

```text
mi-skill/
├── SKILL.md              # Instrucciones principales (REQUERIDO)
├── scripts/              # Codigo ejecutable (se EJECUTA via Bash)
│   └── validate.sh       # Solo el output entra al contexto
├── references/           # Documentacion (se LEE via Read tool)
│   └── api-docs.md       # Contenido completo entra al contexto
├── examples/             # Outputs de ejemplo
│   └── sample.md         # Muestra formato esperado
└── assets/               # Archivos referenciados por path
    └── template.html     # NO se cargan en contexto
```

## Ubicaciones y Prioridad

| Ubicacion | Ruta | Aplica a |
|-----------|------|----------|
| Enterprise | Via managed settings | Todos los usuarios de la org |
| Personal | `~/.claude/skills/<nombre>/SKILL.md` | Todos tus proyectos |
| Proyecto | `.claude/skills/<nombre>/SKILL.md` | Solo este proyecto |
| Plugin | `<plugin>/skills/<nombre>/SKILL.md` | Donde el plugin este habilitado |

**Prioridad** (mayor a menor): Enterprise > Personal > Proyecto.

Soporte monorepo: descubrimiento automatico desde `.claude/skills/` anidados en subdirectorios.

## Variables de Sustitucion

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `$ARGUMENTS` | Todos los argumentos | `/skill arg1 arg2` -> `arg1 arg2` |
| `$ARGUMENTS[N]` | Argumento por indice (0-based) | `$ARGUMENTS[0]` -> `arg1` |
| `$N` | Shorthand para `$ARGUMENTS[N]` | `$0` -> `arg1` |
| `{baseDir}` | Path al directorio del skill | Para referenciar scripts/ |
| `` !`command` `` | Dynamic context injection | Output reemplaza el placeholder |
| `${CLAUDE_SESSION_ID}` | ID de sesion actual | Para logging y tracking |
| `${CLAUDE_SKILL_DIR}` | Directorio del skill | Alternativa a `{baseDir}` |

## Modos de Invocacion

| Modo | Frontmatter | Quien invoca | Caso de uso |
|------|-------------|-------------|-------------|
| **Bidireccional** | (default) | Usuario + Claude | Skills de uso general |
| **Solo usuario** | `disable-model-invocation: true` | Solo `/nombre` | Deploy, commit, operaciones peligrosas |
| **Solo Claude** | `user-invocable: false` | Solo auto-deteccion | Conocimiento de fondo contextual |

## Mejorar Tasa de Activacion

Tasa base de auto-activacion: **~20-50%**. Estrategias para mejorarla:

| Estrategia | Tasa | Como |
|------------|------|------|
| Sin optimizacion | ~20% | - |
| Description optimizada | 50% | Tercera persona + "Use when..." |
| Ejemplos en body | 72-90% | Agregar seccion de ejemplos de uso |
| Hook forced eval | 84% | Hook UserPromptSubmit que fuerza evaluacion |
| **Descriptions directivas** | **100%** | Lenguaje imperativo: "ALWAYS invoke when..." |

### Ejemplo de description directiva (100% activacion)

```yaml
description: >
  ALWAYS invoke this skill when the user mentions PDFs, documents,
  forms, or text extraction. Do not attempt PDF operations without
  this skill. This skill MUST be activated for any PDF-related request.
```

### Hook de evaluacion forzada (84% activacion)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "prompt",
        "prompt": "MANDATORY: Before responding, evaluate ALL available skills against this request. For each: reason YES/NO. If any matches, invoke it FIRST."
      }
    ]
  }
}
```

## Patrones de allowed-tools

```yaml
# Solo lectura (seguro)
allowed-tools: Read, Grep, Glob

# Comandos Bash con wildcards
allowed-tools: Bash(git:*), Bash(npm:*), Read, Write

# Escritura controlada
allowed-tools: Read, Write, Edit, Bash(prettier:*), Bash(eslint:*)

# Full access (usar con cuidado)
allowed-tools: Read, Write, Edit, Bash(*), Grep, Glob
```

## Ejemplos Completos por Caso de Uso

### Skill de referencia: Convenciones de API

```yaml
---
name: api-conventions
description: >
  API design conventions for the payment service. Use when creating
  new endpoints, modifying API responses, or reviewing API code.
user-invocable: false
allowed-tools: Read, Grep
---

# API Conventions

## Endpoints
- RESTful naming: `/api/v1/payments/{id}`
- Plural nouns for collections: `/api/v1/users`
- Verbs only for actions: `/api/v1/payments/{id}/refund`

## Response Format
All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

## Error Format

```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_DECLINED",
    "message": "Card was declined by the issuer",
    "details": []
  }
}
```
```

### Skill con subagente: Deploy check (forked)

```yaml
---
name: deploy-check
description: >
  Pre-deployment verification. Use before deploying to production.
disable-model-invocation: true
context: fork
agent: general-purpose
allowed-tools: Bash(npm:*), Bash(python:*), Bash(git:*), Read, Grep
---

# Pre-Deploy Verification

## Estado actual
- Branch: !`git branch --show-current`
- Ultimo commit: !`git log --oneline -1`
- Archivos sin commit: !`git status --short`

## Checklist

1. **Tests**: Ejecutar suite completa
2. **Linting**: Zero errores
3. **Type check**: Zero errores
4. **Build**: Completado sin warnings
5. **Migrations**: Aplicadas y commiteadas
6. **Env vars**: Documentadas en .env.example
7. **Dependencies**: Auditadas (npm audit / pip audit)
8. **CHANGELOG**: Actualizado

## Resultado

Generar reporte:
- PASS / FAIL por cada item
- Bloqueantes que impiden deploy
- Warnings que deberian revisarse
```

### Skill con hooks: Operaciones seguras

```yaml
---
name: secure-deploy
description: >
  Deployment with security validation. ALWAYS invoke for production deploys.
disable-model-invocation: true
context: fork
agent: general-purpose
allowed-tools: Bash(git:*), Bash(docker:*), Read, Grep
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'Validating command safety...'"
---

# Secure Deploy

Todas las operaciones Bash son validadas antes de ejecutarse.

## Workflow
1. Verificar branch es main/master
2. Verificar tests pasan
3. Build de produccion
4. Deploy con rollback plan
```

### Skill con scripts: Validador de esquema

```text
validate-schema/
├── SKILL.md
└── scripts/
    └── validate.py
```

```yaml
---
name: validate-schema
description: >
  Validate database schema against models. Use when modifying
  models, creating migrations, or checking schema consistency.
allowed-tools: Bash(python:*), Read
---

# Schema Validator

Run the validation script:

```bash
python {baseDir}/scripts/validate.py
```

## Interpretation
- GREEN: Schema matches models
- YELLOW: Pending migrations detected
- RED: Schema mismatch, needs migration
```

### Skill multi-agente: Pre-merge workflow

```yaml
---
name: pre-merge
description: >
  Complete pre-merge workflow: code review + merge message.
  Use before merging branches.
disable-model-invocation: true
---

# Pre-Merge Workflow

## Fase 1: Code Review
Delegar a subagente `code-review-branch`:
- Analizar diff contra rama base
- Validar estandares de CLAUDE.md
- Validar seguridad del booking SaaS (JWT, CSP, RUT/RUC, MP webhooks)
- Generar reporte con severidades

## Fase 2: Evaluacion
- Issues CRITICOS -> BLOQUEAR merge
- Issues IMPORTANTES -> ADVERTIR, pedir confirmacion
- Solo SUGERENCIAS -> Continuar

## Fase 3: Mensaje de Merge
Si review pasa, generar mensaje con:
- Resumen de cambios
- Issues encontrados (si aplica)
- Conventional Commits format
```

## Progressive Disclosure (optimizacion de tokens)

| Nivel | Cuando se carga | Tamano recomendado |
|-------|----------------|-------------------|
| **Metadata** | Siempre (startup) | ~100 tokens por skill |
| **Instructions** | Al activar el skill | < 5,000 tokens (< 500 lineas) |
| **Resources** | Cuando se necesitan | Sin limite (scripts/, references/) |

Mantener SKILL.md bajo 500 lineas. Mover detalle a `references/`.

## Permisos en settings.json

```json
{
  "permissions": {
    "allow": [
      "Skill(review-code)",
      "Skill(deploy-check *)"
    ],
    "deny": [
      "Skill(dangerous-skill)"
    ]
  }
}
```

Patrones:
- `Skill` -> Denegar todos los skills
- `Skill(nombre)` -> Skill especifico
- `Skill(nombre *)` -> Skill con cualquier argumento

## Budget y Limites

| Parametro | Valor |
|-----------|-------|
| Budget default | 2% del context window |
| Budget fallback | 16,000 caracteres |
| Max largo `name` | 64 caracteres |
| Max largo `description` | 1,024 caracteres |
| SKILL.md recomendado | < 500 lineas |
| Tokens al activar | < 5,000 tokens |
| Tokens metadata (siempre) | ~100 tokens por skill |

Override de budget:

```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=32000
```

## Diagnostico Rapido

| Problema | Causa probable | Solucion |
|----------|---------------|----------|
| Skill no aparece en `/context` | Budget excedido | Reducir descriptions o eliminar skills |
| Skill no aparece en `/context` | Path incorrecto | Verificar que SKILL.md existe |
| Skill no aparece en `/context` | YAML invalido | Validar frontmatter |
| Skill aparece pero no activa | Description vaga | Aplicar descriptions directivas |
| Skill aparece pero no activa | Competencia entre skills | Diferenciar descriptions |
| Skill aparece pero no activa | Context overload | `/clear` y probar |

## Anti-patrones

| Anti-patron | Consecuencia | Alternativa |
|-------------|-------------|-------------|
| Skills prematuros | Skill inutil, no se usa | Validar el patron 3+ veces manual primero |
| SKILL.md > 500 lineas | Consume contexto excesivo | Mover detalle a `references/` |
| Description vaga | Activacion < 20% | Ser especifico con triggers y keywords |
| Info temporal ("valido hasta...") | Se rompe con el tiempo | Evitar fechas |
| Referencias anidadas (A->B->C) | Claude pierde contexto | Max 1 nivel de profundidad |
| Duplicar info | Inconsistencias | Definir en un solo lugar (SKILL.md o references/) |
| No usar `context: fork` para tareas pesadas | Contamina contexto principal | Fork para research, deploy, batch |

## Instalacion de Skills de Terceros

```bash
# Via copia directa
git clone https://github.com/user/skills-repo ./tmp/skills
cp -r ./tmp/skills/mi-skill ~/.claude/skills/

# Via --add-dir (shared skills)
claude --add-dir /path/to/shared-skills
```

**Seguridad**: Siempre leer SKILL.md y scripts/ antes de instalar. Verificar que `allowed-tools` no tenga `Bash(*)` generico.

### Repositorios de skills de la comunidad

- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) - Lista curada de skills, hooks, slash-commands
- [Claude Code Skill Factory](https://github.com/alirezarezvani/claude-code-skill-factory) - Toolkit para construir skills production-ready
- [Claude Skills Starter](https://github.com/angakh/claude-skills-starter) - 12 skills esenciales como template
- [Skills Marketplace](https://skillsmp.com) - Marketplace comunitario

## Fuentes

- [Extend Claude with skills - Docs oficiales](https://code.claude.com/docs/en/skills)
- [Agent Skills Open Standard](https://agentskills.io/specification)
- [Agent Skills GitHub](https://github.com/agentskills/agentskills)
- [Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Subagents Reference](https://code.claude.com/docs/en/sub-agents)
- [Skills 2.0 Evals Guide](https://www.pasqualepillitteri.it/en/news/341/claude-code-skills-2-0-evals-benchmarks-guide)
- [Agent Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skill vs Command Best Practices](https://oneaway.io/blog/claude-skill-vs-command)
- [650 Trials: Why Skills Don't Activate](https://medium.com/@ivan.seleznov1/why-claude-code-skills-dont-activate-and-how-to-fix-it-86f679409af1)
- [Complete Guide to Building Skills (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)

---

[Siguiente: Documentacion (CLAUDE.md)](08-docs.md)
