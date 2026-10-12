**09**

# Avisos desde Claude Code

[← Índice](README.md)

---

### Por qué no basta la notificación nativa

Claude Code trae una herramienta de push al celular, pero:

- **Se omite si estás activo en la terminal** ("Not sent — this terminal is active").
- Solo llega con **Remote Control** conectado y la app de Claude con permisos.

Un hook propio con ntfy evita las dos condiciones.

### 1. Script: `~/.claude/hooks/ntfy-notify.sh`

```bash
#!/usr/bin/env bash
# Publica un aviso en tu servidor ntfy y, si está configurado, en ntfy.sh (respaldo).
# Uso: ntfy-notify.sh "mensaje" ["título"] ["tags"]
#      o JSON por stdin con campo .message (hook Notification de Claude Code).
# Variables: NTFY_URL (https://ntfy.tu-dominio.com/alertas), NTFY_TOKEN (tk_...), NTFY_TOPIC (ntfy.sh, opcional)
set -u
msg="${1:-}"
title="${2:-Claude Code · $(basename "$PWD")}"
tags="${3:-}"
if [ -z "$msg" ] && [ ! -t 0 ]; then
  msg=$(jq -r '.message // empty' 2>/dev/null)
fi
msg="${msg:-Claude necesita tu atención}"

rc=0
if [ -n "${NTFY_URL:-}" ] && [ -n "${NTFY_TOKEN:-}" ]; then
  curl -fsS -m 10 -o /dev/null -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: $title" ${tags:+-H "Tags: $tags"} -d "$msg" "$NTFY_URL" || rc=1
fi
if [ -n "${NTFY_TOPIC:-}" ]; then
  curl -fsS -m 10 -o /dev/null -H "Title: $title" ${tags:+-H "Tags: $tags"} \
    -d "$msg" "https://ntfy.sh/${NTFY_TOPIC}" || rc=1
fi
exit $rc
```

### 2. Variables en `~/.claude/settings.json`

```json
{
  "env": {
    "NTFY_URL": "https://ntfy.tu-dominio.com/alertas",
    "NTFY_TOKEN": "<TU_TOKEN>",
    "NTFY_TOPIC": "<tema-aleatorio>"
  }
}
```

- Sin `NTFY_TOPIC`, solo usa tu servidor.
- `settings.json` queda con el token en texto plano: no lo subas a ningún repo.

### 3. Hook `Notification`

Se dispara cuando Claude Code espera tu permiso o tu respuesta. Agrégalo al mismo `settings.json`, junto a lo que ya tengas:

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/ntfy-notify.sh >/dev/null 2>&1 || true",
            "async": true
          }
        ]
      }
    ]
  }
}
```

- `async: true`: no frena a Claude Code mientras envía.
- `|| true`: si ntfy falla, el hook no da error.
- El script lee el campo `.message` del JSON que recibe el hook por stdin.

### 4. Activarlo

- Toma efecto en la próxima sesión, o en la actual después de abrir `/hooks` una vez.
- Valida el JSON: `jq -e '.hooks.Notification[0].hooks[0].command' ~/.claude/settings.json`.

### 5. Probarlo

```bash
echo '{"message":"Prueba del hook"}' | NTFY_URL=... NTFY_TOKEN=... bash ~/.claude/hooks/ntfy-notify.sh; echo "exit=$?"
```

### 6. Pedirle avisos a Claude

"Avísame cuando termine el CI": Claude puede ejecutar el mismo script al terminar:

```bash
bash ~/.claude/hooks/ntfy-notify.sh "CI terminado" "Claude Code" "white_check_mark"
```

`claude-code` `hooks` `ntfy`
