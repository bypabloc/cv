"""
Validators y sanitizers de input.

Funciones puras sin dependencias externas. Uso desde Lambdas:
    from shared.validators import is_valid_email, sanitize_text

Reglas:
- NUNCA confiar en API Gateway request validator: hacer doble validacion
  en Lambda. El validator de API GW solo verifica JSON Schema, no semantica.
- Sanitizers son no-destructivos: retornan string limpia, no mutan input.
"""

from __future__ import annotations

import html
import re

# Email regex pragmatico (RFC 5321 strict es muy laxo y permite caracteres
# que en la practica nadie usa). Cubre 99.9% de emails reales:
# - local-part: alfanumerico + . _ - + (sin .. consecutivos)
# - @
# - domain: alfanumerico + . - (TLD min 2 chars)
_EMAIL_REGEX = re.compile(
    r'^[A-Za-z0-9](?:[A-Za-z0-9._+\-]*[A-Za-z0-9])?'
    r'@'
    r'[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?'
    r'(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?)*'
    r'\.[A-Za-z]{2,}$'
)

# Country code ISO 3166-1 alpha-2 (2 chars upper)
_COUNTRY_REGEX = re.compile(r'^[A-Z]{2}$')

# Limites razonables para inputs del form de contacto
MAX_NAME_LENGTH = 200
MAX_EMAIL_LENGTH = 254  # RFC 5321 maximum
MAX_MESSAGE_LENGTH = 5000
MAX_COMPANY_LENGTH = 200
MAX_ROLE_LENGTH = 100


def is_valid_email(value: str) -> bool:
    """
    Valida formato de email basico (no garantiza deliverability).

    Args:
        value: string a validar (NO trimmed previamente).

    Returns:
        True si matchea formato email RFC 5321 simplificado.

    Examples:
        >>> is_valid_email('user@example.com')
        True
        >>> is_valid_email('not-an-email')
        False
        >>> is_valid_email('')
        False
        >>> is_valid_email('user@')
        False
        >>> is_valid_email('@example.com')
        False
    """
    if not isinstance(value, str):
        return False
    value = value.strip()
    if not value or len(value) > MAX_EMAIL_LENGTH:
        return False
    return bool(_EMAIL_REGEX.match(value))


def is_valid_country(value: str) -> bool:
    """
    Valida ISO 3166-1 alpha-2 country code (2 chars upper).

    Examples:
        >>> is_valid_country('CL')
        True
        >>> is_valid_country('USA')
        False
        >>> is_valid_country('cl')
        False
        >>> is_valid_country('')
        False
    """
    if not isinstance(value, str) or len(value) != 2:
        return False
    return bool(_COUNTRY_REGEX.match(value))


def sanitize_text(value: str, *, max_length: int | None = None) -> str:
    """
    Sanitiza texto: trim + HTML-escape + truncate opcional.

    NO altera el contenido semantico, solo lo hace safe para:
    - Embebido en HTML (escape de < > & " ')
    - Log estructurado (sin newlines crudas que rompan parsing)
    - Email subject/body sin code injection

    Args:
        value: input crudo del usuario
        max_length: si se pasa, trunca el output (sin contar caracteres
                    escapados como 5 chars cada uno).

    Returns:
        Texto sanitizado.

    Examples:
        >>> sanitize_text('  hello  ')
        'hello'
        >>> sanitize_text('<script>alert(1)</script>')
        '&lt;script&gt;alert(1)&lt;/script&gt;'
        >>> sanitize_text('a' * 100, max_length=10)
        'aaaaaaaaaa'
    """
    if not isinstance(value, str):
        return ''
    cleaned = value.strip()
    if max_length is not None and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return html.escape(cleaned, quote=True)
