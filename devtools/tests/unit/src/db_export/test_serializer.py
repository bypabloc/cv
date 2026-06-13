"""Unit tests de db_export.serializer (funciones puras filas -> YAML).

Path mirroring: devtools/db_export/serializer.py -> este archivo.
Asserts EXACTOS sobre los dicts producidos: el shape es el contrato que
consumen los upserts de `cv_write_entities` (round-trip del seed).
"""

from datetime import date

import pytest
import yaml

from db_export.serializer import bilang
from db_export.serializer import dump_yaml
from db_export.serializer import format_date
from db_export.serializer import serialize_award
from db_export.serializer import serialize_certificate
from db_export.serializer import serialize_education
from db_export.serializer import serialize_endorsement
from db_export.serializer import serialize_experience
from db_export.serializer import serialize_language
from db_export.serializer import serialize_profile
from db_export.serializer import serialize_project
from db_export.serializer import serialize_publication
from db_export.serializer import serialize_skill_category


pytestmark = pytest.mark.unit


def test_format_date_when_day_is_first_then_yyyy_mm():
    """
    Given un DATE con day == 1 (la forma que produce coerce_date('YYYY-MM')),
    When format_date,
    Then devuelve 'YYYY-MM' (forma canonica del seed).
    """
    assert format_date(date(2022, 8, 1)) == '2022-08'


def test_format_date_when_day_not_first_then_iso_full():
    """
    Given un DATE con day != 1 (certificados con fecha completa),
    When format_date,
    Then devuelve 'YYYY-MM-DD'.
    """
    assert format_date(date(2023, 4, 20)) == '2023-04-20'


def test_format_date_when_none_then_none():
    """
    Given None (ended_on de una experiencia en curso),
    When format_date,
    Then devuelve None (la key se omite en el YAML).
    """
    assert format_date(None) is None


def test_bilang_when_both_locales_then_es_first():
    """
    Given un campo i18n con es + en,
    When bilang,
    Then devuelve {'es': ..., 'en': ...} en ese orden exacto.
    """
    fields = {'role': {'en': 'Architect', 'es': 'Arquitecto'}}

    result = bilang(fields, 'role')

    assert result == {'es': 'Arquitecto', 'en': 'Architect'}
    assert list(result) == ['es', 'en']


def test_bilang_when_field_missing_then_none():
    """
    Given un campo inexistente en el mapa i18n,
    When bilang,
    Then devuelve None (la key se omite en el YAML).
    """
    assert bilang({'role': {'es': 'X'}}, 'summary') is None


def test_serialize_experience_assembles_full_seed_shape():
    """
    Given una fila de cv_experiences con i18n, bullets desordenados,
      skills, niches y priority,
    When serialize_experience,
    Then produce EXACTAMENTE el dict YAML que consume upsert_experience
      (bullets re-ordenados por position, fechas YYYY-MM).
    """
    row = {
        'id': 'e1',
        'slug': 'destacame-architect',
        'company': 'Destacame',
        'country': 'Chile',
        'company_url': 'https://destacame.cl',
        'started_on': date(2022, 8, 1),
        'ended_on': date(2024, 1, 1),
        'seniority': 'lead',
        'metrics_estimated': True,
    }
    fields = {
        'role': {'es': 'Arquitecto', 'en': 'Architect'},
        'summary': {'es': 'Resumen', 'en': 'Summary'},
    }
    bullets = [
        {'kind': 'responsibility', 'position': 1, 'es': 'R2', 'en': 'R2en'},
        {'kind': 'responsibility', 'position': 0, 'es': 'R1', 'en': 'R1en'},
        {'kind': 'achievement', 'position': 0, 'es': 'A1', 'en': 'A1en'},
    ]
    skills = {'technical': ['Python', 'Vue 3'], 'soft': ['Liderazgo']}

    result = serialize_experience(
        row,
        fields=fields,
        bullets=bullets,
        skills=skills,
        niches=['fintech', 'generic'],
        priority={'fintech': 100, 'generic': 80},
    )

    assert result == {
        'slug': 'destacame-architect',
        'role': {'es': 'Arquitecto', 'en': 'Architect'},
        'company': 'Destacame',
        'country': 'Chile',
        'companyUrl': 'https://destacame.cl',
        'start': '2022-08',
        'end': '2024-01',
        'seniority': 'lead',
        'niches': ['fintech', 'generic'],
        'priority': {'fintech': 100, 'generic': 80},
        'metricsEstimated': True,
        'summary': {'es': 'Resumen', 'en': 'Summary'},
        'responsibilities': {'es': ['R1', 'R2'], 'en': ['R1en', 'R2en']},
        'achievements': {'es': ['A1'], 'en': ['A1en']},
        'skillsTechnical': ['Python', 'Vue 3'],
        'skillsSoft': ['Liderazgo'],
    }


def test_serialize_experience_omits_end_and_false_bool():
    """
    Given una experiencia en curso (ended_on None) con
      metrics_estimated False y sin company_url ni summary,
    When serialize_experience,
    Then omite 'end', 'metricsEstimated', 'companyUrl' y 'summary'.
    """
    row = {
        'id': 'e1',
        'slug': 'goodmeal',
        'company': 'GoodMeal',
        'country': 'Chile',
        'company_url': None,
        'started_on': date(2021, 3, 1),
        'ended_on': None,
        'seniority': 'senior',
        'metrics_estimated': False,
    }

    result = serialize_experience(
        row,
        fields={'role': {'es': 'Dev', 'en': 'Dev'}},
        bullets=[],
        skills={},
        niches=['generic'],
        priority=None,
    )

    assert result == {
        'slug': 'goodmeal',
        'role': {'es': 'Dev', 'en': 'Dev'},
        'company': 'GoodMeal',
        'country': 'Chile',
        'start': '2021-03',
        'seniority': 'senior',
        'niches': ['generic'],
    }


def test_serialize_project_assembles_full_seed_shape():
    """
    Given una fila de cv_projects con case study detallado, metricas
      ordenadas, stack, links JSONB y flags True,
    When serialize_project,
    Then produce el dict exacto con caseStudy/caseStudyDetailed/metrics
      en orden de position y links tal cual.
    """
    row = {
        'id': 'p1',
        'slug': 'faststruct',
        'name': 'FastStruct',
        'url': 'https://marketplace.example/faststruct',
        'links': [{'label': 'Docs', 'url': 'https://docs.example'}],
        'repo': 'https://github.com/bypabloc/faststruct',
        'status': 'active',
        'project_type': 'cli',
        'is_confidential': True,
        'metrics_estimated': True,
    }
    fields = {
        'summary': {'es': 'S', 'en': 'Sen'},
        'description': {'es': 'D', 'en': 'Den'},
        'case_study': {'es': 'CS', 'en': 'CSen'},
    }
    case_study = {
        'problem': {'es': 'P', 'en': 'Pen'},
        'process': {'es': 'Pr', 'en': 'Pren'},
        'result': {'es': 'R', 'en': 'Ren'},
    }
    metrics = [('speedup', '5x'), ('adoption', 'Marketplace')]

    result = serialize_project(
        row,
        fields=fields,
        case_study=case_study,
        metrics=metrics,
        stack=['TypeScript', 'Node.js'],
        niches=['vibe', 'generic'],
        priority={'vibe': 80, 'generic': 65},
    )

    assert result == {
        'slug': 'faststruct',
        'name': 'FastStruct',
        'summary': {'es': 'S', 'en': 'Sen'},
        'description': {'es': 'D', 'en': 'Den'},
        'url': 'https://marketplace.example/faststruct',
        'links': [{'label': 'Docs', 'url': 'https://docs.example'}],
        'repo': 'https://github.com/bypabloc/faststruct',
        'status': 'active',
        'projectType': 'cli',
        'isConfidential': True,
        'niches': ['vibe', 'generic'],
        'priority': {'vibe': 80, 'generic': 65},
        'stack': ['TypeScript', 'Node.js'],
        'caseStudy': {'es': 'CS', 'en': 'CSen'},
        'caseStudyDetailed': {
            'problem': {'es': 'P', 'en': 'Pen'},
            'process': {'es': 'Pr', 'en': 'Pren'},
            'result': {'es': 'R', 'en': 'Ren'},
        },
        'metrics': {'speedup': '5x', 'adoption': 'Marketplace'},
        'metricsEstimated': True,
    }
    assert list(result['metrics']) == ['speedup', 'adoption']


def test_serialize_project_minimal_omits_empty_blocks():
    """
    Given un proyecto sin case study, metrics, stack, links ni flags,
    When serialize_project,
    Then solo quedan las keys con valor.
    """
    row = {
        'id': 'p1',
        'slug': 'mvp',
        'name': 'MVP',
        'url': None,
        'links': None,
        'repo': None,
        'status': 'active',
        'project_type': 'web',
        'is_confidential': False,
        'metrics_estimated': False,
    }

    result = serialize_project(
        row,
        fields={'summary': {'es': 'S', 'en': 'Sen'}},
        case_study=None,
        metrics=[],
        stack=[],
        niches=['generic'],
        priority=None,
    )

    assert result == {
        'slug': 'mvp',
        'name': 'MVP',
        'summary': {'es': 'S', 'en': 'Sen'},
        'status': 'active',
        'projectType': 'web',
        'niches': ['generic'],
    }


def test_serialize_profile_assembles_contacts_and_stats():
    """
    Given la fila singleton de cv_profiles + stats + i18n + niches,
    When serialize_profile,
    Then produce el dict exacto de profile.yaml (contacts anidados,
      stats en camelCase).
    """
    row = {
        'id': 'pr1',
        'name': 'Pablo Contreras',
        'handle': 'bypabloc',
        'location': 'Lima, Peru',
        'email': 'user@example.com',
        'phone': '+51 900000000',
        'linkedin_url': 'https://linkedin.com/in/bypabloc',
        'github_url': 'https://github.com/bypabloc',
        'website_url': 'https://the-full-stack.com',
        'avatar_url': 'https://cdn.example/1.avif',
    }
    stats = {
        'years_experience': 12,
        'companies': 8,
        'countries': 4,
        'certifications': 11,
    }
    fields = {
        'headline': {'es': 'H', 'en': 'Hen'},
        'summary': {'es': 'S', 'en': 'Sen'},
        'availability': {'es': 'A', 'en': 'Aen'},
    }

    result = serialize_profile(
        row,
        stats=stats,
        fields=fields,
        niches=['fintech', 'generic'],
    )

    assert result == {
        'name': 'Pablo Contreras',
        'handle': 'bypabloc',
        'headline': {'es': 'H', 'en': 'Hen'},
        'summary': {'es': 'S', 'en': 'Sen'},
        'location': 'Lima, Peru',
        'availability': {'es': 'A', 'en': 'Aen'},
        'contacts': {
            'email': 'user@example.com',
            'phone': '+51 900000000',
            'linkedin': 'https://linkedin.com/in/bypabloc',
            'github': 'https://github.com/bypabloc',
            'website': 'https://the-full-stack.com',
        },
        'avatarUrl': 'https://cdn.example/1.avif',
        'niches': ['fintech', 'generic'],
        'stats': {
            'yearsExperience': 12,
            'companies': 8,
            'countries': 4,
            'certifications': 11,
        },
    }


def test_serialize_certificate_keeps_full_date():
    """
    Given un certificado con issued_on de dia completo,
    When serialize_certificate,
    Then 'date' queda 'YYYY-MM-DD' y no hay keys i18n.
    """
    row = {
        'id': 'c1',
        'slug': 'docker-2023',
        'title': 'Docker',
        'issuer': 'DevTalles',
        'issued_on': date(2023, 4, 20),
        'url': 'https://cursos.example/cert',
    }

    result = serialize_certificate(
        row,
        niches=['architect', 'generic'],
        priority=None,
    )

    assert result == {
        'slug': 'docker-2023',
        'title': 'Docker',
        'issuer': 'DevTalles',
        'date': '2023-04-20',
        'url': 'https://cursos.example/cert',
        'niches': ['architect', 'generic'],
    }


def test_serialize_award_assembles_bilang_blocks():
    """
    Given un premio con title + motivation bilingues,
    When serialize_award,
    Then 'date' queda 'YYYY-MM' y los bloques bilingues exactos.
    """
    row = {
        'id': 'a1',
        'slug': 'innovator-2023',
        'issuer': 'Destacame',
        'awarded_on': date(2024, 1, 1),
        'url': 'https://heyzine.example/x',
    }
    fields = {
        'title': {'es': 'Innovador', 'en': 'Innovator'},
        'motivation': {'es': 'M', 'en': 'Men'},
    }

    result = serialize_award(
        row,
        fields=fields,
        niches=['generic'],
        priority=None,
    )

    assert result == {
        'slug': 'innovator-2023',
        'title': {'es': 'Innovador', 'en': 'Innovator'},
        'issuer': 'Destacame',
        'date': '2024-01',
        'url': 'https://heyzine.example/x',
        'motivation': {'es': 'M', 'en': 'Men'},
        'niches': ['generic'],
    }


def test_serialize_education_omits_end_when_ongoing():
    """
    Given formacion en curso (ended_on None, sin degree),
    When serialize_education,
    Then omite 'end' y 'degree'; 'start' queda 'YYYY-MM'.
    """
    row = {
        'id': 'ed1',
        'slug': 'udemy',
        'institution': 'Udemy',
        'started_on': date(2017, 1, 1),
        'ended_on': None,
        'url': 'https://udemy.com',
    }

    result = serialize_education(
        row,
        fields={'description': {'es': 'D', 'en': 'Den'}},
        niches=None,
        priority=None,
    )

    assert result == {
        'slug': 'udemy',
        'institution': 'Udemy',
        'start': '2017-01',
        'url': 'https://udemy.com',
        'description': {'es': 'D', 'en': 'Den'},
    }


def test_serialize_endorsement_maps_linkedin_url():
    """
    Given una recomendacion con company y relation bilingue,
    When serialize_endorsement,
    Then 'linkedin_url' se exporta como 'linkedin'.
    """
    row = {
        'id': 'en1',
        'slug': 'alan-vergara',
        'name': 'Alan Vergara',
        'role': 'Software Architect',
        'company': 'Destacame',
        'linkedin_url': 'https://www.linkedin.com/in/alan',
    }

    result = serialize_endorsement(
        row,
        fields={'relation': {'es': 'Companero', 'en': 'Teammate'}},
        niches=None,
        priority=None,
    )

    assert result == {
        'slug': 'alan-vergara',
        'name': 'Alan Vergara',
        'role': 'Software Architect',
        'company': 'Destacame',
        'linkedin': 'https://www.linkedin.com/in/alan',
        'relation': {'es': 'Companero', 'en': 'Teammate'},
    }


def test_serialize_language_minimal():
    """
    Given un idioma con solo name + level bilingues (sin niches),
    When serialize_language,
    Then el dict tiene exactamente slug + name + level.
    """
    row = {'id': 'l1', 'slug': 'english'}
    fields = {
        'name': {'es': 'Ingles', 'en': 'English'},
        'level': {'es': 'Intermedio', 'en': 'Intermediate'},
    }

    result = serialize_language(
        row,
        fields=fields,
        niches=None,
        priority=None,
    )

    assert result == {
        'slug': 'english',
        'name': {'es': 'Ingles', 'en': 'English'},
        'level': {'es': 'Intermedio', 'en': 'Intermediate'},
    }


def test_serialize_publication_maps_canonical_url():
    """
    Given una publicacion con canonical_url y published_on,
    When serialize_publication,
    Then 'canonical_url' -> 'canonical' y 'published_on' -> 'date'.
    """
    row = {
        'id': 'pu1',
        'slug': 'post-astro',
        'title': 'Astro 6',
        'platform': 'dev.to',
        'url': 'https://dev.to/x',
        'canonical_url': 'https://the-full-stack.com/blog/x',
        'published_on': date(2026, 2, 1),
    }

    result = serialize_publication(
        row,
        fields={'summary': {'es': 'S', 'en': 'Sen'}},
        niches=['vibe'],
        priority=None,
    )

    assert result == {
        'slug': 'post-astro',
        'title': 'Astro 6',
        'platform': 'dev.to',
        'url': 'https://dev.to/x',
        'canonical': 'https://the-full-stack.com/blog/x',
        'date': '2026-02',
        'summary': {'es': 'S', 'en': 'Sen'},
        'niches': ['vibe'],
    }


def test_serialize_skill_category_orders_keys():
    """
    Given una categoria con skills ordenadas por position,
    When serialize_skill_category,
    Then el dict preserva la lista exacta y el kind.
    """
    row = {'id': 's1', 'slug': 'frontend', 'kind': 'technical'}

    result = serialize_skill_category(
        row,
        fields={'name': {'es': 'Frontend', 'en': 'Frontend'}},
        skills=['Vue 3', 'Nuxt.js', 'TypeScript'],
        niches=['fintech', 'generic'],
    )

    assert result == {
        'slug': 'frontend',
        'name': {'es': 'Frontend', 'en': 'Frontend'},
        'skills': ['Vue 3', 'Nuxt.js', 'TypeScript'],
        'kind': 'technical',
        'niches': ['fintech', 'generic'],
    }


def test_dump_yaml_round_trips_and_preserves_key_order():
    """
    Given un dict seed-shape con orden de keys significativo,
    When dump_yaml + yaml.safe_load,
    Then el round-trip devuelve el dict identico y el texto arranca
      con la primera key (sort_keys=False).
    """
    data = {'slug': 'x', 'role': {'es': 'A', 'en': 'B'}, 'start': '2022-08'}

    text = dump_yaml(data)

    assert yaml.safe_load(text) == data
    assert text.startswith('slug: x')
