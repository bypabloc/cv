**09**

# Medir la CPU como Oracle y reporte de estado

[← Índice](README.md)

---

### Dos fuentes

| Fuente | Dónde corre | Para qué |
| :-- | :-- | :-- |
| **Oracle Monitoring** | API de Oracle, desde tu PC con `oci` | La cifra que ve Oracle |
| **Registro local** | La VM, cada minuto | Que la VM informe sola su p95 |

### Oracle Monitoring desde la CLI

El agente de cómputo publica `CpuUtilization` en el namespace `oci_computeagent`.

CPU máxima por minuto de la última hora y media:

```bash
S=$(date -u -d '-90 min' +%Y-%m-%dT%H:%M:%SZ); E=$(date -u +%Y-%m-%dT%H:%M:%SZ)
oci monitoring metric-data summarize-metrics-data -c "$C" --namespace oci_computeagent \
  --query-text 'CpuUtilization[1m].max()' --start-time "$S" --end-time "$E" \
  --query 'data[0]."aggregated-datapoints"[].[timestamp,value]' --output json \
  | jq -r '.[] | "\(.[0][11:16]) UTC  \(.[1]|floor)%"'
```

Percentil 95 (para la ventana real de Oracle usa `-7 days` y `[1d]`: obtienes un p95 por día, porque MQL no acepta intervalos mayores a `1d`):

```bash
S=$(date -u -d '-60 min' +%Y-%m-%dT%H:%M:%SZ)
oci monitoring metric-data summarize-metrics-data -c "$C" --namespace oci_computeagent \
  --query-text 'CpuUtilization[1h].percentile(0.95)' --start-time "$S" --end-time "$E" \
  --query 'data[0]."aggregated-datapoints"[-1].value' --raw-output
```

Otras métricas del namespace: `MemoryUtilization`, `NetworksBytesIn`, `NetworksBytesOut`. En la consola: instancia → **Metrics**.

### Reporte de estado desde la VM

La VM registra su CPU cada minuto, calcula el p95 de 24 h y de 7 días, revisa RAM, disco y servicios, y envía un reporte cada 45 min a un **webhook** (cualquier URL que acepte un `POST`: Slack, Discord, Telegram, un endpoint propio…).

- **Por qué desde la VM:** no depende de que tu PC esté encendida y ve datos internos.
- **Límite:** si la VM muere, no envía nada. **Si pasan más de 45 min sin reporte, esa es la alarma.**

Ejemplo de reporte:

```
VM OK (16:43)
CPU p95 24h 49% · 7d 49% (mín. 20%) · ahora 0% (load 0.00 0.00 0.01)
RAM 409/954 MB (42%) · swap 0 MB · disco 8%
servicios activos: cron · encendida 45 minutes
```

#### Script del reporte: `vm-report.sh`

```bash
#!/usr/bin/env bash
# Reporte de estado de la VM. Lo ejecuta el timer systemd cada 45 min.
# Config en /etc/vm-report.env (solo root):
#   REPORT_WEBHOOK=https://...        URL que recibe el POST
#   REPORT_FORMAT=text|slack|discord  text: cuerpo plano; slack/discord: JSON
#   REPORT_AUTH="Bearer ..."          opcional, header Authorization
#   SERVICES="cron nginx"             servicios systemd a vigilar
#   CHECK_URL=https://...             opcional, URL pública que debe responder 2xx
#   TZ_REPORT=America/Guayaquil
set -u
. /etc/vm-report.env
: "${REPORT_FORMAT:=text}" "${SERVICES:=cron}" "${TZ_REPORT:=UTC}"
fails=()

# CPU: actual (5 s), carga y p95 del registro por minuto (/var/log/cpu-minute.log: "epoch pct")
cpu=$((100 - $(vmstat 5 2 | tail -1 | awk '{print $15}')))
load=$(cut -d' ' -f1-3 /proc/loadavg)
p95() {
  awk -v since="$(( $(date +%s) - $1 ))" '$1 >= since {print $2}' /var/log/cpu-minute.log 2>/dev/null \
    | sort -n | awk '{a[NR]=$1} END {if (NR) print a[int(NR*0.95 + 0.999)]; else print "?"}'
}
p95_24h=$(p95 86400); p95_7d=$(p95 604800)
[ "$p95_7d" = "?" ] || [ "$p95_7d" -ge 20 ] || fails+=("CPU p95 7d ${p95_7d}% (Oracle podría reclamarla)")

# RAM, swap, disco
read -r mem_total mem_used <<<"$(free -m | awk '/^Mem:/{print $2, $3}')"
mem_pct=$((mem_used * 100 / mem_total))
swap_used=$(free -m | awk '/^Swap:/{print $3}')
disk_pct=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "$mem_pct" -lt 90 ] || fails+=("RAM ${mem_pct}%")
[ "$disk_pct" -lt 85 ] || fails+=("disco ${disk_pct}%")

# Servicios
for s in $SERVICES; do systemctl is-active --quiet "$s" || fails+=("$s inactivo"); done

# URL pública (opcional)
if [ -n "${CHECK_URL:-}" ]; then
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$CHECK_URL")
  [[ "$code" == 2* ]] || fails+=("$CHECK_URL respondió $code")
fi

reboot=""; [ -f /var/run/reboot-required ] && reboot=" · requiere reinicio"
now=$(TZ="$TZ_REPORT" date '+%H:%M')
body="CPU p95 24h ${p95_24h}% · 7d ${p95_7d}% (mín. 20%) · ahora ${cpu}% (load ${load})
RAM ${mem_used}/${mem_total} MB (${mem_pct}%) · swap ${swap_used} MB · disco ${disk_pct}%
servicios activos: ${SERVICES} · encendida $(uptime -p | sed 's/^up //')${reboot}"

if [ ${#fails[@]} -eq 0 ]; then title="VM OK ($now)"
else title="FALLO VM ($now)"; body="$(IFS='; '; echo "${fails[*]}")
$body"; fi

case "$REPORT_FORMAT" in
  slack)   payload=$(jq -n --arg t "*$title*"$'\n'"$body" '{text: $t}');      ctype=application/json ;;
  discord) payload=$(jq -n --arg t "**$title**"$'\n'"$body" '{content: $t}'); ctype=application/json ;;
  *)       payload="$title"$'\n'"$body";                                       ctype=text/plain ;;
esac
curl -fsS -m 10 -o /dev/null -H "Content-Type: $ctype" \
  ${REPORT_AUTH:+-H "Authorization: $REPORT_AUTH"} -d "$payload" "$REPORT_WEBHOOK"
```

#### Instalador: `vm-install-report.sh`

Copia `vm-report.sh` a la VM y luego ejecuta este instalador allí:

```bash
#!/usr/bin/env bash
# Instala el registro de CPU por minuto y el timer del reporte. Se ejecuta EN LA VM con sudo.
set -e
install -m 0755 /tmp/vm-report.sh /usr/local/bin/vm-report

# Configuración (edítala después con sudoedit /etc/vm-report.env)
if [ ! -f /etc/vm-report.env ]; then
  umask 077
  cat > /etc/vm-report.env <<EOF
REPORT_WEBHOOK=${REPORT_WEBHOOK:?falta REPORT_WEBHOOK}
REPORT_FORMAT=${REPORT_FORMAT:-text}
SERVICES="${SERVICES:-cron}"
CHECK_URL=${CHECK_URL:-}
TZ_REPORT=${TZ_REPORT:-UTC}
EOF
fi

# Registro de CPU por minuto (promedio de 55 s); poda diaria a 8 días
cat > /etc/cron.d/cpu-minute <<'EOF'
* * * * * root echo "$(date +\%s) $((100 - $(vmstat 55 2 | tail -1 | awk '{print $15}')))" >> /var/log/cpu-minute.log
17 3 * * * root f=/var/log/cpu-minute.log; awk -v s=$(( $(date +\%s) - 691200 )) '$1>=s' $f > $f.tmp && mv $f.tmp $f
EOF

cat > /etc/systemd/system/vm-report.service <<'EOF'
[Unit]
Description=Reporte de estado de la VM
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vm-report
EOF

cat > /etc/systemd/system/vm-report.timer <<'EOF'
[Unit]
Description=Reporte de estado de la VM cada 45 minutos

[Timer]
OnBootSec=3min
OnUnitActiveSec=45min

[Install]
WantedBy=timers.target
EOF

apt-get install -y -q jq >/dev/null
systemctl daemon-reload
systemctl enable --now vm-report.timer
systemctl start vm-report.service
systemctl list-timers vm-report.timer --no-pager | sed -n 2p
```

Uso desde tu PC:

```bash
scp vm-report.sh mi-vm:/tmp/
ssh mi-vm "sudo env REPORT_WEBHOOK='https://hooks.slack.com/services/...' REPORT_FORMAT=slack \
  SERVICES='cron' TZ_REPORT=America/Guayaquil bash -s" < vm-install-report.sh
```

Para agregar la cabecera de autenticación, escribe `REPORT_AUTH="Bearer <token>"` en `/etc/vm-report.env` con `sudoedit`.

### Detalles que importan

- **`vmstat 55 2`**: el segundo renglón es el promedio de 55 s; la columna 15 es `idle`.
- **`%` en cron** se escapa como `\%`.
- **Timer de systemd y no cron:** `*/45` en cron dispara a :00 y :45 (huecos de 15 min). `OnUnitActiveSec=45min` cuenta desde la última ejecución y `OnBootSec=3min` envía un reporte tras cada arranque.
- **Coincidencia medida:** p95 local 49 % vs. Oracle 49,9 % en la misma hora.
- Mientras el registro tenga menos de 7 días, la cifra de "7d" cubre solo lo que haya.

### Operar el reporte

```bash
sudo systemctl start vm-report.service       # reporte ahora
systemctl list-timers vm-report.timer        # próxima ejecución
journalctl -u vm-report -n 20                # últimas ejecuciones
sudo systemctl disable --now vm-report.timer # desactivar
```

`oracle-cloud` `monitoring` `p95` `systemd-timer` `webhook`
