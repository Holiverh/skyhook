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

   getting-started
   specification
   distribution
   implementing
   using
   code-generation
   example-sdk-documentation

----

Legal Notices
-------------

Amazon Web Services, AWS, the Powered by AWS logo, Amazon Lambda, Amazon
Simple Notification Service (SNS) and Amazon Simple Queue Service (SQS)
are trademarks of Amazon.com, Inc. or its affiliates. This
project is not endorsed by or affiliated with the trademark holders.
Use of the trademarks by this project are solely for purpose of
identification.


License
^^^^^^^

Copyright 2021-2022 Oliver Ainsworth

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
