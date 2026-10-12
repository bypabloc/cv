# Your own push notification server with ntfy

> A complete guide to running ntfy on your own domain with automatic HTTPS and private access, receiving notifications on your phone from any script with a single `curl`, and integrating it with Claude Code and a server status report.

**Cost:** whatever your VM costs (can be USD 0) · **Time:** ~45 min · **Level:** intermediate (Linux, SSH, DNS)

---

## TL;DR

- **What you get:** `https://ntfy.your-domain.com`, private (user and token), with a Let's Encrypt TLS certificate that renews itself.
- **What you need:** an Ubuntu 24.04 VM with a public IP (any provider), a domain, and access to its DNS.
- **How you publish:** `curl -H "Authorization: Bearer $TOKEN" -d "Hello" https://ntfy.your-domain.com/alertas`.
- **Fallback:** free ntfy.sh receives the failure alert if your server goes down.
- **Monitoring:** every 45 min the server sends its status (services, RAM, disk, TLS days left).

---

## Index

| # | Chapter | What it covers |
| :-- | :-- | :-- |
| 01 | [What ntfy is and when to run your own](01-que-es-ntfy.md) | Architecture and alternatives (free ntfy.sh, Supporter, self-hosted server) |
| 02 | [Free ntfy.sh and its limits](02-ntfy-sh-limites.md) | When the public instance is enough |
| 03 | [Server requirements](03-requisitos.md) | VM, ports, provider firewall |
| 04 | [DNS](04-dns.md) | Unproxied `A` record; Cloudflare via API |
| 05 | [Install ntfy + Caddy](05-instalacion.md) | Idempotent script with automatic TLS |
| 06 | [Users, permissions and tokens](06-usuarios-y-tokens.md) | `deny-all`, admin, one token per system |
| 07 | [Set up the phone app](07-app-movil.md) | Android, iOS and the topic-with-`/` error |
| 08 | [Publish with curl](08-publicar-con-curl.md) | Title, priority, emojis, scheduled messages |
| 09 | [Alerts from Claude Code](09-claude-code.md) | `Notification` hook and alert script |
| 10 | [Status report every 45 min](10-reporte-de-estado.md) | The server reports its own health |
| 11 | [Operations](11-operacion.md) | Passwords, tokens, logs, updates, removal |
| 12 | [Problems and solutions](12-problemas-y-soluciones.md) | Everything that failed and how it was fixed |

---

## Conventions

- **Example values:** domain `ntfy.your-domain.com`, IP `203.0.113.10`, user `admin`, topic `alertas`, SSH alias `mi-vm`.
- **Placeholders:** `<YOUR_TOKEN>`, `<random-topic>`. Never publish tokens or passwords.
- **Terminal:** Linux or WSL2 with `bash`, `curl` and `jq`.
- **Data as of:** October 2026.

`ntfy` `push-notifications` `caddy` `self-hosting` `claude-code`
