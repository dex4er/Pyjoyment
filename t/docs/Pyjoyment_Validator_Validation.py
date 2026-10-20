from Pyjo.Test import *

import re


with subtest('Synopsis'):
    import Pyjoyment.Validator

    from Pyjoyment.Validator.Validation import Validation

    validator = Pyjoyment.Validator.new()
    v = Validation(validator=validator)
    v.input = {'foo': 'bar'}
    v.required('foo').one_of('bar', 'baz')
    is_ok(v.param('foo'), 'bar', 'validated')

    # Or import the module, as in Google Python Style Guide

    import Pyjoyment.Validator
    import Pyjoyment.Validator.Validation

    validator = Pyjoyment.Validator.new()
    v = Pyjoyment.Validator.Validation.new(validator=validator)
    v.input = {'foo': 'bar'}
    v.required('foo').one_of('bar', 'baz')
    is_ok(v.param('foo'), 'bar', 'validated')


def validation(**input):
    return Pyjoyment.Validator.new().validation().set(input=input)


with subtest('Checks'):
    v = validation(foo='Abc', bar='Abc', baz='test')

    # Call validation checks
    v.required('foo').size(2, 5).like(re.compile(r'^[A-Z]'))
    v.optional('bar').equal_to('foo')
    v.optional('baz').one_of('test', '123')
    is_deeply_ok(v.passed, ['bar', 'baz', 'foo'], 'passed')

    # Longer version
    v.required('foo').check('size', 2, 5).check('like', re.compile(r'^[A-Z]'))
    ok(v.is_valid(), 'valid')

    ok(validation(foo='x').required('foo').in_('x').is_valid(), 'check of a keyword')

with subtest('csrf_token'):
    v = validation()
    token = v.csrf_token
    is_ok(token, None, 'default')
    v.csrf_token = 'fa6a08...'

with subtest('input'):
    v = validation()
    input = v.input
    is_deeply_ok(input, {}, 'default')
    v.input = {'foo': 'bar', 'baz': [123, 'yada']}

with subtest('output'):
    v = validation()
    output = v.output
    is_deeply_ok(output, {}, 'default')
    v.output = {'foo': 'bar', 'baz': [123, 'yada']}

with subtest('topic'):
    v = validation()
    topic = v.topic
    is_ok(topic, None, 'default')
    v.topic = 'foo'

with subtest('validator'):
    v = validation()
    validator = v.validator
    isa_ok(validator, Pyjoyment.Validator.object, 'validator')
    v.validator = Pyjoyment.Validator.new()

with subtest('failed'):
    v = validation(foo='x').required('foo').size(2, 3)
    names = v.failed

    # Names of all values that failed
    is_deeply_ok([name for name in v.failed], ['foo'], 'names')

with subtest('has_data'):
    v = validation(foo='bar')
    boolean = v.has_data
    ok(boolean, 'has data')

with subtest('passed'):
    v = validation(foo='bar').required('foo')
    names = v.passed

    # Names of all values that passed
    is_deeply_ok([name for name in v.passed], ['foo'], 'names')

with subtest('check'):
    v = validation(foo='bar').required('foo')
    v = v.check('size', 2, 7)
    ok(v.is_valid(), 'valid')

with subtest('csrf_protect'):
    v = validation(csrf_token='x')
    v = v.csrf_protect()
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'protected')

with subtest('error'):
    v = validation(foo='bar').required('foo').size(1, 2)
    err = v.error('foo')
    is_deeply_ok(err, ['size', True, 1, 2], 'error')
    v = v.error('foo', ['custom_check'])
    check, result, *args = ['size', True, 1, 2]
    v = v.error('foo', [check, result, *args])

    # Details about failed validation
    check, result, *args = v.error('foo')
    is_deeply_ok([check, result, args], ['size', True, [1, 2]], 'details')

    # Force validation to fail for a field without performing a check
    v.error('foo', ['some_made_up_check_name'])
    is_deeply_ok(v.error('foo'), ['some_made_up_check_name'], 'forced')

with subtest('every_param'):
    v = validation(foo=['a', 'b']).required('foo')
    values = v.every_param()
    values = v.every_param('foo')
    is_deeply_ok(values, ['a', 'b'], 'values')

    # Get first value
    first = v.every_param('foo')[0]
    is_ok(first, 'a', 'first')

with subtest('has_error'):
    v = validation(foo='bar').required('foo')
    boolean = v.has_error()
    boolean = v.has_error('foo')
    ok(not boolean, 'no error')

with subtest('is_valid'):
    v = validation(foo='bar').required('foo')
    boolean = v.is_valid()
    boolean = v.is_valid('foo')
    ok(boolean, 'valid')

with subtest('optional'):
    v = validation(foo='bar', user=' sri ')
    v = v.optional('foo')
    v = v.optional('foo', 'trim')

    # Trim value and check size
    v.optional('user', 'trim').size(1, 15)
    is_ok(v.param('user'), 'sri', 'trimmed')

with subtest('param'):
    v = validation(foo='bar', user='sri').required('foo')
    value = v.param()
    value = v.param('foo')
    is_ok(value, 'bar', 'value')

    # Get value right away
    user = v.optional('user').size(1, 15).param()
    is_ok(user, 'sri', 'right away')

with subtest('required'):
    v = validation(foo='bar', user=' sri ')
    v = v.required('foo')
    v = v.required('foo', 'trim')

    # Trim value and check size
    v.required('user', 'trim').size(1, 15)
    is_ok(v.param('user'), 'sri', 'trimmed')

done_testing()
