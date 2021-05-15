"""Tools for interacting with messages."""

import jsonschema

import skyhook.error
import skyhook.hook


class Messenger:

    def __init__(self, service, name):
        self._service = service
        self._message = service.message(name)

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
