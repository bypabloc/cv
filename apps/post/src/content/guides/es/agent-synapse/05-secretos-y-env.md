**05**

# Secretos y archivos .env

[← Índice](README.md)

---

### Leer un .env sin volcarlo

`block_env_read` bloquea la lectura de archivos `.env` con la herramienta de lectura y con comandos como `cat`, `head`, `tail`, `awk`, `strings` o un `python`/`node` inline. En lugar del contenido, el agente recibe un esquema con el tipo y el largo de cada valor:

```text
DATABASE_URL=<URL, 35 caracteres>
API_KEY=<alfanumerico, 32 caracteres>
```

Con eso sabe qué variables existen sin que ningún valor entre al contexto ni al transcript. Las plantillas (`.env.example`, `.env.sample`) se leen normal, y `source .env` está permitido: carga los valores en el proceso sin imprimirlos.

### No escribir credenciales

`detect_secrets` revisa el contenido de cada Edit y Write antes de que llegue al disco:

| Bloquea | Deja pasar |
| :-- | :-- |
| Llaves privadas RSA, SSH y PGP | Placeholders: `your-api-key`, `REPLACE_ME` |
| Tokens de OpenAI, Anthropic, Google, AWS, Stripe, GitHub y Slack | Lecturas de entorno: `process.env.X`, `os.getenv('X')` |
| Contraseñas en texto plano | Llamadas a función que parecen asignaciones |

Los fragmentos de prueba que parecen secretos reales (por ejemplo, para los propios tests del plugin) se escriben con marcadores que el banco de pruebas expande, para no disparar la protección de push de GitHub.

### Una excepción exacta por proyecto

La firma de contraseña a veces choca con valores conocidos y no secretos de un proyecto (una palabra como `required` en un esquema). Para esos casos existe una lista por proyecto en `.synapse/secrets.json` (con respaldo en `.claude/synapse-secrets.json`):

```json
{ "password_rule_values": ["required"] }
```

La excepción es estricta a propósito:

- Solo pasa si **cada** valor capturado coincide exactamente (con mayúsculas) con un elemento de la lista.
- Un valor parecido, o uno permitido mezclado con otro real, se sigue bloqueando.
- Si el archivo falta o es inválido, bloquea.
- Cualquier literal igual pasa en ese proyecto, aunque fuera una credencial real: úsala solo con valores que sepas públicos.

### Lo que Synapse no reemplaza

Synapse evita que el agente lea o escriba secretos por descuido. No reemplaza una política de secretos: los valores reales siguen fuera del repo, en un gestor o en archivos ignorados, y el agente los usa sin verlos (por ejemplo, extrayendo una sola variable en el mismo comando que la consume).

### En mi caso

En mis proyectos la regla es que ningún valor de un `.env` entre a la conversación. Antes de Synapse dependía de que el agente la recordara; ahora, si lo intenta, recibe el esquema y sigue con eso. La excepción por proyecto llegó en la 1.5.0, cuando la firma de contraseña bloqueaba valores conocidos de un proyecto que no tenían nada de secreto, sin forma de permitirlos.

`secretos` `env` `detect_secrets`
