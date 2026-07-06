# 05 — Commits (seccion 9)

> [<- 04 Descomposicion](04-descomposicion.md) · [Worktrees ->](06-paralelizacion-worktrees.md)

Secuencia de commits incrementales. Rama de trabajo nueva (NO reusar
`feature/journey-salas-estandar`, que ya esta cerrada salvo su CIERRE
pendiente — ver decision 1 del README). Cada commit deja el repo verde
(typecheck + lint) y ejecuta su verificacion incremental antes de
commitear.

## C1 — carpeta del plan

```text
docs(specs): agrega plan journey-cuaderno-central
```

- Agrega esta carpeta completa (`README.md` + los `.md` de secciones).
- Verificacion: ninguna (solo docs).

## C2 — reposicionar el pilar del cuaderno (T1)

```text
feat(journey): pilar del cuaderno al eje central de transito

- Mueve lecternNotebook de la esquina junto a la puerta al eje x=0,
  cerca de la entrada de cada sala (infoKit, props.ts)
- Agrega collider footprint 1x1 para forzar el rodeo del jugador
- Sin cambios en retos/aprendizajes/grieta ni en el diseño visual del
  pilar
```

- Cubre AC-1, AC-2, AC-3, AC-4, AC-8.
- Verificacion: `pnpm --filter @portfolio/journey typecheck` + recorrido
  visual en 1-2 salas de muestra.

## C3 — despejar entradas: ipasme + iai (T2)

```text
fix(journey): despeja la entrada de ipasme e iai

- Corre los deskSpots que invadian la franja de 2m desde la puerta,
  mismo margen libre que el aula
```

- Cubre AC-6 (ipasme, iai).
- Verificacion: recorrido visual, typecheck.

## C4 — despejar entradas: asesoria + cofasa (T3)

```text
fix(journey): despeja la entrada de asesoria y cofasa

- Corre los deskSpots invasivos hacia +Z
```

- Cubre AC-6 (asesoria, cofasa).

## C5 — despejar entradas: dibal + goodmeal (T4)

```text
fix(journey): despeja la entrada de dibal y goodmeal

- Corre los deskSpots laterales hacia +Z por consistencia con el resto
```

- Cubre AC-6 (dibal, goodmeal).

## C6 — destacame: escritorio + path del NPC valentina (T5)

```text
fix(journey): despeja la entrada de destacame y ajusta el path de valentina

- Corre el deskSpot central que casi coincidia con el eje del pilar
- Ajusta el path de valentina para rodear el pilar sin cruzarlo
```

- Cubre AC-5, AC-6 (destacame).

## C7 — goodmeal: path del NPC daniela (T6)

```text
fix(journey): ajusta el path de daniela en goodmeal para rodear el pilar
```

- Cubre AC-5 (goodmeal). Si T4 y T6 se hicieron en el mismo commit por
  tocar el mismo archivo, fusionar C5 y C7.

## C8 — futuro: verificacion de coexistencia (T7)

```text
fix(journey): ajusta futuro si el pilar del cuaderno choca con el pedestal-CTA
```

- Solo si hubo cambio de codigo; si la verificacion confirma que ya
  coexisten sin conflicto, este commit se omite y T7 se documenta como
  verificado en el commit de cierre (C9).
- Cubre AC-7.

## C9 — verificacion E2E + cierre del plan

```text
docs(specs): cierra plan journey-cuaderno-central
```

- Bateria completa de la seccion 11 en verde.
- `git rm -r docs/specs/journey-cuaderno-central/` (la carpeta es
  efimera).
- Un solo PR de esta rama a `dev`.

## Resumen de secuencia

```text
C1 (docs) -> C2 (helper, base para todo) -> C3, C4, C5, C6, C7 (salas,
  paralelizables entre si respetando la nota de goodmeal T4/T6) -> C8
  (futuro, si aplica) -> C9 (verificacion + cierre)
```
