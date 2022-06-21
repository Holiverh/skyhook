
.. _write:

#####################
Writing Specification
#####################

Whether using Skyhook to implement a service or to use an existing one,
a specification for it must exist. The service specification is the
canonical description of the interface and behaviour of the service. It
describes what functions the service exposes, including what arguments
each function accepts and what value it will return, if any.

Service specifications are YAML documents which combine metadata
and JSON Schema to describe the interface. This is similar to how
Swagger or Open API Specification work in the world of HTTP-based
services.


****************
Service Metadata
****************

At the top of each service specification there is a ``service`` block.
This block provides the high level description of the service, including
its name and version.

.. code-block:: yaml

    service:
      name: calculator
      version: 0.1.0
      description: An example service for basic arithmetic.

As with all nameable entities, the service itself must following the
:ref:`standard naming rules <names>`. A valid Semantic Versioning
compliant version string must be given. Descriptions are mandatory
and should describe the service in high-level terms.

This section is ultimately informational. Nothing in this section
will change the behaviour of service however these fields are used
by Skyhook's tooling so they should not be neglected.

.. tip::

    YAML supports multiline strings. Use them to add extra, paragraphed
    elaboration to the service description where appropriate.


.. _markup:
.. _names:

***********************
Naming and Descriptions
***********************

All entities defined by a service specification can be named. All
names must be written in so-called ``kebab-case``. That is, all lower
case alphabetic characters with multiple terms each separated by a
single dash. Any names that fail to adhere to this format will cause
the entire specification to be rejected.

When code is generated from a specification, names will be converted
to legal identifiers in the target language. An attempt is also made to
match the established naming conventions of the language. In practice,
for Python this means that function names become ``snake_cased`` but
types become ``PascalCased``.

.. warning::

    Note that the code generator will also need to avoid use of
    language keywords or other sensitive identifiers. Again this
    will be done inline with established convention, e.g. by appending
    an underscore.

In order to promote maintainability through self-documentation, all
nameable entities also require a mandatory description. For simple
functions or types, a short description may be suitable. For functions
with complex behaviour, it is wise to provide intimate elaboration
on the exact behaviour of that function. Do bare in mind, Skyhook can
protect implementers and users of a service from syntactic errors but
there is little it can do to protect against *semantic errors*.

Descriptions are included in generated code. Use of markup in
descriptions should be kept light if present at all as there's no
guarantee that downstream tools will be able to process it correctly.
If markup must be used, stick to basic Markdown to ensure maximum
legibility.


.. _functions:

*********
Functions
*********

Functions define the capabilities of a service. The client of a service
can call any specified function to instruct the service to perform a
an operation. Arguments can be passed along with the function call to
influence its behaviour. Often, on carrying out the requested operation
the service will return a value (:ref:`or error <errors>`) back to the
caller.

.. code-block:: yaml

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

Functions are listed under the correspondingly named ``functions``
block. Each function must be :ref:`named and given a description
<names>`. It is important to capture the exact intended behaviour of
the function in its decription. It will guide the implementer towards
the right implementation and help the user understand the capabilities
of the service.

Any number of arguments can be listed for the function. They too must
be named and described. Most importantly, an argument specifies a
schema which defines what an acceptable value for that argument looks
like. This schema will be enforced by Skyhook  on both the caller and
callee sides.

Although the :ref:`full power of JSON schema <json-schema>` is available
for use with an argument's schema, not all conceivable validation
conditions can be expressed. This is most notably true for *service
level validation* -- that is to say, when something is validated with
respect to the service's own domain; such as an authorisation check.
Reserve argument schema for *structual validation*. Although do include
any other rules that may apply in the function description.

Functions may optionally return a value. If included, the nature of
the return value must be described and a schema specified which applies
to the return value. Return value schemas are similarly enforced like
that of arguments.


.. _errors:

Error Handling
==============

Skyhook reserves exceptions for signalling low-level errors when
interacting with a service. Often this is communication level issues
between the user and implementation such as might be caused by a
lack of sufficient IAM permissions. Exceptions are similarly used to
indicate service contract violations by either party.

Despite this, it's often the case that the service itself has some
notion of an *error*. For example, this could be made by a service
user making a nonsense request such as attempting to deleted a resource
managed by the service that doesn't exist. Or, sometimes in attempting
to complete a valid operation an error is encountered with a connected
system. Such as a database being unavailable due to outage or
maintenance.

To return *service level errors* to the caller, the service function
must explicitly model this as part of its defined return value.
One option to achieve this through the use of ``oneOf``:

.. code-block:: yaml

    returns:
      description: Sum of the two numbers or an error if it cannot be computed.
      schema:
        oneOf:
          - type: object
            properties:
              value: {type: integer}
          - type: object
            properties:
              error: {const: true}

An advantageous effect of doing this is that it can be used to force
the caller to account for the possibility of an error to occur.
Hopefully making the calling application more robust in its error
handling in the process.

.. code-block:: python

    addition = calculator.add(5, 5)
    if "error" not in addition:
        assert addition["value"] == 10

In the example above, a type checker would complain about any attempt
to access ``value`` without first asserting that no error had occured.

Communicating different *kinds of error* is left up to the the author
of the service specification. One option is to introduce an enumeration
of possible error codes -- either numeric or short identifier strings.

.. code-block:: yaml

    returns:
      description: Sum of the two numbers or an error if it cannot be computed.
      schema:
        oneOf:
          - type: object
            properties:
              value: {type: integer}
          - type: object
            properties:
              error:
                enum:
                  - "NumberTooSmall"
                  - "NumberTooBig"
                  - "BusyDoingSomethingElse"
                  - "DidntFeelLikeIt"

When doing this, give consideration as to whether the caller can take
any meaningful action in response to the specific error that can be
returned. Otherwise risk creating a situation where error reporting
descends into valueless noise.


.. _messages:

********
Messages
********

In addition to :ref:`functions <functions>`, services may also define
message buses. Where functions are useful for defining imperative or
procedural interfaces, messages allow for event-driven or message-actor
service designs.

.. code:: yaml

  messages:
    - name: alerts
      description: Notification about state of the system.
      schema:
        type: object
        properties:
          message: {type: string}
          level:
            enum:
              - debug
              - info
              - error

.. tip::

  Strongly consider using a ``$ref`` to a :ref:`separately defined type
  <types>` for use as the message ``schema``. As this will almost always
  produce prettier type annotations due to the fact that types can be
  explicitly named.

Messages are listed under a top-level ``messages`` block within the
service definition. Each message must be :ref:`named and described
<names>`. It's important to explain the purpose of these messages
within the service, highlighting any actions that will take place upon
their receipt.

Simpler than functions, messages just have a single ``schema`` which
describes the structure of the messages themselves. Typically the
schema will be a ``type: object`` but scalar types are also acceptable.

Service designers are free to use both functions and messages in a
single service definition as they see fit. Generally messages should
be reserved for fire-and-forget use cases, where the *caller* /
*publisher* does not necessarily need to confirm that the message was
actually received and processed. However, consideration should be given
to the message durability characteristics of the underlying AWS services
that are used to implement the Skyhook service. Namely SNS or SQS.

Messages may also be the preferable choice where there is a desire to
more strongly de-couple the sender and receiver. For example, in cases
where messages need to be broadcast to multiple receivers which the
sender cannot know about ahead of time.


.. _types:

*****
Types
*****

Rather than merely pushing around primitive data, services often
prefer to reason about their interfaces in terms of their own higher
level data or domain model. Where there may be common types of objects
which are used with various functions and messages but themselves are
made up of multiple fields.

It's not a great leap in logic to imagine extending the earlier example
calculator service to higher dimensions. Allowing it to perform basic
operations on vectors ...

.. code-block:: yaml

    types:
      - name: vector3
        description: A three-dimensional vector.
        schema:
          type: object
          required: [x, y, z]
          properties:
            x: {type: number}
            y: {type: number}
            z: {type: number}

By declaring a ``vector3`` type, functions (and messages) can refer
to this type by name ...

.. code-block:: yaml

    functions:
      - name: add
        description: Add two vectors together.
        arguments:
          - name: a
            description: Left addition operand.
            schema: {$ref: "./types/vector3"}
          - name: b
            description: Right addition operand.
            schema: {$ref: "#/types/vector3"}
        returns:
          description: Sum of the two vectors.
          schema: {$ref: "#/types/vector3"}

An obvious benefit to this is that, despite being used three times
in just a single function, the vector schema needn't be repeated.
However, going beyond simple de-duplication: the Skyhook code generator
will export aliases for the generated types. Making it possible to
write overall cleaner and more concise code for both the service
implementer and user. For example:

.. code-block:: python

  from calculator.functions import add
  from calculator.types import Vector3

  @add.lambda_
  def add_impl(a: Vector3, b: Vector3) -> Vector3: ...

All types are defined under the ``types`` block and as with functions
and messagers, they require :ref:`names and descriptions <names>`.
Beyond this, only a ``schema`` is required.

To reference a type, a regular JSON Schema reference can be used,
where the fragment is the ``name`` of the type preceeded by ``/types/``.
As these are regular JSON Schema references, the type definition itself
needn't necessarily exist in the same file as the function or message
definitions that make use of it.

References to types can occur anywhere inside of a ``schema``. Including
inside the ``schema`` for another type definition.

.. note::

  Note that new types needn't be introduced merely for the sake of
  avoiding repetitive schemas. :ref:`Schemas can be re-used directly
  <json-schema-reuse>` as an alternative. Types should be added for
  representing distinct parts of the service's data/domain model.


.. _json-schema:

***********
JSON Schema
***********

JSON Schema is used to describe the structure of data handled by
service in the specification. Any valid JSON Schema 7.0 can be used.
During code generation, attempts are made to convert these schema to
the target language's type system and notation. In Python, for the most
part this is fine. However there are some edges allowable by JSON Schema
which cannot be adequately mapped into Python.

Negated types such as JSON Schema's ``not`` cannot be represented.
Careless use of ``additionalItems`` or ``additionalProperties`` can
also result in weaker type definitions being produced. As an ultimate
fallback Skyhook will resort to ``typing.Any`` if the given schema
cannot be correctly interpreted.

Generally, service specifications should be simple. As this makes
implementing and using the service simpler too. If this approach is
follow any issues should be few and far between.

Do bare in mind, even if generated type definitions are weaker than
ideal (or perhaps type checking is disabled), the schema will still be
used for validating data passing through the service.


.. _json-schema-reuse:

Re-using Schema
===============

If similar passages of JSON Schema are repeated throughout the service
definition it may be wise to simply define the passage once and re-use
it multiple times.

Re-usable schema excerpts can be placed under a top-level ``schemas``
block and referenced else where using regular JSON Schema ``$ref``
references. Note that schemas have an ID but are *not* :ref:`named
elements <names>` within the service definition. They exist purely
for transclusive purposes and this is a key difference when compared
to :ref:`service defined types <types>`.

.. code-block:: yaml

  functions:
    - name: buy
      description: Buy a unicorn of a given colour.
      arguments:
        - name: colour
          description: Colour of the unicorn to buy.
          schema: {$ref: "#/schemas/UnicornColour"}

  messages:
    - name: sales
      description: Notification of unicorn sales.
      schema:
        type: object
        properties:
          quantity: {type: integer}
          colour: {$ref: "#/schemas/UnicornColour"}

  schemas:
    UnicornColour:
      enum: [red, yellow, pink, blue]

As with type references, schema can be referenced from other files;
as with any JSON Schema reference.
