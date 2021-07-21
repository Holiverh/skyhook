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

    def wraps(self, callable_, batched=False):
        """Wrap message handler into Lambda entry-point.

        Takes a callable which accepts a service message and turns
        it into a function that's suitable for use as the entry-point
        of a Lambda function that receives messages.

        Either SNS or SQS integrations can be used with the returned
        function. Both kinds of event are transparently handled by the
        wrapper, with only a single, plain message passed to the wrapped
        callable.

        If message batching is enabled for SQS integrations, then by
        default the wrapped callable will be invoked multiple times,
        passing each message in turn in batch order. Messages are
        deleted from the in-bound queue as they are successfully
        processed. Should an invocation fail by raising an exception,
        then the message is not deleted from the queue and the Lambda
        will exit with an error.

        .. note::

            Should a message in a batch be processed unsuccessfully,
            the message is subject to SQS's built-in retry behaviour
            which includes re-attempted processing or migration to
            a configured dead-letter queue.

        However, if ``batched`` is set to ``True`` then the wrapped
        callable will be invoked once, instead being passed a sequence
        containing all messages from the batch. Under this scenario
        the batch processing succeeds or fails as a whole.

        .. tip::

            Batched processing can enable performance gains for services
            where there would otherwise be significant per-message
            overhead. For example, in some cases, a service may be able
            to operate on multiple messages in parallel. In such cases,
            batched processing should be strongly considered alongside
            suitable performance analysis.

        If the batch size is set to one or SNS is being used (where
        batching is not supported) and ``batched`` is enabled, then
        the list of messages will always contain a single item.

        :param callable_: Message handler to be wrapped.
        :param batched: Whether to handle messages one-by-one or in
            batches. Only meaningfully applicable to SQS transports
            which batch sizes greater than one.
        """

        @functools.wraps(callable_)
        def lambda_guard(event, context):
            messages = (
                self._messages_from_sns(event)
                + self._messages_from_sqs(event)
            )
            if batched:
                callable_(messages)
            else:
                for message in messages:
                    callable_(message)

        return lambda_guard

    def batched(self, callable_):
        """See :meth:`wrap`."""
        return self.wraps(callable_, batched=True)

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
