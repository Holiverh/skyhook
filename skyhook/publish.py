"""PEP 517 builder for packaging service definitions.

When used as as the build backend for a PEP 517 builder, this module
will produce a Python Wheel containing the given, verbatim service
specification and the necessary entry point hooks to make it
discoverable, e.g. by :func:`..service.discover` after being installed.

To publish a service specification, :file:`service.yaml`, it must
be first bundled into a Python distribution. To do this, create a
:file:`pyproject.toml` that uses this module as the build backend.

.. code-block:: toml

    [build-system]
    requires = ["skyhook"]
    build-backend = "skyhook.publish"

    [tool.skyhook]
    specification = service.yaml

With this configuration a PEP 517 frontend can be used to build the
service specification distributable. For example, using Pip in the
same directory as the two files:

.. code-block:: shell

    $ pip wheel .

The Wheel produced by this process is suitable for upload to a package
index using existing tools. After doing so, the specification will
become "Pip installable" -- so that it can be readily installed for
use with clients and implementers of the service.

https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives

Metadata such as the name and version for the built distribution is
taken from the service specification itself. These can be overriden
in the ``[tool.skyhook]`` section of the file:`pyproject.toml` file.

.. code-block:: toml

    [tool.skyhook]
    specification = service.yaml
    name = unicorn-shop
    version = 0.1.0a5
    description = "Service for buying and selling unicorns."

.. note::

    If publishing the service specification to the public Python package
    index it will need to have a unique name.
"""

import base64
import hashlib
import os.path
import textwrap
import uuid
import zipfile

import toml
import yaml


def build_wheel(wheel_directory,
                metadata_directory=None, config_settings=None):

    with open("pyproject.toml") as pyproject_file:
        pyproject = toml.load(pyproject_file)

    specification_string = ""
    specification_path = pyproject["tool"]["skyhook"]["specification"]
    with open(specification_path) as specification_file:
        specification_string = specification_file.read()
        specification = yaml.safe_load(specification_string)

    distribution = specification["service"]["name"].replace("-", "_")
    version = specification["service"]["version"]
    build = 1
    python = "py3"
    abi = "none"
    platform = "any"
    name = f"{distribution}-{version}-{build}-{python}-{abi}-{platform}.whl"
    dist_info = f"{distribution}-{version}.dist-info"
    data = f"{distribution}-{version}.data"
    package = f"_{distribution}_{uuid.uuid4()}".replace("-", "")
    specification_bundled = "service.yaml"

    # PEP 427
    wheel = textwrap.dedent("""\
    Wheel-Version: 1.0
    Generator: skyhook 0.1.0
    Root-Is-Purelib: true
    Tag: py3-none-any
    Build: 1
    """)

    # PEP 345, 566
    # https://packaging.python.org/specifications/core-metadata/
    metadata = textwrap.dedent(f"""\
    Metadata-Version: 2.1
    Name: {distribution}
    Version: {version}
    Provides-Dist: {distribution} ({version})
    """)

    entry_points = textwrap.dedent(f"""\
    [skyhook]
    specification = {package}
    """)

    top_level = textwrap.dedent(f"""\
    {package}
    """)

    record = "\n".join([
        record_file(f"{dist_info}/WHEEL", wheel),
        record_file(f"{dist_info}/METADATA", metadata),
        record_file(f"{dist_info}/entry_points.txt", entry_points),
        record_file(f"{dist_info}/top_level.txt", top_level),
        record_file(f"{package}/__init__.py", ""),
        record_file(f"{package}/" + specification_bundled, specification_string),
        f"{dist_info}/RECORD,,"
    ])

    with open(os.path.join(wheel_directory, name), "wb") as file:
        with zipfile.ZipFile(file, mode="w") as archive:
            print(archive)
            archive.writestr(f"{dist_info}/WHEEL", wheel)
            archive.writestr(f"{dist_info}/METADATA", metadata)
            archive.writestr(f"{dist_info}/entry_points.txt", entry_points)
            archive.writestr(f"{dist_info}/top_level.txt", top_level)
            archive.writestr(f"{dist_info}/RECORD", record)
            archive.writestr(f"{package}/__init__.py", "")  # namespace package := no data
            archive.write(
                specification_path,
                f"{package}/" + specification_bundled,
            )

    return name


def record_file(path, content):
    content_utf8 = content.encode()
    hash_ = hashlib.sha256(content_utf8)
    hash_b64 = base64.urlsafe_b64encode(hash_.digest()).decode().rstrip("=")
    return f"{path},sha256={hash_b64},{len(content_utf8)}"
