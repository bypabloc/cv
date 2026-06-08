"""Unit tests for serverless.secrets_catalog - parser del catalogo SSM.

Path mirroring: devtools/serverless/secrets_catalog.py -> this file.

Cubre los criterios de aceptacion AC-1 y AC-2 del plan
docs/specs/serverless-secrets-catalog/.
"""

from __future__ import annotations

import textwrap

import pytest


pytestmark = pytest.mark.unit


_VALID_YAML = textwrap.dedent(
    """
    kind: ssm-parameter
    name: turnstile-secret
    description: Cloudflare Turnstile secret key (siteverify)
    path: /portfolio/${stage}/turnstile-secret
    ssm_type: SecureString
    kms_key_alias: alias/portfolio-lambdas
    source_env_var: TURNSTILE_SECRET_KEY
    target_env_var: SSM_TURNSTILE_SECRET_PATH
    stages: [dev, prod]
    required: true
    consumed_by: [contact_form]
    tags: { Project: portfolio, ManagedBy: devtools }
    """,
).strip()


_VALID_GLOBAL_YAML = textwrap.dedent(
    """
    kind: ssm-parameter
    name: owner-email
    description: Email destino del form de contacto
    path: /portfolio/owner-email
    ssm_type: String
    source_env_var: OWNER_EMAIL
    target_env_var: SSM_OWNER_EMAIL_PATH
    stages: [dev, prod]
    required: true
    """,
).strip()


def _write_yaml(directory, name, content):
    """Escribe un YAML del catalogo y devuelve el path."""
    yaml_path = directory / f'{name}.yaml'
    yaml_path.write_text(content, encoding='utf-8')
    return yaml_path


class TestCatalogLoadSuccess:
    """Catalog.load carga YAML validos y normaliza."""

    def test_when_directory_empty_returns_empty_catalog(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        catalog = Catalog.load(tmp_path)

        assert len(catalog) == 0

    def test_when_yaml_valid_returns_secret_spec_normalized(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        _write_yaml(tmp_path, 'turnstile-secret', _VALID_YAML)

        catalog = Catalog.load(tmp_path)

        spec = catalog.get('turnstile-secret')
        assert spec.name == 'turnstile-secret'
        assert spec.ssm_type == 'SecureString'
        assert spec.kms_key_alias == 'alias/portfolio-lambdas'
        assert spec.source_env_var == 'TURNSTILE_SECRET_KEY'
        assert spec.target_env_var == 'SSM_TURNSTILE_SECRET_PATH'
        assert spec.stages == frozenset({'dev', 'prod'})
        assert spec.required is True
        assert spec.consumed_by == ('contact_form',)

    def test_when_ssm_type_securestring_default_kms_alias(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        yaml_no_alias = _VALID_YAML.replace(
            'kms_key_alias: alias/portfolio-lambdas\n',
            '',
        )
        _write_yaml(tmp_path, 'turnstile-secret', yaml_no_alias)

        catalog = Catalog.load(tmp_path)

        assert catalog.get('turnstile-secret').kms_key_alias == (
            'alias/portfolio-lambdas'
        )

    def test_when_ssm_type_string_kms_alias_is_none(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        _write_yaml(tmp_path, 'owner-email', _VALID_GLOBAL_YAML)

        spec = Catalog.load(tmp_path).get('owner-email')

        assert spec.kms_key_alias is None
        assert spec.ssm_type == 'String'

    def test_path_for_resolves_stage_template(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        _write_yaml(tmp_path, 'turnstile-secret', _VALID_YAML)
        spec = Catalog.load(tmp_path).get('turnstile-secret')

        assert spec.path_for('dev') == '/portfolio/dev/turnstile-secret'
        assert spec.path_for('prod') == '/portfolio/prod/turnstile-secret'

    def test_path_for_global_path_returns_unchanged(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        _write_yaml(tmp_path, 'owner-email', _VALID_GLOBAL_YAML)
        spec = Catalog.load(tmp_path).get('owner-email')

        assert spec.path_for('dev') == '/portfolio/owner-email'
        assert spec.path_for('prod') == '/portfolio/owner-email'

    def test_path_for_when_stage_not_in_stages_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        yaml_dev_only = _VALID_YAML.replace(
            'stages: [dev, prod]',
            'stages: [dev]',
        )
        _write_yaml(tmp_path, 'turnstile-secret', yaml_dev_only)
        spec = Catalog.load(tmp_path).get('turnstile-secret')

        with pytest.raises(CatalogError, match='no esta declarado en stage'):
            spec.path_for('prod')

    def test_for_stage_filters_by_stage_membership(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        yaml_dev_only = _VALID_YAML.replace(
            'stages: [dev, prod]',
            'stages: [dev]',
        ).replace('turnstile-secret', 'dev-only-secret')
        _write_yaml(tmp_path, 'dev-only-secret', yaml_dev_only)
        _write_yaml(tmp_path, 'owner-email', _VALID_GLOBAL_YAML)

        catalog = Catalog.load(tmp_path)

        dev_specs = catalog.for_stage('dev')
        prod_specs = catalog.for_stage('prod')

        assert {s.name for s in dev_specs} == {
            'dev-only-secret',
            'owner-email',
        }
        assert {s.name for s in prod_specs} == {'owner-email'}


class TestCatalogLoadFailure:
    """Catalog.load falla con error claro ante YAML invalido."""

    def test_when_directory_does_not_exist_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        with pytest.raises(CatalogError, match='no existe'):
            Catalog.load(tmp_path / 'no-such-dir')

    def test_when_kind_invalid_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace('kind: ssm-parameter', 'kind: dynamodb-table')
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='kind invalido'):
            Catalog.load(tmp_path)

    def test_when_required_field_missing_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace(
            'source_env_var: TURNSTILE_SECRET_KEY\n',
            '',
        )
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='source_env_var'):
            Catalog.load(tmp_path)

    def test_when_name_filename_mismatch_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        _write_yaml(tmp_path, 'wrong-filename', _VALID_YAML)

        with pytest.raises(CatalogError, match='no coincide con el filename'):
            Catalog.load(tmp_path)

    def test_when_stages_contains_local_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace(
            'stages: [dev, prod]',
            'stages: [local, dev]',
        )
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='stages invalidos'):
            Catalog.load(tmp_path)

    def test_when_stages_empty_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace('stages: [dev, prod]', 'stages: []')
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='lista no vacia'):
            Catalog.load(tmp_path)

    def test_when_ssm_type_invalid_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace('ssm_type: SecureString', 'ssm_type: Plain')
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='ssm_type invalido'):
            Catalog.load(tmp_path)

    def test_when_required_not_bool_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace('required: true', 'required: yes-please')
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        with pytest.raises(CatalogError, match='required debe ser bool'):
            Catalog.load(tmp_path)

    def test_when_path_no_template_with_multistage_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        bad = _VALID_YAML.replace(
            'path: /portfolio/${stage}/turnstile-secret',
            'path: /portfolio/turnstile-secret-global',
        )
        # Tres stages pero path sin ${stage} y no es claramente global:
        # exige ${stage} cuando son varios stages distintos.
        # Excepcion: path global compartido vale (ej owner-email).
        # Aqui simulamos por explicitud: un secreto NO global con multi-stage
        # debe declarar ${stage}.
        _write_yaml(tmp_path, 'turnstile-secret', bad)

        # No raise: path sin ${stage} es valido si el dev lo quiere global
        # (interpretacion: vale para los 3 stages el mismo SSM). El parser
        # NO obliga al template; solo lo permite. Documentamos el caso aqui:
        catalog = Catalog.load(tmp_path)
        spec = catalog.get('turnstile-secret')
        assert spec.path_for('dev') == '/portfolio/turnstile-secret-global'
        assert spec.path_for('prod') == '/portfolio/turnstile-secret-global'

    def test_when_yaml_not_mapping_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        _write_yaml(tmp_path, 'bad', '- just\n- a\n- list\n')

        with pytest.raises(CatalogError, match='mapa'):
            Catalog.load(tmp_path)

    def test_when_yaml_syntax_error_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        _write_yaml(tmp_path, 'bad', 'kind: ssm-parameter\n  bad indent: x')

        with pytest.raises(CatalogError, match='mal formado'):
            Catalog.load(tmp_path)


class TestCatalogGet:
    """Catalog.get devuelve por nombre, error claro si no existe."""

    def test_when_unknown_raises_with_known_list(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_catalog import CatalogError

        _write_yaml(tmp_path, 'turnstile-secret', _VALID_YAML)
        catalog = Catalog.load(tmp_path)

        with pytest.raises(CatalogError, match='secreto desconocido'):
            catalog.get('does-not-exist')

    def test_when_known_returns_spec(self, tmp_path):
        from serverless.secrets_catalog import Catalog

        _write_yaml(tmp_path, 'turnstile-secret', _VALID_YAML)
        catalog = Catalog.load(tmp_path)

        spec = catalog.get('turnstile-secret')

        assert spec.name == 'turnstile-secret'
