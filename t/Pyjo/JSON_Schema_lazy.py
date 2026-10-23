# /// script
# requires-python = ">=3.14"
# ///
from Pyjo.JSON.Schema import Schema
from Pyjo.Test import *

from typing import TypedDict


# Not in Mojolicious: the lazy annotations of PEP 649, which name a type that is defined after them


def order(item: Item, quantity: int = 1) -> Receipt:
    pass


class Item(TypedDict):
    name: str


class Receipt(TypedDict):
    items: list[Item]
    total: float


with subtest('Lazy annotations'):
    is_deeply_ok(
        Schema.parameters(order).data,
        {
            'type': 'object',
            'properties': {
                'item': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']},
                'quantity': {'type': 'integer', 'default': 1},
            },
            'required': ['item'],
            'additionalProperties': False,
        },
        'parameters',
    )
    is_deeply_ok(
        Schema.returns(order).data,
        {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']},
                },
                'total': {'type': 'number'},
            },
            'required': ['items', 'total'],
        },
        'returns',
    )

done_testing()
