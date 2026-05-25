"""Catalog: resuelve URLs absolutas por (env, niche, path).

Sigue el estandar de subdominios del portfolio (ver
.claude/docs/subdomain-standard/).

Prod:
  - generic           -> https://the-full-stack.com{path}
  - hub/fintech/...   -> https://{niche}.portfolio.the-full-stack.com{path}
Dev/Stage:
  - todos             -> https://{niche}.portfolio.{env}.the-full-stack.com{path}
Local:
  - todos             -> http://{niche}.localhost:9970{path} (generic = localhost)
"""

NICHES: tuple[str, ...] = (
    'generic',
    'hub',
    'fintech',
    'architect',
    'leader',
    'vibe',
)
APEX_DOMAIN = 'the-full-stack.com'


def resolve_url(env: str, niche: str, path: str = '/') -> str:
    """Devuelve la URL absoluta para un (env, niche, path)."""
    if niche not in NICHES:
        raise ValueError(
            f"unknown niche: '{niche}'. Validos: {', '.join(NICHES)}",
        )
    if not path.startswith('/'):
        raise ValueError(f"path must start with '/': '{path}'")

    if env == 'prod':
        if niche == 'generic':
            return f'https://{APEX_DOMAIN}{path}'
        return f'https://{niche}.portfolio.{APEX_DOMAIN}{path}'

    if env in ('dev', 'stage'):
        return f'https://{niche}.portfolio.{env}.{APEX_DOMAIN}{path}'

    if env == 'local':
        host = 'localhost' if niche == 'generic' else f'{niche}.localhost'
        return f'http://{host}:9970{path}'

    raise ValueError(
        f"unknown env: '{env}'. Validos: local, dev, stage, prod",
    )


def resolve_targets(
    *,
    env: str,
    niches: list[str],
    targets_override: list[dict] | None = None,
) -> list[str]:
    """Resuelve la lista de URLs absolutas a auditar.

    Si ``targets_override`` esta presente, prevalece sobre ``niches`` y
    solo se auditan esos paths puntuales. Si no, se audita ``/`` para
    cada niche en ``niches``.
    """
    if targets_override:
        return [
            resolve_url(env=env, niche=item['niche'], path=item['path'])
            for item in targets_override
        ]
    return [resolve_url(env=env, niche=n, path='/') for n in niches]
