# 10. Paralelización con git worktrees

## Por qué este plan es mayormente secuencial

El pipeline Blender (`T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11`) es una
cadena de dependencias real: cada etapa consume el `.blend`/`.glb` de la
anterior (no se puede riggear antes de tener la malla, ni animar antes
de riggear, ni exportar antes de animar). No hay valor en paralelizar
esa cadena con worktrees — sería trabajo desperdiciado esperando el
mismo archivo.

## Base secuencial

Todo el pipeline Blender (T4-T11) + la validación final (T13) es la
base secuencial. Un solo "hilo" de trabajo (agente o desarrollador) lo
recorre en orden.

## Puntos SÍ paralelizables (worktree-safe)

| Tareas | Por qué son disjuntas | Cómo lanzar |
|--------|------------------------|-------------|
| T1 (scaffold `apps/journey-realistic`) + T2 (scaffold `devtools/npc_pipeline`) | Archivos completamente distintos (`apps/journey-realistic/**` vs `devtools/npc_pipeline/**`), sin dependencia mutua | 2 agentes en paralelo (o 1 worktree cada uno si van a mutar simultáneamente); dado el tamaño chico de ambas tareas, en la práctica alcanza con 2 llamadas de `Agent` sin `isolation: 'worktree'` — no hay colisión real de archivos que lo justifique |
| T3 (setup manual de Blender) | No es código, es una acción local del dev | Corre en paralelo a T1/T2, sin agente |
| T12 (documentar licencias) | Solo lee/escribe `README.md`/un archivo de licencias, no toca ningún archivo de T5-T11 | Puede correr en paralelo a T5-T11 una vez T4 confirmó qué versión de MPFB2/Rigify se usó |

## Qué NO se paraleliza

- El pipeline Blender en sí (T4-T11): secuencial por dependencia real de
  datos, no por convención del proyecto.
- T9 (`character.ts`) depende de T1 Y T8: no puede empezar antes de que
  ambas terminen.
- La sección 09-verificacion-e2e.md (T13): siempre la última, cierra el
  plan.

## Nota sobre concurrencia

Dado que casi todo el plan es secuencial, este plan **no requiere**
`isolation: 'worktree'` de forma sustancial — el único momento de
paralelismo real (T1+T2) es tan chico que ni siquiera amerita el costo
de un worktree (~200-500ms + disco), basta con 2 llamadas de agente
normales corriendo a la vez. Ver
[.claude/rules/orchestration.md](../../../.claude/rules/orchestration.md)
para el criterio general de cuándo sí vale un worktree (mutación
concurrente de archivos que colisionarían).
