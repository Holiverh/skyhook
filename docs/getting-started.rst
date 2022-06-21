***************
Getting Started
***************

To start using Skyhook, first install library and tools with either:

.. code-block:: shell

    $ pip install skyhook-python
    $ pip install skyhook-python[pretty]

Install the ``[pretty]`` extra to enable :ref:`auto-formatting of
generated code <code-pretty>`.

Create a new YAML file, :file:`unicorn-shop.yaml` to contain the
definition for the new service:

.. code-block:: yaml

    service:
      name: unicorns
      description: Unicorn vendor and menagerie.
      version: 1.0
    functions:
      - name: buy
        description: Buy one or more unicorns of a given colour.
        arguments:
          - name: quantity
            description: Number of unicorns to buy.
            schema:
              type: integer
              minimum: 1
          - name: colour
            description: Colour of the unicorns to buy.
            schema: {$ref: "#/types/colour"}
        return:
          description: Whether the purchase succeeded or not.
          schema: {type: boolean}
    types:
      - name: colour
        description: Enumerate of all possible unicorn colours.
        schema:
          enum: [red, yellow, pink, blue]

Generate a service SDK from the service definition:

.. code-block::

    $ skyhook-generate --file unicorn-shop.yaml

Create a new Python module, :file:`shop.py` and :ref:`implement the
functions from the service definition <implement-lambda>` using the
helper decorator. Package the module and SDK for use as a Lambda
function, setting ``shop.buy_unicorn`` as the entry-point. Make a note
of the Lambda function's ARN, it will be required later.

.. code-block:: python

    # shop.py
    import unicorns

    stock = {
        "red": 10,
        "yellow": 2,
        "pink": 0,
        "blue": 5,
    }

    @unicorns.buy.lambda_
    def buy_unicorn(quantity: int, colour: unicorns.Colour) -> bool:
        if colour in stock:
            if quantity <= stock[colour]:
                stock[colour] -= quantity
                return True
        return False

Create another Python module, :file:`customer.py`, that will call into
the service to buy unicorns. Use the previously created Lambda
function's ARN to configure the :class:`skyhook.Hook`.

.. code-block:: python

    # customer.py
    import skyhook
    import unicorns

    hook = skyhook.Hook(unicorns)
    hook.define("buy", arn="...")  # from above
    with hook.bind():
        unicorns.buy(1, "red")
        unicorns.buy(2, "blue")

Run the module with AWS credentials that grant access to the previously
created Lambda function to start procuring unicorns.

.. code-block:: shell

    $ AWS_PROFILE=<profile> python -m customer

And that's it! A new service for buying unicorns built on top of AWS
Lambda has been designed, implemented and used with just a few lines
of Python. All structural validation, type safety and interactions with
the underlying AWS services are handled transparently by Skyhook.

Some ideas for next steps ...

- Extend the ``buy_unicorn`` Lambda to store stock levels persistently.
  Aim to do this without changing any of the arguments or return value
  of the function so as to not break the agreed service interface.
- :ref:`Introduce a new function <functions>` to allow customers to
  sell unicorns back to the shop as well as buy them.
- Generate an inventory report when a :ref:`notification of a sale
  <messages>` is :ref:`received <messages-recv>`.
