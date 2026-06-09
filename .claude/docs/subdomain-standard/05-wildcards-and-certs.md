# 05 - Wildcards y certificados

> [<- 04-portfolio-exception](./04-portfolio-exception.md) | [06-migration-backend-api ->](./06-migration-backend-api.md)

## Wildcards strategicos que el patron permite

| Wildcard | Cubre | Util para |
|----------|-------|-----------|
| `*.the-full-stack.com` | Cualquier subdomain de 1 nivel: `faststruct`, `hub`, `status`, etc. | Universal SSL de Cloudflare (default) |
| `*.dev.the-full-stack.com` | Products en dev: `faststruct.dev`, `proyectoX.dev`, etc. | Cert wildcard 1-nivel por env dev |
| `*.faststruct.the-full-stack.com` | Components de faststruct prod: `app`, `api`, `admin`, etc. | Cert wildcard 1-nivel por product prod |
| `*.faststruct.dev.the-full-stack.com` | Components de faststruct dev | Cert wildcard 1-nivel por product+env dev |

## Limitacion de wildcards SSL

**Un wildcard SSL cubre solo UN nivel de label**. Esto significa:

- `*.the-full-stack.com` cubre `faststruct.the-full-stack.com` ✅
- `*.the-full-stack.com` NO cubre `api.faststruct.the-full-stack.com` ❌
  (2 niveles)
- `*.faststruct.the-full-stack.com` cubre `api.faststruct.the-full-stack.com` ✅

Por eso el patron usa `{component}` como sub-label (no como sufijo del
slug del product). Eso permite que un solo cert wildcard cubra todos los
components.

## Estrategias practicas

### Estrategia A — Cloudflare Pages auto-cert por hostname (DEFAULT, RECOMENDADO)

Cada Pages project agrega su custom domain via UI o API y Cloudflare
emite un cert SAN especifico para ese hostname (via Google Trust Services
o similar). Ventajas:

- Cero gestion manual de certs.
- Renovacion automatica antes de expiracion.
- Funciona para products y components individuales.

Desventajas:

- Cada cert es por hostname (no wildcard). Si tenes 30 hostnames, son 30
  certs.
- Lleva ~5-15min para emitir cada cert nuevo.

**Cuando usar**: 95% de los casos. Por default, dejar que Cloudflare
maneje el SSL.

### Estrategia B — Universal SSL de Cloudflare (gratis)

Cloudflare emite automaticamente un cert wildcard `*.the-full-stack.com`
+ `the-full-stack.com`. Cubre todos los hostnames de **1 nivel**:

- `faststruct.the-full-stack.com` ✅
- `status.the-full-stack.com` ✅
- `portfolio.the-full-stack.com` ✅
- `api.faststruct.the-full-stack.com` ❌ (2 niveles)
- `hub.portfolio.the-full-stack.com` ❌ (2 niveles)

**Cuando usar**: ya esta activo por default. Cubre los products sin
component automaticamente. No requiere nada.

### Estrategia C — Cloudflare Advanced Certificate (pago, ~$10/mes/cert)

Cert wildcard custom para 2 niveles:

- `*.faststruct.the-full-stack.com` cubre app, api, admin, docs, etc.
- `*.dev.the-full-stack.com` cubre cualquier product en dev.

**Cuando usar**: si gestiones >10 hostnames bajo un product/env y queres
1 solo cert. En la escala actual del proyecto (<20 hostnames), Pages
auto-cert (estrategia A) es mas simple y gratis.

### Estrategia D — ACM cert custom (para API Gateway de AWS)

API Gateway requiere un cert ACM en la misma region. Para el backend
serverless del portfolio:

```bash
# Cert SAN cubriendo prod + dev del backend portfolio
aws acm request-certificate \
  --domain-name api.portfolio.the-full-stack.com \
  --subject-alternative-names api.portfolio.dev.the-full-stack.com \
  --validation-method DNS \
  --region us-east-1
```

Despues, agregar los CNAMEs de validacion en Cloudflare. Detalle en
[06-migration-backend-api.md](./06-migration-backend-api.md).

## Decision flow para SSL

```text
1. Product en Cloudflare Pages? -> Estrategia A (auto-cert por hostname)
2. Product sin component (1 nivel)? -> Estrategia B cubre auto via Universal SSL
3. Product con 5+ components y queres 1 cert? -> Estrategia C (Advanced Cert pago)
4. API Gateway de AWS? -> Estrategia D (ACM cert)
5. Otro hosting? -> revisar capabilities del hosting
```

## CAA records

Recomendado tener CAA records en la zona para limitar que CAs pueden
emitir certs:

```text
CAA  the-full-stack.com  0 issue "letsencrypt.org"
CAA  the-full-stack.com  0 issue "pki.goog"
CAA  the-full-stack.com  0 issue "amazon.com"
CAA  the-full-stack.com  0 issuewild "letsencrypt.org"
CAA  the-full-stack.com  0 issuewild "pki.goog"
CAA  the-full-stack.com  0 iodef "mailto:pacg1991@gmail.com"
```

Esto evita que un atacante emita un cert con otra CA si compromete una
parte del DNS. Cloudflare por default emite con `pki.goog` (Google Trust
Services) o `letsencrypt.org`.

## TTL recomendado

| Tipo de record | TTL |
|----------------|-----|
| Apex / www (estable) | 3600s (1h) |
| Products en prod (estables) | 3600s |
| Products en dev (rotacion frecuente) | 300s (5min) |
| Records de verificacion (DKIM, SPF, DMARC, atproto) | 3600s |
| Validacion ACM/Let's Encrypt (temporales) | 300s |
