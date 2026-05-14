# CommonLayer

> Lambda Layer compartido con dependencias runtime de todas las Lambdas del
> backend del portfolio.

## Contenido

| Dependencia | Version | Uso |
|-------------|---------|-----|
| `aws-lambda-powertools[all]` | `>=3.0,<4.0` | Logger, Tracer, Metrics, Parameters, Idempotency, BatchProcessor |
| `httpx` | `>=0.27,<1.0` | HTTP client para Cloudflare Turnstile siteverify |
| `pydantic` | `>=2.5,<3.0` | Validacion de schemas (request/response/SSM values) |
| `pydantic-settings` | `>=2.0,<3.0` | Settings via env vars con type validation |

## boto3

NO se incluye `boto3` en el layer porque viene ya instalado en el runtime
oficial de AWS Lambda Python 3.13. Incluirlo aqui solo aumenta cold start.

Para typings de boto3 en dev usa `boto3-stubs` (es devdep en `pyproject.toml`,
no se empaqueta).

## Rebuild

```bash
# Desde serverless/
make build
# o equivalente:
sam build --use-container --cached
```

`--use-container` es OBLIGATORIO para que las wheels arm64 se compilen en
linux/arm64 (no en tu host x86_64). Sin esto el Layer falla con
`No module named '_cffi_backend'` o similar al deployar.

## Tamano

Layer comprimido ~12-15 MB (limite AWS: 250 MB descomprimido). Powertools
y httpx con pydantic son los pesados pero estan dentro del limite.
