**05**

# Red: compartment, VCN, subred y firewall

[← Índice](README.md)

---

### Qué se crea

| Recurso | Para qué |
| :-- | :-- |
| Compartment | Aísla el proyecto del resto de la cuenta; borrarlo limpia todo |
| VCN `10.0.0.0/16` | Red privada virtual |
| Internet Gateway | Salida y entrada a internet |
| Ruta `0.0.0.0/0 → gateway` | En la tabla de rutas por defecto de la VCN |
| Security List | Entrada solo por 22 (SSH), 80 (HTTP) y 443 (HTTPS) + ICMP de fragmentación |
| Subred pública `10.0.0.0/24` | Donde vive la VM, con IP pública |

### Script: `oci-crear-red.sh`

Corre en tu PC con la CLI configurada ([capítulo 04](04-api-key-y-cli.md)). Imprime los OCID listos para `eval`.

```bash
#!/usr/bin/env bash
# Crea compartment, VCN, internet gateway, ruta, security list (22/80/443) y subred pública.
# Uso: eval "$(bash oci-crear-red.sh mi-vm)"
set -euo pipefail
NAME="${1:-mi-vm}"
LABEL="${NAME//-/}"                       # dns-label: solo letras y números
T=$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)

# 1. Compartment
C=$(oci iam compartment create --compartment-id "$T" --name "$NAME" \
  --description "Proyecto $NAME" --wait-for-state ACTIVE --query 'data.id' --raw-output)
sleep 20                                  # el compartment tarda en propagarse

# 2. VCN
V=$(oci network vcn create -c "$C" --cidr-blocks '["10.0.0.0/16"]' --display-name "$NAME-vcn" \
  --dns-label "${LABEL}vcn" --wait-for-state AVAILABLE --query 'data.id' --raw-output)

# 3. Internet Gateway
IG=$(oci network internet-gateway create -c "$C" --vcn-id "$V" --is-enabled true \
  --display-name "$NAME-igw" --wait-for-state AVAILABLE --query 'data.id' --raw-output)

# 4. Ruta por defecto hacia el gateway
RT=$(oci network vcn get --vcn-id "$V" --query 'data."default-route-table-id"' --raw-output)
oci network route-table update --rt-id "$RT" --force --wait-for-state AVAILABLE \
  --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IG\"}]" >/dev/null

# 5. Security List: 22, 80, 443 y ICMP 3/4
SL=$(oci network vcn get --vcn-id "$V" --query 'data."default-security-list-id"' --raw-output)
ING='[
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},
 {"protocol":"1","source":"0.0.0.0/0","icmpOptions":{"type":3,"code":4}}]'
oci network security-list update --security-list-id "$SL" --force --wait-for-state AVAILABLE \
  --ingress-security-rules "$ING" \
  --egress-security-rules '[{"protocol":"all","destination":"0.0.0.0/0"}]' >/dev/null

# 6. Subred pública
SN=$(oci network subnet create -c "$C" --vcn-id "$V" --cidr-block 10.0.0.0/24 \
  --display-name "$NAME-subnet" --dns-label "${LABEL}sub" --wait-for-state AVAILABLE \
  --query 'data.id' --raw-output)

printf 'export C=%s\nexport V=%s\nexport IG=%s\nexport RT=%s\nexport SL=%s\nexport SN=%s\n' \
  "$C" "$V" "$IG" "$RT" "$SL" "$SN"
```

Uso:

```bash
eval "$(bash oci-crear-red.sh mi-vm)"
echo "$C $SN"     # guárdalos: los usan los capítulos siguientes
```

Tarda ~2 minutos.

### Notas

- `--force` en los `update` evita la confirmación interactiva; esos `update` **reemplazan** la lista completa de reglas.
- Protocolo `6` = TCP, `1` = ICMP. La regla ICMP tipo 3 código 4 permite *Path MTU Discovery*.
- `--wait-for-state` hace que cada paso espere a que el recurso exista.
- Para abrir otro puerto, agrega una regla al JSON `ING` y vuelve a ejecutar el `security-list update`.

### Las dos capas de firewall

En Oracle hay **dos** firewalls y ambos deben permitir el puerto:

1. **Security List** de la VCN (este capítulo).
2. **`iptables` dentro de la VM**: la imagen Ubuntu de Oracle trae un `REJECT` para todo salvo SSH. Se abre en el [capítulo 07](07-primer-arranque.md).

`oracle-cloud` `vcn` `security-list` `firewall` `oci-cli`
