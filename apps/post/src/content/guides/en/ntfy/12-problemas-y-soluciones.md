**12**

# Problems and solutions

[← Index](README.md)

---

### Installation and network

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| `curl https://...` hangs | Port 443 closed in the cloud firewall or in `iptables` | Open it in both layers ([chapter 03](03-requisitos.md)) |
| Certificate error | DNS did not point to the IP yet when Caddy started | Wait for propagation; `journalctl -u caddy -n 50`; `sudo systemctl restart caddy` |
| 502 Bad Gateway | ntfy down | `systemctl status ntfy` |
| `apt` dies on a 1 GB server | No swap | The script creates 1 GB of swap |

### Publishing and receiving

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| 403 when publishing | `auth-default-access: deny-all` with no credentials | `-H "Authorization: Bearer tk_..."` |
| 401 with a token | Token revoked or copied wrong | `sudo ntfy token list admin` |
| Messages published but not received | Nobody subscribed to that topic | Subscribe to the topic; you'll only see what was published in the last 24 h |
| App "reconnecting…" with ⚠ | Topic with `/` (a URL was pasted) | Just the topic name |
| Notifications that do not ring | Permissions or battery optimization | Allow notifications and set battery to "Unrestricted" |
| iOS does not receive | Relay missing | `upstream-base-url: "https://ntfy.sh"` |

### Claude Code

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| The native notification says "Not sent — this terminal is active" | Skipped while you are in the terminal | Your own hook with ntfy ([chapter 09](09-claude-code.md)) |
| The hook does not fire | Configuration not reloaded | Open `/hooks` once or start a new session |
| `settings.json` stops loading | Invalid JSON | `jq -e . ~/.claude/settings.json` |

### Status report

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| "Every 45 min" with cron fires at :00 and :45 | `*/45` is not a real interval | systemd timer with `OnUnitActiveSec=45min` |
| A dead server does not alert | It cannot report if it is dead | The **absence** of a report for more than 45 min is the alarm |
| Too many alerts with sound | All with high priority | "OK" with `low`, "FAILURE" with `high` |

`troubleshooting` `ntfy`
