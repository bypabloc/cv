**12**

# Problemas, mitos y lo que se midió

[← Índice](README.md)

---

### Problemas y soluciones

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| Codex se queda esperando tras un `deny` | Un `ask` en Codex es un `deny` con id | `synapse.py approve <id>` en tu terminal; si es rutina, declárala en `routine_commands` |
| Codex dejó de aplicar los hooks tras actualizar | La confianza se ata al hash de los scripts | Re-aprobar en `/hooks` y reiniciar las sesiones |
| `PreToolUse:… hook failed` en Windows | `python3` resuelve al acceso directo de la tienda | Synapse ≥ 1.7.2 (usa `run-hook.cmd`) o `SYNAPSE_PYTHON` |
| Mensajes con caracteres rotos en Windows | Salida en cp1252 | Synapse ≥ 1.7.1; en scripts propios, `PYTHONUTF8=1` |
| Un comando de tu CLI pide confirmación siempre | No está en la rutina | Agregar el prefijo a `.synapse/commands.json` |
| El agente no puede leer un `.env` | Es lo esperado | Usar el esquema ofuscado o extraer la variable en el mismo comando que la usa |
| Un worktree aparece "fuera del proyecto" | Versión anterior a 1.2.0 | Actualizar: la raíz se calcula desde git |
| Laya no arranca | Falta el delta LFS, PyTorch o la GPU; o es Windows nativo | `synapse.py doctor`; sin Laya, Synapse sigue con reglas |
| Un hook falla en silencio en Codex | Un hook declarado a mano apunta a un clon borrado | Quitarlo de la configuración del usuario; instalar el plugin desde el marketplace |

### Afirmaciones que resultaron falsas

| Afirmación | Realidad |
| :-- | :-- |
| "Un clasificador neuronal es más seguro que unas regex" | En la traza real, todo lo peligroso lo detuvieron las reglas; los 24 `ask` de Laya fueron falsos positivos |
| "Si el agente sigue avanzando, los hooks funcionan" | Un hook que falla no bloquea: en Windows, Synapse no revisaba nada y la sesión parecía normal |
| "Instalar el plugin de Claude Code en otro agente lo protege igual" | En Antigravity, sin adaptar, todo pasaba; en Codex, cada `ask` dejaba correr la herramienta |
| "Proteger `AGENTS.md` y las reglas en Markdown aumenta la seguridad" | Son instrucciones, no permisos; protegerlas solo genera esperas (y en Codex, horas) |
| "Un modelo reentrenado con más datos siempre mejora" | El delta reentrenado con la traza perdió recall (0,772 → 0,757) y no se publicó |

### Lo que se midió

| Medición | Resultado |
| :-- | :-- |
| Costo por comando solo con reglas | ~8 ms (el bloqueo del ejemplo del cap. 07: 7,6 ms) |
| Costo por comando con Laya (traza real) | ~205 ms |
| Latencia de Laya, en proceso frente a daemon | ~6 s frente a ~70 ms |
| Laya afinada | FPR 0,15–0,29 %, recall 78–81 % |
| Port multi-agente | 162 casos del golden idénticos, 1394 tests |

### Lo que no hace

- **No es un sandbox.** Revisa lo que el agente pide hacer; no aísla procesos ni la red. Súmalo a los sandboxes nativos ([cap. 06](06-configurar-por-proyecto.md)).
- **No ve todo lo que corre un comando.** Un script versionado del proyecto se trata como rutina: lo que haga por dentro queda bajo tu responsabilidad.
- **No reemplaza la revisión del código.** Que un cambio no tenga secretos no significa que sea correcto.
- **No cubre agentes sin hooks previos a las herramientas.**

### Riesgos que conviene tener presentes

- Cada excepción por proyecto (rutinas, contraseñas permitidas) amplía lo que pasa sin revisión: mantenlas cortas y versionadas.
- Un guardrail con muchos falsos positivos termina desactivado. Es mejor un `ask` justificado que diez de rutina.
- Las APIs de hooks de los agentes cambian rápido: fija versiones mínimas y vuelve a capturar sus payloads al actualizar.

`troubleshooting` `mediciones` `mitos` `seguridad`
