# 9. Commits

Un PR local `feature/journey-spiderverse-style` (sin push hasta
validación del dueño, decisión no-reabrible 6). Cada commit deja el repo
verde (lint + typecheck del scope) y referencia su AC.

1. `docs(specs): agrega plan journey-spiderverse-style` — esta carpeta.
   AC: N/A (documentación).
2. `feat(journey): agrega loaders GLTF/Draco/KTX2 + fix CSP workers` — T1.
   AC-1, AC-2. Verify: `pnpm --filter @portfolio/journey run build`.
3. `feat(journey): agrega postprocesado halftone/aberracion/outline` — T2.
   AC-3. Verify: smoke visual dev server.
4. `feat(journey): personajes migran a modelos riggeados CC0` — T3.
   AC-4, AC-5. Verify: smoke visual + `pnpm exec tsc --noEmit`.
5. `feat(journey): sala aula migra a assets CC0 estilo Spider-Verse` — T4a.
   AC-6, AC-7.
6. `feat(journey): sala futuro migra a assets CC0 estilo Spider-Verse` — T4b.
   AC-6, AC-7.
7. `feat(journey): sala destacame migra a assets CC0 estilo Spider-Verse` — T4c.
   AC-6, AC-7.
8. `docs(journey): agrega creditos de licencias de assets CC0` — T5. AC-8.
9. `docs(progress): verificacion E2E journey-spiderverse-style + elimina
   carpeta del plan` — T6, incluye `git rm -r docs/specs/journey-spiderverse-style/`
   solo cuando el plan se dé por cerrado (si el dueño pide iterar más,
   este commit se pospone). AC-9.

Sin push/PR real hasta que el dueño confirme visualmente (decisión
no-reabrible 6) — estos commits quedan locales en la rama de trabajo.
