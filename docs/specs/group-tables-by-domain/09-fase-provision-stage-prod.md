# 09 — Fase 5: Provision stage y prod desde cero

[README](README.md) | [08-fase-lambdas](08-fase-lambdas-update.md) |
**09-fase-provision** | [10-commits](10-commits.md)

## Objetivo

Tras mergear `feature/group-tables-by-domain -> dev` y validar dev al
100%, promover a stage y luego a prod siguiendo el flujo
`dev -> stage -> main`. En cada uno: borrar el schema viejo de Neon,
provisionar de cero, correr migraciones, seed.

## Pre-requisitos

- PR `feature/group-tables-by-domain -> dev` mergeado.
- Branch Neon `dev` (`br-little-glitter-akq7ugv3`) con schema
  renombrado + seed cargado + bateria E2E verde.

## Por que rehacer desde cero (decision del usuario)

Las branches Neon `stage` (`br-royal-truth-akbys4af`) y `production`
(`br-misty-math-akuyhn9c`) tienen el **schema viejo del runner SQL
archivado** (7 tablas: contacts, daily_metrics, event_types,
processed_stream_events, schema_migrations, tracking_daily_aggregates,
tracking_events). Alembic NO se ha aplicado nunca ahi.

Si intentamos correr la migracion `group_tables_by_domain` directamente,
fallaria porque depende de que las 37 tablas del schema unificado
existan. Habria que correr primero todas las migrations desde
`81c2cc51db34` hasta `d4e5f6a7b8c9`, lo cual tampoco funciona porque la
inicial intenta crear tablas que ya existen con otro schema.

**El usuario confirmo**: la data en stage/prod es de prueba, descartable.

Estrategia: borrar todo y empezar limpio.

## Pasos por entorno

### 5.1 — Promocion dev -> stage

#### Paso A: PR `dev -> stage` (manual)

```bash
gh pr create --base stage --head dev \
  --title "release: group-tables-by-domain a stage" \
  --body "$(cat <<'EOF'
## Promocion

Promueve a stage los cambios del PR `feature/group-tables-by-domain`
(mergeado a dev).

## Como probar

Se va a ejecutar Fase 5 (provision stage desde cero) tras el merge.
Ver `docs/specs/group-tables-by-domain/09-fase-provision-stage-prod.md`.
EOF
)"
gh pr merge --merge   # SIN --delete-branch (stage es permanente)
```

#### Paso B: Reset de branch Neon `stage`

```bash
# Verificar estado actual (debe mostrar schema viejo)
psql "$STAGE_NEON_URL" -c "\dt"

# Eliminar branch viejo y crear nuevo desde production (que tambien
# se va a borrar; mejor crear desde dev que ya tiene el schema nuevo)
neonctl branches delete br-royal-truth-akbys4af
neonctl branches create --name stage --parent br-little-glitter-akq7ugv3

# Obtener nuevo connection string
neonctl connection-string stage --role-name neondb_owner
# -> actualizar SSM /portfolio/stage/neon-url con el nuevo valor
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/stage/neon-url \
  --key-id=alias/portfolio-lambdas --env=stage
```

#### Paso C: Migrar + seed en stage

```bash
python devtools/run.py serverless run --stage=stage --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev
# espera: log "alembic: upgrade head ok, version = <ULID nuevo>"

python devtools/run.py serverless run --stage=stage --lambda=db \
  --event=events/seed.json --aws-profile=tfs-dev
# espera: log con N entidades cargadas por tabla
```

#### Paso D: Verificacion DB real en stage

```bash
psql "$STAGE_NEON_URL" <<SQL
SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
-- esperado: 39 (37 + alembic_version + tracking_events_default)

SELECT version_num FROM alembic_version;
-- esperado: <ULID nuevo>

SELECT count(*) FROM cv_profiles;
-- esperado: 1

SELECT count(*) FROM cv_endorsements;
-- esperado: 10

SELECT count(*) FROM i18n_translations WHERE entity_type = 'endorsement';
-- esperado: > 0
SQL
```

#### Paso E: Smoke test E2E en stage

```bash
# Test form de contacto contra el endpoint stage
curl -X POST https://api.portfolio.stage.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{...payload valido...}'
# esperado: HTTP 200

# Verificar persistencia
psql "$STAGE_NEON_URL" -c "SELECT id, email FROM vis_contacts ORDER BY created_at DESC LIMIT 1"
```

### 5.2 — Promocion stage -> main

Mismo procedimiento, sustituyendo `stage` por `prod`:

```bash
# 1. PR stage -> main
gh pr create --base main --head stage --title "release: group-tables-by-domain a prod"
gh pr merge --merge

# 2. Reset branch production en Neon
neonctl branches delete br-misty-math-akuyhn9c  # production
neonctl branches create --name production --parent br-little-glitter-akq7ugv3 --primary --default
# IMPORTANTE: --primary --default porque production era el primary del project

# 3. Update SSM /portfolio/neon-url (sin sufijo stage) y /portfolio/prod/neon-url
neonctl connection-string production --role-name neondb_owner
python devtools/run.py serverless setup-ssm --name=/portfolio/prod/neon-url ...
python devtools/run.py serverless setup-ssm --name=/portfolio/neon-url ...  # el legacy

# 4. Migrar + seed
python devtools/run.py serverless run --stage=prod --lambda=db --event=events/migrate.json --aws-profile=tfs-prod
python devtools/run.py serverless run --stage=prod --lambda=db --event=events/seed.json --aws-profile=tfs-prod

# 5. Verificacion DB real
psql "$PROD_NEON_URL" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
# esperado: 39

# 6. Smoke test en prod
curl https://api.portfolio.the-full-stack.com/contact ...
psql "$PROD_NEON_URL" -c "SELECT count(*) FROM vis_contacts WHERE email = '<smoke-email>'"
```

## Rollback

Si stage o prod fallan tras la migracion:

1. **Revertir la branch Neon al snapshot anterior** (Neon retiene 7
   dias de history; usar `neonctl branches restore <id>
   --preserve-under-name old-stage`).
2. **Re-actualizar SSM** con la connection string del snapshot.
3. **Las Lambdas redeployadas siguen apuntando al nombre nuevo** — si
   se restaura el schema viejo, las Lambdas fallaran. Hay que tambien
   revertir el deploy de lambdas:
   `git revert <merge-sha>` + redeploy desde el SHA anterior.

Esta es UNA de las razones por las que el deploy es atomico — si algo
sale mal, el rollback completo es mas claro.

## Definition of done (Fase 5)

- [ ] Branch Neon stage reseteada desde dev y migrada al schema nuevo
- [ ] Branch Neon production reseteada desde dev y migrada
- [ ] SSM `/portfolio/stage/neon-url` y `/portfolio/prod/neon-url`
  actualizados
- [ ] Migrate + seed corridos exitosamente en stage y prod
- [ ] Verificacion DB real: 37+2 tablas, alembic_version con la
  revision nueva, cv_endorsements poblado
- [ ] Smoke test en stage: POST /contact verde + fila en `vis_contacts`
- [ ] Smoke test en prod: idem

## Riesgos y mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Branch `production` es PRIMARY del project Neon — borrarlo puede romper conexiones | Crear el nuevo branch con `--primary --default` antes de borrar el viejo, swap atomico via `neonctl` |
| SSM stale durante el reset | Cambiar `/portfolio/prod/neon-url` ANTES del primer cold start del lambda redeployado |
| El seed falla en prod por algun YAML invalido | Probarlo primero en stage (paso 5.1) |
| El connection string del nuevo branch tiene formato distinto | Verificar el SSL mode (`?sslmode=require&channel_binding=require`) |

## Documentar para el futuro

Tras completar la Fase 5, **agregar entrada en
`.claude/rules/neon-management.md`** documentando:

- El project Neon ahora tiene branches: `dev`, `stage`, `production`
  TODAS con el schema renombrado (cv_/vis_/tax_/i18n_).
- Las branches viejas con schema SQL legacy fueron descartadas en
  2026-05-XX como parte del plan `group-tables-by-domain`.
- El runner SQL archivado en `serverless/migrations/_archive/` NO
  aplica mas a ningun entorno.
