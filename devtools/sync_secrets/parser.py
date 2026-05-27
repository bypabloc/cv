"""Parser de archivos .env (in-memory, hermetico — no imprime valores).

Soporta la subsintaxis usada por docker/env/{client,server,dev-cli}/.{env}:
- KEY=value
- KEY=                (valor vacio, valido)
- # comment           (lineas ignoradas)
- KEY="quoted value"  (comillas dobles se strippean)
- KEY='quoted value'  (comillas simples se strippean)
"""

from pathlib import Path


class EnvParseError(ValueError):
    """Error parseando un .env. NO contiene el valor."""


def parse_env_file(path: Path) -> dict[str, str]:
    """Lee el .env y devuelve {KEY: value}.

    Hermetico: en caso de error, el mensaje contiene el numero de linea y
    la KEY (si pudo extraerse), NUNCA el value.
    """
    if not path.is_file():
        raise FileNotFoundError(f'No existe: {path}')
    result: dict[str, str] = {}
    with path.open('r', encoding='utf-8') as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip('\n').rstrip('\r')
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue
            if '=' not in stripped:
                raise EnvParseError(
                    f'{path}:{lineno}: linea invalida (sin "="). '
                    'No se imprime el contenido.',
                )
            key, _, value = stripped.partition('=')
            key = key.strip()
            if not key:
                raise EnvParseError(f'{path}:{lineno}: KEY vacia.')
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]
            result[key] = value
    return result


def filter_catalog(
    parsed: dict[str, str],
    catalog: frozenset[str],
) -> dict[str, str]:
    """Subset del parsed que coincide con el catalogo. Hermetico."""
    return {k: v for k, v in parsed.items() if k in catalog}
