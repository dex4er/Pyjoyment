from Pyjo.Test import *

import re


with subtest('Synopsis'):
    from Pyjoyment.Routes.Pattern import Pattern

    # Create pattern
    pattern = Pattern('/test/:name')
    is_ok(pattern.unparsed, '/test/:name', 'unparsed')

    # Or import the module, as in Google Python Style Guide
    import Pyjoyment.Routes.Pattern

    # Create pattern
    pattern = Pyjoyment.Routes.Pattern.new('/test/:name')

    # Match routes
    captures = pattern.match('/test/sebastian')
    assert captures is not None
    is_ok(captures['name'], 'sebastian', 'name')

with subtest('constraints'):
    pattern = Pyjoyment.Routes.Pattern.new()
    constraints = pattern.constraints
    is_deeply_ok(constraints, {}, 'default')
    pattern.constraints = {'foo': re.compile(r'\w+')}
    is_deeply_ok(pattern.parse('/:foo', **pattern.constraints).match('/bar'), {'foo': 'bar'}, 'set')

with subtest('defaults'):
    pattern = Pyjoyment.Routes.Pattern.new('/')
    defaults = pattern.defaults
    is_deeply_ok(defaults, {}, 'default')
    pattern.defaults = {'foo': 'bar'}
    is_deeply_ok(pattern.match('/'), {'foo': 'bar'}, 'set')

with subtest('placeholder_start'):
    pattern = Pyjoyment.Routes.Pattern.new()
    start = pattern.placeholder_start
    is_ok(start, ':', 'default')
    pattern.placeholder_start = ':'
    is_ok(pattern.placeholder_start, ':', 'set')

with subtest('placeholders'):
    pattern = Pyjoyment.Routes.Pattern.new('/:foo/:bar')
    placeholders = pattern.placeholders
    is_deeply_ok(placeholders, ['foo', 'bar'], 'names')
    pattern.placeholders = ['foo', 'bar']
    is_deeply_ok(pattern.placeholders, ['foo', 'bar'], 'set')

with subtest('quote_end'):
    pattern = Pyjoyment.Routes.Pattern.new()
    end = pattern.quote_end
    is_ok(end, '>', 'default')
    pattern.quote_end = '}'
    is_ok(pattern.quote_end, '}', 'set')

with subtest('quote_start'):
    pattern = Pyjoyment.Routes.Pattern.new()
    start = pattern.quote_start
    is_ok(start, '<', 'default')
    pattern.quote_start = '{'
    is_deeply_ok(pattern.set(quote_end='}').parse('/{foo}bar').match('/bazbar'), {'foo': 'baz'}, 'set')

with subtest('regex'):
    pattern = Pyjoyment.Routes.Pattern.new('/foo')
    pattern.match('/foo')
    regex = pattern.regex
    ok(regex, 'compiled')
    pattern.regex = regex
    is_ok(pattern.regex, regex, 'set')

with subtest('relaxed_start'):
    pattern = Pyjoyment.Routes.Pattern.new()
    start = pattern.relaxed_start
    is_ok(start, '#', 'default')
    pattern.relaxed_start = '*'
    is_ok(pattern.relaxed_start, '*', 'set')

with subtest('tree'):
    pattern = Pyjoyment.Routes.Pattern.new('/foo')
    tree = pattern.tree
    is_deeply_ok(tree, [['text', '/foo']], 'parsed')
    pattern.tree = [['text', '/foo']]
    is_deeply_ok(pattern.match('/foo'), {}, 'set')

with subtest('type_start'):
    pattern = Pyjoyment.Routes.Pattern.new()
    start = pattern.type_start
    is_ok(start, ':', 'default')
    pattern.type_start = '|'
    is_ok(pattern.type_start, '|', 'set')

with subtest('types'):
    pattern = Pyjoyment.Routes.Pattern.new()
    types = pattern.types
    is_deeply_ok(types, {}, 'default')
    pattern.types = {'int': re.compile(r'[0-9]+')}
    is_deeply_ok(pattern.parse('/<id:int>').match('/23'), {'id': '23'}, 'set')

with subtest('unparsed'):
    pattern = Pyjoyment.Routes.Pattern.new('/:foo/:bar')
    unparsed = pattern.unparsed
    is_ok(unparsed, '/:foo/:bar', 'raw')
    pattern.unparsed = '/:foo/:bar'
    is_ok(pattern.unparsed, '/:foo/:bar', 'set')

with subtest('wildcard_start'):
    pattern = Pyjoyment.Routes.Pattern.new()
    start = pattern.wildcard_start
    is_ok(start, '*', 'default')
    pattern.wildcard_start = '*'
    is_ok(pattern.wildcard_start, '*', 'set')

with subtest('match'):
    pattern = Pyjoyment.Routes.Pattern.new('/foo/:name')
    captures = pattern.match('/foo/bar')
    is_deeply_ok(captures, {'name': 'bar'}, 'captures')
    captures = pattern.match('/foo/bar', True)
    is_deeply_ok(captures, {'name': 'bar'}, 'captures with format detection')

with subtest('match_partial'):
    pattern = Pyjoyment.Routes.Pattern.new('/foo')
    path = '/foo/bar'
    result = pattern.match_partial(path)
    assert result is not None
    captures, path = result
    is_deeply_ok(captures, {}, 'captures')
    is_ok(path, '/bar', 'rest of the path')
    is_deeply_ok(pattern.match_partial('/foo/bar', True), ({}, '/bar'), 'with format detection')

with subtest('new'):
    pattern = Pyjoyment.Routes.Pattern.new()
    is_ok(pattern.unparsed, None, 'not parsed')
    pattern = Pyjoyment.Routes.Pattern.new('/users/:id')
    is_ok(pattern.unparsed, '/users/:id', 'parsed')
    pattern = Pyjoyment.Routes.Pattern.new('/user/:id', id=re.compile(r'\d+'))
    ok(pattern.match('/user/foo') is None, 'constraint')
    pattern = Pyjoyment.Routes.Pattern.new(format=['json', 'yaml'])
    is_deeply_ok(pattern.constraints, {'format': ['json', 'yaml']}, 'format')

with subtest('parse'):
    pattern = Pyjoyment.Routes.Pattern.new()
    pattern = pattern.parse('/user/:id')
    is_ok(pattern.unparsed, '/user/:id', 'parsed')
    pattern = pattern.parse('/user/:id', id=re.compile(r'\d+'))
    is_deeply_ok(pattern.match('/user/23'), {'id': '23'}, 'constraint')
    pattern = pattern.parse(format=['json', 'yaml'])
    is_deeply_ok(pattern.constraints, {'format': ['json', 'yaml']}, 'format')

with subtest('render'):
    pattern = Pyjoyment.Routes.Pattern.new('/user/:id')
    path = pattern.render({'id': 24})
    is_ok(path, '/user/24', 'path')
    path = pattern.render({'id': 24, 'format': 'json'}, True)
    is_ok(path, '/user/24.json', 'path with format')

done_testing()
