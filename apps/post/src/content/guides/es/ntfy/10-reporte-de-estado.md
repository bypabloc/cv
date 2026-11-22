**10**

# Reporte de estado cada 45 minutos

[← Índice](README.md)

---

### Qué es

El servidor se revisa a sí mismo cada 45 min y envía el reporte completo a tu ntfy; a ntfy.sh, si configuras `NTFY_TOPIC`, solo un latido sin métricas:

```
ntfy OK (16:43)
CPU 0% (load 0.00 0.00 0.01) · RAM 409/954 MB (42%) · swap 0 MB · disco 8%
ntfy, caddy y cron activos · TLS 89 días · encendido 45 min
```

- **Desde el servidor:** no depende de que tu PC esté encendida y ve datos internos.
- **Latido en ntfy.sh, sin métricas:** los tópicos de ntfy.sh son públicos y el nombre funciona como contraseña ([docs.ntfy.sh/publish](https://docs.ntfy.sh/publish/#public-topics)): quien lo conozca lee todo. Por eso ahí solo va el título, `ntfy OK (hh:mm)` o `FALLO ntfy (hh:mm)`, sin CPU, RAM, disco, servicios, días de TLS ni el detalle de las fallas. Si tu ntfy deja de responder, el `FALLO` llega igual por ntfy.sh y el detalle queda en `journalctl -u ntfy-report`.
- **Límite:** si el servidor muere por completo, no envía nada. **No recibir el reporte por más de 45 min es la alarma.**

### Qué revisa

| Revisión | Cómo | Falla si |
| :-- | :-- | :-- |
| CPU y carga | `vmstat 5 2`, `/proc/loadavg` | Solo informativo |
| RAM, swap, disco | `free -m`, `df` | RAM ≥ 90 % o disco ≥ 85 % |
| Servicios | `systemctl is-active ntfy caddy cron` | Alguno inactivo |
| Ruta pública completa | `curl https://<dominio>/v1/health` desde el servidor | No responde `healthy` |
| Certificado | `openssl s_client` → días a `notAfter` | Menos de 10 días (la renovación falló) |
| Reinicio pendiente | `/var/run/reboot-required` | Solo informativo |

| Resultado | Título | Prioridad | Emoji |
| :-- | :-- | :-- | :-- |
| Todo bien | `ntfy OK (hh:mm)` | `low` (sin sonido) | ✅ |
| Algo falla | `FALLO ntfy (hh:mm)` + lista de fallas | `high` | 🚨 |

En ntfy.sh llega solo el título de esta tabla, con la misma prioridad y emoji.

### Script: `ntfy-report.sh`

```bash
#!/usr/bin/env bash
# Reporte de estado del servidor ntfy. Lo ejecuta el timer systemd cada 45 min.
# Config en /etc/ntfy-report.env (solo root):
#   NTFY_TOKEN=tk_...  NTFY_DOMAIN=ntfy.tu-dominio.com  NTFY_LOCAL_TOPIC=alertas
#   NTFY_TOPIC=<tema-aleatorio>  TZ_REPORT=America/Guayaquil
set -u
. /etc/ntfy-report.env
: "${NTFY_LOCAL_TOPIC:=alertas}" "${TZ_REPORT:=UTC}"
fails=()

cpu=$((100 - $(vmstat 5 2 | tail -1 | awk '{print $15}')))
load=$(cut -d' ' -f1-3 /proc/loadavg)

read -r mem_total mem_used <<<"$(free -m | awk '/^Mem:/{print $2, $3}')"
mem_pct=$((mem_used * 100 / mem_total))
swap_used=$(free -m | awk '/^Swap:/{print $3}')
disk_pct=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "$mem_pct" -lt 90 ] || fails+=("RAM ${mem_pct}%")
[ "$disk_pct" -lt 85 ] || fails+=("disco ${disk_pct}%")

for s in ntfy caddy cron; do
  systemctl is-active --quiet "$s" || fails+=("$s inactivo")
done

# Ruta pública completa: DNS + TLS + Caddy + ntfy
health=$(curl -fsS -m 10 "https://${NTFY_DOMAIN}/v1/health" 2>&1)
[[ "$health" == *'"healthy":true'* ]] || fails+=("health público: ${health:0:80}")

# Días de TLS
end=$(echo | openssl s_client -servername "$NTFY_DOMAIN" -connect "$NTFY_DOMAIN:443" 2>/dev/null \
  | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$end" ]; then
  tls=$(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 ))
  [ "$tls" -ge 10 ] || fails+=("TLS vence en $tls días")
else
  tls="?"; fails+=("TLS sin certificado")
fi

reboot=""; [ -f /var/run/reboot-required ] && reboot=" · requiere reinicio"
now=$(TZ="$TZ_REPORT" date '+%H:%M')
body="CPU ${cpu}% (load ${load}) · RAM ${mem_used}/${mem_total} MB (${mem_pct}%) · swap ${swap_used} MB · disco ${disk_pct}%
ntfy, caddy y cron activos · TLS ${tls} días · encendido $(awk '{s=int($1); d=int(s/86400); h=int(s%86400/3600); m=int(s%3600/60); if (d) printf "%d d ", d; if (h) printf "%d h ", h; printf "%d min", m}' /proc/uptime)${reboot}"

if [ ${#fails[@]} -eq 0 ]; then
  title="ntfy OK ($now)"; tags="white_check_mark"; prio="low"
else
  title="FALLO ntfy ($now)"; tags="rotating_light"; prio="high"
  body="$(IFS='; '; echo "${fails[*]}")
$body"
fi

post() { curl -fsS -m 10 -o /dev/null -H "Title: $title" -H "Tags: $tags" -H "Priority: $prio" "$@"; }
post -H "Authorization: Bearer ${NTFY_TOKEN}" -d "$body" "http://127.0.0.1:2586/${NTFY_LOCAL_TOPIC}"
# ntfy.sh es público para quien conozca el tópico: solo el latido (OK/FALLO), sin métricas
[ -z "${NTFY_TOPIC:-}" ] || post -d "$title" "https://ntfy.sh/${NTFY_TOPIC}"
```

> Publica a tu ntfy por `127.0.0.1:2586` (sin pasar por Caddy): así el aviso de "Caddy caído" o "TLS vencido" también llega por tu servidor.

### Instalador: `install-ntfy-report.sh`

```bash
#!/usr/bin/env bash
# Instala el reporte como timer systemd cada 45 min. Se ejecuta EN EL SERVIDOR con sudo,
# con ntfy-report.sh copiado antes a /tmp.
set -e
: "${NTFY_DOMAIN:?falta NTFY_DOMAIN}" "${NTFY_ADMIN:=admin}"
install -m 0755 /tmp/ntfy-report.sh /usr/local/bin/ntfy-report

# Token propio para el reporte (revocable sin afectar a otros)
if [ ! -f /etc/ntfy-report.env ]; then
  TK=$(ntfy token add --label server-report "$NTFY_ADMIN" | grep -oE 'tk_[a-z0-9]+')
  umask 077
  printf 'NTFY_TOKEN=%s\nNTFY_DOMAIN=%s\nNTFY_LOCAL_TOPIC=%s\nNTFY_TOPIC=%s\nTZ_REPORT=%s\n' \
    "$TK" "$NTFY_DOMAIN" "${NTFY_LOCAL_TOPIC:-alertas}" "${NTFY_TOPIC:-}" "${TZ_REPORT:-UTC}" \
    > /etc/ntfy-report.env
fi

cat > /etc/systemd/system/ntfy-report.service <<'EOF'
[Unit]
Description=Reporte de estado del servidor ntfy
After=network-online.target ntfy.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ntfy-report
EOF

cat > /etc/systemd/system/ntfy-report.timer <<'EOF'
[Unit]
Description=Reporte de estado del servidor ntfy cada 45 minutos

[Timer]
OnBootSec=3min
OnUnitActiveSec=45min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now ntfy-report.timer
systemctl start ntfy-report.service
systemctl list-timers ntfy-report.timer --no-pager | sed -n 2p
```

### Instalar desde tu PC

```bash
scp ntfy-report.sh mi-vm:/tmp/
ssh mi-vm "sudo env NTFY_DOMAIN=ntfy.tu-dominio.com NTFY_ADMIN=admin NTFY_LOCAL_TOPIC=alertas \
  NTFY_TOPIC=<tema-aleatorio> TZ_REPORT=America/Guayaquil bash -s" < install-ntfy-report.sh
```

### Por qué un timer de systemd y no cron

- `cron` no puede expresar "cada 45 minutos": `*/45` dispara a :00 y :45, con huecos de 15 min.
- `OnUnitActiveSec=45min` cuenta desde la última ejecución.
- `OnBootSec=3min` envía un reporte 3 min después de cada arranque, así que un apagado no deja un hueco largo.

### Operar

```bash
sudo systemctl start ntfy-report.service         # reporte ahora
systemctl list-timers ntfy-report.timer          # próxima ejecución
journalctl -u ntfy-report -n 20                  # últimas ejecuciones
sudo systemctl disable --now ntfy-report.timer   # desactivar
```

32 envíos al día a cada destino (el reporte completo a tu ntfy, el latido a ntfy.sh): por debajo del límite de 250/día de ntfy.sh gratis.

`ntfy` `monitoring` `systemd-timer` `healthcheck`
