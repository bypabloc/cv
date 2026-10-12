**05**

# Install ntfy + Caddy

[← Index](README.md)

---

### Before you start

- A server that meets the [requirements](03-requisitos.md).
- The DNS `A` record created ([chapter 04](04-dns.md)): Caddy needs it to obtain the certificate.

### Script: `setup-ntfy.sh`

Idempotent: it can be run again without breaking anything.

```bash
#!/usr/bin/env bash
# Installs ntfy + Caddy (automatic TLS) on Ubuntu 24.04. Runs ON THE SERVER with sudo.
# Variables: NTFY_DOMAIN (required), NTFY_ADMIN (default admin), NTFY_PASSWORD (read by `ntfy user add`).
set -euo pipefail
: "${NTFY_DOMAIN:?NTFY_DOMAIN is missing}" "${NTFY_ADMIN:=admin}"
export DEBIAN_FRONTEND=noninteractive
ARCH=$(dpkg --print-architecture)          # amd64 or arm64

# 1. 1 GB swap if there is none (servers with 1 GB of RAM)
if ! swapon --show | grep -q . && [ "$(free -m | awk '/^Mem:/{print $2}')" -lt 2000 ]; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 2. Internal firewall: if iptables ends in REJECT, open 80/443 before it and persist
if iptables -S INPUT | grep -q -- '-j REJECT'; then
  pos=$(iptables -L INPUT --line-numbers | awk '/REJECT/{print $1; exit}')
  for p in 443 80; do
    iptables -C INPUT -p tcp -m state --state NEW --dport "$p" -j ACCEPT 2>/dev/null \
      || iptables -I INPUT "$pos" -p tcp -m state --state NEW --dport "$p" -j ACCEPT
  done
  command -v netfilter-persistent >/dev/null || apt-get install -y -q iptables-persistent
  netfilter-persistent save
fi

# 3. Official ntfy and Caddy repositories
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://archive.ntfy.sh/apt/keyring.gpg -o /etc/apt/keyrings/ntfy.gpg
echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/ntfy.gpg] https://archive.ntfy.sh/apt stable main" \
  > /etc/apt/sources.list.d/ntfy.list
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  > /etc/apt/sources.list.d/caddy-stable.list
apt-get update -q
apt-get install -y -q ntfy caddy unattended-upgrades

# 4. ntfy: localhost only, behind Caddy, closed by default
cat > /etc/ntfy/server.yml <<EOF
base-url: "https://${NTFY_DOMAIN}"
listen-http: "127.0.0.1:2586"
behind-proxy: true
cache-file: "/var/cache/ntfy/cache.db"
cache-duration: "24h"
auth-file: "/var/lib/ntfy/user.db"
auth-default-access: "deny-all"
upstream-base-url: "https://ntfy.sh"
EOF
install -d -o ntfy -g ntfy /var/cache/ntfy /var/lib/ntfy

# 5. Caddy: HTTPS with Let's Encrypt and proxy to ntfy
cat > /etc/caddy/Caddyfile <<EOF
${NTFY_DOMAIN} {
	reverse_proxy 127.0.0.1:2586
}
EOF

systemctl enable --now ntfy caddy
systemctl restart ntfy caddy
sleep 2

# 6. Admin user
ntfy user list 2>&1 | grep -q "user ${NTFY_ADMIN}" || ntfy user add --role=admin "$NTFY_ADMIN"

systemctl is-active ntfy caddy
```

### Run it

The admin password is typed at a prompt (it does not end up in the history) and travels through the environment:

```bash
read -rsp 'Admin password for ntfy: ' PW; echo
ssh mi-vm "sudo env NTFY_DOMAIN=ntfy.your-domain.com NTFY_ADMIN=admin NTFY_PASSWORD=$(printf %q "$PW") bash -s" \
  < setup-ntfy.sh
unset PW
```

To generate a random password: `openssl rand -base64 18 | tr -d '/+='`.

### What each part does

| # | Step | Why |
| :-- | :-- | :-- |
| 1 | 1 GB swap | On 1 GB servers, `apt` can run out of memory |
| 2 | Opens 80/443 before the `iptables` `REJECT` | Some images block everything except SSH |
| 3 | Official ntfy and Caddy repos | Up-to-date versions via `apt`; detects `amd64`/`arm64` |
| 4 | `server.yml` | See below |
| 5 | `Caddyfile` | Automatic HTTPS and proxy |
| 6 | Admin user | With `deny-all`, nobody can publish without a user |

### `server.yml`, line by line

| Option | Value | Why |
| :-- | :-- | :-- |
| `base-url` | `https://ntfy.your-domain.com` | Correct URLs in the app and attachments |
| `listen-http` | `127.0.0.1:2586` | Local only: public traffic comes in through Caddy |
| `behind-proxy` | `true` | Takes the real client IP from `X-Forwarded-For` |
| `cache-duration` | `24h` | History the app sees when subscribing |
| `auth-default-access` | `deny-all` | Nothing without a user or token |
| `upstream-base-url` | `https://ntfy.sh` | Push relay for iOS |

### Caddy

- Obtains and renews the Let's Encrypt certificate on its own (HTTP-01 challenge on port 80, renewal ~30 days before expiry).
- Handles the app's long-lived connections (WebSocket and streaming) with no extra configuration.

### Verify

```bash
curl https://ntfy.your-domain.com/v1/health                                          # {"healthy":true}
curl -s -o /dev/null -w '%{http_code}\n' -d test https://ntfy.your-domain.com/alertas  # 403 without credentials
```

Actual result: `{"healthy":true}`, a valid certificate and `403` without credentials.

`ntfy` `caddy` `lets-encrypt` `iptables` `ubuntu`
