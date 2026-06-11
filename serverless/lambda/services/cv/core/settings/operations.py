"""Mapeo de operaciones del Lambda `cv`.

3 operations:

- `cv` (publica, GET): lectura del CV. Actions: `get`, `profile`,
  `experiences`, `projects`, `certificates`, `awards`, `education`,
  `languages`, `references`, `skills`.
- `content` (admin, POST): escritura de las entidades cv_* en Neon +
  `reorder` + `catalogs` + `get-all` (CV completo en shape de edicion).
- `publish` (admin, POST): dispara/consulta el workflow deploy-apps.yml
  via la GitHub API.

`content` y `publish` vivian en el ex Lambda cv_admin (plan
d-cv-consolidation las absorbio aqui: toda la logica del CV en un solo
Lambda). Sus actions requieren access JWT + scope admin (whitelist SSM
admin-emails) via `required_permission = 'admin'` del lambda_kit.

Los controllers se descubren por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`get-all` -> module `controllers/content/get_all.py` + clase `GetAll`.
"""

OPERATIONS = {
    'cv': {
        'controller': 'cv',
        'arn_key': '',
    },
    'content': {
        'controller': 'content',
        'arn_key': '',
    },
    'publish': {
        'controller': 'publish',
        'arn_key': '',
    },
}
