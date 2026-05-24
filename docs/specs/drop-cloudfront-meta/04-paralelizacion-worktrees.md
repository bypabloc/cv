# 04 — Paralelizacion con git worktrees

[← 03-commits.md](03-commits.md) | [05-verificacion-e2e.md →](05-verificacion-e2e.md)

## 10. Paralelizacion

`N/A — cambio secuencial.`

### Razon

El plan tiene 7 commits que dependen linealmente uno del otro:

```text
commit 1 (plan)
   ↓
commit 2 (migracion alembic)
   ↓ define el schema-target
commit 3 (modelos SQLAlchemy)
   ↓ deben matchear la migracion
commit 4 (tracking_pixel service+controller)
   ↓ usan los modelos actualizados
commit 5 (contact_form service+model)
   ↓ idem
commit 6 (unit tests)
   ↓ los tests se rompen sin los commits 3-5
commit 7 (cleanup + bateria E2E)
```

No hay archivos disjuntos paralelizables:

- Los modelos SQLAlchemy bloquean los services (los services importan
  desde `shared.db`).
- Las dos Lambdas (tracking_pixel, contact_form) **podrian** trabajarse
  en paralelo (touching `services/tracking_pixel/` vs
  `services/contact_form/`), pero el ahorro es marginal (~6 lineas
  totales modificadas en cada Lambda) y agrega ceremonia de worktrees +
  rebases.
- El commit 7 ejecuta la bateria de la seccion 11 sobre el codigo
  consolidado y debe ser estrictamente el ultimo.

### Granularidad

7 commits secuenciales, escala **Small/Medium**. Si en una iteracion
futura se decide eliminar tambien el helper + Pydantic fields (revertir
la decision 3), eso justificaria una fase paralela: tracking_pixel
model + contact_form model + http_dispatch + helper en worktrees
disjuntos. Pero NO es el scope actual.

### Anti-patron a evitar

No abrir worktrees concurrentes solo "por consistencia con el
plan-format". El plan-format permite explicitamente `N/A` cuando el
cambio es secuencial por construccion. Forzar paralelismo aqui solo
agrega rebase noise.

---

[← 03-commits.md](03-commits.md) | [05-verificacion-e2e.md →](05-verificacion-e2e.md)
