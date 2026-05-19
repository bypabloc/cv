"""
Exceptions del rate-limit module. Reexporta las que viven en _shared.exceptions
para conveniencia.

Hereda de ApplicationError -> RateLimitExceededError (HTTP 429) o derivados:
- IPBlacklistedError (HTTP 403)
- CountryBlockedError (HTTP 403)
"""

from _shared.exceptions import (
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
)

__all__ = [
    'CountryBlockedError',
    'IPBlacklistedError',
    'RateLimitExceededError',
]
