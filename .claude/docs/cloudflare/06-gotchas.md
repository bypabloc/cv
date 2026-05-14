# Gotchas conocidos

> Errores reales encontrados durante el setup de Cloudflare Pages para
> este portfolio + sus causas raiz y fixes. Consultar antes de
> diagnosticar.

[← DNS](./05-dns-and-custom-domains.md) | [README](./README.md) | [Siguiente: Script idempotente →](./07-script-idempotente.md)

## 1. `Cannot find cwd: /opt/buildhome/repo/apps/<app>`

**Sintoma**: build falla inmediato, antes de ejecutar el build command.

**Causa**: Tenes `root_dir: "apps/<app>"` configurado. El build system
v2 de Pages intenta `cd apps/<app>` antes del build y falla por un bug
con monorepos pnpm.

**Fix**: Setear `root_dir: ""` y `destination_dir: "apps/<app>/dist"`.
Build command corre desde la raiz del repo, donde pnpm puede ver
`pnpm-workspace.yaml`.

Detalle: [04-monorepo-build-config.md](./04-monorepo-build-config.md).

## 2. `No package.json found in /opt/buildhome/repo`

**Sintoma**: build logs muestran `[ERR_PNPM_NO_PKG_MANIFEST]`.

**Causa**: Cloudflare clono un commit antiguo de la branch que no
contenia `package.json` en la raiz. Pasa cuando creas el proyecto y la
branch `main` tenia commits viejos antes de la migracion a monorepo.

**Fix**: Hacer un nuevo commit en `main` (cualquier cosa que tenga
package.json) y re-trigger el deploy. CF auto-detecta el HEAD nuevo y
re-buildea.

```bash
git checkout main
git commit --allow-empty -m "chore: trigger CF rebuild"
git push origin main
```

## 3. HTTP 304 al intentar trigger deploy

**Sintoma**:
```
POST /pages/projects/<name>/deployments → 304 Not Modified
```

**Causa**: Ya existe un deploy del commit actual de `production_branch`.
CF no re-buildea el mismo commit dos veces.

**Fix**: Un commit nuevo (real o `--allow-empty`) en `main` para forzar
un commit_hash distinto.

## 4. HTTP 403 al acceder al custom domain

**Sintoma**: Custom domain (e.g. `the-full-stack.com`) responde 403,
pero el `.pages.dev` URL del deploy responde 200.

**Causas posibles** (en orden de probabilidad):

### 4a. CNAME apunta a `<name>.pages.dev` (sin sufijo) en vez del subdomain real

Si `<name>.pages.dev` esta tomado a nivel global por otro usuario de CF,
tu proyecto recibe un subdomain con sufijo (`generic-3ab.pages.dev`).
Si el CNAME apunta a `generic.pages.dev`, el request va al proyecto del
otro user → 403.

**Fix**: Obtener `subdomain` del payload del proyecto via API y usarlo
como target del CNAME. Detalle en
[05-dns-and-custom-domains.md](./05-dns-and-custom-domains.md).

### 4b. Cert SSL aun emitiendose

Status del domain en `pending` por 1-10 min mientras CF emite el cert
Universal SSL. Espera.

**Verificacion**:
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/<name>/domains/<domain>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq '.result.status'
```

### 4c. Conflicto entre A record viejo y CNAME nuevo

Si el dominio venia de Vercel/Netlify/otro, puede haber A records
residuales con IPs que no son de CF. **Eliminarlos** antes de crear
los CNAMEs (CF rechaza crear CNAME si existe A con mismo nombre, pero
el delete puede no haberse hecho).

## 5. HTTP 522 (Connection timed out)

**Sintoma**: Cloudflare devuelve 522 al cliente.

**Causa**: El edge de CF resuelve el DNS y reachea el origen (`.pages.dev`)
pero la conexion al origen falla o timeoutea. Tipicamente: el CNAME se
actualizo recien y la cache interna de CF aun apunta al viejo.

**Fix**: Esperar 1-5 min para que la cache interna del edge se sincronice.
Si persiste: toggle `proxied=false` → `proxied=true` en el CNAME para
forzar re-process.

```bash
# Force re-process
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -d '{"proxied":false}'
sleep 3
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -d '{"proxied":true}'
```

## 6. HTTP 000 desde WSL2 / DNS cache local

**Sintoma**: `curl https://hub.the-full-stack.com` devuelve `000` (TCP
fail). Pero desde `dig +short`, los nameservers de CF SI responden.

**Causa**: Cache DNS del resolver de WSL2 / systemd-resolved tiene
cacheado el NXDOMAIN viejo (cuando el CNAME no existia aun).

**Fix**:
```bash
# Bypass cache local con --resolve
curl --resolve hub.the-full-stack.com:443:104.21.59.192 \
  https://hub.the-full-stack.com

# O usar resolver externo
dig @1.1.1.1 hub.the-full-stack.com
dig @8.8.8.8 hub.the-full-stack.com

# O flush cache (WSL2 / Linux con systemd-resolved)
sudo systemd-resolve --flush-caches  # legacy
sudo resolvectl flush-caches         # current
```

En navegador: incognito o `chrome://net-internals/#dns` → "Clear host cache".

## 7. `env_vars` se setean como null en lugar del valor

**Sintoma**: PATCH/POST con `environment_variables` retorna 200, pero
`GET` del proyecto muestra `env_vars: null`.

**Causa**: Shape incorrecto. La API espera **`env_vars`** (no
`environment_variables`) con valores en formato
**`{"type": "plain_text", "value": "..."}`** (no string plano).

**Fix**: usar el shape correcto:

```json
{
  "deployment_configs": {
    "production": {
      "env_vars": {
        "NODE_VERSION": {"type": "plain_text", "value": "24"}
      }
    }
  }
}
```

Para secrets usar `"type": "secret_text"` en vez de `"plain_text"`.

## 8. Subdomain `pages.dev` resuelve a OTRO sitio

**Sintoma**: `curl https://generic.pages.dev` devuelve HTML de algun
proyecto random (en mi caso: una landing en chino sobre CAD architecture
asiatico).

**Causa**: Los subdomains `<name>.pages.dev` son **globales a nivel de
toda Cloudflare**. Otros usuarios pudieron registrar `generic`, `hub`,
etc. antes que tu. Tu proyecto recibe el sufijo (`generic-3ab.pages.dev`).

**Fix**: SIEMPRE usar el subdomain real del payload del proyecto
(field `subdomain`). Nunca asumir `<name>.pages.dev`.

## 9. Wrangler no puede crear git-connected projects

**Sintoma**: `wrangler pages project create` no acepta source de git,
o el proyecto creado no tiene webhook a GitHub.

**Causa**: Wrangler v4 NO soporta git-connected projects (issue
[cloudflare/workers-sdk#10972](https://github.com/cloudflare/workers-sdk/issues/10972),
abierto desde octubre 2025).

**Fix**: usar REST API directamente para crear el proyecto. Wrangler
sirve solo para direct upload (`wrangler pages deploy ./dist`).

Detalle: [03-pages-api-setup.md](./03-pages-api-setup.md).

## 10. 1 build concurrent en free tier

**Sintoma**: Trigger 6 deploys, solo 1 buildea, los otros 5 quedan
`queued:active` por minutos.

**Causa**: Free tier hace 1 concurrent build por account (no por
proyecto). Es by-design.

**Fix**: Esperar (~15-25 min para 6 apps Astro chicas) o pasar a Pages
Pro ($5/proyecto/mes para 5 concurrent).

## 11. Build cache obsoleto

**Sintoma**: Build falla con error de "X file not found" o "module
resolution failed" que no tiene sentido contra el repo actual.

**Causa**: Pages cachea `node_modules` entre builds. A veces se
corrompe.

**Fix**: Settings del proyecto → Build & deployments → "Clear cache".
Re-trigger deploy.

## 12. `_headers` / `_redirects` no se aplican

**Sintoma**: Headers de seguridad o redirects definidos en
`apps/<app>/public/_headers` no se ven en la respuesta HTTP.

**Causas posibles**:

- El archivo no esta en `public/` (debe ser servido como asset estatico)
- Sintaxis invalida (CF parsea y silenciosamente skipea reglas con error)
- El archivo no se copio al `dist/` (verificar en build logs)

**Fix**: Verificar
[sintaxis oficial de _headers](https://developers.cloudflare.com/pages/configuration/headers/).
Test local: en el `dist/` del build, debe existir un archivo `_headers`
identico al de `public/`.
