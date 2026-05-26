"""Mapeo de operaciones del Lambda `tracking_worker`.

El Lambda `tracking_worker` tiene una sola operation, `worker`, con una
sola action, `process_batch`. El handler NO usa `run_controller`
estandar (no enruta por (operation, action) por mensaje individual):
en su lugar invoca DIRECTO el controller `ProcessBatch` con la lista
completa de mensajes del batch, para que TODA la persistencia comparta
una unica conexion Neon (cold-start amortizado entre los 10 events).

Mantener `OPERATIONS` aqui es uniformidad con el resto del backend
(`build_event_model(OPERATIONS)` lo necesita) y deja la puerta abierta
a sumar otras operations en el futuro sin reestructurar.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: el Lambda tracking_worker no invoca otros
                 Lambdas).
"""

OPERATIONS = {
    'worker': {
        'controller': 'worker',
        'arn_key': '',
    },
}
