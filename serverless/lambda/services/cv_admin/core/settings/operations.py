"""Mapeo de operations del Lambda `cv_admin`.

2 operations: `content` (escritura de las entidades del CV en Neon +
reorder + catalogos) y `publish` (dispara/consulta el workflow de deploy
de las apps via la GitHub API). Cada operation declara su carpeta de
controllers y un `arn_key` vacio (cv_admin NO invoca otros Lambdas).

Los controllers se descubren por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`upsert-experience` -> module `controllers/content/upsert_experience.py`
+ clase `UpsertExperience(BaseController)`.
"""

OPERATIONS = {
    'content': {
        'controller': 'content',
        'arn_key': '',
    },
    'publish': {
        'controller': 'publish',
        'arn_key': '',
    },
}
