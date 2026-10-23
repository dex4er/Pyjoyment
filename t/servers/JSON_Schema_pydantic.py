from Pyjo.JSON.Schema import Schema
from Pyjo.Test import *

import dataclasses
import datetime
import enum
import importlib.util
import uuid

from typing import Any, Literal, NotRequired, Optional, TypedDict


# Not in Mojolicious: the schemas of the type hints of Pyjo.JSON.Schema next to the ones that pydantic makes, which the
# MCP SDK gives its tools, in the dependency group "servers"

if not importlib.util.find_spec('pydantic'):
    plan(skip_all='needs the dependency group "servers", without pydantic')

from pydantic import TypeAdapter  # noqa: E402


class Unit(enum.Enum):
    CELSIUS = 'celsius'
    FAHRENHEIT = 'fahrenheit'


class Point(TypedDict):
    x: int
    y: int


class Movie(TypedDict):
    title: str
    year: NotRequired[int]


class Pair(TypedDict):
    first: Point
    second: Point | None


@dataclasses.dataclass
class Location:
    city: str
    days: int = 3
    unit: Unit = Unit.CELSIUS


def weather(city: str, days: int = 3, unit: Literal['c', 'f'] | None = None, when: datetime.date | None = None):
    pass


def search(query: str, limit: int = 10, tags: list[str] = [], point: Point | None = None):  # noqa: B006
    pass


TYPES: list[tuple[str, Any]] = [
    ('bool', bool),
    ('int', int),
    ('float', float),
    ('str', str),
    ('None', type(None)),
    ('Any', Any),
    ('datetime', datetime.datetime),
    ('date', datetime.date),
    ('time', datetime.time),
    ('UUID', uuid.UUID),
    ('list', list[int]),
    ('set', set[str]),
    ('frozenset', frozenset[str]),
    ('tuple', tuple[int, str]),
    ('tuple of any length', tuple[int, ...]),
    ('dict', dict[str, float]),
    ('nested', list[dict[str, list[int]]]),
    ('optional', int | None),
    ('Optional', Optional[str]),  # noqa: UP045
    ('union', int | str),
    ('union with None', int | str | None),
    ('optional array', list[int] | None),
    ('literal', Literal['a']),
    ('literals', Literal['a', 'b']),
    ('literals of types', Literal['a', 1]),
    ('enum', Unit),
    ('list of enum', list[Unit]),
    ('TypedDict', Point),
    ('NotRequired', Movie),
    ('reused', Pair),
    ('dataclass', Location),
    ('list of TypedDict', list[Point]),
]


def inline(schema: Any, defs: dict[str, Any] | None = None) -> Any:
    # The $defs in the place of their $ref, as pydantic puts every TypedDict, dataclass and enum.Enum there, and
    # Pyjo.JSON.Schema only those that are used more than once
    if isinstance(schema, list):
        return [inline(item, defs) for item in schema]  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(schema, dict):
        return schema
    if defs is None:
        defs = schema.get('$defs', {})
    ref = schema.get('$ref')
    if isinstance(ref, str) and ref.startswith('#/$defs/'):
        rest = {name: value for name, value in schema.items() if name != '$ref'}  # pyright: ignore[reportUnknownVariableType]
        return {**inline(defs[ref[8:]], defs), **inline(rest, defs)}  # pyright: ignore[reportOptionalSubscript]
    return {name: inline(value, defs) for name, value in schema.items() if name != '$defs'}  # pyright: ignore[reportUnknownVariableType]


def normalize(schema: Any) -> Any:
    # The differences of pydantic, each noted where it is left out
    if isinstance(schema, list):
        return [normalize(item) for item in schema]  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(schema, dict):
        return schema

    # pydantic adds a title, the name of the type or of the property, which is not a property named title
    schema = {
        name: {key: normalize(item) for key, item in value.items()} if name == 'properties' else normalize(value)  # pyright: ignore[reportUnknownVariableType]
        for name, value in schema.items()  # pyright: ignore[reportUnknownVariableType]
        if name != 'title'
    }

    # pydantic has a type and null in anyOf, where Pyjo.JSON.Schema adds null to the type of a schema of only a type
    any_of = schema.get('anyOf')
    if isinstance(any_of, list) and {'type': 'null'} in any_of:
        others = [item for item in any_of if item != {'type': 'null'}]  # pyright: ignore[reportUnknownVariableType]
        if len(others) == 1 and isinstance(others[0], dict) and list(others[0]) == ['type']:  # pyright: ignore[reportUnknownArgumentType]
            schema = {
                **{name: value for name, value in schema.items() if name != 'anyOf'},
                'type': [others[0]['type'], 'null'],
            }  # pyright: ignore[reportUnknownVariableType]

    return schema


with subtest('Types against pydantic'):
    for name, tp in TYPES:
        is_deeply_ok(inline(Schema.of(tp).data), normalize(inline(TypeAdapter(tp).json_schema())), name)

with subtest('Parameters against pydantic'):
    for function in (weather, search):
        is_deeply_ok(
            inline(Schema.parameters(function).data),
            normalize(inline(TypeAdapter(function).json_schema())),
            function.__name__,
        )

done_testing()
