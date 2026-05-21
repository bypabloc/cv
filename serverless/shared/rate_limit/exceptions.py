"""
Exceptions del rate-limit module. Reexporta las que viven en shared.exceptions
para conveniencia.

Hereda de ApplicationError -> RateLimitExceededError (HTTP 429) o derivados:
- IPBlacklistedError (HTTP 403)
- CountryBlockedError (HTTP 403)
"""

from shared.exceptions import (
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
)

__all__ = [
    'CountryBlockedError',
    'IPBlacklistedError',
    'RateLimitExceededError',
]
