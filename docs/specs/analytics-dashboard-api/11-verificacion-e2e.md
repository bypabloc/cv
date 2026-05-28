# 11 — Verificacion E2E iterativa (gate del PR)

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [< README](README.md)

> Fase final del plan. Es la **ultima fase y el ultimo commit**. NO se
> hace `git push` ni se abre el PR hasta que toda esta bateria pase
> completa en verde. Es el gate de cierre, no un paso intermedio.

## Bucle de cierre

```text
loop:
  ejecutar bateria completa
  if alguna parte falla:
    diagnosticar -> corregir -> commit fix
    continue
  else:
    push + abrir PR
    salir
```

No se marca completa con un comando fallando, un test rojo o coverage
< 80%.

---

## Parte A — Refactor de tests (limpieza)

Antes de la bateria, asegurar que NINGUN test viejo apunta a codigo
eliminado o renombrado en el camino.

### A.1 Barrido global de referencias huerfanas

```bash
# Buscar referencias a paths que ya no existen (deberian dar 0)
rg -l "core\\.controllers\\.analytics\\.<deprecated>" tests/  # 0 resultados
rg -l "from core\\.<deleted_module>" tests/                    # 0 resultados
rg -l "fixture_<deprecated>" tests/                            # 0 resultados
```

Si aparecen resultados: el test referencia codigo viejo. Eliminar el
test o re-apuntarlo.

### A.2 Tests en ruta y convencion correcta

```bash
# Convencion: tests en tests/unit o tests/integration. Usar `rg` (no
# `find`): en WSL2 `find` esta aliasado a `fd` y la sintaxis GNU falla.
rg --files -g 'test_*.py' tests | rg -v '^tests/(unit|integration)/' \
  | wc -l    # debe dar 0

# Cada test_*.py tiene UN test function (regla del repo)
for f in $(rg --files -g 'test_*.py' tests/unit); do
  n=$(rg -c '^def test_' "$f")
  if [ "$n" != "1" ]; then echo "BAD: $f tiene $n funciones test_*"; fi
done | rg BAD     # debe dar 0
```

### A.3 conftest.py limpio

```bash
# conftest no debe tener fixtures muertos (no referenciados desde ningun test)
# Esto es manual o via pytest --collect-only -q
python devtools/run.py serverless tests --type=unit --lambda=analytics -- --collect-only -q | head -50
```

---

## Parte B — Bateria de comandos reales

### B.0 Pre-flight (local, no deploys)

```bash
# 1. Sintaxis Python (compileall) — debe pasar 100%
python -m compileall -q serverless/lambda/services/analytics
python -m compileall -q serverless/lambda/services/db   # por el seed command nuevo

# 2. Lint-deps (shared-only imports + dedup)
python devtools/run.py serverless lint-deps --lambda=analytics    # exit 0
python devtools/run.py serverless lint-deps --lambda=db           # exit 0

# 3. Unit tests del nuevo Lambda
python devtools/run.py serverless tests --type=unit --lambda=analytics
# Esperado: 100+ tests verdes, 0 fails, 0 errors

# 4. Unit tests del Lambda `db` (seed command nuevo)
python devtools/run.py serverless tests --type=unit --lambda=db -- -k seed_rate_limit_rule
# Esperado: 4 tests verdes

# 5. Coverage gate
python devtools/run.py serverless tests --type=coverage --lambda=analytics
# Esperado: coverage per-file >= 80% en core/ (AC-21)

# 6. Markdownlint del plan (NO debe fallar antes del rm)
markdownlint docs/specs/analytics-dashboard-api/*.md
# Esperado: warnings ok, errors NO
```

### B.1 Run local del Lambda contra Neon dev (con RIE)

```bash
# Levantar el Lambda en modo RIE (Runtime Interface Emulator)
# y disparar cada accion con su event JSON.
# RIE corre el Lambda en un container Docker local.

for evt in events/*.json; do
  echo "--- $evt ---"
  python devtools/run.py serverless run --stage=local --lambda=analytics \
    --event="$evt" --runtime-mode=rie
done
```

Verificar para cada response:

- HTTP status = 200 (o 4xx esperado segun event)
- Body es JSON valido
- `data` tiene la shape definida en los AC

### B.2 Deploy a dev + seed rule

```bash
# 1. Deploy el Lambda
python devtools/run.py serverless deploy --lambda=analytics --stage=dev \
  --aws-profile=tfs-dev
# Esperado: exit 0, archivo de estado actualizado

# 2. Verificar status
python devtools/run.py serverless status --lambda=analytics --stage=dev \
  --aws-profile=tfs-dev
# Esperado: estado SYNCED

# 3. Seed de la rate-limit rule
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev
# Esperado: {action: created|updated, rule_key: "/analytics"}

# 4. Confirmar la rule en DynamoDB
aws dynamodb get-item \
  --table-name portfolio-rate-limit-rules-dev \
  --key '{"rule_key":{"S":"/analytics"},"kind":{"S":"ip"}}' \
  --region us-east-1 --profile tfs-dev
# Esperado: Item con limit=10, window_seconds=60
```

### B.3 Smoke E2E contra dev (curl, 19 endpoints)

URL base: `https://api.portfolio.dev.the-full-stack.com/analytics`.

```bash
BASE="https://api.portfolio.dev.the-full-stack.com/analytics"
FROM="2026-04-27"
TO="2026-05-27"

# 1. analytics/overview                  AC-1
curl -sS "$BASE?operation=analytics&action=overview&from=$FROM&to=$TO" | jq .

# 2. analytics/timeseries (bucket=day)   AC-7
curl -sS "$BASE?operation=analytics&action=timeseries&from=$FROM&to=$TO&bucket=day" | jq .

# 3. analytics/top-pages
curl -sS "$BASE?operation=analytics&action=top-pages&from=$FROM&to=$TO&limit=10" | jq .

# 4. analytics/top-referrers
curl -sS "$BASE?operation=analytics&action=top-referrers&from=$FROM&to=$TO" | jq .

# 5. analytics/top-niches
curl -sS "$BASE?operation=analytics&action=top-niches&from=$FROM&to=$TO" | jq .

# 6. analytics/active-now                AC-17
curl -sS "$BASE?operation=analytics&action=active-now" | jq .

# 7. analytics/retention                 AC-18
curl -sS "$BASE?operation=analytics&action=retention&from=$FROM&to=$TO" | jq .

# 8. events/distribution
curl -sS "$BASE?operation=events&action=distribution&from=$FROM&to=$TO" | jq .

# 9. events/list                         AC-9
curl -sS "$BASE?operation=events&action=list&from=$FROM&to=$TO&page=1&page_size=50" | jq '.data | {page, page_size, total, has_more, items_count: (.items|length)}'

# 10. events/heatmap
curl -sS "$BASE?operation=events&action=heatmap&from=$FROM&to=$TO" | jq '.data.cells | length'

# 11. sessions/list
curl -sS "$BASE?operation=sessions&action=list&from=$FROM&to=$TO&page=1&page_size=20" | jq '.data | {page, total}'

# 12. sessions/detail (con un session_id real)         AC-12
SID=$(curl -sS "$BASE?operation=sessions&action=list&from=$FROM&to=$TO&page=1&page_size=1" | jq -r '.data.items[0].session_id')
curl -sS "$BASE?operation=sessions&action=detail&session_id=$SID" | jq '.data | keys'

# 13. visits/list
curl -sS "$BASE?operation=visits&action=list&from=$FROM&to=$TO&page=1&page_size=20" | jq '.data | {page, total}'

# 14. visits/landing-pages
curl -sS "$BASE?operation=visits&action=landing-pages&from=$FROM&to=$TO" | jq .

# 15. geo/by-country                     AC-13
curl -sS "$BASE?operation=geo&action=by-country&from=$FROM&to=$TO" | jq '.data.items | length'

# 16. devices/breakdown                  AC-14
curl -sS "$BASE?operation=devices&action=breakdown&from=$FROM&to=$TO" | jq '.data | keys'

# 17. funnel/conversion                  AC-15
curl -sS "$BASE?operation=funnel&action=conversion&from=$FROM&to=$TO" | jq .

# 18. contacts/list                      AC-16
curl -sS "$BASE?operation=contacts&action=list&from=$FROM&to=$TO&page=1" | jq '.data | {page, total}'

# 19. contacts/by-status
curl -sS "$BASE?operation=contacts&action=by-status&from=$FROM&to=$TO" | jq .
```

Cada response debe tener:

- HTTP 200
- Header `Content-Type: application/json`
- Body con `is_valid: true, code: 0, data: {...}`

### B.4 Smoke de errores

```bash
# Operation invalida -> 400 code 1000 (AC-4)
curl -sS -o /dev/null -w '%{http_code}\n' \
  "$BASE?operation=foo&action=bar"
# Esperado: 400

# Action invalida -> 400 code 1000 (AC-4)
curl -sS -o /dev/null -w '%{http_code}\n' \
  "$BASE?operation=analytics&action=bogus"
# Esperado: 400

# Rango fechas > 90d -> 400 code 1001 (AC-3)
curl -sS -o /dev/null -w '%{http_code}\n' \
  "$BASE?operation=analytics&action=overview&from=2025-01-01&to=2026-05-27"
# Esperado: 400

# page_size > max -> 400 code 1002 (AC-10)
curl -sS -o /dev/null -w '%{http_code}\n' \
  "$BASE?operation=events&action=list&from=$FROM&to=$TO&page_size=500"
# Esperado: 400

# sessions/detail con session_id inexistente -> 404 (AC-11)
curl -sS -o /dev/null -w '%{http_code}\n' \
  "$BASE?operation=sessions&action=detail&session_id=does-not-exist"
# Esperado: 404

# 11 requests/min desde la misma IP -> 429 (AC-5)
for i in {1..11}; do
  curl -sS -o /dev/null -w "$i: %{http_code}\n" \
    "$BASE?operation=analytics&action=active-now"
done
# Esperado: las primeras 10 con 200, la 11va con 429
```

**Known limitation**: el test asume que las 11 requests salen con la
misma IP de origen. Detras de NAT corporativo, VPN o cuando el cliente
usa un pool de IPs (CGNAT movil, ciertos proxies), la IP extraida por
API Gateway puede rotar entre requests y el contador del rate-limit no
acumula sobre el mismo bucket. Si la 11va request devuelve 200 en lugar
de 429, verificar con `curl --interface <iface>` o ejecutar el bucle
desde una conexion con IP estable (laptop en wifi residencial) antes
de declarar regresion.

### B.5 Cache hit verificacion (AC-8)

```bash
# Llamada 1 (cache miss)
T1=$(date +%s%N)
curl -sS "$BASE?operation=analytics&action=overview&from=$FROM&to=$TO" > /tmp/r1.json
T2=$(date +%s%N)

# Llamada 2 inmediata (cache hit)
T3=$(date +%s%N)
curl -sS "$BASE?operation=analytics&action=overview&from=$FROM&to=$TO" > /tmp/r2.json
T4=$(date +%s%N)

# Las dos responses deben ser IDENTICAS
diff /tmp/r1.json /tmp/r2.json  # 0 diff

# La segunda debe ser sensiblemente mas rapida (TTL hit)
MS1=$(( (T2 - T1) / 1000000 ))
MS2=$(( (T4 - T3) / 1000000 ))
echo "miss: ${MS1}ms, hit: ${MS2}ms"
# Esperado: MS2 < MS1 / 3 (hit es al menos 3x mas rapido)
```

### B.6 SnapStart verificacion (AC-19)

```bash
# Forzar cold start: redeploy + esperar
python devtools/run.py serverless deploy --lambda=analytics --stage=dev --aws-profile=tfs-dev
sleep 30  # esperar que el snapshot se publique

# Llamada 1 (cold start con SnapStart Restore)
time curl -sS "$BASE?operation=analytics&action=active-now" > /dev/null

# Verificar en CloudWatch Logs el campo "Restore Duration"
aws logs tail /aws/lambda/portfolio-analytics-dev \
  --since 5m --format short --profile tfs-dev | grep "Restore Duration"
# Esperado: Restore Duration < 1500ms (AC-19)
```

### B.7 Logs CloudWatch — sin ERROR/WARN sostenido

```bash
# Tras la bateria, revisar logs:
aws logs tail /aws/lambda/portfolio-analytics-dev \
  --since 15m --filter-pattern '?ERROR ?WARNING' \
  --format short --profile tfs-dev
# Esperado: solo INFO. Si hay ERROR/WARN, diagnosticar.
```

### B.8 Sin tests/coverage rotos

```bash
python devtools/run.py serverless tests --type=unit --lambda=analytics
# Esperado: passed=N, failed=0, errors=0

python devtools/run.py serverless tests --type=integration --lambda=analytics \
  --aws-profile=tfs-dev
# Esperado: passed=6, failed=0, errors=0 (segun seccion 6)

python devtools/run.py serverless tests --type=coverage --lambda=analytics
# Esperado: coverage per-file >= 80% en core/
```

### B.9 (Opcional) Promocion a stage + smoke

Solo si dev pasa todo y se quiere validar antes del PR:

```bash
# Crear PR feature/X -> dev primero. Luego, tras merge a dev, el flujo
# normal dev -> stage -> main se ejecuta via los workflows.
# Cuando llega a stage:
python devtools/run.py serverless run --stage=stage --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev

# Repetir B.3 y B.4 con BASE=https://api.portfolio.stage.the-full-stack.com/analytics
```

---

## Cierre del plan

Cuando TODA la bateria pasa en verde:

```bash
# 1. Limpiar la carpeta de la spec (decision documentada en README)
git rm -r docs/specs/analytics-dashboard-api/

# 2. Actualizar knowledge tree con el Lambda nuevo
# (editar .claude/docs/serverless-backend/03-lambdas.md y agregar entrada)

# 3. Hacer el ultimo commit
git add .claude/docs/serverless-backend/03-lambdas.md
git commit -m "$(cat <<'EOF'
docs(serverless): agrega lambda analytics al knowledge tree y elimina spec efimera

- .claude/docs/serverless-backend/03-lambdas.md: agrega entrada de analytics
- docs/specs/analytics-dashboard-api/: eliminada (efimera, plan implementado)
- Bateria de verificacion E2E (seccion 11) pasa completa en dev:
  19 endpoints OK + 6 cases de error + cache hit + SnapStart < 1500ms
  + coverage >= 80%
EOF
)"

# 4. Push y abrir PR
git push -u origin feature/analytics-dashboard-api
gh pr create --base dev --title "feat(analytics): nuevo Lambda analytics con dashboard API" \
  --body "$(cat <<'EOF'
## Problema
1. El backend persiste sessions/visits/events/contacts en Neon pero no hay forma de leerlos sin abrir `psql`.
2. El dashboard de analytics del portfolio necesita una API HTTP que exponga KPIs, timeseries, rankings y listados.

## Solucion
1. Nuevo Lambda `analytics` (GET `/analytics?operation=...&action=...`) con 19 actions distribuidos en 8 operations.
2. Rate-limit 10 req/min/IP via `shared.rate_limit`, cache 60s via `shared.cache` en queries agregadas, SnapStart habilitado.

## Como probar
- `python devtools/run.py serverless tests --type=coverage --lambda=analytics` (>= 80%)
- Smoke contra dev: ver `docs/specs/analytics-dashboard-api/11-verificacion-e2e.md` seccion B.3 (eliminado al mergear, pero esta en este PR todavia).
- `curl "https://api.portfolio.dev.the-full-stack.com/analytics?operation=analytics&action=overview&from=2026-04-27&to=2026-05-27"` -> 200 con shape esperada.

## TODO
- Auth real (Cloudflare Access o Bearer en SSM) — fuera de scope.
- Frontend Astro del dashboard — proxima iteracion.
EOF
)"
```

---

## Si algo falla en la bateria

Procedimiento:

1. **NO** marcar el plan completo.
2. **NO** abrir el PR.
3. Diagnosticar el fallo:
   - ¿Sintaxis? -> compileall te dice el archivo.
   - ¿Test unitario? -> reproducir local, fix, re-correr.
   - ¿Deploy? -> revisar logs `serverless deploy` + Cloudformation.
   - ¿Smoke 4xx inesperado? -> CloudWatch logs del Lambda.
   - ¿Smoke 5xx? -> CloudWatch + tracer X-Ray.
4. Hacer commit de FIX (NO usar `--amend` salvo en local antes de
   push).
5. Re-correr la bateria COMPLETA desde el inicio (no spot-fix).
6. Repetir hasta verde.

## Anti-patrones del cierre

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `git push --force` para "limpiar" la historia del feature | Se pierde trazabilidad de los fixes | Mergear con `--no-ff` y dejar la historia |
| Abrir PR con "fix later" en TODO | Va contra el gate | Fixear antes |
| Cachear el `tmp/r1.json` y `tmp/r2.json` en disco luego de la bateria | Se mezclan resultados de runs | `rm -f /tmp/r*.json` al final |
| Saltarse B.4 (errores) porque B.3 (happy path) pasa | Los errores pueden estar mal mapeados | Bateria completa o nada |
| Asumir que stage/prod tienen la rule porque dev la tiene | Cada env es independiente | Correr `db seed_rate_limit_analytics` en cada env |

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [< README](README.md)
