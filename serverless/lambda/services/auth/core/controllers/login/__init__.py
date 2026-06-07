"""Controllers de la operation `login` del Lambda `auth`.

Flujo de entrada unico (alta + login). Actions: `check-email`, `start`,
`verify-code`, `verify-magic-link`, `verify-password`, `verify-totp`,
`send-email-code`. El alta ocurre aqui (`login.start` crea el pending si el
email no existe); la operation `register` fue eliminada.
"""
