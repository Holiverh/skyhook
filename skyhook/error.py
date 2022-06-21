"""Errors and warnings."""


# TODO: explicit JSON schema carry-through
# TODO: maybe explicit sub-classes?
class ContractError(Exception):
    """Raised when service the specification is violated."""


class TransportError(Exception):
    """Raised when service implementation is unreachable.

    Typically raised in response to errors encountered when interacting
    with underlying AWS services, such as during outages or when a
    :class:`.Hook` is misconfigured.
    """


class AccessError(TransportError):
    """Raised when access to underlying AWS services is denied."""
