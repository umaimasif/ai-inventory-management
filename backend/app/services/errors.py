"""Domain-level exceptions, mapped to HTTP errors in the API layer."""


class DomainError(Exception):
    """Base class for expected business-rule failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """A referenced entity does not exist."""


class ConflictError(DomainError):
    """The request conflicts with current state (e.g. duplicate SKU)."""


class ValidationError(DomainError):
    """The request is invalid for a business reason (e.g. insufficient stock)."""
