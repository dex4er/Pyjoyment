import Pyjoyment.Routes.Pattern

from Pyjo.String.Unicode import u
from Pyjo.Test import *

import re


# Text pattern (optimized)
pattern = Pyjoyment.Routes.Pattern.new('/test/123')
is_deeply_ok(pattern.match('/test/123'), {}, 'right structure')
is_deeply_ok(pattern.match('/test'), None, 'no result')
is_ok(pattern.tree[0][1], '/test/123', 'optimized pattern')

# Normal pattern with text, placeholders and a default value
pattern = Pyjoyment.Routes.Pattern.new().parse('/test/<controller>/:action')
pattern.defaults = {'action': 'index'}
is_deeply_ok(pattern.match('/test/foo/bar', True), {'controller': 'foo', 'action': 'bar'}, 'right structure')
is_deeply_ok(pattern.match('/test/foo'), {'controller': 'foo', 'action': 'index'}, 'right structure')
is_deeply_ok(pattern.match('/test/foo/'), {'controller': 'foo', 'action': 'index'}, 'right structure')
ok(pattern.match('/test/') is None, 'no result')
is_ok(pattern.render({'controller': 'foo'}), '/test/foo', 'right result')

# Optional placeholder in the middle
pattern = Pyjoyment.Routes.Pattern.new('/test<name>123')
pattern.defaults = {'name': 'foo'}
is_deeply_ok(pattern.match('/test123', True), {'name': 'foo'}, 'right structure')
is_deeply_ok(pattern.match('/testbar123', True), {'name': 'bar'}, 'right structure')
ok(pattern.match('/test/123') is None, 'no result')
is_ok(pattern.render(), '/testfoo123', 'right result')
is_ok(pattern.render({'name': 'bar'}), '/testbar123', 'right result')
pattern.defaults = {'name': ''}
is_deeply_ok(pattern.match('/test123', True), {'name': ''}, 'right structure')
is_ok(pattern.render(), '/test123', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/test/:name/123')
pattern.defaults = {'name': 'foo'}
is_deeply_ok(pattern.match('/test/123', True), {'name': 'foo'}, 'right structure')
is_deeply_ok(pattern.match('/test/bar/123', True), {'name': 'bar'}, 'right structure')
ok(pattern.match('/test') is None, 'no result')
is_ok(pattern.render(), '/test/foo/123', 'right result')
is_ok(pattern.render({'name': 'bar'}), '/test/bar/123', 'right result')

# Multiple optional placeholders in the middle
pattern = Pyjoyment.Routes.Pattern.new('/test/:a/123/:b/456')
pattern.defaults = {'a': 'a', 'b': 'b'}
is_deeply_ok(pattern.match('/test/123/456', True), {'a': 'a', 'b': 'b'}, 'right structure')
is_deeply_ok(pattern.match('/test/c/123/456', True), {'a': 'c', 'b': 'b'}, 'right structure')
is_deeply_ok(pattern.match('/test/123/c/456', True), {'a': 'a', 'b': 'c'}, 'right structure')
is_deeply_ok(pattern.match('/test/c/123/d/456', True), {'a': 'c', 'b': 'd'}, 'right structure')
is_ok(pattern.render(), '/test/a/123/b/456', 'right result')
is_ok(pattern.render({'a': 'c'}), '/test/c/123/b/456', 'right result')
is_ok(pattern.render({'b': 'c'}), '/test/a/123/c/456', 'right result')
is_ok(pattern.render({'a': 'c', 'b': 'd'}), '/test/c/123/d/456', 'right result')

# Root
pattern = Pyjoyment.Routes.Pattern.new('/')
is_ok(pattern.unparsed, None, 'slash has been optimized away')
pattern.defaults = {'action': 'index'}
ok(pattern.match('/test/foo/bar') is None, 'no result')
is_deeply_ok(pattern.match('/'), {'action': 'index'}, 'right structure')
is_ok(pattern.render(), '', 'right result')
is_ok(pattern.render({'format': 'txt'}, True), '.txt', 'right result')

# Regex in pattern
pattern = Pyjoyment.Routes.Pattern.new('/test/<controller>/:action/<id>', id=r'\d+')
pattern.defaults = {'action': 'index', 'id': 1}
is_deeply_ok(pattern.match('/test/foo/bar/203'), {'controller': 'foo', 'action': 'bar', 'id': '203'}, 'right structure')
ok(pattern.match('/test/foo/bar/baz') is None, 'no result')
is_ok(pattern.render({'controller': 'zzz', 'action': 'index', 'id': 13}), '/test/zzz/index/13', 'right result')
is_ok(pattern.render({'controller': 'zzz'}), '/test/zzz', 'right result')

# Quoted placeholders
pattern = Pyjoyment.Routes.Pattern.new('/<:controller>test/<action>')
pattern.defaults = {'action': 'index'}
is_deeply_ok(pattern.match('/footest/bar'), {'controller': 'foo', 'action': 'bar'}, 'right structure')
is_ok(pattern.render({'controller': 'zzz', 'action': 'lala'}), '/zzztest/lala', 'right result')
ok(pattern.match('/test/lala') is None, 'no result')

# Relaxed
pattern = Pyjoyment.Routes.Pattern.new('/test/#controller/:action')
is_deeply_ok(pattern.match('/test/foo.bar/baz'), {'controller': 'foo.bar', 'action': 'baz'}, 'right structure')
is_ok(pattern.render({'controller': 'foo.bar', 'action': 'baz'}), '/test/foo.bar/baz', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/test/<#groovy>')
is_deeply_ok(pattern.match('/test/foo.bar'), {'groovy': 'foo.bar'}, 'right structure')
is_ok(pattern.defaults.get('format'), None, 'no value')
is_ok(pattern.render({'groovy': 'foo.bar'}), '/test/foo.bar', 'right result')

# Wildcard
pattern = Pyjoyment.Routes.Pattern.new('/test/<:controller>/<*action>')
is_deeply_ok(
    pattern.match('/test/foo/bar.baz/yada'), {'controller': 'foo', 'action': 'bar.baz/yada'}, 'right structure'
)
is_ok(pattern.render({'controller': 'foo', 'action': 'bar.baz/yada'}), '/test/foo/bar.baz/yada', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/tset/:controller/*action')
is_deeply_ok(
    pattern.match('/tset/foo/bar.baz/yada'), {'controller': 'foo', 'action': 'bar.baz/yada'}, 'right structure'
)
is_ok(pattern.render({'controller': 'foo', 'action': 'bar.baz/yada'}), '/tset/foo/bar.baz/yada', 'right result')

# Render false value
pattern = Pyjoyment.Routes.Pattern.new('/:id')
is_ok(pattern.render({'id': 0}), '/0', 'right result')

# Regex in path
pattern = Pyjoyment.Routes.Pattern.new('/:test')
is_deeply_ok(pattern.match('/test(test)(\\Qtest\\E)('), {'test': 'test(test)(\\Qtest\\E)('}, 'right structure')
is_ok(pattern.render({'test': '23'}), '/23', 'right result')

# Regex in pattern
pattern = Pyjoyment.Routes.Pattern.new('/.+<:test>')
is_deeply_ok(pattern.match('/.+test'), {'test': 'test'}, 'right structure')
is_ok(pattern.render({'test': '23'}), '/.+23', 'right result')

# Unusual values
pattern = Pyjoyment.Routes.Pattern.new('/:test')
value = u('abc%E4cba').url_unescape().to_str()
is_deeply_ok(pattern.match(f'/{value}'), {'test': value}, 'right structure')
is_ok(pattern.render({'test': value}), f'/{value}', 'right result')
value = u('abc%FCcba').url_unescape().to_str()
is_deeply_ok(pattern.match(f'/{value}'), {'test': value}, 'right structure')
is_ok(pattern.render({'test': value}), f'/{value}', 'right result')
value = u('abc%DFcba').url_unescape().to_str()
is_deeply_ok(pattern.match(f'/{value}'), {'test': value}, 'right structure')
is_ok(pattern.render({'test': value}), f'/{value}', 'right result')
value = u('abc%24cba').url_unescape().to_str()
is_deeply_ok(pattern.match(f'/{value}'), {'test': value}, 'right structure')
is_ok(pattern.render({'test': value}), f'/{value}', 'right result')
value = u('abc%20cba').url_unescape().to_str()
is_deeply_ok(pattern.match(f'/{value}'), {'test': value}, 'right structure')
is_ok(pattern.render({'test': value}), f'/{value}', 'right result')

# Format detection
pattern = Pyjoyment.Routes.Pattern.new('/test')
pattern.defaults = {'action': 'index'}
pattern.constraints = {'format': True}
ok(not pattern.regex, 'no regex')
is_deeply_ok(pattern.match('/test.xml', True), {'action': 'index', 'format': 'xml'}, 'right structure')
ok(pattern.regex, 'regex has been compiled on demand')
pattern = Pyjoyment.Routes.Pattern.new('/test.json')
pattern.defaults = {'action': 'index'}
ok(not pattern.regex, 'no regex')
is_deeply_ok(pattern.match('/test.json'), {'action': 'index'}, 'right structure')
ok(pattern.regex, 'regex has been compiled on demand')
is_deeply_ok(pattern.match('/test.json', True), {'action': 'index'}, 'right structure')
ok(pattern.match('/test.xml') is None, 'no result')
ok(pattern.match('/test') is None, 'no result')

# Formats without detection
pattern = Pyjoyment.Routes.Pattern.new('/test')
pattern.defaults = {'action': 'index'}
ok(not pattern.regex, 'no regex')
ok(pattern.match('/test.xml') is None, 'no result')
ok(pattern.regex, 'regex has been compiled on demand')
is_deeply_ok(pattern.match('/test'), {'action': 'index'}, 'right structure')

# Format detection disabled
pattern = Pyjoyment.Routes.Pattern.new('/test', format=False)
pattern.defaults = {'action': 'index'}
ok(not pattern.regex, 'no regex')
is_deeply_ok(pattern.match('/test', True), {'action': 'index'}, 'right structure')
ok(pattern.regex, 'regex has been compiled on demand')
ok(pattern.match('/test.xml', True) is None, 'no result')

# Special pattern for disabling format detection
pattern = Pyjoyment.Routes.Pattern.new(format=False)
is_ok(pattern.constraints['format'], False, 'right value')
pattern.defaults = {'action': 'index'}
is_deeply_ok(pattern.match('/', True), {'action': 'index'}, 'right structure')
ok(pattern.match('/.xml', True) is None, 'no result')

# Versioned pattern
pattern = Pyjoyment.Routes.Pattern.new('/:test/v1.0')
pattern.defaults = {'action': 'index', 'format': 'html'}
result = pattern.match('/foo/v1.0', True)
is_deeply_ok(result, {'test': 'foo', 'action': 'index', 'format': 'html'}, 'right structure')
is_ok(pattern.render(result), '/foo/v1.0', 'right result')
is_ok(pattern.render(result, True), '/foo/v1.0.html', 'right result')
is_ok(pattern.render({**result, 'format': None}, True), '/foo/v1.0', 'right result')

# Versioned pattern with format
pattern = Pyjoyment.Routes.Pattern.new('/:test/v1.0')
pattern.defaults = {'action': 'index', 'format': 'html'}
pattern.constraints = {'format': ['txt']}
result = pattern.match('/foo/v1.0.txt', True)
is_deeply_ok(result, {'test': 'foo', 'action': 'index', 'format': 'txt'}, 'right structure')
is_ok(pattern.render(result), '/foo/v1.0', 'right result')
is_ok(pattern.render(result, True), '/foo/v1.0.txt', 'right result')
ok(pattern.match('/foo/v2.0', True) is None, 'no result')

# Special placeholder names
pattern = Pyjoyment.Routes.Pattern.new('/:')
result = pattern.match('/foo', True)
is_deeply_ok(result, {'': 'foo'}, 'right structure')
is_ok(pattern.render(result, True), '/foo', 'right result')
is_ok(pattern.render({'': 'bar'}, True), '/bar', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/#')
result = pattern.match('/foo.bar', True)
is_deeply_ok(result, {'': 'foo.bar'}, 'right structure')
is_ok(pattern.render(result, True), '/foo.bar', 'right result')
is_ok(pattern.render({'': 'bar.baz'}, True), '/bar.baz', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/*')
result = pattern.match('/foo/bar', True)
is_deeply_ok(result, {'': 'foo/bar'}, 'right structure')
is_ok(pattern.render(result, True), '/foo/bar', 'right result')
is_ok(pattern.render({'': 'bar/baz'}, True), '/bar/baz', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/:/:0')
result = pattern.match('/foo/bar', True)
is_deeply_ok(result, {'': 'foo', '0': 'bar'}, 'right structure')
is_ok(pattern.render(result, True), '/foo/bar', 'right result')
is_ok(pattern.render({'': 'bar', '0': 'baz'}, True), '/bar/baz', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/<:>test/<0>')
result = pattern.match('/footest/bar', True)
is_deeply_ok(result, {'': 'foo', '0': 'bar'}, 'right structure')
is_ok(pattern.render(result, True), '/footest/bar', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('/<>test')
result = pattern.match('/footest', True)
is_deeply_ok(result, {'': 'foo'}, 'right structure')
is_ok(pattern.render(result, True), '/footest', 'right result')

# Normalize slashes
pattern = Pyjoyment.Routes.Pattern.new(':foo/')
result = pattern.match('/bar', True)
is_deeply_ok(result, {'foo': 'bar'}, 'right structure')
is_ok(pattern.render(result, True), '/bar', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('//:foo//bar//')
result = pattern.match('/foo/bar', True)
is_deeply_ok(result, {'foo': 'foo'}, 'right structure')
is_ok(pattern.render(result, True), '/foo/bar', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('//')
result = pattern.match('/', True)
is_deeply_ok(result, {}, 'right structure')
is_ok(pattern.render(result, True), '', 'right result')
pattern = Pyjoyment.Routes.Pattern.new('0')
result = pattern.match('/0', True)
is_deeply_ok(result, {}, 'right structure')
is_ok(pattern.render(result, True), '/0', 'right result')

# Optional format with constraint
pattern = Pyjoyment.Routes.Pattern.new('/')
pattern.defaults['format'] = 'txt'
pattern.constraints['format'] = ['txt']
result = pattern.match('/', True)
is_deeply_ok(result, {'format': 'txt'}, 'right structure')

# Unicode
pattern = Pyjoyment.Routes.Pattern.new('/<one>♥<two>')
result = pattern.match('/i♥mojolicious')
is_deeply_ok(result, {'one': 'i', 'two': 'mojolicious'}, 'right structure')
is_ok(pattern.render(result, True), '/i♥mojolicious', 'right result')

# Pattern reuse
pattern = Pyjoyment.Routes.Pattern.new().parse('/first').parse('/second').set(defaults={'test': 'works'})
ok(pattern.match('/first') is None, 'no result')
result = pattern.match('/second')
is_deeply_ok(result, {'test': 'works'}, 'right structure')
is_ok(pattern.render(result, True), '/second', 'right result')

# Placeholder types
pattern = Pyjoyment.Routes.Pattern.new().set(types={'num': re.compile(r'\d+')}).parse('/foo/<bar:num>/baz')
result = pattern.match('/foo/23/baz', True)
is_deeply_ok(result, {'bar': '23'}, 'right structure')
is_ok(pattern.render(result, True), '/foo/23/baz', 'right result')
ok(pattern.match('/foo/bar/baz', True) is None, 'no result')

with subtest('Alternate placeholder characters'):
    pattern = Pyjoyment.Routes.Pattern.new().set(placeholder_start='|').parse('/|test')
    result = pattern.match('/foo')
    is_deeply_ok(result, {'test': 'foo'}, 'right structure')
    is_ok(pattern.render(result, True), '/foo', 'right result')
    pattern = Pyjoyment.Routes.Pattern.new().set(relaxed_start='|').parse('/|test')
    result = pattern.match('/foo')
    is_deeply_ok(result, {'test': 'foo'}, 'right structure')
    is_ok(pattern.render(result, True), '/foo', 'right result')
    pattern = Pyjoyment.Routes.Pattern.new().set(wildcard_start='|').parse('/|test')
    result = pattern.match('/foo')
    is_deeply_ok(result, {'test': 'foo'}, 'right structure')
    is_ok(pattern.render(result, True), '/foo', 'right result')
    pattern = (
        Pyjoyment.Routes.Pattern.new().set(types={'num': re.compile(r'\d+')}).set(type_start='|').parse('/<test|num>')
    )
    result = pattern.match('/42')
    is_deeply_ok(result, {'test': '42'}, 'right structure')
    is_ok(pattern.render(result, True), '/42', 'right result')

# Not in Mojolicious: a path whose rest is 0 is no match, where Mojo takes it for one, as 0 is false in Perl
with subtest('Rest of the path'):
    pattern = Pyjoyment.Routes.Pattern.new('/test')
    ok(pattern.match('/test0') is None, 'no result')
    ok(pattern.match('/test/0') is None, 'no result')
    is_deeply_ok(pattern.match('/test/'), {}, 'right structure')
    pattern = Pyjoyment.Routes.Pattern.new('/test/:name')
    is_deeply_ok(pattern.match_partial('/test/foo/bar'), ({'name': 'foo'}, '/bar'), 'captures and the rest')
    is_ok(pattern.match_partial('/foo'), None, 'no result')

done_testing()
