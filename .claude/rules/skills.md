---
description: "Convenciones para crear skills: frontmatter obligatorio, keywords bilingues, ubicacion en .claude/skills/"
globs: ".claude/skills/**/*.md"
---

# Skills del portfolio

## Frontmatter obligatorio

```yaml
---
name: nombre-del-skill
description: >
  Descripcion en ingles que explique CUANDO activar el skill.
  Use when the user says "keyword1", "keyword2", or "keyword3".
  Also use when the user says "keyword en espanol", "otra keyword".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "descripcion del argumento"
---
```

## Campos del frontmatter

| Campo | Obligatorio | Proposito |
|-------|-------------|-----------|
| `name` | Si | Identificador unico, kebab-case |
| `description` | Si | Cuando activar — incluir keywords en ingles Y espanol |
| `user-invocable` | Si | `true` para invocacion con `/nombre` |
| `disable-model-invocation` | No | `true` si SOLO invocacion manual |
| `allowed-tools` | No | Herramientas permitidas (minimo necesario) |
| `argument-hint` | No | Ejemplo de argumento para el usuario |

## Reglas de la description

- SIEMPRE escribir en ingles (el motor de matching es en ingles)
- SIEMPRE incluir pattern "Use when the user says..." con keywords exactas
- SIEMPRE incluir keywords en espanol para usuarios hispanohablantes
- Incluir 5-10 keywords que cubran variaciones naturales del uso
- NO usar frases genericas ("helps with coding") — ser especifico

### Enforcement

Si el usuario pide crear una skill con `description` en espanol unicamente
(o cualquier idioma que no sea ingles), DETENER y advertir antes de generar.
La descripcion siempre debe estar en ingles porque el matching de la skill por
parte del modelo es case-insensitive y entrenado primariamente en ingles.

Solo las keywords adicionales en espanol son aceptables (en la lista
"Use when the user says...") para usuarios hispanohablantes — pero la
descripcion principal y el resto del frontmatter deben estar en ingles.

Ejemplo INCORRECTO (rechazar):
```yaml
description: >
  Skill para gestionar archivos de configuracion del proyecto.
  Usar cuando el usuario diga "configurar", "settings", "config".
```

Ejemplo CORRECTO:
```yaml
description: >
  Manages project configuration files.
  Use when the user says "configure", "settings", "config",
  "configurar", "ajustes", "configuracion".
```

## Ubicacion de skills

Skills del proyecto: `.claude/skills/<nombre>/SKILL.md`

## Prioridad de skills (CRITICO)

Cuando un prompt del usuario matchea TANTO un skill del proyecto como un skill
de superpowers, el skill del proyecto SIEMPRE gana. Esto evita que
`superpowers:brainstorming` o `superpowers:using-superpowers` se inserten en
flujos donde ya existe un skill especializado.

| Si el prompt menciona... | Invocar | NO invocar |
|--------------------------|---------|------------|
| RFC, design doc, descomponer feature, atomic tasks, especificacion | `spec-workflow` | `superpowers:brainstorming` |
| TDD, red-green-refactor, test-first | `tdd-workflow` | `superpowers:test-driven-development` |
| Fix de git hooks (lint, typecheck, tests) | `fix-hooks` | — |
| Auditoria de calidad del codigo | `codebase-audit` | `superpowers:brainstorming` |
| Upgrade de dependencias pnpm | `dependency-upgrade` | — |
| CI con GitHub Actions / act | `github-actions` | — |
| Diagramas Mermaid | `mermaid` | — |
| Animaciones CSS | `animations-css` | — |
| Debug bug, root cause, falla intermitente | `superpowers:systematic-debugging` (es OK, complementario) | — |

Regla general: si existe un skill bajo `.claude/skills/<nombre>/` que matchee
el dominio, ese tiene prioridad sobre cualquier `superpowers:*`. Los superpowers
son metodologia generica; los skills del proyecto codifican convenciones
especificas que no se pueden derivar de otra forma.

## Skills referencia con baja activacion (comportamiento esperado)

Algunos skills (`codebase-audit`, `github-actions`, `mermaid`) son
**referencia documental pura**. El modelo frecuentemente responde sin
invocarlos cuando puede:

- Leer el archivo de codigo directo (mas rapido que el skill)
- Ejecutar el comando con `--help` (mas preciso)
- Citar info ya cargada en CLAUDE.md / project context

Esto es **comportamiento optimo, no un fallo**. Estos skills siguen siendo
utiles para invocacion manual `/skill-name` cuando el usuario quiere la
referencia consolidada.

## Validacion obligatoria post-cambio

Cualquier skill nueva o modificada DEBE validarse con `claude -p` antes de
commit. Comando canonico, estrategia de 5 angulos, lectura de `num_turns` y
caso real que motivo la regla: ver [claude-config-testing.md](./claude-config-testing.md).

Resumen del flujo:

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "<prompt en espanol>"
```

Aplica a TODA la carpeta `.claude/*` (skills, rules, agents, commands, hooks,
settings). Excepcion: skills con web habilitada (`research`) omiten
`--disallowedTools`.

## Referencia completa

Para crear skills, LEE [07-skills.md](../docs/claude/07-skills.md).
