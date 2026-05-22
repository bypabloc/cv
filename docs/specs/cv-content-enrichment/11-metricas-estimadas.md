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

| Experiencia | Cifra generada | Texto del logro | Justificación | ¿Validada? |
|-------------|----------------|-----------------|---------------|------------|
| _(a completar en Fase 3)_ | | | | ☐ |

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
