# PostgresLayer

> Lambda Layer con psycopg3 binary compilado para arm64 Graviton2.
> Usado por la Lambda `stream_processor` (SPEC-009).

## Por que un layer separado

- psycopg[binary] pesa ~10MB. Si lo inlineamos en cada Lambda zip, cada
  function crece y cold start sube.
- Solo `stream_processor` lo necesita. El layer evita inlinear psycopg.
- CommonLayer (SPEC-001) NO incluye psycopg para mantener el size bajo
  para las Lambdas hot path (contact_form, tracking_pixel) que NO tocan
  PostgreSQL.

## Rebuild

```bash
cd serverless
make build  # o: sam build --use-container --cached
```

`--use-container` es OBLIGATORIO porque el binary de psycopg debe matchear
linux/arm64 (no tu host x86_64). Sin esto, falla con
`ImportError: cannot import name 'psycopg' from partially initialized module`.

## Cuando agregar al template

El layer se referencia en SPEC-009 con:

```yaml
Layers:
  - !Ref CommonLayer
  - !Ref PostgresLayer
```

NO referenciarlo en SPECs 005/006 (no tocan DB).
