# 02 — Fase 0 (BLOQUEANTE): medición del cold start + SnapStart

[← 01 contexto](01-contexto-y-decision.md) · [siguiente: 03 shared →](03-shared-foundations.md)

> Primera fase y **bloqueante**: sin baseline medido NO se toca el refactor.
> Evita "optimizar a ciegas". El orquestador ya hizo una pasada en vivo (dev);
> esta fase la formaliza, la extiende a stage, y deja el `after_restore` hook
> para que SnapStart no rompa Neon tras el restore.

## 2.0 Lo ya medido (orquestador, dev, 2026-05-30)

HECHO (CloudWatch + Lambda API), guardado en
`tmp/cold-start-analysis/08-diagnostico-final-datos-duros.md`:

- SnapStart `OptimizationStatus: On` en alias `:live` de cv/auth/users/
  contact-form/tracking-pixel.
- cv: Restore 1.24s + handler 10.1s cold / 7.3s warm → la query domina.
- auth: Restore 1.20s + handler 6.9s cold / 4.2s warm.
- users: Restore 0.90s + handler 7.4s cold / 0.19s warm → cold = Neon wake.
- Versiones SnapStart acumuladas: contact-form 42, auth 32, users 24,
  tracking 16, cv 10 (cleanup pendiente, item de costo).

Esta sub-fase NO se re-ejecuta salvo que el diagnóstico cambie; queda como
baseline. Lo que falta (abajo) SÍ es trabajo de la Fase 0.

## 2.1 Método de medición canónico (corrige el harness)

**SIEMPRE** medir el cold del Lambda con la REPORT line de CloudWatch, NO con
el roundtrip httpx de `api_e2e` (que incluye ~2.6s de red WSL2→us-east-1 que el
usuario real, vía Cloudflare, no paga):

```bash
# 1) SnapStart status real (alias live; NUNCA sin --qualifier: $LATEST da Off)
for fn in cv auth users contact-form tracking-pixel; do
  aws lambda get-function-configuration --function-name "portfolio-$fn-dev" \
    --qualifier live --region us-east-1 --profile tfs-dev \
    --query '{Mem:MemorySize,Arch:Architectures,SnapStart:SnapStart}'
done

# 2) REPORT lines: Restore Duration vs Init Duration vs Duration vs Max Memory
for fn in cv auth users contact-form tracking-pixel; do
  LG="/aws/lambda/portfolio-$fn-dev"
  START=$(( ($(date +%s) - 259200) * 1000 ))
  aws logs filter-log-events --log-group-name "$LG" --start-time "$START" \
    --filter-pattern 'REPORT' --region us-east-1 --profile tfs-dev \
    --max-items 8 --query 'events[].message' --output text \
    | rg -o 'Restore Duration: [0-9.]+ ms|Init Duration: [0-9.]+ ms|Duration: [0-9.]+ ms|Max Memory Used: [0-9]+ MB'
done
```

Reglas de lectura:
- `Restore Duration` presente → SnapStart restaura (imports en snapshot). ✅
- `Init Duration` presente (sin Restore) → corrió `$LATEST` o ventana
  post-deploy → SnapStart NO aplicó en esa invocación.
- `cold_handler - warm_handler` ≈ Neon wake + connect (lo único atacable sin
  tocar la query).
- `warm_handler` alto (cv 7.3s) → la QUERY es el problema, no el cold.

## 2.2 Descomposición por Lambda (entregable de la fase)

Para cada Lambda, aislar el wake de Neon de la query:

```bash
# Wake de Neon: invocar con Neon recién pingeado (despierto) vs tras 6+ min
# idle (dormido). El delta del Handler Duration ≈ el wake.
# (No deploy; sólo invoke + leer REPORT.)
```

Entregable: tabla por Lambda `Restore | Neon-wake | query | total` con números
de CloudWatch, anexada a `tmp/cold-start-analysis/08-...md` o a este archivo.

## 2.3 `after_restore` hook (prerequisito de SnapStart + Neon)

Las conexiones TCP NO sobreviven el snapshot de SnapStart. Hoy `warm_db()` usa
**NullPool** (no abre conexión en INIT) → no arrastra un socket muerto, así que
no rompe. Pero para robustez se registra un hook de restore que invalide
cualquier recurso de red cacheado:

### Crear
- `serverless/lambda/shared/db/snapstart.py` (o extender `warmup.py`):
  - `register_after_restore(callback)` — envuelve
    `snapshot_restore_py.register_after_restore` (módulo del runtime 3.13). Si
    el módulo no existe (local/test), no-op best-effort.
  - En `warm_db()`: tras crear el engine NullPool, registrar un `after_restore`
    que haga `engine.dispose()` (descarta cualquier conexión pre-snapshot;
    NullPool igual no tiene, pero deja el patrón correcto y documentado).
- Tests: `shared/tests/unit/shared/db/test_snapstart_after_restore.py` — Given
  un callback registrado, When se simula el restore, Then se invoca y el engine
  se dispone (assert exacto sobre el mock).

### Regla
- **SIEMPRE** NullPool en el engine de INIT (ya está). El `after_restore` es
  defensa en profundidad: NUNCA arrastrar un socket pre-snapshot.

## 2.4 Cleanup de versiones SnapStart (item de costo, opcional en Fase 0)

Borrar versiones publicadas viejas no apuntadas por `live` (contact-form tiene
42). Reduce el storage de snapshots (AWS lo cobra en Python desde 2025). Es
ortogonal a la latencia; se puede diferir a la fase 8.

```bash
# Listar versiones que NO son la del alias live, y borrar las viejas.
# (script devtools opcional: serverless prune-versions --keep=3)
```

## 2.5 Gate de salida de la Fase 0 (qué desbloquea el resto)

- [ ] SnapStart `On` confirmado en `:live` de los 5 (HECHO).
- [ ] Descomposición Restore/Neon-wake/query documentada por Lambda.
- [ ] `after_restore` hook implementado + test verde.
- [ ] Baseline de memoria registrado (para AC-5: nada sube de memoria).
- [ ] Objetivo de cold acordado por Lambda (realista, post-medición):
  - cv: warm < 0.5s (post-cache) ; cold < ~3s (sólo restore, cache hit).
  - tracking_pixel: cold ≈ 3.7s preservado (no peor).
  - contact_form / auth / users: cold dominado por Neon wake; objetivo =
    reducir lo que se pueda sin subir memoria (cache donde aplique, keep-alive
    opcional), NUNCA regresión.

## Archivos afectados (fase 0)

### Crear
- `serverless/lambda/shared/db/snapstart.py` (o extender `warmup.py`) — hook.
  - Verificar: `serverless tests --type=unit --shared` + `lint-deps --shared`.
- (doc) descomposición del cold por Lambda en `tmp/cold-start-analysis/`.

### Modificar
- `serverless/lambda/shared/db/warmup.py` — registrar `after_restore`.
- `.claude/rules/lambda-config.md` — sección "medir el cold con CloudWatch, no
  con el roundtrip del harness; verificar SnapStart con `--qualifier live`".

[← 01 contexto](01-contexto-y-decision.md) · [siguiente: 03 shared →](03-shared-foundations.md)
