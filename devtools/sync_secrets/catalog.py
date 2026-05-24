"""Catalogo de keys por categoria.

- CLIENT_SYNCED_KEYS: las que se publican a GitHub Environment Variables.
- DEVCLI_EXPECTED_KEYS: las que SOLO existen local (no sync remoto). Se
  validan que existan en el .env del dev para evitar configs rotas.

Para SERVER, el catalogo NO vive aqui: vive como YAMLs en
`serverless/lambda/resources/secrets/*.yaml` y lo carga
`serverless.secrets_catalog.Catalog.load()`. Esa fuente de verdad la
respeta el target server.
"""

# Keys publicas (PUBLIC_*) + URL builders que el build de las apps consume
# via import.meta.env.* o process.env. Espejo de docker/env/client/.example.
CLIENT_SYNCED_KEYS: frozenset[str] = frozenset(
    {
        # URL builder (packages/app-shared/src/lib/site-urls.ts)
        'BASE_DOMAIN',
        'BASE_SCHEME',
        'APEX_DOMAIN',
        # API + Turnstile (consumido por TrackingPixel + /contact)
        'PUBLIC_API_ENDPOINT',
        'PUBLIC_TURNSTILE_SITEKEY',
    },
)

# Keys IGNORADAS de docker/env/client (solo-locales para infra Docker)
CLIENT_IGNORED_KEYS: frozenset[str] = frozenset(
    {
        'PROXY_PORT',
        'BASE_PORT',
        'CI',
        'TURNSTILE_SITE_KEY',  # duplicada de PUBLIC_TURNSTILE_SITEKEY
        'TURNSTILE_ENABLED',
    },
)

# Keys que se esperan en docker/env/dev-cli/.{env} (espejo del .example).
# NO se sincronizan a nada remoto — son credenciales del dev local que
# usa devtools para gestionar infra (AWS deploy, Neon branches, CF Pages,
# Turnstile). En CI se usa OIDC, no estas keys. Se valida presencia
# para detectar configs incompletas que romperian `serverless deploy`.
DEVCLI_EXPECTED_KEYS: frozenset[str] = frozenset(
    {
        # AWS (IAM user `dev`)
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        # Neon (gestion de branches via CLI)
        'NEON_DB_API_KEY',
        # Cloudflare (deploy Pages + DNS + Turnstile management)
        'CLOUDFLARE_API_TOKEN',
        'CLOUDFLARE_ACCOUNT_ID',
        'ACCOUNT_ID',  # AWS account id (no secreto)
    },
)

# Keys opcionales de dev-cli (no fallan si faltan)
DEVCLI_OPTIONAL_KEYS: frozenset[str] = frozenset(
    {
        'AWS_SESSION_TOKEN',  # solo si se usa SSO temporal
        'AWS_DEFAULT_REGION',
        'AWS_REGION',
    },
)
