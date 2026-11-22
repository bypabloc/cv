**11**

# Probar, actualizar y vigilar

[← Índice](README.md)

---

### Las pruebas

```bash
claude plugin validate --strict .   # manifiesto
python3 -m pytest                   # todo, solo reglas deterministas (~40 s)
python3 -m pytest --laya gpu        # con Laya en CUDA (--laya cpu para CPU)
python3 -m pytest tests/e2e         # solo el pipeline completo desde hooks.json
```

| Carpeta | Qué guarda |
| :-- | :-- |
| `tests/cases/<hook>.json` | Casos declarativos: payload → decisión, exit y stderr esperados |
| `tests/unit/` | Un módulo por hook y por regla compartida |
| `tests/golden/` | La salida exacta de Claude Code que ningún cambio puede alterar |
| `tests/fixtures/<host>/` | Payloads reales de cada agente, por sistema operativo y versión |
| `tests/e2e/` | Los hooks reales, y los CLI de cada agente cuando están instalados |

### Agregar un caso

Basta con sumar una entrada al JSON del hook. Cada falso positivo se fija con dos casos: el que fallaba y uno parecido que debe seguir decidiéndose igual. Por ejemplo, `pass_agent_wrapper_help_runs_no_agent` (`codex exec --help` pasa) junto a un `codex exec 'prompt'` que sigue en `ask`. Un caso nuevo debe fallar antes del cambio.

### Actualizar tras un release

| Agente | Cómo |
| :-- | :-- |
| Claude Code | `claude plugin marketplace update bypabloc-agents && claude plugin update synapse@bypabloc-agents`; `/reload-plugins` en las sesiones abiertas |
| Codex | `codex plugin marketplace upgrade` y luego `/hooks` para volver a confiar; reinicia las sesiones abiertas |
| Antigravity | Repetir `agy plugin install https://github.com/bypabloc/agent-plugin-synapse` |
| OpenCode | Con una versión fijada (`#vX.Y.Z`), cambiar la referencia; con `#main`, se actualiza al arrancar |

### Vigilar en sesiones reales

Un guardrail que nadie mira se degrada en silencio. La rutina que uso:

1. Revisar la traza de los últimos días: `ask` y `block` nuevos, y su `decided_by`.
2. Buscar hooks fallidos en los logs del agente, aunque la sesión haya seguido.
3. Confirmar la versión instalada en cada agente y perfil.
4. Cada hallazgo se repara con un caso que lo reproduce, una versión nueva y una entrada en la bitácora: síntoma, causa, cambio, prueba y lección.

### En mi caso

El monorepo tiene un colector de vigilancia que recorre las trazas de Windows y WSL en modo solo lectura, y un flujo fijo para reparar: worktree, caso que falla, fix, PR a `dev` y a `main`, tag de versión y actualización de todas las instalaciones. La regla es que una reparación no termina hasta que está publicada e instalada en todos los agentes; si no, la siguiente sesión vuelve a tropezar con el mismo fallo.

`tests` `release` `vigilancia`
