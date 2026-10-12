**06**

# Creating the instance

[← Index](README.md)

---

### A1 or Micro

| | `VM.Standard.A1.Flex` (ARM) | `VM.Standard.E2.1.Micro` (AMD) |
| :-- | :-- | :-- |
| Free CPU / RAM | Up to 2 OCPU / 12 GB | 1/8 OCPU / 1 GB |
| Availability | **Often returns "Out of host capacity"** | Usually available |
| Reclamation rule | CPU, network, **and memory** | CPU and network only |
| Avoiding reclamation | Small instance: used RAM already exceeds 20% | Needs a CPU keepalive |
| Recommendation | First choice | Plan B when A1 has no capacity |

**A1 trick:** create it with **1 OCPU and 1 GB**. Ubuntu plus a lightweight service use ~400 MB, more than 20% of the RAM: it's never considered idle and there's no need to generate artificial load. See [chapter 08](08-reclamo-por-inactividad.md).

### 1. SSH key

```bash
ssh-keygen -t ed25519 -N "" -C "oci-my-vm" -f ~/.ssh/oci_my_vm
```

### 2. Script: `oci-crear-instancia.sh`

Requires `C` and `SN` exported ([chapter 05](05-red.md)).

```bash
#!/usr/bin/env bash
# Creates the Always Free instance with Ubuntu 24.04.
# Usage: eval "$(bash oci-crear-instancia.sh a1)"     → A1 1 OCPU / 1 GB, retries every 2 min
#        eval "$(bash oci-crear-instancia.sh micro)"  → VM.Standard.E2.1.Micro
set -uo pipefail
KIND="${1:-a1}"
NAME="${NAME:-my-vm}"
SSH_PUB="${SSH_PUB:-$HOME/.ssh/oci_my_vm.pub}"
MAX_TRIES="${MAX_TRIES:-720}"             # 720 × 2 min = 24 h
: "${C:?export C}" "${SN:?export SN}"

AD=$(oci iam availability-domain list -c "$C" --query 'data[0].name' --raw-output)
if [ "$KIND" = "a1" ]; then
  SHAPE=VM.Standard.A1.Flex; CFG=(--shape-config '{"ocpus":1,"memoryInGBs":1}')
else
  SHAPE=VM.Standard.E2.1.Micro; CFG=(); MAX_TRIES=1
fi

# Latest Ubuntu 24.04 image compatible with the shape (aarch64 for A1, x86_64 for Micro)
IMG=$(oci compute image list -c "$C" --operating-system "Canonical Ubuntu" \
  --operating-system-version "24.04" --shape "$SHAPE" --sort-by TIMECREATED --sort-order DESC \
  --limit 1 --query 'data[0].id' --raw-output)

for i in $(seq 1 "$MAX_TRIES"); do
  OUT=$(oci compute instance launch -c "$C" --availability-domain "$AD" --shape "$SHAPE" "${CFG[@]}" \
    --image-id "$IMG" --subnet-id "$SN" --assign-public-ip true \
    --display-name "$NAME" --hostname-label "${NAME//-/}" --ssh-authorized-keys-file "$SSH_PUB" \
    --wait-for-state RUNNING --max-wait-seconds 600 --query 'data.id' --raw-output 2>&1)
  if [[ "$OUT" == ocid1.instance* ]]; then
    IP=$(oci compute instance list-vnics --instance-id "$OUT" --query 'data[0]."public-ip"' --raw-output)
    printf 'export I=%s\nexport IP=%s\n' "$OUT" "$IP"
    exit 0
  fi
  echo "$(date '+%F %T') attempt $i: $(echo "$OUT" | grep -o '"message": "[^"]*"' | head -1)" >&2
  [ "$i" -lt "$MAX_TRIES" ] && sleep 120
done
exit 1
```

### 3. Usage

Try A1 for a while first; if there's no capacity, fall back to Micro:

```bash
MAX_TRIES=6 bash oci-crear-instancia.sh a1 > instancia.env || bash oci-crear-instancia.sh micro > instancia.env
eval "$(cat instancia.env)"; echo "$I $IP"
```

To wait for A1 in the background (up to 24 h):

```bash
nohup bash oci-crear-instancia.sh a1 > instancia-a1.env 2> intentos-a1.log &
tail -f intentos-a1.log
```

### "Out of host capacity"

```
2026-10-11 15:52:04 attempt 1: "message": "Out of host capacity."
```

- It's not your fault: the region has no free ARM hosts for the free tier.
- There's no queue: whoever asks right when one frees up wins. Retrying every few minutes for hours or days usually works.
- Real case in Santiago: 12 failed A1 attempts; the Micro was created on the first try in ~2 minutes.

### Verify

```bash
oci compute instance get --instance-id "$I" --query 'data.{estado:"lifecycle-state",forma:shape}'
```

`oracle-cloud` `compute` `a1-flex` `e2-micro` `out-of-capacity`
