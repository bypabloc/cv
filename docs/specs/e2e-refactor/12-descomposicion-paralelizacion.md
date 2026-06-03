# 12 — Seccion 8: Descomposicion para paralelizacion

[<- 11 archivos afectados](11-archivos-afectados.md) | [Siguiente: 13 commits ->](13-commits.md)

> Tareas atomicas con sus 6 campos (Archivos, AC, Depende de, Paralelizable
> con, Verify, Done). La eleccion de primitiva + CAPS de concurrencia los
> gobierna [orchestration.md](../../../.claude/rules/orchestration.md):
> **<=4 agentes concurrentes**, **1 workflow a la vez**, Opus 4.8 default.
> NO 1 agente LLM por suite de tests (pytest/lint -> Bash).

## Base secuencial (NO paralelizable — todos dependen)

- **T0 — Fase A (`tests/shared/`)**: porta la maquinaria + `browser.py` +
  config desplegada. Es la base de C/D/E. Un solo agente (toca archivos
  transversales que C/D/E importan).
  - Archivos: `tests/shared/*`, `tests/{conftest,pyproject}.py`, `.gitignore`.
  - AC: AC-8, AC-9. Depende de: —. Verify: imports + unit shared verdes.
- **T1 — Fase B (`devtools/e2e/` + container)**: el orquestador + Docker.
  Depende de T0 (importa `tests.shared`). Un solo agente.
  - Archivos: `devtools/e2e/*`, dockerfiles/compose `e2e`, pyproject deps.
  - AC: AC-4, AC-5, AC-6, AC-7. Depende de: T0. Verify: `e2e --help`, build.

## Ola 1 — modulos (worktree-safe, archivos disjuntos)

Tras T0+T1 commiteados, los 3 modulos tocan carpetas DISJUNTAS:

- **T2 — Fase C (`tests/api/`)**: porta los flows api_e2e.
  - Archivos: `tests/api/*`. AC: AC-1, AC-10, AC-11. Depende de: T0, T1.
  - Paralelizable con: T3, T4. Verify: `e2e --module=api --env=dev` PASS.
- **T3 — Fase D (`tests/admin/`)**: flujos browser completos.
  - Archivos: `tests/admin/*`. AC: AC-2. Depende de: T0, T1.
  - Paralelizable con: T2, T4. Verify: `e2e --module=admin --env=dev` PASS.
- **T4 — Fase E (`tests/app/`)**: las 6 apps.
  - Archivos: `tests/app/*`. AC: AC-3. Depende de: T0, T1.
  - Paralelizable con: T2, T3. Verify: `e2e --module=app --env=dev` PASS.

> Ola de 3 agentes (<=4, dentro del cap). Si se usan worktrees, cada uno en
> su worktree (mutan archivos en paralelo). `isolation: 'worktree'` SOLO
> aqui (T2/T3/T4 escriben). NO read-only.

## Ola 2 — secuencial (depende de que C/D/E esten verdes)

- **T5 — Fase F (eliminacion)**: borra api_e2e/feature/tests-feature +
  actualiza callers (hook, CI, compose, CLAUDE.md, refs). Toca config
  TRANSVERSAL -> NO paralelizable. Un solo agente, DESPUES de T2/T3/T4.
  - Archivos: ver [08](08-fase-eliminacion.md) + [11](11-archivos-afectados.md).
  - AC: AC-12. Depende de: T2, T3, T4. Verify: `rg` sin refs vivas + unit verde.
- **T6 — Fase G (rule + skill)**: documentacion Claude. Puede ir en paralelo
  con T5 (archivos disjuntos: `.claude/` vs el resto), PERO la skill valida
  con `claude -p` que cambia la cuenta gh activa (ver gotcha en memory) —
  preferir secuencial tras T5 para no interferir.
  - Archivos: `.claude/rules/e2e-testing.md`, `.claude/skills/e2e-testing/`,
    CLAUDE.md (seccion skills/rules). AC: AC-13. Depende de: T0-T5.
  - Verify: `claude -p` 5/5 angulos.

## Ola 3 — verificacion final (NO paralelizable)

- **T7 — Fase H (seccion 11)**: bateria completa + curl real + los 3 modulos
  de `e2e` verdes contra dev. Un solo agente / inline. Es el ultimo commit
  (incluye `git rm -r docs/specs/e2e-refactor/`).

## Resumen de olas

```text
T0 (shared) -> T1 (comando+container)        [secuencial, base]
   -> [T2 api | T3 admin | T4 app]            [ola de 3, worktree-safe]
   -> T5 (eliminacion)                        [secuencial, transversal]
   -> T6 (rule+skill)                         [secuencial, claude -p]
   -> T7 (verificacion final + rm spec)       [secuencial, gate]
```

## Eleccion de primitiva (orchestration.md)

- T0, T1, T5, T6, T7: **inline o 1 subagente** (transversales/secuenciales).
- T2/T3/T4: **ola de 3 subagentes** (Opus 4.8), `isolation: 'worktree'` si
  se ejecutan en paralelo real. Cada uno corre SU pytest via Bash (no 1
  agente por test — la verificacion es determinista).
- NUNCA un workflow para "documentar/diagnosticar" el refactor (re-provoca
  rate-limit). Si se usa un workflow para T2/T3/T4, **1 workflow a la vez**,
  **olas de <=4**.

## Granularidad

7 tareas (T0-T7) para un plan Large que toca ~40 archivos. Cada tarea pasa
los 3 checks: File Exclusivity (T2/T3/T4 disjuntas), Interface Stability
(T0/T1 estabilizan `tests.shared` + `e2e` antes de la ola), Bounded Scope
(una fase = una tarea).

[<- 11 archivos afectados](11-archivos-afectados.md) | [Siguiente: 13 commits ->](13-commits.md)
