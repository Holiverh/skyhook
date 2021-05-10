Skyhook: Simple Safe Cloud Services
===================================

**Skyhook** is a library and set of tools for defining, implementing
and using simple AWS based services in a way which is both intuitive
and *safe*. Promoting schema driven development, Skyhook provides a
language for describing simple services based off of AWS Lambda, SNS
and SQS which can be used to generate type-safe and runtime validated
code.

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
             type: number
         - name: b
           description: Right addition operand.
           schema:
             type: number
       returns:
         description: Sum of the two numbers.
         schema:
           type: number

Which can be used to generate Lambda function entry points:

.. code-block:: python

   import calculator

   @calculator.add.lambda_
   def add(a: int, b: int) -> int:
      return a + b

Or used on the client side to call into the service:

.. code-block:: python

   import skyhook
   import calculator

   hook = skyhook.Hook(calculator)
   hook.define("add", arn="...")
   with hook.bind():
      assert calculator.add(5, 5) == 10

----

.. toctree::
   :maxdepth: 2

   specification
   distribution
   implementing
   using
