# Lambda `analytics`

API HTTP read-only de metricas del admin: `GET /analytics?operation=<X>&action=<Y>&...`.

Lee de Neon (`vis_*` + `tax_*`), valida el access JWT en cada request
(`auth_guard` -> `jwt_service.require_active_user`, portado del Lambda
`users`), aplica rate-limit per-IP (segunda capa, via `shared.rate_limit`) y
cachea las queries agregadas con TTL 60s (via `shared.cache`). SnapStart
habilitado (`snap_start: true` + `warm_db()` en el INIT).

Patron: `lambda-controller` (operation + action -> controller + service).

## Operations (8) / actions (20)

- `analytics`: overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention, dashboard
- `events`: distribution, list, heatmap
- `sessions`: list, detail
- `visits`: list, landing-pages
- `geo`: by-country
- `devices`: breakdown
- `funnel`: conversion
- `contacts`: list, by-status

## Operacion

```bash
# Tests
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=coverage --lambda=analytics
python devtools/run.py serverless lint-deps --lambda=analytics

# Run local (RIE)
python devtools/run.py serverless run --stage=local --lambda=analytics --event=events/overview.json

# Deploy
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev

# Rate-limit rule (segunda capa, 10 req/min/IP)
python devtools/run.py serverless rate-limit set --endpoint=/analytics --limit=10 --window=60 --stage=dev
```

Plan completo (efimero, se elimina al mergear): `docs/specs/b-analytics-api/`.
