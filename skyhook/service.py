"""Load and validate service definitions."""

import importlib.metadata
import importlib.resources
import inspect

import jsonschema
import yaml


class Service:
    """Definition of a service."""

    def __init__(self, *, source, name, version, description):
        self.source = source  # TODO: replace with to() or something
        self.name = name
        self.version = version
        self.description = description
        self._functions = {}
        self._messages = {}
        self._types = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.name}' @ {self.version}>"

    @classmethod
    def from_(cls, specification):
        service = cls(
            source=specification,
            name=specification["service"]["name"],
            version=specification["service"]["version"],
            description=specification["service"]["description"],
        )
        if "types" in specification:
            for type_specification in specification["types"]:
                service.declare_type(Type(
                    name=type_specification["name"],
                    description=type_specification["description"],
                    schema=type_specification["schema"],
                ))
        if "functions" in specification:
            for function_specification in specification["functions"]:
                function = Function(
                    name=function_specification["name"],
                    description=function_specification["description"],
                )
                service.declare_function(function)
                for argument_specification \
                        in function_specification["arguments"]:
                    function.declare_argument(Argument(
                        name=argument_specification["name"],
                        description=argument_specification["description"],
                        schema=argument_specification["schema"],
                    ))
                if "returns" in function_specification:
                    function.return_ = Return(
                        description=function_specification["returns"]["description"],
                        schema=function_specification["returns"]["schema"],
                    )
        if "messages" in specification:
            for message_specification in specification["messages"]:
                service.declare_message(Message(
                    name=message_specification["name"],
                    description=message_specification["description"],
                    schema=message_specification["schema"],
                ))
        return service

    @classmethod
    def from_yaml(cls, stream):
        specification = yaml.safe_load(stream)
        service = cls.from_(specification)
        return service

    @property
    def types(self):
        yield from self._types.values()

    @property
    def functions(self):
        yield from self._functions.values()

    @property
    def messages(self):
        yield from self._messages.values()

    def validator(self, schema):
        return jsonschema.Draft7Validator(
            schema,
            resolver=_ServiceResolver(self),
            types={"array": (list, tuple)},
        )

    def declare_type(self, type_):
        if type_.name in self._types:
            raise ValueError(f"type '{type_.name}' already declared")
        self._types[type_.name] = type_

    def declare_function(self, function):
        if function.name in self._functions:
            raise ValueError(f"function '{function.name}' already declared ")
        self._functions[function.name] = function

    def declare_message(self, message):
        if message.name in self._messages:
            raise ValueError(f"message '{message.name}' already declared")
        self._messages[message.name] = message

    def type(self, name):
        if name not in self._types:
            raise ValueError(f"no type '{name}' declared'")
        return self._types[name]

    def function(self, name):
        if name not in self._functions:
            raise ValueError(f"no function '{name}' declared")
        return self._functions[name]

    def message(self, name):
        if name not in self._messages:
            raise ValueError(f"no message '{name}' declared")
        return self._messages[name]


class Type:

    def __init__(self, *, name, description, schema):
        self.name = name
        self.description = description
        self.schema = schema


class Function:

    def __init__(self, *, name, description):
        self.name = name
        self.description = description
        self._arguments = {}
        self.return_ = None

    @property
    def arguments(self):
        yield from self._arguments.values()

    def declare_argument(self, argument):
        if argument.name in self._arguments:
            raise ValueError(
                f"duplicate argument '{argument.name}' for '{self.name}'")
        self._arguments[argument.name] = argument

    @property
    def signature(self):
        parameters = []
        for argument in self._arguments.values():
            parameter = inspect.Parameter(
                argument.name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
            parameters.append(parameter)
        return inspect.Signature(parameters)


class Argument:

    def __init__(self, *, name, description, schema):
        self.name = name
        self.description = description
        self.schema = schema


class Return:

    def __init__(self, *, description, schema):
        self.description = description
        self.schema = schema


class Message:

    def __init__(self, *, name, description, schema):
        self.name = name
        self.description = description
        self.schema = schema


def discover():
    """Discover installed service definitions."""
    entries = importlib.metadata.entry_points().get("skyhook", [])
    for entry in entries:
        if entry.name == "specification":
            with importlib.resources.open_text(
                    entry.value, "service.yaml") as source:
                yield skyhook.Service.from_yaml(source)


class _ServiceResolver(jsonschema.RefResolver):
    """JSON Schema reference resolver for a service."""

    def __init__(self, service):
        super().__init__("", "...")
        self.service = service

    def resolve(self, reference):
        try:
            if reference.startswith("#/types/"):
                type_name = reference[len("#/types/"):]
                type_ = self.service.type(type_name)
                return "", type_.schema
        except ValueError:
            raise jsonschema.RefResolutionError(f"unknown {reference}")
        return super().resolve(reference)
