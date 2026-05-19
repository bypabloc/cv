"""Envia email al owner usando SES v2 con HTML + plain-text + render template."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import boto3

from _shared.logger import logger
from _shared.ssm_client import get_parameter

_TEMPLATES_DIR = Path(__file__).parent / 'templates'


def _ses_client() -> Any:
    """Lazy SES client (no module-scope para compat con moto)."""
    return boto3.client(
        'sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1')
    )


def _render_mustache_lite(template: str, context: dict[str, Any]) -> str:
    """
    Render minimo mustache-style: {{var}} y {{#var}}block{{/var}} (truthy gates).

    NO uses Jinja2 (peso adicional al Layer). Esto es suficiente para nuestro
    template plano. Si el value es None/empty, el bloque se omite.
    """

    # Conditional blocks: {{#var}}...{{/var}}
    def conditional_replacer(match: re.Match[str]) -> str:
        var = match.group(1)
        block = match.group(2)
        value = context.get(var)
        if value:
            return block.replace(f'{{{{{var}}}}}', str(value))
        return ''

    rendered = re.sub(
        r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}',
        conditional_replacer,
        template,
        flags=re.DOTALL,
    )

    # Simple variables: {{var}}
    def simple_replacer(match: re.Match[str]) -> str:
        var = match.group(1)
        value = context.get(var, '')
        return str(value) if value else ''

    rendered = re.sub(r'\{\{(\w+)\}\}', simple_replacer, rendered)
    return rendered


def parse_recipients(raw: str) -> list[str]:
    """
    Parsea el parametro SSM `owner-email` como lista CSV de destinatarios.

    El parametro puede contener uno o varios correos separados por coma. Se
    aplica trim a cada entrada y se descartan las vacias (tolera comas
    sobrantes o espacios alrededor).

    Args:
        raw: valor crudo del parametro SSM (ej. " a@x.com , b@y.com ").

    Returns:
        Lista de direcciones limpias, sin entradas vacias.

    Example:
        parse_recipients(' a@x.com , b@y.com ')  # ['a@x.com', 'b@y.com']
        parse_recipients('a@x.com,,b@y.com,')    # ['a@x.com', 'b@y.com']
    """
    return [item.strip() for item in raw.split(',') if item.strip()]


def send_owner_email(contact: dict[str, Any]) -> str:
    """
    Envia un email transaccional al owner del portfolio.

    Args:
        contact: dict con name, email, message, contact_id, created_at, etc.

    Returns:
        SES MessageId.
    """
    from_address_path = os.environ.get(
        'SSM_SES_FROM_PATH', '/portfolio/ses-from-address'
    )
    owner_email_path = os.environ.get(
        'SSM_OWNER_EMAIL_PATH', '/portfolio/owner-email'
    )

    from_address = get_parameter(from_address_path)
    recipients = parse_recipients(get_parameter(owner_email_path))

    # Render templates
    html_template = (_TEMPLATES_DIR / 'owner_email.html').read_text(
        encoding='utf-8'
    )
    text_template = (_TEMPLATES_DIR / 'owner_email.txt').read_text(
        encoding='utf-8'
    )

    context = {**contact, 'niche': contact.get('niche', 'generic')}
    html_body = _render_mustache_lite(html_template, context)
    text_body = _render_mustache_lite(text_template, context)

    subject = f'Portfolio · Nuevo contacto de {contact.get("name", "")} ({contact.get("niche", "generic")})'

    response = _ses_client().send_email(
        FromEmailAddress=f'The Full Stack <{from_address}>',
        Destination={'ToAddresses': recipients},
        ReplyToAddresses=[contact.get('email', from_address)],
        Content={
            'Simple': {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                },
            },
        },
    )

    message_id: str = response.get('MessageId', '')
    logger.info(
        'owner email sent',
        extra={
            'message_id': message_id,
            'contact_id': contact.get('contact_id'),
            'recipient_count': len(recipients),
        },
    )
    return message_id
