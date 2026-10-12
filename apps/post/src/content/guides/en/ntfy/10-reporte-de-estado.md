**10**

# Status report every 45 minutes

[← Index](README.md)

---

### What it is

Every 45 min the server checks itself and sends the result to your ntfy **and** to ntfy.sh:

```
ntfy OK (16:43)
CPU 0% (load 0.00 0.00 0.01) · RAM 409/954 MB (42%) · swap 0 MB · disk 8%
ntfy, caddy and cron active · TLS 89 days · up 45 minutes
```

- **From the server:** it does not depend on your PC being on, and it sees internal data.
- **Two destinations:** if your ntfy stops responding, the alert still arrives through ntfy.sh.
- **Limit:** if the server dies completely, it sends nothing. **Not receiving the report for more than 45 min is the alarm.**

### What it checks

| Check | How | Fails if |
| :-- | :-- | :-- |
| CPU and load | `vmstat 5 2`, `/proc/loadavg` | Informational only |
| RAM, swap, disk | `free -m`, `df` | RAM ≥ 90 % or disk ≥ 85 % |
| Services | `systemctl is-active ntfy caddy cron` | Any of them inactive |
| Full public path | `curl https://<domain>/v1/health` from the server | Does not answer `healthy` |
| Certificate | `openssl s_client` → days until `notAfter` | Fewer than 10 days (renewal failed) |
| Pending reboot | `/var/run/reboot-required` | Informational only |

| Result | Title | Priority | Emoji |
| :-- | :-- | :-- | :-- |
| All good | `ntfy OK (hh:mm)` | `low` (silent) | ✅ |
| Something fails | `FAILURE ntfy (hh:mm)` + list of failures | `high` | 🚨 |

### Script: `ntfy-report.sh`

```bash
#!/usr/bin/env bash
# ntfy server status report. Run by the systemd timer every 45 min.
# Config in /etc/ntfy-report.env (root only):
#   NTFY_TOKEN=tk_...  NTFY_DOMAIN=ntfy.your-domain.com  NTFY_LOCAL_TOPIC=alertas
#   NTFY_TOPIC=<random-topic>  TZ_REPORT=America/Guayaquil
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
[ "$disk_pct" -lt 85 ] || fails+=("disk ${disk_pct}%")

for s in ntfy caddy cron; do
  systemctl is-active --quiet "$s" || fails+=("$s inactive")
done

# Full public path: DNS + TLS + Caddy + ntfy
health=$(curl -fsS -m 10 "https://${NTFY_DOMAIN}/v1/health" 2>&1)
[[ "$health" == *'"healthy":true'* ]] || fails+=("public health: ${health:0:80}")

# TLS days left
end=$(echo | openssl s_client -servername "$NTFY_DOMAIN" -connect "$NTFY_DOMAIN:443" 2>/dev/null \
  | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$end" ]; then
  tls=$(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 ))
  [ "$tls" -ge 10 ] || fails+=("TLS expires in $tls days")
else
  tls="?"; fails+=("TLS without certificate")
fi

reboot=""; [ -f /var/run/reboot-required ] && reboot=" · reboot required"
now=$(TZ="$TZ_REPORT" date '+%H:%M')
body="CPU ${cpu}% (load ${load}) · RAM ${mem_used}/${mem_total} MB (${mem_pct}%) · swap ${swap_used} MB · disk ${disk_pct}%
ntfy, caddy and cron active · TLS ${tls} days · up $(uptime -p | sed 's/^up //')${reboot}"

if [ ${#fails[@]} -eq 0 ]; then
  title="ntfy OK ($now)"; tags="white_check_mark"; prio="low"
else
  title="FAILURE ntfy ($now)"; tags="rotating_light"; prio="high"
  body="$(IFS='; '; echo "${fails[*]}")
$body"
fi

post() { curl -fsS -m 10 -o /dev/null -H "Title: $title" -H "Tags: $tags" -H "Priority: $prio" "$@" -d "$body"; }
post -H "Authorization: Bearer ${NTFY_TOKEN}" "http://127.0.0.1:2586/${NTFY_LOCAL_TOPIC}"
[ -z "${NTFY_TOPIC:-}" ] || post "https://ntfy.sh/${NTFY_TOPIC}"
```

> It publishes to your ntfy via `127.0.0.1:2586` (bypassing Caddy): that way a "Caddy down" or "TLS expired" alert also arrives through your server.

### Installer: `install-ntfy-report.sh`

```bash
#!/usr/bin/env bash
# Installs the report as a systemd timer every 45 min. Runs ON THE SERVER with sudo,
# with ntfy-report.sh copied to /tmp beforehand.
set -e
: "${NTFY_DOMAIN:?NTFY_DOMAIN is missing}" "${NTFY_ADMIN:=admin}"
install -m 0755 /tmp/ntfy-report.sh /usr/local/bin/ntfy-report

# Dedicated token for the report (revocable without affecting others)
if [ ! -f /etc/ntfy-report.env ]; then
  TK=$(ntfy token add --label server-report "$NTFY_ADMIN" | grep -oE 'tk_[a-z0-9]+')
  umask 077
  printf 'NTFY_TOKEN=%s\nNTFY_DOMAIN=%s\nNTFY_LOCAL_TOPIC=%s\nNTFY_TOPIC=%s\nTZ_REPORT=%s\n' \
    "$TK" "$NTFY_DOMAIN" "${NTFY_LOCAL_TOPIC:-alertas}" "${NTFY_TOPIC:-}" "${TZ_REPORT:-UTC}" \
    > /etc/ntfy-report.env
fi

cat > /etc/systemd/system/ntfy-report.service <<'EOF'
[Unit]
Description=ntfy server status report
After=network-online.target ntfy.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ntfy-report
EOF

cat > /etc/systemd/system/ntfy-report.timer <<'EOF'
[Unit]
Description=ntfy server status report every 45 minutes

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

### Install from your PC

```bash
scp ntfy-report.sh mi-vm:/tmp/
ssh mi-vm "sudo env NTFY_DOMAIN=ntfy.your-domain.com NTFY_ADMIN=admin NTFY_LOCAL_TOPIC=alertas \
  NTFY_TOPIC=<random-topic> TZ_REPORT=America/Guayaquil bash -s" < install-ntfy-report.sh
```

### Why a systemd timer and not cron

- `cron` cannot express "every 45 minutes": `*/45` fires at :00 and :45, leaving 15-minute gaps.
- `OnUnitActiveSec=45min` counts from the last run.
- `OnBootSec=3min` sends a report 3 min after every boot, so downtime doesn't leave a long gap.

### Operate

```bash
sudo systemctl start ntfy-report.service         # report now
systemctl list-timers ntfy-report.timer          # next run
journalctl -u ntfy-report -n 20                  # latest runs
sudo systemctl disable --now ntfy-report.timer   # disable
```

32 reports per day per destination: below free ntfy.sh's 250/day limit.

`ntfy` `monitoring` `systemd-timer` `healthcheck`
