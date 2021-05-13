"""Tests for the code generator."""

import astunparse

import skyhook.generate


class TestIDSnake:

    def test_single(self):
        assert skyhook.generate._id_snake("bob") == "bob"

    def test_multiple(self):
        assert skyhook.generate._id_snake("bob-ross") == "bob_ross"

    def test_keyword(self):
        assert skyhook.generate._id_snake("class") == "class_"


class TestIDPascal:

    def test_single(self):
        assert skyhook.generate._id_pascal("bob") == "Bob"

    def test_multiple(self):
        assert skyhook.generate._id_pascal("bob-ross") == "BobRoss"

    def test_keyword(self):
        assert skyhook.generate._id_pascal("true") == "True_"


class TestAnnotateSchema:

    def test_const(self):
        schema = {"const": "foo"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "_typing.Literal['foo']\n"
        assert preamble == []

    def test_enum(self):
        schema = {"enum": ["foo", "bar", 50]}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "_typing.Literal['foo', 'bar', 50]\n"
        assert preamble == []

    def test_type_null(self):
        schema = {"type": "null"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "None\n"
        assert preamble == []

    def test_type_integer(self):
        schema = {"type": "integer"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "int\n"
        assert preamble == []

    def test_type_number(self):
        schema = {"type": "number"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "_typing.Union[int, float]\n"
        assert preamble == []

    def test_type_boolean(self):
        schema = {"type": "boolean"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "bool\n"
        assert preamble == []

    def test_type_string(self):
        schema = {"type": "string"}
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "str\n"
        assert preamble == []

    def test_type_tuple(self):
        schema = {
            "type": "array",
            "items": [
                {"type": "integer"},
                {"type": "string"},
                {"const": 500},
            ],
        }
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "_typing.Tuple[int, str, _typing.Literal[500]]\n"
        assert preamble == []

    def test_type_array(self):
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        node, preamble = skyhook.generate._annotate_schema(schema, ..., [])
        code = astunparse.unparse(node)
        assert code == "_typing.List[str]\n"
        assert preamble == []
