from Pyjoyment.Lite import *


# /test
# /123
@any('/:foo', foo=['test', '123'])
def foo(c):
    foo = c.param('foo')
    c.render(text=f'Our :foo placeholder matched {foo}')


app.start()
