**04**

# El alcance del proyecto y los borrados recuperables

[← Índice](README.md)

---

### Qué es "dentro del proyecto"

La regla `structure.outside_project` bloquea modificar rutas fuera de las raíces permitidas. Esas raíces salen de git, no del texto del comando:

- El toplevel del repo del proyecto (`CLAUDE_PROJECT_DIR` o su equivalente en cada agente; si no hay, el `cwd`).
- El superproyecto, si el repo es un submódulo.
- Los worktrees del mismo repo, aunque vivan en otra carpeta.

Para saber a qué ruta apunta un comando, Synapse sigue los `cd` (incluido `cd -`), resuelve `$HOME`, `~` y las variables asignadas antes en la misma línea, y salta prefijos como `sudo`, `VAR=valor` o `timeout N`. Así, `p=~/; rm -rf "$p/otro"` se ve como lo que es.

### Lo desechable no pregunta

Hay rutas cuyo contenido se puede perder sin consecuencias. Las operaciones sobre ellas se aprueban solas:

| Tipo | Ejemplos |
| :-- | :-- |
| Temporales | `./tmp/**`, el scratchpad de la sesión del agente, `*.log` |
| Artefactos de build | `dist/`, `build/`, `.turbo/`, `target/`, `.cache/`, `node_modules/` |
| Archivos sin versionar | Un archivo (no un directorio) que el agente acaba de crear |
| Cachés de intérpretes | `__pycache__` y similares ignorados por git |

Un detalle que costó un fix: una ruta ignorada por un repo **padre** (por ejemplo, uno que versiona tu carpeta personal) no cuenta como desechable. Lo ignorado se evalúa en el repo del proyecto.

### Borrar lo que git puede restaurar

Borrar archivos versionados y limpios (sin cambios locales) se aprueba solo: git los recupera. El agente recibe, junto con la aprobación, cómo restaurarlos:

```text
git -C ~/code/mi-app checkout -- src/legacy/
```

La regla `structure.git_recoverable_delete` tuvo que cerrar varios huecos antes de ser segura:

- Un `rm -rf link/` sobre un symlink versionado podía borrar fuera del repo: ya no se aprueba solo.
- Solo las cachés de intérpretes cuentan como contenido ignorado regenerable; cualquier otro ignorado puede ser trabajo.
- Un comando compuesto con subcomandos que no son borrados vuelve a `ask`.
- Se excluyen los repos con `.git` propio y los archivos marcados `skip-worktree` o `assume-unchanged`.

### Clonar o tocar otro repo

`git clone` y `git -C <otra-ruta>` hacia fuera del proyecto también cuentan como escrituras fuera del alcance. Si un trabajo necesita otro repo, la forma es abrir una sesión en ese repo, donde será el proyecto.

### En mi caso

Trabajo con varios worktrees por repo y, al principio, cada sesión en un worktree veía al checkout principal como "fuera del proyecto". La raíz calculada desde git (toplevel, superproyecto y worktrees) lo resolvió. La lección que dejó la regla de borrados recuperables: un auto-allow tiene que probar que **todo** lo afectado se puede recuperar; los symlinks, los repos padre y los comandos compuestos son justo por donde se pierde trabajo.

`alcance` `git` `worktrees` `borrados`
