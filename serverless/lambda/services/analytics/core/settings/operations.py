"""Mapeo de operaciones del Lambda `analytics`.

8 operations (un dominio de metricas cada una), 19 actions en total. Cada
operation declara su carpeta de controllers (`controller`); el
`import_controller` resuelve la action del query string del GET por
convencion en `controllers/<controller>/<action>.py` (clase en PascalCase:
`top-pages` -> `controllers/analytics/top_pages.py` -> clase `TopPages`).
"""

OPERATIONS = {
    'analytics': {'controller': 'analytics', 'arn_key': ''},
    'events': {'controller': 'events', 'arn_key': ''},
    'sessions': {'controller': 'sessions', 'arn_key': ''},
    'visits': {'controller': 'visits', 'arn_key': ''},
    'geo': {'controller': 'geo', 'arn_key': ''},
    'devices': {'controller': 'devices', 'arn_key': ''},
    'funnel': {'controller': 'funnel', 'arn_key': ''},
    'contacts': {'controller': 'contacts', 'arn_key': ''},
}
