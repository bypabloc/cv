"""Mapeo de operaciones del Lambda `send_email`.

Una sola operation `email` con la action `send`. El handler sintetiza el
evento `{operation:'email', action:'send', data}` desde el payload del
invoke async.
"""

OPERATIONS = {
    'email': {
        'controller': 'email',
        'arn_key': '',
    },
}
