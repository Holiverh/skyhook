"""Tools for interacting with messages."""

import functools
import json

import jsonschema

import skyhook.error
import skyhook.hook


class Messenger:

    def __init__(self, service, name):
        self._service = service
        self._message = service.message(name)
        self.lambda_ = MessengerLambda(self)

    def validate(self, message):
        validator = self._service.validator(self._message.schema)
        try:
            validator.validate(message)
        except jsonschema.ValidationError as error:
            raise skyhook.error.ContractError from error

    def send(self, message):
        self.validate(message)  # misplaced?
        hook = skyhook.Hook.current()
        hook.send(self._message.name, message)


class MessengerLambda:
    """For building Lambda implementations of message receivers."""

    def __init__(self, messenger):
        self._messenger = messenger

    def __call__(self, callable_):
        """See :meth:`wrap`."""
        return self.wraps(callable_)

    def wraps(self, callable_):

        @functools.wraps(callable_)
        def lambda_guard(event, context):
            messages = (
                self._messages_from_sns(event)
                + self._messages_from_sqs(event)
            )
            for message in messages:
                callable_(message)

        return lambda_guard

    def _messages_from_sns(self, event):
        messages = []
        if not isinstance(event, dict):
            return messages
        if "Records" in event:
            for record in event["Records"]:
                if record.get("EventSource") == "aws:sns":
                    try:
                        message = json.loads(record["Sns"]["Message"])
                    except json.JSONDecodeError as error:
                        raise skyhook.error.ContractError from error
                    else:
                        self._messenger.validate(message)
                        messages.append(message)
        return messages

    def _messages_from_sqs(self, event):
        messages = []
        if not isinstance(event, dict):
            return messages
        if "Records" in event:
            for record in event["Records"]:
                if record.get("eventSource") == "aws:sqs":
                    try:
                        message = json.loads(record["body"])
                    except json.JSONDecodeError as error:
                        raise skyhook.error.ContractError from error
                    else:
                        self._messenger.validate(message)
                        messages.append(message)
        return messages
