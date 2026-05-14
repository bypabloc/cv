"""
Rate-limit module: alternativa $0 a AWS WAF Web ACL ($7/mes).

Patron documentado en `.claude/docs/serverless-rate-limit/` (10 docs).

Uso ergonomico:

    from common.rate_limit import check_or_raise
    from common.ip_extractor import extract_ip, extract_country

    @logger.inject_lambda_context
    def lambda_handler(event, context):
        ip = extract_ip(event)
        country = extract_country(event)
        check_or_raise(
            ip=ip,
            endpoint='/contact',
            country=country,
            turnstile_validated=False,
        )
        # ... resto del handler

Comportamiento:
- IP whitelist? skip rate-limit (return Decision allowed)
- IP blacklist? raise IPBlacklistedError
- Country rule action=block? raise CountryBlockedError
- Sliding window weighted >= limit? raise RateLimitExceededError
- Atomic INCREMENT en bucket + auto-blacklist check
"""

from common.rate_limit.check import check_or_raise
from common.rate_limit.decisions import Decision
from common.rate_limit.exceptions import (
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
)

__all__ = [
    'CountryBlockedError',
    'Decision',
    'IPBlacklistedError',
    'RateLimitExceededError',
    'check_or_raise',
]
