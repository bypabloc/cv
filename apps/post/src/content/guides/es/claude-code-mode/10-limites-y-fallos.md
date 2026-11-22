**10**

# Límites y fallos conocidos

[← Índice](README.md)

---

### Lo que no está disponible

- `claude -p`, el Agent SDK, el panel de VS Code, Desktop, sesiones en la nube, Remote Control, Claude in Chrome y computer use **[doc]**.
- Mover la sesión a Desktop o convertirla en sesión de segundo plano.
- Una sesión iniciada con Code Mode **solo se reanuda en la terminal y con el modo encendido**.
- No hay forma oficial de elegir el modo por skill, subagente o llamada (es una solicitud abierta).

### Subagentes

Si un subagente usa Code Mode depende de su lista de herramientas: todas las herramientas lo incluyen; una lista fija no, salvo que incluya `REPL`; `disallowedTools: REPL` lo apaga. No está documentado oficialmente. El código de un subagente no se ve con `Ctrl+O` desde la sesión principal **[doc]**.

### Fallos que ya se corrigieron

En ocho días hubo siete versiones con decenas de arreglos del modo **[doc]**:

| Versión | Arreglo |
| :-- | :-- |
| 2.1.325 | Scripts que ignoraban el worktree activo |
| 2.1.326 | Soporte con agent teams (en el mismo proceso) |
| 2.1.328 | Una pausa de 0,75 s tras cada script; variables que quedaban `undefined` tras un script fallido; `write()`/`edit()` ofrecidos a subagentes de solo lectura; en Windows, la shell es Git Bash |
| 2.1.329 | Un hook `PreToolUse` que falla ya no rechaza la llamada; límite contra bucles que llenaban la memoria |
| 2.1.330 | Pausa larga tras leer cientos de archivos con reglas por ruta; `/context` que subcontaba las herramientas |

### Fallos abiertos al 22 de noviembre

- El resultado se corta a unos 30 mil caracteres y la parte del medio se pierde.
- Pasos encadenados después de un comando en segundo plano que nunca corren.
- En WSL2, tareas de archivos con cientos de lecturas sueltas, más lentas que el modo normal.
- Subagentes de solo lectura que, según su reportero, siguen recibiendo `write()`/`edit()`.

### En mi caso

Lo que más me afectó fue reanudar: varias veces quise volver a una sesión sin el modo para comparar y no se puede. Mi regla quedó así: una sesión nueva para cada comparación, y `claude update` antes de medir, porque una versión vieja mide un modo distinto.

`límites` `bugs` `changelog`
