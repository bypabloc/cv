"""Validadores puros para AI readiness, sin red ni Playwright.

Cada funcion recibe el contenido raw (string o bytes) y devuelve un
dict con shape estable:

    {
        'status': 'pass' | 'fail' | 'neutral',
        'message': str,
        'details': dict,
    }

Disenado para ser invocado desde `tools/validators.py` (que se encarga
de fetchear los recursos via httpx) o desde tests con fixtures locales.
Cero deps externas mas alla de stdlib + beautifulsoup4 (ya dep de
devtools).

Cubre 4 senales clave que NO mide isitagentready en detalle:
- `llms.txt` segun spec (llmstxt.org)
- `robots.txt` bloqueo accidental de AI bots
- `sitemap.xml` validez basica + presencia
- JSON-LD `Person` o `Organization` en HTML
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup


_LLMS_TXT_MAX_BYTES = 100_000  # spec limit informal (100 KB)

# Firmas reconocibles del bloque robots.txt managed por Cloudflare
# "Content Signals" feature. Cuando estos comentarios aparecen, los
# bloqueos de AI bots son intencionales (decision del owner via
# Cloudflare dashboard), no un descuido del sitio.
_CF_MANAGED_SIGNATURES = (
    '# BEGIN Cloudflare Managed content',
    'As a condition of accessing this website, you agree to abide',
)
_AI_BOTS = (
    'GPTBot',
    'ChatGPT-User',
    'OAI-SearchBot',
    'ClaudeBot',
    'Claude-Web',
    'PerplexityBot',
    'CCBot',
    'Google-Extended',
    'anthropic-ai',
    'Applebot-Extended',
    'cohere-ai',
)


def validate_llms_txt(content: str | None) -> dict[str, Any]:
    """Valida /llms.txt segun spec (llmstxt.org).

    Reglas:
      - Existe (content no es None ni vacio).
      - Empieza con un header H1 ('# <Titulo>').
      - Pesa < 100 KB.
      - Tiene al menos una lista markdown con links ('- [text](url)').
    """
    if not content:
        return {
            'status': 'fail',
            'message': 'llms.txt ausente o vacio',
            'details': {},
        }

    size = len(content.encode('utf-8'))
    issues: list[str] = []
    if size > _LLMS_TXT_MAX_BYTES:
        issues.append(f'tamano {size} bytes > {_LLMS_TXT_MAX_BYTES} bytes')

    stripped = content.lstrip()
    if not stripped.startswith('# '):
        issues.append('no empieza con header H1 (# Titulo)')

    link_count = len(re.findall(r'-\s*\[[^\]]+\]\([^)]+\)', content))
    if link_count == 0:
        issues.append('no contiene links markdown (- [text](url))')

    if issues:
        return {
            'status': 'fail',
            'message': '; '.join(issues),
            'details': {'size_bytes': size, 'links_found': link_count},
        }

    return {
        'status': 'pass',
        'message': f'llms.txt valido ({size} bytes, {link_count} links)',
        'details': {'size_bytes': size, 'links_found': link_count},
    }


def validate_robots_ai_bots(content: str | None) -> dict[str, Any]:
    """Detecta bloqueos accidentales de AI bots conocidos en robots.txt.

    Spec robots.txt: bloques `User-agent: <X>\\n... Disallow: /` aplican
    SOLO al user-agent declarado. Detectamos cuando un AI bot conocido
    tiene Disallow: /.

    Si NO hay bloqueos -> 'pass'. Si hay -> 'fail' (con la lista).
    """
    if not content:
        return {
            'status': 'fail',
            'message': 'robots.txt ausente',
            'details': {},
        }

    blocked: list[str] = []
    blocks = _split_robots_blocks(content)
    for agents, rules in blocks:
        normalized_agents = {a.lower() for a in agents}
        ai_in_block = [
            bot for bot in _AI_BOTS if bot.lower() in normalized_agents
        ]
        if not ai_in_block:
            continue
        if any(_is_full_disallow(rule) for rule in rules):
            blocked.extend(ai_in_block)

    if blocked:
        # Si el bloqueo viene de Cloudflare Content Signals managed, es
        # intencional -> reportar como 'neutral' (no fail), para que el
        # validator no penalice una decision de policy del owner.
        managed = _is_cloudflare_managed(content)
        if managed:
            return {
                'status': 'neutral',
                'message': (
                    'AI bots bloqueados por Cloudflare Content Signals '
                    '(decision intencional del owner): '
                    f'{", ".join(sorted(set(blocked)))}'
                ),
                'details': {
                    'managed': True,
                    'blocked': sorted(set(blocked)),
                },
            }
        return {
            'status': 'fail',
            'message': f'AI bots bloqueados: {", ".join(sorted(set(blocked)))}',
            'details': {
                'managed': False,
                'blocked': sorted(set(blocked)),
            },
        }
    return {
        'status': 'pass',
        'message': 'ningun AI bot conocido esta bloqueado por robots.txt',
        'details': {'blocked': []},
    }


def validate_sitemap_xml(content: str | None) -> dict[str, Any]:
    """Valida shape minima de sitemap.xml (o sitemap-index)."""
    if not content:
        return {
            'status': 'fail',
            'message': 'sitemap.xml ausente',
            'details': {},
        }
    text = content.lstrip()
    if (
        not text.startswith('<?xml')
        and not text.startswith('<urlset')
        and not text.startswith('<sitemapindex')
    ):
        return {
            'status': 'fail',
            'message': 'no parece XML (no empieza con <?xml/<urlset/<sitemapindex)',
            'details': {},
        }
    is_index = '<sitemapindex' in text
    url_count = len(re.findall(r'<loc>', text))
    if url_count == 0:
        return {
            'status': 'fail',
            'message': 'sitemap sin entradas <loc>',
            'details': {'is_index': is_index, 'entries': 0},
        }
    return {
        'status': 'pass',
        'message': f'sitemap {"index" if is_index else "valido"} con {url_count} entradas',
        'details': {'is_index': is_index, 'entries': url_count},
    }


def validate_json_ld_person(html: str | None) -> dict[str, Any]:
    """Valida presencia de JSON-LD schema.org Person u Organization.

    Para un portfolio de dev, Person es lo esperado. Organization
    tambien cuenta (algunos optan por ese tipo).
    """
    if not html:
        return {
            'status': 'fail',
            'message': 'HTML ausente',
            'details': {},
        }
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', type='application/ld+json')
    if not scripts:
        return {
            'status': 'fail',
            'message': 'sin <script type="application/ld+json">',
            'details': {'count': 0},
        }

    found_types: list[str] = []
    for s in scripts:
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
        except json.JSONDecodeError:  # noqa: S112 - skip broken JSON-LD scripts
            continue
        found_types.extend(_extract_types(data))

    relevant = [t for t in found_types if t in ('Person', 'Organization')]
    if relevant:
        return {
            'status': 'pass',
            'message': f'JSON-LD encontrado: {", ".join(sorted(set(relevant)))}',
            'details': {'types_found': sorted(set(found_types))},
        }
    return {
        'status': 'fail',
        'message': (
            f'JSON-LD presente pero sin Person ni Organization '
            f'(tipos: {", ".join(sorted(set(found_types))) or "ninguno"})'
        ),
        'details': {'types_found': sorted(set(found_types))},
    }


def _split_robots_blocks(
    content: str,
) -> list[tuple[list[str], list[str]]]:
    """Parsea robots.txt en bloques [user-agents, [rules]].

    Cada bloque empieza con uno o mas `User-agent: X` consecutivos,
    seguido de directivas hasta el siguiente bloque (o EOF).
    """
    blocks: list[tuple[list[str], list[str]]] = []
    current_agents: list[str] = []
    current_rules: list[str] = []
    expecting_rules = False

    for raw_line in content.splitlines():
        line = raw_line.split('#', 1)[0].strip()
        if not line:
            continue
        if ':' not in line:
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        if key.lower() == 'user-agent':
            if expecting_rules:
                blocks.append((current_agents, current_rules))
                current_agents = []
                current_rules = []
                expecting_rules = False
            current_agents.append(value)
        else:
            current_rules.append(line)
            expecting_rules = True

    if current_agents:
        blocks.append((current_agents, current_rules))
    return blocks


def _is_full_disallow(rule: str) -> bool:
    """True si la regla es 'Disallow: /' (bloquea todo)."""
    if ':' not in rule:
        return False
    key, value = (part.strip() for part in rule.split(':', 1))
    return key.lower() == 'disallow' and value == '/'


def _is_cloudflare_managed(content: str) -> bool:
    """True si el robots.txt viene de la feature Cloudflare Content Signals.

    Cloudflare inyecta firmas reconocibles (un comentario header
    explicando los content signals + el marker `# BEGIN Cloudflare
    Managed content`). Si la firma esta, los bloqueos de AI bots son
    intencionales (decision via dashboard de la zone).
    """
    return any(sig in content for sig in _CF_MANAGED_SIGNATURES)


def _extract_types(data: object) -> list[str]:
    """Extrae todos los `@type` de un grafo JSON-LD (recursivo)."""
    found: list[str] = []
    if isinstance(data, dict):
        type_val = data.get('@type')
        if isinstance(type_val, str):
            found.append(type_val)
        elif isinstance(type_val, list):
            found.extend(t for t in type_val if isinstance(t, str))
        for value in data.values():
            found.extend(_extract_types(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(_extract_types(item))
    return found


def normalize_url(target: str, path: str) -> str:
    """Construye URL absoluta de un path relativo respecto a target."""
    parsed = urlparse(target)
    base = f'{parsed.scheme}://{parsed.netloc}'
    return f'{base}{path}' if path.startswith('/') else f'{base}/{path}'
