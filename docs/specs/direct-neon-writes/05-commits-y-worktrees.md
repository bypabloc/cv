# Commits + paralelizacion con worktrees

[Volver al README](README.md)

## Lista de commits (7 commits, en orden)

1. **`docs(specs): plan direct-neon-writes`**
   - Crea `docs/specs/direct-neon-writes/` con los 6 archivos del spec
   - Verify: typecheck no aplica (solo markdown)

2. **`refactor(tracking_pixel): escritura directa a Neon con ON CONFLICT`**
   - `core/services/tracking_service.py`: insert_tracking en vez de PutItem DDB
   - `manifest.yaml`: -table `tracking`, +secret `neon-url`
   - `pyproject.toml`: +psycopg si no esta heredado
   - Tests unit + integration actualizados
   - Verify: `serverless tests --type=unit --lambda=tracking_pixel`
   - Cubre: AC-1, AC-3, T-1.1, T-1.2, T-1.3

3. **`refactor(contact_form): escritura directa a Neon con idempotency_key`**
   - Mismo patron que tracking_pixel
   - `models/contact.py`: campo `idempotency_key: UUID | None`
   - `contact_service`: idempotencia previene email duplicado
   - Verify: `serverless tests --type=unit --lambda=contact_form`
   - Cubre: AC-2, AC-3, T-2.1, T-2.2, T-2.3, T-2.4

4. **`chore(serverless): eliminar lambda stream_processor`**
   - `git rm -r serverless/lambda/services/stream_processor/`
   - Borrar `shared/db/models/stream.py`
   - Borrar `is_event_processed`, `mark_event_processed` de repository
   - Verify: `rg stream_processor` -> 0 matches; tests de los 3 lambdas restantes verdes
   - Cubre: AC-4 (parcial)

5. **`feat(db): migration alembic drop processed_stream_events`**
   - Nueva migration en `shared/db/alembic/versions/`
   - Probado upgrade + downgrade + upgrade en branch Neon
   - Verify: `alembic current` muestra la nueva revision

6. **`chore(serverless): eliminar recursos DDB contacts/tracking + DLQ + on-table-changes provisioner`**
   - `git rm` los 3 YAMLs de resources
   - Borrar `_TABLES.contacts`, `_TABLES.tracking`, `_VALID_TRIGGERS on-table-changes`, `_wire_table_changes_trigger` del provisioner
   - Borrar tests del provisioner relacionados
   - Verify: `python devtools/run.py test_runner --module=devtools --type=unit`
   - Cubre: AC-4 (resto), AC-5 (parcial — solo el codigo, la infra en Phase 5)

7. **`test(e2e): verificacion direct-to-neon dev/stage/prod + cleanup spec`**
   - Es la fase 5 (verificacion E2E). Incluye los pasos manuales documentados.
   - `git rm -r docs/specs/direct-neon-writes/`
   - Verify: [06-verificacion-e2e.md](06-verificacion-e2e.md) bateria completa
   - Cubre: AC-1 a AC-7 end-to-end

## Cada commit deja el repo verde

Cada commit corre su verify ANTES de commitear. No se difiere al final. Si un commit deja el repo rojo, se corrige ANTES de pasar al siguiente.

## PR

Uno solo: `feature/direct-neon-writes -> dev` con merge commit. Tras merge:
- CI/CD deploya el codigo a dev
- Yo ejecuto manualmente los `aws ... delete-*` para limpiar la infra vieja (documentado en Phase 5)
- Promover a stage cuando dev verifica OK
- Promover a prod cuando stage verifica OK

## Paralelizacion con git worktrees

Phases 1 y 2 son archivos disjuntos (distintos lambdas). Worktree-safe:

```bash
# Worktree para Phase 1
git worktree add ../portfolio-phase-1 feature/direct-neon-writes
cd ../portfolio-phase-1
# Trabaja en serverless/lambda/services/tracking_pixel/...

# En otra sesion / agente:
git worktree add ../portfolio-phase-2 feature/direct-neon-writes
cd ../portfolio-phase-2
# Trabaja en serverless/lambda/services/contact_form/...
```

**Base secuencial** (NO paraleliza): commit 1 (spec) tiene que existir antes que Phase 1/2 comiencen, asi ambos tienen el contexto.

**No worktree-safe** (siempre serial):
- Commit 4 (eliminar stream_processor) — depende de 2 y 3
- Commit 5 (migration) — toca el alembic, modifica `versions/`
- Commit 6 (eliminar recursos + provisioner) — toca config compartida
- Commit 7 (verify + cleanup) — gate de cierre

Si trabajo solo (probable), ejecuto serial. La descomposicion sigue siendo util para review (cada commit es un cambio coherente).
