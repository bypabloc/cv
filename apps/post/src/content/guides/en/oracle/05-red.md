**05**

# Networking: compartment, VCN, subnet, and firewall

[← Index](README.md)

---

### What gets created

| Resource | Purpose |
| :-- | :-- |
| Compartment | Isolates the project from the rest of the account; deleting it cleans up everything |
| VCN `10.0.0.0/16` | Virtual private network |
| Internet Gateway | Inbound and outbound internet access |
| Route `0.0.0.0/0 → gateway` | In the VCN's default route table |
| Security List | Inbound only on 22 (SSH), 80 (HTTP), and 443 (HTTPS) + fragmentation ICMP |
| Public subnet `10.0.0.0/24` | Where the VM lives, with a public IP |

### Script: `oci-crear-red.sh`

Runs on your PC with the CLI configured ([chapter 04](04-api-key-y-cli.md)). Prints the OCIDs ready for `eval`.

```bash
#!/usr/bin/env bash
# Creates compartment, VCN, internet gateway, route, security list (22/80/443), and public subnet.
# Usage: eval "$(bash oci-crear-red.sh my-vm)"
set -euo pipefail
NAME="${1:-my-vm}"
LABEL="${NAME//-/}"                       # dns-label: letters and numbers only
T=$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)

# 1. Compartment
C=$(oci iam compartment create --compartment-id "$T" --name "$NAME" \
  --description "Project $NAME" --wait-for-state ACTIVE --query 'data.id' --raw-output)
sleep 20                                  # the compartment takes a while to propagate

# 2. VCN
V=$(oci network vcn create -c "$C" --cidr-blocks '["10.0.0.0/16"]' --display-name "$NAME-vcn" \
  --dns-label "${LABEL}vcn" --wait-for-state AVAILABLE --query 'data.id' --raw-output)

# 3. Internet Gateway
IG=$(oci network internet-gateway create -c "$C" --vcn-id "$V" --is-enabled true \
  --display-name "$NAME-igw" --wait-for-state AVAILABLE --query 'data.id' --raw-output)

# 4. Default route to the gateway
RT=$(oci network vcn get --vcn-id "$V" --query 'data."default-route-table-id"' --raw-output)
oci network route-table update --rt-id "$RT" --force --wait-for-state AVAILABLE \
  --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IG\"}]" >/dev/null

# 5. Security List: 22, 80, 443, and ICMP 3/4
SL=$(oci network vcn get --vcn-id "$V" --query 'data."default-security-list-id"' --raw-output)
ING='[
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
 {"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},
 {"protocol":"1","source":"0.0.0.0/0","icmpOptions":{"type":3,"code":4}}]'
oci network security-list update --security-list-id "$SL" --force --wait-for-state AVAILABLE \
  --ingress-security-rules "$ING" \
  --egress-security-rules '[{"protocol":"all","destination":"0.0.0.0/0"}]' >/dev/null

# 6. Public subnet
SN=$(oci network subnet create -c "$C" --vcn-id "$V" --cidr-block 10.0.0.0/24 \
  --display-name "$NAME-subnet" --dns-label "${LABEL}sub" --wait-for-state AVAILABLE \
  --query 'data.id' --raw-output)

printf 'export C=%s\nexport V=%s\nexport IG=%s\nexport RT=%s\nexport SL=%s\nexport SN=%s\n' \
  "$C" "$V" "$IG" "$RT" "$SL" "$SN"
```

Usage:

```bash
eval "$(bash oci-crear-red.sh my-vm)"
echo "$C $SN"     # save them: the following chapters use them
```

It takes ~2 minutes.

### Notes

- `--force` on the `update` commands skips the interactive confirmation; those `update` commands **replace** the entire rule list.
- Protocol `6` = TCP, `1` = ICMP. The ICMP type 3 code 4 rule enables *Path MTU Discovery*.
- `--wait-for-state` makes each step wait until the resource exists.
- To open another port, add a rule to the `ING` JSON and rerun the `security-list update`.

### The two firewall layers

Oracle has **two** firewalls, and both must allow the port:

1. The VCN's **Security List** (this chapter).
2. **`iptables` inside the VM**: Oracle's Ubuntu image ships with a `REJECT` for all new inbound traffic except SSH. It's opened in [chapter 07](07-primer-arranque.md).

`oracle-cloud` `vcn` `security-list` `firewall` `oci-cli`
