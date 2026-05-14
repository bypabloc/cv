# PostgresLayer

> Lambda Layer con psycopg3 binary compilado para arm64 Graviton2.
> Usado por las Lambdas `stream_processor` (SPEC-009) y `aggregator` (SPEC-010).

## Por que un layer separado

- psycopg[binary] pesa ~10MB. Si lo inlineamos en cada Lambda zip, cada
  function crece y cold start sube.
- Solo 2 Lambdas (stream_processor, aggregator) lo necesitan. El layer las
  evita duplicar.
- CommonLayer (SPEC-001) NO incluye psycopg para mantener el size bajo
  para las 3 Lambdas hot path (contact_form, tracking_pixel, turnstile_validator)
  que NO tocan PostgreSQL.

## Rebuild

```bash
cd serverless
make build  # o: sam build --use-container --cached
```

`--use-container` es OBLIGATORIO porque el binary de psycopg debe matchear
linux/arm64 (no tu host x86_64). Sin esto, falla con
`ImportError: cannot import name 'psycopg' from partially initialized module`.

## Cuando agregar al template

El layer se referencia en SPEC-009/010 con:

```yaml
Layers:
  - !Ref CommonLayer
  - !Ref PostgresLayer
```

NO referenciarlo en SPECs 005/006/007 (no tocan DB).
