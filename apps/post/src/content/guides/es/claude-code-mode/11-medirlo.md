**11**

# Cómo medirlo en tu proyecto

[← Índice](README.md)

---

### Un A/B honesto

1. **Elige 3 o 4 tareas reales** de tu proyecto con formas distintas: una con muchas llamadas MCP, una de edición en varios archivos, una de "implementar y probar" y una pregunta simple.
2. **Sesiones nuevas** para cada corrida, con el mismo modelo, el mismo esfuerzo, los mismos permisos y los mismos servidores MCP.
3. **El mismo prompt**, copiado tal cual.
4. **Al menos 2 o 3 corridas por modo:** la variación entre corridas idénticas es grande.
5. **Registra:** tiempo, `/cost` al final, `/context` al inicio y al final, y si el resultado pasa la misma verificación (tests, un conteo esperado).
6. **Compara por tarea**, no un promedio global.

| Comando | Qué te dice |
| :-- | :-- |
| `/status` | Que el modo esté realmente encendido |
| `/context` | Cuánto pesan las herramientas y cuánto creció el contexto con la tarea |
| `/cost` | Costo estimado a precio de API (con suscripción, no es la factura) |
| `/usage` | Cuánto consumiste de la cuota de 5 h y semanal (ojo: hay mucho ruido si usas otras sesiones a la vez) |
| `Ctrl+O` | Qué escribió Claude en cada bloque |

### Medir lo que ya hiciste: los transcripts

Los transcripts viven en `~/.claude/projects/<proyecto>/<sesión>.jsonl` (o bajo tu `CLAUDE_CONFIG_DIR`). Cada línea es un evento JSON; los bloques de Code Mode son `tool_use` con nombre `REPL` y el código en `input.code`. Este script cuenta los bloques y su forma:

```python
import glob, json, re, statistics, sys

seen, lines, shell = set(), [], []
for path in glob.glob(sys.argv[1] + '/**/*.jsonl', recursive=True):
    for raw in open(path, encoding='utf-8', errors='ignore'):
        if '"name":"REPL"' not in raw:
            continue
        event = json.loads(raw)
        for block in (event.get('message') or {}).get('content') or []:
            if block.get('type') != 'tool_use' or block.get('name') != 'REPL':
                continue
            if block['id'] in seen:
                continue
            seen.add(block['id'])
            code = block['input'].get('code', '')
            lines.append(code.count('\n') + 1)
            shell.append(len(re.findall(r'\$`', code)))

print(f'bloques: {len(lines)}')
print(f'líneas (mediana): {statistics.median(lines)}')
print(f'comandos de shell por bloque: {sum(shell) / len(shell):.2f}')
```

```bash
python3 contar_bloques.py ~/.claude/projects
```

Para el uso de tokens, cada mensaje `assistant` trae `message.usage` (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens`); agrúpalos por `message.id` para no contar dos veces el mismo request.

### Errores comunes al medir

- Comparar una sesión reanudada con una nueva: el contexto de partida no es el mismo.
- Medir con versiones distintas.
- Lanzar `claude` desde dentro de otra sesión: hereda variables y el modo puede no arrancar.
- Contar solo tokens y no mirar el tiempo ni si el resultado es correcto.

### En mi caso

Hice las comparaciones así, con tareas de klinikae y content-studio, y conté mis transcripts con una versión ampliada de este script. Lo más útil fue separar las tareas por forma antes de medir: con eso, el resultado se volvió predecible.

`medición` `benchmark` `transcripts`
