from __future__ import annotations


class DomainError(Exception):
    """Base exception for pure domain failures."""


class EmptyPoolError(DomainError):
    """Raised when no valid champion mastery entries remain to build a pool."""


class UnknownChampionError(DomainError):
    """Raised when a champion identifier is missing from the loaded catalog."""


class InvalidContentError(DomainError):
    """Raised when static YAML content fails validation or referential integrity."""
