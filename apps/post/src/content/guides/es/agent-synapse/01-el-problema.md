**01**

# Por qué un agente necesita guardrails

[← Índice](README.md)

---

### Lo que puede salir mal

Un agente de código ejecuta comandos y escribe archivos a gran velocidad. En una corrida autónoma de varias horas, basta un error de razonamiento para que ocurra algo difícil de revertir:

| Riesgo | Ejemplo |
| :-- | :-- |
| Borrado irreparable | `rm -rf` sobre una variable vacía o una ruta fuera del proyecto |
| Historia reescrita | `git push --force`, `git reset --hard`, `filter-branch` |
| Fuga de secretos | `cat .env` vuelca credenciales en el contexto y en el transcript |
| Credenciales en el repo | Un token pegado en un archivo de configuración o un test |
| Infraestructura dañada | Editar a mano `.git/`, `.venv/` o un lockfile |
| Cambios en las propias reglas | El agente edita su configuración de permisos o de hooks |
| Esquivar los controles | Escribir archivos con `echo >` o `sed -i` en vez de la herramienta de edición |

### Por qué los permisos nativos no bastan

Cada agente trae su sistema de permisos, y en la práctica te deja elegir entre dos extremos:

- **Preguntar todo:** el agente se detiene a cada rato por operaciones inofensivas. Terminas aprobando sin leer (la fatiga de confirmación anula el control) o vigilando la pantalla para que el trabajo avance.
- **Permitir todo:** el agente avanza solo, pero nada distingue un `rm` de un archivo temporal de un `rm -rf` sobre tu carpeta personal.

Además, los permisos nativos miran el nombre del comando, no lo que hace: `p=/home/x; rm -rf "$p/otro"` parece un `rm` relativo hasta que se resuelve la variable.

### La idea que sostiene la guía

> **Lo que una regla puede decidir no se le deja al modelo ni al usuario.**

Synapse revisa cada herramienta antes de ejecutarla. Si la operación es claramente segura, la deja pasar sin preguntar. Si es claramente peligrosa, la bloquea y le dice al agente por qué. Solo lo genuinamente ambiguo llega a ti. El agente no gasta contexto en esto: los hooks corren fuera de la conversación.

### Qué vas a montar

1. El plugin instalado en el agente que uses ([cap. 02](02-instalacion.md)).
2. Un mapa de lo que decide cada hook ([caps. 03](03-que-decide.md) a [05](05-secretos-y-env.md)).
3. La configuración de tu proyecto para que lo rutinario no pregunte ([cap. 06](06-configurar-por-proyecto.md)).
4. La lectura de la traza para depurar ([cap. 07](07-la-traza.md)).
5. Opcional: Laya para los casos ambiguos ([cap. 08](08-laya.md)).

### En mi caso

Los primeros hooks eran cuatro scripts en la carpeta `.claude/hooks/` de un proyecto. Funcionaban, pero cada proyecto nuevo pedía copiarlos y cada ajuste había que repetirlo en todos. Al convertirlos en plugin, la primera versión (1.0.0, octubre de 2026) ya traía los cuatro hooks de hoy; las catorce versiones siguientes fueron, sobre todo, quitar confirmaciones innecesarias sin abrir huecos.

`guardrails` `permisos` `problema`
