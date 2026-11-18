**02**

# Compactar antes

[← Índice](README.md)

---

### Objetivo

Compactar con **30 a 40 % de margen libre** (60–70 % de uso), con la configuración **versionada en el repo** y sin tocar la configuración global del usuario. Compactar antes no reemplaza al handoff: solo mejora el resumen.

### Claude Code: `.claude/settings.json`

```json
{ "env": { "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "60" }, "autoCompactEnabled": true }
```

- Compacta al 60 % (~600K con 1M). **[doc]** ([env-vars](https://code.claude.com/docs/en/env-vars))
- El override **solo puede bajar el umbral**: un valor mayor que el de fábrica se ignora. **[doc]**
- El `env` del proyecto se aplica después de aceptar la confianza de la carpeta. **[doc]**
- Alternativas en tokens: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` o `autoCompactWindow`. También existen `/autocompact` y `DISABLE_COMPACT`. **[doc]**
- Con un gateway o un id de modelo propio, revisa la ventana: el porcentaje se calcula sobre la ventana que Claude Code cree que tiene el modelo.

### Codex: `.codex/config.toml`

```toml
model_post_turn_compact_threshold_percent = 65   # al cerrar cada turno
model_auto_compact_token_limit = 190000          # tope a mitad de turno: 70 % de 272k; recalcular por modelo
project_doc_max_bytes = 65536                    # si AGENTS.md pasa de 32 KiB
```

- Los dos mecanismos se complementan: el porcentaje solo se evalúa al **terminar** un turno, y un turno largo con muchas herramientas puede pasarlo sin compactar. **[doc]**
- Que `model_auto_compact_token_limit` actúe a mitad de turno lo dice un blog, no la documentación. **[comunidad]**
- El límite efectivo es el menor entre el configurado y el 90 % de la ventana (código upstream, sin documentar).
- La ruta del proyecto debe ser **de confianza** para que Codex cargue `.codex/config.toml`. **[doc + prueba]**

| Uso de 272k | Tokens |
| :-- | :-- |
| 60 % | 163 200 |
| 65 % | 176 800 |
| 70 % | 190 400 |

Un tope en tokens depende del modelo: 190 000 es el 70 % de 272k, pero con una ventana de 500k compactaría al 38 %.

### OpenCode: `opencode.json`

```json
{ "compaction": { "buffer": 400000 } }
```

- `buffer` son los **tokens libres** antes de compactar: 400 000 libres = compactar al 60 % de 1M.
- La documentación V2 acepta `"40%"`, pero la 2.0.29 **descarta sin aviso** todo lo que no sea un entero. **[prueba]**
- El servicio en segundo plano guarda la configuración: tras cambiarla, `opencode service restart`.

### Antigravity: sin ajuste versionable

Solo existe la variable `AGY_CLI_AUTO_COMPACT_OVERRIDE`, que no está documentada **[bin]**: mejor no depender de ella. Lo compensa el handoff inyectado en **cada** invocación ([cap. 05](05-configurar-cada-agente.md)).

### Cómo comprobarlo

| Agente | Comprobación |
| :-- | :-- |
| Claude Code | Un `/compact` real: el handoff aparece en la transcripción después de compactar ([cap. 10](10-probar-el-handoff.md)) |
| Codex | `codex debug prompt-input` sale con 0; con un valor inválido puesto a propósito sale con 1 y nombra la clave, lo que prueba que lee el archivo |
| OpenCode | `opencode service restart && opencode debug config` muestra `compaction: {buffer: 400000}`; una clave que no aparece fue descartada |
| Antigravity | No aplica |

### Límites

- **Los valores en tokens dependen del modelo.** Si cambias de modelo, recalcula el tope de Codex y el `buffer` de OpenCode. Los porcentajes no tienen ese problema.
- **Nada de esto mide la calidad del resumen.** No medí el resumen al 60 % frente al 97 %; la mejora es **[criterio]**.

### En mi caso

Quedé con Claude Code al 60 %, Codex al 65 % más el tope de 190 000 y OpenCode con `buffer: 400000`. El tropiezo fue OpenCode: el `"40%"` que acepta la documentación V2 desaparecía de `opencode debug config` sin un solo error. Desde entonces compruebo cada cambio de configuración con el comando que muestra lo que el agente **validó**, no con lo que escribí. En Codex, además, `AGENTS.md` pesaba ~50 KB y se leía cortado a 32 KiB sin aviso: de ahí sale el `project_doc_max_bytes` del ejemplo ([cap. 12](12-problemas-y-soluciones.md)).

`compactación` `umbral` `configuración`
