
.. _implement:

#####################
Implementing Services
#####################

With a :ref:`service specification written <write>` it is now time to
write some *real code*. Code that will actually do the things the
specification advertises the service to be capable of. This is to say
that the service is to be *implemented*. Often there is a single
implementation of a given service and it is this implementation that
will be later used by clients of the service.


.. _implement-lambda:

******************************************
Example: Implementing Functions as Lambdas
******************************************

Skyhook is for building simple, safe cloud based services. Specifically,
services built on the "*simple*" AWS stack; namely: Lambda, Simple
Notification Service (SNS) and Simple Queue Service (SQS).

Service specifications describe what *functions* a service exposes.
Ultimately these are Lambda functions that accept a JSON input payload
and returns a JSON output; both of which should be compatible with
the structure describe by the specification. For example:

.. code-block:: yaml

    service:
      name: calculator
      version: 0.1.0
      description: An example service for basic arithmetic.

    functions:
      - name: add
        description: Add two numbers together.
        arguments:
          - name: a
            description: Left addition operand.
            schema:
              type: integer
          - name: b
            description: Right addition operand.
            schema:
              type: integer
        returns:
          description: Sum of the two numbers.
          schema:
            type: integer

The example above describes a simple calculator service which exposes
a single function which returns the sum of the two integers passed to it.

To implement this function, first the specification must be converted
to Python using :program:`skyhook-generate`. Assuming the service
definition is saved to a file :file:`calculator.yaml`:

.. code-block:: shell

    $ skyhook-generate --file calculator.yaml

On completion, a Python package, :mod:`calculator` will be created
in the current directory. It contains definitions of all the types
and functions exposed by the service as well as helpers for implementing
said functions.

As generated code, the :mod:`calculator` package should not be modified.
Instead a separate, sibling module should be created to house the
implementation itself such as :file:`service.py`. From this module,
the :mod:`calculator` package can be imported and the
:func:`calculator.add` function accessed.

.. code-block:: python

    # service.py
    import calculator
    print(calculator.add)

Attached to the function is a decorator, a :class:`skyhook.function.Lambda`,
which can be used to turn a suitable implementation of the *function
specification* into a Lambda entry point that is both type-safe and has
its inputs and outputs validated at runtime.

.. code-block:: python

    import calculator

    @calculator.add.lambda_
    def add_impl(a: int, b: int) -> int:
        return a + b

Due to the decorator usage, :func:`service.add_impl` is a valid Lambda
entry point which follows the more conventional signature of
``def add_impl(event, context)``. Note that this isn't purely syntactic
sugar. Through this decorator:

- Lambda input is validated against the function specification's
  schema before :func:`add_impl` is called.

- Return value is similarly validated against the specification
  before it is returned to the caller.

- Arguments are unpacked from the input into their individually named
  parts.

- If type checking is in use, :func:`add_impl` would cause a type
  check error if it did not match the function specification.


***************************
Function Implementation API
***************************

.. autoclass:: skyhook.function.Lambda
    :members:
    :special-members: __call__
    :undoc-members:


***************************************
Packaging and Deploying Implementations
***************************************
