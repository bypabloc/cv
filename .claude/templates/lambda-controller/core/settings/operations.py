"""
Mapeo centralizado de operaciones del servicio.

Cada codename (operation) mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN del Lambda downstream
                 (omitir o dejar '' si la operacion no invoca otro Lambda)

Para agregar una operacion nueva:
  1. Crear controllers/<controller>/<action>.py con la clase <Action>.
  2. Agregar una entrada aqui (el codename puede ser un alias del
     controller; varios codenames pueden apuntar al mismo controller).
  3. Si invoca un Lambda downstream, agregar el ARN en AppConfig
     (settings/config.py).

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

OPERATIONS = {
    # codename -> controller folder + arn key
    'example': {
        'controller': 'example',
        'arn_key': 'arn_example',
    },
    # Ejemplo de alias: otro codename que reusa el mismo controller.
    # 'example_variant': {
    #     'controller': 'example',
    #     'arn_key': 'arn_example',
    # },
}
