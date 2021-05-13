"""Code generator for service definitions."""

import ast
import argparse
import keyword
import pathlib
import textwrap

import astunparse
import black

import skyhook.service


class Package:

    def __init__(self, service):
        self._name = _id_snake(service.name)
        self._service = service
        self._init = None
        self._types = None
        self._functions = None
        self._specification_ast = ast.parse(textwrap.dedent(f"""\
        import skyhook.service

        service = skyhook.Service.from_({self._service.source!r})
        """))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new):
        self._name = _id_snake(new)

    def files(self):
        self._generate()
        directory = pathlib.Path(self.name)
        files = [
            ("__init__.py", self._init.ast),
            ("_spec.py", self._specification_ast),
            ("functions.py", self._functions.ast),
            ("types.py", self._types.ast),
        ]
        for path, tree in files:
            path = pathlib.Path(self.name) / path
            source = astunparse.unparse(tree)
            source = black.format_str(
                source, mode=black.Mode(
                    line_length=79,
                    experimental_string_processing=True))
            yield path, source

    def _generate(self):
        self._generate_types()
        self._generate_functions()
        self._generate_init()

    def _generate_types(self):

        def resolve(reference):
            if not reference.startswith("#/types/"):
                raise ValueError("'{reference}' is not a type reference")
            name = reference[len("#/types/"):]
            return _id_pascal(name)

        module = _Module()
        module.import_typing()
        for type_ in self._service.types:
            name = _id_pascal(type_.name)
            annotation, preamble = _annotate_schema(
                type_.schema, resolve, [type_.name])
            definition = ast.Assign(
                targets=[ast.Name(id=name)],
                value=annotation,
            )
            module.preamble.extend(preamble)
            module.body.append(definition)
        self._types = module

    def _generate_functions(self):

        def resolve(reference):
            if not reference.startswith("#/types/"):
                raise ValueError("'{reference}' is not a type reference")
            name = reference[len("#/types/"):]
            return "_types." + _id_pascal(name)

        module = _Module()
        module.import_typing()
        module.import_types()
        module.import_spec()
        for function in self._service.functions:
            self._generate_function(function, module, resolve)
        self._functions = module

    def _generate_function(self, function, module, resolve):
        name = _id_snake(function.name)
        definition = ast.FunctionDef(
            name=name,
            decorator_list=[],
            args=ast.arguments(
                args=[],
                defaults=[],
                vararg=None,
                kwarg=None,
            ),
            body=[ast.Expr(value=ast.Constant(
                value=_DocString(function.description),
                kind=None,
            ))],
        )
        module.body.append(definition)
        hook = (f"return __import__('skyhook')"
                f".Hook.current().call('{function.name}')")
        hook_ast = ast.parse(hook)
        definition.body.extend(hook_ast.body)
        for argument in function.arguments:
            hook_ast.body[0].value.args.append(ast.Name(id=argument.name))
            annotation, preamble = _annotate_schema(
                argument.schema,
                resolve,
                [function.name, argument.name],
            )
            definition.args.args.append(ast.arg(
                arg=argument.name,
                annotation=annotation,
            ))
            module.preamble.extend(preamble)
        if function.return_:
            definition.returns, preamble = \
                _annotate_schema(function.return_.schema, resolve)
            module.preamble.extend(preamble)
        module.body.append(self._generate_function_lambda_ast(name, function))

    def _generate_function_lambda_ast(self, name, function):
        hook = f"__import__('skyhook').Lambda(_spec.service, '{function.name}')"
        hook_ast = ast.parse(hook)
        assign = ast.Assign(
            targets=[ast.Attribute(value=ast.Name(id=name), attr="lambda_")],
            value=hook_ast.body[0].value,
        )
        return assign

    def _generate_init(self):
        modules = [
            ("functions", self._functions),
            ("types", self._types),
        ]
        init = _Module()
        for module_name, module in modules:
            for name in module.names:
                import_ = ast.ImportFrom(
                    module=module_name,
                    names=[ast.alias(
                        name=name,
                        asname=None,
                    )],
                    level=1,
                )
                init.body.append(import_)
        self._init = init


class _DocString(str):
    """Pretty docstrings for AST unparser."""

    def __repr__(self):
        tokens = []
        lines = self.splitlines()
        for index, line in enumerate(lines):
            if index > 0:
                line = "    " + line
            tokens.append(line)
        if len(tokens) == 0:
            multiline = '""""""'
        if len(tokens) == 1:
            multiline = f'"""{tokens[0]}"""'
        else:
            tokens[0] = f'"""{tokens[0]}'
            tokens.append('    """')
            multiline = "\n".join(tokens)
        return multiline


class _Module:

    def __init__(self):
        self.preamble = []
        self.body = []
        self.epilogue = []

    @property
    def ast(self):
        return ast.Module(body=self.preamble + self.body + self.epilogue)

    @property
    def names(self):
        for node in self.ast.body:
            if isinstance(node, ast.FunctionDef):
                yield node.name
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        yield target.id

    def import_typing(self):
        self.preamble.append(ast.Import(
            names=[ast.alias(
                name="typing",
                asname="_typing",
            )],
        ))
        self.epilogue.append(ast.Delete(targets=[
            ast.Name(id="_typing", ctx=ast.Del()),
        ]))

    def import_types(self):
        self.preamble.append(ast.ImportFrom(
            module="",
            names=[ast.alias("types", asname="_types")],
            level=1,
        ))
        self.epilogue.append(ast.Delete(targets=[
            ast.Name(id="_types", ctx=ast.Del()),
        ]))

    def import_spec(self):
        self.preamble.append(ast.ImportFrom(
            module="",
            names=[ast.alias("_spec", asname=None)],
            level=1,
        ))
        self.epilogue.append(ast.Delete(targets=[
            ast.Name(id="_spec", ctx=ast.Del()),
        ]))

def _id_snake(name):
    """Convert kebab-name to snake_name."""
    parts = name.lower().split("-")
    identifier = "_".join(parts)
    if keyword.iskeyword(identifier):
        identifier = f"{identifier}_"
    return identifier


def _id_pascal(name):
    """Convert kebab-name to KebabName."""
    parts = name.lower().split("-")
    identifier = "".join(part.capitalize() for part in parts)
    if keyword.iskeyword(identifier):
        identifier = f"{identifier}_"
    return identifier


def _is_literal_none(node):
    return isinstance(node, ast.Name) and node.id == "None"


def _typing(name):
    return ast.Attribute(value=ast.Name(id="_typing"), attr=name)


def _annotate_literal(value):
    if value is None:
        return ast.Name(id="None")
    literal = _typing("Literal")
    literal_slice = ast.Index(value=ast.Constant(value=value, kind=None))
    literal_subscript = ast.Subscript(value=literal, slice=literal_slice)
    return literal_subscript


def _annotate_tuple(schema, resolve, names=()):
    preamble = []
    tuple_ = _typing("Tuple")
    elements = ast.ExtSlice(dims=[])
    for subschema in schema["items"]:
        annotated, extra = _annotate_schema(subschema, resolve, names)
        preamble.extend(extra)
        elements.dims.append(annotated)
    subscript = ast.Subscript(value=tuple_, slice=elements)
    return subscript, preamble


def _annotate_schema(schema, resolve, names=()):
    names = list(names)
    if "const" in schema:
        return _annotate_literal(schema["const"]), []

    if "enum" in schema:
        for enumerated in schema["enum"]:
            return _annotate_literal(enumerated), []

    if "anyOf" in schema:  # or oneOf?
        preamble = []
        union = _typing("Union")
        tuple_ = ast.ExtSlice(dims=[])
        for subschema in schema["anyOf"]:
            annotated, extra = _annotate_schema(subschema, resolve, names)
            preamble.extend(extra)
            # FIXME: Optional[T, U] is illegal
            # if _is_literal_none(annotated):
            #     union = _typing("Optional")
            #     continue
            tuple_.dims.append(annotated)
        subscript = ast.Subscript(value=union, slice=tuple_)
        return subscript, preamble

    if "$ref" in schema:
        reference = schema["$ref"]
        resolved = resolve(reference)
        return ast.Constant(value=resolved, kind=None), []

    if "type" in schema:
        if schema["type"] == "null":
            return _annotate_literal(None), []

        if schema["type"] == "integer":
            return ast.Name(id="int"), []

        if schema["type"] == "number":
            return ast.Subscript(
                value=ast.Name(id="Union"),
                slice=ast.ExtSlice(dims=[
                    ast.Name(id="int"),
                    ast.Name(id="float"),
                ]),
            ), []

        if schema["type"] == "boolean":
            return ast.Name(id="bool"), []

        if schema["type"] == "string":
            return ast.Name(id="str"), []

        if schema["type"] == "array":
            if isinstance(schema["items"], list):
                return _annotate_tuple(schema, resolve, names)
            else:
                sequence = _typing("List")
                item, preamble = \
                    _annotate_schema(schema["items"], resolve, names)
                subscript = ast.Subscript(value=sequence, slice=item)
                return subscript, preamble

        if schema["type"] == "object":
            return _annotate_object(schema, resolve, names)

    # return _typing("Any")
    # TODO: optionally default to Any
    raise Exception(schema)


def _annotate_object(schema, resolve, names=()):
    # https://github.com/python/mypy/issues/7654
    names = list(names)
    name = _id_pascal("-".join(names))
    name_object = f"_{name}Dict"
    name_required = f"_{name}Required"
    name_optional = f"_{name}Optional"
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    required_not = set(properties.keys()) - required

    preamble = []
    anno_required = {}
    anno_optional = {}
    for annotations, fields in [
            (anno_required, required), (anno_optional, required_not)]:
        for field in fields:
            annotation, extra = _annotate_schema(
                properties[field], resolve, names + [field])
            annotations[field] = annotation
            preamble.extend(extra)
    ass_required = _typed_dict(name_required, True, anno_required)
    ass_optional = _typed_dict(name_optional, False, anno_optional)

    class_ = ast.ClassDef(
        name=name_object,
        bases=[ast.Name(id=name_required), ast.Name(id=name_optional)],
        body=[ast.Constant(value=...)],
        keywords=[],
        decorator_list=[],
    )
    return (
        ast.Name(id=name_object),
        preamble + [ass_required, ass_optional, class_],
    )


def _typed_dict(name, total, properties):
    dictionary = ast.Dict(keys=[], values=[])
    assign = ast.Assign(
        targets=[ast.Name(id=name)],
        value=ast.Call(
            func=_typing("TypedDict"),
            args=[
                ast.Constant(name, kind=None),
                dictionary,
            ],
            keywords=[ast.keyword(
                arg="total",
                value=ast.Constant(total, kind=None),
            )],
        ),
    )
    for property_, annotation in properties.items():
        dictionary.keys.append(ast.Constant(value=property_, kind=None))
        dictionary.values.append(annotation)
    return assign


def _main():
    parser = argparse.ArgumentParser(
        description="Generate Python package from service specification.")
    parser.add_argument(
        "service",
        help="Name of service or path to specification file.",
    )
    parser.add_argument(
        "--file",
        action="store_true",
        help="Generate package from a specification file.",
    )
    parser.add_argument("--name", help="Override name of the package.")
    parser.add_argument(
        "--clobber",
        action="store_true",
        help="If set, overwrite files that already exist.",
    )
    arguments = parser.parse_args()

    # Find candidate service specs
    services = []
    if arguments.file:
        with open(arguments.service) as service_file:
            services.append(skyhook.service.Service.from_yaml(service_file))
    else:
        for service in skyhook.service.discover():
            if service.name == arguments.service:
                services.append(service)
    if not services:
        raise Exception(
            f"no service specification for '{arguments.service}' installed")

    # Version tie-breaking for candidate specs.
    service = services[0]

    # Generate package
    package = Package(service)
    package.name = arguments.name if arguments.name else package.name
    mode = "w" if arguments.clobber else "x"
    for path, contents in package.files():
        print(f"Writing {path} ...")
        print(contents)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode) as module:
            module.write(contents)
