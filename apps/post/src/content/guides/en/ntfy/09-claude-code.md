**09**

# Alerts from Claude Code

[← Index](README.md)

---

### Why the native notification is not enough

Claude Code ships a push-to-phone tool, but:

- **It is skipped if you are active in the terminal** ("Not sent — this terminal is active").
- It only arrives with **Remote Control** connected and the Claude app granted permissions.

Your own hook with ntfy avoids both conditions.

### 1. Script: `~/.claude/hooks/ntfy-notify.sh`

```bash
#!/usr/bin/env bash
# Publishes an alert to your ntfy server and, if configured, to ntfy.sh (fallback).
# Usage: ntfy-notify.sh "message" ["title"] ["tags"]
#        or JSON on stdin with a .message field (Claude Code Notification hook).
# Variables: NTFY_URL (https://ntfy.your-domain.com/alertas), NTFY_TOKEN (tk_...), NTFY_TOPIC (ntfy.sh, optional)
set -u
msg="${1:-}"
title="${2:-Claude Code · $(basename "$PWD")}"
tags="${3:-}"
if [ -z "$msg" ] && [ ! -t 0 ]; then
  msg=$(jq -r '.message // empty' 2>/dev/null)
fi
msg="${msg:-Claude needs your attention}"

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

### 2. Variables in `~/.claude/settings.json`

```json
{
  "env": {
    "NTFY_URL": "https://ntfy.your-domain.com/alertas",
    "NTFY_TOKEN": "<YOUR_TOKEN>",
    "NTFY_TOPIC": "<random-topic>"
  }
}
```

- Without `NTFY_TOPIC`, it only uses your server.
- `settings.json` holds the token in plain text: do not push it to any repo.

### 3. `Notification` hook

It fires when Claude Code is waiting for your permission or your answer. Add it to the same `settings.json`, alongside whatever you already have:

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

- `async: true`: does not block Claude Code while sending.
- `|| true`: if ntfy fails, the hook does not error out.
- The script reads the `.message` field of the JSON the hook receives on stdin.

### 4. Enable it

- It takes effect in the next session, or in the current one after opening `/hooks` once.
- Validate the JSON: `jq -e '.hooks.Notification[0].hooks[0].command' ~/.claude/settings.json`.

### 5. Test it

```bash
echo '{"message":"Hook test"}' | NTFY_URL=... NTFY_TOKEN=... bash ~/.claude/hooks/ntfy-notify.sh; echo "exit=$?"
```

### 6. Ask Claude for alerts

"Let me know when the CI finishes": Claude can run the same script when it is done:

```bash
bash ~/.claude/hooks/ntfy-notify.sh "CI finished" "Claude Code" "white_check_mark"
```

`claude-code` `hooks` `ntfy`
