# Cloudflare Transform Rules (zona `the-full-stack.com`)

> Reglas de transformacion HTTP activas en la zona DNS principal del
> portfolio. Cubren los 6 subdominios Pages (`{niche}.portfolio.*`) +
> el apex.

## Reglas activas

### TR-1 — Serve Markdown to agents requesting `text/markdown`

**Tipo**: URL Rewrite
**Estado**: PENDING (debe activarse manualmente en el dashboard tras
mergear el plan ai-audit-level-3-4)
**Cubre**: AC-6 del plan

#### Expression

```text
(any(http.request.headers["accept"][*] contains "text/markdown"))
and (not http.request.uri.path matches "\\.(json|xml|txt|png|jpg|jpeg|gif|svg|ico|css|js|woff2?|webp|avif|map)$")
and (not starts_with(http.request.uri.path, "/.well-known/"))
and (not starts_with(http.request.uri.path, "/mcp"))
```

#### Action

URL rewrite dynamic:

```text
concat(
  http.request.uri.path,
  if(ends_with(http.request.uri.path, "/"), "index.md", "/index.md")
)
```

#### Por que

- Astro builda con directory style: `/about/` -> `dist/about/index.html`.
- El postbuild de `@portfolio/markdown-export` (Fase 1B) genera
  `dist/about/index.md` al lado del HTML.
- La rule reescribe `/about` (o `/about/`) -> `/about/index.md` SOLO
  cuando el cliente envia `Accept: text/markdown`.
- Excluye static assets (sin .md gemelo), `.well-known/` (JSONs propios)
  y `/mcp` (Pages Function de MCP server).

#### Activar (manual desde dashboard)

1. Cloudflare → the-full-stack.com → Rules → Transform Rules → Rewrite URL
2. Create rule
3. Name: `Serve Markdown to agents`
4. When incoming requests match: Custom filter expression con la
   expresion de arriba
5. URI Path: Rewrite to → Dynamic, con la expresion de la action
6. Deploy
7. Verificar:

```bash
curl -sI -H 'Accept: text/markdown' https://the-full-stack.com/about
# Debe responder content-type: text/markdown; charset=UTF-8
# Sin el header Accept, devuelve HTML normalmente
```

#### Activar (alternativa via API — referencia)

```bash
ZONE_ID=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=the-full-stack.com" \
  | jq -r '.result[0].id')

curl -X PUT \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/rulesets/phases/http_request_transform/entrypoint" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @cloudflare/payloads/tr-1-markdown.json
```

(`cloudflare/payloads/tr-1-markdown.json` no esta versionado todavia
porque devtools no automatiza Transform Rules. Si en el futuro lo hace,
extender `devtools/cloudflare_setup/` para incluirlas.)

## Limites del Free tier

- 10 Transform Rules por zona.
- Cuenta hoy: 1/10 (TR-1).

## Mantenimiento

Cuando se agreguen nuevas Functions en `/mcp/*` u otros paths que NO
deben caer en el rewrite, agregar el path al `not starts_with` de la
expresion. Asi se evita que un POST `/mcp` con `Accept: text/markdown`
incorrectamente sea reescrito.
