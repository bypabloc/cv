"""
Subpaquete `http`: utilidades de la capa HTTP de las Lambdas.

Agrupa CORS (whitelist de 6 subdominios), construccion de respuestas API
Gateway REST, extraccion de IP/country del evento, validacion del token
Cloudflare Turnstile y sanitizacion de input. Depende de `shared.core`
(excepciones, tipos), `shared.aws.ssm` (Turnstile secret) y
`shared.observability.logger`.

Convencion: importar SIEMPRE desde `shared.http.<modulo>`.
"""

from shared.http.cors import (
    cors_headers,
    is_allowed_origin,
    public_cors_origin,
    resolve_origin,
)
from shared.http.ip_extractor import extract_country, extract_ip
from shared.http.responses import (
    error_response,
    json_response,
    no_content_response,
)
from shared.http.turnstile import verify_turnstile_token
from shared.http.validators import (
    is_valid_country,
    is_valid_email,
    sanitize_text,
)

__all__ = [
    'cors_headers',
    'error_response',
    'extract_country',
    'extract_ip',
    'is_allowed_origin',
    'is_valid_country',
    'is_valid_email',
    'json_response',
    'no_content_response',
    'public_cors_origin',
    'resolve_origin',
    'sanitize_text',
    'verify_turnstile_token',
]
