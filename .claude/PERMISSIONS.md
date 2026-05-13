# Politica de Permissions de Claude Code

> Toda configuracion de permissions, hooks y attribution vive en
> `.claude/settings.json` (versionado, compartido entre colaboradores).
> El archivo `.claude/settings.local.json` quedo eliminado del proyecto.

## Filosofia

Sweet spot autonomia/seguridad: **`acceptEdits` + allowlist quirurgico
+ deny robusto + hooks PreToolUse**. NO escalar a `bypassPermissions` como
modo default — solo para sesiones one-shot controladas.

Anthropic guidance 2026: `bypassPermissions` se reserva para sandboxes
efimeros (CI runs, scripts headless), no para uso interactivo cotidiano.

## Reglas

### NO crear `.claude/settings.local.json`

El archivo esta en `.gitignore` por lo que cualquier colaborador puede
crearlo, pero el proyecto NO depende de el. Toda la config de equipo va
en `settings.json` versionado.

Si necesitas un override local:

- WebFetch a dominios personales no listados: agrega al allow del
  `settings.local.json` SOLO esos dominios. Nunca permissions de Bash o
  herramientas core.
- Skills personales (no del proyecto): agregalas en
  `settings.local.json` solo en `Skill(...)` allow.
- NUNCA agregar `Edit(*)`, `Write(*)`, `Bash(docker:*)`, `Bash(git push:*)`
  ni similares en local. Si los necesitas, justificalo y movelos al
  `settings.json` versionado para que el resto del equipo los reciba.

### `defaultMode: acceptEdits`

Activo a nivel proyecto. Significa:

- Edit/Write/MultiEdit en working dir: auto-aprobado
- Bash: validado contra allow/deny + hooks PreToolUse
- WebFetch: solo dominios en allowlist
- MCP tools: requieren prompt manual (security default)

### Allowlist scoped (no `*`)

Cada `Bash(...)` permitido define el comando + scope:

- Bien: `Bash(pnpm exec biome check:*)` — un subcomando especifico
- Mal: `Bash(pnpm:*)` cuando solo se quieren los subcomandos basicos (usar `pnpm run`, `pnpm exec`, etc. por separado si quieres mas granular)
- Bien: `Bash(git push origin feature/:*)` — solo branches feature/
- Mal: `Bash(git push:*)` — permite push a master/main/dev

### Deny list robusto

`settings.json` incluye 30+ deny entries cubriendo:

- `rm -rf /`, `~`, `/etc/`, `/usr/`, `.git/`, `.git-hooks/`, `.claude/`
- `git push --force` (todas las variantes)
- `git push origin master|main|dev|release` (ramas protegidas)
- `git reset --hard`, `git clean -fd`, `git branch -D`
- `sudo:*`
- `curl|wget * | bash|sh` (descargas a shell remoto)

### Hooks PreToolUse como segunda linea

Aunque la deny list cubra patrones literales, los hooks PreToolUse
detectan patrones contextuales que el matcher textual no alcanza:

- `protect-bash.sh`: detecta redirects a `.env`, modificacion de
  `.git-hooks/`, pipes `curl|bash`, `--no-verify`, `chmod 777`, edicion
  in-place de lockfiles.
- `protect-branch.sh`: bloquea `git commit/push/merge` cuando HEAD esta
  en rama protegida (master/main/dev/release).
- `protect-sensitive.sh`: bloquea Edit/Write a `.env`, secrets, keys,
  `.git-hooks/`, `.git/config`, `.git/hooks/`.

Mensaje de bloqueo siempre indica el motivo y el comando alternativo.

## Modo bypass para autonomia total (one-shot)

Para validar autonomia full sin prompts, usar:

```bash
claude --permission-mode bypassPermissions -p "<tarea>"
```

Casos de uso aceptables:

- CI: validar que un agente puede completar una tarea end-to-end sin
  intervencion humana.
- Scripts: ejecutar batch de fixes triviales con review posterior.
- Demos: mostrar capacidades autonomas en presentaciones.

NUNCA usar como modo default interactivo. Razones:

1. Saltea TODA la deny list y los hooks PreToolUse.
2. Permite operaciones destructivas accidentales sin confirmacion.
3. No queda registro de que comandos se aprobaron implicitamente.

Si en CI necesitas autonomia + seguridad, prefiere correr en sandbox
efimero (Docker container desechable) en vez de bypass directo.

## Como auditar permissions

```bash
# Validar JSON
python3 -m json.tool .claude/settings.json > /dev/null && echo OK

# Listar entradas allow
python3 -c "import json; d=json.load(open('.claude/settings.json')); [print(f'  {x}') for x in d['permissions']['allow']]"

# Contar deny entries
python3 -c "import json; d=json.load(open('.claude/settings.json')); print(len(d['permissions']['deny']))"

# Ver hooks activos
python3 -c "import json; d=json.load(open('.claude/settings.json')); [print(f'{k}: {len(v)} matcher(s)') for k,v in d['hooks'].items()]"
```

## Si tienes dudas

1. Lee `.claude/hooks/README.md` (todos los hooks documentados).
2. Lee `.claude/rules/general.md` (stack y workflow).
3. Revisa `.claude/settings.json` para ver el allow/deny actual.
