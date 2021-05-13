"""Tests for the top level package."""

import skyhook
import skyhook.error
import skyhook.function
import skyhook.hook
import skyhook.service


def test_aliases():
    assert skyhook.ContractError is skyhook.error.ContractError
    assert skyhook.Lambda is skyhook.function.Lambda
    assert skyhook.Hook is skyhook.hook.Hook
    assert skyhook.Service is skyhook.service.Service
