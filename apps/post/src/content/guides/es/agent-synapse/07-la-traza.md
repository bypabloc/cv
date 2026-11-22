**07**

# La traza: quién decidió y por qué

[← Índice](README.md)

---

### Un paso por línea

Cada ejecución de un hook escribe una traza JSONL diaria (`AAAA-MM-DD.jsonl`), agrupada por `run` y con el id de la sesión del agente. El contenido de Write y Edit nunca se registra, y los tokens se enmascaran.

```bash
python3 <plugin>/scripts/synapse_log.py --since 30m          # 30m, 2h, 1d
python3 <plugin>/scripts/synapse_log.py --decision block     # allow | ask | block | pass
python3 <plugin>/scripts/synapse_log.py --session 49c43f62 --hook block_dangerous
python3 <plugin>/scripts/synapse_log.py --json | jq .        # JSONL crudo
python3 <plugin>/scripts/synapse_log.py --follow             # en vivo
python3 <plugin>/scripts/synapse.py log --host codex         # trazas de otro agente
```

### Cómo se lee

```text
━━ 2026-10-02 09:00:56.720 ━━ block_dangerous ━━ run 29e84acc ━━ session 49c43f62
   tool    Bash
   cwd     ~/code/mi-app
   engine  laya-daemon-gpu
   input   p=~; rm -rf "$p/otro"
   ├─ regex.catastrophic         result=no_match  checked=21
   ├─ structure.outside_project  result=match  subcmd=rm -rf "$p/otro"  target=~/otro
   └─ DECISION  BLOCK  python · structure.outside_project  (7.6 ms)
      evidencia  {"subcmd": "rm -rf \"$p/otro\"", "target": "~/otro"}
```

- **engine:** qué motor estaba disponible (reglas solas, Laya en GPU o en CPU).
- **Cada paso** muestra la regla evaluada y su resultado.
- **DECISION** dice quién decidió (`python` = una regla, `laya` = el clasificador), con qué regla, el tiempo y la evidencia.

### Depurar un falso positivo

1. Encuéntralo: `synapse_log.py --decision ask --since 1d` (o `block`).
2. Mira `decided_by` y `rule`: si fue una regla, el caso va a esa regla; si fue Laya, probablemente falta una regla determinista.
3. Fíjalo en un caso de prueba ([cap. 11](11-probar-y-operar.md)), **junto a un valor parecido que debe seguir decidiéndose igual**, para no abrir un hueco al cerrar el falso positivo.

### Por qué la atribución importa

Hasta la 1.2.0, un `block` o un `ask` no decía si venía de una regla o del modelo, y depurar un falso positivo era adivinar. Desde entonces hay un test que exige que **toda** decisión `block` o `ask` nombre quién la tomó. Sin eso, la traza no sirve como banco de pruebas.

### En mi caso

La traza es la fuente de casi todas las versiones del plugin. La revisión periódica es siempre la misma: filtrar los `ask` y `block` de los últimos días, separar los correctos de los falsos positivos y convertir cada falso positivo en un caso. En noviembre, esa revisión sobre semanas de uso es la que llevó a apagar Laya por defecto ([cap. 08](08-laya.md)).

`traza` `logs` `depuración`
