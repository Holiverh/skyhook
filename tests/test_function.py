"""Tests for function implementation helpers."""

import pytest

import skyhook.error
import skyhook.service
import skyhook.function


@pytest.fixture
def service():
    service = skyhook.service.Service(
        source={}, name="test", version="0.0.0", description="...")
    function = skyhook.service.Function(name="test", description="...")
    function.declare_argument(skyhook.service.Argument(
        name="foo",
        description="...",
        schema={"const": "bar"},
    ))
    function.declare_argument(skyhook.service.Argument(
        name="spam",
        description="...",
        schema={"type": "string"},
    ))
    function.return_ = skyhook.service.Return(
        description="...",
        schema={"type": "number"},
    )
    service.declare_function(function)
    return service


class TestLambdaValidate:

    def test_valid(self, service):
        try:
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate({"foo": "bar", "spam": "eggs"})
        except skyhook.error.ContractError:
            pytest.fail("should not have raised")

    def test_superfluous(self, service):
        with pytest.raises(skyhook.error.ContractError):
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate({"foo": "bar", "spam": "eggs", "up": "down"})

    def test_missing(self, service):
        with pytest.raises(skyhook.error.ContractError):
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate({"foo": "bar"})

    def test_invalid(self, service):
        with pytest.raises(skyhook.error.ContractError):
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate({"foo": "bar", "spam": 100})


class TestLambdaValidateReturn:

    def test_valid(self, service):
        try:
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate_return(500)
        except skyhook.error.ContractError:
            pytest.fail("should not have raised")

    def test_invalid(self, service):
        with pytest.raises(skyhook.error.ContractError):
            lambda_ = skyhook.function.Lambda(service, "test")
            lambda_.validate("not number")


class TestLambdaWrap:

    def test(self, service):

        def impl(foo, spam):
            assert foo == "bar"
            assert spam == "eggs"
            return 500

        lambda_ = skyhook.function.Lambda(service, "test")
        lambda_entry = lambda_.wrap(impl)
        lambda_return = lambda_entry({"foo": "bar", "spam": "eggs"}, ...)
        assert lambda_return == 500

    def test_invalid_event(self, service):

        def impl(foo, spam):
            assert False, "should not have been called"

        lambda_ = skyhook.function.Lambda(service, "test")
        lambda_entry = lambda_.wrap(impl)
        with pytest.raises(skyhook.error.ContractError):
            lambda_entry({"foo": "bar"}, ...)

    def test_invalid_return(self, service):

        def impl(foo, spam):
            nonlocal called
            called = True
            assert foo == "bar"
            assert spam == "eggs"
            return "not number"

        called = False
        lambda_ = skyhook.function.Lambda(service, "test")
        lambda_entry = lambda_.wrap(impl)
        with pytest.raises(skyhook.error.ContractError):
            lambda_entry({"foo": "bar", "spam": "eggs"}, ...)
        assert called
