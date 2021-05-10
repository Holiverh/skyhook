
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


*********
Functions
*********

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


*****
Types
*****

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
