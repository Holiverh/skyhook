##########################
Distributing Specification
##########################

After :ref:`writing the specification for a service <write>` it is
probably a good idea to distribute it to service implementers and users.
It can be used as both as an informational reference and for use with
Skyhook's code generation.

Ultimately service specifications are just YAML files which can be
distributed as the author sees fit -- including emailing copies to
each and every party who might be interested.

To ease distribution, specifications can be bundled into Python packages
and published to a package index. By doing this the specification
becomes "*Pip installable*" which provides a rather elegant way to
express a Python application's dependency on the service -- by including
the specification package in its own ``install_requires``.

Skyhook provides a PEP 517 build backend which can used to build these
packages.


*****************************************
Bundling Specification in Python Packages
*****************************************

.. automodule:: skyhook.publish


************************************
Using Multiple Versions of a Service
************************************

When service specifications are bundled into Python packages using
:mod:`skyhook.publish` the version of the package is taken from the
specification itself. This makes quite a lot of sense, if an application
depends on verison ``2.3.4`` of the ``foo`` service then its Python
package dependency is, well, ``foo==2.3.4``.

A problem arises when multiple versions of the same service are needed.
For example, a single implementation of the service might need to
provide both ``2.x`` and ``1.x`` versions of the service to aid in
backwards compatability. Or similarly, the user of a service may be
happily using ``1.x`` but really needs that shiny new feature that was
only added to ``2.x`` and cannot justify porting the entire application
forward to the new version.

It is impossible to express this requirement to Python packaging
systems.

To account for this, it may be wise to publish alias packages for
each major version of the service. Continuing with the above example,
``foo 2.3.4`` would be packaged and published under the name ``foo2``
as well as ``foo`` itself.

In such a configuration it would be possible to depend on both a
``foo2`` and a ``foo1`` simultaneously. When code is generated from
these specifications they can follow a similar naming scheme too.

Note that alias packages would only be required for each major version
as minor version changes are promised to be backwards compatible in
keeping with the Semantic Versioning scheme which applies to the
specification. Unless the service in question is experiencing a great
deal of design churn and there are not suitable deprecation policies
in place, then the need for more than two major versions of a service
to co-exist should be relegated to only the most extreme cases.
