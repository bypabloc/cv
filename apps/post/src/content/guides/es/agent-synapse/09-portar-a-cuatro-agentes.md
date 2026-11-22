**09**

# Caso de estudio: portar a cuatro agentes

[← Índice](README.md)

---

### El punto de partida

Hasta la 1.6.1, Synapse era un plugin de Claude Code: cuatro scripts que leían el JSON de Claude Code por stdin y respondían con su protocolo (exit 2 para bloquear, `permissionDecision` para preguntar). Al pasar trabajo a Codex, Antigravity u OpenCode, no había ningún control.

### El riesgo de instalarlo sin adaptar

Lo más peligroso no era la falta de cobertura sino la **falsa** cobertura: varios agentes leen manifiestos de Claude Code, cargan los hooks y los ejecutan con otro protocolo.

| Agente | Qué pasaba con los hooks de Claude Code sin adaptar | Severidad |
| :-- | :-- | :-- |
| Antigravity | Todo `exit 2` se ignora y el stdin usa otros nombres: los scripts no encontraban la herramienta y terminaban con `exit 0`. **Todo pasaba** | Crítica |
| Codex | Los bloqueos funcionaban, pero un `ask` o `allow` dejaba el hook como fallido y la herramienta corría. Los patches de `apply_patch` llegaban con campos vacíos | Alta |
| OpenCode | No carga hooks de Claude Code: sin protección | Sin cobertura |

### La arquitectura: núcleo neutral + adaptadores

La lógica de decisión (tokenizar el shell, el alcance git, las firmas de secretos, Laya, la traza) no estaba acoplada a Claude Code. Lo acoplado era solo la entrada, la salida y unas rutas. El port se concentró ahí:

```text
stdin del host ──▶ hosts.normalize() ──▶ HookEvent (tipo: shell | read | write | edit,
                                                   comando, archivos, cwd, proyecto, sesión)
                   lógica actual de cada hook (sin cambios) ──▶ Decision
                   hosts.emit() ──▶ el contrato exacto de cada host
```

| Host | Herramienta de shell | De escritura |
| :-- | :-- | :-- |
| Claude Code | `Bash` | `Write`, `Edit` |
| Codex | `Bash` | `apply_patch` (un patch con varios archivos) |
| Antigravity | `run_command` | `write_to_file`, `replace_file_content` |
| OpenCode | `shell` | `write`, `edit`, `patch` |

Tres principios guiaron el diseño:

1. **El host se declara** en cada manifiesto (`--host codex`), nunca se adivina por la forma del payload.
2. **Ningún host falla abierto por formato.** En Antigravity, un error interno emite `force_ask`, porque ahí un exit distinto de 0 equivale a permitir.
3. **Degradar hacia el lado seguro:** donde un hook no puede preguntar (Codex), el `ask` se emite como `deny` con un id de aprobación.

Para Codex hubo que escribir un parser de `apply_patch` (`patch.py`): un patch puede agregar, actualizar, mover y borrar varios archivos, y cada uno se evalúa por separado. Un archivo protegido rechaza el patch completo nombrando la causa.

### Sin regresiones en Claude Code

Antes de refactorizar, grabé un **golden**: la salida exacta de la 1.6.1 para cada caso de prueba. La 1.7.0 tuvo que reproducirlo byte a byte: 162 casos idénticos, más 17 nuevos. Los fixtures de cada host son payloads reales capturados con una sonda (Codex 0.171.0, agy 1.5.13, OpenCode 2.3.2), y la suite llegó a 1394 tests.

### Lo que no se pudo igualar

- **Codex** no puede preguntar desde un hook ([cap. 10](10-codex-y-windows.md)).
- **Codex** no tiene herramienta de lectura: el bloqueo de `.env` cubre solo comandos de shell.
- **Windows nativo**: el análisis de PowerShell es parcial y Laya no corre.

### En mi caso

La decisión que más valió fue el golden. Durante el refactor cambié la entrada y la salida de los cuatro hooks, y cada vez que algo se movía, el golden lo decía de inmediato. El mismo patrón (núcleo puro y un cableado por host) es el que usé después para portar session-handoff.

`multi-agente` `arquitectura` `caso-de-estudio`
