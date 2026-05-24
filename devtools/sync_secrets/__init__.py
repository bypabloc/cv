"""sync_secrets script: comando unificado de sincronizacion de las 3
categorias de secretos del portfolio.

Categorias y destinos:
- client   -> GitHub Environment Variables (publico, build-time)
- server   -> AWS SSM Parameter Store (SecureString + KMS)
- dev-cli  -> NO se sincroniza (local-only — IAM keys del dev)

Hermetico: ningun valor de secreto aparece en stdout, stderr, ni mensajes
de error. Solo nombres de KEY + acciones (SKIP/PUSH/CREATE/MISSING/LOCAL-ONLY).
"""
