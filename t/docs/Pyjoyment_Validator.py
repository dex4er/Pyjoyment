import Pyjo.Upload
import Pyjoyment.Validator.Validation

from Pyjo.Test import *

import re


with subtest('Synopsis'):
    import Pyjoyment.Validator

    validator = Pyjoyment.Validator.new()
    v = validator.validation()
    v.input = {'foo': 'bar'}
    v.required('foo').like(re.compile(r'ar$'))
    is_ok(v.param('foo'), 'bar', 'validated')


def validation(**input):
    return Pyjoyment.Validator.new().validation().set(input=input)


with subtest('equal_to'):
    v = validation(foo='bar', bar='bar').required('bar')
    v = v.equal_to('foo')
    ok(v.is_valid(), 'equal')

with subtest('in'):
    v = validation(foo='bar').required('foo')
    v = v.one_of('foo', 'bar', 'baz')
    ok(v.is_valid(), 'one of the values')
    ok(not validation(foo='x').required('foo').in_('foo').is_valid(), 'alias')

with subtest('like'):
    v = validation(foo='Bar').required('foo')
    v = v.like(re.compile(r'^[A-Z]'))
    ok(v.is_valid(), 'matches')

with subtest('num'):
    v = validation(foo='4').required('foo')
    v = v.num()
    v = v.num(2, 5)
    v = v.num(-3, 7)
    v = v.num(2, None)
    v = v.num(None, 5)
    ok(v.is_valid(), 'number in range')

with subtest('size'):
    v = validation(foo='four').required('foo')
    v = v.size(2, 5)
    v = v.size(2, None)
    v = v.size(None, 5)
    ok(v.is_valid(), 'size in range')

with subtest('upload'):
    v = validation(foo=Pyjo.Upload.new()).required('foo')
    v = v.upload()
    ok(v.is_valid(), 'upload')

with subtest('comma_separated'):
    v = validation(foo='a, b')
    v = v.optional('foo', 'comma_separated')
    is_deeply_ok(v.output, {'foo': ['a', 'b']}, 'split')

with subtest('not_empty'):
    v = validation(foo='')
    v = v.optional('foo', 'not_empty')
    ok(not v.is_valid(), 'removed')

with subtest('trim'):
    v = validation(foo=' bar ')
    v = v.optional('foo', 'trim')
    is_ok(v.param(), 'bar', 'trimmed')

with subtest('checks'):
    validator = Pyjoyment.Validator.new()
    checks = validator.checks
    is_deeply_ok(sorted(checks), ['equal_to', 'in', 'like', 'num', 'size', 'upload'], 'default')
    validator.checks = {'size': lambda v, name, value, *args: ...}

with subtest('filters'):
    validator = Pyjoyment.Validator.new()
    filters = validator.filters
    is_deeply_ok(sorted(filters), ['comma_separated', 'not_empty', 'trim'], 'default')
    validator.filters = {'trim': lambda v, name, value: ...}

with subtest('add_check'):
    validator = Pyjoyment.Validator.new()
    validator = validator.add_check('size', lambda v, name, value, *args: ...)

    @validator.add_check('size')
    def size(v, name, value, *args): ...

    @validator.add_check('foo')
    def foo(v, name, value, *args):
        ...
        return None

    is_ok(validator.checks['foo'], foo, 'registered')
    ok(validator.validation().set(input={'x': 1}).required('x').foo().is_valid(), 'check of the validation')

with subtest('add_filter'):
    validator = Pyjoyment.Validator.new()
    validator = validator.add_filter('trim', lambda v, name, value: ...)

    @validator.add_filter('trim')
    def trim(v, name, value): ...

    @validator.add_filter('foo')
    def foo(v, name, value):
        ...
        return value

    is_ok(validator.filters['foo'], foo, 'registered')

with subtest('new'):
    validator = Pyjoyment.Validator.new()
    isa_ok(validator, Pyjoyment.Validator.object, 'validator')

with subtest('validation'):
    validator = Pyjoyment.Validator.new()
    v = validator.validation()
    isa_ok(v, Pyjoyment.Validator.Validation.object, 'validation')

    v = validator.validation()
    v.input = {'foo': 'bar'}
    v.required('foo').size(1, 5)
    is_ok(v.param('foo'), 'bar', 'validated')

done_testing()
