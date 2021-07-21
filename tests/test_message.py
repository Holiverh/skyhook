"""Tests for message sending and handler helpers."""

import json

import pytest

import skyhook.service
import skyhook.message


@pytest.fixture
def service():
    service = skyhook.service.Service(
        source={}, name="test", version="0.0.0", description="...")
    service.declare_message(skyhook.service.Message(
        name="foo",
        description="...",
        schema={"type": "string"},
    ))
    return service


class TestLambdaSNS:

    @pytest.fixture
    def event(self):
        return {
            "Records": [{
                "EventSource": "aws:sns",
                "EventSubscriptionArn": (
                    "arn:aws:sns:eu-west-2:000000000000"
                    ":skyhook:959d3ce0-b9a7-4217-a806-a9d3dc8e5542"
                ),
                "EventVersion": "1.0",
                "Sns": {
                    "Message": json.dumps("bar"),
                    "MessageAttributes": {},
                    "MessageId": "0497c77a-63a8-5dd4-9c36-9e62ad2321d7",
                    "Signature": (
                        "ScS1Rz7kl4b+jMlnC5j1c3I505rlzqUMn90puCLxj0"
                        "Yk6JU+8I4gh3dcvPJxyPAQ5/c5Pmvrzt1JWnO/P+bG"
                        "NAEV635CFEkgshixvsygLfEpCwcr7C8KpJ4Pw4eYJ/"
                        "USa7TyPvLbFk+sXzr9og5VpiGo2z5WZd6cSKjLPlcL"
                        "pVCjgH/GSX7T+XuldLyw21wJDPeJdRMS6hKucaH+WD"
                        "/ciurz0DCDJMwfsPfZ9NzjeIXPWYAVVPZ0f6MF6pag"
                        "lssIbHGGFLlo4dU1lONOhiRTRf7mGVy8WZzwboYXqY"
                        "j3s8QtkunD+zu000hVQsGXHNlfk9zIm4Ohp7WmGXhA"
                        "ZKQpAA=="
                    ),
                    "SignatureVersion": "1",
                    "SigningCertUrl": (
                        "https://sns.eu-west-2.amazonaws.com/"
                        "SimpleNotificationService-"
                        "010a507c1833636cd94bdb98bd93083a.pem"
                    ),
                    "Subject": None,
                    "Timestamp": "2021-05-14T19:15:23.684Z",
                    "TopicArn": "arn:aws:sns:eu-west-2:000000000000:skyhook",
                    "Type": "Notification",
                    "UnsubscribeUrl": (
                        "https://sns.eu-west-2.amazonaws.com/"
                        "?Action=Unsubscribe&SubscriptionArn="
                        "arn:aws:sns:eu-west-2:000000000000:skyhook"
                        ":959d3ce0-b9a7-4217-a806-a9d3dc8e5542"
                    ),
                },
            }],
        }

    def test_single(self, service, event):

        def impl(foo):
            nonlocal called
            called = True
            assert foo == "bar"

        called = False
        messenger = skyhook.message.Messenger(service, "foo")
        lambda_ = skyhook.message.MessengerLambda(messenger)
        lambda_entry = lambda_.wrap(impl)
        lambda_entry(event, ...)
        assert called

    def test_single_batched(self, service, event):

        def impl(foos):
            nonlocal called
            called = True
            assert foos == ["bar"]

        called = False
        messenger = skyhook.message.Messenger(service, "foo")
        lambda_ = skyhook.message.MessengerLambda(messenger)
        lambda_entry = lambda_.wrap(impl, batched=True)
        lambda_entry(event, ...)
        assert called

    def test_invalid_event(self, service):

        def impl(foo):
            assert False, "should not have been called"

        messenger = skyhook.message.Messenger(service, "foo")
        lambda_ = skyhook.message.MessengerLambda(messenger)
        lambda_entry = lambda_.wrap(impl)
        with pytest.raises(skyhook.error.ContractError):
            lambda_entry({"spam": "eggs"}, ...)

    def test_invalid_message(self, service, event):

        def impl(foo):
            assert False, "should not have been called"

        event["Records"][0]["Sns"]["Message"] = json.dumps(["not a string"])
        messenger = skyhook.message.Messenger(service, "foo")
        lambda_ = skyhook.message.MessengerLambda(messenger)
        lambda_entry = lambda_.wrap(impl)
        with pytest.raises(skyhook.error.ContractError):
            lambda_entry(event, ...)

    def test_error(self, service, event):

        def impl(foo):
            assert foo == "bar"
            raise RuntimeError

        messenger = skyhook.message.Messenger(service, "foo")
        lambda_ = skyhook.message.MessengerLambda(messenger)
        lambda_entry = lambda_.wrap(impl)
        with pytest.raises(RuntimeError):
            lambda_entry(event, ...)
