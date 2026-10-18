from Pyjoyment.Lite import *


# /foo/test
# /foo/test123
@get('/foo/:bar')
def foo(c):
    bar = c.stash('bar')
    c.render(text=f'Our :bar placeholder matched {bar}')


# /testsomething/foo
# /test123something/foo
@get('/<:bar>something/foo')
def something(c):
    bar = c.param('bar')
    c.render(text=f'Our :bar placeholder matched {bar}')


app.start()
