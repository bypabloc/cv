**04**

# DNS

[← Índice](README.md)

---

### El registro

| Tipo | Nombre | Contenido | Proxy | TTL |
| :-- | :-- | :-- | :-- | :-- |
| `A` | `ntfy` | `203.0.113.10` | **Sin proxy** ("DNS only" en Cloudflare) | 300 |

Cualquier proveedor de DNS sirve; solo hace falta el registro `A` a la IP pública.

### Por qué sin proxy

- Los proxies como el de Cloudflare cortan conexiones HTTP inactivas largas; la app del celular mantiene una abierta todo el tiempo.
- Caddy valida el dominio con Let's Encrypt (HTTP-01) directo contra el servidor.
- Con proxy, ntfy vería la IP del proxy y no la del cliente.

### Cloudflare por API

Token con permiso **Zone → DNS → Edit** sobre la zona. Guárdalo en una variable, nunca en un archivo versionado:

```bash
read -rsp 'Token de Cloudflare: ' CF_API_TOKEN; echo
H=(-H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json")
DOMINIO=tu-dominio.com; HOST=ntfy.tu-dominio.com; IP=203.0.113.10

# Verificar el token
curl -s "${H[@]}" https://api.cloudflare.com/client/v4/user/tokens/verify | jq -r '.result.status'   # active

# ID de la zona
Z=$(curl -s "${H[@]}" "https://api.cloudflare.com/client/v4/zones?name=$DOMINIO" | jq -r '.result[0].id')

# Crear o actualizar (idempotente)
BODY=$(jq -n --arg n "$HOST" --arg ip "$IP" '{type:"A", name:$n, content:$ip, ttl:300, proxied:false, comment:"ntfy"}')
EX=$(curl -s "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records?name=$HOST" | jq -r '.result[0].id // empty')
if [ -n "$EX" ]; then
  curl -s -X PUT "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records/$EX" -d "$BODY"
else
  curl -s -X POST "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records" -d "$BODY"
fi | jq -c '{success, r: .result | {name, content, proxied}}'
```

Respuesta esperada:

```json
{"success":true,"r":{"name":"ntfy.tu-dominio.com","content":"203.0.113.10","proxied":false}}
```

### Comprobar

```bash
dig +short ntfy.tu-dominio.com     # 203.0.113.10
```

### Borrar

```bash
curl -s -X DELETE "${H[@]}" "https://api.cloudflare.com/client/v4/zones/$Z/dns_records/$EX"
```

`dns` `cloudflare` `api`
