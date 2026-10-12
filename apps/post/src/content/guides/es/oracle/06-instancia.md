**06**

# Crear la instancia

[← Índice](README.md)

---

### A1 o Micro

| | `VM.Standard.A1.Flex` (ARM) | `VM.Standard.E2.1.Micro` (AMD) |
| :-- | :-- | :-- |
| CPU / RAM gratis | Hasta 2 OCPU / 12 GB | 1/8 OCPU / 1 GB |
| Disponibilidad | **Suele dar "Out of host capacity"** | Normalmente disponible |
| Regla de reclamo | CPU, red **y memoria** | Solo CPU y red |
| Evitar el reclamo | Instancia chica: la RAM usada ya supera el 20 % | Necesita un keepalive de CPU |
| Recomendación | Primera opción | Plan B cuando A1 no tiene capacidad |

**Truco para A1:** créala con **1 OCPU y 1 GB**. Ubuntu más un servicio liviano usan ~400 MB, más del 20 % de la RAM: nunca se considera inactiva y no hace falta generar carga artificial. Ver [capítulo 08](08-reclamo-por-inactividad.md).

### 1. Clave SSH

```bash
ssh-keygen -t ed25519 -N "" -C "oci-mi-vm" -f ~/.ssh/oci_mi_vm
```

### 2. Script: `oci-crear-instancia.sh`

Requiere `C` y `SN` exportados ([capítulo 05](05-red.md)).

```bash
#!/usr/bin/env bash
# Crea la instancia Always Free con Ubuntu 24.04.
# Uso: eval "$(bash oci-crear-instancia.sh a1)"     → A1 1 OCPU / 1 GB, reintenta cada 2 min
#      eval "$(bash oci-crear-instancia.sh micro)"  → VM.Standard.E2.1.Micro
set -uo pipefail
KIND="${1:-a1}"
NAME="${NAME:-mi-vm}"
SSH_PUB="${SSH_PUB:-$HOME/.ssh/oci_mi_vm.pub}"
MAX_TRIES="${MAX_TRIES:-720}"             # 720 × 2 min = 24 h
: "${C:?exporta C}" "${SN:?exporta SN}"

AD=$(oci iam availability-domain list -c "$C" --query 'data[0].name' --raw-output)
if [ "$KIND" = "a1" ]; then
  SHAPE=VM.Standard.A1.Flex; CFG=(--shape-config '{"ocpus":1,"memoryInGBs":1}')
else
  SHAPE=VM.Standard.E2.1.Micro; CFG=(); MAX_TRIES=1
fi

# Imagen Ubuntu 24.04 más reciente compatible con la forma (aarch64 para A1, x86_64 para Micro)
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
  echo "$(date '+%F %T') intento $i: $(echo "$OUT" | grep -o '"message": "[^"]*"' | head -1)" >&2
  [ "$i" -lt "$MAX_TRIES" ] && sleep 120
done
exit 1
```

### 3. Uso

Primero intenta A1 un rato; si no hay capacidad, Micro:

```bash
MAX_TRIES=6 bash oci-crear-instancia.sh a1 > instancia.env || bash oci-crear-instancia.sh micro > instancia.env
eval "$(cat instancia.env)"; echo "$I $IP"
```

Para esperar A1 en segundo plano (hasta 24 h):

```bash
nohup bash oci-crear-instancia.sh a1 > instancia-a1.env 2> intentos-a1.log &
tail -f intentos-a1.log
```

### "Out of host capacity"

```
2026-10-11 15:52:04 intento 1: "message": "Out of host capacity."
```

- No es un error tuyo: la región no tiene hosts ARM libres para la capa gratis.
- No hay cola: el que pide justo cuando se libera, gana. Reintentar cada pocos minutos durante horas o días suele funcionar.
- Caso real en Santiago: 12 intentos de A1 fallidos; la Micro se creó al primer intento en ~2 minutos.

### Comprobar

```bash
oci compute instance get --instance-id "$I" --query 'data.{estado:"lifecycle-state",forma:shape}'
```

`oracle-cloud` `compute` `a1-flex` `e2-micro` `out-of-capacity`
