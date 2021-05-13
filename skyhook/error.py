"""Errors and warnings."""


# TODO: explicit JSON schema carry-through
# TODO: maybe explicit sub-classes?
class ContractError(Exception):
    """Raised when service specification is violated."""
