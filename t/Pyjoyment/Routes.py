import Pyjoyment.Controller
import Pyjoyment.Routes
import Pyjoyment.Routes.Match

from Pyjo.Test import *

import re


# /clean
r = Pyjoyment.Routes.new()
r.any('/clean').to(clean=1).set(name='very_clean')

# /clean/too
r.any('/clean/too').to(something=1).set(name='very_clean')

# /0
r.any('0').to(null=1)

# /alternatives
# /alternatives/0
# /alternatives/test
# /alternatives/23
r.any('/alternatives/:foo', foo=['0', 'test', '23']).to(foo=11)

# /alternatives2/0
# /alternatives2/test
# /alternatives2/23
r.any('/alternatives2/:foo/', foo=['0', 'test', '23'])

# /alternatives3/foo
# /alternatives3/foobar
r.any('/alternatives3/:foo', foo=['foo', 'foobar'])

# /alternatives4/foo
# /alternatives4/foo.bar
r.any('/alternatives4/:foo', foo=['foo', 'foo.bar'])

# /optional/*
# /optional/*/*
r.any('/optional/:foo/:bar', format=True).to(bar='test')

# /optional2
# /optional2/*
# /optional2/*/*
r.any('/optional2/:foo', format=True).to(foo='one').any('/:bar').to(bar='two')

# /*/test
test = r.any('/:testcase/test').to(action='test')

# /*/test/edit
test.any('/edit').to(action='edit').set(name='test_edit')

# /*/testedit
r.any('/:testcase/testedit').to(action='testedit')

# /*/test/delete/*
test.any('/delete/<id>', id=re.compile(r'\d+')).to(action='delete', id=23)

# /test2
test2 = r.any('/test2/').set(inline=True).to(testcase='test2')

# /test2 (inline)
test4 = test2.any('/').set(inline=True).to(testcase='index')

# /test2/foo
test4.any('/foo').to(testcase='baz')

# /test2/bar
test4.any('/bar').to(testcase='lalala')

# /test2/baz
test2.any('/baz').to('just#works')

# /
r.any('/').to(testcase='hello', action='world')

# /wildcards/1/*
r.any('/wildcards/1/<*wildcard>', wildcard=re.compile(r'(?:.*)')).to(testcase='wild', action='card')

# /wildcards/2/*
r.any('/wildcards/2/*wildcard').to(testcase='card', action='wild')

# /wildcards/3/*/foo
r.any('/wildcards/3/<*wildcard>/foo').to(testcase='very', action='dangerous')

# /wildcards/4/*/foo
r.any('/wildcards/4/*wildcard/foo').to(testcase='somewhat', action='dangerous')

# /format
# /format.*
r.any('/format', format=True).to(testcase='hello').to(action='you', format='html')

# /format2.txt
r.any('/format2', format=re.compile(r'txt')).to(testcase='we', action='howdy')

# /format3.txt
# /format3.text
r.any('/format3', format=['txt', 'text']).to(testcase='we', action='cheers')

# /format4
# /format4.html
r.any('/format4', format=['html']).to(testcase='us', action='yay', format='html')

# /format5
r.any('/format5', format=False).to(testcase='us', action='wow')

# /format6
r.any('/format6', format=False).to(testcase='us', action='doh', format='xml')

# /format7.foo
# /format7.foobar
r.any('/format7', format=['foo', 'foobar']).to('perl#rocks')

# /type/23
# /type/24
r.add_type('my_num', [23, 24])
r.any('/type/<id:my_num>').to('foo#bar')

# /articles/1/edit
# /articles/1/delete
# /articles/1/delete.json
inline = r.any('/articles/:id').set(inline=True).to(testcase='articles', action='load', format='html')
inline.any('/edit').to(testcase='articles', action='edit')
inline.any('/delete', format=['json']).to(testcase='articles', action='delete', format=None).set(name='articles_delete')

# GET /method/get
r.any('/method/get', format=['html']).methods('GET').to(testcase='method', action='get', format=None)

# POST /method/post
r.any('/method/post').methods('post').to(testcase='method', action='post')

# POST|GET /method/post_get
r.any('/method/post_get').methods('POST', 'get').to(testcase='method', action='post_get')

# /simple/form
r.any('/simple/form').to('test-test#test')

# /regex/alternatives/*
r.any('/regex/alternatives/:alternatives', alternatives=re.compile(r'foo|bar|baz')).to(
    testcase='regex', action='alternatives'
)

# /versioned/1.0/test
# /versioned/1.0/test.xml
# /versioned/2.4/test
# /versioned/2.4/test.xml
versioned = r.any('/versioned')
versioned.any('/1.0').to(testcase='bar').any('/test', format=['xml']).to(action='baz', format=None)
versioned.any('/2.4').to(testcase='foo').any('/test', format=['xml']).to(action='bar', format=None)

# /versioned/too/1.0
too = r.any('/versioned/too').to('too#')
too.any('/1.0').to('#foo')
too.any('/2.0', format=False).to('#bar')

# /multi/foo.bar
multi = r.any('/multi')
multi.any('/foo.bar', format=False).to('just#works')
multi.any('/bar.baz').to('works#too', format='xml')

# /nodetect
# /nodetect2.txt
# /nodetect2.html
inactive = r.any('/')
inactive.any('/nodetect').to('foo#none')
inactive.any('/nodetect2', format=['txt', 'html']).to('bar#hyper')

# /target/first
# /target/second
# /target/second.xml
# /source/third
# /source/third.xml
source = r.any('/source').to('source#')
first = source.any('/', format=False).any('/first').to('#first')
source.any('/second', format=['xml']).to('#second', format=None)
third = source.any('/third', format=['xml']).to('#third', format=None)
target = r.remove().any('/target').to('target#')
second = r.find('second')
is_ok(second.render({}), '/source/second', 'right result')
second.remove()
is_ok(second.render({}), '/second', 'right result')
target.add_child(first).add_child(second)
is_ok(second.render({}), '/target/second', 'right result')

# /websocket
r.websocket('/websocket', {'testcase': 'ws'}).any('/').to(action='just').any().to(works=1)

# /slash
# /slash.txt
r.any('/slash').to(testcase='just').any('/', format=['txt']).to(action='slash', format=None)

# /missing/*/name
# /missing/too
# /missing/too/test
r.any('/missing/:/name').to('missing#placeholder')
r.any('/missing/*/name').to('missing#wildcard')
r.any('/missing/too/*', **{'': ['test']}).to('missing#too', **{'': 'missing'})

# /partial/*
r.any('/partial').set(partial=True).to('foo#bar')

# GET   /similar/*
# PATCH /similar/too
similar = r.any('/similar').methods('DELETE', 'GET', 'PATCH').set(inline=True)
similar.any('/:something').methods('GET').to('similar#get')
similar.any('/too').methods('PATCH').to('similar#post')

# /custom_pattern/test_*_test
custom = r.get().to(four=4)
custom.pattern.set(quote_start='{', quote_end='}', placeholder_start='.', relaxed_start='$', wildcard_start='@')
custom.parse('/custom_pattern/a_{.one}_b/{$two}/{@three}')

# /inherit/first.html
# /inherit/first.json
# /inherit/second
# /inherit/second.html
# /inherit/second.json
inherit_format = r.any('/inherit', format=['json', 'html'])
inherit_format.get('/first').to('inherit#first')
inherit_format.get('/second').to('inherit#second', format=None)

# /inherit2/first
# /inherit2/first.xml
# /inherit2/second
# /inherit2/second.html
# /inherit2/third
inherit_format2 = r.any('/inherit2', format=['xml']).to('inherit#', format=None)
inherit_format2.get('/first').to('#first', format='html')
inherit_format2.post('/second', format=['html']).to('#second')
inherit_format2.get('/third', format=False).to('#third')

with subtest('Cached lookup'):
    fast = r.any('/fast')
    is_ok(r.find('fast'), fast, 'fast route found')
    is_ok(r.lookup('fast'), fast, 'fast route found')
    faster = r.any('/faster').set(name='fast')
    is_ok(r.find('fast'), faster, 'faster route found')
    is_ok(r.lookup('fast'), fast, 'fast route found')

with subtest('Make sure stash stays clean'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/clean')
    is_ok(m.root, r, 'right root')
    is_ok(m.endpoint.name, 'very_clean', 'right name')
    is_deeply_ok(m.stack, [{'clean': 1}], 'right strucutre')
    is_ok(m.path_for()['path'], '/clean', 'right path')
    is_ok(m.endpoint.suggested_method, 'GET', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/clean/too')
    is_deeply_ok(m.stack, [{'something': 1}], 'right strucutre')
    is_ok(m.path_for()['path'], '/clean/too', 'right path')

with subtest('No match'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/does_not_exist')
    is_ok(m.root, r, 'right root')
    is_ok(m.endpoint, None, 'no endpoint')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Introspect'):
    is_ok(r.find('very_clean').to_str(), '/clean', 'right pattern')
    is_ok(r.find('0').to_str(), '/0', 'right pattern')
    is_ok(r.find('test_edit').to_str(), '/:testcase/test/edit', 'right pattern')
    is_ok(r.find('articles_delete').to_str(), '/articles/:id/delete', 'right pattern')
    ok(not r.find('nodetect').pattern.constraints.get('format'), 'no value')
    is_ok(r.find('nodetect').to()['controller'], 'foo', 'right testcase')

with subtest('Null route'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/0')
    is_deeply_ok(m.stack, [{'null': 1}], 'right strucutre')
    is_ok(m.path_for()['path'], '/0', 'right path')

with subtest('Alternatives with default'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives')
    is_deeply_ok(m.stack, [{'foo': 11}], 'right strucutre')
    is_ok(m.path_for()['path'], '/alternatives', 'right path')
    is_ok(m.path_for(format='txt')['path'], '/alternatives/11.txt', 'right path')
    is_ok(m.path_for(foo=12, format='txt')['path'], '/alternatives/12.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/0')
    is_deeply_ok(m.stack, [{'foo': '0'}], 'right strucutre')
    is_ok(m.path_for()['path'], '/alternatives/0', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/test')
    is_deeply_ok(m.stack, [{'foo': 'test'}], 'right strucutre')
    is_ok(m.path_for()['path'], '/alternatives/test', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/23')
    is_deeply_ok(m.stack, [{'foo': '23'}], 'right strucutre')
    is_ok(m.path_for()['path'], '/alternatives/23', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/24')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/tset')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/00')
    is_deeply_ok(m.stack, [], 'empty stack')
    is_ok(m.path_for('alternativesfoo')['path'], '/alternatives', 'right path')
    is_ok(m.path_for('alternativesfoo', format='txt')['path'], '/alternatives/11.txt', 'right path')
    is_ok(m.path_for('alternativesfoo', foo=12, format='txt')['path'], '/alternatives/12.txt', 'right path')

with subtest('Alternatives without default'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/2')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/0')
    is_deeply_ok(m.stack, [{'foo': '0'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives2/0', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/test')
    is_deeply_ok(m.stack, [{'foo': 'test'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives2/test', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/23')
    is_deeply_ok(m.stack, [{'foo': '23'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives2/23', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/24')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/tset')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives2/00')
    is_deeply_ok(m.stack, [], 'empty stack')
    is_ok(m.path_for('alternatives2foo')['path'], '/alternatives2/', 'right path')
    is_ok(m.path_for('alternatives2foo', foo=0)['path'], '/alternatives2/0', 'right path')

with subtest('Alternatives with similar start'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives3/foo')
    is_deeply_ok(m.stack, [{'foo': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives3/foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives3/foobar')
    is_deeply_ok(m.stack, [{'foo': 'foobar'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives3/foobar', 'right path')

with subtest('Alternatives with special characters'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives4/foo')
    is_deeply_ok(m.stack, [{'foo': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives4/foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives4/foo.bar')
    is_deeply_ok(m.stack, [{'foo': 'foo.bar'}], 'right structure')
    is_ok(m.path_for()['path'], '/alternatives4/foo.bar', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives4/foobar')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives4/bar')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives4/bar.foo')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Optional placeholder'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional/23')
    is_deeply_ok(m.stack, [{'foo': '23', 'bar': 'test'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional/23', 'right path')
    is_ok(m.path_for(format='txt')['path'], '/optional/23/test.txt', 'right path')
    is_ok(m.path_for(foo=12, format='txt')['path'], '/optional/12/test.txt', 'right path')
    is_ok(m.path_for('optionalfoobar', format='txt')['path'], '/optional/23/test.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional/23/24')
    is_deeply_ok(m.stack, [{'foo': '23', 'bar': '24'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional/23/24', 'right path')
    is_ok(m.path_for(format='txt')['path'], '/optional/23/24.txt', 'right path')
    is_ok(m.path_for('optionalfoobar')['path'], '/optional/23/24', 'right path')
    is_ok(m.path_for('optionalfoobar', foo=0)['path'], '/optional/0/24', 'right path')

with subtest('Optional placeholders in nested routes'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional2')
    is_deeply_ok(m.stack, [{'foo': 'one', 'bar': 'two'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional2', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional2.txt')
    is_deeply_ok(m.stack, [{'foo': 'one', 'bar': 'two', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional2', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional2/three')
    is_deeply_ok(m.stack, [{'foo': 'three', 'bar': 'two'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional2/three', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional2/three/four')
    is_deeply_ok(m.stack, [{'foo': 'three', 'bar': 'four'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional2/three/four', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/optional2/three/four.txt')
    is_deeply_ok(m.stack, [{'foo': 'three', 'bar': 'four', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/optional2/three/four', 'right path')

with subtest('Real world example using most features at once'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/articles/1/edit')
    stack = [
        {'testcase': 'articles', 'action': 'load', 'id': '1', 'format': 'html'},
        {'testcase': 'articles', 'action': 'edit', 'id': '1', 'format': 'html'},
    ]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/articles/1/edit', 'right path')
    is_ok(m.path_for(format='html')['path'], '/articles/1/edit.html', 'right path')
    is_ok(m.path_for('articles_delete', format=None)['path'], '/articles/1/delete', 'right path')
    is_ok(m.path_for('articles_delete')['path'], '/articles/1/delete', 'right path')
    is_ok(m.path_for('articles_delete', id=12)['path'], '/articles/12/delete', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/articles/1/delete')
    stack = [
        {'testcase': 'articles', 'action': 'load', 'id': '1', 'format': 'html'},
        {'testcase': 'articles', 'action': 'delete', 'id': '1', 'format': None},
    ]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/articles/1/delete', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/articles/1/delete.json')
    stack = [
        {'testcase': 'articles', 'action': 'load', 'id': '1', 'format': 'json'},
        {'testcase': 'articles', 'action': 'delete', 'id': '1', 'format': 'json'},
    ]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/articles/1/delete.json', 'right path')

with subtest('Root'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/')
    is_deeply_ok(m.stack, [{'testcase': 'hello', 'action': 'world'}], 'right structure')
    is_ok(m.path_for()['path'], '/', 'right path')

with subtest('Path and captures'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/foo/test/edit')
    is_deeply_ok(m.stack, [{'testcase': 'foo', 'action': 'edit'}], 'right structure')
    is_ok(m.path_for()['path'], '/foo/test/edit', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/foo/testedit')
    is_deeply_ok(m.stack, [{'testcase': 'foo', 'action': 'testedit'}], 'right structure')
    is_ok(m.path_for()['path'], '/foo/testedit', 'right path')
    is_ok(m.endpoint.suggested_method, 'GET', 'right method')

with subtest('Optional captures in sub route with requirement'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/bar/test/delete/22')
    is_deeply_ok(m.stack, [{'testcase': 'bar', 'action': 'delete', 'id': '22'}], 'right structure')
    is_ok(m.path_for()['path'], '/bar/test/delete/22', 'right path')

with subtest('Defaults in sub route'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/bar/test/delete')
    is_deeply_ok(m.stack, [{'testcase': 'bar', 'action': 'delete', 'id': 23}], 'right structure')
    is_ok(m.path_for()['path'], '/bar/test/delete', 'right path')

with subtest('Chained routes'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/test2/foo')
    stack = [{'testcase': 'test2'}, {'testcase': 'index'}, {'testcase': 'baz'}]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/test2/foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/test2/bar')
    stack = [{'testcase': 'test2'}, {'testcase': 'index'}, {'testcase': 'lalala'}]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/test2/bar', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/test2/baz')
    stack = [{'testcase': 'test2'}, {'testcase': 'test2', 'controller': 'just', 'action': 'works'}]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/test2/baz', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/test2baz')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Named path_for'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/alternatives/test')
    is_ok(m.path_for()['path'], '/alternatives/test', 'right path')
    is_ok(m.path_for('test_edit', testcase='foo')['path'], '/foo/test/edit', 'right path')
    is_ok(m.path_for('test_edit', {'testcase': 'foo'})['path'], '/foo/test/edit', 'right path')

with subtest('Wildcards'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/1/hello/there')
    is_deeply_ok(m.stack, [{'testcase': 'wild', 'action': 'card', 'wildcard': 'hello/there'}], 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/1/hello/there', 'right path')
    is_ok(m.path_for(wildcard='')['path'], '/wildcards/1/', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/2/hello/there')
    is_deeply_ok(m.stack, [{'testcase': 'card', 'action': 'wild', 'wildcard': 'hello/there'}], 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/2/hello/there', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/3/hello/there/foo')
    is_deeply_ok(m.stack, [{'testcase': 'very', 'action': 'dangerous', 'wildcard': 'hello/there'}], 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/3/hello/there/foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/4/hello/there/foo')
    is_deeply_ok(
        m.stack, [{'testcase': 'somewhat', 'action': 'dangerous', 'wildcard': 'hello/there'}], 'right structure'
    )
    is_ok(m.path_for()['path'], '/wildcards/4/hello/there/foo', 'right path')

with subtest('Special characters'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/1/♥')
    is_deeply_ok(m.stack, [{'testcase': 'wild', 'action': 'card', 'wildcard': '♥'}], 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/1/♥', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/1/http://www.google.com')
    stack = [{'testcase': 'wild', 'action': 'card', 'wildcard': 'http://www.google.com'}]
    is_deeply_ok(m.stack, stack, 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/1/http://www.google.com', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/wildcards/1/%foo%bar%')
    is_deeply_ok(m.stack, [{'testcase': 'wild', 'action': 'card', 'wildcard': '%foo%bar%'}], 'right structure')
    is_ok(m.path_for()['path'], '/wildcards/1/%foo%bar%', 'right path')

with subtest('Format'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format')
    is_deeply_ok(m.stack, [{'testcase': 'hello', 'action': 'you', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/format', 'right path')
    is_ok(m.path_for(format=None)['path'], '/format', 'right path')
    is_ok(m.path_for(format='html')['path'], '/format.html', 'right path')
    is_ok(m.path_for(format='txt')['path'], '/format.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format.html')
    is_deeply_ok(m.stack, [{'testcase': 'hello', 'action': 'you', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/format', 'right path')
    is_ok(m.path_for(format=None)['path'], '/format', 'right path')
    is_ok(m.path_for(format='html')['path'], '/format.html', 'right path')
    is_ok(m.path_for(format='txt')['path'], '/format.txt', 'right path')

with subtest('Format with regex constraint'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format2')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format2.txt')
    is_deeply_ok(m.stack, [{'testcase': 'we', 'action': 'howdy', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/format2.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format2.html')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format2.txt.txt')
    is_deeply_ok(m.stack, [], 'empty stack')
    is_ok(m.path_for('format2', format='txt')['path'], '/format2.txt', 'right path')

with subtest('Format with constraint alternatives'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format3')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format3.txt')
    is_deeply_ok(m.stack, [{'testcase': 'we', 'action': 'cheers', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/format3.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format3.text')
    is_deeply_ok(m.stack, [{'testcase': 'we', 'action': 'cheers', 'format': 'text'}], 'right structure')
    is_ok(m.path_for()['path'], '/format3.text', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format3.html')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format3.txt.txt')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Format with constraint and default'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format4')
    is_deeply_ok(m.stack, [{'testcase': 'us', 'action': 'yay', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/format4.html', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format4.html')
    is_deeply_ok(m.stack, [{'testcase': 'us', 'action': 'yay', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/format4.html', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format4.txt')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format4.txt.html')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Forbidden format'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format5')
    is_deeply_ok(m.stack, [{'testcase': 'us', 'action': 'wow'}], 'right structure')
    is_ok(m.path_for()['path'], '/format5', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format5.html')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Forbidden format and default'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format6')
    is_deeply_ok(m.stack, [{'testcase': 'us', 'action': 'doh', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/format6', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format6.xml')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Formats with similar start'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format7.foo')
    is_deeply_ok(m.stack, [{'controller': 'perl', 'action': 'rocks', 'format': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/format7.foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format7.foobar')
    is_deeply_ok(m.stack, [{'controller': 'perl', 'action': 'rocks', 'format': 'foobar'}], 'right structure')
    is_ok(m.path_for()['path'], '/format7.foobar', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/format7.foobarbaz')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Placeholder types'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/type/23')
    is_deeply_ok(m.stack, [{'controller': 'foo', 'action': 'bar', 'id': '23'}], 'right structure')
    is_ok(m.path_for()['path'], '/type/23', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/type/24')
    is_deeply_ok(m.stack, [{'controller': 'foo', 'action': 'bar', 'id': '24'}], 'right structure')
    is_ok(m.path_for()['path'], '/type/24', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/type/25')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Format inheritance'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/first.html')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'first', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit/first.html', 'right path')
    is_ok(m.path_for(format=None)['path'], '/inherit/first', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/first.json')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'first', 'format': 'json'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit/first.json', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/first')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/first.xml')
    is_deeply_ok(m.stack, [], 'empty stack')

    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/second.html')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'second', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit/second.html', 'right path')
    is_ok(m.path_for(format=None)['path'], '/inherit/second', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/second.json')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'second', 'format': 'json'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit/second.json', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit/second')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'second', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit/second', 'right path')

    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit2/first')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'first', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit2/first.html', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit2/first.xml')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'first', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit2/first.xml', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit2/first.html')
    is_deeply_ok(m.stack, [], 'empty stack')

    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='POST', path='/inherit2/second')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'second', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit2/second', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='POST', path='/inherit2/second.html')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'second', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit2/second.html', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='POST', path='/inherit2/second.xml')
    is_deeply_ok(m.stack, [], 'empty stack')

    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit2/third')
    is_deeply_ok(m.stack, [{'controller': 'inherit', 'action': 'third', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/inherit2/third', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/inherit2/third.xml')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Request methods'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/method/get.html')
    is_deeply_ok(m.stack, [{'testcase': 'method', 'action': 'get', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/method/get.html', 'right path')
    is_ok(m.endpoint.suggested_method, 'GET', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='POST', path='/method/post')
    is_deeply_ok(m.stack, [{'testcase': 'method', 'action': 'post'}], 'right structure')
    is_ok(m.path_for()['path'], '/method/post', 'right path')
    is_ok(m.endpoint.suggested_method, 'POST', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/method/post_get')
    is_deeply_ok(m.stack, [{'testcase': 'method', 'action': 'post_get'}], 'right structure')
    is_ok(m.path_for()['path'], '/method/post_get', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='POST', path='/method/post_get')
    is_deeply_ok(m.stack, [{'testcase': 'method', 'action': 'post_get'}], 'right structure')
    is_ok(m.path_for()['path'], '/method/post_get', 'right path')
    is_ok(m.endpoint.suggested_method, 'GET', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='DELETE', path='/method/post_get')
    is_deeply_ok(m.stack, [], 'empty stack')
    is_ok(m.path_for().get('path'), None, 'no path')

with subtest('Not found'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/not_found')
    is_ok(m.path_for('test_edit', testcase='foo')['path'], '/foo/test/edit', 'right path')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Simplified form'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/simple/form')
    is_deeply_ok(m.stack, [{'controller': 'test-test', 'action': 'test'}], 'right structure')
    is_ok(m.path_for()['path'], '/simple/form', 'right path')
    is_ok(m.path_for('current')['path'], '/simple/form', 'right path')

with subtest('Special edge case with intermediate destinations (regex)'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/regex/alternatives/foo')
    is_deeply_ok(m.stack, [{'testcase': 'regex', 'action': 'alternatives', 'alternatives': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/regex/alternatives/foo', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/regex/alternatives/bar')
    is_deeply_ok(m.stack, [{'testcase': 'regex', 'action': 'alternatives', 'alternatives': 'bar'}], 'right structure')
    is_ok(m.path_for()['path'], '/regex/alternatives/bar', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/regex/alternatives/baz')
    is_deeply_ok(m.stack, [{'testcase': 'regex', 'action': 'alternatives', 'alternatives': 'baz'}], 'right structure')
    is_ok(m.path_for()['path'], '/regex/alternatives/baz', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/regex/alternatives/yada')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Route with version'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/1.0/test')
    is_deeply_ok(m.stack, [{'testcase': 'bar', 'action': 'baz', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/1.0/test', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/1.0/test.xml')
    is_deeply_ok(m.stack, [{'testcase': 'bar', 'action': 'baz', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/1.0/test.xml', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/2.4/test')
    is_deeply_ok(m.stack, [{'testcase': 'foo', 'action': 'bar', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/2.4/test', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/2.4/test.xml')
    is_deeply_ok(m.stack, [{'testcase': 'foo', 'action': 'bar', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/2.4/test.xml', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/3.0/test')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/3.4/test')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/0.3/test')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Route with version at the end'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/too/1.0')
    is_deeply_ok(m.stack, [{'controller': 'too', 'action': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/too/1.0', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/versioned/too/2.0')
    is_deeply_ok(m.stack, [{'controller': 'too', 'action': 'bar'}], 'right structure')
    is_ok(m.path_for()['path'], '/versioned/too/2.0', 'right path')

with subtest('Multiple extensions'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/multi/foo.bar')
    is_deeply_ok(m.stack, [{'controller': 'just', 'action': 'works'}], 'right structure')
    is_ok(m.path_for()['path'], '/multi/foo.bar', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/multi/foo.bar.baz')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/multi/bar.baz')
    is_deeply_ok(m.stack, [{'controller': 'works', 'action': 'too', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/multi/bar.baz', 'right path')

with subtest('Disabled format detection inheritance'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect')
    is_deeply_ok(m.stack, [{'controller': 'foo', 'action': 'none'}], 'right structure')
    is_ok(m.path_for()['path'], '/nodetect', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect.txt')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect2.txt')
    is_deeply_ok(m.stack, [{'controller': 'bar', 'action': 'hyper', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/nodetect2.txt', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect2.html')
    is_deeply_ok(m.stack, [{'controller': 'bar', 'action': 'hyper', 'format': 'html'}], 'right structure')
    is_ok(m.path_for()['path'], '/nodetect2.html', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect2')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/nodetect2.xml')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Removed routes'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/target/first')
    is_deeply_ok(m.stack, [{'controller': 'target', 'action': 'first'}], 'right structure')
    is_ok(m.path_for()['path'], '/target/first', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/target/first.xml')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/source/first')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/target/second')
    is_deeply_ok(m.stack, [{'controller': 'target', 'action': 'second', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/target/second', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/target/second.xml')
    is_deeply_ok(m.stack, [{'controller': 'target', 'action': 'second', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/target/second.xml', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/source/second')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/source/third')
    is_deeply_ok(m.stack, [{'controller': 'source', 'action': 'third', 'format': None}], 'right structure')
    is_ok(m.path_for()['path'], '/source/third', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/source/third.xml')
    is_deeply_ok(m.stack, [{'controller': 'source', 'action': 'third', 'format': 'xml'}], 'right structure')
    is_ok(m.path_for()['path'], '/source/third.xml', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/target/third')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('WebSocket'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/websocket')
    is_deeply_ok(m.stack, [], 'empty stack')
    m.find(c, method='GET', path='/websocket', websocket=True)
    is_deeply_ok(m.stack, [{'testcase': 'ws', 'action': 'just', 'works': 1}], 'right structure')
    is_ok(m.path_for()['path'], '/websocket', 'right path')
    ok(m.path_for()['websocket'], 'is a websocket')

with subtest('Just a slash with a format after a path'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/slash.txt')
    is_deeply_ok(m.stack, [{'testcase': 'just', 'action': 'slash', 'format': 'txt'}], 'right structure')
    is_ok(m.path_for()['path'], '/slash.txt', 'right path')
    ok(not m.path_for()['websocket'], 'not a websocket')
    is_ok(m.path_for(format='html')['path'], '/slash.html', 'right path')

with subtest('Nameless placeholder'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/missing/foo/name')
    is_deeply_ok(m.stack, [{'controller': 'missing', 'action': 'placeholder', '': 'foo'}], 'right structure')
    is_ok(m.path_for()['path'], '/missing/foo/name', 'right path')
    is_ok(m.path_for(**{'': 'bar'})['path'], '/missing/bar/name', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/missing/foo/bar/name')
    is_deeply_ok(m.stack, [{'controller': 'missing', 'action': 'wildcard', '': 'foo/bar'}], 'right structure')
    is_ok(m.path_for()['path'], '/missing/foo/bar/name', 'right path')
    is_ok(m.path_for(**{'': 'bar/baz'})['path'], '/missing/bar/baz/name', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/missing/too/test')
    is_deeply_ok(m.stack, [{'controller': 'missing', 'action': 'too', '': 'test'}], 'right structure')
    is_ok(m.path_for()['path'], '/missing/too/test', 'right path')
    is_ok(m.path_for(**{'': 'bar/baz'})['path'], '/missing/too/bar/baz', 'right path')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/missing/too/tset')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/missing/too')
    is_deeply_ok(m.stack, [{'controller': 'missing', 'action': 'too', '': 'missing'}], 'right structure')
    is_ok(m.path_for()['path'], '/missing/too', 'right path')

with subtest('Partial route'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/partial/test')
    is_deeply_ok(m.stack, [{'controller': 'foo', 'action': 'bar', 'path': '/test'}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/partial.test')
    is_deeply_ok(m.stack, [{'controller': 'foo', 'action': 'bar', 'path': '.test'}], 'right structure')

with subtest('Similar routes with placeholders'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/similar/too')
    is_deeply_ok(m.stack, [{}, {'controller': 'similar', 'action': 'get', 'something': 'too'}], 'right structure')
    is_ok(m.endpoint.suggested_method, 'GET', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='PATCH', path='/similar/too')
    is_deeply_ok(m.stack, [{}, {'controller': 'similar', 'action': 'post'}], 'right structure')
    is_ok(m.endpoint.suggested_method, 'PATCH', 'right method')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='DELETE', path='/similar/too')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Custom pattern'):
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/custom_pattern/a_123_b/c.123/d/123')
    is_deeply_ok(m.stack, [{'one': '123', 'two': 'c.123', 'three': 'd/123', 'four': 4}], 'right structure')
    is_ok(m.path_for()['path'], '/custom_pattern/a_123_b/c.123/d/123', 'right path')

with subtest('Unknown placeholder type (matches nothing)'):
    r = Pyjoyment.Routes.new()
    r.get('/<foo:does_not_exist>')
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/test')
    is_deeply_ok(m.stack, [], 'empty stack')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/23')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Routes with overlapping text prefixes'):
    r = Pyjoyment.Routes.new()
    r.get('/res1').to(n=1)
    r.get('/res10/:id').to(n=10)
    r.under('/res').get('/nested/:id').to(n='nested')
    r.get('/:any').to(n='any')
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/res10/23')
    is_deeply_ok(m.stack, [{'n': 10, 'id': '23'}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/res1')
    is_deeply_ok(m.stack, [{'n': 1}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/res/nested/5')
    is_deeply_ok(m.stack, [{}, {'n': 'nested', 'id': '5'}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/re')
    is_deeply_ok(m.stack, [{'n': 'any', 'any': 're'}], 'right structure')

with subtest('Routes changed after matching'):
    r = Pyjoyment.Routes.new()
    bridge = r.under('/').to(n='bridge')
    nested = bridge.any('/').to(n='nested')
    nested.get('/a').to(n='a')
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/a')
    is_deeply_ok(m.stack, [{'n': 'bridge'}, {'n': 'a'}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/b')
    is_deeply_ok(m.stack, [], 'empty stack')

    b = nested.get('/b').to(n='b')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/b')
    is_deeply_ok(m.stack, [{'n': 'bridge'}, {'n': 'b'}], 'right structure')

    b.remove()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/b')
    is_deeply_ok(m.stack, [], 'empty stack')

with subtest('Custom regex'):
    r = Pyjoyment.Routes.new()
    r.get('/foo').to(n='foo').pattern.regex = re.compile(r'^/foo', re.I)
    api = r.any().to(n='api')
    api.pattern.regex = re.compile(r'^/api')
    api.get('/users').to(n='users')
    c = Pyjoyment.Controller.new()
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/FOO')
    is_deeply_ok(m.stack, [{'n': 'foo'}], 'right structure')
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(c, method='GET', path='/api/users')
    is_deeply_ok(m.stack, [{'n': 'users'}], 'right structure')

done_testing()
