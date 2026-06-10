"""@module serializer — filas de Neon -> dicts con el shape YAML del seed.

Funciones PURAS (sin DB, sin AWS): reciben filas ya leidas por
`queries.py` y devuelven dicts con EXACTAMENTE las claves que consumen
los upserts de `shared.db.repositories.cv_write_entities` (camelCase,
bloques bilingues `{es, en}`, `niches`, `priority`). Garantia
round-trip: export -> seed(restore) -> export produce el mismo YAML.

Convenciones:
- Keys con valor None / lista vacia / dict vacio se OMITEN (igual que
  los YAML originales del seed).
- Bools con default False (`metricsEstimated`, `isConfidential`) se
  omiten cuando son False (mismo criterio que los YAML originales).
- Fechas DATE -> 'YYYY-MM' si day == 1, sino 'YYYY-MM-DD'. El
  `coerce_date` del seed re-parsea ambas formas a la misma fila.
"""

from datetime import date
from typing import Any

import yaml


# Un campo bilingue: {'es': ..., 'en': ...} (cualquiera puede faltar).
type Bilang = dict[str, str]
# Mapa field -> Bilang de UNA entidad (subset de i18n_translations).
type I18nFields = dict[str, Bilang]
# Dict final con el shape YAML del seed.
type YamlDict = dict[str, Any]


def format_date(value: date | None) -> str | None:
    """Convierte un DATE de Neon al formato string del YAML seed.

    day == 1 -> 'YYYY-MM' (la forma canonica de los YAML del seed);
    cualquier otro day -> 'YYYY-MM-DD'. None -> None (key omitida).
    """
    if value is None:
        return None
    if value.day == 1:
        return f'{value.year:04d}-{value.month:02d}'
    return value.isoformat()


def bilang(fields: I18nFields | None, field: str) -> Bilang | None:
    """Extrae el bloque bilingue `{es, en}` de un campo i18n.

    Solo incluye los locales presentes; None si el campo no existe.
    """
    block = (fields or {}).get(field) or {}
    out = {
        locale: block[locale]
        for locale in ('es', 'en')
        if block.get(locale) is not None
    }
    return out or None


def _clean(data: YamlDict) -> YamlDict:
    """Omite keys con None o coleccion vacia (shape de los YAML seed)."""
    return {
        key: value
        for key, value in data.items()
        if value is not None and value != [] and value != {}
    }


def dump_yaml(data: YamlDict) -> str:
    """Serializa un dict al YAML del snapshot (orden de keys preservado)."""
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )


def serialize_profile(
    row: dict[str, Any],
    *,
    stats: dict[str, Any] | None,
    fields: I18nFields | None,
    niches: list[str] | None,
) -> YamlDict:
    """Arma `profile.yaml` (singleton) con contacts + stats + i18n."""
    contacts = _clean(
        {
            'email': row['email'],
            'phone': row['phone'],
            'linkedin': row['linkedin_url'],
            'github': row['github_url'],
            'website': row['website_url'],
        }
    )
    stats_block = (
        _clean(
            {
                'yearsExperience': stats['years_experience'],
                'companies': stats['companies'],
                'countries': stats['countries'],
                'certifications': stats['certifications'],
            }
        )
        if stats
        else None
    )
    return _clean(
        {
            'name': row['name'],
            'handle': row['handle'],
            'headline': bilang(fields, 'headline'),
            'summary': bilang(fields, 'summary'),
            'location': row['location'],
            'availability': bilang(fields, 'availability'),
            'contacts': contacts,
            'avatarUrl': row['avatar_url'],
            'niches': niches,
            'stats': stats_block,
        }
    )


def _bullet_block(
    bullets: list[dict[str, Any]],
    kind: str,
) -> Bilang | None:
    """Reconstruye `{es: [...], en: [...]}` de los bullets de un kind.

    Ordena por position y arma cada lista con los textos no-nulos del
    locale (mismo criterio con que el seed los inserto).
    """
    rows = sorted(
        (b for b in bullets if b['kind'] == kind),
        key=lambda b: b['position'],
    )
    block = {
        locale: [b[locale] for b in rows if b.get(locale) is not None]
        for locale in ('es', 'en')
    }
    return _clean(block) or None


def serialize_experience(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    bullets: list[dict[str, Any]],
    skills: dict[str, list[str]],
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma una experiencia (fila + bullets + skills + i18n)."""
    return _clean(
        {
            'slug': row['slug'],
            'role': bilang(fields, 'role'),
            'company': row['company'],
            'country': row['country'],
            'companyUrl': row['company_url'],
            'start': format_date(row['started_on']),
            'end': format_date(row['ended_on']),
            'seniority': row['seniority'],
            'niches': niches,
            'priority': priority,
            'metricsEstimated': row['metrics_estimated'] or None,
            'summary': bilang(fields, 'summary'),
            'responsibilities': _bullet_block(bullets, 'responsibility'),
            'achievements': _bullet_block(bullets, 'achievement'),
            'skillsTechnical': skills.get('technical'),
            'skillsSoft': skills.get('soft'),
        }
    )


def serialize_project(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    case_study: I18nFields | None,
    metrics: list[tuple[str, str]],
    stack: list[str],
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma un proyecto (fila + case study + metricas ordenadas + stack)."""
    detailed = (
        _clean(
            {
                'problem': bilang(case_study, 'problem'),
                'process': bilang(case_study, 'process'),
                'result': bilang(case_study, 'result'),
            }
        )
        if case_study
        else None
    )
    return _clean(
        {
            'slug': row['slug'],
            'name': row['name'],
            'summary': bilang(fields, 'summary'),
            'description': bilang(fields, 'description'),
            'url': row['url'],
            'links': row['links'],
            'repo': row['repo'],
            'status': row['status'],
            'projectType': row['project_type'],
            'isConfidential': row['is_confidential'] or None,
            'niches': niches,
            'priority': priority,
            'stack': stack,
            'caseStudy': bilang(fields, 'case_study'),
            'caseStudyDetailed': detailed,
            'metrics': dict(metrics),
            'metricsEstimated': row['metrics_estimated'] or None,
        }
    )


def serialize_skill_category(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    skills: list[str],
    niches: list[str] | None,
) -> YamlDict:
    """Arma una categoria de skills (name bilingue + skills ordenadas)."""
    return _clean(
        {
            'slug': row['slug'],
            'name': bilang(fields, 'name'),
            'skills': skills,
            'kind': row['kind'],
            'niches': niches,
        }
    )


def serialize_certificate(
    row: dict[str, Any],
    *,
    fields: I18nFields | None = None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma un certificado (sin campos i18n propios)."""
    del fields  # los certificados no tienen textos bilingues
    return _clean(
        {
            'slug': row['slug'],
            'title': row['title'],
            'issuer': row['issuer'],
            'date': format_date(row['issued_on']),
            'url': row['url'],
            'niches': niches,
            'priority': priority,
        }
    )


def serialize_award(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma un premio (title + motivation bilingues)."""
    return _clean(
        {
            'slug': row['slug'],
            'title': bilang(fields, 'title'),
            'issuer': row['issuer'],
            'date': format_date(row['awarded_on']),
            'url': row['url'],
            'motivation': bilang(fields, 'motivation'),
            'niches': niches,
            'priority': priority,
        }
    )


def serialize_education(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma una entrada de formacion (degree + description bilingues)."""
    return _clean(
        {
            'slug': row['slug'],
            'institution': row['institution'],
            'start': format_date(row['started_on']),
            'end': format_date(row['ended_on']),
            'url': row['url'],
            'degree': bilang(fields, 'degree'),
            'description': bilang(fields, 'description'),
            'niches': niches,
            'priority': priority,
        }
    )


def serialize_endorsement(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma una recomendacion (relation bilingue, linkedin_url -> linkedin)."""
    return _clean(
        {
            'slug': row['slug'],
            'name': row['name'],
            'role': row['role'],
            'company': row['company'],
            'linkedin': row['linkedin_url'],
            'relation': bilang(fields, 'relation'),
            'niches': niches,
            'priority': priority,
        }
    )


def serialize_language(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma un idioma (name + level bilingues)."""
    return _clean(
        {
            'slug': row['slug'],
            'name': bilang(fields, 'name'),
            'level': bilang(fields, 'level'),
            'niches': niches,
            'priority': priority,
        }
    )


def serialize_publication(
    row: dict[str, Any],
    *,
    fields: I18nFields | None,
    niches: list[str] | None,
    priority: dict[str, int] | None,
) -> YamlDict:
    """Arma una publicacion (canonical_url -> canonical, summary bilingue)."""
    return _clean(
        {
            'slug': row['slug'],
            'title': row['title'],
            'platform': row['platform'],
            'url': row['url'],
            'canonical': row['canonical_url'],
            'date': format_date(row['published_on']),
            'summary': bilang(fields, 'summary'),
            'niches': niches,
            'priority': priority,
        }
    )
