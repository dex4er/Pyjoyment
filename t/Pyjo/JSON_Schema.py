import Pyjo.JSON
import Pyjo.JSON.Schema
import Pyjo.URL

from Pyjo.JSON.Schema import Schema, z
from Pyjo.Test import *

import dataclasses
import datetime
import enum
import re
import typing
import uuid

from typing import Annotated, Any, Literal, NewType, NotRequired, Optional, Required, TypedDict


# Not in Mojolicious: Pyjo.JSON.Schema, JSON Schema from type hints and a builder after zod


class Unit(enum.Enum):
    """Unit of the temperature."""

    CELSIUS = 'celsius'
    FAHRENHEIT = 'fahrenheit'


class Level(enum.IntEnum):
    LOW = 1
    HIGH = 2


class Point(TypedDict):
    x: int
    y: int


class Movie(TypedDict, total=False):
    """A movie.

    With more about it.
    """

    title: Required[str]
    year: int


class Tagged(TypedDict):
    name: str
    tag: NotRequired[Annotated[str, 'A tag', {'minLength': 1}]]


class Node(TypedDict):
    name: str
    children: list['Node']


class Pair(TypedDict):
    first: Point
    second: Point | None


class Tree(TypedDict):
    root: 'Branch'


class Branch(TypedDict):
    leaves: list[str]
    branches: list['Branch']


@dataclasses.dataclass
class Location:
    city: str
    days: int = 3
    tags: list[str] = dataclasses.field(default_factory=list)
    hidden: int = dataclasses.field(default=0, init=False)


@dataclasses.dataclass
class Described:
    """A location of its own."""

    city: str


UserId = NewType('UserId', int)

type Celsius = Annotated[float, {'minimum': -273.15}]

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


with subtest('Scalars'):
    is_deeply_ok(Schema.of(bool).data, {'type': 'boolean'}, 'bool')
    is_deeply_ok(Schema.of(int).data, {'type': 'integer'}, 'int')
    is_deeply_ok(Schema.of(float).data, {'type': 'number'}, 'float')
    is_deeply_ok(Schema.of(str).data, {'type': 'string'}, 'str')
    is_deeply_ok(Schema.of(None).data, {'type': 'null'}, 'None')
    is_deeply_ok(Schema.of(type(None)).data, {'type': 'null'}, 'NoneType')
    is_deeply_ok(Schema.of(Any).data, {}, 'Any')
    is_deeply_ok(Schema.of(object).data, {}, 'object')

with subtest('Formats'):
    is_deeply_ok(Schema.of(datetime.datetime).data, {'type': 'string', 'format': 'date-time'}, 'datetime')
    is_deeply_ok(Schema.of(datetime.date).data, {'type': 'string', 'format': 'date'}, 'date')
    is_deeply_ok(Schema.of(datetime.time).data, {'type': 'string', 'format': 'time'}, 'time')
    is_deeply_ok(Schema.of(uuid.UUID).data, {'type': 'string', 'format': 'uuid'}, 'UUID')
    is_deeply_ok(Schema.of(Pyjo.URL.object).data, {'type': 'string', 'format': 'uri'}, 'Pyjo.URL')

with subtest('Collections'):
    is_deeply_ok(Schema.of(list[int]).data, {'type': 'array', 'items': {'type': 'integer'}}, 'list')
    is_deeply_ok(Schema.of(list).data, {'type': 'array'}, 'list of any')
    is_deeply_ok(Schema.of(set[str]).data, {'type': 'array', 'items': {'type': 'string'}, 'uniqueItems': True}, 'set')
    is_deeply_ok(
        Schema.of(frozenset[str]).data, {'type': 'array', 'items': {'type': 'string'}, 'uniqueItems': True}, 'frozenset'
    )
    is_deeply_ok(
        Schema.of(tuple[int, str]).data,
        {'type': 'array', 'prefixItems': [{'type': 'integer'}, {'type': 'string'}], 'minItems': 2, 'maxItems': 2},
        'tuple',
    )
    is_deeply_ok(
        Schema.of(tuple[int, ...]).data, {'type': 'array', 'items': {'type': 'integer'}}, 'tuple of any length'
    )
    is_deeply_ok(
        Schema.of(tuple[()]).data, {'type': 'array', 'prefixItems': [], 'minItems': 0, 'maxItems': 0}, 'empty tuple'
    )
    is_deeply_ok(
        Schema.of(dict[str, float]).data, {'type': 'object', 'additionalProperties': {'type': 'number'}}, 'dict'
    )
    is_deeply_ok(Schema.of(dict).data, {'type': 'object'}, 'dict of any')
    is_deeply_ok(
        Schema.of(list[dict[str, list[int]]]).data,
        {
            'type': 'array',
            'items': {'type': 'object', 'additionalProperties': {'type': 'array', 'items': {'type': 'integer'}}},
        },
        'nested',
    )

with subtest('Unions'):
    is_deeply_ok(Schema.of(int | None).data, {'type': ['integer', 'null']}, 'optional')
    # The forms of typing, which the type hints of older code have
    is_deeply_ok(
        Schema.of(Optional[str]).data,  # noqa: UP045
        {'type': ['string', 'null']},
        'Optional',
    )
    is_deeply_ok(Schema.of(int | str).data, {'anyOf': [{'type': 'integer'}, {'type': 'string'}]}, 'union')
    is_deeply_ok(
        Schema.of(int | str | None).data,
        {'anyOf': [{'type': 'integer'}, {'type': 'string'}, {'type': 'null'}]},
        'union with None',
    )
    is_deeply_ok(
        Schema.of(list[int] | None).data,
        {'anyOf': [{'type': 'array', 'items': {'type': 'integer'}}, {'type': 'null'}]},
        'optional array',
    )
    is_deeply_ok(
        Schema.of(typing.Union[int, str]).data,  # noqa: UP007
        {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        'Union',
    )

with subtest('Choices'):
    is_deeply_ok(Schema.of(Literal['a']).data, {'type': 'string', 'const': 'a'}, 'literal')
    is_deeply_ok(Schema.of(Literal['a', 'b']).data, {'type': 'string', 'enum': ['a', 'b']}, 'literals')
    is_deeply_ok(Schema.of(Literal['a', 1]).data, {'enum': ['a', 1]}, 'literals of types')
    is_deeply_ok(Schema.of(Literal[True]).data, {'type': 'boolean', 'const': True}, 'literal of bool')
    is_deeply_ok(Schema.of(Literal[1, 2]).data, {'type': 'integer', 'enum': [1, 2]}, 'literals of int')
    is_deeply_ok(Schema.of(Literal['a'] | None).data, {'anyOf': [{'type': 'string', 'const': 'a'}, {'type': 'null'}]})
    is_deeply_ok(
        Schema.of(Unit).data,
        {'type': 'string', 'enum': ['celsius', 'fahrenheit'], 'description': 'Unit of the temperature.'},
        'enum',
    )
    is_deeply_ok(Schema.of(Level).data, {'type': 'integer', 'enum': [1, 2]}, 'enum of int')
    is_deeply_ok(Schema.of(Literal[Unit.CELSIUS]).data, {'type': 'string', 'const': 'celsius'}, 'literal of enum')

with subtest('TypedDict'):
    is_deeply_ok(
        Schema.of(Point).data,
        {'type': 'object', 'properties': {'x': {'type': 'integer'}, 'y': {'type': 'integer'}}, 'required': ['x', 'y']},
        'TypedDict',
    )
    is_deeply_ok(
        Schema.of(Movie).data,
        {
            'type': 'object',
            'description': 'A movie.',
            'properties': {'title': {'type': 'string'}, 'year': {'type': 'integer'}},
            'required': ['title'],
        },
        'not total, with Required and its description',
    )
    is_deeply_ok(
        Schema.of(Tagged).data,
        {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'tag': {'type': 'string', 'description': 'A tag', 'minLength': 1},
            },
            'required': ['name'],
        },
        'NotRequired and Annotated',
    )
    read_only = getattr(typing, 'ReadOnly', None)
    if read_only is not None:
        # The functional syntax, as Python 3.12 has no ReadOnly
        Frozen = TypedDict('Frozen', {'a': read_only[int]})  # noqa: UP013  # pyright: ignore[reportInvalidTypeForm]
        is_deeply_ok(
            Schema.of(Frozen).data,
            {'type': 'object', 'properties': {'a': {'type': 'integer'}}, 'required': ['a']},
            'ReadOnly',
        )
    try:
        # The functional syntax, as Python 3.12 has no closed and extra_items of PEP 728
        Closed = TypedDict('Closed', {'a': int}, closed=True)  # noqa: UP013  # pyright: ignore[reportCallIssue]
        Extra = TypedDict('Extra', {'a': int}, extra_items=str)  # noqa: UP013  # pyright: ignore[reportCallIssue]
    except TypeError:
        Closed = Extra = None
    if Closed is not None:
        is_deeply_ok(
            Schema.of(Closed).data,
            {
                'type': 'object',
                'properties': {'a': {'type': 'integer'}},
                'required': ['a'],
                'additionalProperties': False,
            },
            'closed',
        )
        is_deeply_ok(
            Schema.of(Extra).data,
            {
                'type': 'object',
                'properties': {'a': {'type': 'integer'}},
                'required': ['a'],
                'additionalProperties': {'type': 'string'},
            },
            'extra items',
        )

with subtest('Dataclasses'):
    is_deeply_ok(
        Schema.of(Location).data,
        {
            'type': 'object',
            'properties': {
                'city': {'type': 'string'},
                'days': {'type': 'integer', 'default': 3},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['city'],
        },
        'dataclass',
    )
    is_deeply_ok(
        Schema.of(Described).data,
        {
            'type': 'object',
            'description': 'A location of its own.',
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
        },
        'with its description',
    )

with subtest('Aliases'):
    is_deeply_ok(Schema.of(UserId).data, {'type': 'integer'}, 'NewType')
    is_deeply_ok(Schema.of(Celsius).data, {'type': 'number', 'minimum': -273.15}, 'type alias')
    is_deeply_ok(
        Schema.of(list[Celsius]).data,
        {'type': 'array', 'items': {'type': 'number', 'minimum': -273.15}},
        'type alias used once',
    )

with subtest('Annotated'):
    is_deeply_ok(
        Schema.of(Annotated[str, 'Name of the city']).data, {'type': 'string', 'description': 'Name of the city'}
    )
    is_deeply_ok(
        Schema.of(Annotated[int, {'minimum': 1, 'maximum': 7}]).data,
        {'type': 'integer', 'minimum': 1, 'maximum': 7},
        'keywords',
    )
    is_deeply_ok(
        Schema.of(Annotated[str, 'City', {'pattern': '^[A-Z]'}, 42]).data,
        {'type': 'string', 'description': 'City', 'pattern': '^[A-Z]'},
        'both, and another value',
    )
    is_deeply_ok(
        Schema.of(list[Annotated[int, {'minimum': 0}]]).data,
        {'type': 'array', 'items': {'type': 'integer', 'minimum': 0}},
        'nested',
    )

with subtest('Recursion and reuse'):
    is_deeply_ok(
        Schema.of(Node).data,
        {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'children': {'type': 'array', 'items': {'$ref': '#'}}},
            'required': ['name', 'children'],
        },
        'recursive at the root',
    )
    is_deeply_ok(
        Schema.of(list[Node]).data,
        {
            'type': 'array',
            'items': {'$ref': '#/$defs/Node'},
            '$defs': {
                'Node': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'children': {'type': 'array', 'items': {'$ref': '#/$defs/Node'}},
                    },
                    'required': ['name', 'children'],
                }
            },
        },
        'recursive below the root',
    )
    is_deeply_ok(
        Schema.of(Tree).data,
        {
            'type': 'object',
            'properties': {'root': {'$ref': '#/$defs/Branch'}},
            'required': ['root'],
            '$defs': {
                'Branch': {
                    'type': 'object',
                    'properties': {
                        'leaves': {'type': 'array', 'items': {'type': 'string'}},
                        'branches': {'type': 'array', 'items': {'$ref': '#/$defs/Branch'}},
                    },
                    'required': ['leaves', 'branches'],
                }
            },
        },
        'another recursive type',
    )
    point = {
        'type': 'object',
        'properties': {'x': {'type': 'integer'}, 'y': {'type': 'integer'}},
        'required': ['x', 'y'],
    }
    is_deeply_ok(
        Schema.of(Pair).data,
        {
            'type': 'object',
            'properties': {
                'first': {'$ref': '#/$defs/Point'},
                'second': {'anyOf': [{'$ref': '#/$defs/Point'}, {'type': 'null'}]},
            },
            'required': ['first', 'second'],
            '$defs': {'Point': point},
        },
        'reused',
    )
    is_deeply_ok(
        Schema.of(tuple[Unit, Unit]).data,
        {
            'type': 'array',
            'prefixItems': [{'$ref': '#/$defs/Unit'}, {'$ref': '#/$defs/Unit'}],
            'minItems': 2,
            'maxItems': 2,
            '$defs': {
                'Unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit'], 'description': 'Unit of the temperature.'}
            },
        },
        'reused enum',
    )
    json = Schema.of(Json).data
    is_deeply_ok(
        json,
        {
            'anyOf': [
                {'type': 'object', 'additionalProperties': {'$ref': '#'}},
                {'type': 'array', 'items': {'$ref': '#'}},
                {'type': 'string'},
                {'type': 'integer'},
                {'type': 'number'},
                {'type': 'boolean'},
                {'type': 'null'},
            ]
        },
        'recursive type alias',
    )

with subtest('Errors'):
    throws_ok(lambda: Schema.of(bytes), re.compile(r'^JSON Schema does not support bytes$', re.M), 'bytes')
    throws_ok(lambda: Schema.of(list[bytes]), re.compile(r'^JSON Schema does not support bytes$', re.M), 'nested bytes')
    throws_ok(lambda: Schema.of(dict[int, str]), re.compile(r'^JSON Schema has no names of int$', re.M), 'names of int')
    throws_ok(lambda: Schema.of(typing.TypeVar('T')), re.compile(r'^JSON Schema does not support ~T$', re.M), 'TypeVar')

    class Bad(TypedDict):
        data: bytes

    throws_ok(
        lambda: Schema.of(Bad),
        re.compile(r'^JSON Schema does not support bytes in the key data of __main__\.Bad$', re.M),
        'in a TypedDict',
    )

    class Missing(TypedDict):
        data: 'Unknown'  # noqa: F821  # pyright: ignore[reportUndefinedVariable]

    throws_ok(
        lambda: Schema.of(Missing),
        re.compile(r"^JSON Schema of __main__\.Missing: name 'Unknown' is not defined$", re.M),
        'unknown name',
    )

with subtest('Functions'):

    def weather(city: str, days: int = 3, unit: Unit = Unit.CELSIUS, when: datetime.date | None = None) -> list[float]:
        """Forecast of the weather.

        For the next days.

        :param city: Name of the city.
        :param int days: Number of
            days.
        :type days: int
        :returns: Temperatures,
            one for each day.
        """
        return []

    is_deeply_ok(
        Schema.parameters(weather).data,
        {
            'type': 'object',
            'description': 'Forecast of the weather.',
            'properties': {
                'city': {'type': 'string', 'description': 'Name of the city.'},
                'days': {'type': 'integer', 'description': 'Number of days.', 'default': 3},
                'unit': {
                    'type': 'string',
                    'enum': ['celsius', 'fahrenheit'],
                    'description': 'Unit of the temperature.',
                    'default': 'celsius',
                },
                'when': {'anyOf': [{'type': 'string', 'format': 'date'}, {'type': 'null'}], 'default': None},
            },
            'required': ['city'],
            'additionalProperties': False,
        },
        'parameters of reStructuredText',
    )
    is_deeply_ok(
        Schema.returns(weather).data,
        {'type': 'array', 'items': {'type': 'number'}, 'description': 'Temperatures, one for each day.'},
        'returns of reStructuredText',
    )

    def search(c: object, query: str, limit: Annotated[int, {'minimum': 1}] = 10, **filters: str) -> dict[str, Any]:
        """Search the documents.

        Args:
            query (str): What to find,
                in any words.
            limit: How many at most.
            **filters: Fields to match.

        Returns:
            dict[str, Any]: The documents
                that match.

        Raises:
            ValueError: Never.
        """
        return {}

    is_deeply_ok(
        Schema.parameters(search, skip=1).data,
        {
            'type': 'object',
            'description': 'Search the documents.',
            'properties': {
                'query': {'type': 'string', 'description': 'What to find, in any words.'},
                'limit': {'type': 'integer', 'minimum': 1, 'description': 'How many at most.', 'default': 10},
            },
            'required': ['query'],
            'additionalProperties': {'type': 'string'},
        },
        'parameters of the Google Python Style Guide, with skip and **kwargs',
    )
    is_deeply_ok(
        Schema.returns(search).data,
        {'type': 'object', 'additionalProperties': {}, 'description': 'The documents that match.'},
        'returns of the Google Python Style Guide',
    )

    def plain(a, b=None, *, c: 'int', **rest):  # noqa: ANN001
        pass

    is_deeply_ok(
        Schema.parameters(plain).data,
        {
            'type': 'object',
            'properties': {'a': {}, 'b': {'default': None}, 'c': {'type': 'integer'}},
            'required': ['a', 'c'],
            'additionalProperties': {},
        },
        'without annotations and docstring, a string annotation',
    )
    is_ok(Schema.returns(plain), None, 'no return annotation')

    def nothing() -> None:
        pass

    is_deeply_ok(
        Schema.parameters(nothing).data, {'type': 'object', 'properties': {}, 'additionalProperties': False}, 'none'
    )
    is_deeply_ok(Schema.returns(nothing).data, {'type': 'null'}, 'returns None')

    def defaults(a: Any = object(), b: list[int] = [1, 2], c: datetime.date = datetime.date(2026, 10, 23)):  # noqa: B006, B008
        pass

    is_deeply_ok(
        Schema.parameters(defaults).data['properties'],
        {
            'a': {},
            'b': {'type': 'array', 'items': {'type': 'integer'}, 'default': [1, 2]},
            'c': {
                'type': 'string',
                'format': 'date',
                'default': '2026-10-23',
            },
        },
        'defaults of JSON only',
    )

    class Tool:
        def __call__(self, city: str) -> str:
            return city

        def method(self, city: str) -> str:
            return city

    is_deeply_ok(
        Schema.parameters(Tool()).data,
        {
            'type': 'object',
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'additionalProperties': False,
        },
        'callable object',
    )
    is_deeply_ok(
        Schema.parameters(Tool().method).data,
        {
            'type': 'object',
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'additionalProperties': False,
        },
        'bound method',
    )
    is_deeply_ok(Schema.returns(Tool()).data, {'type': 'string'}, 'returns of a callable object')
    is_deeply_ok(
        Schema.parameters(Location).data['required'], ['city'], 'class, with the parameters of its constructor'
    )

    def positional(a: int, /, b: int):
        pass

    is_deeply_ok(Schema.parameters(positional, skip=1).data['required'], ['b'], 'positional-only skipped')
    throws_ok(
        lambda: Schema.parameters(positional),
        re.compile(r'^JSON Schema has no positional members for the parameter a$', re.M),
        'positional-only',
    )
    throws_ok(
        lambda: Schema.parameters(lambda *args: None),
        re.compile(r'^JSON Schema has no positional members for the parameter args$', re.M),
        '*args',
    )

    def unknown(a: 'Unknown'):  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        pass

    throws_ok(
        lambda: Schema.parameters(unknown),
        re.compile(r"^JSON Schema of the function .*unknown: name 'Unknown' is not defined$", re.M),
        'unknown name',
    )

    def unsupported(a: bytes):
        pass

    throws_ok(
        lambda: Schema.parameters(unsupported),
        re.compile(r'^JSON Schema does not support bytes in the parameter a$', re.M),
        'unsupported type',
    )

    def returns_bytes() -> bytes:
        return b''

    throws_ok(
        lambda: Schema.returns(returns_bytes),
        re.compile(r'^JSON Schema does not support bytes in the return value$', re.M),
        'unsupported return type',
    )

with subtest('Docstrings'):

    def rst(a: int, b: int, c: int) -> int:
        """Sum.

        :param a: First.
        :param b:
        :param c: Third,
            and more.

        Something else.
        """
        return a + b + c

    is_deeply_ok(
        Schema.parameters(rst).data['properties'],
        {
            'a': {'type': 'integer', 'description': 'First.'},
            'b': {'type': 'integer'},
            'c': {'type': 'integer', 'description': 'Third, and more.'},
        },
        'fields of reStructuredText',
    )

    def google(a: int, b: int) -> int:
        """Sum of
        two numbers.

        Arguments:
            a: First,
              with more.
            b (int): Second.

        Example:
            a: not a parameter.
        """
        return a + b

    schema = Schema.parameters(google).data
    is_ok(schema['description'], 'Sum of two numbers.', 'paragraph of two lines')
    is_deeply_ok(
        schema['properties'],
        {
            'a': {'type': 'integer', 'description': 'First, with more.'},
            'b': {'type': 'integer', 'description': 'Second.'},
        },
        'section of the Google Python Style Guide',
    )
    is_ok(Schema.returns(google).data, {'type': 'integer'}, 'without a description of the return value')

    def returns_only() -> str:
        """
        Returns:
            A string.
        """
        return ''

    is_deeply_ok(Schema.returns(returns_only).data, {'type': 'string', 'description': 'A string.'}, 'only a section')
    ok('description' not in Schema.parameters(returns_only).data, 'no paragraph')

with subtest('Hand-written'):
    is_deeply_ok(Schema.new().data, {}, 'any value')
    is_deeply_ok(Schema.new({'type': 'string', 'minLength': 1}).data, {'type': 'string', 'minLength': 1}, 'dict')
    is_ok(Schema.new(False).data, False, 'none')
    is_deeply_ok(Schema.of({'type': 'string'}).data, {'type': 'string'}, 'of a dict')
    schema = z.string()
    ok(Schema.of(schema) is schema, 'of a schema')
    is_deeply_ok(
        Schema.new({'type': 'object', 'properties': {'a': z.int(), 'b': [z.string()]}}).data,
        {'type': 'object', 'properties': {'a': {'type': 'integer'}, 'b': [{'type': 'string'}]}},
        'with schemas',
    )
    is_deeply_ok(
        Schema.of(list[Annotated[str, Schema.new({'format': 'email'})]]).data,
        {'type': 'array', 'items': {'type': 'string', 'format': 'email'}},
        'keywords of a schema in Annotated',
    )

with subtest('Encoding'):
    is_ok(
        Pyjo.JSON.encode_json(z.string().min(1)),
        b'{"type":"string","minLength":1}',
        'encode_json, with the keys in the order of the schema',
    )
    is_ok(
        Pyjo.JSON.to_json({'inputSchema': z.object(a=z.int())}),
        '{"inputSchema":{"type":"object","properties":{"a":{"type":"integer"}},"required":["a"]}}',
        'to_json of a schema in a structure',
    )
    is_ok(repr(z.string()), "Pyjo.JSON.Schema.Pyjo_JSON_Schema({'type': 'string'})", 'repr')

with subtest('Builder scalars'):
    is_deeply_ok(z.string().data, {'type': 'string'}, 'string')
    is_deeply_ok(z.number().data, {'type': 'number'}, 'number')
    is_deeply_ok(z.int().data, {'type': 'integer'}, 'int')
    is_deeply_ok(z.boolean().data, {'type': 'boolean'}, 'boolean')
    is_deeply_ok(z.null().data, {'type': 'null'}, 'null')
    is_deeply_ok(z.any().data, {}, 'any')
    ok(z is Schema, 'z is the class')
    ok(Pyjo.JSON.Schema.z is Pyjo.JSON.Schema.object, 'z of the module')

with subtest('Builder strings'):
    is_deeply_ok(
        z.string().min(1).max(5).regex(r'^a+$').data,
        {'type': 'string', 'minLength': 1, 'maxLength': 5, 'pattern': '^a+$'},
        'min, max and regex',
    )
    is_deeply_ok(z.string().regex(re.compile(r'^a+$')).data, {'type': 'string', 'pattern': '^a+$'}, 're.Pattern')
    is_deeply_ok(z.string().length(3).data, {'type': 'string', 'minLength': 3, 'maxLength': 3}, 'length')
    is_deeply_ok(z.string().nonempty().data, {'type': 'string', 'minLength': 1}, 'nonempty')
    is_deeply_ok(z.string().gte(1).lte(2).data, {'type': 'string', 'minLength': 1, 'maxLength': 2}, 'gte and lte')
    is_deeply_ok(z.email().data, {'type': 'string', 'format': 'email'}, 'email')
    is_deeply_ok(z.string().email().data, {'type': 'string', 'format': 'email'}, 'string email')
    is_deeply_ok(z.url().data, {'type': 'string', 'format': 'uri'}, 'url')
    is_deeply_ok(z.string().url().data, {'type': 'string', 'format': 'uri'}, 'string url')
    is_deeply_ok(z.uuid().data, {'type': 'string', 'format': 'uuid'}, 'uuid')
    is_deeply_ok(z.string().uuid().data, {'type': 'string', 'format': 'uuid'}, 'string uuid')
    is_deeply_ok(z.iso.datetime().data, {'type': 'string', 'format': 'date-time'}, 'iso datetime')
    is_deeply_ok(z.iso.date().data, {'type': 'string', 'format': 'date'}, 'iso date')
    is_deeply_ok(z.iso.time().data, {'type': 'string', 'format': 'time'}, 'iso time')
    is_deeply_ok(z.string().datetime().data, {'type': 'string', 'format': 'date-time'}, 'string datetime')
    is_deeply_ok(z.string().date().data, {'type': 'string', 'format': 'date'}, 'string date')
    is_deeply_ok(z.string().time().data, {'type': 'string', 'format': 'time'}, 'string time')

with subtest('Builder numbers'):
    is_deeply_ok(z.number().min(0).max(10).data, {'type': 'number', 'minimum': 0, 'maximum': 10}, 'min and max')
    is_deeply_ok(
        z.number().gt(0).lt(10).multiple_of(2).data,
        {'type': 'number', 'exclusiveMinimum': 0, 'exclusiveMaximum': 10, 'multipleOf': 2},
        'gt, lt and multiple_of',
    )
    is_deeply_ok(z.int().min(1).data, {'type': 'integer', 'minimum': 1}, 'int min')
    is_deeply_ok(z.int().nullable().min(1).data, {'type': ['integer', 'null'], 'minimum': 1}, 'nullable int min')

with subtest('Builder choices'):
    is_deeply_ok(z.literal('a').data, {'type': 'string', 'const': 'a'}, 'literal')
    is_deeply_ok(z.literal(['a', 'b']).data, {'type': 'string', 'enum': ['a', 'b']}, 'literals')
    is_deeply_ok(z.literal(None).data, {'type': 'null', 'const': None}, 'literal None')
    is_deeply_ok(z.enum(['a', 'b']).data, {'type': 'string', 'enum': ['a', 'b']}, 'enum')
    is_deeply_ok(z.enum(['a']).data, {'type': 'string', 'enum': ['a']}, 'enum of one')
    is_deeply_ok(z.enum(Unit).data, {'type': 'string', 'enum': ['celsius', 'fahrenheit']}, 'enum of Enum')
    is_deeply_ok(
        z.union([z.string(), z.int(), int]).data,
        {'anyOf': [{'type': 'string'}, {'type': 'integer'}, {'type': 'integer'}]},
        'union, also of a type',
    )

with subtest('Builder arrays'):
    is_deeply_ok(
        z.array(z.string()).min(1).max(3).data,
        {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 3},
        'array',
    )
    is_deeply_ok(z.array().data, {'type': 'array'}, 'array of any')
    is_deeply_ok(z.array(str).data, {'type': 'array', 'items': {'type': 'string'}}, 'array of a type')
    is_deeply_ok(
        z.array(z.string()).nonempty().data, {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1}, 'nonempty'
    )
    is_deeply_ok(
        z.array(z.string()).length(2).data,
        {'type': 'array', 'items': {'type': 'string'}, 'minItems': 2, 'maxItems': 2},
        'length',
    )
    is_deeply_ok(
        z.tuple([z.string(), z.int()]).data,
        {'type': 'array', 'prefixItems': [{'type': 'string'}, {'type': 'integer'}], 'minItems': 2, 'maxItems': 2},
        'tuple',
    )
    is_deeply_ok(
        z.tuple([z.string()], z.int()).data,
        {'type': 'array', 'prefixItems': [{'type': 'string'}], 'minItems': 1, 'items': {'type': 'integer'}},
        'tuple with rest',
    )

with subtest('Builder objects'):
    is_deeply_ok(
        z.object({'a': z.string(), 'b': z.int().optional(), 'c': z.int().default(1), 'd': z.string().nullable()}).data,
        {
            'type': 'object',
            'properties': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer', 'default': 1},
                'd': {'type': ['string', 'null']},
            },
            'required': ['a', 'd'],
        },
        'object',
    )
    is_deeply_ok(
        z.object(city=z.string(), days=int).data,
        {
            'type': 'object',
            'properties': {'city': {'type': 'string'}, 'days': {'type': 'integer'}},
            'required': ['city', 'days'],
        },
        'keyword arguments and a type',
    )
    is_deeply_ok(
        z.object({'class': z.string()}, id=z.int()).data,
        {
            'type': 'object',
            'properties': {'class': {'type': 'string'}, 'id': {'type': 'integer'}},
            'required': ['class', 'id'],
        },
        'both',
    )
    is_deeply_ok(z.object().data, {'type': 'object', 'properties': {}}, 'empty')
    is_deeply_ok(
        z.object(a=z.string()).strict().data,
        {'type': 'object', 'properties': {'a': {'type': 'string'}}, 'required': ['a'], 'additionalProperties': False},
        'strict',
    )
    is_deeply_ok(z.strict_object({'a': z.string()}).data, z.object(a=z.string()).strict().data, 'strict_object')
    is_deeply_ok(
        z.object(a=z.string()).loose().data,
        {'type': 'object', 'properties': {'a': {'type': 'string'}}, 'required': ['a'], 'additionalProperties': {}},
        'loose',
    )
    is_deeply_ok(z.object(a=z.string()).passthrough().data, z.object(a=z.string()).loose().data, 'passthrough')
    is_deeply_ok(z.loose_object(a=z.string()).data, z.object(a=z.string()).loose().data, 'loose_object')
    is_deeply_ok(
        z.record(z.string(), z.int()).data,
        {'type': 'object', 'additionalProperties': {'type': 'integer'}},
        'record',
    )
    is_deeply_ok(z.record(z.int()).data, {'type': 'object', 'additionalProperties': {'type': 'integer'}}, 'of values')
    is_deeply_ok(
        z.record(z.enum(['a', 'b']), z.int()).data,
        {
            'type': 'object',
            'additionalProperties': {'type': 'integer'},
            'propertyNames': {'type': 'string', 'enum': ['a', 'b']},
        },
        'record of names',
    )
    is_deeply_ok(
        z.object(point=Point).data,
        {
            'type': 'object',
            'properties': {
                'point': {
                    'type': 'object',
                    'properties': {'x': {'type': 'integer'}, 'y': {'type': 'integer'}},
                    'required': ['x', 'y'],
                }
            },
            'required': ['point'],
        },
        'of a TypedDict',
    )

with subtest('Builder modifiers'):
    is_deeply_ok(z.string().describe('City').data, {'type': 'string', 'description': 'City'}, 'describe')
    is_deeply_ok(z.int().nullable().data, {'type': ['integer', 'null']}, 'nullable')
    is_deeply_ok(z.int().nullable().nullable().data, {'type': ['integer', 'null']}, 'nullable twice')
    is_deeply_ok(
        z.int().min(1).nullable().data,
        {'anyOf': [{'type': 'integer', 'minimum': 1}, {'type': 'null'}]},
        'nullable of more than a type',
    )
    is_deeply_ok(z.int().nullish().data, {'type': ['integer', 'null']}, 'nullish')
    ok(z.int().nullish().is_optional, 'nullish is optional')
    ok(z.int().optional().nullable().is_optional, 'optional and nullable')
    ok(not z.int().is_optional, 'not optional')
    is_deeply_ok(z.int().optional().data, {'type': 'integer'}, 'optional at the root')
    is_deeply_ok(z.int().default(3).data, {'type': 'integer', 'default': 3}, 'default at the root')
    is_deeply_ok(
        z.string().meta({'$schema': Pyjo.JSON.Schema.DIALECT}).data,
        {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'string'},
        'meta of the dialect',
    )
    is_deeply_ok(
        z.string().meta(title='City', examples=['Warsaw']).data,
        {'type': 'string', 'title': 'City', 'examples': ['Warsaw']},
        'meta',
    )
    schema = z.string()
    ok(schema.min(1) is not schema, 'a new schema')
    is_deeply_ok(schema.data, {'type': 'string'}, 'the schema stays')
    is_deeply_ok(Schema.of(int).min(1).data, {'type': 'integer', 'minimum': 1}, 'of a type')

with subtest('Builder recursion'):
    category = z.object(name=z.string(), subcategories=z.array(z.lazy(lambda: category)))
    is_deeply_ok(
        category.data,
        {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'subcategories': {'type': 'array', 'items': {'$ref': '#'}}},
            'required': ['name', 'subcategories'],
        },
        'lazy at the root',
    )
    linked = z.lazy(lambda: z.object(value=z.int(), next=z.lazy(lambda: linked).optional()))
    is_deeply_ok(
        linked.data,
        {
            'type': 'object',
            'properties': {'value': {'type': 'integer'}, 'next': {'$ref': '#'}},
            'required': ['value'],
        },
        'lazy root',
    )
    is_deeply_ok(
        z.array(category).data,
        {
            'type': 'array',
            'items': {'$ref': '#/$defs/Schema'},
            '$defs': {
                'Schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'subcategories': {'type': 'array', 'items': {'$ref': '#/$defs/Schema'}},
                    },
                    'required': ['name', 'subcategories'],
                }
            },
        },
        'lazy below the root',
    )
    category.name = 'Category'
    is_deeply_ok(list(z.array(category).data['$defs']), ['Category'], 'name in $defs')
    tag = z.string().min(1)
    is_deeply_ok(
        z.object(a=tag, b=tag).data,
        {
            'type': 'object',
            'properties': {'a': {'type': 'string', 'minLength': 1}, 'b': {'type': 'string', 'minLength': 1}},
            'required': ['a', 'b'],
        },
        'reused without a name',
    )
    tag.name = 'Tag'
    is_deeply_ok(
        z.object(a=tag, b=tag).data,
        {
            'type': 'object',
            'properties': {'a': {'$ref': '#/$defs/Tag'}, 'b': {'$ref': '#/$defs/Tag'}},
            'required': ['a', 'b'],
            '$defs': {'Tag': {'type': 'string', 'minLength': 1}},
        },
        'reused with a name',
    )
    is_deeply_ok(
        z.object(a=z.lazy(lambda: z.int()).describe('An int')).data,
        {'type': 'object', 'properties': {'a': {'type': 'integer', 'description': 'An int'}}, 'required': ['a']},
        'lazy with a description',
    )
    ok(z.lazy(lambda: z.int()).is_lazy, 'is_lazy')
    ok(not z.int().is_lazy, 'not is_lazy')
    is_deeply_ok(z.lazy(lambda: int).resolve().data, {'type': 'integer'}, 'resolve a type')
    loop = z.lazy(lambda: loop)
    throws_ok(lambda: loop.data, re.compile(r'^JSON Schema of a lazy schema that gives itself$', re.M), 'loop')

with subtest('Builder errors'):
    throws_ok(lambda: z.boolean().min(1), re.compile(r'^JSON Schema has no min for the type boolean$', re.M), 'min')
    throws_ok(lambda: z.any().max(1), re.compile(r'^JSON Schema has no max for a schema without a type$', re.M), 'max')
    throws_ok(lambda: z.string().gt(1), re.compile(r'^JSON Schema has no gt for the type string$', re.M), 'gt')
    throws_ok(lambda: z.int().regex('a'), re.compile(r'^JSON Schema has no regex for the type integer$', re.M), 'regex')
    throws_ok(lambda: z.int().email(), re.compile(r'^JSON Schema has no email for the type integer$', re.M), 'email')
    throws_ok(
        lambda: z.string().strict(), re.compile(r'^JSON Schema has no strict for the type string$', re.M), 'strict'
    )
    throws_ok(lambda: Schema.new(True).describe('x'), re.compile(r'^JSON Schema True has no keywords$', re.M), 'bool')

done_testing()
