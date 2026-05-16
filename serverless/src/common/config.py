"""
Settings: configuracion del backend desde env vars.

Inyectado por SAM template (Globals.Function.Environment.Variables). En tests
unitarios se override con monkeypatch.setenv() o conftest fixtures.

Uso:
    from common.config import settings
    table_name = settings.contacts_table_name
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings cargado desde env vars. Cache LRU con maxsize=1 para reusar
    entre invocaciones warm (BaseSettings instancia parsea env solo 1 vez).
    """

    model_config = SettingsConfigDict(
        env_file=None,  # NO leer .env en runtime (env vars vienen del template)
        case_sensitive=False,
        extra='ignore',
    )

    # ---- Stage / runtime markers ------------------------------------------
    stage: str = Field(
        default='dev', description='Ambiente: dev | stage | prod'
    )
    aws_region: str = Field(default='us-east-1', alias='AWS_REGION')
    log_level: str = Field(default='INFO')

    # ---- DynamoDB tables --------------------------------------------------
    contacts_table_name: str = Field(default='portfolio-contacts-dev')
    tracking_table_name: str = Field(default='portfolio-tracking-dev')
    cache_table_name: str = Field(default='portfolio-cache-dev')

    # ---- SSM Parameter Store paths ----------------------------------------
    ssm_turnstile_secret_path: str = Field(
        default='/portfolio/turnstile-secret'
    )
    ssm_neon_url_path: str = Field(default='/portfolio/neon-url')
    ssm_owner_email_path: str = Field(default='/portfolio/owner-email')
    ssm_ses_from_path: str = Field(default='/portfolio/ses-from-address')

    # ---- KMS --------------------------------------------------------------
    kms_key_alias: str = Field(default='alias/portfolio-lambdas')

    # ---- Turnstile -------------------------------------------------------
    turnstile_bypass_secret: str = Field(
        default='', description='Secret para skip Turnstile en tests'
    )

    # ---- SSM cache TTL ---------------------------------------------------
    # Cuanto cachear los valores de SSM en memoria Powertools (Lambda warm)
    ssm_cache_seconds: int = Field(default=300)

    @property
    def is_prod(self) -> bool:
        return self.stage == 'prod'

    @property
    def is_stage(self) -> bool:
        return self.stage == 'stage'

    @property
    def is_dev(self) -> bool:
        return self.stage == 'dev'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton de Settings. Lee env vars solo la primera vez por warm Lambda.

    En tests usar `get_settings.cache_clear()` antes de tests que cambian env.
    """
    return Settings()


# Alias ergonomico: `from common.config import settings`
settings = get_settings()
