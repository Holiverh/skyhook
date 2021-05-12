##############
Using Services
##############

With both a :ref:`service specification written <write>` and
:ref:`implemented <implement>` it is now time to start using the service
in client applications. To get started, a client application will need
a copy of the service specification that has been distributed. If it
has been :ref:`bundled into a Python package and uploaded <distribute>`
to a package index then it should be as simple installing it with Pip.

.. code-block:: shell

    $ pip install calculator==0.1.0

Or perhaps it's distributed by other means, such as copy-pasting it
into some documentation ...

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


*******
Example
*******

As when implementing the simple calculator service, to *use* it, it must
be first converted to Python using :program:`skyhook-generate`. Which
will generate an importable Python package in the current directory.

.. code-block:: shell

    $ skyhook-generate calculator  # if installed from a package
    $ skyhook-generate --file calculator.yaml

Note how this process is identical as used when implementing the
service. In fact, assuming the same version of Skyhook is used, the
exact same generated Python code is used for both *sides* of the
service. Although do bear in that there's no requirement for service
implementers and clients to use the same version of Skyhook!

Having generated the code for the service, it can be imported like any
other Python module.

.. code-block:: python

    # application.py
    import calculator

Intuitively, one might attempt to call one of the service functions.

.. code-block:: python

    import calculator

    calculator.add(5, 5)

Only to be unceremoniously met with a :exc:`NotImplementedError`.

.. code-block:: pytb

    Traceback (most recent call last):
      File "application.py", line 3, in <module>
        calculator.add(5, 5)
      File "...\skyhook\examples\calculator\calculator\functions.py", line 8, in add
        return __import__("skyhook").Hook.current().call("add", a, b)
      File "...\skyhook\skyhook\hook.py", line 119, in current
        raise NotImplementedError("no hook bound")
    NotImplementedError: no hook bound

Before calling into a service, the Skyhook generated library must be
first told where the implementation lives. Or in other words, it must
be fed the ARNs of the Lambda functions that provide the service. This
is done by constructing a :class:`skyhook.Hook` and configuring it with
ARNs before activating it.

.. code-block:: python

    import skyhook
    import calculator

    hook = skyhook.Hook(calculator)
    hook.define("add", arn="arn:aws:lambda:eu-west-2:123456789012:function:add")
    with hook.bind():
        assert calculator.add(5, 5) == 10

Now when using :func:`calculator.add`, Skyhook will dispatch the the
call to the Lambda function that was configured for it using the
active hook. The given arguments are serialised into the input payload
that will be submitted to the Lambda. The arguments are validated
before the Lambda is invoked, returning a :class:`skyhook.ContractError`
if they are not valid. The return value of the Lambda function is
similarly deserialised and validated before being returned to the
calling code.


**************************
Implementation Binding API
**************************

.. autoclass:: skyhook.Hook
    :members:
    :undoc-members:
