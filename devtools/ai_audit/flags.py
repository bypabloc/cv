"""Flag validation for ai_audit command.

Soporta 2 subcomandos:
- (default)  audita los targets contra las tools elegidas
- report     re-renderiza el Markdown desde un snapshot.json existente

Nota: el subcomando `setup` fue eliminado cuando se migro de tools que
requerian storageState (Ahrefs/Semrush) a tools con API publica o API
key gratuita (isitagentready, validators OSS propios, lighthouse_psi).
"""

import sys

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_ENVS = ('local', 'dev', 'stage', 'prod')
VALID_NICHES = ('generic', 'hub', 'fintech', 'architect', 'leader', 'vibe')
VALID_TOOLS = ('isitagentready', 'validators', 'lighthouse_psi')
VALID_SUBCOMMANDS = ('audit', 'report')

ALLOWED_FLAGS = [
    # Globales
    'env',
    'niches',
    'tools',
    'targets',
    'headless',
    'help',
    # Report-only
    'snapshot',
]


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for ai_audit command."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    _extract_subcommand(flags_dict)

    normalized = set_default_values(
        flags_dict,
        {
            'env': 'prod',
            'niches': '',
            'tools': '',
            'targets': '',
            'headless': True,
            'snapshot': '',
        },
    )

    sub = normalized['subcommand']
    if sub == 'report':
        _validate_report(normalized)
    else:
        _validate_audit(normalized)

    return normalized


def _extract_subcommand(flags_dict: dict) -> None:
    """Extract positional subcommand (audit | report).

    Default: 'audit'. Si el primer posicional no es un subcomando
    conocido, lo rechaza con un mensaje claro (evita typos
    silenciosos).
    """
    raw_args = sys.argv[2:]
    positional: list[str] = []
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            positional.append(arg)

    if not positional:
        flags_dict['subcommand'] = 'audit'
        return

    sub = positional[0]
    if sub not in VALID_SUBCOMMANDS:
        raise ValueError(
            f"Subcomando desconocido: '{sub}'. "
            f'Validos: {", ".join(VALID_SUBCOMMANDS)}',
        )
    flags_dict['subcommand'] = sub


def _validate_audit(normalized: dict) -> None:
    """Valida flags del subcomando default (audit)."""
    env = normalized['env']
    if env not in VALID_ENVS:
        raise ValueError(
            f"--env='{env}' invalido. Valores validos: "
            + ', '.join(VALID_ENVS),
        )

    niches = _parse_csv(normalized['niches'])
    if niches:
        unknown = [n for n in niches if n not in VALID_NICHES]
        if unknown:
            raise ValueError(
                f'unknown niches: {", ".join(unknown)}. '
                f'Validos: {", ".join(VALID_NICHES)}',
            )
        normalized['niches'] = niches
    else:
        normalized['niches'] = list(VALID_NICHES)

    tools = _parse_csv(normalized['tools'])
    if tools:
        unknown = [t for t in tools if t not in VALID_TOOLS]
        if unknown:
            raise ValueError(
                f'unknown tool: {", ".join(unknown)}. '
                f'Validos: {", ".join(VALID_TOOLS)}',
            )
        normalized['tools'] = tools
    else:
        normalized['tools'] = list(VALID_TOOLS)

    targets = _parse_targets(normalized['targets'])
    normalized['targets'] = targets


def _validate_report(normalized: dict) -> None:
    """Valida flags del subcomando report."""
    if not normalized['snapshot']:
        raise ValueError('report requires --snapshot=<path>')


def _parse_csv(raw: object) -> list[str]:
    """Parsea 'a,b,c' a ['a', 'b', 'c']. Empty string -> []."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return [item.strip() for item in str(raw).split(',') if item.strip()]


def _parse_targets(raw: object) -> list[dict]:
    """Parsea '--targets=niche:/path,niche:/path' a lista de dicts.

    Cada item es {'niche': str, 'path': str}. Vacio si no se pasa.
    Path debe empezar con '/'.
    """
    if not raw:
        return []
    items = _parse_csv(raw)
    parsed: list[dict] = []
    for item in items:
        if ':' not in item:
            raise ValueError(
                f"--targets item '{item}' invalido: falta ':'. "
                'Formato: niche:/path',
            )
        niche, path = item.split(':', 1)
        niche = niche.strip()
        path = path.strip()
        if niche not in VALID_NICHES:
            raise ValueError(
                f"--targets item '{item}' invalido: niche '{niche}' "
                f'desconocido. Validos: {", ".join(VALID_NICHES)}',
            )
        if not path.startswith('/'):
            raise ValueError(
                f"--targets item '{item}' invalido: path must start with /",
            )
        parsed.append({'niche': niche, 'path': path})
    return parsed


def describe() -> ScriptDescribe:
    """Machine-readable inventory of ai_audit flags."""
    return {
        'name': 'ai_audit',
        'kind': 'subcommand',
        'summary': (
            'Audita preparacion para IA combinando 3 fuentes: '
            'isitagentready (API publica), validators OSS propios '
            '(llms.txt+robots+sitemap+JSON-LD) y Google PageSpeed Insights'
        ),
        'commands': [
            {
                'name': 'audit',
                'summary': 'Default. Corre el audit sobre los targets',
                'flags': ['env', 'niches', 'tools', 'targets', 'headless'],
                'destructive': False,
            },
            {
                'name': 'report',
                'summary': 'Re-renderiza Markdown desde un snapshot.json',
                'flags': ['snapshot'],
                'destructive': False,
            },
        ],
        'flags': {
            'env': {
                'type': 'choice',
                'choices': list(VALID_ENVS),
                'default': 'prod',
                'summary': 'Env destino (prod por defecto)',
            },
            'niches': {
                'type': 'string',
                'default': '',
                'summary': 'CSV de niches (default: los 6)',
            },
            'tools': {
                'type': 'string',
                'default': '',
                'summary': 'CSV de tools (default: las 3)',
            },
            'targets': {
                'type': 'string',
                'default': '',
                'summary': 'CSV niche:/path (default: home de cada niche)',
            },
            'snapshot': {
                'type': 'string',
                'default': '',
                'summary': '(report) path al snapshot.json',
            },
            'headless': {
                'type': 'bool',
                'default': True,
                'summary': 'Corre Playwright headless (default True)',
            },
        },
    }
