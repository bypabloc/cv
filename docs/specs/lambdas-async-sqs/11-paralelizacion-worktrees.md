# 11 — Paralelizacion con git worktrees (seccion 10)

> Desde que commit se puede paralelizar la implementacion con git worktrees
> o subagentes concurrentes, y que fases son worktree-safe.

[< 10](10-commits.md) | [Siguiente: 12 — Verificacion E2E >](12-verificacion-e2e.md)

---

## Base secuencial (rama `feature/lambdas-async-sqs`)

Los siguientes commits son **base secuencial** — todos los worktrees los
necesitan o tocan archivos transversales. Se ejecutan en orden, en la
rama principal, antes de lanzar cualquier worktree:

```text
Commit 1  docs plan                            (sin codigo)
Commit 2  YAMLs resources/sqs + cloudwatch     (sin codigo de devtools)
Commit 3  devtools: redrive + visibility       BASE — modifica infra_provision.py
Commit 4  devtools: cloudwatch-alarm           BASE — modifica infra_provision.py
Commit 5  provision-infra dev                  OPERATIVO — no modifica repo
Commit 6  devtools: trigger.type=sqs + uses.q  BASE — modifica provisioner.py
Commit 7  shared/queue (publisher)             BASE — nuevo subpaquete shared
Commit 8  shared/db: insert_*_idempotent       BASE — modifica shared/db
   |
   +--- desde aqui se lanzan worktrees ---
```

**Razon de cada base**:

- C3, C4, C6: tocan `devtools/serverless/{infra_provision,provisioner}.py`
  — son los pilares del provisioning. Toda fase paralela posterior asume
  que estan disponibles.
- C7: crea `shared/queue/` — los encoders (C11, C12) lo importan.
- C8: agrega helpers idempotentes a `shared/db/repository.py` — los
  workers (C9, C10) los usan.
- C5: provisiona AWS (no toca repo) — necesario porque los deploys
  posteriores requieren las colas creadas.

## Fase paralelizable (worktrees, lanzables tras commit 8)

Tras la base, los siguientes 4 commits tocan archivos disjuntos y se
pueden ejecutar en paralelo via git worktrees o subagentes:

| Worktree | Commit | Archivos creados | Archivos modificados | Colision |
|----------|--------|------------------|----------------------|----------|
| WT-A | C9  (contact_worker) | `services/contact_worker/**` | ninguno | — |
| WT-B | C10 (tracking_worker) | `services/tracking_worker/**` | ninguno | — |
| WT-C | C11 (encoder contact_form) | tests nuevos | `services/contact_form/**` | — |
| WT-D | C12 (encoder tracking_pixel) | tests nuevos | `services/tracking_pixel/**` | — |

**Comprobacion de file exclusivity**:

- WT-A escribe SOLO en `services/contact_worker/` (carpeta nueva).
- WT-B escribe SOLO en `services/tracking_worker/` (carpeta nueva).
- WT-C escribe SOLO en `services/contact_form/` (existente — no se solapa
  con WT-A ni WT-D).
- WT-D escribe SOLO en `services/tracking_pixel/` (existente — no se
  solapa con WT-B ni WT-C).

**Cero colisiones**: cada worktree opera sobre una carpeta diferente.
Los `pyproject.toml` agregan `shared.queue` y `shared.db` (en WT-C/D) pero
esos modulos ya existen tras la base, son solo declaraciones en
`internal-deps`.

## Fase secuencial final (rama principal)

Tras integrar los 4 worktrees a `feature/lambdas-async-sqs`:

```text
Integracion: merge WT-A -> WT-B -> WT-C -> WT-D       (cualquier orden, los archivos son disjuntos)
Commit 13  deploy workers dev (operativo)             requiere los 4 worktrees integrados
Commit 14  redeploy encoders dev (operativo)          requiere los 4 worktrees integrados
Commit 15  verificacion E2E + cleanup spec            ULTIMO commit del plan
```

Estos NO se paralelizan:

- C13/C14 son comandos AWS que mutan el cluster — secuenciales por
  definicion (deploy en paralelo confunde el debugging).
- C15 es la verificacion E2E con todo integrado — depende de TODO lo
  anterior.

## Maximo paralelismo util

**4 worktrees concurrentes** (WT-A, WT-B, WT-C, WT-D). Mas no aporta
porque la base secuencial ocupa los primeros 8 commits y la integracion
final requiere serializarlos.

Si quien implementa es 1 humano + Claude, recomendado:
- Hacer C1-C8 secuencial (la base).
- Hacer C9-C12 en paralelo con 2-3 subagentes (no 4 — el revisor humano
  satura).
- Hacer C13-C15 secuencial.

## Como lanzar un worktree

### Manual (humano)

```bash
# desde la raiz, con la base secuencial ya commiteada (commit 8 listo)
git worktree add ../portfolio-wt-contact-worker feature/lambdas-async-sqs
cd ../portfolio-wt-contact-worker
git checkout -b feature/lambdas-async-sqs-contact-worker

# Implementar el commit C9 segun docs/specs/lambdas-async-sqs/05-contact-worker.md
# ...
git add services/contact_worker/
git commit -m "feat(contact_worker): nuevo Lambda worker para SQS contact-form"

# Al integrar:
cd ../portfolio
git merge --no-ff feature/lambdas-async-sqs-contact-worker
git worktree remove ../portfolio-wt-contact-worker
git branch -d feature/lambdas-async-sqs-contact-worker
```

### Subagente Claude

Usar `Agent` con `isolation: "worktree"`:

```python
Agent(
    description="Implementar contact_worker (WT-A)",
    subagent_type="general-purpose",
    isolation="worktree",
    prompt="""
    Implementa el Lambda contact_worker SIGUIENDO ESTRICTAMENTE la spec
    docs/specs/lambdas-async-sqs/05-contact-worker.md. NO te desvies del
    diseno.

    Cuando termines, deja todo verde:
      cd serverless/lambda/services/contact_worker
      ../../.venv/bin/python -m pytest tests/unit -v
      ../../.venv/bin/python -m pytest tests/integration -v   # si Neon esta disponible

    Hace UN solo commit:
      feat(contact_worker): nuevo Lambda worker para SQS contact-form

    NO toques nada fuera de serverless/lambda/services/contact_worker/.
    Reporta al final el path del worktree + el hash del commit creado.
    """
)
```

Lanzar los 4 worktrees en paralelo (1 sola tool call con multiples Agent):

```python
# En el mismo turno, paralelamente:
Agent(description="WT-A contact_worker", isolation="worktree", prompt="...")
Agent(description="WT-B tracking_worker", isolation="worktree", prompt="...")
Agent(description="WT-C encoder contact_form", isolation="worktree", prompt="...")
Agent(description="WT-D encoder tracking_pixel", isolation="worktree", prompt="...")
```

Al regresar los 4, integrar en orden (cualquier orden funciona — archivos
disjuntos).

## Reglas al integrar worktrees

- **SIEMPRE** integrar UNO a la vez (no `git merge octopus`). Despues de
  cada merge correr `serverless tests --type=unit` del lambda integrado.
- **SIEMPRE** verificar `git diff origin/dev...HEAD` despues de integrar
  todos los worktrees para ver el alcance total antes de los commits
  operativos (C13/C14).
- **SIEMPRE** los cambios menores en archivos transversales que un
  worktree pudiera necesitar (ej. registrar el nuevo Lambda en algun
  index global) se aplican AL INTEGRAR (en commits separados de la rama
  principal), NO dentro del worktree — eso seria colision.
- **NUNCA** un worktree edita archivos fuera de su scope declarado.
- **NUNCA** se lanza un worktree antes de que toda la base secuencial
  (commits 1-8) este completa y testeada.

## Anti-patrones de worktrees

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Lanzar WT-A antes de commit 7 (shared/queue) | El encoder importa el helper que aun no existe | Esperar a commit 8 |
| WT-C modifica `shared/db/repository.py` para "ajustar" | Colision con commit 8 y posibles otros WTs | El commit 8 ya cubre eso |
| 6 worktrees concurrentes | Overhead de review + integracion satura | Max 4 |
| Worktree que toca `manifest.yaml` de otro Lambda | Colision con su propio WT | Solo su carpeta |
| Hacer `git push` desde el worktree | Antes de integrar puede confundir CI | Integrar primero, push al final |
| Olvidar `git worktree remove` despues de integrar | Acumula directorios fantasma | Cleanup obligatorio |

## Checklist de seguridad antes de lanzar paralelo

- [ ] Base secuencial (commits 1-8) en `feature/lambdas-async-sqs` con
  todos los tests verdes.
- [ ] `serverless provision-infra --stage=dev --aws-profile=tfs-dev`
  ejecutado y exitoso (commit 5 hecho).
- [ ] Las 4 colas SQS visibles con `aws sqs list-queues --profile tfs-dev`.
- [ ] `shared/queue/.venv/bin/pytest tests/` verde.
- [ ] `shared/db` tests idempotentes verdes.
- [ ] No hay cambios sin commitear en la rama principal (`git status`).

Recien entonces lanzar los 4 worktrees.

---

[< 10](10-commits.md) | [Siguiente: 12 — Verificacion E2E >](12-verificacion-e2e.md)
