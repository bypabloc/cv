# Anexo — Métricas estimadas (para validación del usuario)

[← Verificación E2E](10-verificacion-e2e.md) · [README](README.md)

> Este anexo registra TODAS las cifras inventadas que el plan introduce
> en el CV. Cada entry afectada lleva `metricsEstimated: true` en su YAML
> (campo interno, NO se renderiza). El usuario revisa, corrige o
> reemplaza cada cifra con su dato real antes del merge a `stage`/`main`.

## Por qué existe este anexo

El usuario autorizó (cuestionario P2/P7/P9) generar métricas plausibles
porque no tiene las cifras reales a mano. Riesgo asumido: un reclutador
puede preguntar por una cifra en entrevista. Mitigación:

1. Las cifras son **conservadoras** (rangos defendibles, nunca
   exageradas).
2. Cada entry con cifras inventadas tiene `metricsEstimated: true` — así
   el usuario sabe exactamente qué revisar.
3. Esta tabla centraliza cada cifra: el usuario la valida en un solo
   lugar.

## Estado

Este anexo se completa durante las Fases 3, 4 y 5. Al cerrar el plan
(Commit 9) su contenido se traslada al cuerpo del PR (o a un issue) para
que sobreviva al borrado de la carpeta del plan.

## Tabla — Experiencias (Fase 3)

Las 9 experiencias llevan `metricsEstimated: true`. 18 cifras/rangos. De
ellas: 5 son derivaciones exactas de las fechas `start`/`end` del YAML
(no son invento), 3 reexpresan cifras del texto original, ~10 son rangos
cualitativos conservadores ("de X a Y", tamaños de equipo). Cero
porcentajes agresivos.

| Experiencia | Cifra generada | Justificación | ¿Validada? |
|-------------|----------------|---------------|------------|
| corpoelec | "tres estados / tres sedes" | El YAML ya decía "tres estados del país" | ☐ |
| corpoelec | "varios minutos → consulta inmediata" | Rango cualitativo: papel → query | ☐ |
| ipasme | "varios minutos → consulta inmediata" | Digitalizar fichas físicas → registro consultable | ☐ |
| iai | "~tres personas" (equipo) | Equipo de tesis típico 2-4 personas | ☐ |
| iai | "jornadas manuales → reportes generados" | Reportes automáticos vs consolidación manual | ☐ |
| projects-degrees | "~una semana vs varios meses" | El YAML original ya lo decía | ☐ |
| projects-degrees | "~seis estudiantes" | 2 equipos × ~3 integrantes | ☐ |
| projects-degrees | "de meses a días" | Reexpresión del dato original | ☐ |
| cofasa | "casi dos años" | Fechas: 2017-01 → 2018-11 = ~23 meses | ☐ |
| cofasa | "varias horas → consulta directa" | Reportes de productividad: manual → sistema | ☐ |
| dibal | "1 dev → ~4-6 personas" | "Primer dev contratado" es dato; 4-6 es rango startup | ☐ |
| dibal | "casi tres años" | Fechas: 2018-12 → 2021-09 = ~34 meses | ☐ |
| dibal | "jornadas manuales → pocas horas" (deploy) | AWS ya en el YAML; automatizar deploy | ☐ |
| goodmeal | "iteración a iteración" (Scrum) | Mejora cualitativa de proceso, sin número | ☐ |
| destacame-frontend | "~ocho meses" | Fechas: 2021-12 → 2022-08 = ~8 meses | ☐ |
| destacame-architect | "~4-6 personas" (equipo) | Rango para equipos de plataforma; seniority lead | ☐ |
| destacame-architect | "más de tres años" | Fechas: 2022-08 → presente = ~3 años 9 meses | ☐ |
| destacame-architect | "de horas a minutos" (admin campañas) | El YAML ya describía la automatización | ☐ |

**Adiciones interpretativas a revisar** (el agente las señaló):
- `goodmeal` se enmarcó con ángulo fintech ("flujo de pagos") porque
  procesa pagos y declara el nicho `fintech` — no es un producto fintech
  inventado, es redacción para cubrir el nicho.
- `destacame-architect` se enmarcó con ángulo IA/dev tools porque declara
  el nicho `vibe` — adición interpretativa, sin inventar un proyecto.

## Tabla — Proyectos (Fase 4)

| Proyecto | Métrica (`metrics` key) | Valor generado | Justificación | ¿Validada? |
|----------|-------------------------|----------------|---------------|------------|
| _(a completar en Fase 4)_ | | | | ☐ |

## Tabla — Summaries por nicho (Fase 5)

| Nicho | Afirmación con cifra | Valor generado | Justificación | ¿Validada? |
|-------|----------------------|----------------|---------------|------------|
| _(a completar en Fase 5 si algún summary incluye cifras)_ | | | | ☐ |

## Reglas para completar este anexo

- Una fila por cada cifra concreta inventada (no por cada entry — una
  experiencia puede aportar varias filas).
- "Justificación" explica por qué la cifra es plausible (rol, seniority,
  época, tipo de proyecto). Ej: "rol senior en una fintech con varias
  integraciones bancarias activas — un equipo de 4-6 personas es
  consistente con la escala".
- Si una cifra es un **hecho verificable** (ej. "publicado en VS Code
  Marketplace", "6 apps en el monorepo"), NO va en este anexo y la entry
  NO se marca `metricsEstimated`.
- Toda cifra de este anexo arranca con ¿Validada? = ☐. El usuario la
  marca ✓ cuando confirma o corrige el valor.

## Acción del usuario tras el merge

1. Revisar cada fila de este anexo (trasladado al PR/issue).
2. Para cada cifra: confirmar el valor, o reemplazarlo por el real.
3. Cuando una entry ya no tenga cifras estimadas (todas validadas o
   reemplazadas por datos reales), quitar `metricsEstimated: true` de su
   YAML.
4. Un futuro test puede listar las entries que aún tienen
   `metricsEstimated: true` como recordatorio de deuda pendiente.

[← Verificación E2E](10-verificacion-e2e.md) · [README](README.md)
