"""@module template_service — renderiza plantillas de auth emails.

Soporta los 5 `kind` del plan 01-auth-infra-basics:
  - `register-magic-link`
  - `register-code`
  - `login-magic-link`
  - `login-code`
  - `password-reset`

Para cada kind, busca `core/templates/<locale>/<kind>.txt` y
`<kind>.html`. Renderiza con `string.Template` (placeholders
`${variable}`), evitando dependencias extra (Jinja2, MJML).

Locale: MVP soporta solo `es` (mapeado a `app_config.default_locale`).
El subject viene de un mapa hardcodeado en este modulo (corto, max 60
chars, en espanol).
"""

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Any

from settings.config import app_config

__all__ = [
    'SUPPORTED_KINDS',
    'TemplateNotFoundError',
    'render_template',
]

SUPPORTED_KINDS: tuple[str, ...] = (
    'register-magic-link',
    'register-code',
    'login-magic-link',
    'login-code',
    'password-reset',
    'email-change-verify',
    'email-changed',
    'account-disabled',
    'account-deleted',
)


class TemplateNotFoundError(Exception):
    """El kind solicitado no tiene plantilla en core/templates/<locale>/."""


# templates/ vive dentro de core/. Este archivo esta en core/services/,
# asi que parents[1] = core/.
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / 'templates'

# Subjects por kind (locale='es'). Max 60 chars cada uno.
_SUBJECTS_ES: dict[str, str] = {
    'register-magic-link': 'Activa tu cuenta en the-full-stack.com',
    'register-code': 'Tu codigo de verificacion',
    'login-magic-link': 'Inicia sesion en the-full-stack.com',
    'login-code': 'Tu codigo de acceso',
    'password-reset': 'Restablece tu contrasena',
    'email-change-verify': 'Confirma tu nuevo email en the-full-stack.com',
    'email-changed': 'Tu email fue actualizado',
    'account-disabled': 'Tu cuenta fue deshabilitada',
    'account-deleted': 'Tu cuenta fue eliminada',
}


def render_template(
    *,
    kind: str,
    data: dict[str, Any],
    niche: str | None = None,
) -> tuple[str, str, str]:
    """Renderiza subject + text + html para un kind dado.

    Parameters
    ----------
    kind : str
        Tipo de email (uno de `SUPPORTED_KINDS`).
    data : dict
        Diccionario con los placeholders del template
        (`verify_url`, `code`, `expires_in_min`, ...).
    niche : str | None
        Nicho de origen (reservado para plantillas niche-aware en
        futuros planes). Hoy se ignora.

    Returns
    -------
    tuple[str, str, str]
        `(subject, text_body, html_body)`.

    Raises
    ------
    TemplateNotFoundError
        Si `kind` no esta en `SUPPORTED_KINDS` o no existen los archivos
        `.txt`/`.html` para el locale activo.
    """
    if kind not in SUPPORTED_KINDS:
        raise TemplateNotFoundError(
            f'unknown email kind: {kind!r} (supported: {SUPPORTED_KINDS})',
        )

    locale = app_config.default_locale
    locale_dir = _TEMPLATES_DIR / locale
    txt_path = locale_dir / f'{kind}.txt'
    html_path = locale_dir / f'{kind}.html'

    if not txt_path.is_file() or not html_path.is_file():
        raise TemplateNotFoundError(
            f'template files missing for kind={kind!r} locale={locale!r} '
            f'(expected {txt_path} + {html_path})',
        )

    text_template = txt_path.read_text(encoding='utf-8')
    html_template = html_path.read_text(encoding='utf-8')

    # Context para los placeholders: el dict del mensaje SQS,
    # estringificado. string.Template requiere todos los valores en str.
    context: dict[str, str] = {
        key: ('' if value is None else str(value))
        for key, value in data.items()
    }

    # safe_substitute: si falta un placeholder, deja `${var}` literal en
    # vez de crashear — el caller decide si valida la salida.
    text_body = Template(text_template).safe_substitute(context)
    html_body = Template(html_template).safe_substitute(context)

    subject = _SUBJECTS_ES[kind]

    return subject, text_body, html_body
