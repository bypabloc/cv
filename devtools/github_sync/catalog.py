"""Catalogo de keys de docker/env/client/.{env} que se sincronizan a
GitHub Environment Variables. Solo las que afectan el build de las apps
Astro. Las solo-locales (puerto Docker, flags de CI) se ignoran.
"""

# Keys publicas que el build de las apps consume via import.meta.env.*
# o que site-urls.ts lee de process.env.
SYNCED_KEYS: frozenset[str] = frozenset(
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

# Keys IGNORADAS explicitamente (presentes en .env pero no relevantes
# para el build remoto):
#   - PROXY_PORT, BASE_PORT       -> infra Docker local
#   - CI                          -> flag de CI mode (test/stage local)
#   - TURNSTILE_SITE_KEY          -> duplicada de PUBLIC_TURNSTILE_SITEKEY
#   - TURNSTILE_ENABLED           -> siempre true en envs deployados
IGNORED_KEYS: frozenset[str] = frozenset(
    {
        'PROXY_PORT',
        'BASE_PORT',
        'CI',
        'TURNSTILE_SITE_KEY',
        'TURNSTILE_ENABLED',
    },
)
