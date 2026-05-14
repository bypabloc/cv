# DNS y custom domains

> Como gestionar DNS records para custom domains de Cloudflare Pages,
> incluyendo el apex con CNAME flattening y el gotcha del subdomain
> con sufijo aleatorio.

[← Monorepo build](./04-monorepo-build-config.md) | [README](./README.md) | [Siguiente: Gotchas →](./06-gotchas.md)

## Decision: CNAME proxied para todos (incluido apex)

Cloudflare DNS soporta **CNAME flattening** nativo: podes poner un CNAME
en el apex de la zona (`the-full-stack.com`) y Cloudflare lo resuelve
transparentemente como A/AAAA al cliente. Esto NO funciona en otros DNS
providers (Route 53 lo emula con "Alias records").

```
the-full-stack.com         CNAME → generic-3ab.pages.dev   (proxied)
www.the-full-stack.com     CNAME → generic-3ab.pages.dev   (proxied)
hub.the-full-stack.com     CNAME → hub-9sd.pages.dev       (proxied)
...
```

Todos con `proxied: true` (proxy CF activo) — esto da:
- SSL termination en el edge
- Cache CDN
- WAF basico
- DDoS protection
- HTTP/3, Brotli, etc.

## ⚠️ GOTCHA: subdomain pages.dev con sufijo aleatorio

Cuando creas un proyecto Pages, Cloudflare le asigna un subdominio
`<name>.pages.dev`. PERO si `<name>.pages.dev` ya esta ocupado por otro
usuario de Cloudflare a nivel global, te asigna un **sufijo aleatorio**:

| Proyecto | URL esperada | URL real |
|----------|--------------|----------|
| `generic` | `generic.pages.dev` | `generic-3ab.pages.dev` |
| `hub` | `hub.pages.dev` | `hub-9sd.pages.dev` |
| `fintech` | `fintech.pages.dev` | `fintech-868.pages.dev` |

**Si apuntas el CNAME a `generic.pages.dev` (sin sufijo), va a un
proyecto que NO es tuyo** y CF responde HTTP 403 al request (mismo
host, distinto proyecto Pages).

### Como obtener el subdomain real

API: `GET /accounts/{id}/pages/projects/{name}` devuelve el field
`subdomain` con el valor real. Ejemplo:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/generic" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | jq -r '.result.subdomain'
# Output: generic-3ab.pages.dev
```

### Como crear el CNAME correcto

```python
project = client.get_project("generic")
target = project["subdomain"]  # "generic-3ab.pages.dev"
client.create_dns_record(
    zone_id,
    record_type="CNAME",
    name="the-full-stack.com",
    content=target,
    proxied=True,
)
```

NUNCA hardcodear `f"{project_name}.pages.dev"` — leer el subdomain real
del payload del proyecto.

## Endpoint DNS

```
POST /zones/{zone_id}/dns_records
GET  /zones/{zone_id}/dns_records?name=<host>&type=CNAME
PUT  /zones/{zone_id}/dns_records/{record_id}    # reemplaza el record
PATCH /zones/{zone_id}/dns_records/{record_id}   # update parcial
```

### Obtener zone_id

```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=the-full-stack.com" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | jq -r '.result[0].id'
```

### Payload basico CNAME

```json
{
  "type": "CNAME",
  "name": "hub.the-full-stack.com",
  "content": "hub-9sd.pages.dev",
  "proxied": true,
  "ttl": 1
}
```

- `ttl: 1` = "Auto" (CF gestiona TTL cuando proxied=true)
- `proxied: true` = trafico pasa por el edge de CF
- `proxied: false` = "DNS only" (cliente conecta directo al origen,
  pierdes CDN/WAF/SSL termination)

## Custom domain attach (en Pages)

Crear el CNAME NO basta. Hay que **attachar el custom domain al proyecto
Pages** explicitamente:

```bash
curl -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/generic/domains" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -d '{"name": "the-full-stack.com"}'
```

Cuando attachas el domain:
1. Pages emite un cert SSL (Google CA por default, ~5-10 min)
2. `status` del domain pasa por: `pending` → `active`
3. Una vez `active`, CF empieza a servir el contenido del proyecto

## Status de domain

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/generic/domains/the-full-stack.com" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

Campos relevantes:
- `status`: estado global (`pending` | `active` | `deactivated`)
- `verification_data.status`: `pending` → CNAME no detectado |
  `active` → CNAME OK
- `validation_data.status`: validacion HTTP del domain
  (`pending` → `active`)
- `certificate_authority`: `google` (default 2026)

Cuando los 3 estan `active`, el domain sirve via HTTPS.

## CNAME flattening (apex sin A record)

Cloudflare resuelve CNAMEs en el apex aplicando "CNAME flattening": al
query externo, devuelve las IPs A/AAAA detras del CNAME (las del edge
de Cloudflare cuando proxied).

```
dig the-full-stack.com
→ 172.67.182.237
→ 104.21.59.192

dig CNAME the-full-stack.com   # opcional, expone el CNAME real
→ generic-3ab.pages.dev.
```

Esto **solo funciona dentro de Cloudflare DNS**. Si tu zona estuviera
en Route 53 u otro provider, tendrias que usar A records con IPs de
Cloudflare (que cambian) — frágil.

## Propagacion DNS

- Cambios en records dentro de CF: **instant** a nivel de los NS
  autoritativos de CF
- Resolvers publicos (8.8.8.8, 1.1.1.1): 30s-5 min
- Resolvers ISP: 5-60 min dependiendo de TTL viejo
- Caches DNS locales (sistema, browser): hasta el TTL del query

Si tu maquina local cachea un NXDOMAIN viejo, los nuevos records pueden
tardar mas. Workaround: usar `--resolve` en curl o forzar query a
nameservers de CF:

```bash
curl --resolve hub.the-full-stack.com:443:104.21.59.192 https://hub.the-full-stack.com
dig @1.1.1.1 hub.the-full-stack.com
```

## DNS records preexistentes (Vercel, otros)

Si el dominio venia de otro hosting (Vercel, Netlify, etc.), antes de
crear los CNAMEs de Pages **borrar los A records viejos**:

```bash
# Listar todos
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# Buscar A records sospechosos (ej: 76.76.21.21 = Vercel)
# Borrar:
curl -X DELETE \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/{record_id}" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

CF rechaza crear un CNAME si existe un A record con el mismo nombre
(conflict por RFC).
