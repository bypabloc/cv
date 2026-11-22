**08**

# Laya: un clasificador que solo puede preguntar

[← Índice](README.md)

---

### Qué es

[Laya](https://github.com/convaiinnovations/laya) es un modelo liviano de clasificación (un "System 1": decide rápido, sin generar texto). Synapse lo usa para lo que las reglas no resuelven: un comando ambiguo, una línea que podría ser un secreto. Corre en local, en GPU si hay CUDA o en CPU, sin llamadas a ninguna API.

Dos reglas de diseño lo acotan:

1. **Laya nunca bloquea:** como mucho, escala a `ask`. Un clasificador con falsos positivos no puede tener la última palabra.
2. **Solo ve lo ambiguo:** todo lo que una regla puede decidir se decide antes, con reglas.

### Cómo se afinó

| Versión | Cambio | Resultado medido |
| :-- | :-- | :-- |
| 1.0.0 | Laya zero-shot sobre el texto del comando | FPR de 3,8 % en comandos reales; recall de 5,7 % en los riesgosos de ShellRisk-Bench **[medido]** |
| 1.1.0 | Pregunta binaria sobre un **resumen de evidencia** (qué borra, escribe, lee o envía), delta afinado y calibración | FPR de 0,29 %, recall de 78 % **[medido]** |
| 1.2.0 | Daemon persistente en un socket Unix y compuerta determinista antes del modelo | De ~6 s a ~70 ms por hook; FPR de 0,15 %, recall de 81,35 %, 28 % menos consultas **[medido]** |

La lección de la 1.1.0: al clasificador se le da evidencia estructurada, no el texto crudo. Si el modelo da un score alto con evidencia neutra, está reaccionando al vocabulario, y eso se arregla con una regla, no subiendo el umbral.

### Por qué viene apagado

En la traza real de un proyecto, entre octubre y noviembre de 2026 **[medido]**:

| Medición | Valor |
| :-- | :-- |
| Consultas a Laya en `block_dangerous` | ~20 mil |
| Costo por comando | ~205 ms con Laya, ~8 ms solo con reglas |
| Confirmaciones pedidas por Laya | 24 |
| De esas, falsos positivos | **24** (`bun run typecheck`, `git worktree list`, `pdfinfo`, …) |

Todo lo peligroso de ese período lo detuvieron las reglas deterministas. Así que en la 1.6.0 Laya pasó a estar apagada por defecto, y sus falsos positivos se convirtieron en reglas de rutina. También se reentrenó el delta con esa traza, pero no se publicó: el recall bajó de 0,772 a 0,757, y un modelo que pierde recall no se publica.

### Cuándo encenderla

Tiene sentido si trabajas con comandos poco comunes que las reglas no cubren, o si quieres una segunda opinión en los hooks de secretos. Se enciende desde el `env` de la configuración del agente:

```jsonc
{ "env": { "SYNAPSE_LAYA": "on" } }                     // todos los hooks
{ "env": { "SYNAPSE_LAYA_HOOKS": "block_dangerous" } }  // solo ese hook
{ "env": { "SYNAPSE_LAYA": "off" } }                    // apagada aunque haya lista
```

Requisitos: el delta del modelo (~100 MB, viene por Git LFS), PyTorch y, para que sea rápido, una GPU con CUDA. El daemon arranca con la primera consulta y se apaga tras 20 minutos sin uso para liberar la VRAM. Si no arranca a tiempo, ese hook sigue solo con reglas. No corre en Windows nativo.

### En mi caso

Laya fue lo que me dio confianza para soltarle la mano al agente al principio: mientras las reglas eran pocas, el clasificador atrapaba lo raro y yo dormía tranquilo con corridas autónomas en marcha. Con semanas de traza, las reglas aprendieron lo que Laya marcaba y el modelo dejó de aportar. Hoy queda apagado por defecto, y el trabajo lo hacen las reglas que salieron de su traza.

`laya` `clasificador` `gpu` `mediciones`
