"""Controllers del Lambda `auth`.

Cada operation (`login`, `verify`, `session`, `mfa`, `webauthn`,
`security`) tiene su subcarpeta con un modulo por action. La operation
`register` fue eliminada (el alta ocurre dentro del flujo `login` unico).
"""
