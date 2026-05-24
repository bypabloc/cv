# 07 — Verificacion E2E iterativa (gate de cierre)

[← Paralelizacion](06-paralelizacion-worktrees.md) | [Volver al README](README.md)

Es la ultima fase del plan. NO se hace `git push` ni se crea el PR
hasta que esta bateria pase **completa, en verde, de punta a punta**.

## Parte A — Refactor de tests

Verificar que ningun test viejo siga referenciando codigo eliminado.
Cero resultados esperados en cada `rg`:

```bash
# Imports a columnas dropeadas que ya no existen en ORM
rg -n 'TrackingEvent\(.*(ip|country|user_agent|browser|browser_version|os|device_type|utm_source|utm_medium|utm_campaign|utm_content|utm_term)=' serverless/lambda/

# Persistencia directa de esos campos en payload dicts (post-refactor solo se pasan a ensure_session_and_visit, no a TrackingEvent)
rg -n "'ip':|'user_agent':|'utm_source':|'utm_medium':|'utm_campaign':" serverless/lambda/services/tracking_pixel/core/services/

# Contacts con ip/country/user_agent — deben ser cero post-refactor
rg -n 'Contact\(.*(ip|country|user_agent)=' serverless/lambda/

# Tests viejos que asserten columnas dropeadas
rg -n 'contacts\.(ip|country|user_agent)|tracking_events\.(ip|country|user_agent|browser|os|device_type|utm_)' serverless/lambda/

# Niches: _VALID_NICHES debe haber desaparecido (centralizado en shared/core/niches)
rg -n '_VALID_NICHES' serverless/lambda/
```

Si algun comando arriba devuelve >0 lineas: corregir antes de
continuar. Estos son los AC-8 / AC-9 / AC-14 en forma de "no quedan
referencias huerfanas".

## Parte B — Bateria de comandos reales (post-deploy en dev)

Bucle "no parar hasta que funcione": ejecutar -> si falla,
diagnosticar -> corregir -> re-ejecutar la suite -> repetir.

### B.1 — Build estatico + tests del proyecto

```bash
pnpm exec biome check .                                                   # lint frontend ok
python -m compileall -q serverless/                                       # python syntax ok
serverless tests --type=unit --lambda=tracking_pixel --aws-profile=tfs-dev
serverless tests --type=unit --lambda=contact_form  --aws-profile=tfs-dev
serverless tests --type=integration --lambda=tracking_pixel --aws-profile=tfs-dev
serverless tests --type=integration --lambda=contact_form  --aws-profile=tfs-dev
```

Esperado: todos verdes, coverage >= 80% per-file en archivos
modificados.

### B.2 — Deploy backend dev

```bash
python devtools/run.py serverless deploy --stage=dev --lambda=db             --aws-profile=tfs-dev
python devtools/run.py serverless run    --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev
python devtools/run.py serverless deploy --stage=dev --lambda=tracking_pixel --aws-profile=tfs-dev
python devtools/run.py serverless deploy --stage=dev --lambda=contact_form   --aws-profile=tfs-dev
```

Esperado:

- `db` deploy ok, migration corre y `current=d4e5f6a7b8c9 (head)`.
- `tracking_pixel`, `contact_form` y `cv` deploys ok (este ultimo
  porque la centralizacion de niches modifico su modelo).

### B.3 — Verificar schema final en Neon dev

```bash
mkdir -p tmp
aws --profile tfs-dev ssm get-parameter --region us-east-1 \
  --name /portfolio/dev/neon-url --with-decryption \
  --query 'Parameter.Value' --output text > tmp/.dburl
chmod 600 tmp/.dburl

# 1. sessions y session_visits existen
psql "$(cat tmp/.dburl)" -c "SELECT to_regclass('sessions'), to_regclass('session_visits');"

# 2. tracking_events YA NO tiene las columnas dropeadas
psql "$(cat tmp/.dburl)" -c "
  SELECT column_name FROM information_schema.columns
  WHERE table_name='tracking_events'
    AND column_name IN ('ip','country','user_agent','browser','browser_version','os','device_type','utm_source','utm_medium','utm_campaign','utm_content','utm_term');
"
# Esperado: 0 rows.

# 3. contacts YA NO tiene ip/country/user_agent y session_id es NOT NULL
psql "$(cat tmp/.dburl)" -c "
  SELECT column_name, is_nullable
  FROM information_schema.columns
  WHERE table_name='contacts' AND column_name IN ('ip','country','user_agent','session_id');
"
# Esperado: solo session_id (is_nullable=NO). El resto, 0 rows.

# 4. FKs creadas
psql "$(cat tmp/.dburl)" -c "
  SELECT conname FROM pg_constraint
  WHERE conrelid IN ('tracking_events'::regclass, 'contacts'::regclass)
    AND contype='f';
"
# Esperado: 3 rows (fk_tracking_events_session, fk_tracking_events_visit, fk_contacts_session) + la FK existente a event_types.

rm -f tmp/.dburl
```

### B.4 — /track real con payload realista

```bash
SESSION_ID="sess-debug-$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
EVENT_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
PAGE_LOAD_TYPE='019e372b-e0a7-7154-8279-8829bcf6a08c'

curl -i -X POST 'https://api.portfolio.dev.the-full-stack.com/track' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://hub.portfolio.dev.the-full-stack.com' \
  -d "{
    \"operation\":\"tracking\",
    \"action\":\"track\",
    \"session_id\":\"$SESSION_ID\",
    \"event_id\":\"$EVENT_ID\",
    \"event_type_id\":\"$PAGE_LOAD_TYPE\",
    \"page_url\":\"https://hub.portfolio.dev.the-full-stack.com/?utm_source=twitter&utm_medium=social\",
    \"page_title\":\"Hub\",
    \"page_path\":\"/\",
    \"referrer\":\"https://t.co/abc\",
    \"utm_source\":\"twitter\",
    \"utm_medium\":\"social\",
    \"utm_campaign\":\"\",
    \"utm_content\":\"\",
    \"viewport_width\":1280,
    \"viewport_height\":800,
    \"niche\":\"hub\"
  }"
```

Esperado: `HTTP 204`. Luego en psql:

```sql
SELECT * FROM sessions       WHERE session_id = '$SESSION_ID';   -- 1 row
SELECT * FROM session_visits WHERE session_id = '$SESSION_ID';   -- 1 row
SELECT * FROM tracking_events WHERE session_id = '$SESSION_ID';  -- 1 row
```

Cubre AC-1 + AC-5.

### B.5 — Multi-visit (cambio de UTM)

Repetir el curl B.4 cambiando `utm_source` a `'linkedin'`:

```bash
EVENT_ID2=$(python3 -c 'import uuid; print(uuid.uuid4())')
# (mismo SESSION_ID que B.4)
curl -X POST ... -d "{ ..., \"event_id\":\"$EVENT_ID2\", \"utm_source\":\"linkedin\", ... }"
```

Esperado: `HTTP 204`. En psql:

```sql
SELECT visit_id, utm_source, ip FROM session_visits
WHERE session_id = '$SESSION_ID' ORDER BY started_at;
-- Esperado: 2 rows. Primera utm_source='twitter', segunda 'linkedin'.

SELECT visit_id FROM tracking_events
WHERE session_id = '$SESSION_ID' ORDER BY created_at;
-- Esperado: 2 rows, cada una con SU visit_id distinto.
```

Cubre AC-4.

### B.6 — Idempotencia (mismo UTM y IP)

Repetir el curl B.4 con MISMO `utm_source='twitter'` y nuevo
`event_id`. Esperado: `HTTP 204`, `tracking_events` con 3 rows pero
`session_visits` con SOLO 2 rows (el visit twitter reusa, no se crea
uno nuevo). `ended_at` del primer visit (twitter) se actualizo a
`now()`.

Cubre AC-2.

### B.7 — /contact desde el browser real

Abrir `https://hub.portfolio.dev.the-full-stack.com/contact` (o
cualquier niche dev), completar el form, submit con widget Turnstile
activo. Esperado:

- Response: `HTTP 200`.
- En psql, verificar el contact + la session enlazada:

```sql
SELECT id, session_id, name, email FROM contacts ORDER BY created_at DESC LIMIT 1;
-- 1 row con session_id NOT NULL.

SELECT * FROM sessions WHERE session_id = (
  SELECT session_id FROM contacts ORDER BY created_at DESC LIMIT 1
);
-- 1 row (creada por /track previo o por /contact on-the-fly).
```

Cubre AC-6 / AC-7.

### B.8 — Cero errores en CloudWatch post-deploy

```bash
SINCE_TS=$(($(date +%s) * 1000 - 600000))   # ultimos 10 min

aws --profile tfs-dev logs filter-log-events --region us-east-1 \
  --log-group-name '/aws/lambda/portfolio-tracking-pixel-dev' \
  --start-time $SINCE_TS \
  --filter-pattern '"NotNullViolation" "ForeignKeyViolation" "IntegrityError"' \
  --query 'events[*].timestamp' --output text

aws --profile tfs-dev logs filter-log-events --region us-east-1 \
  --log-group-name '/aws/lambda/portfolio-contact-form-dev' \
  --start-time $SINCE_TS \
  --filter-pattern '"NotNullViolation" "ForeignKeyViolation" "IntegrityError"' \
  --query 'events[*].timestamp' --output text
```

Esperado: ambas queries devuelven vacio.

### B.9 — FK obligatoria (AC-11)

```bash
psql "$(cat tmp/.dburl)" -c "
  DELETE FROM sessions WHERE session_id = '$SESSION_ID';
"
# Esperado: ERROR: update or delete on table 'sessions' violates foreign key constraint
# (porque tiene tracking_events/contacts).
```

Cubre AC-11.

### B.10 — Invariante `event_count == COUNT(*)` (AC-16)

```bash
psql "$(cat tmp/.dburl)" -c "
  SELECT
    v.visit_id,
    v.event_count AS cached,
    COUNT(t.*)::int AS real_count,
    v.event_count = COUNT(t.*) AS coherent
  FROM session_visits v
  LEFT JOIN tracking_events t ON t.visit_id = v.visit_id
  WHERE v.session_id = '$SESSION_ID'
  GROUP BY v.visit_id, v.event_count;
"
# Esperado: la columna 'coherent' es TRUE para todos los visits.
```

Si algun row tiene `coherent=FALSE` -> bug en el incremento del helper
(el UPDATE no corre dentro de la misma tx que el INSERT, o se duplica).

Cubre AC-15 / AC-16.

### B.11 — Modulo central de niches importable y consumido (AC-13/14)

```bash
# Importacion desde el repo (sin Lambda)
cd serverless/lambda
.venv/bin/python -c "
from shared.core.niches import ALL_NICHES, CV_NICHES, niche_from_origin
assert ALL_NICHES == {'hub', 'fintech', 'architect', 'leader', 'vibe', 'generic'}, ALL_NICHES
assert CV_NICHES == ALL_NICHES - {'hub'}, CV_NICHES
assert niche_from_origin('https://fintech.portfolio.dev.the-full-stack.com') == 'fintech'
assert niche_from_origin('https://the-full-stack.com') is None
assert niche_from_origin(None) is None
print('OK')
"
cd ../..

# Y desde el Lambda cv ya deployado: invocar GET /cv?niche=fintech y verificar 200
curl -s -o /dev/null -w 'HTTP %{http_code}\n' \
  'https://api.portfolio.dev.the-full-stack.com/cv?operation=cv&action=get&niche=fintech&locale=es' \
  -H 'Origin: https://hub.portfolio.dev.the-full-stack.com'
# Esperado: HTTP 200.
```

Cubre AC-13 / AC-14.

### B.12 — Cleanup (datos de prueba dev)

```bash
# Borrar el SESSION_ID de prueba en orden inverso:
psql "$(cat tmp/.dburl)" -c "
  DELETE FROM tracking_events WHERE session_id = '$SESSION_ID';
  DELETE FROM session_visits  WHERE session_id = '$SESSION_ID';
  DELETE FROM contacts        WHERE session_id = '$SESSION_ID';  -- si aplico
  DELETE FROM sessions        WHERE session_id = '$SESSION_ID';
"
```

## Parte C — git rm de la spec

Ultimo paso del C8:

```bash
git rm -r docs/specs/sessions-normalize/
git commit -m "$(cat <<'EOF'
verify(spec): sessions-normalize bateria E2E + cleanup

- bateria de [07-verificacion-e2e.md] pasa completa en verde
- migration aplicada en dev (current=d4e5f6a7b8c9)
- /track + /contact funcionando con nueva tabla sessions/session_visits
- cleanup: spec efimera eliminada (vive solo en git log)
EOF
)"
```

## Regla de cierre

NO se hace `git push` ni `gh pr create` hasta:

- [ ] Parte A: cero referencias huerfanas (todos los `rg -n` retornan vacio, incluida `_VALID_NICHES`).
- [ ] Parte B.1: build + lint + unit + integration verdes.
- [ ] Parte B.2: deploy backend dev exitoso (incluye `cv`).
- [ ] Parte B.3: schema verificado en Neon dev (sessions + session_visits + event_count).
- [ ] Parte B.4-B.7: curls reales devuelven HTTP esperado y la DB tiene las rows correctas.
- [ ] Parte B.8: 0 errores en CloudWatch ultimos 10 min.
- [ ] Parte B.9: FK rechaza el DELETE.
- [ ] Parte B.10: invariante `event_count == COUNT(*)` cumplida para todos los visits.
- [ ] Parte B.11: modulo central de niches importable y `cv` responde 200.
- [ ] Parte B.12: cleanup de prueba ok.
- [ ] Parte C: spec eliminada con `git rm -r`.

Si algun item falla -> corregir en la rama -> re-ejecutar la bateria
completa desde B.1. NO se "skip" ningun item.

[← Paralelizacion](06-paralelizacion-worktrees.md) | [Volver al README](README.md)
