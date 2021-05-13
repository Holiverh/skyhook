"""Tools for implementing service functions."""

import functools

import jsonschema

import skyhook.error

# TODO: typedefs

class Lambda:
    """For building Lambda implementations of service functions.

    Generally this class should not be instantiated directly. Instead,
    when code is generated for a service, an instance of this class
    will be attached to each function in the generated code under the
    ``lambda_`` attribute. It is from here that they should be used
    by service implementers.

    Instances of this class are usable as decorators.

    :param service: Service the service function comes from.
    :param name: Canonical name of the service function.
    """

    def __init__(self, service, name):
        self._service = service
        self._function = service.function(name)

    def __call__(self, callable_):
        """See :meth:`wrap`."""
        return self.wrap(callable_)

    def wrap(self, callable_):
        """Wrap an implementation into a Lambda.

        Given a callable that implements the service function's
        specification this will turn it into into a callable that is
        suitable for use as a Lambda entry point.

        This entry point will validate incoming events against the
        the specification's schema, unpacking arguments into their
        most natural form before passing them onto the wrapped callable.
        The wrapped callable will not be called if the incoming event
        is not valid.

        If the function specification defines a return value, the
        return value of the wrapped callable will be similarly validated
        before being returned as the output of the Lambda.

        :param callable\_: Function or otherwise that implements the
            specified service function.
        """

        @functools.wraps(callable_)
        def lambda_guard(event, context):
            self.validate(event)
            arguments = self._function.signature.bind(**event)
            return_ = callable_(*arguments.args, **arguments.kwargs)  # TODO: kebab to Python
            if self._function.return_:
                self.validate_return(return_)
                return return_

        return lambda_guard

    def validate(self, event):
        """Validate a Lambda event.

        Given an *event* as passed to a Lambda entry point, this will
        ensure that the event matches the expectation of the function
        as defined by the service.

        Specifically, for each required argument defined in the
        specification there is expected to be a correspondingly named
        field in the event object whose value passes the JSON schema
        defined for that argument.

        :raises skyhook.ContractError: If the given event is not valid.
        """
        event_schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        for argument in self._function.arguments:
            event_schema["properties"][argument.name] = argument.schema
            event_schema["required"].append(argument.name)
        event_validator = self._service.validator(event_schema)
        try:
            event_validator.validate(event)
        except jsonschema.ValidationError as error:
            raise skyhook.error.ContractError from error

    def validate_return(self, return_):
        """Validate the return value of a Lambda.

        If the service function is specified to have a return value,
        this will ensure that the given value is valid according to
        the function's return value JSON schema.

        If no return value is specified, then all values are considered
        to be invalid.

        :raises skyhook.ContractError: If the given value is not valid.
        """
        return_validator = \
            self._service.validator(self._function.return_.schema)
        try:
            return_validator.validate(return_)
        except jsonschema.ValidationError as error:
            raise skyhook.error.ContractError from error
