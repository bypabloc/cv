**09**

# Measuring CPU like Oracle and the status report

[← Index](README.md)

---

### Two sources

| Source | Where it runs | Purpose |
| :-- | :-- | :-- |
| **Oracle Monitoring** | Oracle's API, from your PC with `oci` | The figure Oracle sees |
| **Local log** | The VM, every minute | Lets the VM report its own p95 |

### Oracle Monitoring from the CLI

The compute agent publishes `CpuUtilization` in the `oci_computeagent` namespace.

Maximum CPU per minute over the last hour and a half:

```bash
S=$(date -u -d '-90 min' +%Y-%m-%dT%H:%M:%SZ); E=$(date -u +%Y-%m-%dT%H:%M:%SZ)
oci monitoring metric-data summarize-metrics-data -c "$C" --namespace oci_computeagent \
  --query-text 'CpuUtilization[1m].max()' --start-time "$S" --end-time "$E" \
  --query 'data[0]."aggregated-datapoints"[].[timestamp,value]' --output json \
  | jq -r '.[] | "\(.[0][11:16]) UTC  \(.[1]|floor)%"'
```

95th percentile (for Oracle's actual window use `-7 days` and `[7d]`):

```bash
S=$(date -u -d '-60 min' +%Y-%m-%dT%H:%M:%SZ)
oci monitoring metric-data summarize-metrics-data -c "$C" --namespace oci_computeagent \
  --query-text 'CpuUtilization[1h].percentile(0.95)' --start-time "$S" --end-time "$E" \
  --query 'data[0]."aggregated-datapoints"[-1].value' --raw-output
```

Other metrics in the namespace: `MemoryUtilization`, `NetworksBytesIn`, `NetworksBytesOut`. In the console: instance → **Metrics**.

### Status report from the VM

The VM logs its CPU every minute, computes the 24 h and 7-day p95, checks RAM, disk, and services, and sends a report every 45 min to a **webhook** (any URL that accepts a `POST`: Slack, Discord, Telegram, your own endpoint…).

- **Why from the VM:** it doesn't depend on your PC being on, and it sees internal data.
- **Limitation:** if the VM dies, it sends nothing. **Not receiving the report for more than 45 min is the alarm.**

Sample report:

```
VM OK (16:43)
CPU p95 24h 49% · 7d 49% (min. 20%) · now 0% (load 0.00 0.00 0.01)
RAM 409/954 MB (42%) · swap 0 MB · disk 8%
active services: cron · up 45 minutes
```

#### Report script: `vm-report.sh`

```bash
#!/usr/bin/env bash
# VM status report. Run by the systemd timer every 45 min.
# Config in /etc/vm-report.env (root only):
#   REPORT_WEBHOOK=https://...        URL that receives the POST
#   REPORT_FORMAT=text|slack|discord  text: plain body; slack/discord: JSON
#   REPORT_AUTH="Bearer ..."          optional, Authorization header
#   SERVICES="cron nginx"             systemd services to watch
#   CHECK_URL=https://...             optional, public URL that must return 2xx
#   TZ_REPORT=America/Guayaquil
set -u
. /etc/vm-report.env
: "${REPORT_FORMAT:=text}" "${SERVICES:=cron}" "${TZ_REPORT:=UTC}"
fails=()

# CPU: current (5 s), load, and p95 from the per-minute log (/var/log/cpu-minute.log: "epoch pct")
cpu=$((100 - $(vmstat 5 2 | tail -1 | awk '{print $15}')))
load=$(cut -d' ' -f1-3 /proc/loadavg)
p95() {
  awk -v since="$(( $(date +%s) - $1 ))" '$1 >= since {print $2}' /var/log/cpu-minute.log 2>/dev/null \
    | sort -n | awk '{a[NR]=$1} END {if (NR) print a[int(NR*0.95 + 0.999)]; else print "?"}'
}
p95_24h=$(p95 86400); p95_7d=$(p95 604800)
[ "$p95_7d" = "?" ] || [ "$p95_7d" -ge 20 ] || fails+=("CPU p95 7d ${p95_7d}% (Oracle could reclaim it)")

# RAM, swap, disk
read -r mem_total mem_used <<<"$(free -m | awk '/^Mem:/{print $2, $3}')"
mem_pct=$((mem_used * 100 / mem_total))
swap_used=$(free -m | awk '/^Swap:/{print $3}')
disk_pct=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "$mem_pct" -lt 90 ] || fails+=("RAM ${mem_pct}%")
[ "$disk_pct" -lt 85 ] || fails+=("disk ${disk_pct}%")

# Services
for s in $SERVICES; do systemctl is-active --quiet "$s" || fails+=("$s inactive"); done

# Public URL (optional)
if [ -n "${CHECK_URL:-}" ]; then
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$CHECK_URL")
  [[ "$code" == 2* ]] || fails+=("$CHECK_URL returned $code")
fi

reboot=""; [ -f /var/run/reboot-required ] && reboot=" · reboot required"
now=$(TZ="$TZ_REPORT" date '+%H:%M')
body="CPU p95 24h ${p95_24h}% · 7d ${p95_7d}% (min. 20%) · now ${cpu}% (load ${load})
RAM ${mem_used}/${mem_total} MB (${mem_pct}%) · swap ${swap_used} MB · disk ${disk_pct}%
active services: ${SERVICES} · up $(uptime -p | sed 's/^up //')${reboot}"

if [ ${#fails[@]} -eq 0 ]; then title="VM OK ($now)"
else title="VM FAILURE ($now)"; body="$(IFS='; '; echo "${fails[*]}")
$body"; fi

case "$REPORT_FORMAT" in
  slack)   payload=$(jq -n --arg t "*$title*"$'\n'"$body" '{text: $t}');      ctype=application/json ;;
  discord) payload=$(jq -n --arg t "**$title**"$'\n'"$body" '{content: $t}'); ctype=application/json ;;
  *)       payload="$title"$'\n'"$body";                                       ctype=text/plain ;;
esac
curl -fsS -m 10 -o /dev/null -H "Content-Type: $ctype" \
  ${REPORT_AUTH:+-H "Authorization: $REPORT_AUTH"} -d "$payload" "$REPORT_WEBHOOK"
```

#### Installer: `vm-install-report.sh`

Copy `vm-report.sh` to the VM and then run this installer there:

```bash
#!/usr/bin/env bash
# Installs the per-minute CPU log and the report timer. Runs ON THE VM with sudo.
set -e
install -m 0755 /tmp/vm-report.sh /usr/local/bin/vm-report

# Configuration (edit it later with sudoedit /etc/vm-report.env)
if [ ! -f /etc/vm-report.env ]; then
  umask 077
  cat > /etc/vm-report.env <<EOF
REPORT_WEBHOOK=${REPORT_WEBHOOK:?missing REPORT_WEBHOOK}
REPORT_FORMAT=${REPORT_FORMAT:-text}
SERVICES="${SERVICES:-cron}"
CHECK_URL=${CHECK_URL:-}
TZ_REPORT=${TZ_REPORT:-UTC}
EOF
fi

# Per-minute CPU log (55 s average); daily pruning to 8 days
cat > /etc/cron.d/cpu-minute <<'EOF'
* * * * * root echo "$(date +\%s) $((100 - $(vmstat 55 2 | tail -1 | awk '{print $15}')))" >> /var/log/cpu-minute.log
17 3 * * * root f=/var/log/cpu-minute.log; awk -v s=$(( $(date +\%s) - 691200 )) '$1>=s' $f > $f.tmp && mv $f.tmp $f
EOF

cat > /etc/systemd/system/vm-report.service <<'EOF'
[Unit]
Description=VM status report
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vm-report
EOF

cat > /etc/systemd/system/vm-report.timer <<'EOF'
[Unit]
Description=VM status report every 45 minutes

[Timer]
OnBootSec=3min
OnUnitActiveSec=45min
Persistent=true

[Install]
WantedBy=timers.target
EOF

apt-get install -y -q jq >/dev/null
systemctl daemon-reload
systemctl enable --now vm-report.timer
systemctl start vm-report.service
systemctl list-timers vm-report.timer --no-pager | sed -n 2p
```

Usage from your PC:

```bash
scp vm-report.sh my-vm:/tmp/
ssh my-vm "sudo env REPORT_WEBHOOK='https://hooks.slack.com/services/...' REPORT_FORMAT=slack \
  SERVICES='cron' TZ_REPORT=America/Guayaquil bash -s" < vm-install-report.sh
```

To add the authentication header, write `REPORT_AUTH="Bearer <token>"` to `/etc/vm-report.env` with `sudoedit`.

### Details that matter

- **`vmstat 55 2`**: the second line is the 55 s average; column 15 is `idle`.
- **`%` in cron** is escaped as `\%`.
- **systemd timer, not cron:** `*/45` in cron fires at :00 and :45 (15 min gaps). `OnUnitActiveSec=45min` counts from the last run, and `Persistent=true` catches up on a missed run.
- **Measured agreement:** local p95 49% vs. Oracle 49.9% over the same hour.
- While the log has less than 7 days of data, the "7d" figure only covers what's there.

### Operating the report

```bash
sudo systemctl start vm-report.service       # report now
systemctl list-timers vm-report.timer        # next run
journalctl -u vm-report -n 20                # latest runs
sudo systemctl disable --now vm-report.timer # disable
```

`oracle-cloud` `monitoring` `p95` `systemd-timer` `webhook`
