**04**

# DNS

[← Index](README.md)

---

### The record

| Type | Name | Content | Proxy | TTL |
| :-- | :-- | :-- | :-- | :-- |
| `A` | `ntfy` | `203.0.113.10` | **No proxy** ("DNS only" in Cloudflare) | 300 |

Any DNS provider works; all you need is the `A` record pointing to the public IP.

### Why no proxy

- Proxies like Cloudflare's cut long idle HTTP connections; the phone app keeps one open at all times.
- Caddy validates the domain with Let's Encrypt (HTTP-01) directly against the server.
- With a proxy, ntfy would see the proxy's IP instead of the client's.

### Cloudflare via API

A token with the **Zone → DNS → Edit** permission on the zone. Keep it in a variable, never in a versioned file:

```bash
read -rsp 'Cloudflare token: ' CF_API_TOKEN; echo
H=(-H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json")
DOMINIO=your-domain.com; HOST=ntfy.your-domain.com; IP=203.0.113.10

# Verify the token
curl -s "${H[@]}" https://api.cloudflare.com/client/v4/user/tokens/verify | jq -r '.result.status'   # active

# Zone ID
Z=$(curl -s "${H[@]}" "https://api.cloudflare.com/client/v4/zones?name=$DOMINIO" | jq -r '.result[0].id')

# Create or update (idempotent)
BODY=$(jq -n --arg n "$HOST" --arg ip "$IP" '{type:"A", name:$n, content:$ip, ttl:300, proxied:false, comment:"ntfy"}')
EX=$(curl -s "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records?name=$HOST" | jq -r '.result[0].id // empty')
if [ -n "$EX" ]; then
  curl -s -X PUT "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records/$EX" -d "$BODY"
else
  curl -s -X POST "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records" -d "$BODY"
fi | jq -c '{success, r: .result | {name, content, proxied}}'
```

Expected response:

```json
{"success":true,"r":{"name":"ntfy.your-domain.com","content":"203.0.113.10","proxied":false}}
```

### Check

```bash
dig +short ntfy.your-domain.com     # 203.0.113.10
```

### Delete

```bash
curl -s -X DELETE "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records/$EX"
```

`dns` `cloudflare` `api`
