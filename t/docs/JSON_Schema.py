from Pyjo.Test import *

import re

from typing import TypedDict


with subtest('Synopsis'):
    from Pyjo.JSON.Schema import Schema, z

    def weather(city: str, days: int = 3) -> dict[str, float]:
        """Forecast of the weather.

        :param city: Name of the city.
        :param days: Number of days.
        """
        return {}

    is_deeply_ok(
        Schema.parameters(weather).data,
        {
            'type': 'object',
            'description': 'Forecast of the weather.',
            'properties': {
                'city': {'type': 'string', 'description': 'Name of the city.'},
                'days': {'type': 'integer', 'description': 'Number of days.', 'default': 3},
            },
            'required': ['city'],
            'additionalProperties': False,
        },
        'Schema.parameters(weather).data',
    )
    is_deeply_ok(
        Schema.returns(weather).data,
        {'type': 'object', 'additionalProperties': {'type': 'number'}},
        'Schema.returns(weather).data',
    )

    is_deeply_ok(
        z.object(city=z.string().describe('Name of the city'), days=z.int().min(1).optional()).data,
        {
            'type': 'object',
            'properties': {
                'city': {'type': 'string', 'description': 'Name of the city'},
                'days': {'type': 'integer', 'minimum': 1},
            },
            'required': ['city'],
        },
        'z.object(...).data',
    )

    # Or import the module, as in Google Python Style Guide

    import Pyjo.JSON.Schema

    is_deeply_ok(
        Pyjo.JSON.Schema.of(list[int]).data, {'type': 'array', 'items': {'type': 'integer'}}, 'of(list[int]).data'
    )
    is_deeply_ok(Pyjo.JSON.Schema.new({'type': 'string'}).data, {'type': 'string'}, "new({'type': 'string'}).data")

with subtest('Description'):
    # {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'string'}
    is_deeply_ok(
        z.string().meta({'$schema': Pyjo.JSON.Schema.DIALECT}).data,
        {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'string'},
        'DIALECT',
    )

with subtest('new'):
    schema = Pyjo.JSON.Schema.new()
    is_deeply_ok(schema.data, {}, 'any value')
    schema = Pyjo.JSON.Schema.new({'type': 'string', 'minLength': 1})
    is_deeply_ok(schema.data, {'type': 'string', 'minLength': 1}, 'written by hand')

with subtest('name'):
    name = schema.name
    is_ok(name, None, 'no name')
    schema.name = 'Category'
    is_ok(schema.name, 'Category', 'schema.name')

with subtest('__json__'):
    data = schema.__json__()
    is_deeply_ok(data, {'type': 'string', 'minLength': 1}, 'data')

with subtest('data'):
    data = schema.data
    is_deeply_ok(data, {'type': 'string', 'minLength': 1}, 'data')

    # {'type': 'array', 'items': {'type': 'integer'}}
    is_deeply_ok(Pyjo.JSON.Schema.of(list[int]).data, {'type': 'array', 'items': {'type': 'integer'}}, 'of a list')

with subtest('is_optional'):
    boolean = z.int().optional().is_optional
    is_ok(boolean, True, 'boolean')

with subtest('is_lazy'):
    boolean = z.lazy(lambda: z.int()).is_lazy
    is_ok(boolean, True, 'boolean')

with subtest('keywords'):
    keywords = z.array(z.int()).keywords
    is_deeply_ok(list(keywords), ['type', 'items'], 'keywords')
    ok(isinstance(keywords['items'], Pyjo.JSON.Schema.object), 'with a schema')

with subtest('resolve'):
    schema = z.lazy(lambda: z.int()).resolve()
    is_deeply_ok(schema.data, {'type': 'integer'}, 'resolve')

with subtest('of'):

    class Point(TypedDict):
        x: int
        y: int

    schema = Pyjo.JSON.Schema.of(list[int])
    is_deeply_ok(schema.data, {'type': 'array', 'items': {'type': 'integer'}}, 'of a list')
    schema = Pyjo.JSON.Schema.of(Point)
    is_deeply_ok(
        schema.data,
        {'type': 'object', 'properties': {'x': {'type': 'integer'}, 'y': {'type': 'integer'}}, 'required': ['x', 'y']},
        'of a TypedDict',
    )

    # {'type': ['string', 'null']}
    is_deeply_ok(Pyjo.JSON.Schema.of(str | None).data, {'type': ['string', 'null']}, 'of str | None')

    # {'type': 'object', 'additionalProperties': {'type': 'number'}}
    is_deeply_ok(
        Pyjo.JSON.Schema.of(dict[str, float]).data,
        {'type': 'object', 'additionalProperties': {'type': 'number'}},
        'of dict[str, float]',
    )

with subtest('parameters'):

    def tool(c: object, city: str) -> str:
        return city

    schema = Pyjo.JSON.Schema.parameters(tool)
    is_deeply_ok(schema.data['required'], ['c', 'city'], 'parameters')
    schema = Pyjo.JSON.Schema.parameters(tool, skip=1)
    is_deeply_ok(schema.data['required'], ['city'], 'skip')

    def weather(c, city: str, days: int = 3):  # noqa: ANN001
        """Forecast of the weather.

        Args:
            city: Name of the city.
        """

    # {'type': 'object', 'description': 'Forecast of the weather.',
    #  'properties': {'city': {'type': 'string', 'description': 'Name of the city.'},
    #                 'days': {'type': 'integer', 'default': 3}},
    #  'required': ['city'], 'additionalProperties': False}
    is_deeply_ok(
        Pyjo.JSON.Schema.parameters(weather, skip=1).data,
        {
            'type': 'object',
            'description': 'Forecast of the weather.',
            'properties': {
                'city': {'type': 'string', 'description': 'Name of the city.'},
                'days': {'type': 'integer', 'default': 3},
            },
            'required': ['city'],
            'additionalProperties': False,
        },
        'parameters(weather, skip=1)',
    )

with subtest('returns'):
    schema = Pyjo.JSON.Schema.returns(tool)
    is_deeply_ok(schema.data, {'type': 'string'}, 'returns')

    def forecast(city: str) -> list[float]:
        """Temperatures.

        :returns: One for each day.
        """
        return []

    # {'type': 'array', 'items': {'type': 'number'}, 'description': 'One for each day.'}
    is_deeply_ok(
        Pyjo.JSON.Schema.returns(forecast).data,
        {'type': 'array', 'items': {'type': 'number'}, 'description': 'One for each day.'},
        'returns(forecast)',
    )

with subtest('string'):
    schema = z.string()
    is_deeply_ok(schema.data, {'type': 'string'}, 'string')

    # {'type': 'string', 'minLength': 1, 'maxLength': 5}
    is_deeply_ok(z.string().min(1).max(5).data, {'type': 'string', 'minLength': 1, 'maxLength': 5}, 'min and max')

with subtest('number'):
    schema = z.number()
    is_deeply_ok(schema.data, {'type': 'number'}, 'number')

    # {'type': 'number', 'exclusiveMinimum': 0}
    is_deeply_ok(z.number().gt(0).data, {'type': 'number', 'exclusiveMinimum': 0}, 'gt')

with subtest('boolean'):
    schema = z.boolean()
    is_deeply_ok(schema.data, {'type': 'boolean'}, 'boolean')

with subtest('null'):
    schema = z.null()
    is_deeply_ok(schema.data, {'type': 'null'}, 'null')

with subtest('literal'):
    schema = z.literal('celsius')
    is_deeply_ok(schema.data, {'type': 'string', 'const': 'celsius'}, 'literal')
    schema = z.literal(['celsius', 'fahrenheit'])
    is_deeply_ok(schema.data, {'type': 'string', 'enum': ['celsius', 'fahrenheit']}, 'literals')

    # {'type': 'string', 'const': 'celsius'}
    is_deeply_ok(z.literal('celsius').data, {'type': 'string', 'const': 'celsius'}, "literal('celsius')")

with subtest('union'):
    schema = z.union([z.string(), z.int()])
    is_deeply_ok(schema.data, {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}, 'union')

with subtest('array'):
    schema = z.array(z.string())
    is_deeply_ok(schema.data, {'type': 'array', 'items': {'type': 'string'}}, 'array')

    # {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1}
    is_deeply_ok(
        z.array(z.string()).nonempty().data, {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1}, 'nonempty'
    )

with subtest('tuple'):
    schema = z.tuple([z.string(), z.int()])
    is_ok(schema.data['maxItems'], 2, 'tuple')
    schema = z.tuple([z.string()], z.int())
    is_deeply_ok(schema.data['items'], {'type': 'integer'}, 'with rest')

    # {'type': 'array', 'prefixItems': [{'type': 'string'}, {'type': 'integer'}],
    #  'minItems': 2, 'maxItems': 2}
    is_deeply_ok(
        z.tuple([z.string(), z.int()]).data,
        {'type': 'array', 'prefixItems': [{'type': 'string'}, {'type': 'integer'}], 'minItems': 2, 'maxItems': 2},
        'tuple of two',
    )

with subtest('record'):
    schema = z.record(z.string(), z.int())
    is_deeply_ok(schema.data, {'type': 'object', 'additionalProperties': {'type': 'integer'}}, 'record')
    schema = z.record(z.int())
    is_deeply_ok(schema.data, {'type': 'object', 'additionalProperties': {'type': 'integer'}}, 'of values')

    # {'type': 'object', 'additionalProperties': {'type': 'integer'}}
    is_deeply_ok(
        z.record(z.string(), z.int()).data,
        {'type': 'object', 'additionalProperties': {'type': 'integer'}},
        'record(z.string(), z.int())',
    )

with subtest('strict_object'):
    schema = z.strict_object({'city': z.string()})
    is_ok(schema.data['additionalProperties'], False, 'strict_object')

with subtest('loose_object'):
    schema = z.loose_object({'city': z.string()})
    is_deeply_ok(schema.data['additionalProperties'], {}, 'loose_object')

with subtest('lazy'):
    category = z.object(name=z.string(), subcategories=z.array(z.lazy(lambda: category)))
    schema = z.lazy(lambda: category)
    is_deeply_ok(schema.data, category.data, 'lazy')

    # {'type': 'object',
    #  'properties': {'name': {'type': 'string'},
    #                 'subcategories': {'type': 'array', 'items': {'$ref': '#'}}},
    #  'required': ['name', 'subcategories']}
    is_deeply_ok(
        category.data,
        {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'subcategories': {'type': 'array', 'items': {'$ref': '#'}}},
            'required': ['name', 'subcategories'],
        },
        'category.data',
    )

with subtest('min'):
    schema = z.string().min(1)
    is_ok(schema.data['minLength'], 1, 'min')

with subtest('max'):
    schema = z.string().max(5)
    is_ok(schema.data['maxLength'], 5, 'max')

with subtest('gte'):
    schema = z.int().gte(1)
    is_ok(schema.data['minimum'], 1, 'gte')

with subtest('lte'):
    schema = z.int().lte(5)
    is_ok(schema.data['maximum'], 5, 'lte')

with subtest('length'):
    schema = z.string().length(3)
    is_deeply_ok(schema.data, {'type': 'string', 'minLength': 3, 'maxLength': 3}, 'length')

with subtest('nonempty'):
    schema = z.string().nonempty()
    is_ok(schema.data['minLength'], 1, 'nonempty')

with subtest('gt'):
    schema = z.number().gt(0)
    is_ok(schema.data['exclusiveMinimum'], 0, 'gt')

with subtest('lt'):
    schema = z.number().lt(10)
    is_ok(schema.data['exclusiveMaximum'], 10, 'lt')

with subtest('multiple_of'):
    schema = z.number().multiple_of(2)
    is_ok(schema.data['multipleOf'], 2, 'multiple_of')

with subtest('regex'):
    schema = z.string().regex(r'^[a-z]+$')
    is_ok(schema.data['pattern'], '^[a-z]+$', 'regex')
    schema = z.string().regex(re.compile(r'^[a-z]+$'))
    is_ok(schema.data['pattern'], '^[a-z]+$', 're.Pattern')

with subtest('email'):
    schema = z.email()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'email'}, 'email')
    schema = z.string().email()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'email'}, 'string email')

with subtest('url'):
    schema = z.url()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'uri'}, 'url')
    schema = z.string().url()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'uri'}, 'string url')

with subtest('uuid'):
    schema = z.uuid()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'uuid'}, 'uuid')
    schema = z.string().uuid()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'uuid'}, 'string uuid')

with subtest('datetime'):
    schema = z.string().datetime()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'date-time'}, 'datetime')

with subtest('date'):
    schema = z.string().date()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'date'}, 'date')

with subtest('time'):
    schema = z.string().time()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'time'}, 'time')

with subtest('strict'):
    schema = z.object(city=z.string()).strict()
    is_ok(schema.data['additionalProperties'], False, 'strict')

with subtest('loose'):
    schema = z.object(city=z.string()).loose()
    is_deeply_ok(schema.data['additionalProperties'], {}, 'loose')

with subtest('passthrough'):
    schema = z.object(city=z.string()).passthrough()
    is_deeply_ok(schema.data['additionalProperties'], {}, 'passthrough')

with subtest('optional'):
    schema = z.int().optional()
    ok(schema.is_optional, 'optional')

    # {'type': 'object', 'properties': {'days': {'type': 'integer'}}}
    is_deeply_ok(
        z.object(days=z.int().optional()).data,
        {'type': 'object', 'properties': {'days': {'type': 'integer'}}},
        'not required',
    )

with subtest('nullable'):
    schema = z.int().nullable()
    is_deeply_ok(schema.data, {'type': ['integer', 'null']}, 'nullable')

    # {'type': ['string', 'null']}
    is_deeply_ok(z.string().nullable().data, {'type': ['string', 'null']}, 'string nullable')

with subtest('nullish'):
    schema = z.int().nullish()
    ok(schema.is_optional, 'optional')
    is_deeply_ok(schema.data, {'type': ['integer', 'null']}, 'nullable')

with subtest('default'):
    schema = z.int().default(3)
    ok(schema.is_optional, 'optional')
    is_deeply_ok(schema.data, {'type': 'integer', 'default': 3}, 'default')

with subtest('describe'):
    schema = z.string().describe('Name of the city')
    is_deeply_ok(schema.data, {'type': 'string', 'description': 'Name of the city'}, 'describe')

with subtest('meta'):
    schema = z.string().meta({'$schema': Pyjo.JSON.Schema.DIALECT})
    is_ok(schema.data['$schema'], 'https://json-schema.org/draft/2020-12/schema', 'meta of a dict')
    schema = z.string().meta(title='City', examples=['Warsaw'])
    is_deeply_ok(schema.data, {'type': 'string', 'title': 'City', 'examples': ['Warsaw']}, 'meta of keywords')

with subtest('any'):
    schema = z.any()
    is_deeply_ok(schema.data, {}, 'any')

with subtest('int'):
    schema = z.int()
    is_deeply_ok(schema.data, {'type': 'integer'}, 'int')

    # {'type': 'integer', 'minimum': 1, 'maximum': 7}
    is_deeply_ok(z.int().min(1).max(7).data, {'type': 'integer', 'minimum': 1, 'maximum': 7}, 'min and max')

with subtest('enum'):
    import enum

    class Unit(enum.Enum):
        CELSIUS = 'celsius'
        FAHRENHEIT = 'fahrenheit'

    schema = z.enum(['celsius', 'fahrenheit'])
    is_deeply_ok(schema.data, {'type': 'string', 'enum': ['celsius', 'fahrenheit']}, 'enum')
    schema = z.enum(Unit)
    is_deeply_ok(schema.data, {'type': 'string', 'enum': ['celsius', 'fahrenheit']}, 'enum of Enum')

    # {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
    is_deeply_ok(
        z.enum(['celsius', 'fahrenheit']).data, {'type': 'string', 'enum': ['celsius', 'fahrenheit']}, 'enum of values'
    )

with subtest('object'):
    schema = z.object({'city': z.string(), 'days': z.int().optional()})
    is_deeply_ok(schema.data['required'], ['city'], 'object of a dict')
    schema = z.object(city=z.string(), days=z.int().optional())
    is_deeply_ok(schema.data['required'], ['city'], 'object of keyword arguments')

    # {'type': 'object', 'properties': {'class': {'type': 'string'}}, 'required': ['class']}
    is_deeply_ok(
        z.object({'class': z.string()}).data,
        {'type': 'object', 'properties': {'class': {'type': 'string'}}, 'required': ['class']},
        'a keyword of Python',
    )

with subtest('iso'):
    schema = z.iso.datetime()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'date-time'}, 'datetime')
    schema = z.iso.date()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'date'}, 'date')
    schema = z.iso.time()
    is_deeply_ok(schema.data, {'type': 'string', 'format': 'time'}, 'time')

done_testing()
