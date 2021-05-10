"""Tools for implementing service functions."""

import functools

# TODO: typedefs

class Lambda:

    def __init__(self, service, name):
        self._service = service
        self._function = service.function(name)

    def __call__(self, callable_):
        return self.wrap(callable_)

    def wrap(self, callable_):
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

        @functools.wraps(callable_)
        def lambda_guard(event, context):
            event_validator.validate(event)
            arguments = self._function.signature.bind(**event)
            return_ = callable_(*arguments.args, **arguments.kwargs)  # TODO: kebab to Python
            if self._function.return_:
                return_validator = \
                    self._service.validator(self._function.return_.schema)
                return_validator.validate(return_)
                return return_

        return lambda_guard
