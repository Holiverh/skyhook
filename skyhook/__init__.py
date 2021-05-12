"""Package for building simple, schema-driven AWS-based service."""

from .error import ContractError
from .function import Lambda
from .hook import Hook
from .service import Service
