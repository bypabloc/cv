**05**

# Instalar ntfy + Caddy

[← Índice](README.md)

---

### Antes de empezar

- Servidor que cumple los [requisitos](03-requisitos.md).
- Registro DNS `A` creado ([capítulo 04](04-dns.md)): Caddy lo necesita para obtener el certificado.

### Script: `setup-ntfy.sh`

Idempotente: se puede volver a ejecutar sin romper nada.

```bash
#!/usr/bin/env bash
# Instala ntfy + Caddy (TLS automático) en Ubuntu 24.04. Se ejecuta EN EL SERVIDOR con sudo.
# Variables: NTFY_DOMAIN (obligatoria), NTFY_ADMIN (default admin), NTFY_PASSWORD (la lee `ntfy user add`).
set -euo pipefail
: "${NTFY_DOMAIN:?falta NTFY_DOMAIN}" "${NTFY_ADMIN:=admin}"
export DEBIAN_FRONTEND=noninteractive
ARCH=$(dpkg --print-architecture)          # amd64 o arm64

# 1. Swap de 1 GB si no hay (servidores de 1 GB de RAM)
if ! swapon --show | grep -q . && [ "$(free -m | awk '/^Mem:/{print $2}')" -lt 2000 ]; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 2. Firewall interno: si iptables termina en REJECT, abrir 80/443 antes y persistir
if iptables -S INPUT | grep -q -- '-j REJECT'; then
  pos=$(iptables -L INPUT --line-numbers | awk '/REJECT/{print $1; exit}')
  for p in 443 80; do
    iptables -C INPUT -p tcp -m state --state NEW --dport "$p" -j ACCEPT 2>/dev/null \
      || iptables -I INPUT "$pos" -p tcp -m state --state NEW --dport "$p" -j ACCEPT
  done
  command -v netfilter-persistent >/dev/null || apt-get install -y -q iptables-persistent
  netfilter-persistent save
fi

# 3. Repositorios oficiales de ntfy y Caddy
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

# 4. ntfy: solo en localhost, detrás de Caddy, cerrado por defecto
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

# 5. Caddy: HTTPS con Let's Encrypt y proxy a ntfy
cat > /etc/caddy/Caddyfile <<EOF
${NTFY_DOMAIN} {
	reverse_proxy 127.0.0.1:2586
}
EOF

systemctl enable --now ntfy caddy
systemctl restart ntfy caddy
sleep 2

# 6. Usuario administrador
ntfy user list 2>&1 | grep -q "user ${NTFY_ADMIN}" || ntfy user add --role=admin "$NTFY_ADMIN"

systemctl is-active ntfy caddy
```

### Ejecutar

La clave del admin se pide por teclado (no queda en el historial) y viaja por el entorno:

```bash
read -rsp 'Clave del admin de ntfy: ' PW; echo
ssh mi-vm "sudo env NTFY_DOMAIN=ntfy.tu-dominio.com NTFY_ADMIN=admin NTFY_PASSWORD=$(printf %q "$PW") bash -s" \
  < setup-ntfy.sh
unset PW
```

Para generar una clave aleatoria: `openssl rand -base64 18 | tr -d '/+='`.

### Qué hace cada parte

| # | Paso | Por qué |
| :-- | :-- | :-- |
| 1 | Swap de 1 GB | En servidores de 1 GB, `apt` puede quedarse sin memoria |
| 2 | Abre 80/443 antes del `REJECT` de `iptables` | Algunas imágenes bloquean todo salvo SSH |
| 3 | Repos oficiales de ntfy y Caddy | Versiones al día con `apt`; detecta `amd64`/`arm64` |
| 4 | `server.yml` | Ver abajo |
| 5 | `Caddyfile` | HTTPS automático y proxy |
| 6 | Usuario admin | Con `deny-all`, sin usuario nadie publica |

### `server.yml`, línea por línea

| Opción | Valor | Por qué |
| :-- | :-- | :-- |
| `base-url` | `https://ntfy.tu-dominio.com` | URLs correctas en la app y los adjuntos |
| `listen-http` | `127.0.0.1:2586` | Solo local: el público entra por Caddy |
| `behind-proxy` | `true` | Toma la IP real del cliente desde `X-Forwarded-For` |
| `cache-duration` | `24h` | Historial que ve la app al suscribirse |
| `auth-default-access` | `deny-all` | Nada sin usuario o token |
| `upstream-base-url` | `https://ntfy.sh` | Relay de push para iOS |

### Caddy

- Pide y renueva el certificado de Let's Encrypt solo (desafío HTTP-01 por el puerto 80, renovación ~30 días antes de vencer).
- Soporta las conexiones largas (WebSocket y streaming) de la app sin configuración extra.

### Verificar

```bash
curl https://ntfy.tu-dominio.com/v1/health                                          # {"healthy":true}
curl -s -o /dev/null -w '%{http_code}\n' -d test https://ntfy.tu-dominio.com/alertas  # 403 sin credenciales
```

Resultado real: `{"healthy":true}`, certificado válido y `403` sin credenciales.

`ntfy` `caddy` `lets-encrypt` `iptables` `ubuntu`
