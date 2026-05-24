# 05 — Verificacion E2E iterativa (fase final)

[← 04-paralelizacion-worktrees.md](04-paralelizacion-worktrees.md) | [README](README.md)

## 11. Verificacion E2E (commit 7)

Fase de cierre. SIEMPRE es el ultimo commit (`verify(spec):
drop-cloudfront-meta bateria E2E + cleanup`). NO se hace `git push` ni
se crea el PR hasta que esta bateria pase **completa en verde**.

## Parte A — Refactor de tests (barrido final)

Verificar que el repo no tiene referencias huerfanas a las columnas
borradas en archivos de codigo / tests **post-cleanup**:

```bash
# 1. Ningun service/model debe persistir las columnas huerfanas a Neon.
rg -n "cloudfront_meta" serverless/lambda/services/ \
  serverless/lambda/shared/db/
# Esperado: 0 resultados.

rg -n "'expires_at'|\"expires_at\"" \
  serverless/lambda/services/tracking_pixel/core/ \
  serverless/lambda/services/contact_form/core/ \
  serverless/lambda/shared/db/models/
# Esperado: 0 resultados.

# 2. page_url, page_title, referrer no aparecen en el payload Neon.
#    Quedan vivos en Pydantic + tests de tracking_payload (Pydantic),
#    pero NO en core/services ni en el ORM.
rg -n "'page_url'|'page_title'|'referrer'" \
  serverless/lambda/services/tracking_pixel/core/services/ \
  serverless/lambda/shared/db/models/tracking.py
# Esperado: 0 resultados.

# 3. La migracion nueva existe y referencia b2c3d4e5f6a7 como down_revision.
rg -n "down_revision.*b2c3d4e5f6a7" \
  serverless/lambda/shared/db/alembic/versions/
# Esperado: 1 resultado (la migracion nueva).

# 4. idx_tracking_referrer NO debe quedar en los modelos vivos.
rg -n "idx_tracking_referrer" serverless/lambda/shared/db/models/
# Esperado: 0 resultados (solo aparece en la migracion nueva en
# downgrade y en la migracion vieja 81c2cc51db34 en upgrade).
```

## Parte B — Bateria de comandos reales

Bucle "no parar hasta que funcione": ejecutar -> si falla, diagnosticar
-> corregir -> re-ejecutar la suite -> repetir. NO se marca completa
con un comando fallando, un test rojo o coverage < 80%.

### B.1 — Compilacion + lint

```bash
# Compilacion sintactica de todo el codigo Python tocado
python -m compileall -q serverless/lambda/

# Biome sobre el repo (no debe romperse aunque no toquemos TS/JS)
pnpm exec biome check .
```

### B.2 — Migracion Alembic (branch Neon de prueba)

```bash
# 1. Crear branch desde main para no contaminar dev
neon branches create --name test-drop-cfm-verify --parent main

# 2. Apuntar DB_URL al branch y correr upgrade + downgrade + upgrade
#    (verifica que upgrade y downgrade son reversibles)
DATABASE_URL="<connection-string-del-branch>" \
  .venv/bin/alembic -c serverless/lambda/shared/db/alembic.ini upgrade head
DATABASE_URL="<connection-string-del-branch>" \
  .venv/bin/alembic -c serverless/lambda/shared/db/alembic.ini downgrade -1
DATABASE_URL="<connection-string-del-branch>" \
  .venv/bin/alembic -c serverless/lambda/shared/db/alembic.ini upgrade head

# 3. Verificar columnas borradas con un \d via psql
psql "<connection-string-del-branch>" -c '\d tracking_events'
psql "<connection-string-del-branch>" -c '\d contacts'
# Esperado: ni cloudfront_meta ni expires_at en tracking_events;
#           sin cloudfront_meta en contacts.

# 4. Verificar que indice idx_tracking_referrer no existe post-upgrade
psql "<connection-string-del-branch>" -c '\di tracking_events*'
# Esperado: idx_tracking_referrer NO esta; idx_tracking_page_path SI.

# 5. Cleanup
neon branches delete test-drop-cfm-verify
```

### B.3 — Unit tests + coverage por Lambda

```bash
# tracking_pixel
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
# Coverage per-file >= 80% en archivos modificados.

# contact_form
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=contact_form

# db (los modelos SQLAlchemy + alembic)
python devtools/run.py serverless tests --type=unit --lambda=db

# shared (helpers + lambda_kit + http)
# Los tests de extract_cloudfront_meta y http_handler_injects_meta_from_headers
# DEBEN seguir verdes — decision del plan.
python devtools/run.py serverless tests --type=unit --shared
```

### B.4 — Integration tests (E2E con AWS local)

```bash
# tracking_pixel: AC-6 — handler /track sigue devolviendo 204 con headers
# cloudfront-* en el evento de API Gateway sintetico.
python devtools/run.py serverless tests \
  --type=integration --lambda=tracking_pixel

# contact_form: AC-7 — handler /contact sigue devolviendo 201 con headers
# cloudfront-* en el evento de API Gateway sintetico.
python devtools/run.py serverless tests \
  --type=integration --lambda=contact_form
```

### B.5 — Linter de dependencias shared (D-3)

```bash
# Valida que ningun Lambda declare deps que aporta shared/.
python devtools/run.py serverless lint-deps
```

### B.6 — Status del backend (drift check post-cambio)

```bash
# Solo si ya hay AWS profile en sesion: confirma que el state local
# concuerda con AWS (no debe haber drift inesperado por este plan).
python devtools/run.py serverless status \
  --stage=local --lambda=tracking_pixel
python devtools/run.py serverless status \
  --stage=local --lambda=contact_form
```

## Regla de cierre

Esta bateria es el **gate** del PR. Solo cuando TODOS los comandos
arriba terminan exit 0:

1. Hacer `git rm -r docs/specs/drop-cloudfront-meta/`.
2. Commit final (commit 7) con la firma de la seccion 9.
3. `git push origin feature/drop-cloudfront-meta`.
4. Crear PR con `gh pr create --base dev --head feature/drop-cloudfront-meta`,
   body en formato del template (Problema / Solucion / Como probar /
   TODO).
5. Tras mergear a `dev`:
   - Aplicar la migracion en AWS dev: `python devtools/run.py
     serverless run --stage=dev --lambda=db --event=events/migrate.json
     --aws-profile=tfs-dev`.
   - Verificar: `serverless run --stage=dev --lambda=db
     --event=events/current.json --aws-profile=tfs-dev` devuelve la
     nueva revision.
6. Promocion `dev -> stage -> main` siguiendo el flujo en cadena del
   proyecto. Repetir el paso del migrate en stage y prod.

---

[← 04-paralelizacion-worktrees.md](04-paralelizacion-worktrees.md) | [README](README.md)
