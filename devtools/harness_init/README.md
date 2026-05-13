# harness_init — Gate BLOQUEANTE de inicio (Harness Engineering)

Wrapper Python sobre `.claude/hooks/harness-init.sh`. Verifica que el entorno
del arnes (Harness Engineering) este listo para empezar a trabajar.

## Uso

```bash
# Modo normal (muestra [OK] / [WARN] / [FAIL])
python devtools/run.py harness_init

# Modo silencioso (solo [WARN] y [FAIL])
python devtools/run.py harness_init --quiet

# Invocacion directa del shell hook (equivalente)
./.claude/hooks/harness-init.sh
```

## Que verifica

1. **Archivos base** — `docs/CHECKPOINTS.md`, `docs/progress/current.md`,
   `docs/progress/history.md`, `CLAUDE.md`, `.claude/settings.json`
2. **`feature_list.json` por modulo** — recorre
   `docs/<modulo>/feature_list.json` (landing, dashboard, server,
   marketplace, cross). JSON valido y respeta `one_feature_at_a_time` por
   modulo. Si un modulo no tiene archivo, no es error (solo aviso).
3. **Docker** — daemon corriendo y containers principales up
4. **Branch** — la actual no debe ser protegida (master/dev/release)
5. **`docs/progress/`** — limpio, sin temporales viejos de subagentes

## Cuando usarlo

- Al iniciar una sesion de trabajo no trivial (Medium/Large)
- Despues de un `git checkout` a una rama donde no recordas el estado
- Antes de lanzar subagentes pesados (researcher, code-reviewer)
- Como gate previo a invocar `/ship` o `/autopilot`

## Exit codes

| Code | Significado |
|------|-------------|
| `0`  | Todo OK — puedes empezar a trabajar |
| `1`  | Algo critico fallo — NO trabajar antes de resolver |

## Relacion con otros componentes

- Logica real en `.claude/hooks/harness-init.sh` (este archivo solo es
  wrapper para descubrimiento via `devtools/run.py`)
- Documentacion del protocolo: `.claude/rules/harness-protocol.md`
- Criterios de salud agregados: `docs/CHECKPOINTS.md`
- feature_list por modulo: `docs/<modulo>/feature_list.json`
