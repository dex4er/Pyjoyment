from Pyjoyment.Lite import *


plugin('Config', file='/etc/myapp.conf', default={'foo': 'bar'})


# Return configured foo value, or default if no configuration file
@get('/foo')
def foo(c):
    foo = c.app.config('foo')
    c.render(json={'foo': foo})


app.start()
