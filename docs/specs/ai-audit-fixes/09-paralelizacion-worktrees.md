# 09 - Paralelizacion worktrees

[< 08 Commits](08-commits.md) | [10 Verificacion E2E >](10-verificacion-e2e.md)

## Base secuencial obligatoria

El commit #2 (`feat(packages/seo): builders + buildHeaders`) DEBE
hacerse PRIMERO antes de poder paralelizar nada. Razon: el commit
#5 (`apps prebuild scripts`) y el #6 (`app-shared JSON-LD`)
**importan** las funciones que aporta el #2. Sin el #2, los
imports fallan.

Igual el commit #4 (`devtools validator`) es independiente — puede
correr en paralelo con cualquier otro.

## Tabla de paralelizabilidad

Tras el commit #2 + #3:

| Tarea | Tras commit | Paralelizable con | Archivos exclusivos? |
|-------|-------------|-------------------|----------------------|
| #3 fix(ui) tokens | tras #2 | #4 | si (packages/ui solo) |
| #4 feat(devtools) | tras #1 | #2, #3, #5, #6 | si (devtools/ solo) |
| #5 feat(apps) prebuild | tras #2 | #6 | si (apps/*/scripts/ solo) |
| #6 feat(app-shared) | tras #2 | #5 | si (packages/app-shared/ solo) |
| #7 test(claude) | tras #6 | #8 | si (no toca codigo) |

## Plan de ejecucion

Dado el scope (pocos archivos por fase, ningun import cross), NO
amerita git worktrees. Mas simple ejecutarlos en serie:

```text
1 (HECHO) -> 2 -> {3, 4 en paralelo} -> {5, 6 en paralelo} -> 7 -> 8
```

Si se quisiera paralelizar 3+4 o 5+6 con worktrees:

```bash
# Crear worktree para tarea #4 (devtools, independiente de #2)
git worktree add ../portfolio-devtools-validator feature/ai-audit-devtools
cd ../portfolio-devtools-validator
# trabajar la fase 3 ahi
```

Pero el overhead de cambiar de directorio no compensa: cada fase
es ~30 min de trabajo + tests rapidos.

## Conclusion

Ejecucion secuencial en la rama `feature/ai-audit-devtools`. Sin
worktrees para este plan.

[< 08 Commits](08-commits.md) | [10 Verificacion E2E >](10-verificacion-e2e.md)
