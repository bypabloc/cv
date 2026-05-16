# 06 - Migracion del backend serverless al estandar

> [<- 05-wildcards-and-certs](./05-wildcards-and-certs.md) | [07-anti-patterns ->](./07-anti-patterns.md)

## Estado actual (2026-05-15)

El backend serverless del portfolio usa los hostnames raw de API Gateway:

```text
prod   https://332ivhahf2.execute-api.us-east-1.amazonaws.com/prod
dev    https://ssnj6odx7l.execute-api.us-east-1.amazonaws.com/dev
```

Frontend lo consume via `PUBLIC_API_ENDPOINT` en `docker/env/.{dev,prod}`.

## Estado objetivo

Aplicando el estandar (product = `portfolio`, component = `api`):

```text
prod    https://api.portfolio.the-full-stack.com
stage   https://api.portfolio.stage.the-full-stack.com
dev     https://api.portfolio.dev.the-full-stack.com
```

> Nota: el stack SAM `stage` (`portfolio-backend-stage`) se despliega como
> parte de esta migracion — el `template.yaml` agrega `stage` a los
> `AllowedValues` del parametro `Stage` y `samconfig.toml` un bloque
> `[stage.*]`. Cada env tiene su REST API independiente.

## Plan de migracion

### Paso 1 — Cert ACM en us-east-1

API Gateway REST API requiere cert ACM en la misma region (us-east-1).
Un solo cert con 3 SANs cubre los 3 envs:

```bash
aws acm request-certificate \
  --domain-name api.portfolio.the-full-stack.com \
  --subject-alternative-names \
      api.portfolio.dev.the-full-stack.com \
      api.portfolio.stage.the-full-stack.com \
  --validation-method DNS \
  --region us-east-1 \
  --output json
```

Anotar el `CertificateArn` retornado.

### Paso 2 — Validacion via DNS en Cloudflare

ACM devuelve 2 records CNAME (1 por hostname) que hay que crear en
Cloudflare como **DNS only** (no proxied):

```bash
aws acm describe-certificate \
  --certificate-arn <ARN> \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord]' \
  --output json
```

Crear en Cloudflare los 2 CNAMEs con `proxied: false` y TTL 300.

Esperar el `Status: ISSUED` del cert (~5-30min).

### Paso 3 — Custom Domain Names en API Gateway

Crear 3 entries (prod + stage + dev). El bloque de abajo muestra prod+dev;
para stage repetir con `api.portfolio.stage.the-full-stack.com`:

```bash
# prod
aws apigateway create-domain-name \
  --domain-name api.portfolio.the-full-stack.com \
  --certificate-arn <ARN> \
  --endpoint-configuration types=REGIONAL \
  --security-policy TLS_1_2 \
  --region us-east-1

# dev
aws apigateway create-domain-name \
  --domain-name api.portfolio.dev.the-full-stack.com \
  --certificate-arn <ARN> \
  --endpoint-configuration types=REGIONAL \
  --security-policy TLS_1_2 \
  --region us-east-1
```

Cada uno devuelve un `regionalDomainName` (algo como
`d-abc123.execute-api.us-east-1.amazonaws.com`).

### Paso 4 — Base Path Mapping

Mapear cada custom domain al stage correspondiente:

```bash
# prod -> stage prod del REST API 332ivhahf2
aws apigateway create-base-path-mapping \
  --domain-name api.portfolio.the-full-stack.com \
  --rest-api-id 332ivhahf2 \
  --stage prod \
  --region us-east-1

# dev -> stage dev del REST API ssnj6odx7l
aws apigateway create-base-path-mapping \
  --domain-name api.portfolio.dev.the-full-stack.com \
  --rest-api-id ssnj6odx7l \
  --stage dev \
  --region us-east-1
```

### Paso 5 — CNAMEs en Cloudflare apuntando a API Gateway

Crear CNAMEs **proxied** (recomendado para tener WAF + cache) o
**DNS only** (mas simple):

```text
CNAME  api.portfolio.the-full-stack.com         -> d-abc123.execute-api.us-east-1.amazonaws.com  (proxied)
CNAME  api.portfolio.dev.the-full-stack.com     -> d-xyz789.execute-api.us-east-1.amazonaws.com  (proxied)
```

Con proxied: Cloudflare termina TLS en su edge + reencripta hacia API
Gateway. Hay un small overhead pero gana WAF + DDoS + rate limit en el edge.

### Paso 6 — Actualizar frontend

Editar `docker/env/.dev`:

```bash
PUBLIC_API_ENDPOINT=https://api.portfolio.dev.the-full-stack.com
```

Editar `docker/env/.prod`:

```bash
PUBLIC_API_ENDPOINT=https://api.portfolio.the-full-stack.com
```

Redeploy del frontend (Cloudflare Pages rebuild de las 6 apps).

### Paso 7 — Verificacion

```bash
# Verificar resolucion DNS
dig api.portfolio.the-full-stack.com +short
dig api.portfolio.dev.the-full-stack.com +short

# Verificar cert
echo | openssl s_client -servername api.portfolio.the-full-stack.com \
  -connect api.portfolio.the-full-stack.com:443 2>/dev/null \
  | openssl x509 -noout -dates -subject

# Verificar endpoint funcional
curl -i https://api.portfolio.the-full-stack.com/health
curl -i https://api.portfolio.dev.the-full-stack.com/health
```

### Paso 8 — Soft-rollback period

Mantener URLs raw `execute-api.amazonaws.com` operativas por **30 dias**.
NO eliminar nada de API Gateway. Solo el frontend deja de apuntar ahi.

Despues de 30 dias sin issues:
- Confirmar que ningun cliente externo usa la URL raw.
- Documentar la URL raw como deprecated en INTEGRATION.md.

### Paso 9 — Eventual cleanup (opcional, post-validacion)

Si en 60+ dias nadie consume las URLs raw, se pueden desactivar pero
NO es necesario — API Gateway no cobra por hostname raw inactivo.

## Costos esperados

| Item | Costo mensual |
|------|---------------|
| Custom Domain Names (2 entries) | $0 (no charge per domain) |
| ACM cert (regional) | $0 (free) |
| API Gateway requests (1M free tier + $3.50/M) | igual que antes |
| Cloudflare DNS records (2 CNAMEs proxied) | $0 (free plan) |
| Cloudflare proxied requests | $0 (free plan, 100k/dia) |

**Cost delta: ~$0/mes.**

## Riesgos

1. **DNS propagation**: cambio de PUBLIC_API_ENDPOINT puede tardar ~5min
   en propagarse a usuarios via cache CDN del frontend.
2. **CORS**: si la app tiene CORS estricto whitelisting el hostname raw,
   actualizar la config para incluir el nuevo hostname antes del cutover.
3. **Hard-coded URLs**: buscar en codigo y docs por `execute-api` antes
   del cutover.

## Comandos de busqueda pre-migracion

```bash
# Buscar referencias hardcoded
grep -rn "execute-api.us-east-1.amazonaws.com" \
  --include="*.ts" --include="*.astro" --include="*.md" \
  --include="*.py" --include="*.json" --exclude-dir=node_modules .
```
