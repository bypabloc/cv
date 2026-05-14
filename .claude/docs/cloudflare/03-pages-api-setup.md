# Pages projects via REST API

> Como crear, actualizar y borrar proyectos Pages git-connected
> usando la REST API de Cloudflare. Wrangler NO sirve para este caso.

[← API token](./02-api-token.md) | [README](./README.md) | [Siguiente: monorepo build →](./04-monorepo-build-config.md)

## Wrangler vs REST API (decision)

| Capacidad | Wrangler CLI | REST API |
|-----------|--------------|----------|
| Crear proyecto direct upload | ✓ | ✓ |
| Crear proyecto git-connected | ❌ (issue cloudflare/workers-sdk#10972) | ✓ |
| Subir build manual | ✓ (`wrangler pages deploy`) | ✓ |
| Patch build config | ✓ parcial | ✓ completo |
| Listar deployments | ✓ | ✓ |
| Configurar env vars | ✓ | ✓ (formato distinto, ver abajo) |
| Attach custom domain | ❌ | ✓ |

**Conclusion**: para git-connected con 6 proyectos, REST API. Wrangler
sirve solo si vas a buildear localmente y subir el dist/.

## Endpoint: crear proyecto

```
POST https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects
Authorization: Bearer {api_token}
Content-Type: application/json
```

## Payload minimo (git-connected)

```json
{
  "name": "generic",
  "production_branch": "main",
  "source": {
    "type": "github",
    "config": {
      "owner": "bypabloc",
      "repo_name": "cv",
      "production_branch": "main",
      "deployments_enabled": true,
      "pr_comments_enabled": false,
      "production_deployments_enabled": true,
      "preview_deployment_setting": "none"
    }
  },
  "build_config": {
    "build_command": "pnpm install --frozen-lockfile && pnpm --filter @portfolio/generic... build",
    "destination_dir": "apps/generic/dist",
    "root_dir": ""
  },
  "deployment_configs": {
    "production": {
      "env_vars": {
        "NODE_VERSION": {"type": "plain_text", "value": "24"},
        "PNPM_VERSION": {"type": "plain_text", "value": "11.0.9"}
      }
    },
    "preview": {
      "env_vars": {
        "NODE_VERSION": {"type": "plain_text", "value": "24"},
        "PNPM_VERSION": {"type": "plain_text", "value": "11.0.9"}
      }
    }
  }
}
```

### Gotcha: `env_vars` shape

El formato correcto en 2026 es **`env_vars`** (no `environment_variables`)
y cada valor es **`{"type": "plain_text", "value": "..."}`** (no string
plano).

Tipos validos de env var:
- `plain_text` — texto normal, visible en logs
- `secret_text` — secret, oculto en logs y UI

Si pasas el shape viejo (`{"value": "..."}`) la API responde 200 pero
silenciosamente NO setea las env vars (vuelven `null`).

### Gotcha: `preview_deployment_setting`

| Valor | Comportamiento |
|-------|----------------|
| `all` | Deploy preview por cada push a CUALQUIER branch (consume builds) |
| `custom` | Deploy preview por branches que matcheen `preview_branch_includes` |
| `none` | Solo deploy en production_branch — no previews por PR |

Para portfolio con bajo trafico de PRs: `none` para ahorrar builds.

## Endpoints utiles

| Operacion | Method + path |
|-----------|---------------|
| Listar proyectos | `GET /accounts/{id}/pages/projects` |
| Obtener proyecto | `GET /accounts/{id}/pages/projects/{name}` |
| Crear proyecto | `POST /accounts/{id}/pages/projects` |
| Actualizar proyecto | `PATCH /accounts/{id}/pages/projects/{name}` |
| Borrar proyecto | `DELETE /accounts/{id}/pages/projects/{name}` |
| Listar deployments | `GET /accounts/{id}/pages/projects/{name}/deployments` |
| Crear deployment (trigger build) | `POST /accounts/{id}/pages/projects/{name}/deployments` |
| Obtener logs de deployment | `GET /accounts/{id}/pages/projects/{name}/deployments/{deploy_id}/history/logs` |
| Listar custom domains | `GET /accounts/{id}/pages/projects/{name}/domains` |
| Attach custom domain | `POST /accounts/{id}/pages/projects/{name}/domains` body `{"name": "domain"}` |
| Obtener status de domain | `GET /accounts/{id}/pages/projects/{name}/domains/{domain}` |

## Trigger deploy manual

```bash
curl -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/generic/deployments" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

**Response 304 Not Modified**: significa que ya hay un deploy del commit
actual de `production_branch`. CF no re-buildea el mismo commit.
Workaround: hacer un commit no-op + push (`git commit --allow-empty`).

## Status de deploy

Cada deployment tiene un `latest_stage` con `name` y `status`:

| Stage name | Significado |
|-----------|-------------|
| `queued` | En cola esperando build slot |
| `initialize` | Setup del build env |
| `clone_repo` | Clone del repo |
| `build` | Ejecutando `build_command` |
| `deploy` | Subiendo assets al edge |

Status posibles: `active` (en curso), `success`, `failure`, `cancelled`.

El deploy esta **realmente listo** cuando `stage.name == "deploy"` y
`stage.status == "success"`.

## Bug del free tier: 1 build concurrent

Free tier corre **1 build a la vez por account** (no por proyecto). Si
disparas 6 deploys, los otros 5 quedan `queued:active`. Plan Pro ($5)
sube a 5 concurrent.

Tiempo total estimado para 6 apps Astro chicas: ~15-25 min secuencial.

## Idempotencia

`POST /pages/projects` con un `name` que ya existe devuelve **409
Conflict**. Antes de crear:

```python
existing = client.get_project(name)
if existing is None:
    client.create_project(payload)
else:
    client.patch_project(name, patch_payload)
```

PATCH puede actualizar `build_config` y `deployment_configs` sin recrear
el proyecto (mantiene custom domains, deployments history, etc.).

## Limites

- 5 proyectos por account default (se sube solicitando a Cloudflare,
  granted en ~24h)
- 100 custom domains por proyecto
- 500 builds/mes por proyecto (free tier)
- 100MB max para un solo archivo, 20K archivos max por deployment
- 25MB max para `_redirects` y `_headers` files
