"""@module shared.templating.jinja — render de templates con Jinja2.

Portador unico de `jinja2`. El `core/` de `send_email` NUNCA importa `jinja2`
directo: usa `from shared.templating.jinja import render_html, render_text`.

- `render_html`: autoescape ON (anti-XSS en las vars del visitante, ej. el
  mensaje del form de contacto que va al email del owner).
- `render_text`: autoescape OFF (texto plano + subject; no se escapa `&`/`<`).
- `StrictUndefined`: si falta una var del contexto, lanza `TemplateRenderError`
  en vez de renderizar un hueco silencioso (un email a medias es peor que
  fallar ruidoso y reintentar).

`jinja2` se importa LAZY dentro de las funciones (no en el top del modulo)
para no penalizar el cold de un Lambda que importe el modulo sin renderizar.
Ver `.claude/rules/lambda-config.md`.
"""

from __future__ import annotations

from typing import Any


class TemplateRenderError(Exception):
    """Fallo al renderizar un template (sintaxis o variable faltante)."""


def _render(template_str: str, context: dict[str, Any], *, autoescape: bool) -> str:
    """Renderiza `template_str` con `context` (StrictUndefined)."""
    from jinja2 import Environment, StrictUndefined, TemplateError

    env = Environment(autoescape=autoescape, undefined=StrictUndefined)
    try:
        return env.from_string(template_str).render(**context)
    except TemplateError as exc:
        raise TemplateRenderError(str(exc)) from exc


def render_html(template_str: str, context: dict[str, Any]) -> str:
    """Renderiza un template HTML con autoescape (anti-XSS)."""
    return _render(template_str, context, autoescape=True)


def render_text(template_str: str, context: dict[str, Any]) -> str:
    """Renderiza un template de texto plano / subject (sin escape)."""
    return _render(template_str, context, autoescape=False)
